import React from 'react';
import SearchBar from '@/components/SearchBar';
import './app.css';

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">TenderHack</div>
      </header>
      <main className="content">
        <h1 className="title">Поиск</h1>
        <SearchBar
          placeholder="Найти тендер, команду, участника…"
          onSearch={async (q) => {
            const resp = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
            if (!resp.ok) {
              alert('Ошибка: ' + resp.status);
              return;
            }
            const data = await resp.json().catch(() => ({}));
            alert('Результаты:\n' + JSON.stringify(data, null, 2));
          }}
        />
      </main>
    </div>
  );
}
