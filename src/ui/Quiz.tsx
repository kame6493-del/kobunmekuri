import { useEffect, useMemo, useRef, useState } from 'react';
import type { AppData, Mode, Word } from '../domain/types';
import { dayKey, isNigate, makeKindQuestion, makeQuestion, rng, streakDays, type Question } from '../domain/study';
import { buzz } from '../platform/native';
import { Art, Hit, Icon, Pill, TopBar, WordBody } from './Chrome';

export { TopBar, WordBody, Hit } from './Chrome';

export interface Session {
  title: string;
  ids: string[];
  mode: Mode;
  seed: number;
  /** 例文のおためし(無料) */
  trial?: boolean;
  /** 敬語の種類(尊敬・謙譲・丁寧)を当てる */
  kind?: boolean;
  /** 今日の復習(終わって残りが0なら「本日の復習おわり」) */
  review?: boolean;
}

interface Answer { word: Word; ok: boolean; wasNigate: boolean }

const LETTERS = ['A', 'B', 'C', 'D'];
const MODE_ICON: Record<Mode, string> = { mean: 'ic_book', reverse: 'ic_doc', example: 'ic_scroll_pen', card: 'ic_review' };

function setLabel(w: Word) {
  return w.set === 'keigo' ? '敬語' : w.set === 'jodoshi' ? '助動詞' : '古文単語';
}

