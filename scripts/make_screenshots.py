"""Play ストア用の画面写真とフィーチャー画像(作り直した見た目)。python scripts/make_screenshots.py [URL]
1) 開発サーバーの見本データ(?demo=1&premium=1)で画面を撮る → store/raw/
   完全版の状態で撮るので「無料版」の文字は出ない。購入画面(値段)は撮らない
2) 和紙の地に見出しを書いて重ねる → store/play/play_shot_1〜5.png(1080x1920)
3) フィーチャー画像 store/play/feature.png(1024x500)。アイコン 512 は scripts/make_icon.py
iOS の画面写真(store/shot_*.png)は iOS を出し直さないので作らない。"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5393/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "store")
RAW = os.path.join(STORE, "raw")
PLAY = os.path.join(STORE, "play")
IMG = os.path.join(ROOT, "public", "img")
os.makedirs(RAW, exist_ok=True)
os.makedirs(PLAY, exist_ok=True)
WORDS = json.load(open(os.path.join(ROOT, "public", "data", "words.json"), encoding="utf-8"))
SERIF = "C:/Windows/Fonts/NotoSerifJP-VF.ttf"
BG = (244, 239, 227)
AI = (30, 58, 95)
SUMI = (47, 47, 47)
SHU = (201, 79, 63)

# 見出し(語り口で短く。値段・無料は書かない)
SHOTS = [
    ("1_example", "古典の本文の一文で", "印の語の、その文での意味を当てる"),
    ("2_home", "今日やる分が、ひと目で", "今日の復習・苦手・試験日までの日数"),
    ("3_answer", "答えたら、すぐに解説", "意味・例文・出典と、ほかの選択肢の意味"),
    ("4_nigate", "苦手は2回続けて正解で消える", "間違えた語だけを、くり返し"),
    ("5_plan", "試験日から逆算する", "1日に覚える語数を、自動で出す"),
]


def font(size, wght=700):
    f = ImageFont.truetype(SERIF, size)
    f.set_variation_by_axes([wght])
    return f


def right_index(pg):
    texts = pg.locator(".choice-t").all_inner_texts()
    w = pg.locator(".q-prompt").first.evaluate("e => e.firstChild ? e.firstChild.textContent : ''")
    k = pg.locator(".q-prompt small").inner_text() if pg.locator(".q-prompt small").count() else ""
    x = next((x for x in WORDS if x["w"] == w and x["kanji"] == k), None) or next(x for x in WORDS if x["w"] == w)
    return texts.index(x["quiz"])


def capture():
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 700}, device_scale_factor=3, locale="ja-JP")
        pg = ctx.new_page()
        pg.goto(URL + "?demo=1&premium=1&n=220&acc=0.72")
        pg.wait_for_selector(".home")
        pg.goto(URL)
        pg.wait_for_selector(".home")
        pg.wait_for_function("document.fonts.status === 'loaded'")
        pg.wait_for_timeout(500)
        pg.screenshot(path=os.path.join(RAW, "2_home.png"))

        # 例文で当てる(問題)
        pg.click(".tabbar button:has-text('学習')")
        pg.click(".cardrow:has-text('例文で当てる')")
        pg.wait_for_selector(".q-ex")
        pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(RAW, "1_example.png"))
        pg.click(".topbar .icon")

        # 4択で意味: 正解を選んで解説まで
        pg.click(".cardrow:has-text('4択で意味')")
        pg.wait_for_selector(".choice")
        pg.locator(".choice").nth(right_index(pg)).click()
        pg.wait_for_selector(".verdict.good")
        pg.add_style_tag(content=".bottom-bar{display:none!important}")
        pg.evaluate("document.querySelector('.choice.right').scrollIntoView({block:'start'}); window.scrollBy(0, -78)")
        pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(RAW, "3_answer.png"))
        pg.goto(URL)
        pg.wait_for_selector(".home")

        pg.click(".tabbar button:has-text('苦手')")
        pg.wait_for_selector(".wrows")
        pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(RAW, "4_nigate.png"))
        pg.click(".tabbar button:has-text('ホーム')")
        pg.click(".exam-head")
        pg.wait_for_selector(".plan-page")
        pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(RAW, "5_plan.png"))
        b.close()


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=r, fill=255)
    out = im.convert("RGBA")
    out.putalpha(m)
    return out


def art(name):
    return Image.open(os.path.join(IMG, name + ".webp")).convert("RGBA")


def compose():
    W, H = 1080, 1920
    for k, (name, title, sub) in enumerate(SHOTS, 1):
        c = Image.new("RGBA", (W, H), BG + (255,))
        # 上の飾り: 見本の景色の絵
        head = art("head_sub")
        head = head.resize((W, int(head.height * W / head.width)), Image.LANCZOS)
        c.alpha_composite(head, (0, 0))
        veil = Image.new("RGBA", (W, head.height), BG + (215,))
        c.alpha_composite(veil, (0, 0))
        d = ImageDraw.Draw(c)
        size = 76
        while font(size).getlength(title) > 900:
            size -= 2
        f1, f2 = font(size), font(40, 500)
        tw = d.textlength(title, font=f1)
        d.text(((W - tw) / 2, 70 + (76 - size) // 2), title, font=f1, fill=SUMI)
        sw = d.textlength(sub, font=f2)
        d.text(((W - sw) / 2, 180), sub, font=f2, fill=AI)
        seal = art("ic_seal").resize((34, 43))
        c.alpha_composite(seal, (int((W + tw) / 2) + 8, 82))
        # 画面
        shot = Image.open(os.path.join(RAW, name + ".png")).convert("RGB")
        sw2 = 840
        sh2 = int(shot.height * sw2 / shot.width)
        shot = shot.resize((sw2, sh2), Image.LANCZOS)
        x, y = (W - sw2) // 2, 290
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle([x + 6, y + 14, x + sw2 + 6, y + sh2 + 14], radius=48, fill=(70, 50, 20, 70))
        c.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
        frame = Image.new("RGBA", (sw2 + 16, sh2 + 16), (0, 0, 0, 0))
        ImageDraw.Draw(frame).rounded_rectangle([0, 0, sw2 + 15, sh2 + 15], radius=54, fill=(250, 247, 240, 255), outline=(214, 202, 178, 255), width=3)
        c.alpha_composite(frame, (x - 8, y - 8))
        c.alpha_composite(rounded(shot, 46), (x, y))
        # 下の梅
        plum = art("plum_corner")
        plum = plum.resize((120, int(plum.height * 120 / plum.width)))
        c.alpha_composite(plum, (0, H - plum.height))
        c.convert("RGB").save(os.path.join(PLAY, f"play_shot_{k}.png"), optimize=True)
        print("play_shot", k)

    # フィーチャー画像 1024x500
    W, H = 1024, 500
    c = Image.new("RGBA", (W, H), BG + (255,))
    land = art("head_home")
    land = land.resize((W, int(land.height * W / land.width)), Image.LANCZOS)
    c.alpha_composite(land, (0, H - land.height + 10))
    d = ImageDraw.Draw(c)
    icon = Image.open(os.path.join(ROOT, "assets", "icon.png")).convert("RGB").resize((176, 176), Image.LANCZOS)
    c.alpha_composite(rounded(icon, 38), (84, 60))
    f1, f2 = font(92), font(36, 600)
    d.text((300, 62), "こぶんめくり", font=f1, fill=SUMI)
    seal = art("ic_seal").resize((30, 38))
    c.alpha_composite(seal, (300 + int(d.textlength("こぶんめくり", font=f1)) + 6, 82))
    d.text((306, 186), "― 古文単語600・例文つき ―", font=f2, fill=AI)
    c.convert("RGB").save(os.path.join(PLAY, "feature.png"), optimize=True)
    print("feature")


if __name__ == "__main__":
    if "--compose-only" not in sys.argv:
        capture()
    compose()
