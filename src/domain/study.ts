import type { AppData, Mode, Record1, Settings, Word } from './types';

/** 2回続けて正解したら、まちがえた語から外れる */
export const CLEAR_STREAK = 2;
/** 無料で使える見出し語(重要度順の上位) */
export const FREE_MAIN = 150;
/** 無料で試せる例文問題の数 */
export const EXAMPLE_TRIAL = 5;
/** 間隔反復の間隔(日)。箱 n に入った語は INTERVALS[n] 日後に出る */
export const INTERVALS = [0, 1, 3, 7, 14, 30, 60];
/** この箱以上を「覚えた」と数える(=1週間あけても答えられた) */
export const LEARNED_BOX = 4;

export const defaultSettings = (): Settings => ({ fontScale: 1, examDate: '', remind: false, remindAt: '20:00', batch: 10 });

export function emptyData(): AppData {
  return { version: 1, records: {}, settings: defaultSettings(), daily: {}, exTrial: 0 };
}

/** 保存データを読み込むときに欠けた所を埋める(古い版や壊れた値でも落ちない) */
export function normalize(x: unknown): AppData {
  const d = emptyData();
  if (!x || typeof x !== 'object') return d;
  const o = x as Partial<AppData>;
  if (o.records && typeof o.records === 'object') {
    for (const [k, r] of Object.entries(o.records)) {
      if (!r || typeof r !== 'object' || typeof r.n !== 'number') continue;
      d.records[k] = {
        n: r.n, ok: r.ok ?? 0, at: r.at ?? 0, streak: r.streak ?? 0, missed: !!r.missed,
        box: Math.max(0, Math.min(INTERVALS.length - 1, r.box ?? 0)), due: typeof r.due === 'string' ? r.due : '',
      };
    }
  }
  if (o.settings && typeof o.settings === 'object') d.settings = { ...d.settings, ...o.settings };
  if (o.daily && typeof o.daily === 'object') d.daily = { ...o.daily };
  if (typeof o.exTrial === 'number') d.exTrial = o.exTrial;
  return d;
}

export function dayKey(t: number): string {
  const d = new Date(t);
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export function addDays(t: number, n: number): number {
  const d = new Date(t);
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n, 12).getTime();
}

/** 鍵がかかっているか。無料は本編の上位 FREE_MAIN 語だけ。敬語・助動詞のセットは完全版 */
export function isLocked(w: Word, premium: boolean): boolean {
  if (premium) return false;
  return w.set !== 'main' || w.rank > FREE_MAIN;
}

/** 苦手 = 間違えたことがあって、まだ2回続けて正解していない語 */
export function isNigate(r: Record1 | undefined): boolean {
  return !!r && r.missed && r.streak < CLEAR_STREAK;
}

export function isLearned(r: Record1 | undefined): boolean {
  return !!r && r.box >= LEARNED_BOX && !isNigate(r);
}

/**
 * 1問答えた結果を書き込む。
 * 正解: 箱を1つ進め、その箱の間隔だけ先を次の復習日にする。不正解: 箱1に戻し、明日また出す。
 */
export function record(data: AppData, id: string, ok: boolean, now: number): AppData {
  const prev = data.records[id];
  const box = ok ? Math.min(INTERVALS.length - 1, (prev?.box ?? 0) + 1) : 1;
  const next: Record1 = {
    n: (prev?.n ?? 0) + 1,
    ok: (prev?.ok ?? 0) + (ok ? 1 : 0),
    at: now,
    streak: ok ? (prev?.streak ?? 0) + 1 : 0,
    missed: (prev?.missed ?? false) || !ok,
    box,
    due: dayKey(addDays(now, INTERVALS[box])),
  };
  const day = dayKey(now);
  return { ...data, records: { ...data.records, [id]: next }, daily: { ...data.daily, [day]: (data.daily[day] ?? 0) + 1 } };
}

