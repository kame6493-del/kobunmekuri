# -*- coding: utf-8 -*-
"""見出し語ごとに、本文から例文の候補を抜き出す。→ research/candidates.json  {rank: [ {sid, work, loc, text, hit} ]}"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
S = [json.loads(l) for l in open(os.path.join(HERE, "sentences.jsonl"), encoding="utf-8")]
W = json.load(open(os.path.join(HERE, "words_order.json"), encoding="utf-8"))

ROWS = ["あいうえお", "かきくけこ", "がぎぐげご", "さしすせそ", "ざじずぜぞ", "たちつてと", "だぢづでど", "なにぬねの", "はひふへほ", "ばびぶべぼ", "まみむめも", "やゆよ", "らりるれろ", "わゐうゑを"]
PRI = {"枕草子": 3.0, "徒然草": 3.0, "源氏物語": 2.0, "竹取物語": 2.5, "更級日記": 2.5, "方丈記": 2.5, "紫式部日記": 1.8, "土佐日記": 1.6,
       "和泉式部日記": 1.4, "おくのほそ道": 1.6, "大鏡": 1.3, "蜻蛉日記": 1.2, "十六夜日記": 1.0}


def row_of(ch):
    for r in ROWS:
        if ch in r:
            return r
    return ch


def patterns(w, kanji, pos):
    forms = [w] + [k for k in re.split(r"[・]", kanji) if k]
    pats = []
    for f in forms:
        if pos == "形容詞" and f[-1] in "しじ":
            b = re.escape(f[:-1])
            if len(f[:-1]) >= 2 or not re.fullmatch(r"[ぁ-ん]+", f[:-1]):
                pats.append(b + "(?:" + re.escape(f[-1]) + "?(?:く|う|き|けれ|から|かり|かる|かれ|さ|げ)|" + re.escape(f[-1]) + ")")
        elif pos == "形容動詞" and f.endswith("なり"):
            b = f[:-2]
            if len(b) >= 2 or not re.fullmatch(r"[ぁ-ん]+", b):
                pats.append(re.escape(b) + "(?:なら|なり|なる|なれ|に)")
        elif pos == "動詞" and len(f) >= 2:
            stem, last = f[:-1], f[-1]
            if len(stem) >= 2 or not re.fullmatch(r"[ぁ-ん]+", stem):
                pats.append(re.escape(stem) + "[" + row_of(last) + "]")
        else:
            if len(f) >= 2:
                pats.append(re.escape(f.replace("〜", "")))
    return pats


out = {}
for w in W:
    pats = patterns(w["w"], w["kanji"], w["pos"])
    if not pats:
        out[w["rank"]] = []
        continue
    rx = re.compile("|".join(pats))
    hits = []
    for s in S:
        m = rx.search(s["text"])
        if m:
            L = len(s["text"])
            score = PRI.get(s["work"], 1) - abs(L - 32) / 30.0
            if L > 90:
                score -= 3
            hits.append((score, s, m.group(0)))
    hits.sort(key=lambda x: -x[0])
    # 作品が偏らないように、1作品あたり最大4文
    per, picked = {}, []
    for sc, s, h in hits:
        if per.get(s["work"], 0) >= 4:
            continue
        per[s["work"]] = per.get(s["work"], 0) + 1
        picked.append({"sid": s["id"], "work": s["work"], "loc": s["loc"], "text": s["text"], "hit": h})
        if len(picked) >= 14:
            break
    out[w["rank"]] = picked
json.dump(out, open(os.path.join(HERE, "candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
none = [w["w"] for w in W if not out[w["rank"]]]
few = [w["w"] for w in W if 0 < len(out[w["rank"]]) < 3]
print("words", len(W), "none", len(none), none)
print("few", len(few), few)
