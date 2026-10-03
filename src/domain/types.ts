/** 例文1つ。text は古典本文のそのままの一部、tr は自作の現代語訳 */
export interface Example {
  text: string;
  /** text の中で見出し語が出てくる部分(活用したまま) */
  hit: string;
  tr: string;
  /** means の何番目の意味で使われているか */
  sense: number;
  /** 「徒然草・第百八段」のような出典 */
  src: string;
}

export type WordSet = 'main' | 'keigo' | 'jodoshi';

export interface Word {
  /** "m001" / "k01" / "j01" */
  id: string;
  set: WordSet;
  /** セットの中での重要度順(1が最重要) */
  rank: number;
  w: string;
  kanji: string;
  pos: string;
  /** 意味の分類。4択の外れの選択肢を近い意味から選ばないために使う */
  cat: string;
  means: string[];
  /** 4択で正解として出す短い意味 */
  quiz: string;
  note: string;
  ex: Example[];
  /** 敬語: 尊敬・謙譲・丁寧 */
  kind?: string;
  /** 敬語: 普通の語 */
  plain?: string;
  /** 助動詞: 接続 */
  conn?: string;
}

export interface Record1 {
  /** 答えた回数 */
  n: number;
  ok: number;
  /** 最後に答えた時刻(ms) */
  at: number;
  /** 最後の結果から続いている正解の数 */
  streak: number;
  /** 一度でも間違えたか */
  missed: boolean;
  /** 間隔反復の箱(0〜6)。大きいほど覚えている */
  box: number;
  /** 次に復習する日 "2026-10-04" */
  due: string;
}

export interface Settings {
  fontScale: number;
  /** 試験日 "2027-01-16"。空なら逆算しない */
  examDate: string;
  remind: boolean;
  remindAt: string;
  /** 一度に出す問題の数 */
  batch: number;
}

export interface AppData {
  version: 1;
  records: Record<string, Record1>;
  settings: Settings;
  /** 日ごとの答えた数 */
  daily: Record<string, number>;
  /** 無料の例文おためしを使った数 */
  exTrial: number;
}

export type Mode = 'mean' | 'reverse' | 'example' | 'card';
