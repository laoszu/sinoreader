import os
import uuid

import pymupdf
from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

import config
import pdf_tools
from dictionary import lookup

UPLOADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOADS, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_MB * 1024 * 1024

def pdf_path(doc_id):
    try:
        valid = uuid.UUID(doc_id).hex == doc_id
    except ValueError:
        valid = False
    path = os.path.join(UPLOADS, doc_id + ".pdf")
    if not valid or not os.path.isfile(path):
        abort(404)
    return path

def clamp(z):
    return max(config.MIN_ZOOM, min(config.MAX_ZOOM, round(z)))

def zoom_arg():
    return clamp(request.args.get("zoom", 100, type=int))

def cached(resp):
    resp.headers["Cache-Control"] = "private, max-age=3600"
    return resp

@app.route("/")
def home():
    return render_template("picker.html")

@app.errorhandler(413)
def too_large(_):
    return render_template("picker.html", error=f"File is too large (max {config.MAX_UPLOAD_MB} MB)."), 413

@app.post("/upload")
def upload():
    f = request.files.get("file")
    data = f.read() if f else b""
    app.logger.info("upload: name=%r type=%r bytes=%d", f and f.filename, f and f.mimetype, len(data))
    if not data:
        return render_template("picker.html", error="No file received - choose a PDF and try again."), 400
    try:
        with pymupdf.open(stream=data, filetype="pdf") as d:
            if d.page_count == 0:
                raise ValueError("empty")
    except Exception:
        return render_template("picker.html", error="That file is not a valid PDF."), 400

    doc_id = uuid.uuid4().hex
    with open(os.path.join(UPLOADS, doc_id + ".pdf"), "wb") as out:
        out.write(data)
    return redirect(url_for("view", doc_id=doc_id))

@app.route("/doc/<doc_id>")
def view(doc_id):
    zoom = zoom_arg()
    return render_template(
        "viewer.html",
        doc=doc_id,
        pages=list(enumerate(pdf_tools.ratios(pdf_path(doc_id)))),
        zoom=zoom,
        pinyin=request.args.get("pinyin", 0, type=int),
        lookup_len=config.LOOKUP_MAX_LEN,
        zoom_in=clamp(zoom * config.ZOOM_STEP),
        zoom_out=clamp(zoom / config.ZOOM_STEP),
    )

@app.route("/doc/<doc_id>/page/<int:n>.png")
def page_image(doc_id, n):
    try:
        png = pdf_tools.render(pdf_path(doc_id), n, zoom_arg(), request.args.get("pinyin", 0, type=int))
    except IndexError:
        abort(404)
    return cached(app.response_class(png, mimetype="image/png"))

@app.route("/doc/<doc_id>/page/<int:n>/chars.json")
def page_chars(doc_id, n):
    try:
        return cached(jsonify(pdf_tools.chars(pdf_path(doc_id), n)))
    except IndexError:
        abort(404)

@app.route("/lookup")
def lookup_api():
    return jsonify(lookup(request.args.get("q", "")))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))