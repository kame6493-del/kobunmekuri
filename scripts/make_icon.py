"""アイコンを描く。python scripts/make_icon.py → assets/icon.png(1024) ・ icon-foreground/background ・ splash
墨色の地に、めくりかけの和紙の札。札に明朝の「古」、右下に朱の印。"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
os.makedirs(OUT, exist_ok=True)
INK = (38, 35, 32)
PAPER = (246, 241, 231)
PAPER2 = (229, 220, 202)
SHU = (184, 69, 47)
MINCHO = "C:/Windows/Fonts/yumindb.ttf"
S = 1024


def card_layer(size, scale=1.0):
    """札(めくれた右上の角つき)を透明な層に描く"""
    L = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    c = size / 2
    w, h = 560 * scale * size / S, 700 * scale * size / S
    x0, y0, x1, y1 = c - w / 2, c - h / 2, c + w / 2, c + h / 2
    fold = 150 * scale * size / S
    # 下の札(1枚めくった跡)
    d.rounded_rectangle([x0 + 26 * size / S, y0 + 30 * size / S, x1 + 26 * size / S, y1 + 30 * size / S], radius=28 * size / S, fill=PAPER2)
    # 上の札: 右上の角を折る
    d.polygon([(x0, y0 + 28 * size / S), (x0 + 28 * size / S, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1 - 28 * size / S), (x1 - 28 * size / S, y1), (x0 + 28 * size / S, y1), (x0, y1 - 28 * size / S)], fill=PAPER)
    d.polygon([(x1 - fold, y0), (x1 - fold, y0 + fold), (x1, y0 + fold)], fill=PAPER2)
    f = ImageFont.truetype(MINCHO, int(420 * scale * size / S))
    bb = d.textbbox((0, 0), "古", font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((c - tw / 2 - bb[0], c - th / 2 - bb[1] - 30 * scale * size / S), "古", font=f, fill=INK)
    r = 62 * scale * size / S
    sx, sy = x1 - 110 * scale * size / S, y1 - 110 * scale * size / S
    d.rounded_rectangle([sx - r, sy - r, sx + r, sy + r], radius=14 * size / S, fill=SHU)
    fs = ImageFont.truetype(MINCHO, int(84 * scale * size / S))
    bb = d.textbbox((0, 0), "めくり"[0], font=fs)
    d.text((sx - (bb[2] - bb[0]) / 2 - bb[0], sy - (bb[3] - bb[1]) / 2 - bb[1]), "め", font=fs, fill=PAPER)
    return L.rotate(-6, resample=Image.BICUBIC, center=(c, c))


def with_shadow(layer):
    a = layer.split()[3].filter(ImageFilter.GaussianBlur(18))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: v * 0.45))
    sh = Image.composite(Image.new("RGBA", layer.size, (0, 0, 0, 255)), sh, sh.split()[3]) if False else sh
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (10, 18))
    out.alpha_composite(layer)
    return out


icon = Image.new("RGBA", (S, S), INK + (255,))
icon.alpha_composite(with_shadow(card_layer(S)))
icon.convert("RGB").save(os.path.join(OUT, "icon.png"))
icon.convert("RGB").save(os.path.join(OUT, "icon-only.png"))
# Android の adaptive icon: 前景は安全域(中央66%)に収める
fg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
fg.alpha_composite(with_shadow(card_layer(S, 0.72)))
fg.save(os.path.join(OUT, "icon-foreground.png"))
Image.new("RGB", (S, S), INK).save(os.path.join(OUT, "icon-background.png"))
# スプラッシュ: 和紙色の地に小さい札
sp = Image.new("RGBA", (2732, 2732), PAPER + (255,))
small = with_shadow(card_layer(S, 0.9)).resize((620, 620), Image.LANCZOS)
sp.alpha_composite(small, ((2732 - 620) // 2, (2732 - 620) // 2))
sp.convert("RGB").save(os.path.join(OUT, "splash.png"))
sp.convert("RGB").save(os.path.join(OUT, "splash-dark.png"))
print("ok")
