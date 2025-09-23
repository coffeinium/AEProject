// src/components/SearchBar/SearchBar.tsx
import React, { useEffect, useMemo, useRef, useState } from 'react';
import './searchbar.css';
import { searchHistorySuggestions } from '@/lib/api';
import { SUGGEST_DEBOUNCE_MS, SUGGEST_MIN_TOKEN } from '@/lib/config';

type Props = {
  placeholder?: string;
  onSearch: (q: string) => void | Promise<void>;
  onCreate: () => void;
  highlighted?: boolean;
};

function lastToken(s: string) {
  const trimmed = s.replace(/\s+$/, '');
  const parts = trimmed.split(/\s+/);
  return parts[parts.length - 1] ?? '';
}

export default function SearchBar({ placeholder = 'Поиск…', onSearch, onCreate, highlighted = false }: Props) {
  const [q, setQ] = useState('');
  const [suggests, setSuggests] = useState<string[]>([]);
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState<number>(-1);
  const boxRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<number | null>(null);

  const shouldQueryHistory = useMemo(() => {
    if (!q) return false;
    const spaceEnded = /\s$/.test(q);
    const tok = lastToken(q);
    return spaceEnded || tok.length >= SUGGEST_MIN_TOKEN;
  }, [q]);

  useEffect(() => {
    if (!shouldQueryHistory) {
      setSuggests([]);
      setOpen(false);
      return;
    }
    if (timerRef.current) window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(async () => {
      try {
        const items = await searchHistorySuggestions(q);
        setSuggests(items);
        setOpen(items.length > 0);
        setActiveIdx(-1);
      } catch {
        setSuggests([]);
        setOpen(false);
      }
    }, SUGGEST_DEBOUNCE_MS);
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, [q, shouldQueryHistory]);

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!boxRef.current) return;
      if (!boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  const submit = (value?: string) => {
    const text = (value ?? q).trim();
    if (!text) return;
    setOpen(false);
    onSearch(text);
  };

  const onKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
    if (!open || suggests.length === 0) {
      if (e.key === 'Enter') submit();
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIdx((p) => (p + 1) % suggests.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIdx((p) => (p - 1 + suggests.length) % suggests.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const pick = activeIdx >= 0 ? suggests[activeIdx] : q;
      submit(pick);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <div className="searchbar" ref={boxRef}>
      <div className="searchbar__row">
        <button
          type="button"
          className="searchbar__create"
          aria-label="Создать документ"
          title="Создать документ"
          onClick={onCreate}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M11 11V5h2v6h6v2h-6v6h-2v-6H5v-2z" />
          </svg>
        </button>

        <input
          className={`searchbar__input ${highlighted ? 'searchbar__input--highlighted' : ''}`}
          placeholder={placeholder}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => setOpen(suggests.length > 0)}
          onKeyDown={onKeyDown}
        />

        {/* заменено: лупа → плюс */}
        <button
          type="button"
          className="searchbar__go"
          onClick={() => submit()}
          title="Создать документ"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M11 11V5h2v6h6v2h-6v6h-2v-6H5v-2z" />
          </svg>
        </button>
      </div>

      {open && suggests.length > 0 && (
        <div className="searchbar__dropdown" role="listbox">
          {suggests.map((s, i) => (
            <div
              key={`${s}-${i}`}
              role="option"
              aria-selected={i === activeIdx}
              className={`searchbar__item ${i === activeIdx ? 'is-active' : ''}`}
              onMouseDown={(e) => {
                e.preventDefault();
                submit(s);
              }}
            >
              {s}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
