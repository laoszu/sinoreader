import gzip
import json
import os
import re

import pymupdf

from pinyin_pdf import add_pinyin

def save(gz, data):
    # gzipped result stored next to the pdf (pdfs are immutable)
    tmp = f"{gz}.{os.getpid()}.tmp"
    with open(tmp, "wb") as f:
        f.write(gzip.compress(data.encode(), 6, mtime=0))
    os.replace(tmp, gz)

def ratios(path):
    gz = f"{path}.ratios.gz"
    if not os.path.exists(gz):
        with pymupdf.open(path) as d:
            save(gz, json.dumps([p.rect.height / p.rect.width for p in d]))
    with gzip.open(gz) as f:
        return json.load(f)

def render_svg(path, n, pinyin=False):
    gz = f"{path}.{n}.{int(bool(pinyin))}.svg.gz"
    if os.path.exists(gz):
        return gz
    with pymupdf.open(path) as d:
        page = d[n]
        if pinyin:
            add_pinyin(page)
        svg = page.get_svg_image(matrix=pymupdf.Identity, text_as_path=True)
    # glyphs are drawn twice (fill + stroke overlay, fake bold), so drop the overlay
    out, pos = [], 0
    while (start := svg.find("<use ", pos)) != -1:
        end = svg.find(">", start)

        if end == -1:
            break
        end += 1
        out.append(svg[pos:start])
        tag = svg[start:end]
        if tag.endswith("/>") and 'fill="none"' in tag:
            if svg.startswith("\n", end):
                end += 1
        else:
            out.append(tag) # plain <use> - kept
        pos = end
    out.append(svg[pos:])
    save(gz, "".join(out))
    return gz

def chars(path, n):
    gz = f"{path}.{n}.chars.gz"
    if os.path.exists(gz):
        return gz
    # [char, x, y, w, h, line], boxes as fractions of the page size
    with pymupdf.open(path) as d:
        page = d[n]
        w, h = page.rect.width, page.rect.height
        out, line_no = [], 0
        for block in page.get_text("rawdict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    for c in span["chars"]:
                        x0, y0, x1, y1 = c["bbox"]
                        out.append([c["c"], round(x0 / w, 5), round(y0 / h, 5),
                                    round((x1 - x0) / w, 5), round((y1 - y0) / h, 5), line_no])
                line_no += 1
    save(gz, json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    return gz