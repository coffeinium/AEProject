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
  onCreate: (payload: any) => void;              // открываем модалку ТОЛЬКО по этой кнопке
  onSelectSuggestion?: (s: Suggest) => void;     // опционально сообщаем наверх, что выбрали подсказку
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
  const [activeIdx, setActiveIdx] = useState<number>(-1); // для клавиатуры
  const [picked, setPicked] = useState<Suggest | null>(null); // последняя выбранная подсказка

  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // === загрузка подсказок: пробел ИЛИ последний токен >= 2 символов + дебаунс 300мс ===
  useEffect(() => {
    const controller = new AbortController();

    const lastToken = q.trim().split(/\s+/).pop() || '';
    const shouldFire = lastToken.length >= 2 || (q.endsWith(' ') && q.trim().length > 0);

    const t = setTimeout(async () => {
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
        // ignore
      }
    }, 300);

    return () => {
      controller.abort();
      clearTimeout(t);
    };
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
    setShow(false); // список скрываем, модалку НЕ открываем
  };

  const selectSuggestion = (s: Suggest) => {
    setQ(s.label);
    setPicked(s);                 // запоминаем выбранную подсказку
    onSelectSuggestion?.(s);      // сообщаем наверх (если нужно)
    // НИКАКОЙ модалки тут — только поиск по клику можно запустить отдельно:
    // по UX оставим просто выбор текста и скрытие списка
    setShow(false);
  };

  // клавиатура в инпуте
  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!show || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIdx((i) => (i + 1) % suggestions.length);
      scrollActiveIntoView((activeIdx + 1) % suggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIdx((i) => (i - 1 + suggestions.length) % suggestions.length);
      scrollActiveIntoView((activeIdx - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === 'Enter') {
      // Enter на открытом списке — выбираем подсказку (не открываем модалку)
      if (activeIdx >= 0 && activeIdx < suggestions.length) {
        e.preventDefault();
        selectSuggestion(suggestions[activeIdx]);
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
    // создаём документ ТОЛЬКО по клику на кнопку "создать"
    // приоритет: выбранная подсказка -> точное совпадение текста -> первая подсказка -> пустой объект
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
              // onMouseDown — чтобы не терять фокус инпута до select
              onMouseDown={(e) => {
                e.preventDefault();
                selectSuggestion(s);
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
