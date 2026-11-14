import pymupdf
from pypinyin import Style, pinyin

import config

def add_pinyin(page):
    fnt= pymupdf.Font(config.PINYIN_FONT)

    chars = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                for c in span["chars"]:
                    # first and last character of cjk
                    if "㐀" <= c["c"] <= "鿿":
                        chars.append((c["c"], pymupdf.Rect(c["bbox"])))
    if not chars:
        return
    labels = [p[0] for p in pinyin("".join(c for c, _ in chars), style=Style.TONE)]
    tw = pymupdf.TextWriter(page.rect)
    for label, (_, r) in zip(labels, chars):
        w = fnt.text_length(label, fontsize=config.PINYIN_SIZE)
        tw.append(((r.x0 + r.x1 - w) / 2, r.y0 - config.PINYIN_OFFSET), label, font=fnt, fontsize=config.PINYIN_SIZE)
    tw.write_text(page, color=config.PINYIN_COLOR)
