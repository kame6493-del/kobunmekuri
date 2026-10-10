import { useState, type ReactNode } from 'react';
import type { AppData, Settings } from '../domain/types';
import { restore } from '../platform/billing';
import { setDailyReminder } from '../platform/native';
import { Art, Icon, TopBar } from './Chrome';

function Item(p: { ic: ReactNode; title: string; sub: string; children?: ReactNode; className?: string }) {
  return (
    <section className={`set-item${p.className ? ' ' + p.className : ''}`}>
      <div className="set-item-h">
        <span className="set-ic">{p.ic}</span>
        <div><h2>{p.title}</h2><p>{p.sub}</p></div>
      </div>
      {p.children && <div className="set-item-c">{p.children}</div>}
    </section>
  );
}

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
    <div className="page settings has-tabs">
      <TopBar title="設定" onClose={p.onBack} />
      <Art name="head_sub" className="sub-art" />

      <Item ic={<Art name="ic_bell" />} title="通知" sub="復習のリマインドを設定できます">
        <label className="switch">
          <input type="checkbox" checked={s.remind} onChange={(e) => remind(e.target.checked)} />
          <span>決まった時刻に復習をお知らせする</span>
        </label>
        {s.remind && <input type="time" className="date" value={s.remindAt} onChange={(e) => remind(true, e.target.value)} aria-label="お知らせの時刻" />}
      </Item>

      <Item ic={<Art name="ic_calendar" />} title="試験日設定" sub="共通テストや志望校の試験日から、1日に覚える語数を逆算します">
        <div className="row-inline">
          <input type="date" className="date" value={s.examDate} onChange={(e) => p.onChange({ examDate: e.target.value })} aria-label="試験日" />
          {s.examDate && <button className="btn small ghost" onClick={() => p.onChange({ examDate: '' })}>消す</button>}
        </div>
      </Item>

      <Item ic={<Icon name="aa" size={26} />} title="文字サイズ" sub="読みやすい大きさに調整できます">
        <div className="seg">
          {[[0.92, '小'], [1, '中'], [1.12, '大'], [1.25, '特大']].map(([v, l]) => (
            <button key={String(v)} className={s.fontScale === v ? 'on' : ''} onClick={() => p.onChange({ fontScale: Number(v) })}>{l}</button>
          ))}
        </div>
      </Item>

      <Item ic={<Icon name="list" size={24} />} title="1回の問題数" sub="4択・カードで一度に出す数です">
        <div className="seg">
          {[5, 10, 20].map((n) => <button key={n} className={s.batch === n ? 'on' : ''} onClick={() => p.onChange({ batch: n })}>{n}問</button>)}
        </div>
      </Item>

      <Item ic={<Art name="ic_crown" />} title="完全版" sub={p.premium ? '購入済みです。ありがとうございます。' : '601語すべて・例文モード・敬語/助動詞セット'}>
        {!p.premium && <button className="btn wide" onClick={p.onPaywall}>完全版を見る</button>}
        <button className="link" onClick={async () => { const ok = await restore().catch(() => false); setMsg(ok ? '購入を復元しました' : '購入は見つかりませんでした'); if (ok) p.onRestored(); }}>購入情報の復元</button>
      </Item>

      <Item ic={<Icon name="trash" size={24} className="shu-ic" />} title="データ初期化" sub="学習データをすべて削除します">
        {!confirm ? (
          <button className="btn danger wide" onClick={() => setConfirm(true)}>学習の記録をすべて消す</button>
        ) : (
          <div className="confirm">
            <p>苦手・復習の予定・連続日数がすべて消えます。元に戻せません。</p>
            <div className="row-inline">
              <button className="btn" onClick={() => setConfirm(false)}>やめる</button>
              <button className="btn danger" onClick={() => { p.onReset(); setConfirm(false); setMsg('記録を消しました'); }}>消す</button>
            </div>
          </div>
        )}
      </Item>
      {msg && <p className="err set-msg">{msg}</p>}

      <section className="about">
        <Art name="app_icon" className="about-icon" alt="こぶんめくりのアイコン" />
        <h2 className="about-name">こぶんめくり</h2>
        <p className="about-sub">― 安心して、ずっと使える ―</p>
        <div className="about-cards">
          <div><Art name="ic_noreg" /><b>登録なし</b><span>会員登録は必要ありません。学習の記録はこの端末の中だけに保存し、外へ送りません。</span></div>
          <div><Art name="ic_noad" /><b>広告なし</b><span>無料版でも完全版でも、広告は出ません。</span></div>
        </div>
        <Art name="books_plum" className="about-books" />
        <p className="about-tag">ことばと、<br />じっくり向き合える時間を。</p>
        <p className="small muted about-credit">例文は著作権の切れた古典の本文から引いています(本文の翻刻はウィキソース日本語版、CC BY-SA 4.0)。字体は新字体に改めました。意味・解説・現代語訳はこのアプリで書いたものです。見出しの書体は Noto Serif JP(SIL Open Font License 1.1)です。</p>
      </section>
    </div>
  );
}