export function Quiz(p: {
  session: Session; byId: Map<string, Word>; pool: Word[]; data: AppData;
  /** 今日の復習の残り(結果の出し分け用) */
  dueLeft: number;
  onAnswer: (w: Word, ok: boolean, trial: boolean) => void;
  onEnd: (rate: number) => void;
  onClose: () => void; onHome: () => void;
  onAgain: (s: Session) => void;
  onPaywall: () => void;
  onWord: (id: string) => void;
}) {
  const s = p.session;
  const words = useMemo(() => s.ids.map((id) => p.byId.get(id)).filter((w): w is Word => !!w), [s.ids, p.byId]);
  const questions = useMemo<Question[]>(() => {
    const rand = rng(s.seed);
    return words.map((w) => {
      if (s.kind) return makeKindQuestion(w);
      const exIndex = s.mode === 'example' && w.ex.length ? Math.floor(rand() * w.ex.length) : 0;
      return makeQuestion(w, s.mode, p.pool, rand, exIndex);
    });
    // 出題は始めた時点で固定する(答えるたびに作り直さない)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [words]);
  const [i, setI] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [flipped, setFlipped] = useState(false);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [done, setDone] = useState(false);
  const startNigate = useRef(new Map(words.map((w) => [w.id, isNigate(p.data.records[w.id])])));

  const q = questions[i];
  const answeredNow = picked !== null;

  useEffect(() => { window.scrollTo(0, 0); }, [i, done]);

  if (!q) return <div className="page"><TopBar title={s.title} onClose={p.onClose} /><p className="empty">出す語がありません</p></div>;

  const commit = (ok: boolean, choice: number) => {
    setPicked(choice);
    buzz(ok);
    p.onAnswer(q.word, ok, !!s.trial);
    setAnswers((a) => [...a, { word: q.word, ok, wasNigate: startNigate.current.get(q.word.id) ?? false }]);
  };
  const next = () => {
    if (i + 1 >= questions.length) {
      setDone(true);
      const ok = answers.filter((a) => a.ok).length;
      p.onEnd(ok / Math.max(1, answers.length));
      return;
    }
    setI(i + 1); setPicked(null); setFlipped(false);
  };

  if (done) return <Result s={s} answers={answers} data={p.data} dueLeft={p.dueLeft} onClose={p.onClose} onHome={p.onHome} onAgain={p.onAgain} onPaywall={p.onPaywall} onWord={p.onWord} />;

  const ex = s.mode === 'example' ? q.word.ex[q.exIndex ?? 0] : undefined;
  const ok = picked === q.answer;
  const w = q.word;
  const nigateNow = isNigate(p.data.records[w.id]) && !answeredNow;
  const card = s.mode === 'card' && !s.kind;
  const lettered = !s.kind && s.mode !== 'example';

  return (
    <div className={`page quiz mode-${s.kind ? 'kind' : s.mode}`}>
      <TopBar title={s.title} icon={s.kind ? 'ic_fan' : MODE_ICON[s.mode]} onClose={p.onClose} closeLabel="やめる" right={<span className="count">{i + 1}<small> / {questions.length}</small></span>} />
      <div className="progress" role="progressbar" aria-valuenow={i + 1} aria-valuemax={questions.length}><i style={{ width: `${((i + (answeredNow ? 1 : 0)) / questions.length) * 100}%` }} /></div>

      {card ? (
        !flipped ? (
          <>
            <section className="flash front">
              <Art name="plum_corner" className="flash-plum" />
              <p className="flash-tag">{setLabel(w)}{w.set === 'main' ? ` ・ 重要度 ${w.rank}` : ''}{nigateNow && <span className="q-ng">苦手</span>}</p>
              <p className="q-prompt flash-w">{w.w}{w.kanji && <small>{w.kanji}</small>}</p>
              <button className="card-flip" onClick={() => setFlipped(true)}><Icon name="flip" size={22} />めくる</button>
              <Art name="land_card" className="flash-land" />
            </section>
            <p className="flash-hint">意味を思い出してから、<br />めくりましょう。</p>
          </>
        ) : (
          <>
            <section className="flash back card-back">
              <Art name="plum_corner" className="flash-plum" />
              <p className="q-prompt flash-w">{w.w}{w.kanji && <small>{w.kanji}</small>}</p>
              <p className="flash-pos"><Pill>{w.kind ? `${w.kind}語` : w.pos}</Pill></p>
              <ol className="flash-means">{w.means.map((m, k) => <li key={k}>{m}</li>)}</ol>
              {(w.plain || w.conn) && <p className="flash-sub">{w.plain ? `普通の語: ${w.plain}` : `接続: ${w.conn}`}</p>}
              {w.ex[0] && (
                <div className="flash-ex">
                  <span className="flash-ex-h">〈例文〉</span>
                  <p><Hit text={w.ex[0].text} hit={w.ex[0].hit} /></p>
                  <p className="flash-tr">{w.ex[0].tr}</p>
                  <p className="ex-src">── {w.ex[0].src}</p>
                </div>
              )}
              <p className="flash-note">{w.note}</p>
              <Art name="land_pagoda" className="flash-land" />
            </section>
            {!answeredNow ? (
              <>
                <p className="grade-ask">覚えていましたか?</p>
                <div className="self-grade">
                  <button className="btn grade ok" onClick={() => commit(true, q.answer)}><Icon name="check" size={20} />わかった</button>
                  <button className="btn grade ng" onClick={() => commit(false, -1)}><Icon name="mark" size={20} />苦手に入れる</button>
                </div>
              </>
            ) : (
              <p className={`graded ${ok ? 'good' : 'bad'}`}>{ok ? 'わかった語として記録しました' : '苦手に入れました。2回続けて正解すると消えます'}</p>
            )}
          </>
        )
      ) : (
        <>
          {s.mode === 'example' && ex ? (
            <>
              <section className="excard">
                <Art name="plum_corner" className="excard-plum" />
                <blockquote className="q-ex"><Hit text={ex.text} hit={ex.hit} /></blockquote>
                <p className="q-exsrc">── {ex.src}</p>
                <Art name="land_card" className="excard-land" />
              </section>
              <p className="q-ask2"><span className="q-tag">問題</span><span>この文の中の【{ex.hit}】の{w.set === 'jodoshi' ? '意味(用法)' : '意味'}として、最も適切なものを選びましょう。</span></p>
            </>
          ) : (
            <section className="qcard">
              <span className="q-no">問題 {i + 1}</span>
              <Art name="plum_corner" className="qcard-plum" />
              {s.mode === 'reverse' && !s.kind ? (
                <>
                  <p className="q-ask">この意味にあてはまる古語を、選びましょう。</p>
                  <p className="q-prompt q-meaning">{q.prompt}</p>
                  <p className="q-meta">{w.set === 'main' ? `重要度 ${w.rank}` : setLabel(w)}{nigateNow && <span className="q-ng">苦手</span>}</p>
                </>
              ) : (
                <>
                  <p className="q-pill"><Pill tone="shu">{setLabel(w)}</Pill></p>
                  <p className="q-prompt">{w.w}{w.kanji && <small>{w.kanji}</small>}</p>
                  <p className="q-meta">{w.set === 'main' ? `重要度 ${w.rank} ・ ` : ''}{w.set === 'jodoshi' ? '' : w.pos}{nigateNow && <span className="q-ng">苦手</span>}</p>
                  <p className="q-ask">{s.kind ? 'この敬語の種類を選びましょう。' : 'この古語の意味として、最も適切なものを選びましょう。'}</p>
                </>
              )}
            </section>
          )}

          <ol className={`choices${s.kind ? ' kind' : ''}${lettered ? ' lettered' : ' numbered'}`}>
            {q.choices.map((c, k) => {
              let cls = 'choice';
              if (answeredNow) {
                if (k === q.answer) cls += ' right';
                else if (k === picked) cls += ' wrong';
              }
              return (
                <li key={k}>
                  <button className={cls} disabled={answeredNow} onClick={() => commit(k === q.answer, k)}>
                    {!s.kind && <span className={`choice-k k${k}`}>{lettered ? LETTERS[k] : k + 1}</span>}
                    <span className="choice-t">{c}</span>
                  </button>
                </li>
              );
            })}
          </ol>

          {answeredNow && (
            <section className={`verdict ${ok ? 'good' : 'bad'}`}>
              <p className="verdict-head">{ok ? <><Art name="ic_ok" className="verdict-ic" />正解です!</> : <><Art name="ic_ng" className="verdict-ic" />残念…</>}</p>
              <p className="verdict-ans">
                <span className="verdict-lab">{ok ? 'あなたの答え' : '正解は…'}</span>
                {!s.kind && <span className={`choice-k k${q.answer}`}>{lettered ? LETTERS[q.answer] : q.answer + 1}</span>}
                <b>{q.choices[q.answer]}</b>
                {s.mode !== 'reverse' && <span className="verdict-w">{w.w}{w.kanji ? `(${w.kanji})` : ''}</span>}
              </p>
              <WordBody word={w} exIndex={q.exIndex} quoted={s.mode === 'example'} />
              <Others q={q} mode={s.mode} kind={!!s.kind} lettered={lettered} />
            </section>
          )}
        </>
      )}

      {answeredNow && (
        <div className="bottom-bar">
          <button className={`btn primary wide big${ok ? ' midori' : ''}`} onClick={next}>{i + 1 >= questions.length ? '結果を見る' : '次の問題へ'}<Icon name="chev" size={18} /></button>
        </div>
      )}
    </div>
  );
}

/** 他の選択肢が、どの語の意味(どの語)だったか */
function Others(p: { q: Question; mode: Mode; kind: boolean; lettered: boolean }) {
  const { q } = p;
  if (p.kind || !q.from) return null;
  const rows = q.choices.map((c, k) => ({ c, k, w: q.from![k] })).filter((r) => r.k !== q.answer && r.w && r.w.id !== q.word.id);
  if (!rows.length) return null;
  return (
    <section className="wsec others">
      <h3>他の選択肢について</h3>
      <ul>
        {rows.map((r) => (
          <li key={r.k}>
            <span className={`choice-k k${r.k}`}>{p.lettered ? LETTERS[r.k] : r.k + 1}</span>
            <span>{p.mode === 'reverse' ? <><b>{r.c}</b> … 「{r.w.quiz}」の意味</> : <>「{r.c}」… <b>{r.w.w}</b>{r.w.kanji ? `(${r.w.kanji})` : ''}の意味</>}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Result(p: {
  s: Session; answers: Answer[]; data: AppData; dueLeft: number;
  onClose: () => void; onHome: () => void; onAgain: (s: Session) => void; onPaywall: () => void; onWord: (id: string) => void;
}) {
  const { s, answers } = p;
  const ok = answers.filter((a) => a.ok).length;
  const wrong = answers.length - ok;
  const newNigate = answers.filter((a) => !a.ok && !a.wasNigate).length;
  const cleared = answers.filter((a) => a.wasNigate && !isNigate(p.data.records[a.word.id])).length;
  const rate = Math.round((ok / Math.max(1, answers.length)) * 100);
  const now = Date.now();
  const list = (
    <>
      <h3 className="sec">今回の語</h3>
      <ul className="result-list">
        {answers.map((a, k) => (
          <li key={k}>
            <button onClick={() => p.onWord(a.word.id)}>
              <span className={a.ok ? 'mark-ok' : 'mark-ng'}>{a.ok ? '○' : '×'}</span>
              <span className="rl-w">{a.word.w}</span>
              <span className="rl-m">{a.word.quiz}</span>
              <Icon name="chev" size={16} className="rl-chev" />
            </button>
          </li>
        ))}
      </ul>
    </>
  );

  if (s.review && p.dueLeft === 0) {
    return (
      <div className="page result done-review" data-ok={ok}>
        <TopBar title="今日の復習" onClose={p.onClose} />
        <Art name="done_ema" className="done-art" />
        <h2 className="done-title">本日の復習おわり</h2>
        <p className="done-text">よくがんばりました!<br />ひとつひとつの積み重ねが、きっと力になります。<br />また明日も、一緒にがんばりましょう。</p>
        <div className="done-stats">
          <div><Art name="ic_review" /><span>今日答えた数</span><b>{p.data.daily[dayKey(now)] ?? answers.length}<small>問</small></b></div>
          <div><Icon name="bars" size={28} className="midori-ic" /><span>学習継続日数</span><b>{streakDays(p.data.daily, now)}<small>日</small></b></div>
        </div>
        <p className="done-score">今回 <b className="res-ok">{ok}</b> / {answers.length} 問 正解{cleared ? ` ・ 苦手から外れた ${cleared}語` : ''}</p>
        <button className="btn primary big pill-btn" onClick={p.onHome}>ホームに戻る</button>
        {list}
      </div>
    );
  }

  return (
    <div className="page result" data-ok={ok}>
      <TopBar title={<><Icon name="bars" size={20} className="midori-ic" />学習結果</>} onClose={p.onClose} />
      <Art name="head_sub" className="result-art" />
      <section className="result-card result-hero">
        <p className="result-label">今回の学習</p>
        <p className="result-total"><b>{answers.length}</b>語</p>
        <div className="result-pair">
          <div className="rp ok"><span className="rp-ic">○</span><span>正解</span><b className="res-ok">{ok}<small>語</small></b></div>
          <div className="rp ng"><span className="rp-ic">×</span><span>苦手</span><b className="res-ng">{wrong}<small>語</small></b></div>
        </div>
        <div className="rate">
          <Art name="ic_crown" className="rate-ic" />
          <span>正解率 {rate}%</span>
          <div className="bar"><i style={{ width: `${rate}%` }} /></div>
        </div>
        <ul className="result-moves">
          <li>苦手から外れた<b className="res-cleared">{cleared}語</b></li>
          <li>新しく苦手に入った<b className="res-new">{newNigate}語</b></li>
        </ul>
      </section>
      <section className="cheer">
        <Art name="ic_books" className="cheer-ic" />
        <div>
          <b>{rate >= 70 ? 'よくがんばりました' : 'おつかれさまでした'}</b>
          <p>{wrong ? '苦手な語を復習して、さらに定着させましょう。' : '全部正解です。この調子で続けましょう。'}</p>
        </div>
      </section>
      {s.trial && (
        <button className="unlock" onClick={p.onPaywall}>
          <Art name="ic_crown" className="unlock-ic" />
          <span><span className="unlock-title">例文モードのおためしは、ここまでです</span>
          <span className="unlock-sub">完全版で全語の例文問題と、敬語・助動詞のセットが開きます</span></span>
        </button>
      )}
      <div className="result-actions">
        {!s.trial && <button className="btn shu wide big" onClick={() => p.onAgain(s)}>同じ語をもう一度<Icon name="chev" size={18} /></button>}
        <button className="link-btn" onClick={p.onHome}>ホームに戻る</button>
      </div>
      {list}
    </div>
  );
}
