import { useMemo, useState } from 'react';
import type { AppData, Mode, Word, WordSet } from '../domain/types';
import { CLEAR_STREAK, EXAMPLE_TRIAL, INTERVALS, addDays, dayKey, progress, type Plan } from '../domain/study';
import { Art, Empty, Icon, TopBar } from './Chrome';

/** 学習のタブ: 覚え方4つと敬語・助動詞のセット */
export function StudyPage(p: {
  data: AppData; premium: boolean; keigoN: number; jodoN: number; first: boolean;
  onBack: () => void; onToday: () => void; onMode: (m: Mode) => void; onSet: (s: WordSet) => void; onList: () => void;
}) {
  const trialLeft = Math.max(0, EXAMPLE_TRIAL - p.data.exTrial);
  const item = (ic: string, title: string, sub: string, on: () => void, lock = false) => (
    <li key={title}>
      <button className="cardrow" onClick={on}>
        <Art name={ic} className="cardrow-ic" />
        <span className="cardrow-body"><b>{title}</b><span>{sub}</span></span>
        {lock ? <Icon name="lock" size={18} className="lock-ic" /> : <Icon name="chev" size={18} className="chev" />}
      </button>
    </li>
  );
  return (
    <div className="page study has-tabs">
      <TopBar title="学習" icon="ic_book" onClose={p.onBack} />
      <Art name="head_sub" className="sub-art" />
      <h2 className="sec-h"><span>覚え方を選ぶ</span></h2>
      <ul className="cardrows">
        {item('ic_shelf', '重要語からめくる', p.first ? 'はじめの10語。重要度の高い順に4択で' : '今日の復習と新しい語を、重要度の順に', p.onToday)}
        {item('ic_book', '4択で意味', '古語を見て、正しい意味を選ぶ', () => p.onMode('mean'))}
        {item('ic_doc', '意味から古語', '現代語の意味を見て、古語を選ぶ', () => p.onMode('reverse'))}
        {item('ic_scroll_pen', '例文で当てる', p.premium ? '古典の本文の中で、印の語の意味を選ぶ' : trialLeft ? `完全版・あと${trialLeft}問おためし可` : '完全版で使えます', () => p.onMode('example'), !p.premium && !trialLeft)}
        {item('ic_review', '一問一答カード', '思い出してから、めくって確かめる', () => p.onMode('card'))}
      </ul>
      <h2 className="sec-h"><span>セットで覚える</span></h2>
      <ul className="cardrows">
        {item('ic_fan', '敬語セット', p.premium ? `${p.keigoN}語・尊敬/謙譲/丁寧` : `${p.keigoN}語・問題は完全版`, () => p.onSet('keigo'))}
        {item('ic_scroll', '助動詞セット', p.premium ? `${p.jodoN}項目・意味の見分け` : `${p.jodoN}項目・問題は完全版`, () => p.onSet('jodoshi'))}
      </ul>
      <button className="btn wide list-btn" onClick={p.onList}><Icon name="search" size={20} />単語の一覧・さがす</button>
    </div>
  );
}

