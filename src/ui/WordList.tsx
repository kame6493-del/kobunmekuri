import { useMemo, useState } from 'react';
import type { AppData, Word } from '../domain/types';
import { isLearned, isLocked, isNigate } from '../domain/study';
import { Icon, TopBar } from './Chrome';

type Filter = 'all' | 'nigate' | 'learned' | 'new';

/** 辞書: 本編の語を検索・絞り込み */
export function WordList(p: { main: Word[]; data: AppData; premium: boolean; onBack: () => void; onWord: (id: string) => void; onPaywall: () => void; onSettings: () => void }) {
  const [q, setQ] = useState('');
  const [f, setF] = useState<Filter>('all');
  const list = useMemo(() => {
    const t = q.trim();
    return p.main.filter((w) => {
      const r = p.data.records[w.id];
      if (f === 'nigate' && !isNigate(r)) return false;
      if (f === 'learned' && !isLearned(r)) return false;
      if (f === 'new' && r) return false;
      if (!t) return true;
      return w.w.includes(t) || w.kanji.includes(t) || w.means.some((m) => m.includes(t));
    });
  }, [p.main, p.data, q, f]);

  return (
    <div className="page wlist has-tabs">
      <TopBar title="辞書を引く" onClose={p.onBack} right={<button className="icon" aria-label="設定" onClick={p.onSettings}><Icon name="gear" size={22} /></button>} />
      <label className="search-box">
        <Icon name="search" size={20} />
        <input className="search" type="search" placeholder="古語・漢字・意味で検索…" value={q} onChange={(e) => setQ(e.target.value)} />
      </label>
      <h2 className="sec-h"><span>探す・絞り込む</span></h2>
      <div className="chips-row seg">
        {([['all', 'すべて'], ['nigate', '苦手'], ['learned', '覚えた'], ['new', 'まだ']] as [Filter, string][]).map(([k, l]) => (
          <button key={k} className={f === k ? 'on' : ''} onClick={() => setF(k)}>{l}</button>
        ))}
      </div>
      <p className="muted small list-n">重要度順・{list.length}語</p>
      <ul className="rows">
        {list.map((w) => {
          const r = p.data.records[w.id];
          const locked = isLocked(w, p.premium);
          return (
            <li key={w.id}>
              <button className={`row${locked ? ' locked' : ''}`} onClick={() => (locked ? p.onPaywall() : p.onWord(w.id))}>
                <span className="row-rank">{w.rank}</span>
                <span className="row-w">{w.w}</span>
                <span className="row-m">{locked ? <><Icon name="lock" size={14} />完全版</> : w.quiz}</span>
                <span className={`dot ${isNigate(r) ? 'ng' : isLearned(r) ? 'ok' : r ? 'seen' : ''}`} />
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
