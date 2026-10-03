import type { AppData, Word } from '../domain/types';
import { INTERVALS, isLearned, isNigate } from '../domain/study';
import { TopBar, WordBody } from './Quiz';

export function WordDetail(p: { word: Word; data: AppData; onBack: () => void }) {
  const w = p.word;
  const r = p.data.records[w.id];
  const state = !r ? 'まだ解いていません' : isNigate(r) ? `苦手(あと${2 - r.streak}回続けて正解で外れます)` : isLearned(r) ? '覚えた' : '練習中';
  return (
    <div className="page wdetail">
      <TopBar title={w.set === 'keigo' ? '敬語' : w.set === 'jodoshi' ? '助動詞' : `重要度 ${w.rank}`} onClose={p.onBack} />
      <h2 className="wd-head">{w.w}{w.kanji && <small>{w.kanji}</small>}</h2>
      <p className="wd-pos">{w.pos}</p>
      <WordBody word={w} />
      <section className="card wd-rec">
        <h3>自分の記録</h3>
        <p>{state}</p>
        {r && <p className="muted small">{r.n}回答えて{r.ok}回正解。次の復習 {r.due}(間隔 {INTERVALS[r.box]}日)</p>}
      </section>
    </div>
  );
}
