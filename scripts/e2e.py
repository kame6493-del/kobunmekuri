"""ブラウザで実際に押して回る確認。
  python scripts/e2e.py            … dist をその場で配信して開く(買った人と同じ製品のビルド。課金は「準備中」)
  python scripts/e2e.py --dev URL  … 開発サーバー(疑似購入あり)で完全版の流れも回る
画面写真は scripts/e2e_out/ に置く。NG が1つでもあれば exit 1。"""
import functools
import http.server
import json
import os
import socketserver
import sys
import threading
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEV = "--dev" in sys.argv
OUT = os.path.join(HERE, "e2e_out", "dev" if DEV else "dist")
os.makedirs(OUT, exist_ok=True)
WORDS = json.load(open(os.path.join(ROOT, "dist" if not DEV else "public", "data", "words.json"), encoding="utf-8"))
errors, fails = [], []


def check(cond, msg):
    print(("OK  " if cond else "NG  ") + msg)
    if not cond:
        fails.append(msg)


def shot(page, name):
    page.screenshot(path=os.path.join(OUT, name + ".png"), full_page=True)


def find_word(page):
    """問題に出ている語を words.json から引く(見出し語 + 漢字表記で特定)"""
    w = page.locator(".q-prompt").first.evaluate("e => e.firstChild ? e.firstChild.textContent : ''")
    k = page.locator(".q-prompt small").inner_text() if page.locator(".q-prompt small").count() else ""
    for x in WORDS:
        if x["w"] == w and x["kanji"] == k:
            return x
    for x in WORDS:
        if x["w"] == w:
            return x
    return None


def answer_right(page, mode="mean"):
    if mode == "reverse":
        meaning = page.locator(".q-prompt").inner_text()
        cands = [x["w"] for x in WORDS if x["quiz"] == meaning]
        texts = page.locator(".choice").all_inner_texts()
        k = next(i for i, t in enumerate(texts) if t in cands)
    else:
        w = find_word(page)
        texts = page.locator(".choice").all_inner_texts()
        k = texts.index(w["quiz"])
    page.locator(".choice").nth(k).click()
    page.wait_for_selector(".verdict.good")


class Quiet(http.server.SimpleHTTPRequestHandler):
    # Windows はレジストリ次第で .js を text/plain で返し、ブラウザが読み込まない。種類を固定する
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript", ".css": "text/css", ".json": "application/json"}

    def log_message(self, *a):
        pass


def serve_dist():
    handler = functools.partial(Quiet, directory=os.path.join(ROOT, "dist"))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


httpd = None
if DEV:
    URL = sys.argv[sys.argv.index("--dev") + 1]