/** 苦手のタブ: 間違えた語の一覧。2回続けて正解で消える */
export function NigatePage(p: { words: Word[]; data: AppData; onBack: () => void; onStart: (ws: Word[]) => void; onWord: (id: string) => void; onStudy: () => void }) {
  const [f, setF] = useState<'all' | WordSet>('all');
  const counts = { main: 0, keigo: 0, jodoshi: 0 } as Record<WordSet, number>;
  for (const w of p.words) counts[w.set]++;
  const list = f === 'all' ? p.words : p.words.filter((w) => w.set === f);
  if (!p.words.length) {
    return (
      <div className="page nigate-page has-tabs">
        <TopBar title="苦手" onClose={p.onBack} />
        <Empty art="empty_cat" title="苦手がありません" action={<button className="btn ghost-pill" onClick={p.onStudy}>問題を解く<Icon name="chev" size={18} /></button>}>
          <p>すばらしいです!<br />今のところ、苦手な単語はありません。<br />間違えた語はここに残り、<br />2回続けて正解すると消えます。</p>
        </Empty>
      </div>
    );
  }
  const n = Math.min(20, list.length);
  return (
    <div className="page nigate-page has-tabs">
      <TopBar title="こぶんめくり" onClose={p.onBack} />
      <section className="page-head">
        <Art name="head_sub" className="page-head-art" />
        <p className="page-head-title"><Art name="ic_omamori" className="page-head-ic" />苦手</p>
        <p className="page-head-sub">{CLEAR_STREAK}回続けて正解すると消えます。</p>
      </section>
      <div className="chips-row">
        <button className={f === 'all' ? 'on' : ''} onClick={() => setF('all')}>すべて <b>{p.words.length}</b></button>
        {(['main', 'keigo', 'jodoshi'] as WordSet[]).filter((k) => counts[k]).map((k) => (
          <button key={k} className={f === k ? 'on' : ''} onClick={() => setF(k)}>{k === 'main' ? '古文単語' : k === 'keigo' ? '敬語' : '助動詞'} <b>{counts[k]}</b></button>
        ))}
      </div>
      <ul className="wrows">
        {list.map((w) => {
          const r = p.data.records[w.id];
          const st = r?.streak ?? 0;
          return (
            <li key={w.id}>
              <button className="wrow" onClick={() => p.onWord(w.id)}>
                <Icon name={st ? 'markFill' : 'mark'} size={20} className="wrow-mark" />
                <span className="wrow-body"><b>{w.w}</b>{w.kanji && <small>{w.kanji}</small>}<span>{w.quiz}</span></span>
                <span className="streak">
                  <span className="dots">{Array.from({ length: CLEAR_STREAK }, (_, k) => <i key={k} className={k < st ? 'on' : ''} />)}</span>
                  <span>あと{CLEAR_STREAK - st}回</span>
                </span>
                <Icon name="chev" size={16} className="chev" />
              </button>
            </li>
          );
        })}
      </ul>
      <div className="bottom-bar above-tabs">
        <button className="btn shu wide big start-nigate" onClick={() => p.onStart(list)}>苦手を解く({n}語)<Icon name="chev" size={18} /></button>
      </div>
    </div>
  );
}

const GAP: Record<number, string> = { 0: '今日', 1: '1日あけ', 3: '3日あけ', 7: '1週間あけ', 14: '2週間あけ', 30: '1か月あけ', 60: '2か月あけ' };

/** 今日の復習: 期限が来た語の一覧 */
export function ReviewPage(p: { words: Word[]; data: AppData; onBack: () => void; onStart: () => void; onToday: () => void; onWord: (id: string) => void }) {
  if (!p.words.length) {
    return (
      <div className="page review-page">
        <TopBar title="今日の復習" onClose={p.onBack} />
        <Empty art="empty_veranda" wide title="今日の復習はありません" action={<button className="btn ghost-pill" onClick={p.onToday}>問題を解く<Icon name="chev" size={18} /></button>}>
          <p>本日の復習はすべて完了しています。<br />答えた語は、1日後・3日後・1週間後…と<br />間をあけて、ここにまた戻ってきます。</p>
        </Empty>
      </div>
    );
  }
  const n = Math.min(40, p.words.length);
  return (
    <div className="page review-page">
      <TopBar title="こぶんめくり" onClose={p.onBack} />
      <section className="page-head">
        <Art name="head_sub" className="page-head-art" />
        <p className="page-head-title"><Art name="ic_review" className="page-head-ic" />今日の復習</p>
        <p className="page-head-sub">今日は <b>{p.words.length}</b> 語の復習です<br /><small>忘れる前に、もう一度確認しましょう。</small></p>
      </section>
      <ul className="wrows">
        {p.words.map((w) => {
          const r = p.data.records[w.id]!;
          const gap = INTERVALS[r.box] ?? 0;
          const ex = w.ex[0];
          return (
            <li key={w.id}>
              <button className="wrow" onClick={() => p.onWord(w.id)}>
                <span className="wrow-body"><b>{w.w}</b>{w.kanji && <small>{w.kanji}</small>}<span>{ex ? shorten(ex.text, ex.hit) : w.quiz}</span></span>
                <span className={`gap g${gap}`}>{GAP[gap] ?? `${gap}日あけ`}</span>
                <Icon name="chev" size={16} className="chev" />
              </button>
            </li>
          );
        })}
      </ul>
      <div className="bottom-bar">
        <button className="btn shu wide big start-review" onClick={p.onStart}>今日の復習をはじめる({n}語)<Icon name="chev" size={18} /></button>
      </div>
    </div>
  );
}

