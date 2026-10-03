import { describe, expect, it } from 'vitest';
import type { Word } from './types';
import {
  CLEAR_STREAK, kindQuizWords, EXAMPLE_TRIAL, FREE_MAIN, INTERVALS, KEIGO_KINDS, addDays, daysLeft, dayKey, dueWords, emptyData, isLearned, isLocked, isNigate,
  makeKindQuestion, makePlan, makeQuestion, nigateOrder, normalize, progress, record, rng, splitHit, streakDays, unseen,
} from './study';

const CATS = ['感動・趣', '不快・嫌悪', '時・時間', '程度・強調', '様子・状態'];
function word(i: number, extra: Partial<Word> = {}): Word {
  return {
    id: `m${String(i).padStart(3, '0')}`, set: 'main', rank: i, w: `語${i}`, kanji: '', pos: i % 2 ? '形容詞' : '動詞', cat: CATS[i % CATS.length],
    means: [`意味${i}`, `別義${i}`], quiz: `意味${i}`, note: '', ex: [{ text: `本文${i}の語${i}を含む`, hit: `語${i}`, tr: '訳', sense: 1, src: '徒然草・第一段' }], ...extra,
  };
}
const WORDS = Array.from({ length: 300 }, (_, k) => word(k + 1));
const T0 = new Date(2026, 9, 4, 9).getTime();

describe('記録と苦手', () => {
  it('間違えると苦手に入り、2回続けて正解すると外れる', () => {
    let d = emptyData();
    d = record(d, 'm001', false, T0);
    expect(isNigate(d.records.m001)).toBe(true);
    d = record(d, 'm001', true, T0 + 1);
    expect(isNigate(d.records.m001)).toBe(true);
    d = record(d, 'm001', true, T0 + 2);
    expect(d.records.m001.streak).toBe(CLEAR_STREAK);
    expect(isNigate(d.records.m001)).toBe(false);
  });
  it('正解続きの途中で間違えると、また2回続けて正解が要る', () => {
    let d = emptyData();
    for (const ok of [false, true, false, true]) d = record(d, 'm001', ok, T0);
    expect(isNigate(d.records.m001)).toBe(true);
  });
  it('一度も間違えていない語は苦手にならない', () => {
    const d = record(emptyData(), 'm002', true, T0);
    expect(isNigate(d.records.m002)).toBe(false);
  });
  it('日ごとの答えた数を数える', () => {
    let d = record(emptyData(), 'm001', true, T0);
    d = record(d, 'm002', false, T0 + 1000);
    expect(d.daily[dayKey(T0)]).toBe(2);
  });
  it('苦手を解く順は、続けて正解した数が少ない物から', () => {
    let d = emptyData();
    d = record(d, 'm001', false, T0); d = record(d, 'm001', true, T0 + 1);
    d = record(d, 'm002', false, T0 + 2);
    expect(nigateOrder(WORDS, d).map((w) => w.id)).toEqual(['m002', 'm001']);
  });
});

describe('間隔反復', () => {
  it('正解で箱が進み、間隔の日数だけ先が復習日になる', () => {
    let d = record(emptyData(), 'm001', true, T0);
    expect(d.records.m001.box).toBe(1);
    expect(d.records.m001.due).toBe(dayKey(addDays(T0, INTERVALS[1])));
    d = record(d, 'm001', true, T0);
    expect(d.records.m001.due).toBe(dayKey(addDays(T0, INTERVALS[2])));
  });
  it('不正解は箱1に戻り、翌日に出る', () => {
    let d = emptyData();
    for (let k = 0; k < 4; k++) d = record(d, 'm001', true, T0);
    d = record(d, 'm001', false, T0);
    expect(d.records.m001.box).toBe(1);
    expect(d.records.m001.due).toBe(dayKey(addDays(T0, 1)));
  });
  it('箱は上限で止まる', () => {
    let d = emptyData();
    for (let k = 0; k < 20; k++) d = record(d, 'm001', true, T0);
    expect(d.records.m001.box).toBe(INTERVALS.length - 1);
  });
  it('今日の復習は、復習日が今日以前の語だけ。翌日になると出る', () => {
    const d = record(emptyData(), 'm001', true, T0);
    expect(dueWords(WORDS, d, T0)).toHaveLength(0);
    expect(dueWords(WORDS, d, addDays(T0, 1)).map((w) => w.id)).toEqual(['m001']);
  });
  it('覚えた = 箱4以上で苦手でない', () => {
    let d = emptyData();
    for (let k = 0; k < 4; k++) d = record(d, 'm001', true, T0);
    expect(isLearned(d.records.m001)).toBe(true);
    expect(progress(WORDS, d)).toEqual({ total: 300, seen: 1, learned: 1, nigate: 0 });
  });
  it('まだ答えていない語は重要度順', () => {
    const d = record(emptyData(), 'm001', true, T0);
    expect(unseen(WORDS, d).slice(0, 2).map((w) => w.rank)).toEqual([2, 3]);
  });
});

