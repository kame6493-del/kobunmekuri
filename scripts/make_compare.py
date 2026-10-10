"""見本(kobun_ref_1〜7)と作り直した画面(docs/screens/375)を並べた比較画像を作る。
  python scripts/make_compare.py → docs/compare_redesign_1〜7.png と docs/compare_redesign_all.png"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.environ.get("KOBUN_REF", r"C:\Users\yuichi1\Downloads")
SC = os.path.join(ROOT, "docs", "screens", "375")
F = ImageFont.truetype("C:/Windows/Fonts/meiryob.ttc", 26)
F2 = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 20)
PAIRS = {
    1: ("ホーム・タブ・カード", ["01_home", "02_study", "04_dict", "03_nigate"]),
    2: ("重要語からめくる・カード・学習結果", ["15_card_front", "16_card_back", "09_mean_q", "17_result"]),
    3: ("4択クイズ・正解時・不正解時", ["09_mean_q", "12_reverse_q", "10_mean_right", "11_mean_wrong"]),
    4: ("例文で当てる・単語詳細・辞書", ["13_example_q", "05_detail", "05_detail_b", "04_dict"]),
    5: ("今日の復習・苦手・学習計画・結果", ["08_review", "03_nigate", "07_plan", "17_result_b"]),
    6: ("完全版・比較・敬語セット・助動詞セット", ["19_paywall", "19_paywall_b", "22_keigo", "24_jodoshi"]),
    7: ("設定・このアプリについて・空の状態", ["06_settings", "06_settings_b", "20_empty_nigate", "21_empty_review", "25_review_done"]),
}
BG = (238, 232, 218)


def main():
    outs = []
    for n, (title, names) in PAIRS.items():
        ref = Image.open(os.path.join(REF, f"kobun_ref_{n}_941x1672.png")).convert("RGB")
        cols = 3 if len(names) > 4 else 2
        rows = (len(names) + cols - 1) // cols
        sw = 375
        sh = 812
        scale = min(1.0, 1672 / (rows * (sh + 34)))
        tw, th = int(sw * scale), int(sh * scale)
        right_w = cols * (tw + 16) + 16
        W = 941 + 40 + right_w + 20
        H = 1672 + 90
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        d.text((20, 20), f"見本 kobun_ref_{n}", fill=(60, 50, 40), font=F)
        d.text((941 + 50, 20), f"作り直した画面(375幅) ― {title}", fill=(30, 58, 95), font=F)
        im.paste(ref, (20, 70))
        for k, name in enumerate(names):
            s = Image.open(os.path.join(SC, name + ".png")).convert("RGB").resize((tw, th), Image.LANCZOS)
            x = 941 + 40 + 16 + (k % cols) * (tw + 16)
            y = 70 + (k // cols) * (th + 34)
            d.text((x, y), name, fill=(100, 90, 80), font=F2)
            im.paste(s, (x, y + 28))
            d.rectangle([x - 1, y + 27, x + tw, y + 28 + th], outline=(200, 190, 170))
        p = os.path.join(ROOT, "docs", f"compare_redesign_{n}.png")
        im.save(p, optimize=True)
        outs.append(p)
        print(p, im.size)
    # 一覧
    thumbs = [Image.open(p) for p in outs]
    tw = 900
    ts = [t.resize((tw, int(t.height * tw / t.width)), Image.LANCZOS) for t in thumbs]
    cols = 2
    rows = (len(ts) + 1) // cols
    th = max(t.height for t in ts)
    allim = Image.new("RGB", (cols * (tw + 20) + 20, rows * (th + 20) + 20), (220, 212, 196))
    for k, t in enumerate(ts):
        allim.paste(t, (20 + (k % cols) * (tw + 20), 20 + (k // cols) * (th + 20)))
    allim.save(os.path.join(ROOT, "docs", "compare_redesign_all.png"), optimize=True)
    print("all", allim.size)


if __name__ == "__main__":
    main()
