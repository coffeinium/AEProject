import React, { useState, useEffect, useRef, FormEvent, KeyboardEvent } from 'react';
import './searchbar.css';
import SearchIcon from '@/icons/search.svg?react';
import CloseIcon from '@/icons/close.svg?react';
import DocAddIcon from '@/icons/document-add.svg?react';
import { getSuggest } from '@/lib/api';

type Suggest = { label: string; payload: any };

type Props = {
  placeholder?: string;
  onSearch: (q: string) => void | Promise<void>;
  onCreate: (payload: any) => void;
  onSelectSuggestion?: (s: Suggest) => void;
};

const LS_KEY = 'th_suggest_history';
const HISTORY_LIMIT = 50;

export default function SearchBar({
  placeholder = 'Поиск…',
  onSearch,
  onCreate,
  onSelectSuggestion,
}: Props) {
  const [q, setQ] = useState('');
  const [suggestions, setSuggestions] = useState<Suggest[]>([]);
  const [show, setShow] = useState(false);
  const [activeIdx, setActiveIdx] = useState<number>(-1);
  const [picked, setPicked] = useState<Suggest | null>(null);
  const [history, setHistory] = useState<Suggest[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const skipSuggestRef = useRef(false);

  // history load/save
  useEffect(() => {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) setHistory(parsed);
      }
    } catch {}
  }, []);
  useEffect(() => {
    try { localStorage.setItem(LS_KEY, JSON.stringify(history.slice(0, HISTORY_LIMIT))); } catch {}
  }, [history]);

  const addToHistory = (s: Suggest) => setHistory((p) => [s, ...p].slice(0, HISTORY_LIMIT));
  const clearHistory = () => setHistory([]);

  // suggestions
  useEffect(() => {
    if (skipSuggestRef.current) { skipSuggestRef.current = false; return; }
    const lastToken = q.trim().split(/\s+/).pop() || '';
    const shouldFire = lastToken.length >= 2 || (q.endsWith(' ') && q.trim().length > 0);
    const t = window.setTimeout(async () => {
      if (!shouldFire) { setSuggestions([]); setShow(false); setActiveIdx(-1); return; }
      try {
        const list = await getSuggest(q);
        const arr = Array.isArray(list) ? list : [];
        setSuggestions(arr);
        setShow(arr.length > 0);
        setActiveIdx(arr.length ? 0 : -1);
      } catch {}
    }, 300);
    return () => clearTimeout(t);
  }, [q]);

  // click outside
  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!show) return;
      const t = e.target as Node;
      if (!document.getElementById('th-search-form')?.contains(t)) {
        setShow(false); setActiveIdx(-1);
      }
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [show]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const value = q.trim();
    if (!value) return;
    await onSearch(value);
    setShow(false);
  };

  const selectSuggestion = async (s: Suggest) => {
    setShow(false);
    setActiveIdx(-1);
    skipSuggestRef.current = true;
    setQ(s.label);
    setPicked(s);
    onSelectSuggestion?.(s);
    addToHistory(s);
    await onSearch(s.label);
  };

  const selectHistory = async (s: Suggest) => {
    setQ(s.label);
    setPicked(s);
    skipSuggestRef.current = true;
    setShow(false);
    await onSearch(s.label);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!show || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault(); const next = (activeIdx + 1) % suggestions.length; setActiveIdx(next); scrollActiveIntoView(next);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault(); const prev = (activeIdx - 1 + suggestions.length) % suggestions.length; setActiveIdx(prev); scrollActiveIntoView(prev);
    } else if (e.key === 'Enter') {
      if (activeIdx >= 0 && activeIdx < suggestions.length) { e.preventDefault(); selectSuggestion(suggestions[activeIdx]); }
    } else if (e.key === 'Escape') { setShow(false); setActiveIdx(-1); }
  };

  const scrollActiveIntoView = (idx: number) => {
    const list = listRef.current; if (!list) return;
    const item = list.querySelectorAll('li')[idx] as HTMLElement | undefined; if (!item) return;
    const { top: ct, bottom: cb } = list.getBoundingClientRect();
    const { top: it, bottom: ib } = item.getBoundingClientRect();
    if (it < ct) list.scrollTop -= (ct - it); else if (ib > cb) list.scrollTop += (ib - cb);
  };

  const clear = () => { setQ(''); setSuggestions([]); setShow(false); setActiveIdx(-1); setPicked(null); inputRef.current?.focus(); };

  const createClick = () => {
    const fromPicked = picked?.payload;
    const exact = suggestions.find((s) => s.label === q)?.payload;
    const first = suggestions[0]?.payload;
    onCreate(fromPicked ?? exact ?? first ?? {});
  };

  const keyFor = (s: Suggest, i: number) => `${(s.label ?? '').trim().replace(/\s+/g, ' ').toLowerCase()}#${i}`;

  return (
    <div className="th-search-wrapper">
      <form id="th-search-form" className="th-search" onSubmit={submit} role="search">
        <SearchIcon className="th-search__icon" aria-hidden />
        <input
          ref={inputRef}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={placeholder}
          className="th-search__input"
          aria-autocomplete="list"
          aria-expanded={show}
          aria-controls="th-suggest-list"
          onFocus={() => suggestions.length && setShow(true)}
          onKeyDown={onKeyDown}
        />

        {q && (
          <button
            type="button"
            className="th-search__clear"
            onClick={clear}
            title="Очистить"
            aria-label="Очистить"
          >
            <CloseIcon className="th-clear__icon" />
          </button>
        )}

        <button
          type="button"
          className="th-search__create"
          title="Создать документ"
          aria-label="Создать документ"
          onClick={createClick}
        >
          <DocAddIcon className="th-clear__icon" />
        </button>

        {/* ВЫПАДАШКА ПЕРЕНЕСЕНА ВНУТРЬ ФОРМЫ, ЯКОРЬ — .th-search */}
        {show && suggestions.length > 0 && (
          <ul
            ref={listRef}
            id="th-suggest-list"
            className="th-suggestions"
            role="listbox"
            aria-label="Подсказки"
          >
            {suggestions.map((s, i) => (
              <li
                key={keyFor(s, i)}
                role="option"
                aria-selected={i === activeIdx}
                className={i === activeIdx ? 'is-active' : undefined}
                onMouseDown={(e) => { e.preventDefault(); selectSuggestion(s); }}
              >
                <div className="th-suggestion__row">
                  <span className="th-suggestion__label">{s.label}</span>
                  {s.payload?.__type && (
                    <span className="th-suggestion__type">{String(s.payload.__type)}</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </form>

      {/* История — НИЖЕ формы, список всегда поверх неё по z-index */}
      {history.length > 0 && (
        <div className="th-history" aria-label="История выбора">
          <div className="th-history__header">
            <span className="th-history__title">История</span>
            <button
              type="button"
              className="th-history__reset"
              onClick={clearHistory}
              aria-label="Сбросить историю"
              title="Сбросить историю"
            >
              Сбросить
            </button>
          </div>
          <ul className="th-history__list">
            {history.map((h, i) => (
              <li
                key={keyFor(h, i)}
                className="th-history__item"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => selectHistory(h)}
                title={h.label}
              >
                {h.label}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