describe('試験日からの逆算', () => {
  it('残り日数(当日は0、過ぎたら null、形が違えば null)', () => {
    expect(daysLeft('2026-10-04', T0)).toBe(0);
    expect(daysLeft('2026-10-14', T0)).toBe(10);
    expect(daysLeft('2026-10-01', T0)).toBeNull();
    expect(daysLeft('', T0)).toBeNull();
    expect(daysLeft('2026/10/14', T0)).toBeNull();
  });
  it('最後の2週間を総復習に残して、未習の語を割る', () => {
    const p = makePlan(WORDS, emptyData(), '2027-01-16', T0)!;
    expect(p.days).toBe(104);
    expect(p.remaining).toBe(300);
    expect(p.perDay).toBe(Math.max(5, Math.ceil(300 / (104 - 14))));
    const many = Array.from({ length: 600 }, (_, k) => word(k + 1));
    expect(makePlan(many, emptyData(), '2027-01-16', T0)!.perDay).toBe(Math.ceil(600 / 90));
    expect(p.bufferDays).toBeGreaterThanOrEqual(14);
  });
  it('残りが少なくても1日5語は出す。覚え終わったら0', () => {
    expect(makePlan(WORDS.slice(0, 3), emptyData(), '2027-01-16', T0)!.perDay).toBe(5);
    let d = emptyData();
    for (let k = 0; k < 4; k++) d = record(d, 'm001', true, T0);
    expect(makePlan(WORDS.slice(0, 1), d, '2027-01-16', T0)!.perDay).toBe(0);
  });
  it('試験が近いと、残りを日数で割った数になる', () => {
    const p = makePlan(WORDS, emptyData(), '2026-10-14', T0)!;
    expect(p.perDay).toBe(Math.ceil(300 / (10 - 2)));
  });
  it('試験日が無ければ逆算しない', () => {
    expect(makePlan(WORDS, emptyData(), '', T0)).toBeNull();
  });
});

describe('無料と完全版', () => {
  it('無料は本編の上位150語だけ', () => {
    expect(isLocked(WORDS[FREE_MAIN - 1], false)).toBe(false);
    expect(isLocked(WORDS[FREE_MAIN], false)).toBe(true);
    expect(isLocked(WORDS[FREE_MAIN], true)).toBe(false);
  });
  it('敬語・助動詞のセットは完全版', () => {
    expect(isLocked(word(1, { set: 'keigo' }), false)).toBe(true);
    expect(isLocked(word(1, { set: 'jodoshi' }), true)).toBe(false);
  });
  it('例文のおためしは5問', () => expect(EXAMPLE_TRIAL).toBe(5));
});

