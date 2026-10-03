import { useState } from 'react';
import type { Word } from '../domain/types';
import { EXAMPLE_TRIAL, FREE_MAIN } from '../domain/study';
import { BILLING } from '../config';
import { purchase, restore, type BillingState } from '../platform/billing';
import { TopBar } from './Quiz';

export function Paywall(p: { billing: BillingState; main: Word[]; all: Word[]; onClose: () => void; onBought: () => void }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');
  const price = p.billing.status === 'ready' ? p.billing.price ?? BILLING.price : BILLING.price;
  const keigo = p.all.filter((w) => w.set === 'keigo').length;
  const jodo = p.all.filter((w) => w.set === 'jodoshi').length;
  const exN = p.main.filter((w) => w.ex.length).length;

  const buy = async () => {
    setBusy(true); setMsg('');
    try {
      if (await purchase(p.billing)) p.onBought();
    } catch (e) {
      setMsg(`購入できませんでした(${(e as Error).message ?? e})`);
    } finally { setBusy(false); }
  };
  const doRestore = async () => {
    setBusy(true); setMsg('');
    try {
      if (await restore()) p.onBought();
      else setMsg('このアカウントでの購入は見つかりませんでした');
    } catch (e) {
      setMsg(`復元できませんでした(${(e as Error).message ?? e})`);
    } finally { setBusy(false); }
  };

  return (
    <div className="page paywall">
      <TopBar title="完全版" onClose={p.onClose} />
      <section className="pw-hero">
        <p className="pw-kicker">買い切り・月額なし・広告なし</p>
        <h2>{p.main.length}語を、<br />本文の中で覚える。</h2>
      </section>
      <table className="pw-table">
        <thead><tr><th></th><th>無料</th><th>完全版</th></tr></thead>
        <tbody>
          <tr><td>古文単語</td><td>上位{FREE_MAIN}語</td><td>{p.main.length}語</td></tr>
          <tr><td>例文で当てる</td><td>{EXAMPLE_TRIAL}問おためし</td><td>{exN}語の例文</td></tr>
          <tr><td>敬語セット</td><td>一覧のみ</td><td>{keigo}語</td></tr>
          <tr><td>助動詞セット</td><td>一覧のみ</td><td>{jodo}語</td></tr>
          <tr><td>苦手・今日の復習・逆算</td><td>○</td><td>○</td></tr>
          <tr><td>広告</td><td>なし</td><td>なし</td></tr>
        </tbody>
      </table>
      <div className="pw-cta">
        {p.billing.status === 'ready' ? (
          <button className="btn primary wide big" disabled={busy || (!p.billing.pkg && !import.meta.env.DEV)} onClick={buy}>
            {busy ? '処理中…' : `${price} で買う(1回だけ)`}
          </button>
        ) : (
          <button className="btn wide big" disabled>{p.billing.reason}</button>
        )}
        <button className="link" disabled={busy} onClick={doRestore}>以前に買った方はこちら(購入の復元)</button>
        {msg && <p className="err">{msg}</p>}
      </div>
      <p className="muted small">一度買えば、同じストアのアカウントなら機種変更後も「購入の復元」で使えます。記録はこの端末の中だけに保存し、外へ送りません。</p>
    </div>
  );
}
