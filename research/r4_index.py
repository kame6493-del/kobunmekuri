# -*- coding: utf-8 -*-
"""本文を1文ずつに切り、作品名と巻・段などの場所を付ける。→ research/sentences.jsonl
例文の照合(tools/validate.py)と、見出し語ごとの候補文の抽出(r5_candidates.py)に使う。"""
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
C, R = os.path.join(HERE, "corpus"), os.path.join(HERE, "corpus_r")

OLD = ("國国 萬万 佛仏 與与 續続 聲声 戀恋 變変 參参 歸帰 氣気 實実 舊旧 樂楽 學学 覺覚 擧挙 圓円 處処 傳伝 體体 會会 爲為 將将 從従 齒歯 盡尽 晝昼 惠恵 澤沢 濱浜 邊辺 靈霊 戰戦 數数 歡歓 觀観 權権 譽誉 讀読 賣売 寶宝 廣広 雜雑 醫医 單単 嚴厳 壽寿 稱称 莊荘 辭辞 "
       "鐵鉄 顯顕 髮髪 黑黒 默黙 齋斎 亂乱 假仮 兒児 兩両 內内 劍剣 卽即 卷巻 圍囲 壞壊 壯壮 奧奥 寢寝 寫写 對対 屬属 廳庁 彈弾 徑径 惡悪 戲戯 拂払 拔抜 收収 敎教 曉暁 條条 榮栄 櫻桜 歲歳 歷歴 殘残 每毎 淺浅 淸清 溫温 滿満 燈灯 營営 爭争 狀状 獨独 獻献 疊畳 發発 盜盗 眞真 碎砕 祕秘 禮礼 "
       "穗穂 經経 絲糸 綠緑 緖緒 縣県 總総 繪絵 繼継 聽聴 腦脳 舍舎 艷艶 藏蔵 蟲虫 螢蛍 衞衛 裝装 覽覧 觸触 證証 豐豊 轉転 輕軽 辨弁 遲遅 鄕郷 醉酔 釋釈 錢銭 鎭鎮 關関 隱隠 險険 隨随 雙双 靜静 頰頬 顏顔 飮飲 驗験 鷄鶏 麥麦 黃黄 點点 齡齢 姬姫 惱悩 應応 懷懐 搖揺 曆暦 檢検 淚涙 澁渋 濟済 瀨瀬 爐炉 畫画 "
       "當当 稻稲 絕絶 緣縁 繩縄 臺台 藝芸 號号 譯訳 讓譲 豫予 賴頼 鄰隣 錄録 靑青 餘余 騷騒 驅駆 鹽塩 黨党 齊斉 龜亀 戾戻 敍叙 步歩 涉渉 祿禄 禪禅 稅税 德徳 廢廃 拜拝 據拠 擔担 斷断 樣様 橫横 沒没 淨浄 燒焼 狹狭 產産 穩穏 竝並 纖繊 薰薫 虛虚 蟬蝉 謠謡 郞郎 銳鋭 陷陥 鬭闘 晩晩 歎歎 "
       "卑卑 碑碑 祈祈 祖祖 神神 祝祝 福福 禍禍 都都 者者 諸諸 著著 暑暑 署署 緒緒 渚渚 煮煮 猪猪 賓賓 頻頻 類類 隆隆 館館 器器 突突 臭臭 塚塚 層層 侮侮 勤勤 嘆嘆 漢漢 難難 謹謹 墨墨 憎憎 僧僧 增増 贈贈 悔悔 敏敏 梅梅 海海 繁繁 每毎 欄欄 廊廊 朗朗 曾曽 揭掲 渴渇 謁謁 喝喝 褐褐 "
       "瘦痩 晉晋 冱冴 册冊 凉涼 况況 冲沖 册冊 剩剰 勞労 勳勲 匯匯 區区 卻却 參参 收収 啓啓 嚴厳 圈圏 堯尭 壓圧 壘塁 奬奨 孃嬢 寬寛 寳宝 尙尚 屆届 岡岡 峯峰 巢巣 帶帯 弘弘 彌弥 徵徴 恆恒 惠恵 慘惨 慣慣 戶戸 拔抜 揷挿 攝摂 擊撃 晚晩 曉暁 朗朗 枡枡 柳柳 栖栖 榊榊 檜桧 欵款 歐欧 殼殻 "
       "渊淵 溪渓 滯滞 灣湾 炎炎 焰炎 熱熱 爵爵 犧犠 獵猟 珎珍 瓣弁 瓶瓶 甁瓶 疎疎 癡痴 盃盃 眾衆 硏研 碍碍 禀稟 秃禿 稻稲 穀穀 竊窃 粹粋 糺糾 緜綿 縱縦 繡繍 羣群 聰聡 肅粛 脉脈 臟臓 莖茎 萠萌 蔣蒋 蘆芦 處処 蠅蝿 蠶蚕 衆衆 裏裏 褒褒 覇覇 觀観 訣訣 說説 諭諭 謌歌 讃讃 豬猪 貍狸 "
       "賤賤 贊賛 踐践 躰体 輯輯 辯弁 遞逓 遙遥 遷遷 邉辺 醬醤 鈴鈴 鉤鈎 錬錬 鍊錬 鑄鋳 鑛鉱 閒間 陰陰 隣隣 雞鶏 雜雑 響響 頸頸 顚顛 顧顧 飜翻 餅餅 騎騎 驛駅 髓髄 鬱鬱 鬼鬼 鳴鳴 麪麺 黄黄 默黙 龍竜 來来 學学 歸帰")
