"""ストア用の画面写真。python scripts/make_screenshots.py [URL]
1) 開発サーバーの見本データ(?demo=1)で画面を撮る → store/raw/
2) 和紙の地に見出しを書いて重ねる → store/shot_1〜5.png(iPhone 1290x2796)と store/play/play_shot_1〜5.png(1080x1920)
3) Play 用のアイコン 512 とフィーチャー 1024x500"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5291/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "store")
RAW = os.path.join(STORE, "raw")
PLAY = os.path.join(STORE, "play")
os.makedirs(RAW, exist_ok=True)
os.makedirs(PLAY, exist_ok=True)
WORDS = json.load(open(os.path.join(ROOT, "public", "data", "words.json"), encoding="utf-8"))

PAPER = (246, 241, 231)
PAPER2 = (236, 228, 212)
INK = (38, 35, 32)
SHU = (184, 69, 47)
KIN = (233, 196, 106)
MINCHO = "C:/Windows/Fonts/yumindb.ttf"
GOTHIC = "C:/Windows/Fonts/YuGothB.ttc"


def find_word(pg):
    w = pg.locator(".q-prompt").first.evaluate("e => e.firstChild ? e.firstChild.textContent : ''")
    k = pg.locator(".q-prompt small").inner_text() if pg.locator(".q-prompt small").count() else ""
    return next((x for x in WORDS if x["w"] == w and x["kanji"] == k), None) or next(x for x in WORDS if x["w"] == w)


def capture():
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 430, "height": 932}, device_scale_factor=3, locale="ja-JP")
        pg = ctx.new_page()
        pg.goto(URL + "?demo=1&premium=1&n=220&acc=0.72")
        pg.wait_for_selector(".home")
        pg.goto(URL)
        pg.wait_for_selector(".hero-num")
        # 下に固定した「次へ」の帯は、写真の下端で切れて見えるので消して撮る
        pg.add_style_tag(content=".bottom-bar{display:none!important}")
        pg.screenshot(path=os.path.join(RAW, "2_home.png"))

        # 例文で当てる: 正解を選んだ所(本文と訳が見える)
        pg.click("text=例文で当てる")
        pg.wait_for_selector(".q-ex")
        pg.screenshot(path=os.path.join(RAW, "1_example_q.png"))
        w = None
        texts = pg.locator(".choice").all_inner_texts()
        hit = pg.locator(".q-ex mark").inner_text()
        cand = [x for x in WORDS if x["set"] == "main" and any(e["hit"] == hit for e in x["ex"])]
        k = 0
        for x in cand:
            for e in x["ex"]:
                if e["hit"] == hit:
                    right = x["quiz"] if e["sense"] == 0 else x["means"][e["sense"]]
                    if right in texts:
                        k = texts.index(right)
        pg.locator(".choice").nth(k).click()
        pg.wait_for_selector(".verdict")
        pg.evaluate("() => window.scrollTo(0, 0)")
        pg.screenshot(path=os.path.join(RAW, "1_example.png"))
        pg.click(".topbar .icon")

        # 4択: わざと間違えた所(苦手に入る)
        pg.wait_for_selector(".home")
        pg.click("text=4択で意味")
        pg.wait_for_selector(".choice")
        x = find_word(pg)
        texts = pg.locator(".choice").all_inner_texts()
        wrong = next(i for i, t in enumerate(texts) if t != x["quiz"])
        pg.locator(".choice").nth(wrong).click()
        pg.wait_for_selector(".verdict")
        pg.evaluate("() => window.scrollTo(0, 0)")
        pg.screenshot(path=os.path.join(RAW, "3_wrong.png"))
        pg.click(".topbar .icon")

        # 苦手だけ → 結果(苦手から外れた)。ここだけ warm=1 の見本データ(苦手が「あと1回正解」の状態)
        pg.goto(URL + "?demo=1&premium=1&n=220&acc=0.72&warm=1")
        pg.wait_for_selector(".home")
        pg.goto(URL)
        pg.wait_for_selector(".home")
        pg.add_style_tag(content=".bottom-bar{display:none!important}")
        pg.click(".tile.nigate")
        for i in range(25):
            pg.wait_for_selector(".choice, .card-flip")
            x = find_word(pg)
            texts = pg.locator(".choice").all_inner_texts()
            k = texts.index(x["quiz"]) if i != 3 else next(j for j, t in enumerate(texts) if t != x["quiz"])
            pg.locator(".choice").nth(k).click()
            pg.wait_for_selector(".verdict")
            pg.evaluate("() => document.querySelector('.bottom-bar .btn.primary').click()")
            if pg.locator(".result-hero").count():
                break
        pg.wait_for_selector(".result-hero")
        pg.screenshot(path=os.path.join(RAW, "4_result.png"))
        pg.click("text=ホームへ")

        # 敬語の種類(選択肢の並びは固定)
        pg.wait_for_selector(".home")
        pg.click("text=敬語セット")
        pg.click("button:has-text('尊敬・謙譲・丁寧')")
        pg.wait_for_selector(".choices.kind")
        pg.locator(".choice").nth(0).click()
        pg.wait_for_selector(".verdict")
        pg.evaluate("() => window.scrollTo(0, 0)")
        pg.screenshot(path=os.path.join(RAW, "5_keigo.png"))
        b.close()


def paper(w, h):
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    # 和紙の繊維のような薄い横筋
    for y in range(0, h, 7):
        if (y * 37) % 11 < 2:
            d.line([(0, y), (w, y)], fill=PAPER2, width=1)
    return img


def compose(n, raw, title, sub):
    W, H = 1290, 2796
    img = paper(W, H)
    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(MINCHO, 100)
    f2 = ImageFont.truetype(GOTHIC, 46)
    y = 190
    for ln in title.split("\n"):
        bb = d.textbbox((0, 0), ln, font=f1)
        x = (W - (bb[2] - bb[0])) // 2
        d.text((x - bb[0], y), ln, font=f1, fill=INK)
        y += 132
    # 朱の印
    d.rounded_rectangle([W // 2 - 26, y + 12, W // 2 + 26, y + 64], radius=8, fill=SHU)
    y += 100
    bb = d.textbbox((0, 0), sub, font=f2)
    d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], y), sub, font=f2, fill=(92, 86, 77))
    y += 100
    shot = Image.open(os.path.join(RAW, raw)).convert("RGB")
    sw = 1000
    sh = int(shot.height * sw / shot.width)
    shot = shot.resize((sw, sh), Image.LANCZOS)
    avail = H - y - 60
    if sh > avail:
        shot = shot.crop((0, 0, sw, avail))
        sh = avail
    x0 = (W - sw) // 2
    mask = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw - 1, sh + 60], radius=48, fill=255)
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle([x0 + 10, y + 20, x0 + sw + 10, y + sh + 80], radius=48, fill=90)
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    img.paste((150, 135, 110), (0, 0), shadow)
    img.paste(shot, (x0, y), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y, x0 + sw - 1, y + sh + 60], radius=48, outline=(214, 204, 186), width=3)
    img.save(os.path.join(STORE, f"shot_{n}.png"))
    # Play: 9:16。高さ1920に縮め、左右を和紙の色で埋める
    pw = int(W * 1920 / H)
    play = paper(1080, 1920)
    play.paste(img.resize((pw, 1920), Image.LANCZOS), ((1080 - pw) // 2, 0))
    play.save(os.path.join(PLAY, f"play_shot_{n}.png"))


def play_assets():
    icon = Image.open(os.path.join(ROOT, "assets", "icon.png")).convert("RGB")
    icon.resize((512, 512), Image.LANCZOS).save(os.path.join(PLAY, "icon_512.png"))
    W, H = 1024, 500
    fg = paper(W, H)
    d = ImageDraw.Draw(fg)
    f_big = ImageFont.truetype(MINCHO, 66)
    f_small = ImageFont.truetype(GOTHIC, 30)
    d.text((70, 110), "古文単語を、", font=f_big, fill=INK)
    d.text((70, 196), "本文の中でめくる。", font=f_big, fill=INK)
    bb = d.textbbox((70, 196), "本文の中でめくる。", font=f_big)
    d.line([(bb[0], bb[3] + 12), (bb[2] - 30, bb[3] + 8)], fill=SHU, width=6)
    d.text((72, 330), "こぶんめくり 大学受験の古文単語601語", font=f_small, fill=INK)
    d.text((72, 376), "全語に古典の例文・広告なし", font=f_small, fill=(92, 86, 77))
    ic = icon.resize((300, 300), Image.LANCZOS)
    mask = Image.new("L", ic.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, 299, 299], radius=66, fill=255)
    fg.paste(ic, (W - 360, 100), mask)
    fg.save(os.path.join(PLAY, "feature.png"))


if __name__ == "__main__":
    if "--no-capture" not in sys.argv:
        capture()
    compose(1, "1_example.png", "古文単語を、\n本文の中で覚える", "源氏物語・徒然草・枕草子の一文で意味を選ぶ")
    compose(2, "2_home.png", "試験日から、\n1日の語数を逆算", "601語を重要度順に。今日の復習も自動で")
    compose(3, "3_wrong.png", "間違えた語は\n「苦手」に残る", "意味・解説・例文の訳をその場で確かめる")
    compose(4, "4_result.png", "2回続けて正解で、\n苦手が消える", "覚えた語は1日後・3日後・1週間後にまた出る")
    compose(5, "5_keigo.png", "敬語と助動詞も\nまとめて", "尊敬・謙譲・丁寧は、いつも同じ並びで選べる")
    play_assets()
    print("ok")
