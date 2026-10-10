"""ブラウザで実際に押して回る確認。
  python scripts/e2e.py            … dist をその場で配信して開く(買った人と同じ製品のビルド。課金は「準備中」)
  python scripts/e2e.py --dev URL  … 開発サーバー(疑似購入あり)で完全版の流れも回る
幅 375 と 430 の両方で回る。画面写真は scripts/e2e_out/<dist|dev>/<幅>/ に置く。NG が1つでもあれば exit 1。"""
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


CUR = {"out": OUT, "w": 0}


def shot(page, name):
    page.screenshot(path=os.path.join(CUR["out"], name + ".png"), full_page=True)
    sw = page.evaluate("document.documentElement.scrollWidth")
    check(sw <= CUR["w"], f"[{CUR['w']}] {name}: 横はみ出しなし ({sw})")


def num(t):
    return int("".join(ch for ch in t if ch.isdigit()) or 0)


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
        texts = page.locator(".choice-t").all_inner_texts()
        k = next(i for i, t in enumerate(texts) if t in cands)
    else:
        w = find_word(page)
        texts = page.locator(".choice-t").all_inner_texts()
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


def tab(page, name):
    page.click(f".tabbar button:has-text('{name}')")


def run(p, width, height):
    CUR["w"] = width
    CUR["out"] = os.path.join(OUT, str(width))
    os.makedirs(CUR["out"], exist_ok=True)
    W = f"[{width}] "
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": width, "height": height}, device_scale_factor=2, locale="ja-JP")
    page = ctx.new_page()
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))

    # 1. はじめて開いた所
    page.goto(URL)
    page.wait_for_selector(".home")
    shot(page, "01_home_first")
    check("はじめの10語" in page.locator(".tile.today").inner_text(), W + "初回は「重要語からめくる」に「はじめの10語」が出る")
    check(page.locator(".unlock-row").count() == 1, W + "無料のときは完全版の案内が出る")
    check(page.locator(".tabbar button").count() == 5, W + "下のタブが5つ")
    main = [w for w in WORDS if w["set"] == "main"]
    check(len(main) >= 300, f"本編の語数 {len(main)} >= 300")

    # 2. 10問。わざと全部1番を押す
    page.click(".tile.today")
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
    check(sorted(ranks) == list(range(1, 11)), W + f"はじめは重要度1〜10の語: {sorted(ranks)}")
    score = num(page.locator(".res-ok").inner_text())
    check(score == 10 - wrong, W + f"結果の正解数 {score} = 10 - 不正解 {wrong}")
    newn = num(page.locator(".res-new").inner_text())
    check(newn == wrong, W + f"新しく苦手に入った数 {newn} = {wrong}")

    # 3. ホームに苦手の数
    page.click("text=ホームに戻る")
    page.wait_for_selector(".home")
    check(num(page.locator(".tile.nigate .tile-num").inner_text()) == wrong, W + "ホームの苦手の数")
    shot(page, "04_home_after")

    # 4. 苦手: 2回続けて正解すると消える
    if wrong:
        for rnd in range(2):
            tab(page, "苦手")
            page.wait_for_selector(".start-nigate")
            if rnd == 0:
                check(page.locator(".wrow").count() == wrong, W + "苦手の一覧の数")
                shot(page, "04b_nigate")
            page.click(".start-nigate")
            for _ in range(wrong):
                page.wait_for_selector(".choice")
                answer_right(page)
                page.click(".bottom-bar .btn.primary")
            page.wait_for_selector(".result-hero")
            page.click("text=ホームに戻る")
            page.wait_for_selector(".home")
        check(num(page.locator(".tile.nigate .tile-num").inner_text()) == 0, W + "2回続けて正解すると苦手が0になる")
        tab(page, "苦手")
        check(page.locator("text=苦手がありません").count() == 1, W + "苦手0の画面")
        tab(page, "ホーム")

    # 5. 意味から古語
    tab(page, "学習")
    page.click(".cardrow:has-text('意味から古語')")
    for i in range(10):
        page.wait_for_selector(".choice")
        answer_right(page, "reverse")
        if i == 0:
            shot(page, "05_reverse")
        page.click(".bottom-bar .btn.primary")
    page.wait_for_selector(".result-hero")
    check(num(page.locator(".res-ok").inner_text()) == 10, W + "意味から古語: 全部正解できる(正解の判定が合っている)")
    page.click("text=ホームに戻る")
    page.wait_for_selector(".home")

    # 6. 一問一答カード
    tab(page, "学習")
    page.click(".cardrow:has-text('一問一答カード')")
    page.wait_for_selector(".card-flip")
    shot(page, "06_card_front")
    page.click(".card-flip")
    page.wait_for_selector(".card-back")
    shot(page, "07_card_back")
    page.click("text=わかった")
    check(page.locator(".bottom-bar").count() == 1, W + "カードは自己採点のあと次へ進める")
    page.click(".topbar .icon")
    page.wait_for_selector(".study")

    # 7. 例文で当てる(無料のおためし5問)
    page.click(".cardrow:has-text('例文で当てる')")
    page.wait_for_selector(".q-ex")
    shot(page, "08_example")
    check(page.locator(".q-ex mark").count() == 1, W + "例文の中の見出し語に印が付く")
    for i in range(5):
        page.wait_for_selector(".choice")
        page.locator(".choice").first.click()
        page.wait_for_selector(".verdict")
        if i == 0:
            shot(page, "09_example_answered")
            check(page.locator(".verdict .ex-src").count() >= 1, W + "例文の出典が出る")
        page.click(".bottom-bar .btn.primary")
    page.wait_for_selector(".result-hero")
    check(page.locator("text=例文モードのおためしは、ここまでです").count() == 1, W + "おためし5問のあと案内が出る")
    page.click("text=ホームに戻る")
    tab(page, "学習")
    page.click(".cardrow:has-text('例文で当てる')")
    page.wait_for_selector(".paywall")
    check(True, W + "おためしを使い切ると完全版の画面へ")
    shot(page, "10_paywall")
    if not DEV:
        check(page.locator("text=購入は準備中です").count() == 1, W + "キーが無い製品ビルドでは「購入は準備中」と出る(落ちない)")
    page.click(".topbar .icon")

    # 8. 辞書と詳しい画面
    tab(page, "辞書")
    page.wait_for_selector(".rows")
    page.fill(".search", "あはれ")
    page.wait_for_timeout(200)
    check(page.locator(".row").count() >= 1, W + "辞書で「あはれ」を探せる")
    page.locator(".row").first.click()
    page.wait_for_selector(".wd-head")
    shot(page, "11_detail")
    check(page.locator(".dsec.ex blockquote").count() >= 1, W + "詳しい画面に例文がある")
    page.click(".topbar .icon")
    page.fill(".search", "")
    page.locator(".row.locked").first.click()
    page.wait_for_selector(".paywall")
    check(True, W + "鍵の付いた語を押すと完全版の画面へ")
    page.click(".topbar .icon")

    # 9. 敬語セット(無料では一覧だけ)
    tab(page, "学習")
    page.click(".cardrow:has-text('敬語セット')")
    page.wait_for_selector(".setpage")
    check(page.locator(".unlock").count() == 1 or DEV, W + "無料では敬語セットの問題は完全版の案内")
    shot(page, "12_keigo_free")
    page.click(".topbar .icon")

    # 10. 設定: 試験日を入れると逆算が出る
    tab(page, "設定")
    page.wait_for_selector(".settings")
    page.fill("input[type=date]", "2027-01-16")
    shot(page, "13_settings")
    tab(page, "ホーム")
    page.wait_for_selector(".home")
    check(page.locator(".exam-days").count() == 1, W + "試験日を入れると残り日数が出る")
    check("1日" in page.locator(".hero-sub").inner_text(), W + "1日に覚える語数が出る: " + page.locator(".hero-sub").inner_text())
    shot(page, "14_home_plan")
    page.click(".exam-head")
    page.wait_for_selector(".plan-page")
    check(page.locator(".plan-num b").count() == 1, W + "学習計画に残り日数")
    page.click(".topbar .icon")

    # 11. 開き直しても記録が残る
    before = page.locator(".tiles").inner_text()
    page.reload()
    page.wait_for_selector(".home")
    check(page.locator(".tiles").inner_text() == before, W + "開き直しても記録が残る")

    # 12. 完全版の流れ(開発サーバーの疑似購入だけ)
    if DEV:
        page.click(".unlock-row")
        page.wait_for_selector(".paywall")
        page.click(".pw-cta .btn.buy")
        page.wait_for_selector(".home")
        check(page.locator(".unlock-row").count() == 0, W + "買ったら案内が消える")
        tab(page, "学習")
        page.click(".cardrow:has-text('敬語セット')")
        page.click("button:has-text('尊敬・謙譲・丁寧')")
        page.wait_for_selector(".choices.kind")
        texts = page.locator(".choice").all_inner_texts()
        check(texts == ["尊敬語", "謙譲語", "丁寧語"], W + f"敬語の種類の選択肢は固定の順: {texts}")
        shot(page, "15_keigo_kind")
        page.click(".topbar .icon")
        page.click(".topbar .icon")
        page.click(".cardrow:has-text('助動詞セット')")
        page.click("text=例文で見分ける")
        page.wait_for_selector(".q-ex")
        shot(page, "16_jodoshi_example")
        page.click(".topbar .icon")
        page.click(".topbar .icon")
        page.click(".cardrow:has-text('例文で当てる')")
        page.wait_for_selector(".q-ex")
        check("例文で当てる" == page.locator(".topbar h1").inner_text().strip(), W + "完全版では例文モードが制限なし")
    b.close()


with sync_playwright() as p:
    for w, h in ((375, 812), (430, 932)):
        run(p, w, h)
if httpd:
    httpd.shutdown()

errs = [e for e in errors if "favicon" not in e]
check(not errs, f"コンソールのエラー 0件 {errs[:3]}")
print("FAIL" if fails else "ALL OK", len(fails))
sys.exit(1 if fails else 0)
