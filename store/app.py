import json
import os
import socket
import sqlite3
from contextlib import contextmanager

import redis as redis_lib
from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
VERSION = "1.0"
CURRENT_TOPIC = "P2.1"
DB_PATH = os.environ.get("DB_PATH", "/data/store.db")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
CACHE_TTL_SECONDS = 30

CACHE_KEY_PRODUCTS = "products:all"
CACHE_KEY_HITS = "cache:hits"
CACHE_KEY_MISSES = "cache:misses"

ARCHITECTURE_STAGES = [
    {
        "topic": 3,
        "title": "Monolith",
        "tagline": "Pull and run",
        "summary": "One pre-built container, static JSON inside.",
        "components": [
            {"name": "Browser", "kind": "client"},
            {"name": "Flask + products.json", "kind": "app"},
        ],
    },
    {
        "topic": 4,
        "title": "Build it yourself",
        "tagline": "Same shape, your Dockerfile",
        "summary": "Same architecture as Topic 3 — but you write the Dockerfile and build the image.",
        "components": [
            {"name": "Browser", "kind": "client"},
            {"name": "Flask (your image)", "kind": "app"},
        ],
    },
    {
        "topic": 5,
        "title": "Persistence",
        "tagline": "Add a volume",
        "summary": "SQLite on a named volume — cart survives restarts.",
        "components": [
            {"name": "Browser", "kind": "client"},
            {"name": "Flask", "kind": "app"},
            {"name": "SQLite (volume)", "kind": "storage"},
        ],
    },
    {
        "topic": 6,
        "title": "Sidecar",
        "tagline": "Two containers, one network",
        "summary": "Add Redis on a user-defined network for caching.",
        "components": [
            {"name": "Browser", "kind": "client"},
            {"name": "Flask", "kind": "app"},
            {"name": "Redis", "kind": "cache"},
            {"name": "SQLite (volume)", "kind": "storage"},
        ],
    },
    {
        "topic": "P2.1",
        "title": "Multi-stage + Bake",
        "tagline": "Build many, push all",
        "summary": "Production-shape image (Tailwind build, gunicorn), Docker Bake orchestrates parallel builds and pushes to a registry.",
        "components": [
            {"name": "Browser", "kind": "client"},
            {"name": "Flask (gunicorn, slim)", "kind": "app"},
            {"name": "Redis (custom image)", "kind": "cache"},
            {"name": "SQLite (volume)", "kind": "storage"},
            {"name": "Registry", "kind": "external"},
        ],
    },
    {
        "topic": "P2.2",
        "title": "Compose stack",
        "tagline": "MySQL, Redis, Ollama",
        "summary": "Full Compose: Flask + MySQL + Redis + Ollama-powered /recommend.",
        "components": [
            {"name": "Browser", "kind": "client"},
            {"name": "Flask", "kind": "app"},
            {"name": "MySQL", "kind": "storage"},
            {"name": "Redis", "kind": "cache"},
            {"name": "Ollama", "kind": "ai"},
        ],
    },
]


def _load_products():
    with open(os.path.join(os.path.dirname(__file__), "products.json")) as f:
        return json.load(f)


PRODUCTS = _load_products()
PRODUCTS_BY_ID = {p["id"]: p for p in PRODUCTS}
CATEGORIES = sorted({p["category"] for p in PRODUCTS})


