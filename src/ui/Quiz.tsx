import { useEffect, useMemo, useRef, useState } from 'react';
import type { AppData, Mode, Word } from '../domain/types';
import { isNigate, makeKindQuestion, makeQuestion, rng, splitHit, type Question } from '../domain/study';
import { buzz } from '../platform/native';

export interface Session {
  title: string;
  ids: string[];
  mode: Mode;
  seed: number;
  /** 例文のおためし(無料) */
  trial?: boolean;
  /** 敬語の種類(尊敬・謙譲・丁寧)を当てる */
  kind?: boolean;
}

export function TopBar(p: { title: string; onClose: () => void; right?: React.ReactNode; closeLabel?: string }) {
  return (
    <header className="topbar">
      <button className="icon" aria-label={p.closeLabel ?? '戻る'} onClick={p.onClose}>‹</button>
      <h1>{p.title}</h1>
      <div className="topbar-right">{p.right}</div>
    </header>
  );
}

export function Hit(p: { text: string; hit: string }) {
  const [a, b, c] = splitHit(p.text, p.hit);
  return <>{a}{b && <mark>{b}</mark>}{c}</>;
}

/** 語の中身(意味・解説・例文)。答えたあと・単語の詳しい画面で同じ物を使う */
export function WordBody(p: { word: Word; exIndex?: number; showNote?: boolean; quoted?: boolean }) {
  const w = p.word;
  const exs = p.exIndex !== undefined && w.ex[p.exIndex] ? [w.ex[p.exIndex], ...w.ex.filter((_, i) => i !== p.exIndex)] : w.ex;
  return (
    <div className="wbody">
      <ol className="means">
        {w.means.map((m, i) => <li key={i}>{m}</li>)}
      </ol>
      {(w.kind || w.plain || w.conn) && (
        <p className="wtags">
          {w.kind && <span>{w.kind}語</span>}
          {w.plain && <span>普通の語: {w.plain}</span>}
          {w.conn && <span>接続: {w.conn}</span>}
        </p>
      )}
      {p.showNote !== false && <p className="note">{w.note}</p>}
      {exs.map((e, i) => (
        <figure className="ex" key={i}>
          {/* 例文問題では、問題の欄に同じ本文が出ているので訳だけ見せる */}
          {!(p.quoted && i === 0) && <blockquote><Hit text={e.text} hit={e.hit} /></blockquote>}
          {p.quoted && i === 0 && <span className="ex-label">この文の訳</span>}
          <figcaption>
            <span className="ex-tr">{e.tr}</span>
            <span className="ex-src">{e.src}{w.set === 'jodoshi' ? `(${w.means[e.sense] ?? ''})` : ''}</span>
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

interface Answer { word: Word; ok: boolean; wasNigate: boolean }

export function Quiz(p: {
  session: Session; byId: Map<string, Word>; pool: Word[]; data: AppData;
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

  if (done) {
    const ok = answers.filter((a) => a.ok).length;
    const newNigate = answers.filter((a) => !a.ok && !a.wasNigate).length;
    const cleared = answers.filter((a) => a.wasNigate && !isNigate(p.data.records[a.word.id])).length;
    return (
      <div className="page result">
        <TopBar title={s.title} onClose={p.onClose} />
        <section className="result-hero">
          <p className="result-score"><b>{ok}</b><span>/ {answers.length}</span></p>
          <ul className="result-moves">
            <li>苦手から外れた<b>{cleared}語</b></li>
            <li>新しく苦手に入った<b>{newNigate}語</b></li>
          </ul>
        </section>
        <ul className="result-list">
          {answers.map((a, k) => (
            <li key={k}>
              <button onClick={() => p.onWord(a.word.id)}>
                <span className={a.ok ? 'mark-ok' : 'mark-ng'}>{a.ok ? '○' : '×'}</span>
                <span className="rl-w">{a.word.w}</span>
                <span className="rl-m">{a.word.quiz}</span>
              </button>
            </li>
          ))}
        </ul>
        {s.trial && (
          <button className="unlock" onClick={p.onPaywall}>
            <span className="unlock-title">例文モードのおためしは、ここまでです</span>
            <span className="unlock-sub">完全版で全語の例文問題と、敬語・助動詞のセットが開きます</span>
          </button>
        )}
        <div className="result-actions">
          {!s.trial && <button className="btn wide" onClick={() => p.onAgain(s)}>同じ語をもう一度</button>}
          <button className="btn primary wide big" onClick={p.onHome}>ホームへ</button>
        </div>
      </div>
    );
  }

  const ex = s.mode === 'example' ? q.word.ex[q.exIndex ?? 0] : undefined;
  const ok = picked === q.answer;

  return (
    <div className="page quiz">
      <TopBar title={s.title} onClose={p.onClose} closeLabel="やめる" right={<span className="count">{i + 1}<small>/{questions.length}</small></span>} />
      <div className="progress"><i style={{ width: `${(i / questions.length) * 100}%` }} /></div>

      <section className="question">
        <p className="q-meta">
          <span className="q-tag">{q.word.set === 'keigo' ? '敬語' : q.word.set === 'jodoshi' ? '助動詞' : `重要度 ${q.word.rank}`}</span>
          <span>{q.word.pos}</span>
          {isNigate(p.data.records[q.word.id]) && !answeredNow && <span className="q-ng">苦手</span>}
        </p>
        {s.mode === 'reverse' && !s.kind ? (
          <>
            <p className="q-ask">この意味の古語は?</p>
            <p className="q-prompt q-meaning">{q.prompt}</p>
          </>
        ) : s.mode === 'example' && ex ? (
          <>
            <p className="q-ask">印の語の、この文での意味は?</p>
            <blockquote className="q-ex"><Hit text={ex.text} hit={ex.hit} /></blockquote>
            <p className="q-exsrc">{ex.src}</p>
          </>
        ) : (
          <>
            <p className="q-ask">{s.kind ? 'この敬語の種類は?' : s.mode === 'card' ? '意味を思い出してから、めくる' : '意味は?'}</p>
            <p className="q-prompt">{q.word.w}{q.word.kanji && <small>{q.word.kanji}</small>}</p>
          </>
        )}
      </section>

      {s.mode === 'card' && !s.kind ? (
        !flipped ? (
          <button className="card-flip" onClick={() => setFlipped(true)}>めくる</button>
        ) : (
          <div className="card-back">
            <WordBody word={q.word} />
            {!answeredNow && (
              <div className="self-grade">
                <button className="btn ng big" onClick={() => commit(false, -1)}>まだ</button>
                <button className="btn ok big" onClick={() => commit(true, q.answer)}>覚えてた</button>
              </div>
            )}
          </div>
        )
      ) : (
        <ol className={`choices${s.kind ? ' kind' : ''}`}>
          {q.choices.map((c, k) => {
            let cls = 'choice';
            if (answeredNow) {
              if (k === q.answer) cls += ' right';
              else if (k === picked) cls += ' wrong';
            }
            return (
              <li key={k}>
                <button className={cls} disabled={answeredNow} onClick={() => commit(k === q.answer, k)}>{c}</button>
              </li>
            );
          })}
        </ol>
      )}

      {answeredNow && s.mode !== 'card' && (
        <section className={`verdict ${ok ? 'good' : 'bad'}`}>
          <p className="verdict-head">{ok ? '正解' : '不正解'}<span>{q.word.w}{q.word.kanji ? `(${q.word.kanji})` : ''}</span></p>
          <WordBody word={q.word} exIndex={q.exIndex} quoted={s.mode === 'example'} />
        </section>
      )}

      {answeredNow && (
        <div className="bottom-bar">
          <button className="btn primary wide big" onClick={next}>{i + 1 >= questions.length ? '結果を見る' : '次へ'}</button>
        </div>
      )}
    </div>
  );
}
