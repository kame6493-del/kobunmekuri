import type { AppData, Mode, Word, WordSet } from '../domain/types';
import { EXAMPLE_TRIAL, FREE_MAIN, dayKey, dueWords, progress, streakDays, type Plan } from '../domain/study';

export function Home(p: {
  data: AppData; main: Word[]; open: Word[]; all: Word[]; premium: boolean; plan: Plan | null;
  onToday: () => void; onReview: () => void; onNigate: () => void; onMode: (m: Mode) => void;
  onList: () => void; onSet: (s: WordSet) => void; onPaywall: () => void; onSettings: () => void;
}) {
  const now = Date.now();
  const pr = progress(p.open, p.data);
  const nigateAll = progress(p.all, p.data).nigate;
  const due = dueWords(p.open, p.data, now).length;
  const today = p.data.daily[dayKey(now)] ?? 0;
  const streak = streakDays(p.data.daily, now);
  const first = Object.keys(p.data.records).length === 0;
  const trialLeft = Math.max(0, EXAMPLE_TRIAL - p.data.exTrial);
  const keigoN = p.all.filter((w) => w.set === 'keigo').length;
  const jodoN = p.all.filter((w) => w.set === 'jodoshi').length;
  const newToday = p.plan ? p.plan.perDay : p.data.settings.batch;

  return (
    <div className="page home">
      <header className="home-head">
        <div className="brand">
          <span className="brand-name">こぶんめくり</span>
          <span className="brand-sub">古文単語{p.main.length}語</span>
        </div>
        <button className="icon gear" aria-label="設定" onClick={p.onSettings}>⚙</button>
      </header>

      <section className="hero">
        {p.plan ? (
          <>
            <p className="hero-label">試験まで</p>
            <p className="hero-num"><b>{p.plan.days}</b><span>日</span></p>
            <p className="hero-sub">
              {p.plan.remaining === 0 ? '全部覚えました。あとは復習だけです。' : `あと${p.plan.remaining}語。1日${p.plan.perDay}語で${fmt(p.plan.finishDate)}に一周します。`}
            </p>
          </>
        ) : first ? (
          <>
            <p className="hero-lead">1日10語、めくるだけ。</p>
            <p className="hero-sub">間違えた語は一覧に残り、2回続けて正解すると消えます。覚えた語は1日後・3日後・1週間後…と間をあけてまた出ます。</p>
          </>
        ) : (
          <>
            <p className="hero-label">覚えた語</p>
            <p className="hero-num"><b>{pr.learned}</b><span>/ {pr.total}語</span></p>
            <p className="hero-sub">試験日を入れると、1日に覚える数を逆算します。<button className="link inline" onClick={p.onSettings}>試験日を入れる</button></p>
          </>
        )}
        <button className="btn primary wide big two" onClick={p.onToday}>
          {first ? 'はじめの10語をめくる' : <>今日の分をはじめる<small>復習 {due}語 ・ 新しい語 {newToday}語</small></>}
        </button>
      </section>

      <div className="chips">
        <span className="chip">今日 <b>{today}</b>問</span>
        <span className="chip">連続 <b>{streak}</b>日</span>
        <span className="chip">覚えた <b>{pr.learned}</b>/{pr.total}</span>
        <span className="chip ng">まちがい <b>{nigateAll}</b></span>
      </div>

      <div className="twin">
        <button className="tile" onClick={p.onReview} disabled={due === 0}>
          <b>今日の復習</b><span>{due ? `${due}語が待っています` : '今日の分は終わりました'}</span>
        </button>
        <button className="tile nigate" onClick={p.onNigate} disabled={nigateAll === 0}>
          <b>まちがえた語だけ</b><span>{nigateAll ? `${nigateAll}語。2回続けて正解で消えます` : 'まだありません'}</span>
        </button>
      </div>

      <h2 className="sec">覚え方を選ぶ</h2>
      <div className="menu">
        <button onClick={() => p.onMode('mean')}><b>4択で意味</b><span>古語を見て意味を選ぶ</span></button>
        <button onClick={() => p.onMode('reverse')}><b>意味から古語</b><span>意味を見て古語を選ぶ</span></button>
        <button onClick={() => p.onMode('example')}>
          <b>例文で当てる</b>
          <span>{p.premium ? '古典の本文の中で意味を選ぶ' : trialLeft ? `完全版・あと${trialLeft}問おためし可` : '完全版で使えます'}</span>
        </button>
        <button onClick={() => p.onMode('card')}><b>一問一答カード</b><span>思い出してから、めくる</span></button>
        <button onClick={() => p.onSet('keigo')}><b>敬語セット</b><span>{p.premium ? `${keigoN}語・尊敬/謙譲/丁寧` : `${keigoN}語・完全版`}</span></button>
        <button onClick={() => p.onSet('jodoshi')}><b>助動詞セット</b><span>{p.premium ? `${jodoN}語・意味の見分け` : `${jodoN}語・完全版`}</span></button>
      </div>
      <button className="btn wide list-btn" onClick={p.onList}>単語の一覧・さがす</button>

      {!p.premium && (
        <button className="unlock" onClick={p.onPaywall}>
          <span className="unlock-title">完全版(買い切り)</span>
          <span className="unlock-sub">いまは重要度の上位{FREE_MAIN}語。完全版で{p.main.length}語すべてと例文モード、敬語・助動詞セットが開きます。広告はありません。</span>
        </button>
      )}

      <p className="credit">例文は著作権の切れた古典の本文(ウィキソース所収の翻刻)から引き、字体を新字体に改めました。意味・解説・現代語訳はこのアプリで書いたものです。</p>
    </div>
  );
}

function fmt(day: string) {
  const [, m, d] = day.split('-').map(Number);
  return `${m}月${d}日`;
}
