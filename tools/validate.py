# -*- coding: utf-8 -*-
"""単語データの機械検査。python tools/validate.py research/batches/words_01.json [...]
引数なしなら research/batches/*.json を全部見る。
- 例文 ex.text が、索引の文(sid)の連続した一部であること(=原文に実在する)
- ex.hit が ex.text の中にあること
- 必須項目・字数・カテゴリ・意味の番号
エラーがあれば一覧を出して exit 1。"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = {}
for l in open(os.path.join(ROOT, "research", "sentences.jsonl"), encoding="utf-8"):
    s = json.loads(l)
    S[s["id"]] = s
CATS = ["感動・趣", "賞賛・すぐれる", "美・優雅", "かわいい・いとしい", "不快・嫌悪", "つらい・悲しい", "不安・心配", "驚き・あきれ", "身分・高貴",
        "程度・強調", "時・時間", "様子・状態", "性格・態度", "恋愛・人間関係", "宗教・死・出家", "言葉・音・手紙", "行動・動作", "心・思考", "呼応・否定・疑問", "その他"]
POS = ["動詞", "形容詞", "形容動詞", "名詞", "副詞", "連体詞", "感動詞", "連語", "接続詞", "代名詞", "接続助詞", "助動詞"]
BAD = re.compile(r"\*\*|[\U0001F300-\U0001FAFF☀-➿]")


def check_ex(e, where, errs):
    for k in ("sid", "text", "hit", "tr"):
        if k not in e:
            errs.append(f"{where}: ex に {k} が無い")
            return
    s = S.get(e["sid"])
    if not s:
        errs.append(f"{where}: sid {e['sid']} が索引に無い")
        return
    if e["text"] not in s["text"]:
        errs.append(f"{where}: ex.text が sid {e['sid']} の文の一部ではない\n    ex : {e['text']}\n    原文: {s['text']}")
    if e["hit"] not in e["text"]:
        errs.append(f"{where}: hit「{e['hit']}」が ex.text に無い")
    if len(e["text"]) > 80:
        errs.append(f"{where}: ex.text が長い({len(e['text'])}字)")
    if not (4 <= len(e["tr"]) <= 120):
        errs.append(f"{where}: 訳の長さ {len(e['tr'])}")


def check_file(path):
    errs = []
    data = json.load(open(path, encoding="utf-8"))
    kind = data.get("kind", "words") if isinstance(data, dict) else "words"
    items = data["items"] if isinstance(data, dict) else data
    for it in items:
        where = f"{os.path.basename(path)} {it.get('rank', '?')} {it.get('w', '?')}"
        if BAD.search(json.dumps(it, ensure_ascii=False)):
            errs.append(f"{where}: 太字記法か絵文字がある")
        for k in ("w", "pos", "means", "quiz", "note"):
            if k not in it:
                errs.append(f"{where}: {k} が無い")
        if it.get("pos") not in POS:
            errs.append(f"{where}: 品詞 {it.get('pos')}")
        if kind == "words" and it.get("cat") not in CATS:
            errs.append(f"{where}: カテゴリ {it.get('cat')}")
        ms = it.get("means", [])
        if not (1 <= len(ms) <= 4) or any(not m or len(m) > 20 for m in ms):
            errs.append(f"{where}: means の数か長さ {ms}")
        if len(it.get("quiz", "")) > 14:
            errs.append(f"{where}: quiz が長い {it.get('quiz')}")
        if not (30 <= len(it.get("note", "")) <= 180):
            errs.append(f"{where}: note の長さ {len(it.get('note', ''))}")
        exs = it.get("exs") or ([it["ex"]] if it.get("ex") else [])
        if not exs and not it.get("noex"):
            errs.append(f"{where}: 例文が無い(見つからなければ noex: true)")
        for i, e in enumerate(exs):
            check_ex(e, f"{where} 例{i + 1}", errs)
            if kind == "words" and not (0 <= e.get("sense", -1) < len(ms)):
                errs.append(f"{where}: ex.sense {e.get('sense')} が means の範囲外")
    return items, errs


if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "research", "batches", "*.json")))
    allerr, n = [], 0
    for p in paths:
        items, errs = check_file(p)
        n += len(items)
        allerr += errs
    for e in allerr:
        print("NG", e)
    print(f"{len(paths)} files, {n} items, {len(allerr)} errors")
    sys.exit(1 if allerr else 0)
