# -*- coding: utf-8 -*-
"""例文の照合用に、ウィキソース日本語版から古典本文(著作権切れ)を取ってくる。
python research/r2_corpus.py → research/corpus/<作品>/<ページ>.txt
本文はアプリに丸ごと入れない。例文として引いた1文が本当に原文にあるかを機械で確かめるために使う。"""
import json, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "corpus")
UA = {"User-Agent": "kobunmekuri-research/0.1 (personal study app; contact kame6493@gmail.com)"}
WORKS = ["源氏物語", "枕草子", "徒然草", "竹取物語", "伊勢物語", "土佐日記", "方丈記", "更級日記", "平家物語", "大鏡", "宇治拾遺物語",
         "今昔物語集", "紫式部日記", "蜻蛉日記", "堤中納言物語", "十訓抄", "沙石集", "大和物語", "和泉式部日記", "無名草子", "落窪物語",
         "発心集", "古本説話集", "讃岐典侍日記", "十六夜日記", "うつほ物語", "宇津保物語", "浜松中納言物語", "とりかへばや物語", "夜の寝覚", "狭衣物語", "雨月物語", "奥の細道", "おくのほそ道"]


def get(url):
    for i in range(6):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8")
        except Exception as ex:
            print("  retry", i, ex)
            time.sleep(3 + i * 2)
    return None


def api(params):
    s = get("https://ja.wikisource.org/w/api.php?" + urllib.parse.urlencode(dict(params, format="json")))
    return json.loads(s) if s else {}


def clean(t):
    t = re.sub(r"<ref[^>]*?/>", "", t)
    t = re.sub(r"<ref.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"'''?", "", t)
    return t


pages_all = {}
for w in WORKS:
    d = api({"action": "query", "list": "allpages", "apprefix": w, "aplimit": 500})
    ps = [p["title"] for p in d.get("query", {}).get("allpages", [])]
    ps = [p for p in ps if p == w or p.startswith(w + "/") or p.startswith(w + " ")]
    pages_all[w] = ps
    print(w, len(ps), flush=True)
    os.makedirs(os.path.join(OUT, w), exist_ok=True)
    for p in ps:
        fn = os.path.join(OUT, w, re.sub(r'[\\/:*?"<>|]', "_", p) + ".txt")
        if os.path.exists(fn):
            continue
        raw = get("https://ja.wikisource.org/w/index.php?" + urllib.parse.urlencode({"title": p, "action": "raw"}))
        if raw is None:
            print("  FAIL", p)
            continue
        open(fn, "w", encoding="utf-8").write(clean(raw))
        time.sleep(0.4)
json.dump(pages_all, open(os.path.join(HERE, "corpus_pages.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
