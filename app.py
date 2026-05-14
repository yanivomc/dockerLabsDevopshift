import json
import os
import socket

from flask import Flask, jsonify, render_template

app = Flask(__name__)
VERSION = "1.0"

with open(os.path.join(os.path.dirname(__file__), "products.json")) as f:
    PRODUCTS = json.load(f)


@app.route("/")
def index():
    return render_template(
        "index.html",
        products=PRODUCTS,
        hostname=socket.gethostname(),
        version=VERSION,
    )


@app.route("/products")
def products():
    return jsonify(PRODUCTS)


@app.route("/health")
def health():
    return jsonify(status="ok", version=VERSION)


@app.route("/info")
def info():
    return jsonify(
        hostname=socket.gethostname(),
        version=VERSION,
        env=os.environ.get("APP_ENV", "dev"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
