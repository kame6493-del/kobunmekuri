"""画面に出る「苦手」を「まちがえた語」系の言葉に替える(App Store 4.3(a) 対策。ニガテ帳と同じ言葉を使わない)。
仕組み(2回続けて正解で外れる)は変えない。何度流しても同じ結果になる。
python tools/rename_nigate.py"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDITS = [
    ("src/App.tsx", "start('苦手だけ',", "start('まちがえた語だけ',"),
    ("src/ui/Home.tsx", "間違えた語は「苦手」に残り、2回続けて正解すると消えます。", "間違えた語は一覧に残り、2回続けて正解すると消えます。"),
    ("src/ui/Home.tsx", ">苦手 <b>", ">まちがい <b>"),
    ("src/ui/Home.tsx", "<b>苦手だけ</b>", "<b>まちがえた語だけ</b>"),
    ("src/ui/Paywall.tsx", "<td>苦手・今日の復習・逆算</td>", "<td>まちがえた語・今日の復習・逆算</td>"),
    ("src/ui/Quiz.tsx", "<li>苦手から外れた<b>", "<li>まちがいが消えた<b>"),
    ("src/ui/Quiz.tsx", "<li>新しく苦手に入った<b>", "<li>新しくまちがえた<b>"),
    ("src/ui/Quiz.tsx", '<span className="q-ng">苦手</span>', '<span className="q-ng">まちがい</span>'),
    ("src/ui/SettingsPage.tsx", "<p>苦手・復習の予定・連続日数がすべて消えます。", "<p>まちがえた語・復習の予定・連続日数がすべて消えます。"),
    ("src/ui/WordDetail.tsx", "`苦手(あと${2 - r.streak}回続けて正解で外れます)`", "`まちがえた語(あと${2 - r.streak}回続けて正解で外れます)`"),
    ("src/ui/WordList.tsx", "['nigate', '苦手']", "['nigate', 'まちがい']"),
    ("src/domain/study.ts", "/** 2回続けて正解したら苦手から外れる(ニガテ帳と同じ決まり) */", "/** 2回続けて正解したら、まちがえた語から外れる */"),
]
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel)
    s = open(p, encoding="utf-8").read()
    if new in s and old not in s:
        print("済", rel, new[:20])
        continue
    assert s.count(old) == 1, (rel, old, s.count(old))
    open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))
    print("替えた", rel, new[:20])
