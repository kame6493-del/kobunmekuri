import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import type { Word } from './types';
import { FREE_MAIN, makeQuestion, rng } from './study';

/** 出荷する単語データそのものを検査する(public/data/words.json) */
const words: Word[] = JSON.parse(readFileSync(new URL('../../public/data/words.json', import.meta.url), 'utf-8'));
const main = words.filter((w) => w.set === 'main');

describe('単語データ', () => {
  it('本編は600語前後(最低300)で、重要度は1から欠けなく並ぶ', () => {
    expect(main.length).toBeGreaterThanOrEqual(300);
    expect(main.map((w) => w.rank)).toEqual(main.map((_, i) => i + 1));
  });
  it('id は重複しない', () => {
    expect(new Set(words.map((w) => w.id)).size).toBe(words.length);
  });
  it('無料の範囲(上位150語)はすべて例文つき', () => {
    expect(main.slice(0, FREE_MAIN).every((w) => w.ex.length > 0)).toBe(true);
  });
  it('例文の印の語は本文の中にあり、意味の番号は範囲内、出典が付いている', () => {
    for (const w of words) for (const e of w.ex) {
      expect(e.text.includes(e.hit), `${w.w}: ${e.hit}`).toBe(true);
      expect(e.sense >= 0 && e.sense < w.means.length, `${w.w}: sense`).toBe(true);
      expect(e.src.length > 1, `${w.w}: src`).toBe(true);
    }
  });
  it('太字記法・絵文字が入っていない', () => {
    const s = JSON.stringify(words);
    expect(s.includes('**')).toBe(false);
    expect(/[\u{1F300}-\u{1FAFF}]/u.test(s)).toBe(false);
  });
  it('全語で4択が作れ、正解が1つだけ', () => {
    const rand = rng(11);
    for (const w of main) {
      const q = makeQuestion(w, 'mean', words, rand);
      expect(q.choices.length).toBe(4);
      expect(q.choices.filter((c) => c === w.quiz).length).toBe(1);
    }
  });
});