/** 今日の復習 = 一度は答えた語のうち、復習日が今日か過ぎている語。期限の古い順 */
export function dueWords(words: Word[], data: AppData, now: number): Word[] {
  const today = dayKey(now);
  return words
    .filter((w) => { const r = data.records[w.id]; return !!r && !!r.due && r.due <= today; })
    .sort((a, b) => data.records[a.id]!.due.localeCompare(data.records[b.id]!.due) || a.rank - b.rank);
}

/** 苦手を解く順: 続けて正解した数が少ない → 間違えた割合が高い → 前に解いてから時間が経った */
export function nigateOrder(words: Word[], data: AppData): Word[] {
  return words.filter((w) => isNigate(data.records[w.id])).sort((a, b) => {
    const ra = data.records[a.id]!, rb = data.records[b.id]!;
    if (ra.streak !== rb.streak) return ra.streak - rb.streak;
    const ma = 1 - ra.ok / ra.n, mb = 1 - rb.ok / rb.n;
    if (ma !== mb) return mb - ma;
    return ra.at - rb.at;
  });
}

/** まだ一度も答えていない語(重要度順) */
export function unseen(words: Word[], data: AppData): Word[] {
  return words.filter((w) => !data.records[w.id]).sort((a, b) => a.rank - b.rank);
}

/** 試験日までの残り日数(今日を含めない)。過ぎていたら null */
export function daysLeft(examDate: string, now: number): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(examDate);
  if (!m) return null;
  const exam = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])).getTime();
  const t = new Date(now);
  const today = new Date(t.getFullYear(), t.getMonth(), t.getDate()).getTime();
  const d = Math.round((exam - today) / 86400000);
  return d >= 0 ? d : null;
}

export interface Plan {
  days: number;
  /** まだ覚えていない語 */
  remaining: number;
  /** 1日に新しく覚える語の数 */
  perDay: number;
  /** 一通り覚え終わる日 */
  finishDate: string;
  /** 仕上げの見直しに残る日数 */
  bufferDays: number;
}

/**
 * 試験日からの逆算。
 * 最後の2週間(残りが短ければ2割)は総復習に残し、それまでに未習の語を均等に割る。
 * 1日の数は最低5語、切り上げ。
 */
export function makePlan(words: Word[], data: AppData, examDate: string, now: number): Plan | null {
  const days = daysLeft(examDate, now);
  if (days === null) return null;
  const remaining = words.filter((w) => !isLearned(data.records[w.id])).length;
  const buffer = Math.min(14, Math.floor(days * 0.2));
  const studyDays = Math.max(1, days - buffer);
  const perDay = remaining === 0 ? 0 : Math.max(5, Math.ceil(remaining / studyDays));
  const need = perDay ? Math.ceil(remaining / perDay) : 0;
  return { days, remaining, perDay, finishDate: dayKey(addDays(now, Math.max(0, need - 1))), bufferDays: Math.max(0, days - need) };
}

/** 再現できる乱数(テスト用・出題の並び用) */
export function rng(seed: number) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >>> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

