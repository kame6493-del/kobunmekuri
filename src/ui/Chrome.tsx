import type { ReactNode } from 'react';
import type { Word } from '../domain/types';
import { splitHit } from '../domain/study';

/** 見本から切り出した絵(public/img)。飾りなので読み上げない */
export function Art(p: { name: string; className?: string; alt?: string }) {
  return <img className={p.className} src={`./img/${p.name}.webp`} alt={p.alt ?? ''} aria-hidden={p.alt ? undefined : true} draggable={false} />;
}

/** 線のアイコン(見本の線画に合わせて描いた SVG) */
export function Icon(p: { name: IconName; size?: number; className?: string }) {
  const s = p.size ?? 22;
  const common = { width: s, height: s, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, className: p.className, 'aria-hidden': true };
  switch (p.name) {
    case 'back': return <svg {...common}><path d="M15 5l-7 7 7 7" /></svg>;
    case 'close': return <svg {...common}><path d="M6 6l12 12M18 6L6 18" /></svg>;
    case 'chev': return <svg {...common}><path d="M9 5l7 7-7 7" /></svg>;
    case 'home': return <svg {...common}><path d="M3.5 11L12 4l8.5 7" /><path d="M5.5 9.5V20h5v-5.5h3V20h5V9.5" /></svg>;
    case 'homeFill': return <svg {...common}><path d="M3.5 11L12 4l8.5 7" /><path d="M5.5 9.5V20h5v-5.5h3V20h5V9.5L12 4z" fill="currentColor" /></svg>;
    case 'book': return <svg {...common}><path d="M12 6.5C10 5 7 4.6 3.5 5v13c3.5-.4 6.5 0 8.5 1.5 2-1.5 5-1.9 8.5-1.5V5C17 4.6 14 5 12 6.5z" /><path d="M12 6.5v13" /></svg>;
    case 'bars': return <svg {...common}><path d="M5 20v-6M10 20V9M15 20v-8M20 20V5" /></svg>;
    case 'search': return <svg {...common}><circle cx="10.5" cy="10.5" r="6" /><path d="M15 15l5 5" /></svg>;
    case 'gear': return <svg {...common}><circle cx="12" cy="12" r="3" /><path d="M12 2.8l1.6 2.3 2.7-.7.7 2.7 2.3 1.6-1.2 2.3 1.2 2.3-2.3 1.6-.7 2.7-2.7-.7L12 21.2l-1.6-2.3-2.7.7-.7-2.7L4.7 15.3 5.9 13 4.7 10.7 7 9.1l.7-2.7 2.7.7z" /></svg>;
    case 'shelf': return <svg {...common}><path d="M4 4.5v14M7.5 4.5v14M11 4.5v14M14.5 5l3.5 13.5M3 19.5h18" /></svg>;
    case 'check': return <svg {...common}><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>;
    case 'mark': return <svg {...common}><path d="M7 3.5h10v17l-5-3.5-5 3.5z" /></svg>;
    case 'markFill': return <svg {...common}><path d="M7 3.5h10v17l-5-3.5-5 3.5z" fill="currentColor" /></svg>;
    case 'flip': return <svg {...common}><path d="M8 4h9a2 2 0 012 2v12" /><rect x="4" y="7" width="11" height="13" rx="1.5" /></svg>;
    case 'redo': return <svg {...common}><path d="M19 12a7 7 0 11-2.1-5" /><path d="M19 4v4h-4" /></svg>;
    case 'pen': return <svg {...common}><path d="M4 20l1-4L16 5l3 3L8 19z" /><path d="M14 7l3 3" /></svg>;
    case 'quote': return <svg {...common}><path d="M4 6h16M4 10h16M4 14h10" /><path d="M4 18h7" /></svg>;
    case 'talk': return <svg {...common}><path d="M4 5h16v11H9l-5 4z" /></svg>;
    case 'note': return <svg {...common}><rect x="5" y="3.5" width="14" height="17" rx="1.5" /><path d="M8.5 8h7M8.5 12h7M8.5 16h4" /></svg>;
    case 'clock': return <svg {...common}><circle cx="12" cy="12" r="8" /><path d="M12 7.5V12l3 2" /></svg>;
    case 'lock': return <svg {...common}><rect x="5" y="10.5" width="14" height="10" rx="2" /><path d="M8 10.5V8a4 4 0 018 0v2.5" /></svg>;
    case 'aa': return <svg {...common} strokeWidth={1.5}><path d="M3 18l4-11 4 11M4.5 14h5" /><path d="M13 18l4.5-13L22 18M14.8 13.5h5.4" /></svg>;
    case 'list': return <svg {...common}><path d="M9 6h11M9 12h11M9 18h11" /><circle cx="4.5" cy="6" r=".8" fill="currentColor" /><circle cx="4.5" cy="12" r=".8" fill="currentColor" /><circle cx="4.5" cy="18" r=".8" fill="currentColor" /></svg>;
    case 'trash': return <svg {...common}><path d="M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 13h9l1-13" /></svg>;
    case 'restore': return <svg {...common}><path d="M4 12a8 8 0 102.3-5.7" /><path d="M4 4v4h4" /></svg>;
  }
}
export type IconName =
  | 'back' | 'close' | 'chev' | 'home' | 'homeFill' | 'book' | 'bars' | 'search' | 'gear' | 'shelf' | 'check' | 'mark' | 'markFill'
  | 'flip' | 'redo' | 'pen' | 'quote' | 'talk' | 'note' | 'clock' | 'lock' | 'aa' | 'list' | 'trash' | 'restore';

