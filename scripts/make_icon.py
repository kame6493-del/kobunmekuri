"""アイコンを作る。python scripts/make_icon.py
見本 kobun_ref_1 の左上「アプリアイコン」(紺の地に「こ」の本・朱のしおり・金の雲・梅)を切り出し、
Real-ESRGAN で4倍にして 1024 の正方形に整える。角の丸の外(白)は紺で埋める。
書き出す物:
- assets/icon.png・icon-only.png(1024 不透明、iOS 用)/ icon-foreground.png・icon-background.png(Android 適応アイコン)/ splash.png・splash-dark.png
- android の mipmap 各寸法(適応アイコンの前景・背景色、従来の四角と丸)・drawable の splash
- ios の AppIcon 1024・Splash
- icons/*.webp(Web マニフェスト)・store/play/icon_512.png
- docs/icon_check.png(安全域66%の円・丸・角丸で切った見え方)"""
import glob
import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from esrgan import up4  # noqa: E402

REF = os.environ.get("KOBUN_REF", r"C:\Users\yuichi1\Downloads")
S = 1024
PAPER = (248, 245, 236)


def icon_art():
    """見本のアイコンを切り出し、角の外を紺で埋めた正方形(4倍)"""
    src = Image.open(os.path.join(REF, "kobun_ref_1_941x1672.png")).convert("RGB").crop((40, 240, 270, 468))
    big = np.asarray(up4(src)).copy()
    h, w = big.shape[:2]
    lum = big.mean(-1)
    # 角の外(白〜縁の明るい線)= 隅からつながった明るい所
    bright = (lum > 95).astype(np.uint8)
    n, lab = cv2.connectedComponents(bright, connectivity=4)
    outer = np.zeros_like(bright)
    for cx, cy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if bright[cy, cx]:
            outer[lab == lab[cy, cx]] = 1
    outer = cv2.dilate(outer, np.ones((19, 19), np.uint8))
    # 紺の四角の範囲(外の白を除いた範囲)を切り出す
    ys, xs = np.where(outer == 0)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    pad = 6
    crop = big[y0 + pad:y1 - pad, x0 + pad:x1 - pad]
    mask = outer[y0 + pad:y1 - pad, x0 + pad:x1 - pad] * 255
    bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    # 角の外と、元の縁の内側の影の帯を、すぐ内側の紺の色で埋める(内側の色を外へ延ばす)
    band = cv2.dilate(mask, np.ones((27, 27), np.uint8))
    fr = 18  # 元の四角の縁の暗い帯
    band[:fr] = 255; band[-fr:] = 255; band[:, :fr] = 255; band[:, -fr:] = 255
    ring = cv2.dilate(band, np.ones((41, 41), np.uint8)) - band
    px = crop[ring > 0].reshape(-1, 3)
    navy = np.median(px[px.mean(-1) < 110], axis=0)
    small = cv2.resize(bgr, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    smask = cv2.resize(band, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    ext = cv2.inpaint(small, smask, 12, cv2.INPAINT_TELEA)
    ext = cv2.GaussianBlur(cv2.resize(ext, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_CUBIC), (0, 0), 6)
    soft = cv2.GaussianBlur((band > 0).astype(np.float32), (0, 0), 7)[..., None]
    rng = np.random.default_rng(3)
    fill = ext.astype(np.float32) + rng.normal(0, 3.0, bgr.shape[:2])[..., None]
    bgr = np.clip(bgr.astype(np.float32) * (1 - soft) + fill * soft, 0, 255).astype(np.uint8)
    art = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    side = min(art.size)
    art = art.crop(((art.width - side) // 2, (art.height - side) // 2, (art.width - side) // 2 + side, (art.height - side) // 2 + side))
    return art.resize((S, S), Image.LANCZOS), tuple(int(v) for v in navy)


def book_bbox(art):
    """主役(和紙の本)の範囲。明るい所の最大のかたまり"""
    a = np.asarray(art).mean(-1)
    m = (a > 175).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = stats[k, :4]
    return x, y, x + w, y + h


def foreground(art, navy):
    """適応アイコンの前景(108dp 相当の 1024)。本が直径66%の円に収まる大きさにし、縁は紺へぼかして背景色になじませる"""
    bx0, by0, bx1, by1 = book_bbox(art)
    diag = ((bx1 - bx0) ** 2 + (by1 - by0) ** 2) ** 0.5
    scale = (S * 0.66 * 0.97) / diag
    size = int(S * scale)
    small = art.resize((size, size), Image.LANCZOS)
    # 本の中心をキャンバスの中心へ
    cx, cy = (bx0 + bx1) / 2 * scale, (by0 + by1) / 2 * scale
    ox, oy = int(S / 2 - cx), int(S / 2 - cy)
    fg = Image.new("RGBA", (S, S), navy + (0,))
    m = np.zeros((size, size), np.float32)
    e = int(size * 0.12)
    ramp = np.sin(np.linspace(0, np.pi / 2, e)) ** 2
    m[:] = 1
    m[:, :e] *= ramp[None]; m[:, -e:] *= ramp[::-1][None]; m[:e] *= ramp[:, None]; m[-e:] *= ramp[::-1][:, None]
    layer = small.convert("RGBA")
    layer.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    fg.alpha_composite(layer, (ox, oy))
    return fg, (ox, oy, size, scale)


def masked(img, shape):
    m = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(m)
    w, h = img.size
    if shape == "circle":
        d.ellipse([0, 0, w - 1, h - 1], fill=255)
    elif shape == "squircle":
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(w * 0.3), fill=255)
    else:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(w * 0.18), fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img.convert("RGBA"), (0, 0), m)
    return out


def adaptive_view(fg, navy, size):
    """端末の表示の再現: 108dp のうち中央 72dp(66.7%)が見える"""
    full = Image.new("RGBA", (S, S), navy + (255,))
    full.alpha_composite(fg)
    v = int(S * 72 / 108)
    o = (S - v) // 2
    return full.crop((o, o, o + v, o + v)).resize((size, size), Image.LANCZOS)


def splash(icon, size, bg=PAPER):
    w, h = size
    im = Image.new("RGB", (w, h), bg)
    s = int(min(w, h) * 0.28)
    ic = masked(icon.resize((s, s), Image.LANCZOS), "rounded")
    im.paste(ic, ((w - s) // 2, (h - s) // 2 - int(s * 0.12)), ic)
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/NotoSerifJP-VF.ttf", max(12, int(s * 0.2)))
        f.set_variation_by_axes([700])
        d = ImageDraw.Draw(im)
        t = "こぶんめくり"
        tw = d.textlength(t, font=f)
        d.text(((w - tw) / 2, (h + s) / 2 - int(s * 0.02)), t, font=f, fill=(30, 58, 95))
    except OSError:
        pass
    # 色数を減らして軽くする(Android の drawable は寸法ごとに20枚近くある)
    return im.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)


def main():
    art, navy = icon_art()
    print("navy", navy)
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    A = lambda *p: os.path.join(ROOT, *p)
    art.save(A("assets", "icon.png"))
    art.save(A("assets", "icon-only.png"))
    fg, info = foreground(art, navy)
    fg.save(A("assets", "icon-foreground.png"))
    Image.new("RGB", (S, S), navy).save(A("assets", "icon-background.png"))
    sp = splash(art, (2732, 2732))
    sp.save(A("assets", "splash.png"))
    sp.save(A("assets", "splash-dark.png"))

    # Android mipmap
    res = A("android", "app", "src", "main", "res")
    dens = {"ldpi": 0.75, "mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
    view = adaptive_view(fg, navy, 512)
    for k, f in dens.items():
        d = os.path.join(res, f"mipmap-{k}")
        os.makedirs(d, exist_ok=True)
        n108, n48 = round(108 * f), round(48 * f)
        fg.resize((n108, n108), Image.LANCZOS).save(os.path.join(d, "ic_launcher_foreground.png"))
        Image.new("RGB", (n108, n108), navy).save(os.path.join(d, "ic_launcher_background.png"))
        masked(view.resize((n48, n48), Image.LANCZOS), "rounded").save(os.path.join(d, "ic_launcher.png"))
        masked(view.resize((n48, n48), Image.LANCZOS), "circle").save(os.path.join(d, "ic_launcher_round.png"))
    xml = ('<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
           '    <background android:drawable="@color/ic_launcher_background" />\n'
           '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n</adaptive-icon>\n')
    for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
        open(os.path.join(res, "mipmap-anydpi-v26", name), "w", encoding="utf-8").write(xml)
    hexc = "#%02X%02X%02X" % navy
    open(os.path.join(res, "values", "ic_launcher_background.xml"), "w", encoding="utf-8").write(
        f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">{hexc}</color>\n</resources>')
    for p in glob.glob(os.path.join(res, "drawable*", "splash.png")):
        splash(art, Image.open(p).size).save(p)

    # iOS
    ios = A("ios", "App", "App", "Assets.xcassets")
    art.convert("RGB").save(os.path.join(ios, "AppIcon.appiconset", "AppIcon-512@2x.png"))
    for p in glob.glob(os.path.join(ios, "Splash.imageset", "*.png")):
        splash(art, Image.open(p).size).save(p)

    # Web マニフェスト・Play
    for n in (48, 72, 96, 128, 192, 256, 512):
        art.resize((n, n), Image.LANCZOS).save(A("icons", f"icon-{n}.webp"), "WEBP", quality=90)
    os.makedirs(A("store", "play"), exist_ok=True)
    art.resize((512, 512), Image.LANCZOS).convert("RGB").save(A("store", "play", "icon_512.png"))
    # アプリ内で使う小さいアイコン(ホームの頭・設定のこのアプリについて)
    masked(art.resize((240, 240), Image.LANCZOS), "rounded").save(A("public", "img", "app_icon.webp"), "WEBP", quality=90)

    # 確認用の絵
    os.makedirs(A("docs"), exist_ok=True)
    W = 1700
    sheet = Image.new("RGB", (W, 760), PAPER)
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 22)
    # 1) 前景+背景の全体(108dp)に安全域の円(直径66%)と見える範囲(72dp)
    full = Image.new("RGBA", (S, S), navy + (255,))
    full.alpha_composite(fg)
    chk = full.copy()
    cd = ImageDraw.Draw(chk)
    r = S * 0.66 / 2
    cd.ellipse([S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r], outline=(255, 80, 80, 255), width=6)
    v = S * 72 / 108 / 2
    cd.rectangle([S / 2 - v, S / 2 - v, S / 2 + v, S / 2 + v], outline=(255, 230, 0, 255), width=4)
    sheet.paste(chk.resize((420, 420)).convert("RGB"), (20, 60))
    d.text((20, 20), "適応アイコン 108dp(赤=安全域66% 黄=見える72dp)", fill=(0, 0, 0), font=f)
    x = 470
    for label, shape in (("丸", "circle"), ("角丸", "squircle"), ("四角に近い", "rounded")):
        im = masked(view.resize((300, 300), Image.LANCZOS), shape)
        sheet.paste(im, (x, 120), im)
        d.text((x, 80), label, fill=(0, 0, 0), font=f)
        x += 330
    d.text((20, 500), "iOS 1024(不透明)・48/96px", fill=(0, 0, 0), font=f)
    sheet.paste(art.resize((220, 220)), (20, 530))
    sheet.paste(art.resize((96, 96)), (260, 530))
    sheet.paste(art.resize((48, 48)), (370, 530))
    lr = Image.open(os.path.join(res, "mipmap-xxxhdpi", "ic_launcher_round.png"))
    sheet.paste(lr, (470, 530), lr)
    d.text((470, 500), "従来の丸 192", fill=(0, 0, 0), font=f)
    sheet.save(A("docs", "icon_check.png"))
    print("foreground", info)


if __name__ == "__main__":
    main()
