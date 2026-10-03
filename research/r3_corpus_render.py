# -*- coding: utf-8 -*-
"""raw が空(Page: 名前空間から差し込む作り)の頁と、くの字点などのテンプレートが消えた頁を、描画後の HTML から取り直す。
リンク先の頁(版ごとの目次から辿れる本文)も1段だけ辿る。→ research/corpus_r/<作品>/<頁>.txt"""
import html as H, json, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "corpus_r")
UA = {"User-Agent": "kobunmekuri-research/0.1 (personal study app; contact kame6493@gmail.com)"}


def get(url):
    for i in range(6):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8")
        except Exception as ex:
            print("  retry", i, ex, flush=True)
            time.sleep(3 + i * 2)
    return None


def parse(title):
    s = get("https://ja.wikisource.org/w/api.php?" + urllib.parse.urlencode({"action": "parse", "page": title, "prop": "text|links", "format": "json", "redirects": 1}))
    if not s:
        return None, []
    d = json.loads(s)
    if "parse" not in d:
        return None, []
    p = d["parse"]
    return p["text"]["*"], [l["*"] for l in p.get("links", []) if l.get("ns") == 0 and l.get("exists") is not None]


def text_of(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", h, flags=re.S)
    h = re.sub(r'<span class="mw-editsection.*?</span>\s*</span>', "", h, flags=re.S)
    h = re.sub(r"<rt>.*?</rt>|<rp>.*?</rp>", "", h, flags=re.S)
    h = re.sub(r"<br\s*/?>|</p>|</div>|</h\d>|</li>", "\n", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = H.unescape(h)
    h = h.replace("〳〵", "＊").replace("／＼", "＊")
    return re.sub(r"\n{3,}", "\n\n", h)


ROOTS = {
    "伊勢物語": ["伊勢物語"], "土佐日記": ["土佐日記 (國文大觀)"], "方丈記": ["方丈記 (群書類從)", "方丈記 (國文大觀)"],
    "大鏡": ["大鏡 (國文大觀)"], "平家物語": ["平家物語 (國文大觀)", "平家物語 (校註日本文學大系)"], "今昔物語集": ["今昔物語集 (國史大系)"],
    "蜻蛉日記": ["蜻蛉日記 (國文大觀)"], "堤中納言物語": ["堤中納言物語"], "和泉式部日記": ["和泉式部日記"], "徒然草": ["徒然草 (校註日本文學大系)", "徒然草 (國文大觀)"],
    "竹取物語": ["竹取物語 (國民文庫)"], "更級日記": ["更級日記"], "宇治拾遺物語": ["宇治拾遺物語"], "紫式部日記": ["紫式部日記 (渋谷栄一校訂)"],
    "おくのほそ道": ["おくのほそ道"], "十六夜日記": ["十六夜日記 (國文大觀)"],
}
for work, roots in ROOTS.items():
    os.makedirs(os.path.join(OUT, work), exist_ok=True)
    seen = set()
    queue = [(r, 0) for r in roots]
    while queue:
        t, depth = queue.pop(0)
        if t in seen:
            continue
        seen.add(t)
        fn = os.path.join(OUT, work, re.sub(r'[\\/:*?"<>|]', "_", t) + ".txt")
        if os.path.exists(fn):
            continue
        h, links = parse(t)
        if h is None:
            print("  none", t)
            continue
        txt = text_of(h)
        open(fn, "w", encoding="utf-8").write(txt)
        print(work, t, len(txt), len(links), flush=True)
        if depth == 0:
            for l in links:
                if l.startswith(t + "/") or (l.startswith(work) and "/" in l):
                    queue.append((l, 1))
        time.sleep(0.4)