OLDMAP = {}
for p in OLD.split():
    if len(p) == 2 and p[0] != p[1]:
        OLDMAP[p[0]] = p[1]

VOICE = dict(zip("かきくけこさしすせそたちつてとはひふへほカキクケコサシスセソタチツテトハヒフヘホ", "がぎぐげござじずぜぞだぢづでどばびぶべぼガギグゲゴザジズゼゾダヂヅデドバビブベボ"))


def norm_display(t):
    """見せる形: 注の〔〕を消す、踊り字を戻す、旧字を新字に"""
    t = re.sub(r"〔[^〕]*〕", "", t)
    t = re.sub(r"〈[^〉]*〉", "", t)
    t = re.sub(r"（[^）]{0,20}）", "", t)
    t = t.replace("＼\"／", "〴〵").replace("＼／", "〳〵").replace("／＼", "〳〵").replace("＊", "〳〵")
    out = []
    for ch in t:
        if ch == "ゝ" and out:
            out.append(out[-1])
        elif ch == "ゞ" and out:
            out.append(VOICE.get(out[-1], out[-1]))
        else:
            out.append(ch)
    t = "".join(out)
    # くの字点: 直前の2文字を繰り返す(〴〵は1文字目を濁る)
    def rep(m):
        s, mark = m.group(1), m.group(2)
        return s + (VOICE.get(s[0], s[0]) + s[1:] if mark == "〴〵" else s)
    t = re.sub(r"(..)(〳〵|〴〵)", rep, t)
    t = "".join(OLDMAP.get(c, c) for c in t)
    return t


PUNCT = re.compile(r"[\s、。，．・「」『』（）()〈〉《》“”\"'！？!?　―…‥－\-]")


def norm_key(t):
    """照合用: 句読点・かぎかっこ・空白を落とす"""
    return PUNCT.sub("", norm_display(t))


sents = []


def add(work, loc, text):
    for para in text.split("\n"):
        para = para.strip()
        if not para or para.startswith(("Category:", "*", "#", "底本", "姉妹", "他の版", "書誌", "作者", "==")):
            continue
        for s in re.findall(r"[^。]+。?", para):
            s = norm_display(s).strip()
            if len(PUNCT.sub("", s)) < 6:
                continue
            sents.append({"work": work, "loc": loc, "text": s})


def read(p):
    return open(p, encoding="utf-8").read()


KANJI_NUM = "〇一二三四五六七八九十百"


def kanji_num(n):
    n = int(n)
    d = "〇一二三四五六七八九"
    if n < 10:
        return d[n]
    if n < 100:
        t, o = divmod(n, 10)
        return ("" if t == 1 else d[t]) + "十" + ("" if o == 0 else d[o])
    h, r = divmod(n, 100)
    return ("" if h == 1 else d[h]) + "百" + ("" if r == 0 else kanji_num(r))


# 源氏物語(巻ごとの頁)
for p in sorted(glob.glob(os.path.join(C, "源氏物語", "源氏物語_*.txt"))):
    maki = os.path.basename(p)[len("源氏物語_"):-4]
    add("源氏物語", maki, read(p))

