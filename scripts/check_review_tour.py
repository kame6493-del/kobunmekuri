"""録画用の自動操作(src/dev/reviewTour.ts)が最後まで進むかを手元のブラウザで確かめる。
先に録画用ビルドを作って配っておく:
  VITE_REVIEW_TOUR=1 npx vite build --outDir <一時フォルダ> → npx vite preview --outDir <一時フォルダ> --port 5242 で配る、または
  VITE_REVIEW_TOUR=1 npx vite --port 5242 --strictPort (開発サーバーは疑似購入)
python scripts/check_review_tour.py [URL] [録画の置き場所]
→ 通った画面の見出しを順に出し、購入画面に着いた秒数を出す。録画(webm)は2つ目の引数のフォルダ(既定は一時フォルダ)に置く"""
import os
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5242/"
OUT = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix="kobun_tour_")
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 393, "height": 852}, device_scale_factor=2, locale="ja-JP",
                        record_video_dir=OUT, record_video_size={"width": 393, "height": 852})
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL)
    seen = []
    t0 = time.time()
    reached = None
    while time.time() - t0 < 150:
        txt = pg.evaluate("document.body.innerText.slice(0,60).replace(/\\s+/g,' ')")
        if not seen or seen[-1] != txt:
            seen.append(txt)
            print(round(time.time() - t0), txt, flush=True)
        if reached is None and pg.locator(".paywall").count() > 0:
            reached = round(time.time() - t0)
        if reached is not None and time.time() - t0 > reached + 25:
            break
        time.sleep(1)
    print("data:", pg.evaluate("localStorage.length"), "keys")
    path = pg.video.path()
    ctx.close()
    b.close()
    print("paywall reached at", reached, "s / total", round(time.time() - t0), "s")
    print("page errors:", errors)
    print("video", path)
    sys.exit(0 if reached is not None and not errors else 1)
