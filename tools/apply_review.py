# -*- coding: utf-8 -*-
"""検査(2回目)の直しを research/batches に当てる。python tools/apply_review.py
- research/review/review_*.json を読み、rank ごとに field を書き換える
- 当てる前の版を research/batches_before_review/ に1度だけ控える
- 当てた数を分類別に research/review/applied_summary.json へ書く
- 最後に validate を通す(エラーがあれば exit 1)"""
import glob, json, os, shutil, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from validate import check_file  # noqa: E402

B = os.path.join(ROOT, "research", "batches")
BK = os.path.join(ROOT, "research", "batches_before_review")
if not os.path.isdir(BK):
    shutil.copytree(B, BK)

files = {}
by_rank = {}
for p in sorted(glob.glob(os.path.join(BK, "words_*.json"))):
    items = json.load(open(p, encoding="utf-8"))
    files[os.path.basename(p)] = items
    for it in items:
        by_rank[it["rank"]] = it

# 敬語・助動詞のセット({"kind","items"} の形。rank はファイルごとの番号)
sets = {}
for name, kind in (("set_keigo.json", "keigo"), ("set_jodoshi.json", "jodoshi")):
    src = os.path.join(BK, name)
    if not os.path.exists(src):
        shutil.copy(os.path.join(B, name), src)
    sets[kind] = (name, json.load(open(src, encoding="utf-8")))

applied, skipped = [], []
for rp in sorted(glob.glob(os.path.join(ROOT, "research", "review", "review_*.json"))):
    for fx in json.load(open(rp, encoding="utf-8")):
        f = fx.get("field")
        if fx.get("set") in sets:
            it = next((x for x in sets[fx["set"]][1]["items"] if x["rank"] == fx.get("rank")), None)
        else:
            it = by_rank.get(fx.get("rank"))
        if not it or (fx.get("w") and fx["w"] != it["w"]):
            skipped.append((os.path.basename(rp), fx.get("rank"), f, "見出しが合わない"))
            continue
        if f in ("means", "quiz", "note", "pos", "cat", "kind", "plain", "conn", "exs"):
            it[f] = fx["new"]
        elif f == "ex":
            it["ex"] = fx["new"]
            it.pop("noex", None)
        elif f in ("ex.tr", "ex.sense"):
            if "ex" not in it:
                skipped.append((os.path.basename(rp), fx["rank"], f, "例文が無い"))
                continue
            it["ex"][f[3:]] = fx["new"]
        else:
            skipped.append((os.path.basename(rp), fx.get("rank"), f, "知らない field"))
            continue
        applied.append({"set": fx.get("set", "main"), "rank": it["rank"], "w": it["w"], "field": f, "reason": fx.get("reason", ""), "file": os.path.basename(rp)})

for name, items in files.items():
    json.dump(items, open(os.path.join(B, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

for kind, (name, data) in sets.items():
    json.dump(data, open(os.path.join(B, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
errs = []
for name in list(files) + [n for n, _ in sets.values()]:
    errs += check_file(os.path.join(B, name))[1]
summary = {"applied": len(applied), "words": len({(a["set"], a["rank"]) for a in applied}), "by_field": Counter(a["field"] for a in applied), "skipped": skipped}
json.dump({**summary, "list": applied}, open(os.path.join(ROOT, "research", "review", "applied_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False))
for e in errs:
    print("NG", e)
sys.exit(1 if errs else 0)
