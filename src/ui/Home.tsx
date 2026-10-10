import type { AppData, Word } from '../domain/types';
import { FREE_MAIN, dueWords, progress, type Plan } from '../domain/study';
import { Art, Brand, Icon, fmtMD } from './Chrome';

export function Home(p: {
  data: AppData; main: Word[]; open: Word[]; premium: boolean; plan: Plan | null; nigate: number;
  onToday: () => void; onReview: () => void; onNigate: () => void; onExample: () => void;
  onPlan: () => void; onList: () => void; onPaywall: () => void; onSettings: () => void;
}) {
  const now = Date.now();
  const pr = progress(p.open, p.data);
  const due = dueWords(p.open, p.data, now).length;
  const first = Object.keys(p.data.records).length === 0;
  const total = p.premium ? p.main.length : FREE_MAIN;
  const newToday = p.plan ? p.plan.perDay : p.data.settings.batch;

  return (
    <div className="page home has-tabs">
      <header className="home-head">
        <button className="icon" aria-label="辞書(単語の一覧)" onClick={p.onList}><Icon name="shelf" size={26} /></button>
        <button className="icon gear" aria-label="設定" onClick={p.onSettings}><Icon name="gear" size={26} /></button>
      </header>
      <div className="home-brand">
        <Brand />
        <Art name="head_home" className="home-art" />
      </div>

      <section className="prog-card">
        <div className="prog-row">
          <Art name="ic_book_green" className="prog-ic" />
          <div className="prog-body">
            <p className="prog-label">{p.premium ? '完全版' : '無料版'} <b>{pr.seen}</b><small>/{total}語</small><span className="prog-note">めくった語</span></p>
            <div className="bar green"><i style={{ width: `${Math.min(100, (pr.seen / Math.max(1, total)) * 100)}%` }} /></div>
          </div>
        </div>
        {!p.premium && (
          <button className="prog-row unlock-row" onClick={p.onPaywall}>
            <Art name="ic_crown" className="prog-ic" />
            <div className="prog-body">
              <p className="prog-label kin">完全版で{p.main.length}語すべて</p>
              <div className="bar kin"><i style={{ width: '100%' }} /></div>
            </div>
            <Icon name="chev" size={18} className="chev" />
          </button>
        )}
      </section>

      <div className="tiles">
        <button className="tile hot" onClick={p.onReview}>
          <Art name="ic_review" className="tile-ic" />
          <b>今日の復習</b>
          <span className="tile-num">{due}<small>語</small></span>
          <Icon name="chev" size={18} className="chev" />
        </button>
        <button className="tile today" onClick={p.onToday}>
          <Art name="ic_shelf" className="tile-ic" />
          <b>重要語からめくる</b>
          <span className="tile-sub">{first ? 'はじめの10語' : `新しい語 ${newToday}語`}</span>
          <Icon name="chev" size={18} className="chev" />
        </button>
        <button className="tile nigate" onClick={p.onNigate}>
          <Art name="ic_omamori" className="tile-ic" />
          <b>苦手</b>
          <span className="tile-num ng">{p.nigate}<small>語</small></span>
          <Icon name="chev" size={18} className="chev" />
        </button>
        <button className="tile example" onClick={p.onExample}>
          <Art name="ic_scroll_pen" className="tile-ic" />
          <b>例文で覚える</b>
          <span className="tile-sub">古典の本文で当てる</span>
          <Icon name="chev" size={18} className="chev" />
        </button>
      </div>

      <section className="exam">
        <button className="exam-head" onClick={p.onPlan}>
          <Art name="ic_sprig" className="exam-sprig" />
          <span>試験日まで</span>
          {p.plan && <b className="exam-days">あと{p.plan.days}日</b>}
          <Icon name="chev" size={18} className="chev" />
        </button>
        <div className="exam-stats">
          <div><Art name="ic_review" className="st-ic" /><span>今日の復習</span><b>{due}<small>語</small></b></div>
          <div><Art name="ic_calendar" className="st-ic" /><span>試験日</span><b>{p.data.settings.examDate ? fmtMD(p.data.settings.examDate) : '未設定'}</b></div>
          <div><Icon name="bars" size={26} className="st-ic midori-ic" /><span>{p.plan ? '1日' : '1回'}</span><b>{p.plan ? p.plan.perDay : p.data.settings.batch}<small>語</small></b><span className="st-sub">ペース</span></div>
        </div>
        {p.plan ? (
          <p className="exam-sub hero-sub">{p.plan.remaining === 0 ? '全部覚えました。あとは復習だけです。' : `あと${p.plan.remaining}語。1日${p.plan.perDay}語で${fmtJa(p.plan.finishDate)}に一周します。`}</p>
        ) : (
          <p className="exam-sub hero-sub">試験日を入れると、1日に覚える語数を逆算します。<button className="link inline" onClick={p.onSettings}>試験日を入れる</button></p>
        )}
      </section>

      <p className="credit">例文は著作権の切れた古典の本文(ウィキソース所収の翻刻、CC BY-SA 4.0)から引き、字体を新字体に改めました。意味・解説・現代語訳はこのアプリで書いたものです。</p>
    </div>
  );
}

function fmtJa(day: string) {
  const [, m, d] = day.split('-').map(Number);
  return `${m}月${d}日`;
}
