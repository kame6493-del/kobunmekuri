/**
 * App Review 用の画面録画で流す自動操作。VITE_REVIEW_TOUR=1 で作ったビルドだけで動く(製品版には入らない)。
 * 持ち主が iPhone を持っていないので、CI のシミュレーターでこれを流しながら録画する(.github/workflows/ios-review-video.yml)。
 * 起動 → はじめの10語(4択で意味・解説)→ 結果 → 一問一答カード → 例文で当てる → 単語の一覧と詳しい画面
 * → 敬語セット(完全版の案内)→ 完全版の購入画面。押した所に丸を出す。
 */

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function tapMark(el: Element) {
  const r = el.getBoundingClientRect();
  const dot = document.createElement('div');
  Object.assign(dot.style, {
    position: 'fixed', left: `${r.left + r.width / 2 - 22}px`, top: `${r.top + r.height / 2 - 22}px`,
    width: '44px', height: '44px', borderRadius: '50%', background: 'rgba(210,64,42,0.35)',
    border: '2px solid rgba(210,64,42,0.8)', zIndex: '99999', pointerEvents: 'none', transition: 'opacity .6s, transform .6s',
  });
  document.body.appendChild(dot);
  requestAnimationFrame(() => { dot.style.transform = 'scale(1.4)'; dot.style.opacity = '0'; });
  setTimeout(() => dot.remove(), 700);
}

async function find(pred: (b: HTMLElement) => boolean, wait = 6000, sel = 'button, a'): Promise<HTMLElement | null> {
  const end = Date.now() + wait;
  while (Date.now() < end) {
    const el = [...document.querySelectorAll<HTMLElement>(sel)].find((b) => b.getClientRects().length > 0 && !(b as HTMLButtonElement).disabled && pred(b));
    if (el) return el;
    await sleep(200);
  }
  return null;
}

async function tap(pred: (b: HTMLElement) => boolean, pause = 1500, sel?: string) {
  const el = await find(pred, 6000, sel);
  if (!el) return false;
  el.scrollIntoView({ block: 'center', behavior: 'smooth' });
  await sleep(500);
  tapMark(el);
  await sleep(250);
  el.click();
  await sleep(pause);
  return true;
}

const text = (s: string) => (b: HTMLElement) => b.innerText.replace(/\s+/g, '').includes(s.replace(/\s+/g, ''));
const any = () => true;
const back = () => tap(any, 2000, '.topbar .icon');

async function scrollSlow(to: number, ms = 1600) {
  const from = window.scrollY;
  const steps = 30;
  for (let k = 1; k <= steps; k++) { window.scrollTo(0, from + ((to - from) * k) / steps); await sleep(ms / steps); }
}

/** 1問答える(選択肢の k 番目)。答えた後に解説までゆっくり下げて見せ、次へ */
async function answerOne(k: number, showMs = 1600, fast = false) {
  const choices = [...document.querySelectorAll<HTMLElement>('.choice')];
  if (choices.length === 0) return false;
  const t = choices[Math.min(k, choices.length - 1)];
  t.scrollIntoView({ block: 'center', behavior: 'smooth' });
  await sleep(fast ? 350 : 700);
  tapMark(t); t.click();
  await sleep(fast ? 600 : 900);
  if (!fast) await scrollSlow(document.body.scrollHeight, 1200);
  await sleep(showMs);
  return tap(any, fast ? 500 : 1200, '.bottom-bar .btn.primary');
}

export async function runReviewTour() {
  await sleep(3500); // ホーム(初回)を見せる

  // はじめの10語(4択で意味)。正解と不正解が混ざるように押す
  if (await tap(text('はじめの10語をめくる'), 1500)) {
    const picks = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1];
    for (let i = 0; i < picks.length; i++) {
      await find(any, 6000, '.choice');
      if (!(await answerOne(picks[i], i < 3 ? 2000 : 200, i >= 3))) break;
    }
  }
  // 結果(正解数・苦手に入った数)
  await find(any, 6000, '.result-hero');
  await sleep(1200);
  await scrollSlow(document.body.scrollHeight, 1500); await sleep(1000);
  await tap(text('ホームへ'), 2000);

  // 一問一答カード: めくって自己採点
  if (await tap(text('一問一答カード'), 1500)) {
    await tap(any, 2500, '.card-flip');
    await tap(text('覚えてた'), 1200);
    await back();
  }

  // 例文で当てる(無料のおためし): 古典の本文の一文で、その場の意味を選ぶ
  if (await tap(text('例文で当てる'), 2000)) {
    await find(any, 6000, '.choice');
    await answerOne(0, 2500);
    await back();
  }

  // 単語の一覧 → 詳しい画面(意味・解説・例文と出典)
  if (await tap(text('単語の一覧・さがす'), 1800)) {
    await tap(any, 2000, '.row:not(.locked)');
    await scrollSlow(document.body.scrollHeight, 2000); await sleep(1500);
    await back();
    await back();
  }

  // 敬語セット(無料は一覧だけ)→ 完全版の購入画面
  await tap(text('敬語セット'), 2500);
  if (!(await tap(any, 3000, '.unlock'))) {
    await back();
    await tap(any, 3000, '.unlock');
  }
  await scrollSlow(document.body.scrollHeight, 2500);
  await sleep(2500);
  // 購入ボタン(シミュレーターでストアの商品が取れたときだけ押せる)
  await tap((b) => b.closest('.pw-cta') !== null && /で買う/.test(b.innerText), 10000);
  await sleep(6000);
}
