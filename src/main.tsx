import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';

if (import.meta.env.DEV) {
  const params = new URLSearchParams(location.search);
  // 画面写真用の見本データ(開発ビルドだけ)。書き終えてから描く
  if (params.get('demo') === '1') await (await import('./dev/demo')).installDemo(params);
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