else:
    httpd, URL = serve_dist()

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="ja-JP")
    page = ctx.new_page()
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))

    # 1. はじめて開いた所
    page.goto(URL)
    page.wait_for_selector(".home")
    shot(page, "01_home_first")
    check(page.locator("text=はじめの10語をめくる").count() == 1, "初回は「はじめの10語」が出る")
    check(page.locator(".unlock").count() == 1, "無料のときは完全版の案内が出る")
    main = [w for w in WORDS if w["set"] == "main"]
    check(len(main) >= 300, f"本編の語数 {len(main)} >= 300")

    # 2. 10問。わざと全部1番を押す
    page.click("text=はじめの10語をめくる")
    wrong = 0
    ranks = []
    for i in range(10):
        page.wait_for_selector(".choice")
        w = find_word(page)
        ranks.append(w["rank"] if w else 999)
        page.locator(".choice").first.click()
        page.wait_for_selector(".verdict")
        if page.locator(".verdict.bad").count():
            wrong += 1
        if i == 0:
            shot(page, "02_quiz_answered")
        page.click(".bottom-bar .btn.primary")
    page.wait_for_selector(".result-hero")
    shot(page, "03_result")
    check(sorted(ranks) == list(range(1, 11)), f"はじめは重要度1〜10の語: {sorted(ranks)}")
    score = int(page.locator(".result-score b").inner_text())
    check(score == 10 - wrong, f"結果の正解数 {score} = 10 - 不正解 {wrong}")
    newn = page.locator(".result-moves li").nth(1).locator("b").inner_text()
    check(newn == f"{wrong}語", f"新しく苦手に入った数 {newn} = {wrong}")

    # 3. ホームに苦手の数
    page.click("text=ホームへ")
    page.wait_for_selector(".home")
    check(page.locator(".chip.ng b").inner_text() == str(wrong), "ホームの苦手の数")
    shot(page, "04_home_after")

    # 4. 苦手だけ: 2回続けて正解すると消える
    if wrong:
        for rnd in range(2):
            page.click(".tile.nigate")
            for _ in range(wrong):
                page.wait_for_selector(".choice")
                answer_right(page)
                page.click(".bottom-bar .btn.primary")
            page.wait_for_selector(".result-hero")
            page.click("text=ホームへ")
            page.wait_for_selector(".home")
        check(page.locator(".chip.ng b").inner_text() == "0", "2回続けて正解すると苦手が0になる")

    # 5. 意味から古語
    page.click("text=意味から古語")
    for i in range(10):
        page.wait_for_selector(".choice")
        answer_right(page, "reverse")
        if i == 0:
            shot(page, "05_reverse")
        page.click(".bottom-bar .btn.primary")
    page.wait_for_selector(".result-hero")
    check(page.locator(".result-score b").inner_text() == "10", "意味から古語: 全部正解できる(正解の判定が合っている)")
    page.click("text=ホームへ")

    # 6. 一問一答カード
    page.click("text=一問一答カード")
    page.wait_for_selector(".card-flip")
    shot(page, "06_card_front")
    page.click(".card-flip")
    page.wait_for_selector(".card-back")
    shot(page, "07_card_back")
    page.click("text=覚えてた")
    check(page.locator(".bottom-bar").count() == 1, "カードは自己採点のあと次へ進める")
    page.click(".topbar .icon")
    page.wait_for_selector(".home")

    # 7. 例文で当てる(無料のおためし5問)
    page.click("text=例文で当てる")
    page.wait_for_selector(".q-ex")
    shot(page, "08_example")
    check(page.locator(".q-ex mark").count() == 1, "例文の中の見出し語に印が付く")
    for i in range(5):
        page.wait_for_selector(".choice")
        page.locator(".choice").first.click()
        page.wait_for_selector(".verdict")
        if i == 0:
            shot(page, "09_example_answered")
            check(page.locator(".verdict .ex-src").count() >= 1, "例文の出典が出る")
        page.click(".bottom-bar .btn.primary")
    page.wait_for_selector(".result-hero")
    check(page.locator("text=例文モードのおためしは、ここまでです").count() == 1, "おためし5問のあと案内が出る")
    page.click("text=ホームへ")
    page.click("text=例文で当てる")
    page.wait_for_selector(".paywall")
    check(True, "おためしを使い切ると完全版の画面へ")
    shot(page, "10_paywall")
    if not DEV:
        check(page.locator("text=購入は準備中です").count() == 1, "キーが無い製品ビルドでは「購入は準備中」と出る(落ちない)")
    page.click(".topbar .icon")

    # 8. 単語の一覧と詳しい画面
    page.click("text=単語の一覧・さがす")
    page.wait_for_selector(".rows")
    page.fill(".search", "あはれ")
    page.wait_for_timeout(200)
    check(page.locator(".row").count() >= 1, "一覧で「あはれ」を探せる")
    page.locator(".row").first.click()
    page.wait_for_selector(".wd-head")
    shot(page, "11_detail")
    check(page.locator(".ex blockquote").count() >= 1, "詳しい画面に例文がある")
    page.click(".topbar .icon")
    page.fill(".search", "")
    page.locator(".row.locked").first.click()
    page.wait_for_selector(".paywall")
    check(True, "鍵の付いた語を押すと完全版の画面へ")
    page.click(".topbar .icon")
    page.click(".topbar .icon")

    # 9. 敬語セット(無料では一覧だけ)
    page.click("text=敬語セット")
    page.wait_for_selector(".setpage")
    check(page.locator(".unlock").count() == 1 or DEV, "無料では敬語セットの問題は完全版の案内")
    shot(page, "12_keigo_free")
    page.click(".topbar .icon")

    # 10. 設定: 試験日を入れると逆算が出る
    page.click(".gear")
    page.wait_for_selector(".settings")
    page.fill("input[type=date]", "2027-01-16")
    shot(page, "13_settings")
    page.click(".topbar .icon")
    page.wait_for_selector(".home")
    check(page.locator(".hero-label", has_text="試験まで").count() == 1, "試験日を入れると残り日数が出る")
    check("1日" in page.locator(".hero-sub").inner_text(), "1日に覚える語数が出る: " + page.locator(".hero-sub").inner_text())
    shot(page, "14_home_plan")

    # 11. 開き直しても記録が残る
    before = page.locator(".chips").inner_text()
    page.reload()
    page.wait_for_selector(".home")
    check(page.locator(".chips").inner_text() == before, "開き直しても記録が残る")

    # 12. 完全版の流れ(開発サーバーの疑似購入だけ)
    if DEV:
        page.click(".unlock")
        page.wait_for_selector(".paywall")
        page.click(".pw-cta .btn.primary")
        page.wait_for_selector(".home")
        check(page.locator(".unlock").count() == 0, "買ったら案内が消える")
        page.click("text=敬語セット")
        page.click("button:has-text('尊敬・謙譲・丁寧')")
        page.wait_for_selector(".choices.kind")
        texts = page.locator(".choice").all_inner_texts()
        check(texts == ["尊敬語", "謙譲語", "丁寧語"], f"敬語の種類の選択肢は固定の順: {texts}")
        shot(page, "15_keigo_kind")
        page.click(".topbar .icon")
        page.click(".topbar .icon")
        page.click("text=助動詞セット")
        page.click("text=例文で見分ける")
        page.wait_for_selector(".q-ex")
        shot(page, "16_jodoshi_example")
        page.click(".topbar .icon")
        page.click(".topbar .icon")
        page.click("text=例文で当てる")
        page.wait_for_selector(".q-ex")
        check(page.locator(".topbar h1").inner_text() == "例文で当てる", "完全版では例文モードが制限なし")

    b.close()
if httpd:
    httpd.shutdown()

errs = [e for e in errors if "favicon" not in e]
check(not errs, f"コンソールのエラー 0件 {errs[:3]}")
print("FAIL" if fails else "ALL OK", len(fails))
sys.exit(1 if fails else 0)
