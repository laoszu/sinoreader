import os
import sqlite3

import config

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config.DICT_DB)
_cache = {"mtime": None, "index": {}}

def _forms(word):
    # 并（且） => 并且 and 并
    base, _, rest = word.strip().partition("（")
    return {base + rest[:-1], base} if rest.endswith("）") else {word.strip()}

def _index():
    # chnage forms to entries, reloaded when the db file changes
    if not os.path.isfile(_path):
        return {}
    mtime = os.path.getmtime(_path)
    if _cache["mtime"] != mtime:
        index = {}
        with sqlite3.connect(_path) as db:
            db.row_factory = sqlite3.Row
            for row in db.execute("SELECT simplified, traditional, pinyin, polish, english FROM custom_dict"):
                entry = {k: row[k] or "" for k in row.keys()}
                for word in (row["simplified"], row["traditional"]):
                    for form in _forms(word) if word else ():
                        if entry not in index.setdefault(form, []):
                            index[form].append(entry)
        _cache.update(mtime=mtime, index=index)
    return _cache["index"]

def lookup(text, pos=0):
    # every prefix of text found in the dictionary, longest first
    index = _index()
    results = []
    for n in range(min(len(text), config.LOOKUP_MAX_LEN), 0, -1):
        for start in range(max(0, pos - n+1), min(pos + 1, len(text)-n+1)):
            word = text[start:start + n]
            if word in index:
                results.append({"word": word, "entries": index[word]})

    #print(results)
    return results