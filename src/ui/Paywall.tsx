import { useState } from 'react';
import type { Word } from '../domain/types';
import { EXAMPLE_TRIAL, FREE_MAIN } from '../domain/study';
import { BILLING } from '../config';
import { purchase, restore, type BillingState } from '../platform/billing';
import { Art, TopBar } from './Chrome';

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

  const feats: [string, string, string][] = [
    ['ic_book', `${p.main.length}語すべて`, `重要度の高い順に${p.main.length}語。無料の上位${FREE_MAIN}語の先まで。`],
    ['ic_doc', '例文モード', `${exN}語すべてに古典の本文の例文・出典・現代語訳・解説つき。`],
    ['ic_fan', '敬語セット', `尊敬・謙譲・丁寧の${keigo}語を、意味・種類・例文で。`],
    ['ic_scroll', '助動詞セット', `${jodo}項目を、意味・接続・例文での見分けで。`],
  ];

  return (
    <div className="page paywall">
      <TopBar title="こぶんめくり" onClose={p.onClose} />
      <Art name="head_sub" className="sub-art pw-art" />
      <p className="pw-kicker"><Art name="ic_crown" className="mini-ic" />完全版のご案内</p>
      <section className="pw-title">
        <Art name="ic_plum" className="pw-plum" />
        <h2>完全版<small>(買い切り)</small></h2>
        <p>月額なし・広告なし。古文を、本文の中で深く。</p>
      </section>
      <ul className="pw-feats">
        {feats.map(([ic, t, d]) => (
          <li key={t}><Art name={ic} className="pw-ic" /><div><b>{t}</b><span>{d}</span></div></li>
        ))}
      </ul>
      <section className="pw-free">
        <p>まずは無料でお試しできます</p>
        <div><Art name="ic_book_green" className="mini-ic" /><span><b>無料版は上位{FREE_MAIN}語まで</b><small>苦手・今日の復習・逆算は無料版でも使えます</small></span></div>
      </section>
      <h2 className="sec-h"><span>無料版と完全版の比較</span></h2>
      <table className="pw-table">
        <thead><tr><th></th><th className="free">無料版</th><th className="full"><Art name="ic_crown" className="mini-ic" /><br />完全版(買い切り)</th></tr></thead>
        <tbody>
          <tr><td>収録語数</td><td>上位{FREE_MAIN}語</td><td>{p.main.length}語すべて</td></tr>
          <tr><td>例文モード</td><td>{EXAMPLE_TRIAL}問おためし</td><td className="maru">○<small>{exN}語の例文</small></td></tr>
          <tr><td>敬語セット</td><td>一覧のみ</td><td className="maru">○<small>{keigo}語・尊敬/謙譲/丁寧</small></td></tr>
          <tr><td>助動詞セット</td><td>一覧のみ</td><td className="maru">○<small>{jodo}項目・意味/接続</small></td></tr>
          <tr><td>苦手・今日の復習・逆算</td><td className="maru">○</td><td className="maru">○</td></tr>
          <tr><td>広告の表示</td><td>なし</td><td>なし</td></tr>
        </tbody>
      </table>
      <div className="pw-cta">
        {p.billing.status === 'ready' ? (
          <button className="btn shu wide big buy" disabled={busy || (!p.billing.pkg && !import.meta.env.DEV)} onClick={buy}>
            <Art name="ic_crown" className="buy-ic" />
            <span>{busy ? '処理中…' : <>完全版を購入する<small>{price}(買い切り・1回だけ)</small></>}</span>
          </button>
        ) : (
          <button className="btn wide big" disabled>{p.billing.reason}</button>
        )}
        <button className="link" disabled={busy} onClick={doRestore}>購入情報の復元</button>
        {msg && <p className="err">{msg}</p>}
      </div>
      <p className="muted small">一度買えば、同じストアのアカウントなら機種変更後も「購入情報の復元」で使えます。記録はこの端末の中だけに保存し、外へ送りません。</p>
    </div>
  );
}
