// src/components/History/History.tsx
import React from 'react';
import './history.css';
import type { HistoryRecord } from '@/lib/api';

type Props = {
  items: HistoryRecord[];
  // Возвращаем полный record, чтобы можно было взять entities для предзаполнения
  onPick: (text: string, record: HistoryRecord) => void;
};

export default function History({ items, onPick }: Props) {
  if (!items || items.length === 0) return null;
  return (
    <div className="history">
      <div className="history__title">История</div>
      <div className="history__list">
        {items.map((r) => (
          <button
            key={r.id}
            className="history__item"
            title={new Date(r.timestamp || r.created_at).toLocaleString()}
            onClick={() => onPick(r.text, r)}
          >
            <div className="history__text">{r.text}</div>
            <div className="history__meta">
              {r.intent ? <span className="history__tag">{r.intent}</span> : null}
              {typeof r.confidence === 'number' ? (
                <span className="history__conf">{(r.confidence * 100).toFixed(1)}%</span>
              ) : null}
              <span className="history__time">
                {new Date(r.timestamp || r.created_at).toLocaleString()}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
