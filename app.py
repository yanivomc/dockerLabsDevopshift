import json
import os
import socket
from collections import Counter

from flask import Flask, abort, jsonify, render_template, request

app = Flask(__name__)
VERSION = "1.0"
CURRENT_TOPIC = 4

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
        "topic": 7,
        "title": "Publish",
        "tagline": "Push to a registry",
        "summary": "Push your image to Docker Hub and GHCR — share what you built.",
        "components": [
            {"name": "Browser", "kind": "client"},
            {"name": "Flask", "kind": "app"},
            {"name": "Redis", "kind": "cache"},
            {"name": "SQLite (volume)", "kind": "storage"},
            {"name": "Registry", "kind": "external"},
        ],
    },
    {
        "topic": "P2.1",
        "title": "Slim down",
        "tagline": "Multi-stage build",
        "summary": "Shrink the image with a multi-stage Dockerfile.",
        "components": [
            {"name": "Browser", "kind": "client"},
            {"name": "Flask (slim)", "kind": "app"},
            {"name": "Redis", "kind": "cache"},
            {"name": "SQLite (volume)", "kind": "storage"},
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
views = Counter()


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
        "views_total": sum(views.values()),
    }


@app.route("/")
def index():
    views["home"] += 1
    category = request.args.get("category")
    return render_template(
        "index.html",
        products=_filter_by_category(category),
        categories=CATEGORIES,
        selected_category=category,
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    views["product"] += 1
    product = PRODUCTS_BY_ID.get(product_id)
    if not product:
        abort(404)
    return render_template("product.html", product=product)


@app.route("/architecture")
def architecture():
    views["architecture"] += 1
    return render_template("architecture.html", stages=ARCHITECTURE_STAGES)


@app.route("/products")
def products():
    return jsonify(_filter_by_category(request.args.get("category")))


@app.route("/products/<int:product_id>")
def product_json(product_id):
    product = PRODUCTS_BY_ID.get(product_id)
    if not product:
        abort(404)
    return jsonify(product)


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
        views=dict(views),
    )


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
