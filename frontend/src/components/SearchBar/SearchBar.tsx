// src/components/SearchBar/SearchBar.tsx
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

  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Флаг, чтобы не перезапускать подсказки сразу после выбора из списка
  const skipSuggestRef = useRef(false);

  // === загрузка подсказок: пробел ИЛИ последний токен >= 2 символов + дебаунс 300мс ===
  useEffect(() => {
    // если мы только что выбрали подсказку — пропускаем обновление
    if (skipSuggestRef.current) {
      skipSuggestRef.current = false;
      return;
    }

    const lastToken = q.trim().split(/\s+/).pop() || '';
    const shouldFire = lastToken.length >= 2 || (q.endsWith(' ') && q.trim().length > 0);

    const t = window.setTimeout(async () => {
      if (!shouldFire) {
        setSuggestions([]);
        setShow(false);
        setActiveIdx(-1);
        return;
      }
      try {
        const norm = await getSuggest(q);
        setSuggestions(norm);
        setShow(norm.length > 0);
        setActiveIdx(norm.length ? 0 : -1);
      } catch {
        /* ignore */
      }
    }, 300);

    return () => clearTimeout(t);
  }, [q]);

  // закрытие списка по клику вне
  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!show) return;
      const target = e.target as Node;
      if (
        inputRef.current &&
        !inputRef.current.contains(target) &&
        listRef.current &&
        !listRef.current.contains(target)
      ) {
        setShow(false);
        setActiveIdx(-1);
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

  // внутри SearchBar.tsx
  const selectSuggestion = async (s: Suggest) => {
    setShow(false);
    setActiveIdx(-1);
    skipSuggestRef.current = true;

    setQ(s.label);
    setPicked(s);
    onSelectSuggestion?.(s);

    // ВАЖНО: подтягиваем актуальные envelopes под выбранный пункт
    await onSearch(s.label);
  };

  // клавиатура в инпуте
  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!show || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const next = (activeIdx + 1) % suggestions.length;
      setActiveIdx(next);
      scrollActiveIntoView(next);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prev = (activeIdx - 1 + suggestions.length) % suggestions.length;
      setActiveIdx(prev);
      scrollActiveIntoView(prev);
    } else if (e.key === 'Enter') {
      if (activeIdx >= 0 && activeIdx < suggestions.length) {
        e.preventDefault();
        selectSuggestion(suggestions[activeIdx]); // выпад. закроется
      }
    } else if (e.key === 'Escape') {
      setShow(false);
      setActiveIdx(-1);
    }
  };

  const scrollActiveIntoView = (idx: number) => {
    const list = listRef.current;
    if (!list) return;
    const item = list.querySelectorAll('li')[idx] as HTMLElement | undefined;
    if (!item) return;
    const { top: ct, bottom: cb } = list.getBoundingClientRect();
    const { top: it, bottom: ib } = item.getBoundingClientRect();
    if (it < ct) list.scrollTop -= (ct - it);
    else if (ib > cb) list.scrollTop += (ib - cb);
  };

  const clear = () => {
    setQ('');
    setSuggestions([]);
    setShow(false);
    setActiveIdx(-1);
    setPicked(null);
    inputRef.current?.focus();
  };

  const createClick = () => {
    const fromPicked = picked?.payload;
    const exact = suggestions.find((s) => s.label === q)?.payload;
    const first = suggestions[0]?.payload;
    onCreate(fromPicked ?? exact ?? first ?? {});
  };

  return (
    <div className="th-search-wrapper">
      <form className="th-search" onSubmit={submit} role="search">
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
      </form>

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
              key={`${s.label}-${i}`}
              role="option"
              aria-selected={i === activeIdx}
              className={i === activeIdx ? 'is-active' : undefined}
              onMouseDown={(e) => {
                e.preventDefault();      // не теряем фокус поля
                selectSuggestion(s);     // список скрываем сразу
              }}
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
    </div>
  );
}