# 枕草子(段ごとの頁。重複する2系統は Wikisource 版を優先)
seen_dan = set()
for p in sorted(glob.glob(os.path.join(C, "枕草子", "枕草子*_第*段.txt")), key=lambda x: ("Wikisource" not in x, x)):
    dan = re.search(r"_(第.+段)\.txt", p).group(1)
    if dan in seen_dan:
        continue
    t = read(p)
    if t.startswith("#転送") or len(t) < 80:
        continue
    seen_dan.add(dan)
    t = t.split("==出典==")[0].split("== 出典 ==")[0]
    add("枕草子", dan, t)

# 徒然草(数字だけの行が段の始まり)
def numbered(work, path, fmt):
    loc = None
    buf = []
    for line in read(path).split("\n"):
        s = line.strip()
        if work == "徒然草" and loc == "第一段" and s.startswith("いでや"):
            add(work, "序段", "\n".join(buf))
            buf = []
        if re.fullmatch(r"\d{1,3}", s):
            if loc and buf:
                add(work, loc, "\n".join(buf))
            loc, buf = fmt(int(s)), []
        elif loc:
            buf.append(line)
    if loc and buf:
        add(work, loc, "\n".join(buf))

numbered("徒然草", os.path.join(R, "徒然草", "徒然草 (校註日本文學大系).txt"), lambda n: "第%s段" % kanji_num(n) if n else "序段")
numbered("竹取物語", os.path.join(R, "竹取物語", "竹取物語 (國民文庫).txt"), lambda n: "第%s節" % kanji_num(n))

# 更級日記(「1 東路の道のはてよりも」形式の見出し)
loc, buf = None, []
for line in read(os.path.join(C, "更級日記", "更級日記 (有朋堂文庫).txt")).split("\n"):
    m = re.fullmatch(r"\s*(\d{1,3}) (.+)", line)
    if m:
        if loc and buf:
            add("更級日記", loc, "\n".join(buf))
        loc, buf = "「%s」" % norm_display(m.group(2)).strip(), []
    elif loc:
        buf.append(line)
if loc and buf:
    add("更級日記", loc, "\n".join(buf))

# 1冊ひとまとまりで場所を細かく付けない作品
for work, path in [("紫式部日記", os.path.join(R, "紫式部日記", "紫式部日記 (渋谷栄一校訂).txt")),
                   ("方丈記", os.path.join(R, "方丈記", "方丈記 (國文大觀).txt")),
                   ("和泉式部日記", os.path.join(R, "和泉式部日記", "和泉式部日記.txt")),
                   ("おくのほそ道", os.path.join(R, "おくのほそ道", "おくのほそ道.txt")),
                   ("十六夜日記", os.path.join(R, "十六夜日記", "十六夜日記 (國文大觀).txt"))]:
    add(work, "", read(path))

# 土佐日記(日付の行で場所を付ける)
loc, buf = "", []
for line in read(os.path.join(R, "土佐日記", "土佐日記 (國文大觀).txt")).split("\n"):
    m = re.match(r"\s*((?:[十二三四五六七八九一]+月)?(?:[十二三四五六七八九一]+|つごもり|ついたち)[日の]?)", line)
    d = re.match(r"\s*([一二三四五六七八九十廿]{1,3}日)", line)
    if d:
        if buf:
            add("土佐日記", loc, "\n".join(buf))
        loc, buf = d.group(1), [line]
    else:
        buf.append(line)
add("土佐日記", loc, "\n".join(buf))

# 大鏡・蜻蛉日記(巻の見出しで場所を付ける)
for work, path, pat in [("大鏡", os.path.join(R, "大鏡", "大鏡 (國文大觀).txt"), r"大鏡卷之(.)"),
                        ("蜻蛉日記", os.path.join(R, "蜻蛉日記", "蜻蛉日記 (國文大觀).txt"), r"蜻蛉日記(?:卷)?(上|中|下)")]:
    loc, buf = "", []
    for line in read(path).split("\n"):
        m = re.search(pat, line.strip())
        if m and len(line.strip()) < 16:
            if buf:
                add(work, loc, "\n".join(buf))
            loc, buf = (("巻" + norm_display(m.group(1))) if work == "大鏡" else (m.group(1) + "巻")), []
        else:
            buf.append(line)
    add(work, loc, "\n".join(buf))

with open(os.path.join(HERE, "sentences.jsonl"), "w", encoding="utf-8") as f:
    for i, s in enumerate(sents):
        s["id"] = i
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
from collections import Counter
print(len(sents), Counter(s["work"] for s in sents))
print(Counter((s["work"], s["loc"]) for s in sents if s["work"] in ("大鏡", "蜻蛉日記", "土佐日記")).most_common(12))
