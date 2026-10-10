import { useState } from 'react';
import type { AppData, Mode, Word, WordSet } from '../domain/types';
import { isNigate, kindQuizWords, rng, shuffle } from '../domain/study';
import { Art, Icon, Pill, TopBar } from './Chrome';

const KIND_TEXT: Record<string, [string, string]> = {
  尊敬: ['尊敬語', '動作をする人を高めて表す言い方です。主に、身分の高い人の動作や様子を敬います。'],
  謙譲: ['謙譲語', '動作を受ける人を高めて表す言い方です。動作をする側がへりくだります。'],
  丁寧: ['丁寧語', '聞き手(読み手)に対して、丁寧に述べる言い方です。「はべり」「さぶらふ」など。'],
};
const KIND_IC: Record<string, string> = { 尊敬: 'ic_plum', 謙譲: 'ic_leaf', 丁寧: 'ic_plum' };

export function SetPage(p: {
  set: WordSet; words: Word[]; data: AppData; premium: boolean;
  onBack: () => void; onPaywall: () => void; onWord: (id: string) => void;
  onStart: (title: string, ws: Word[], mode: Mode, kind?: boolean) => void;
}) {
  const keigo = p.set === 'keigo';
  const title = keigo ? '敬語セット' : '助動詞セット';
  const mix = (ws: Word[], n = 10) => shuffle(ws, rng(Date.now())).slice(0, n);
  const withEx = p.words.filter((w) => w.ex.length);
  const [kind, setKind] = useState('尊敬');
  const rows = keigo ? p.words.filter((w) => w.kind === kind) : p.words;

  return (
    <div className="page setpage">
      <TopBar title={title} icon={keigo ? 'ic_fan' : 'ic_scroll'} onClose={p.onBack} />
      <p className="set-lead">
        {keigo
          ? '入試に出る敬語を、意味・普通の語・尊敬/謙譲/丁寧の別でまとめました。種類の3択は、選択肢がいつも「尊敬・謙譲・丁寧」の順に並びます。'
          : '助動詞を、意味・接続・見分け方でまとめました。例文の問題は、同じ助動詞のどの意味かを選びます。'}
      </p>
      {!p.premium ? (
        <button className="unlock" onClick={p.onPaywall}>
          <Art name="ic_crown" className="unlock-ic" />
          <span><span className="unlock-title">{title}の問題は完全版で使えます</span>
          <span className="unlock-sub">下の一覧で中身を確かめられます</span></span>
          <Icon name="chev" size={18} className="chev" />
        </button>
      ) : (
        <div className="menu">
          <button onClick={() => p.onStart(`${title}・意味`, mix(p.words), 'mean')}><Art name="ic_book" /><b>意味の4択</b><span>10問</span></button>
          {keigo
            ? <button onClick={() => p.onStart('敬語の種類', mix(kindQuizWords(p.words)), 'mean', true)}><Art name="ic_fan" /><b>尊敬・謙譲・丁寧</b><span>種類を見分ける10問</span></button>
            : <button onClick={() => p.onStart('助動詞・例文', mix(withEx), 'example')}><Art name="ic_scroll_pen" /><b>例文で見分ける</b><span>文の中での意味を選ぶ</span></button>}
          {keigo && <button onClick={() => p.onStart('敬語・例文', mix(withEx), 'example')}><Art name="ic_scroll_pen" /><b>例文で当てる</b><span>本文の中で意味を選ぶ</span></button>}
          <button onClick={() => p.onStart(`${title}・カード`, mix(p.words), 'card')}><Art name="ic_review" /><b>一問一答カード</b><span>めくって確かめる</span></button>
        </div>
      )}

      {keigo ? (
        <>
          <div className="kind-tabs" role="tablist">
            {['尊敬', '謙譲', '丁寧'].map((k) => (
              <button key={k} role="tab" aria-selected={kind === k} className={kind === k ? 'on' : ''} onClick={() => setKind(k)}>
                <Art name={KIND_IC[k]} className="kind-ic" />{k}
              </button>
            ))}
          </div>
          <section className="kind-desc">
            <Art name="ic_plum" className="kind-desc-ic" />
            <div><b>{KIND_TEXT[kind][0]}</b><p>{KIND_TEXT[kind][1]}</p></div>
          </section>
        </>
      ) : (
        <h2 className="sec-h"><span>一覧から選ぶ</span></h2>
      )}

      <ul className="setrows rows">
        {rows.map((w) => {
          const r = p.data.records[w.id];
          return (
            <li key={w.id}>
              <button className={`setrow row${p.premium ? '' : ' locked'}`} onClick={() => (p.premium ? p.onWord(w.id) : p.onPaywall())}>
                <Art name={keigo ? KIND_IC[w.kind ?? '尊敬'] : 'ic_plum'} className="setrow-ic" />
                <span className="setrow-body">
                  <span className="setrow-h"><b className="row-w">{w.w}</b>{keigo && w.kanji && <small>({w.kanji})</small>}</span>
                  <span className="setrow-tags">
                    {keigo ? <><Pill tone="shu">{w.kind}</Pill><Pill>{w.pos}</Pill></> : <Pill>{w.conn ? `接続: ${w.conn}` : w.pos}</Pill>}
                  </span>
                  <span className="row-m setrow-m">
                    {p.premium ? (keigo ? <><i className="lab">意味</i>{w.quiz}</> : <><i className="lab">意味</i>{w.quiz}</>) : (keigo ? <><i className="lab">普通の語</i>{w.plain ?? ''}</> : <><Icon name="lock" size={14} />意味は完全版</>)}
                  </span>
                </span>
                <span className={`dot ${isNigate(r) ? 'ng' : r ? 'seen' : ''}`} />
                <Icon name={p.premium ? 'chev' : 'lock'} size={16} className="chev" />
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
