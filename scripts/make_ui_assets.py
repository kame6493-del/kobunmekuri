"""画面の絵(public/img/*.webp)を、持ち主が用意した見本画像 kobun_ref_1〜7 から切り出して作る。
  python scripts/make_ui_assets.py
- 見本は 941x1672 と小さいので、Real-ESRGAN(scripts/esrgan.py)で4倍にしてから使う
- cut: 和紙の地の色を透明にする(アイコン類) / feather: 縁をぼかして地になじませる(景色の絵) / none: そのまま
- inpaint: 絵の上に乗っている見本の文字を消す(元の座標で指定)
- 新しく描いた物はここには無い(線のアイコンは src/ui/Icons.tsx の SVG)"""
import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from esrgan import up4  # noqa: E402

REF = os.environ.get("KOBUN_REF", r"C:\Users\yuichi1\Downloads")
OUT = os.path.join(ROOT, "public", "img")
os.makedirs(OUT, exist_ok=True)
_refs = {}


def ref(n):
    if n not in _refs:
        _refs[n] = Image.open(os.path.join(REF, f"kobun_ref_{n}_941x1672.png")).convert("RGB")
    return _refs[n]


# 名前: (見本の番号, 切り出す枠 x0,y0,x1,y1, 方式, 文字を消す枠のリスト)
ASSETS = {
    # 景色(ホームの頭・各画面の頭・カードの下)
    "head_home": (1, (550, 262, 908, 377), "feather", [(630, 262, 830, 287), (838, 262, 860, 275)]),
    "head_sub": (7, (113, 374, 414, 444), "feather", []),
    "land_pagoda": (2, (79, 708, 407, 791), "feather", []),
    "land_bridge": (2, (544, 708, 867, 790), "feather", []),
    "land_card": (2, (350, 1392, 576, 1468), "feather", []),
    "plum_corner": (2, (78, 393, 122, 482), "cut", []),
    # 空の状態・おわり
    "empty_cat": (7, (38, 1113, 302, 1349), "feather", []),
    "empty_veranda": (7, (345, 1113, 600, 1341), "none", []),
    "done_ema": (7, (643, 1113, 903, 1306), "feather", []),
    "books_plum": (7, (562, 692, 818, 838), "feather", []),
    # 色のアイコン
    "ic_review": (1, (616, 496, 675, 548), "cut", []),
    "ic_shelf": (1, (788, 496, 844, 548), "cut", []),
    "ic_omamori": (1, (618, 652, 672, 707), "cut", []),
    "ic_scroll_pen": (1, (791, 652, 854, 707), "cut", []),
    "ic_book_green": (1, (570, 385, 610, 418), "cut", []),
    "ic_crown": (1, (262, 970, 312, 1010), "cut", []),
    "ic_seal": (1, (388, 108, 417, 143), "cut", []),
    "ic_sprig": (1, (557, 778, 607, 818), "cut", []),
    "ic_plum": (6, (166, 414, 200, 452), "cut", []),
    "ic_book": (6, (144, 490, 206, 540), "cut", []),
    "ic_doc": (6, (148, 563, 201, 616), "cut", []),
    "ic_fan": (6, (141, 638, 208, 690), "cut", []),
    "ic_scroll": (6, (144, 714, 206, 776), "cut", []),
    "ic_ok": (3, (158, 1174, 212, 1228), "cut", []),
    "ic_ng": (3, (615, 1175, 670, 1230), "cut", []),
    "ic_books": (2, (652, 1465, 722, 1538), "cut", []),
    "ic_noreg": (7, (574, 465, 652, 542), "cut", []),
    "ic_noad": (7, (712, 465, 790, 542), "cut", []),
    "ic_calendar": (5, (78, 997, 133, 1039), "cut", []),
    "ic_trophy": (5, (624, 1158, 667, 1197), "cut", []),
    "ic_leaf": (6, (222, 1228, 248, 1255), "cut", []),
    "ic_bell": (7, (138, 462, 170, 496), "cut", []),
}


def inpaint(im, boxes, origin):
    if not boxes:
        return im
    a = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)
    m = np.zeros(a.shape[:2], np.uint8)
    for x0, y0, x1, y1 in boxes:
        m[max(0, y0 - origin[1]):y1 - origin[1], max(0, x0 - origin[0]):x1 - origin[0]] = 255
    a = cv2.inpaint(a, m, 5, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))


def cut(im):
    """縁の色(和紙の地)からの離れ具合を不透明度にする"""
    a = np.asarray(im).astype(np.float32)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(border, axis=0)
    d = np.sqrt(((a - bg) ** 2).sum(-1))
    alpha = np.clip((d - 14) / 34, 0, 1)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.0)
    # 地に残った色(和紙の黄み)を引いて、地の上に置いたとき縁が濁らないようにする
    out = np.dstack([a, alpha * 255]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")
    bbox = img.getchannel("A").point(lambda v: 255 if v > 10 else 0).getbbox()
    return img.crop(bbox) if bbox else img


def feather(im, edge=0.09):
    w, h = im.size
    m = np.ones((h, w), np.float32)
    ex, ey = int(w * edge), int(h * edge * 1.3)
    ramp = lambda n: (np.sin(np.linspace(0, np.pi / 2, n)) ** 2)
    m[:, :ex] *= ramp(ex)[None, :]
    m[:, w - ex:] *= ramp(ex)[::-1][None, :]
    m[:ey, :] *= ramp(ey)[:, None]
    m[h - ey:, :] *= ramp(ey)[::-1][:, None]
    out = im.convert("RGBA")
    out.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    return out


def build(name, spec):
    n, box, mode, boxes = spec
    im = ref(n).crop(box)
    im = inpaint(im, boxes, box[:2])
    big = up4(im)
    if mode == "cut":
        big = cut(big)
    elif mode == "feather":
        big = feather(big)
    path = os.path.join(OUT, name + ".webp")
    big.save(path, "WEBP", quality=84, method=6)
    return path, big.size


if __name__ == "__main__":
    only = sys.argv[1:]
    for k, v in ASSETS.items():
        if only and k not in only:
            continue
        p, s = build(k, v)
        print(k, s, os.path.getsize(p))
