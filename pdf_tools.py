import pymupdf

import config
from pinyin_pdf import add_pinyin

def ratios(path):
    with pymupdf.open(path) as d:
        return [p.rect.height / p.rect.width for p in d]

def render(path, n, zoom, pinyin=False):
    with pymupdf.open(path) as d:
        page = d[n]
        if pinyin:
            add_pinyin(page)
        scale = config.RENDER_WIDTH * zoom / 100 / page.rect.width
        return page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).tobytes("png")

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