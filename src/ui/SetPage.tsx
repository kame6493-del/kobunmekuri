import type { AppData, Mode, Word, WordSet } from '../domain/types';
import { isNigate, kindQuizWords, rng, shuffle } from '../domain/study';
import { TopBar } from './Quiz';

export function SetPage(p: {
  set: WordSet; words: Word[]; data: AppData; premium: boolean;
  onBack: () => void; onPaywall: () => void; onWord: (id: string) => void;
  onStart: (title: string, ws: Word[], mode: Mode, kind?: boolean) => void;
}) {
  const keigo = p.set === 'keigo';
  const title = keigo ? '敬語セット' : '助動詞セット';
  const mix = (ws: Word[], n = 10) => shuffle(ws, rng(Date.now())).slice(0, n);
  const withEx = p.words.filter((w) => w.ex.length);

  return (
    <div className="page setpage">
      <TopBar title={title} onClose={p.onBack} />
      <p className="set-lead">
        {keigo
          ? '入試に出る敬語を、意味・普通の語・尊敬/謙譲/丁寧の別でまとめました。種類の3択は、選択肢がいつも「尊敬・謙譲・丁寧」の順に並びます。'
          : '助動詞を、意味・接続・見分け方でまとめました。例文の問題は、同じ助動詞のどの意味かを選びます。'}
      </p>
      {!p.premium ? (
        <button className="unlock" onClick={p.onPaywall}>
          <span className="unlock-title">{title}は完全版で使えます</span>
          <span className="unlock-sub">下の一覧で中身を確かめられます(問題は完全版)</span>
        </button>
      ) : (
        <div className="menu">
          <button onClick={() => p.onStart(`${title}・意味`, mix(p.words), 'mean')}><b>意味の4択</b><span>10問</span></button>
          {keigo
            ? <button onClick={() => p.onStart('敬語の種類', mix(kindQuizWords(p.words)), 'mean', true)}><b>尊敬・謙譲・丁寧</b><span>種類を見分ける10問</span></button>
            : <button onClick={() => p.onStart('助動詞・例文', mix(withEx), 'example')}><b>例文で見分ける</b><span>文の中での意味を選ぶ</span></button>}
          {keigo && <button onClick={() => p.onStart('敬語・例文', mix(withEx), 'example')}><b>例文で当てる</b><span>本文の中で意味を選ぶ</span></button>}
          <button onClick={() => p.onStart(`${title}・カード`, mix(p.words), 'card')}><b>一問一答カード</b><span>めくって確かめる</span></button>
        </div>
      )}
      <ul className="rows">
        {p.words.map((w) => (
          <li key={w.id}>
            <button className={`row${p.premium ? '' : ' locked'}`} onClick={() => (p.premium ? p.onWord(w.id) : p.onPaywall())}>
              <span className="row-rank">{keigo ? w.kind : ''}</span>
              <span className="row-w">{w.w}</span>
              <span className="row-m">{p.premium ? w.quiz : (keigo ? w.plain ?? '' : w.conn ?? '')}</span>
              <span className={`dot ${isNigate(p.data.records[w.id]) ? 'ng' : p.data.records[w.id] ? 'seen' : ''}`} />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
