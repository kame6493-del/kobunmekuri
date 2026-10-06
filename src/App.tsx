import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { App as CapApp } from '@capacitor/app';
import type { AppData, Mode, Word, WordSet } from './domain/types';
import { EXAMPLE_TRIAL, dueWords, isLocked, makePlan, nigateOrder, record, rng, shuffle, unseen } from './domain/study';
import { loadData, saveData } from './platform/storage';
import { loadBilling, type BillingState } from './platform/billing';
import { askReview } from './platform/native';
import { Home } from './ui/Home';
import { Quiz, type Session } from './ui/Quiz';
import { WordList } from './ui/WordList';
import { WordDetail } from './ui/WordDetail';
import { SetPage } from './ui/SetPage';
import { Paywall } from './ui/Paywall';
import { SettingsPage } from './ui/SettingsPage';

export type Route =
  | { name: 'home' }
  | { name: 'quiz'; session: Session }
  | { name: 'list' }
  | { name: 'word'; id: string }
  | { name: 'set'; set: WordSet }
  | { name: 'paywall' }
  | { name: 'settings' };

export default function App() {
  const [data, setData] = useState<AppData | null>(null);
  const [all, setAll] = useState<Word[] | null>(null);
  const [loadError, setLoadError] = useState('');
  const [billing, setBilling] = useState<BillingState>({ status: 'unavailable', reason: '読み込み中' });
  const [stack, setStack] = useState<Route[]>([{ name: 'home' }]);
  const route = stack[stack.length - 1];
  const dataRef = useRef<AppData | null>(null);

  useEffect(() => {
    loadData().then((d) => { dataRef.current = d; setData(d); });
    fetch('./data/words.json')
      .then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
      .then((ws: Word[]) => setAll(ws))
      .catch((e) => setLoadError(`単語を読み込めませんでした(${e})`));
    loadBilling().then(setBilling);
  }, []);

  const premium = billing.status === 'ready' && billing.premium;

  const update = useCallback((f: (d: AppData) => AppData) => {
    const cur = dataRef.current;
    if (!cur) return;
    const next = f(cur);
    dataRef.current = next;
    setData(next);
    saveData(next);
  }, []);

  const push = useCallback((r: Route) => setStack((s) => [...s, r]), []);
  const back = useCallback(() => setStack((s) => (s.length > 1 ? s.slice(0, -1) : s)), []);
  const home = useCallback(() => setStack([{ name: 'home' }]), []);

  // Android の戻るボタン
  useEffect(() => {
    const h = CapApp.addListener('backButton', () => {
      setStack((s) => {
        if (s.length > 1) return s.slice(0, -1);
        CapApp.minimizeApp().catch(() => {});
        return s;
      });
    });
    return () => { h.then((x) => x.remove()).catch(() => {}); };
  }, []);

  const main = useMemo(() => (all ?? []).filter((w) => w.set === 'main'), [all]);
  /** 鍵の無い本編の語 */
  const open = useMemo(() => main.filter((w) => !isLocked(w, premium)), [main, premium]);
  const byId = useMemo(() => new Map((all ?? []).map((w) => [w.id, w])), [all]);
  const plan = useMemo(() => (data ? makePlan(open, data, data.settings.examDate, Date.now()) : null), [open, data]);

  const start = useCallback((title: string, ws: Word[], mode: Mode, extra: Partial<Session> = {}) => {
    if (ws.length === 0) return;
    push({ name: 'quiz', session: { title, ids: ws.map((w) => w.id), mode, seed: Date.now(), ...extra } });
  }, [push]);

  /** 次に出す語: 今日の復習 → まだ答えていない語(重要度順) → 前に答えた語のうち箱の小さい物 */
  const nextBatch = useCallback((pool: Word[], n: number) => {
    const d = dataRef.current!;
    const now = Date.now();
    const due = dueWords(pool, d, now).slice(0, Math.ceil(n / 2));
    const fresh = unseen(pool, d).slice(0, n - due.length);
    let picked = [...due, ...fresh];
    if (picked.length < n) {
      const rest = shuffle(pool.filter((w) => !picked.includes(w)), rng(now)).sort((a, b) => (d.records[a.id]?.box ?? 0) - (d.records[b.id]?.box ?? 0));
      picked = [...picked, ...rest.slice(0, n - picked.length)];
    }
    return shuffle(picked, rng(now + 1));
  }, []);

  const starters = useMemo(() => ({
    today: () => {
      if (!data) return;
      const now = Date.now();
      const due = dueWords(open, data, now);
      const fresh = unseen(open, data).slice(0, plan?.perDay || data.settings.batch);
      start('今日の分', [...due.slice(0, 40), ...fresh], 'mean');
    },
    review: () => data && start('今日の復習', dueWords(open, data, Date.now()).slice(0, 40), 'mean'),
    nigate: () => data && start('まちがえた語だけ', nigateOrder([...open, ...(all ?? []).filter((w) => w.set !== 'main' && !isLocked(w, premium))], data).slice(0, 20), 'mean'),
    mode: (mode: Mode) => {
      if (!data) return;
      const titles: Record<Mode, string> = { mean: '4択で意味', reverse: '意味から古語', example: '例文で当てる', card: '一問一答カード' };
      if (mode === 'example') {
        const pool = (premium ? main : main.filter((w) => w.rank <= 150)).filter((w) => w.ex.length);
        if (!premium) {
          const left = EXAMPLE_TRIAL - data.exTrial;
          if (left <= 0) { push({ name: 'paywall' }); return; }
          start('例文で当てる(おためし)', nextBatch(pool, left), 'example', { trial: true });
          return;
        }
        start(titles.example, nextBatch(pool, data.settings.batch), 'example');
        return;
      }
      start(titles[mode], nextBatch(open, data.settings.batch), mode);
    },
  }), [data, open, main, all, plan, premium, start, nextBatch, push]);

  const answered = useCallback((w: Word, ok: boolean, trial: boolean) => {
    update((d) => {
      const n = record(d, w.id, ok, Date.now());
      return trial ? { ...n, exTrial: n.exTrial + 1 } : n;
    });
  }, [update]);

  const sessionsDone = useRef(0);
  const onSessionEnd = useCallback((rate: number) => {
    sessionsDone.current++;
    if (sessionsDone.current >= 2 && rate >= 0.7) askReview();
  }, []);

  if (loadError) return <div className="fatal">{loadError}</div>;
  if (!data || !all) return <div className="splash"><span>こぶんめくり</span></div>;

  const fontStyle = { ['--fs' as string]: String(data.settings.fontScale) };

  return (
    <div className="app" style={fontStyle}>
      {route.name === 'home' && (
        <Home
          data={data} main={main} open={open} all={all} premium={premium} plan={plan}
          onToday={starters.today}
          onReview={starters.review}
          onNigate={starters.nigate}
          onMode={starters.mode}
          onList={() => push({ name: 'list' })}
          onSet={(s) => push({ name: 'set', set: s })}
          onPaywall={() => push({ name: 'paywall' })}
          onSettings={() => push({ name: 'settings' })}
        />
      )}
      {route.name === 'quiz' && (
        <Quiz
          key={route.session.seed}
          session={route.session} byId={byId} pool={all} data={data}
          onAnswer={answered}
          onEnd={onSessionEnd}
          onClose={back}
          onHome={home}
          onAgain={(s) => { back(); start(s.title, s.ids.map((id) => byId.get(id)!).filter(Boolean), s.mode, { kind: s.kind }); }}
          onPaywall={() => push({ name: 'paywall' })}
          onWord={(id) => push({ name: 'word', id })}
        />
      )}
      {route.name === 'list' && (
        <WordList main={main} data={data} premium={premium} onBack={back} onWord={(id) => push({ name: 'word', id })} onPaywall={() => push({ name: 'paywall' })} />
      )}
      {route.name === 'word' && byId.get(route.id) && (
        <WordDetail word={byId.get(route.id)!} data={data} onBack={back} />
      )}
      {route.name === 'set' && (
        <SetPage
          set={route.set} words={all.filter((w) => w.set === route.set)} data={data} premium={premium}
          onBack={back}
          onPaywall={() => push({ name: 'paywall' })}
          onWord={(id) => push({ name: 'word', id })}
          onStart={(title, ws, mode, kind) => start(title, ws, mode, { kind })}
        />
      )}
      {route.name === 'paywall' && (
        <Paywall
          billing={billing} main={main} all={all}
          onClose={back}
          onBought={() => { loadBilling().then(setBilling); back(); }}
        />
      )}
      {route.name === 'settings' && (
        <SettingsPage
          data={data} premium={premium}
          onBack={back}
          onChange={(s) => update((d) => ({ ...d, settings: { ...d.settings, ...s } }))}
          onReset={() => update((d) => ({ ...d, records: {}, daily: {} }))}
          onPaywall={() => push({ name: 'paywall' })}
          onRestored={() => loadBilling().then(setBilling)}
        />
      )}
    </div>
  );
}