export function shuffle<T>(xs: T[], rand: () => number): T[] {
  const a = xs.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export interface Question {
  word: Word;
  mode: Mode;
  /** 問題として見せる文字 */
  prompt: string;
  choices: string[];
  answer: number;
  /** 例文問題のときの例文 */
  exIndex?: number;
}

/** 選択肢に出す文字(意味の問題は quiz、語を当てる問題は見出し語) */
const label = (w: Word, mode: Mode) => (mode === 'reverse' ? w.w : w.quiz);

/**
 * 4択を作る。外れは「同じセット」「違う意味の分類」「正解と同じ文字にならない」語から選ぶ。
 * 品詞が同じ語を優先して、品詞だけで見抜けないようにする。
 */
export function makeQuestion(word: Word, mode: Mode, pool: Word[], rand: () => number, exIndex = 0): Question {
  const right = label(word, mode);
  // 同じ見出しの別項目(たてまつる 謙譲/尊敬、なり 断定/伝聞推定 など)は、外れにすると正解が2つになるので使わない
  const sameSet = pool.filter((p) => p.id !== word.id && p.w !== word.w && p.set === word.set && label(p, mode) !== right && (p.cat !== word.cat || p.cat === 'その他' || word.set !== 'main'));
  const keyOf = (p: Word) => (word.set === 'jodoshi' ? p.quiz : label(p, mode));
  const pick: Word[] = [];
  const seen = new Set([keyOf(word)]);
  for (const group of [sameSet.filter((p) => p.pos === word.pos), sameSet]) {
    for (const p of shuffle(group, rand)) {
      if (pick.length >= 3) break;
      const k = keyOf(p);
      if (seen.has(k)) continue;
      seen.add(k);
      pick.push(p);
    }
  }
  const choices = shuffle([word, ...pick], rand);
  let prompt = word.w;
  if (mode === 'reverse') prompt = word.quiz;
  if (mode === 'example') prompt = word.ex[exIndex]?.text ?? word.w;
  const options = choices.map((c) => label(c, mode));
  // 例文問題の正解は、その例文で使われている意味
  if (mode === 'example' && word.ex[exIndex]) {
    const i = choices.indexOf(word);
    options[i] = word.set === 'jodoshi' ? word.means[word.ex[exIndex].sense] : (word.ex[exIndex].sense === 0 ? word.quiz : word.means[word.ex[exIndex].sense]);
    if (word.set === 'jodoshi') {
      // 助動詞は同じ語の別の意味を外れにする(見分けが問われる所)
      const others = word.means.filter((_, k) => k !== word.ex[exIndex].sense);
      const fill = shuffle(['完了', '過去', '推量', '打消', '断定', '受身', '使役', '存続', '意志', '当然'].filter((m) => !word.means.includes(m)), rand);
      const wrong = [...shuffle(others, rand), ...fill].slice(0, 3);
      const all = shuffle([options[i], ...wrong], rand);
      return { word, mode, prompt, choices: all, answer: all.indexOf(options[i]), exIndex };
    }
  }
  return { word, mode, prompt, choices: options, answer: choices.indexOf(word), exIndex };
}

/** 敬語の種類の3択。選択肢の並びは毎回「尊敬・謙譲・丁寧」で固定(並びが変わると押し間違える) */
export const KEIGO_KINDS = ['尊敬', '謙譲', '丁寧'];
/** 種類の問題に出せる敬語。見出しと漢字が同じで種類だけ違う物(たてまつる・はべり など)は、見ただけでは決まらないので外す */
export function kindQuizWords(words: Word[]): Word[] {
  return words.filter((w) => !words.some((o) => o.id !== w.id && o.w === w.w && o.kanji === w.kanji && o.kind !== w.kind));
}
export function makeKindQuestion(word: Word): Question {
  return { word, mode: 'mean', prompt: word.w, choices: KEIGO_KINDS.map((k) => k + '語'), answer: Math.max(0, KEIGO_KINDS.indexOf(word.kind ?? '')) };
}

/** 続けて勉強した日数(今日まだなら昨日までで数える) */
export function streakDays(daily: Record<string, number>, now: number): number {
  let t = now;
  if (!daily[dayKey(t)]) t -= 86400000;
  let n = 0;
  while (daily[dayKey(t)]) { n++; t -= 86400000; }
  return n;
}

export interface Progress { total: number; seen: number; learned: number; nigate: number }

export function progress(words: Word[], data: AppData): Progress {
  let seen = 0, learned = 0, nigate = 0;
  for (const w of words) {
    const r = data.records[w.id];
    if (!r) continue;
    seen++;
    if (isLearned(r)) learned++;
    if (isNigate(r)) nigate++;
  }
  return { total: words.length, seen, learned, nigate };
}

/** 文字列の中の hit を強調表示用に3つに分ける */
export function splitHit(text: string, hit: string): [string, string, string] {
  const i = text.indexOf(hit);
  if (i < 0 || !hit) return [text, '', ''];
  return [text.slice(0, i), hit, text.slice(i + hit.length)];
}