describe('4択', () => {
  it('選択肢は4つで重複が無く、正解の位置が正しい', () => {
    const rand = rng(1);
    for (const w of WORDS.slice(0, 50)) {
      const q = makeQuestion(w, 'mean', WORDS, rand);
      expect(q.choices).toHaveLength(4);
      expect(new Set(q.choices).size).toBe(4);
      expect(q.choices[q.answer]).toBe(w.quiz);
    }
  });
  it('外れは意味の分類が違う語から選ぶ', () => {
    const rand = rng(2);
    const q = makeQuestion(WORDS[0], 'mean', WORDS, rand);
    const others = q.choices.filter((_, k) => k !== q.answer).map((c) => WORDS.find((w) => w.quiz === c)!);
    for (const o of others) expect(o.cat).not.toBe(WORDS[0].cat);
  });
  it('意味から古語: 選択肢は見出し語', () => {
    const q = makeQuestion(WORDS[4], 'reverse', WORDS, rng(3));
    expect(q.prompt).toBe(WORDS[4].quiz);
    expect(q.choices[q.answer]).toBe(WORDS[4].w);
  });
  it('例文問題の正解は、その例文で使われている意味', () => {
    const q = makeQuestion(WORDS[5], 'example', WORDS, rng(4), 0);
    expect(q.prompt).toBe(WORDS[5].ex[0].text);
    expect(q.choices[q.answer]).toBe(WORDS[5].means[1]);
  });
  it('同じ乱数の種なら同じ問題になる', () => {
    expect(makeQuestion(WORDS[9], 'mean', WORDS, rng(5))).toEqual(makeQuestion(WORDS[9], 'mean', WORDS, rng(5)));
  });
  it('語が少なくても落ちない(選択肢が足りない分は減る)', () => {
    const q = makeQuestion(WORDS[0], 'mean', WORDS.slice(0, 2), rng(6));
    expect(q.choices.length).toBeGreaterThanOrEqual(1);
    expect(q.choices[q.answer]).toBe(WORDS[0].quiz);
  });
  it('助動詞の例文問題は、同じ助動詞の別の意味を外れにする', () => {
    const j = word(1, { set: 'jodoshi', pos: '助動詞', means: ['受身', '尊敬', '自発', '可能'], quiz: '受身・尊敬・自発・可能', ex: [{ text: 'あ', hit: 'あ', tr: 't', sense: 2, src: 's' }] });
    const q = makeQuestion(j, 'example', [j], rng(7), 0);
    expect(q.choices[q.answer]).toBe('自発');
    expect(q.choices).toHaveLength(4);
    expect(q.choices.filter((c) => j.means.includes(c))).toHaveLength(4);
  });
  it('敬語の種類の選択肢は、いつも尊敬・謙譲・丁寧の順', () => {
    const k = word(1, { set: 'keigo', kind: '謙譲' });
    const q = makeKindQuestion(k);
    expect(q.choices).toEqual(KEIGO_KINDS.map((x) => x + '語'));
    expect(q.answer).toBe(1);
  });
});

describe('同じ見出しの別項目', () => {
  it('外れの選択肢に同じ見出しの語を使わない', () => {
    const a = word(1, { set: 'keigo', w: 'たてまつる', kanji: '奉る', kind: '謙譲', quiz: '差し上げる', cat: '謙譲' });
    const b = word(2, { set: 'keigo', w: 'たてまつる', kanji: '奉る', kind: '尊敬', quiz: 'お召しになる', cat: '尊敬' });
    const rest = Array.from({ length: 6 }, (_, k) => word(k + 3, { set: 'keigo', cat: '尊敬' }));
    for (let s = 1; s < 30; s++) expect(makeQuestion(a, 'mean', [a, b, ...rest], rng(s)).choices).not.toContain('お召しになる');
  });
  it('種類の問題からは、見ただけで種類が決まらない敬語を外す', () => {
    const a = word(1, { set: 'keigo', w: 'はべり', kanji: '侍り', kind: '丁寧' });
    const b = word(2, { set: 'keigo', w: 'はべり', kanji: '侍り', kind: '謙譲' });
    const c = word(3, { set: 'keigo', w: 'たまふ', kanji: '給ふ・四段', kind: '尊敬' });
    const d = word(4, { set: 'keigo', w: 'たまふ', kanji: '給ふ・下二段', kind: '謙譲' });
    expect(kindQuizWords([a, b, c, d]).map((w) => w.id)).toEqual([c.id, d.id]);
  });
});

describe('保存データ', () => {
  it('壊れた値・古い形でも落ちずに埋める', () => {
    expect(normalize(null)).toEqual(emptyData());
    const d = normalize({ records: { a: { n: 2, ok: 1 }, b: 'x' }, settings: { examDate: '2027-01-16' } });
    expect(d.records.a).toMatchObject({ n: 2, ok: 1, streak: 0, box: 0, due: '' });
    expect(d.records.b).toBeUndefined();
    expect(d.settings.examDate).toBe('2027-01-16');
    expect(d.settings.batch).toBe(10);
  });
  it('JSON で往復しても同じ', () => {
    const d = record(emptyData(), 'm001', false, T0);
    expect(normalize(JSON.parse(JSON.stringify(d)))).toEqual(d);
  });
});

describe('そのほか', () => {
  it('連続日数', () => {
    const daily = { [dayKey(T0)]: 3, [dayKey(addDays(T0, -1))]: 1, [dayKey(addDays(T0, -3))]: 1 };
    expect(streakDays(daily, T0)).toBe(2);
    expect(streakDays({ [dayKey(addDays(T0, -1))]: 1 }, T0)).toBe(1);
  });
  it('例文の強調の切り分け', () => {
    expect(splitHit('いとをかしげなり', 'をかし')).toEqual(['いと', 'をかし', 'げなり']);
    expect(splitHit('なし', 'ある')).toEqual(['なし', '', '']);
  });
});
