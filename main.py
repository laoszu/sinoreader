import os

from flask import Flask, abort, send_from_directory

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC_FILES = {"index.html", "viewer.js"}

app = Flask(__name__, static_folder=None)

@app.route("/")
def home():
    return send_from_directory(ROOT, "index.html")

@app.route("/<path:path>")
def static_file(path):
    if path in PUBLIC_FILES:
        return send_from_directory(ROOT, path)
    abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))