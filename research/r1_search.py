# -*- coding: utf-8 -*-
"""App Store 検索「古文単語」「古文」「古典 単語」の上位20本の課金・語数・不満を集める。
python research/r1_search.py  → research/r1_raw.json と research/r1_table.md"""
import html, json, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36", "Accept-Language": "ja"}
TERMS = ["古文単語", "古文", "古典 単語"]


def fetch(url):
    for i in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8")
        except Exception as ex:
            print("retry", url, ex)
            time.sleep(2)
    return ""


apps = {}
for t in TERMS:
    u = "https://itunes.apple.com/search?" + urllib.parse.urlencode({"term": t, "country": "jp", "entity": "software", "limit": 20, "lang": "ja_jp"})
    d = json.loads(fetch(u) or "{}")
    for rank, r in enumerate(d.get("results", []), 1):
        k = str(r["trackId"])
        a = apps.setdefault(k, {"id": k, "name": r["trackName"], "seller": r.get("sellerName", ""), "price": r.get("formattedPrice", ""),
                                "ratings": r.get("userRatingCount", 0), "rating": round(r.get("averageUserRating", 0), 2),
                                "released": r.get("releaseDate", "")[:10], "updated": r.get("currentVersionReleaseDate", "")[:10],
                                "genre": r.get("primaryGenreName", ""), "desc": r.get("description", ""), "ranks": {}})
        a["ranks"][t] = rank
    time.sleep(1)

MONEY = re.compile(r"(¥|円|有料|無料|プレミアム|サブスク|課金|Pro|PRO|プラン|広告|買い切り|トライアル|月額|年額|解放|購入)")
for k, a in apps.items():
    s = fetch("https://apps.apple.com/jp/app/id%s" % k)
    pairs = re.findall(r'class="text-pair[^"]*"><span>(.*?)</span>\s*<span>(.*?)</span>', s)
    iap = []
    for x, y in pairs:
        tt = (html.unescape(x).strip(), html.unescape(y).strip())
        if "¥" in tt[1] and tt not in iap:
            iap.append(tt)
    if not iap:
        # 新しい形のページ: JSON の中に "In-App Purchases" の項目が入っている
        for m in re.finditer(r'"name":"([^"]{1,60})","price":"(¥[\d,]+)"', s):
            tt = (m.group(1), m.group(2))
            if tt not in iap:
                iap.append(tt)
    a["iap"] = ["%s %s" % t for t in iap]
    a["page_len"] = len(s)
    nums = re.findall(r"([0-9,０-９]{3,6})\s*(?:語|単語|個の単語)", a["desc"])
    a["word_counts"] = sorted({int(n.replace(",", "").translate(str.maketrans("０１２３４５６７８９", "0123456789"))) for n in nums})
    a["desc_money"] = [l.strip() for l in a["desc"].splitlines() if MONEY.search(l) and len(l.strip()) < 160][:12]
    # レビュー(新しい順、最大2ページ)
    revs = []
    for page in (1, 2):
        j = fetch("https://itunes.apple.com/jp/rss/customerreviews/page=%d/id=%s/sortby=mostrecent/json" % (page, k))
        try:
            ents = json.loads(j)["feed"].get("entry", [])
        except Exception:
            ents = []
        if isinstance(ents, dict):
            ents = [ents]
        for e in ents:
            if "im:rating" not in e:
                continue
            revs.append({"stars": int(e["im:rating"]["label"]), "title": e["title"]["label"], "body": e["content"]["label"][:300], "ver": e.get("im:version", {}).get("label", "")})
        if len(ents) < 50:
            break
        time.sleep(0.5)
    a["reviews"] = revs
    print(a["name"][:30], a["ratings"], len(a["iap"]), len(revs), flush=True)
    time.sleep(0.8)

json.dump(list(apps.values()), open(os.path.join(HERE, "r1_raw.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("apps", len(apps))
