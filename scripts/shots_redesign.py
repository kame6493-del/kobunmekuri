"""作り直した見た目の全画面を 375 / 430 幅で撮る(開発サーバーの見本データ ?demo=1)。
  python scripts/shots_redesign.py [URL]  → docs/screens/375/*.png, docs/screens/430/*.png
押して回りながら、画面ごとに要素があるかも確かめる。NG があれば exit 1。"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5291/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDS = json.load(open(os.path.join(ROOT, "public", "data", "words.json"), encoding="utf-8"))
fails, errors = [], []


def check(c, m):
    print(("OK  " if c else "NG  ") + m)
    if not c:
        fails.append(m)


def right_index(pg, mode="mean"):
    texts = pg.locator(".choice-t").all_inner_texts()
    if mode == "reverse":
        meaning = pg.locator(".q-prompt").inner_text()
        cands = [x["w"] for x in WORDS if x["quiz"] == meaning]
        return next(i for i, t in enumerate(texts) if t in cands)
    w = pg.locator(".q-prompt").first.evaluate("e => e.firstChild ? e.firstChild.textContent : ''")
    k = pg.locator(".q-prompt small").inner_text() if pg.locator(".q-prompt small").count() else ""
    x = next((x for x in WORDS if x["w"] == w and x["kanji"] == k), None) or next(x for x in WORDS if x["w"] == w)
    return texts.index(x["quiz"])


def run(width, height):
    out = os.path.join(ROOT, "docs", "screens", str(width))
    os.makedirs(out, exist_ok=True)

    def shot(pg, name, full=False):
        # 画面の大きさで撮る(下に固定したタブ・ボタンが正しい位置に写る)。長い画面は下までの1枚も撮る
        pg.wait_for_timeout(250)
        pg.evaluate("window.scrollTo(0, 0)")
        pg.wait_for_timeout(100)
        pg.screenshot(path=os.path.join(out, name + ".png"))
        if full and pg.evaluate("document.documentElement.scrollHeight") > height + 40:
            pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
            pg.wait_for_timeout(200)
            pg.screenshot(path=os.path.join(out, name + "_b.png"))
            pg.evaluate("window.scrollTo(0, 0)")
        # 横にはみ出していないか
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(sw <= width, f"[{width}] {name}: 横はみ出しなし ({sw})")

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": width, "height": height}, device_scale_factor=2, locale="ja-JP")
        pg = ctx.new_page()
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append(str(e)))

        # --- はじめて(記録なし) ---
        pg.goto(URL)
        pg.evaluate("localStorage.clear()")
        pg.goto(URL)
        pg.wait_for_selector(".home")
        pg.wait_for_function("document.fonts.status === 'loaded'")
        shot(pg, "00_home_first")
        pg.click(".tabbar button:has-text('苦手')")
        pg.wait_for_selector(".empty-state")
        check(pg.locator("text=苦手がありません").count() == 1, f"[{width}] 苦手0の空の状態")
        shot(pg, "20_empty_nigate")
        pg.click(".tabbar button:has-text('ホーム')")
        pg.click(".tile.hot")
        pg.wait_for_selector(".empty-state")
        check(pg.locator("text=今日の復習はありません").count() == 1, f"[{width}] 今日の復習0の空の状態")
        shot(pg, "21_empty_review")

        # --- 見本データ(無料) ---
        pg.goto(URL + "?demo=1&n=220&acc=0.72")
        pg.wait_for_selector(".home")
        pg.goto(URL)
        pg.wait_for_selector(".home")
        pg.wait_for_function("document.fonts.status === 'loaded'")
        shot(pg, "01_home", full=True)
        check(pg.locator(".unlock-row").count() == 1, f"[{width}] 無料のときホームに完全版の行")
        pg.click(".tabbar button:has-text('学習')")
        pg.wait_for_selector(".study")
        shot(pg, "02_study", full=True)
        pg.click(".tabbar button:has-text('苦手')")
        pg.wait_for_selector(".nigate-page .wrows")
        shot(pg, "03_nigate")
        pg.click(".tabbar button:has-text('辞書')")
        pg.wait_for_selector(".wlist .rows")
        shot(pg, "04_dict", full=False)
        pg.fill(".search", "あはれ")
        pg.wait_for_timeout(200)
        pg.locator(".row").first.click()
        pg.wait_for_selector(".wd-head")
        shot(pg, "05_detail", full=True)
        pg.click(".topbar .icon")
        pg.click(".tabbar button:has-text('設定')")
        pg.wait_for_selector(".settings")
        shot(pg, "06_settings", full=True)
        pg.click(".tabbar button:has-text('ホーム')")
        pg.click(".exam-head")
        pg.wait_for_selector(".plan-page")
        shot(pg, "07_plan", full=True)
        pg.click(".topbar .icon")
        pg.click(".tile.hot")
        pg.wait_for_selector(".review-page .wrows")
        shot(pg, "08_review", full=False)
        pg.click(".topbar .icon")

        # 4択で意味: 問題・正解・不正解
        pg.click(".tabbar button:has-text('学習')")
        pg.click(".cardrow:has-text('4択で意味')")
        pg.wait_for_selector(".choice")
        shot(pg, "09_mean_q")
        k = right_index(pg)
        pg.locator(".choice").nth(k).click()
        pg.wait_for_selector(".verdict.good")
        shot(pg, "10_mean_right", full=True)
        pg.click(".bottom-bar .btn")
        pg.wait_for_selector(".choice")
        k = right_index(pg)
        pg.locator(".choice").nth((k + 1) % 4).click()
        pg.wait_for_selector(".verdict.bad")
        check(pg.locator(".others li").count() >= 1, f"[{width}] 他の選択肢についてが出る")
        shot(pg, "11_mean_wrong", full=True)
        pg.click(".topbar .icon")

        # 意味から古語
        pg.click(".cardrow:has-text('意味から古語')")
        pg.wait_for_selector(".choice")
        shot(pg, "12_reverse_q")
        pg.locator(".choice").nth(right_index(pg, "reverse")).click()
        pg.wait_for_selector(".verdict.good")
        pg.click(".topbar .icon")

        # 例文で当てる(おためし)
        pg.click(".cardrow:has-text('例文で当てる')")
        pg.wait_for_selector(".q-ex")
        check(pg.locator(".q-ex mark").count() == 1, f"[{width}] 例文の印")
        shot(pg, "13_example_q")
        pg.locator(".choice").first.click()
        pg.wait_for_selector(".verdict")
        shot(pg, "14_example_answered", full=True)
        pg.click(".topbar .icon")

        # カード
        pg.click(".cardrow:has-text('一問一答カード')")
        pg.wait_for_selector(".card-flip")
        shot(pg, "15_card_front")
        pg.click(".card-flip")
        pg.wait_for_selector(".card-back")
        shot(pg, "16_card_back", full=True)
        pg.click("text=わかった")
        check(pg.locator(".bottom-bar").count() == 1, f"[{width}] カードは自己採点のあと次へ")
        pg.click(".topbar .icon")

        # 結果(5問)
        pg.click(".tabbar button:has-text('設定')")
        pg.click(".seg button:has-text('5問')")
        pg.click(".tabbar button:has-text('学習')")
        pg.click(".cardrow:has-text('4択で意味')")
        for n in range(5):
            pg.wait_for_selector(".choice")
            k = right_index(pg)
            pg.locator(".choice").nth(k if n % 2 == 0 else (k + 1) % 4).click()
            pg.click(".bottom-bar .btn")
        pg.wait_for_selector(".result-hero")
        check(pg.locator(".res-ok").inner_text().startswith("3"), f"[{width}] 結果の正解数 3")
        shot(pg, "17_result", full=True)
        pg.click("text=ホームに戻る")

        # 敬語(無料)・完全版
        pg.click(".tabbar button:has-text('学習')")
        pg.click(".cardrow:has-text('敬語セット')")
        pg.wait_for_selector(".setpage")
        shot(pg, "18_keigo_free", full=True)
        pg.click(".unlock")
        pg.wait_for_selector(".paywall")
        shot(pg, "19_paywall", full=True)

        # --- 完全版(疑似購入)---
        pg.goto(URL + "?demo=1&n=220&acc=0.72&premium=1")
        pg.wait_for_selector(".home")
        pg.goto(URL)
        pg.wait_for_selector(".home")
        pg.click(".tabbar button:has-text('学習')")
        pg.click(".cardrow:has-text('敬語セット')")
        pg.wait_for_selector(".kind-tabs")
        shot(pg, "22_keigo", full=True)
        pg.click(".kind-tabs button:has-text('謙譲')")
        check(pg.locator(".setrow").count() >= 10, f"[{width}] 謙譲のタブで絞り込み")
        pg.click("button:has-text('尊敬・謙譲・丁寧')")
        pg.wait_for_selector(".choices.kind")
        texts = pg.locator(".choice").all_inner_texts()
        check(texts == ["尊敬語", "謙譲語", "丁寧語"], f"[{width}] 敬語の種類の並び固定 {texts}")
        shot(pg, "23_keigo_kind")
        pg.click(".topbar .icon")
        pg.click(".topbar .icon")
        pg.click(".cardrow:has-text('助動詞セット')")
        pg.wait_for_selector(".setpage")
        shot(pg, "24_jodoshi", full=True)

        # 本日の復習おわり: 復習が少ない見本データで今日の復習を全部解く
        pg.goto(URL + "?demo=1&n=14&acc=0.6&premium=1")
        pg.wait_for_selector(".home")
        pg.goto(URL)
        pg.wait_for_selector(".home")
        pg.click(".tile.hot")
        if pg.locator(".start-review").count():
            pg.click(".start-review")
            while True:
                pg.wait_for_selector(".choice, .result")
                if pg.locator(".result").count():
                    break
                pg.locator(".choice").nth(right_index(pg)).click()
                pg.click(".bottom-bar .btn")
            check(pg.locator("text=本日の復習おわり").count() == 1, f"[{width}] 今日の復習を終えると「本日の復習おわり」")
            shot(pg, "25_review_done", full=True)
        else:
            check(False, f"[{width}] 見本データに今日の復習がない")
        b.close()


for w, h in ((375, 812), (430, 932)):
    run(w, h)
errs = [e for e in errors if "favicon" not in e]
check(not errs, f"コンソールのエラー 0件 {errs[:3]}")
print("FAIL" if fails else "ALL OK", len(fails))
sys.exit(1 if fails else 0)