# --- SQLite storage ---------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS cart_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 1,
  added_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS page_views (
  path TEXT PRIMARY KEY,
  count INTEGER NOT NULL DEFAULT 0
);
"""


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with db() as conn:
        conn.executescript(SCHEMA)


def record_view(path):
    with db() as conn:
        conn.execute(
            "INSERT INTO page_views(path, count) VALUES (?, 1) "
            "ON CONFLICT(path) DO UPDATE SET count = count + 1",
            (path,),
        )


def get_views():
    with db() as conn:
        return {r["path"]: r["count"] for r in conn.execute("SELECT path, count FROM page_views")}


def get_views_total():
    with db() as conn:
        row = conn.execute("SELECT COALESCE(SUM(count), 0) AS total FROM page_views").fetchone()
        return row["total"]


def add_to_cart(product_id, quantity=1):
    with db() as conn:
        conn.execute(
            "INSERT INTO cart_items(product_id, quantity) VALUES (?, ?)",
            (product_id, quantity),
        )


def get_cart_rows():
    with db() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT product_id, SUM(quantity) AS quantity "
                "FROM cart_items GROUP BY product_id "
                "ORDER BY MIN(added_at) DESC"
            )
        ]


def get_cart_count():
    with db() as conn:
        row = conn.execute("SELECT COALESCE(SUM(quantity), 0) AS total FROM cart_items").fetchone()
        return row["total"]


def clear_cart():
    with db() as conn:
        conn.execute("DELETE FROM cart_items")


def _decorate_cart(rows):
    items = []
    total = 0
    for r in rows:
        p = PRODUCTS_BY_ID.get(r["product_id"])
        if not p:
            continue
        line = p["price"] * r["quantity"]
        total += line
        items.append({"product": p, "quantity": r["quantity"], "line_total": line})
    return items, total


# --- Redis cache ------------------------------------------------------------

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis_lib.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
    return _redis_client


def get_cached_products(category=None):
    """Cache-aside read for /products. Falls through to PRODUCTS if Redis is down."""
    base = _filter_by_category(category)
    try:
        r = get_redis()
        raw = r.get(CACHE_KEY_PRODUCTS)
        if raw is not None:
            r.incr(CACHE_KEY_HITS)
            cached = json.loads(raw)
            return [p for p in cached if not category or p["category"] == category]
        r.incr(CACHE_KEY_MISSES)
        r.setex(CACHE_KEY_PRODUCTS, CACHE_TTL_SECONDS, json.dumps(PRODUCTS))
    except redis_lib.RedisError:
        pass
    return base


def cache_stats():
    try:
        r = get_redis()
        hits = int(r.get(CACHE_KEY_HITS) or 0)
        misses = int(r.get(CACHE_KEY_MISSES) or 0)
        ttl = r.ttl(CACHE_KEY_PRODUCTS)
        total = hits + misses
        return {
            "connected": True,
            "redis_host": REDIS_HOST,
            "redis_port": REDIS_PORT,
            "hits": hits,
            "misses": misses,
            "ratio": round(hits / total, 3) if total else 0,
            "ttl_remaining": ttl if ttl and ttl > 0 else None,
            "ttl_seconds": CACHE_TTL_SECONDS,
        }
    except redis_lib.RedisError:
        return {
            "connected": False,
            "redis_host": REDIS_HOST,
            "redis_port": REDIS_PORT,
            "hits": 0,
            "misses": 0,
            "ratio": 0,
            "ttl_remaining": None,
            "ttl_seconds": CACHE_TTL_SECONDS,
        }


# --- Flask routes -----------------------------------------------------------

def _filter_by_category(category):
    return [p for p in PRODUCTS if p["category"] == category] if category else PRODUCTS


@app.context_processor
def inject_globals():
    current_stage = next(s for s in ARCHITECTURE_STAGES if s["topic"] == CURRENT_TOPIC)
    return {
        "current_topic": CURRENT_TOPIC,
        "current_stage": current_stage,
        "hostname": socket.gethostname(),
        "version": VERSION,
        "views_total": get_views_total(),
        "cart_count": get_cart_count(),
        "cache": cache_stats(),
    }


@app.route("/")
def index():
    record_view("home")
    category = request.args.get("category")
    return render_template(
        "index.html",
        products=_filter_by_category(category),
        categories=CATEGORIES,
        selected_category=category,
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    record_view("product")
    product = PRODUCTS_BY_ID.get(product_id)
    if not product:
        abort(404)
    return render_template("product.html", product=product)


@app.route("/architecture")
def architecture():
    record_view("architecture")
    return render_template("architecture.html", stages=ARCHITECTURE_STAGES)


@app.route("/cart")
def cart():
    record_view("cart")
    items, total = _decorate_cart(get_cart_rows())
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    if product_id not in PRODUCTS_BY_ID:
        abort(404)
    add_to_cart(product_id)
    return redirect(request.referrer or url_for("cart"))


@app.route("/cart/clear", methods=["POST"])
def cart_clear():
    clear_cart()
    return redirect(url_for("cart"))


@app.route("/products")
def products():
    return jsonify(get_cached_products(request.args.get("category")))


@app.route("/products/<int:product_id>")
def product_json(product_id):
    product = PRODUCTS_BY_ID.get(product_id)
    if not product:
        abort(404)
    return jsonify(product)


@app.route("/cache")
def cache():
    return jsonify(cache_stats())


@app.route("/health")
def health():
    return jsonify(status="ok", version=VERSION)


@app.route("/info")
def info():
    return jsonify(
        hostname=socket.gethostname(),
        version=VERSION,
        env=os.environ.get("APP_ENV", "dev"),
        topic=CURRENT_TOPIC,
        db_path=DB_PATH,
        views=get_views(),
        cart_count=get_cart_count(),
        cache=cache_stats(),
    )


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
