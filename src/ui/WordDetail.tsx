import type { AppData, Word } from '../domain/types';
import { CLEAR_STREAK, INTERVALS, isLearned, isNigate } from '../domain/study';
import { Art, Hit, Icon, Pill, TopBar } from './Chrome';

/** 単語詳細: 意味・例文・現代語訳・解説・自分の記録 */
export function WordDetail(p: { word: Word; data: AppData; onBack: () => void }) {
  const w = p.word;
  const r = p.data.records[w.id];
  const state = !r ? 'まだ解いていません' : isNigate(r) ? `苦手(あと${CLEAR_STREAK - r.streak}回続けて正解で外れます)` : isLearned(r) ? '覚えた' : '練習中';
  return (
    <div className="page wdetail">
      <TopBar title="単語詳細" onClose={p.onBack} />
      <Art name="plum_corner" className="wd-plum" />
      <header className="wd-top">
        <h2 className="wd-head">{w.w}</h2>
        <span className="wd-badge">{w.set === 'keigo' ? '敬語' : w.set === 'jodoshi' ? '助動詞' : <>重要度 <b>{w.rank}</b></>}</span>
      </header>
      <p className="wd-pos"><Pill tone="kin">{w.kind ? `${w.kind}語` : w.pos}</Pill>{w.kanji && <span>{w.kanji}</span>}</p>

      <section className="dsec">
        <h3><Icon name="pen" size={20} className="shu-ic" />意味</h3>
        <ol className="means">{w.means.map((m, i) => <li key={i}>{m}</li>)}</ol>
        {(w.plain || w.conn) && <p className="wtags">{w.plain && <span>普通の語: {w.plain}</span>}{w.conn && <span>接続: {w.conn}</span>}</p>}
      </section>

      {w.ex.map((e, i) => (
        <div key={i}>
          <section className="dsec ex">
            <h3><Icon name="book" size={20} className="midori-ic" />例文{w.ex.length > 1 ? ` ${i + 1}` : ''}</h3>
            <blockquote><Hit text={e.text} hit={e.hit} /></blockquote>
            <p className="ex-src">── {e.src}{w.set === 'jodoshi' ? `(${w.means[e.sense] ?? ''})` : ''}</p>
          </section>
          <section className="dsec">
            <h3><Icon name="talk" size={20} className="midori-ic" />現代語訳</h3>
            <p>{e.tr}</p>
          </section>
        </div>
      ))}

      <section className="dsec">
        <h3><Icon name="note" size={20} className="midori-ic" />解説</h3>
        <p>{w.note}</p>
      </section>

      <section className="dsec wd-rec">
        <h3><Icon name="clock" size={20} className="ai-ic" />自分の記録</h3>
        <p>{state}</p>
        {r && <p className="muted small">{r.n}回答えて{r.ok}回正解。次の復習 {r.due}(間隔 {INTERVALS[r.box]}日)</p>}
      </section>
    </div>
  );
}