function shorten(text: string, hit: string) {
  if (text.length <= 22) return text;
  const i = Math.max(0, text.indexOf(hit) - 6);
  return (i > 0 ? '…' : '') + text.slice(i, i + 22) + '…';
}

/** 学習計画: 試験日からの逆算と、毎日の答えた数 */
export function PlanPage(p: { open: Word[]; data: AppData; plan: Plan | null; due: number; nigate: number; onBack: () => void; onSettings: () => void }) {
  const pr = progress(p.open, p.data);
  const now = Date.now();
  const days = useMemo(() => Array.from({ length: 7 }, (_, k) => dayKey(addDays(now, k - 6))), [now]);
  const vals = days.map((d) => p.data.daily[d] ?? 0);
  const max = Math.max(10, ...vals);
  const pct = Math.round((pr.learned / Math.max(1, pr.total)) * 100);
  return (
    <div className="page plan-page">
      <TopBar title={<><Art name="ic_calendar" className="topbar-ic" />学習計画</>} onClose={p.onBack} />
      <section className="plan-hero">
        <Art name="head_sub" className="plan-art" />
        {p.plan ? (
          <>
            <p className="plan-lab">試験日まであと</p>
            <p className="plan-num"><b>{p.plan.days}</b>日</p>
            <p className="plan-sub">1日{p.plan.perDay}語ペースで、がんばりましょう。</p>
          </>
        ) : (
          <>
            <p className="plan-lab">試験日が未設定です</p>
            <p className="plan-sub">試験日を入れると、残りの日数から<br />1日に覚える語数を逆算します。</p>
          </>
        )}
      </section>
      <section className="card plan-prog">
        <p className="plan-prog-h"><Art name="ic_book_green" className="mini-ic" />学習進捗<span className="plan-prog-n"><Art name="ic_crown" className="mini-ic" /><b>{pr.learned}</b>/{pr.total}語({pct}%)</span></p>
        <div className="bar green"><i style={{ width: `${pct}%` }} /></div>
      </section>
      <div className="stat3">
        <div><Art name="ic_book_green" className="st-ic" /><span>覚えた語</span><b>{pr.learned}<small>語</small></b></div>
        <div><Icon name="redo" size={26} className="st-ic kin-ic" /><span>復習待ち</span><b>{p.due}<small>語</small></b></div>
        <div><Art name="ic_omamori" className="st-ic" /><span>苦手</span><b>{p.nigate}<small>語</small></b></div>
      </div>
      <section className="card chart-card">
        <h3 className="chart-h">1日の学習数<small>(答えた問題の数・この7日)</small></h3>
        <div className="chart">
          {vals.map((v, k) => (
            <div key={k} className="chart-col">
              <span className="chart-v">{v || ''}</span>
              <i style={{ height: `${(v / max) * 100}%` }} />
              <span className="chart-d">{Number(days[k].slice(5, 7))}/{Number(days[k].slice(8))}</span>
            </div>
          ))}
        </div>
      </section>
      <section className="card goal">
        <Icon name="bars" size={24} className="midori-ic" />
        <div>
          <p className="goal-h">1日の目標</p>
          <p className="goal-v">{p.plan ? `1日${p.plan.perDay}語ペース` : `1回${p.data.settings.batch}問`}</p>
          <p className="goal-s">{p.plan ? '試験日から自動で算出しています。' : '試験日を入れると自動で算出します。'}</p>
        </div>
        <button className="btn small ghost-pill" onClick={p.onSettings}>変更する<Icon name="chev" size={16} /></button>
      </section>
    </div>
  );
}
