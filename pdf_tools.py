import re

import pymupdf

from pinyin_pdf import add_pinyin

def ratios(path):
    with pymupdf.open(path) as d:
        return [p.rect.height / p.rect.width for p in d]

def render_svg(path, n, pinyin=False):
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
    return "".join(out)

def chars(path, n):
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
        return out