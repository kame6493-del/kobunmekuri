# -*- coding: utf-8 -*-
"""research/batches/*.json をまとめて public/data/words.json を作る。python tools/build_data.py
- 例文の出典(作品・巻/段)は、執筆者の申告ではなく索引(sentences.jsonl)の sid から機械で付ける
- 重複した見出し(同じ語・同じ品詞)は重要度の高い方だけ残す
- 本編は rank を詰め直して 1..N にする(無料の範囲が「上位150語」になるように)"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from validate import check_file  # noqa: E402

S = {}
for l in open(os.path.join(ROOT, "research", "sentences.jsonl"), encoding="utf-8"):
    s = json.loads(l)
    S[s["id"]] = s

# 同じ意味の見出しが二重になっている物(先に出た方へまとめる)
DROP = {("あながち", "副詞"), ("あながちに", "副詞"), ("なかなかに", "副詞")}


def src_of(sid):
    s = S[sid]
    loc = s["loc"]
    if not loc:
        return s["work"]
    if s["work"] == "竹取物語":
        return f"竹取物語({loc})"
    return f"{s['work']}・{loc}"


def conv_ex(e):
    return {"text": e["text"], "hit": e["hit"], "tr": e["tr"], "sense": e.get("sense", 0), "src": src_of(e["sid"])}


def main():
    errors = []
    main_items, keigo, jodoshi = [], [], []
    for p in sorted(glob.glob(os.path.join(ROOT, "research", "batches", "*.json"))):
        items, errs = check_file(p)
        errors += errs
        data = json.load(open(p, encoding="utf-8"))
        kind = data.get("kind", "words") if isinstance(data, dict) else "words"
        {"words": main_items, "keigo": keigo, "jodoshi": jodoshi}[kind].extend(items)
    if errors:
        for e in errors:
            print("NG", e)
        sys.exit(1)

    out = []
    seen = set()
    main_items.sort(key=lambda x: x["rank"])
    n = 0
    for it in main_items:
        k = (it["w"], it["pos"])
        # 例文が本文に見つからなかった語は入れない(全語を例文つきにする。代わりの語を words_09.json に足した)
        if k in seen or k in DROP or it.get("noex"):
            continue
        seen.add(k)
        n += 1
        exs = it.get("exs") or ([it["ex"]] if it.get("ex") else [])
        out.append({"id": "m%03d" % n, "set": "main", "rank": n, "w": it["w"], "kanji": it.get("kanji", ""), "pos": it["pos"], "cat": it["cat"],
                    "means": it["means"], "quiz": it["quiz"], "note": it["note"], "ex": [conv_ex(e) for e in exs]})
    for prefix, items, setname in (("k", keigo, "keigo"), ("j", jodoshi, "jodoshi")):
        for i, it in enumerate(sorted(items, key=lambda x: x["rank"]), 1):
            exs = it.get("exs") or ([it["ex"]] if it.get("ex") else [])
            # 「さぶらふ(丁寧)」「なり(断定)」のような見出しは答えを書いてしまうので、括弧は見出しから外す。
            # 敬語: 種類(尊敬・謙譲・丁寧)は kind に入っているので捨てる。四段/下二段は見分けの手がかりなので漢字の欄に残す。
            # 助動詞: 接続を漢字の欄に出して、同じ形(なり・たり)を接続で見分けさせる。
            head, kanji = it["w"], it.get("kanji", "")
            m = re.match(r"^(.+?)[(（](.+)[)）]$", head)
            if m:
                head = m.group(1)
                if setname == "keigo" and m.group(2) not in ("尊敬", "謙譲", "丁寧"):
                    kanji = f"{kanji}・{m.group(2)}" if kanji else m.group(2)
            if setname == "jodoshi":
                kanji = ("接続: " + it["conn"]) if it.get("conn") else kanji
            w = {"id": "%s%02d" % (prefix, i), "set": setname, "rank": i, "w": head, "kanji": kanji, "pos": it["pos"],
                 "cat": it.get("kind", "その他"), "means": it["means"], "quiz": it["quiz"], "note": it["note"], "ex": [conv_ex(e) for e in exs]}
            for f in ("kind", "plain", "conn"):
                if it.get(f):
                    w[f] = it[f]
            out.append(w)
    os.makedirs(os.path.join(ROOT, "public", "data"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "public", "data", "words.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    by = {}
    for w in out:
        by[w["set"]] = by.get(w["set"], 0) + 1
    noex = [w["w"] for w in out if not w["ex"]]
    print("words.json", by, "例文なし", len(noex), noex[:30])


if __name__ == "__main__":
    main()
