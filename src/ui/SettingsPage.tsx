import { useState } from 'react';
import type { AppData, Settings } from '../domain/types';
import { restore } from '../platform/billing';
import { setDailyReminder } from '../platform/native';
import { TopBar } from './Quiz';

export function SettingsPage(p: {
  data: AppData; premium: boolean;
  onBack: () => void; onChange: (s: Partial<Settings>) => void; onReset: () => void;
  onPaywall: () => void; onRestored: () => void;
}) {
  const s = p.data.settings;
  const [msg, setMsg] = useState('');
  const [confirm, setConfirm] = useState(false);

  const remind = async (on: boolean, at = s.remindAt) => {
    const ok = await setDailyReminder(on, at, '復習の語がたまっています。1分だけめくりましょう。');
    p.onChange({ remind: on && ok, remindAt: at });
    if (on && !ok) setMsg('通知が許可されていません。端末の設定から許可してください。');
  };

  return (
    <div className="page settings">
      <TopBar title="設定" onClose={p.onBack} />

      <section className="card">
        <h2>試験日</h2>
        <p className="muted small">共通テストや志望校の試験日を入れると、残りの日数から1日に覚える語数を逆算します。</p>
        <div className="row-inline">
          <input type="date" className="date" value={s.examDate} onChange={(e) => p.onChange({ examDate: e.target.value })} aria-label="試験日" />
          {s.examDate && <button className="btn small ghost" onClick={() => p.onChange({ examDate: '' })}>消す</button>}
        </div>
      </section>

      <section className="card">
        <h2>1回の問題数</h2>
        <div className="seg">
          {[5, 10, 20].map((n) => <button key={n} className={s.batch === n ? 'on' : ''} onClick={() => p.onChange({ batch: n })}>{n}問</button>)}
        </div>
      </section>

      <section className="card">
        <h2>文字の大きさ</h2>
        <div className="seg">
          {[[0.92, '小'], [1, '中'], [1.12, '大'], [1.25, '特大']].map(([v, l]) => (
            <button key={String(v)} className={s.fontScale === v ? 'on' : ''} onClick={() => p.onChange({ fontScale: Number(v) })}>{l}</button>
          ))}
        </div>
      </section>

      <section className="card">
        <h2>毎日のお知らせ</h2>
        <label className="switch">
          <input type="checkbox" checked={s.remind} onChange={(e) => remind(e.target.checked)} />
          <span>決まった時刻に復習をお知らせする</span>
        </label>
        {s.remind && <input type="time" className="date" value={s.remindAt} onChange={(e) => remind(true, e.target.value)} aria-label="お知らせの時刻" />}
        {msg && <p className="err">{msg}</p>}
      </section>

      <section className="card">
        <h2>完全版</h2>
        {p.premium ? <p>購入済みです。ありがとうございます。</p> : <button className="btn wide" onClick={p.onPaywall}>完全版を見る</button>}
        <button className="link" onClick={async () => { const ok = await restore().catch(() => false); setMsg(ok ? '購入を復元しました' : '購入は見つかりませんでした'); if (ok) p.onRestored(); }}>購入の復元</button>
      </section>

      <section className="card">
        <h2>記録</h2>
        {!confirm ? (
          <button className="btn danger wide" onClick={() => setConfirm(true)}>学習の記録をすべて消す</button>
        ) : (
          <div className="confirm">
            <p>まちがえた語・復習の予定・連続日数がすべて消えます。元に戻せません。</p>
            <div className="row-inline">
              <button className="btn" onClick={() => setConfirm(false)}>やめる</button>
              <button className="btn danger" onClick={() => { p.onReset(); setConfirm(false); setMsg('記録を消しました'); }}>消す</button>
            </div>
          </div>
        )}
      </section>

      <section className="card about">
        <h2>このアプリについて</h2>
        <p className="small">学習の記録はこの端末の中だけに保存します。アカウント登録はなく、記録を外部へ送ることもありません。</p>
        <p className="small">例文は著作権の切れた古典の本文から引いています(本文の翻刻はウィキソース日本語版、CC BY-SA 4.0)。字体は新字体に改めました。意味・解説・現代語訳はこのアプリで書いたものです。</p>
      </section>
    </div>
  );
}
