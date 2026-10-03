import { useMemo, useState } from 'react';
import type { AppData, Word } from '../domain/types';
import { isLearned, isLocked, isNigate } from '../domain/study';
import { TopBar } from './Quiz';

type Filter = 'all' | 'nigate' | 'learned' | 'new';

export function WordList(p: { main: Word[]; data: AppData; premium: boolean; onBack: () => void; onWord: (id: string) => void; onPaywall: () => void }) {
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
    <div className="page wlist">
      <TopBar title="単語の一覧" onClose={p.onBack} />
      <input className="search" type="search" placeholder="古語・漢字・意味でさがす" value={q} onChange={(e) => setQ(e.target.value)} />
      <div className="seg">
        {([['all', 'すべて'], ['nigate', '苦手'], ['learned', '覚えた'], ['new', 'まだ']] as [Filter, string][]).map(([k, l]) => (
          <button key={k} className={f === k ? 'on' : ''} onClick={() => setF(k)}>{l}</button>
        ))}
      </div>
      <p className="muted small">{list.length}語</p>
      <ul className="rows">
        {list.map((w) => {
          const r = p.data.records[w.id];
          const locked = isLocked(w, p.premium);
          return (
            <li key={w.id}>
              <button className={`row${locked ? ' locked' : ''}`} onClick={() => (locked ? p.onPaywall() : p.onWord(w.id))}>
                <span className="row-rank">{w.rank}</span>
                <span className="row-w">{w.w}</span>
                <span className="row-m">{locked ? '完全版' : w.quiz}</span>
                <span className={`dot ${isNigate(r) ? 'ng' : isLearned(r) ? 'ok' : r ? 'seen' : ''}`} />
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
