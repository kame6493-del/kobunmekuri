import { Preferences } from '@capacitor/preferences';
import type { AppData, Word } from '../domain/types';
import { addDays, dayKey, emptyData, record } from '../domain/study';

/**
 * 画面写真用の見本データ(開発ビルドの ?demo=1 だけ)。
 * n=答えた語数 acc=正答率 exam=試験日 premium=1 で疑似購入済み
 */
export async function installDemo(params: URLSearchParams) {
  const words: Word[] = await (await fetch('./data/words.json')).json();
  const n = Number(params.get('n') ?? 180);
  const acc = Number(params.get('acc') ?? 0.75);
  const now = Date.now();
  let d: AppData = emptyData();
  d.settings.examDate = params.get('exam') ?? dayKey(addDays(now, 104));
  let seed = 7;
  const rand = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const main = words.filter((w) => w.set === 'main').slice(0, n);
  // 過去5週間にわたって答えた形にする。前半の語は間をあけて何度も正解して「覚えた」まで進んでいる
  main.forEach((w, i) => {
    if (i < main.length * 0.45) {
      let t = addDays(now, -36 + Math.floor(i / 12));
      for (const gap of [1, 3, 7, 14]) { d = record(d, w.id, rand() < 0.93, t); t = addDays(t, gap); if (t > now) break; }
      return;
    }
    const t0 = addDays(now, -14 + Math.floor((i / main.length) * 13));
    d = record(d, w.id, rand() < acc, t0);
    if (rand() < 0.6) d = record(d, w.id, rand() < acc + 0.1, addDays(t0, 1));
  });
  // warm=1: 苦手の語を「あと1回正解で外れる」所まで進めておく(結果画面の写真用)
  if (params.get('warm') === '1') {
    for (const [id, r] of Object.entries(d.records)) if (r.missed && r.streak === 0) d = record(d, id, true, addDays(now, -1));
  }
  for (let k = 0; k < 18; k++) d.daily[dayKey(addDays(now, -k))] = 20 + Math.floor(rand() * 30);
  await Preferences.set({ key: 'kobunmekuri.v1', value: JSON.stringify(d) });
  if (params.get('premium') === '1') localStorage.setItem('kobunmekuri.mockFull', '1');
  else localStorage.removeItem('kobunmekuri.mockFull');
  history.replaceState(null, '', location.pathname);
}
