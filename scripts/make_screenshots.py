"""Play ストア用の画面写真とフィーチャー画像(作り直した見た目)。python scripts/make_screenshots.py [URL]
--compose-only で撮影を飛ばして store/raw/ から組むだけにできる。
1) 開発サーバーの見本データ(?demo=1&premium=1)で画面を撮る → store/raw/
   完全版の状態で撮るので「無料版」の文字は出ない。購入画面(値段)は撮らない
2) 紺の地(梅の花びら・金の星)に HG明朝E の見出しを書いて重ねる(2026-10-10 和紙の地をやめた。元は store/_cream_backup_2026-10-10/) → store/play/play_shot_1〜5.png(1080x1920)
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


NAVY = (22, 41, 70)       # アイコンの紺(29,60,92)を少し深く
NAVY2 = (12, 24, 44)
UME = (240, 160, 172)     # 梅の花の色(添え書き)
GOLD = (205, 172, 104)    # 枠の金
TITLE_F = "C:/Windows/Fonts/HGRME.TTC"   # HG明朝E(見出し)
SUB_F = "C:/Windows/Fonts/yumindb.ttf"   # 游明朝 Demibold(添え書き)


def tfont(size):
    return ImageFont.truetype(TITLE_F, size)


def navy_ground(W, H, seed=3):
    """紺の地(上から下へ深く)に、梅の花びらを少しだけ散らす。2026-10-10 和紙の地をやめた"""
    import random
    c = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(c)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(round(NAVY[i] + (NAVY2[i] - NAVY[i]) * k) for i in range(3)) + (255,))
    rnd = random.Random(seed)
    petal = art("ic_plum")
    for _ in range(int(W * H / 90000)):
        s = rnd.randint(22, 46)
        pe = petal.resize((s, int(petal.height * s / petal.width)), Image.LANCZOS).rotate(rnd.randint(0, 359), expand=True)
        a = pe.split()[-1].point(lambda v, f=rnd.uniform(0.18, 0.4): int(v * f))
        pe.putalpha(a)
        c.alpha_composite(pe, (rnd.randint(0, W - 40), rnd.randint(0, H - 40)))
    # 細い金の星(アイコンの夜空)
    for _ in range(int(W * H / 30000)):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        r = rnd.choice((1, 1, 2))
        d.ellipse((x - r, y - r, x + r, y + r), fill=GOLD + (rnd.randint(60, 150),))
    return c


def compose():
    W, H = 1080, 1920
    for k, (name, title, sub) in enumerate(SHOTS, 1):
        c = navy_ground(W, H, seed=k)
        # 四すみに大きめの梅をはっきり
        for (px, py, ps, rot) in ((W - 120, 30, 96, 20), (W - 70, 150, 54, -30), (24, H - 150, 110, 10), (130, H - 70, 50, 40)):
            pe = art("ic_plum").resize((ps, int(126 * ps / 110)), Image.LANCZOS).rotate(rot, expand=True)
            c.alpha_composite(pe, (px, py))
        d = ImageDraw.Draw(c)
        size = 84
        while tfont(size).getlength(title) > 880:
            size -= 2
        f1, f2 = tfont(size), ImageFont.truetype(SUB_F, 40)
        tw = d.textlength(title, font=f1)
        d.text(((W - tw) / 2, 74 + (84 - size) // 2), title, font=f1, fill=(255, 255, 255))
        sw = d.textlength(sub, font=f2)
        d.text(((W - sw) / 2, 192), sub, font=f2, fill=UME)
        # 画面(金の細い枠)
        shot = Image.open(os.path.join(RAW, name + ".png")).convert("RGB")
        sw2 = 840
        sh2 = int(shot.height * sw2 / shot.width)
        shot = shot.resize((sw2, sh2), Image.LANCZOS)
        x, y = (W - sw2) // 2, 300
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle([x + 4, y + 18, x + sw2 + 4, y + sh2 + 18], radius=48, fill=(0, 0, 0, 130))
        c.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)))
        frame = Image.new("RGBA", (sw2 + 20, sh2 + 20), (0, 0, 0, 0))
        ImageDraw.Draw(frame).rounded_rectangle([0, 0, sw2 + 19, sh2 + 19], radius=56, fill=NAVY2 + (255,), outline=GOLD + (255,), width=3)
        c.alpha_composite(frame, (x - 10, y - 10))
        c.alpha_composite(rounded(shot, 46), (x, y))
        c.convert("RGB").save(os.path.join(PLAY, f"play_shot_{k}.png"), optimize=True)
        print("play_shot", k)

    # フィーチャー画像 1024x500: 左は紺に名前、右は山と塔の絵を窓のように切り抜く
    W, H = 1024, 500
    c = navy_ground(W, H, seed=9)
    land = art("head_home")
    lh = 420
    land = land.resize((int(land.width * lh / land.height), lh), Image.LANCZOS)
    win_w = 430
    land = land.crop((land.width - win_w - 20, 0, land.width - 20, lh))
    m = Image.new("L", land.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, win_w - 1, lh - 1), radius=200, fill=255)   # 丸窓(上下が丸い)
    land.putalpha(Image.composite(land.split()[-1], Image.new("L", land.size, 0), m))
    wx, wy = W - win_w - 40, 40
    ring = Image.new("RGBA", (win_w + 12, lh + 12), (0, 0, 0, 0))
    ImageDraw.Draw(ring).rounded_rectangle((0, 0, win_w + 11, lh + 11), radius=206, outline=GOLD + (255,), width=3)
    c.alpha_composite(land, (wx, wy))
    c.alpha_composite(ring, (wx - 6, wy - 6))
    d = ImageDraw.Draw(c)
    icon = Image.open(os.path.join(ROOT, "assets", "icon.png")).convert("RGB").resize((130, 130), Image.LANCZOS)
    c.alpha_composite(rounded(icon, 30), (60, 70))
    f1, f2 = tfont(82), ImageFont.truetype(SUB_F, 32)
    d.text((58, 228), "こぶんめくり", font=f1, fill=(255, 255, 255))
    d.text((62, 344), "古文単語600・例文つき", font=f2, fill=UME)
    for (px, py, ps, rot) in ((470, 380, 70, 15), (520, 440, 40, -25), (250, 60, 46, 30)):
        pe = art("ic_plum").resize((ps, int(126 * ps / 110)), Image.LANCZOS).rotate(rot, expand=True)
        c.alpha_composite(pe, (px, py))
    c.convert("RGB").save(os.path.join(PLAY, "feature.png"), optimize=True)
    print("feature")


if __name__ == "__main__":
    if "--compose-only" not in sys.argv:
        capture()
    compose()