/** 上の帯: 戻る・題名(絵のアイコンつき)・右 */
export function TopBar(p: { title: ReactNode; onClose: () => void; right?: ReactNode; closeLabel?: string; icon?: string; close?: 'back' | 'close' }) {
  return (
    <header className="topbar">
      <button className="icon" aria-label={p.closeLabel ?? '戻る'} onClick={p.onClose}><Icon name={p.close ?? 'back'} size={24} /></button>
      <h1>{p.icon && <Art name={p.icon} className="topbar-ic" />}<span>{p.title}</span></h1>
      <div className="topbar-right">{p.right}</div>
    </header>
  );
}

export type Tab = 'home' | 'study' | 'nigate' | 'list' | 'settings';

/** 下のタブ: ホーム・学習・苦手・辞書・設定 */
export function TabBar(p: { active: Tab; onTab: (t: Tab) => void; nigate?: number }) {
  const tabs: [Tab, string, IconName][] = [['home', 'ホーム', 'home'], ['study', '学習', 'book'], ['nigate', '苦手', 'bars'], ['list', '辞書', 'search'], ['settings', '設定', 'gear']];
  return (
    <nav className="tabbar" aria-label="画面の切り替え">
      {tabs.map(([k, l, ic]) => (
        <button key={k} className={p.active === k ? 'on' : ''} aria-current={p.active === k ? 'page' : undefined} onClick={() => p.onTab(k)}>
          <Icon name={p.active === k && k === 'home' ? 'homeFill' : ic} size={24} />
          <span>{l}</span>
          {k === 'nigate' && !!p.nigate && <i className="tab-badge">{p.nigate > 99 ? '99+' : p.nigate}</i>}
        </button>
      ))}
    </nav>
  );
}

/** アプリ名の題字(朱の印つき) */
export function Brand(p: { small?: boolean }) {
  return (
    <div className={`brand${p.small ? ' small' : ''}`}>
      <p className="brand-name">こぶんめくり<Art name="ic_seal" className="brand-seal" /></p>
      <p className="brand-sub">古文単語600・例文つき</p>
    </div>
  );
}

export function Hit(p: { text: string; hit: string }) {
  const [a, b, c] = splitHit(p.text, p.hit);
  return <>{a}{b && <mark>{b}</mark>}{c}</>;
}

/** 種類の小札(品詞・敬語の種類) */
export function Pill(p: { children: ReactNode; tone?: 'shu' | 'kin' | 'ai' | 'midori' }) {
  return <span className={`pill${p.tone ? ' ' + p.tone : ''}`}>{p.children}</span>;
}

/** 語の中身(意味・解説・例文)。答えたあと・カードの裏で使う */
export function WordBody(p: { word: Word; exIndex?: number; quoted?: boolean; compact?: boolean }) {
  const w = p.word;
  const exs = p.exIndex !== undefined && w.ex[p.exIndex] ? [w.ex[p.exIndex], ...w.ex.filter((_, i) => i !== p.exIndex)] : w.ex;
  return (
    <div className="wbody">
      <section className="wsec">
        <h3><Art name="ic_sprig" className="wsec-ic" />なぜ正解か</h3>
        <ol className="means">{w.means.map((m, i) => <li key={i}>{m}</li>)}</ol>
        {(w.kind || w.plain || w.conn) && (
          <p className="wtags">
            {w.kind && <Pill tone="shu">{w.kind}語</Pill>}
            {w.plain && <span>普通の語: {w.plain}</span>}
            {w.conn && <span>接続: {w.conn}</span>}
          </p>
        )}
        <p className="note">{w.note}</p>
      </section>
      {exs.length > 0 && (
        <section className="wsec ex-sec">
          <h3><Icon name="quote" size={18} />{p.quoted ? 'この文の訳' : '例文'}</h3>
          {exs.map((e, i) => (
            <figure className="ex" key={i}>
              {/* 例文問題では、問題の欄に同じ本文が出ているので訳だけ見せる */}
              {!(p.quoted && i === 0) && <blockquote><Hit text={e.text} hit={e.hit} /></blockquote>}
              <figcaption>
                <span className="ex-tr">{e.tr}</span>
                <span className="ex-src">── {e.src}{w.set === 'jodoshi' ? `(${w.means[e.sense] ?? ''})` : ''}</span>
              </figcaption>
            </figure>
          ))}
        </section>
      )}
    </div>
  );
}

/** 空の状態(絵・見出し・文・ボタン) */
export function Empty(p: { art: string; title: string; children: ReactNode; action?: ReactNode; wide?: boolean }) {
  return (
    <section className="empty-state">
      <Art name={p.art} className={`empty-art${p.wide ? ' wide' : ''}`} />
      <h2>{p.title}</h2>
      <div className="empty-text">{p.children}</div>
      {p.action}
    </section>
  );
}

export function fmtMD(day: string) {
  const [, m, d] = day.split('-').map(Number);
  return `${m}/${d}`;
}
