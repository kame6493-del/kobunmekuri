"""見出し用の明朝(Noto Serif JP、SIL OFL 1.1)を、アプリで使う文字だけの woff2 にする。
  python scripts/make_font.py → public/fonts/kobun-serif.woff2
文字は public/data/words.json と src/ の文字列から集める。太さの軸(可変)は残す。"""
import glob, json, os
from fontTools import subset
from fontTools.ttLib import TTFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get("KOBUN_SERIF", r"C:\Windows\Fonts\NotoSerifJP-VF.ttf")
chars = set(chr(c) for c in range(0x20, 0x7f))
chars |= set("ぁ-んァ-ヶー・、。「」『』〈〉()〔〕【】―…!?○×△◎%/〜")
for c in range(0x3041, 0x3097): chars.add(chr(c))
for c in range(0x30a1, 0x30fb): chars.add(chr(c))
for c in range(0xff01, 0xff5f): chars.add(chr(c))
chars |= set(open(os.path.join(ROOT, "public", "data", "words.json"), encoding="utf-8").read())
for f in glob.glob(os.path.join(ROOT, "src", "**", "*.ts*"), recursive=True):
    chars |= set(open(f, encoding="utf-8").read())
chars = {c for c in chars if ord(c) >= 0x20}
os.makedirs(os.path.join(ROOT, "public", "fonts"), exist_ok=True)
out = os.path.join(ROOT, "public", "fonts", "kobun-serif.woff2")
opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]; opts.name_IDs = ["*"]; opts.notdef_outline = True
font = TTFont(SRC)
s = subset.Subsetter(opts); s.populate(text="".join(sorted(chars))); s.subset(font)
font.flavor = "woff2"; font.save(out)
print(len(chars), "chars", os.path.getsize(out), "bytes")
