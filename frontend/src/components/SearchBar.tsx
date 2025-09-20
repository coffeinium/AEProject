import React, { useState, useEffect, FormEvent, useRef } from 'react';
import './searchbar.css';
import SearchIcon from '@/icons/search.svg?react';
import CloseIcon from '@/icons/close.svg?react';

type Props = {
  placeholder?: string;
  onSearch: (q: string) => void | Promise<void>;
};

export default function SearchBar({ placeholder = 'Поиск…', onSearch }: Props) {
  const [q, setQ] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [show, setShow] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchSuggestions() {
      if (!q.trim()) {
        setSuggestions([]);
        return;
      }
      try {
        const resp = await fetch(`/api/search?q=${encodeURIComponent(q)}`, { signal: controller.signal });
        if (resp.ok) {
          const data = await resp.json();
          const items = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : []);
          setSuggestions(items);
          setShow(items.length > 0);
        } else {
          setSuggestions([]);
        }
      } catch {
        setSuggestions([]);
      }
    }

    const t = setTimeout(fetchSuggestions, 300);
    return () => { controller.abort(); clearTimeout(t); };
  }, [q]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const value = q.trim();
    if (!value) return;
    await onSearch(value);
    setShow(false);
  };

  const clickSuggestion = (s: string) => {
    setQ(s);
    onSearch(s);
    setShow(false);
  };

  const clear = () => {
    setQ('');
    setSuggestions([]);
    setShow(false);
    inputRef.current?.focus();
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
          autoComplete="off"
          onFocus={() => { if (suggestions.length) setShow(true); }}
          onBlur={() => setTimeout(() => setShow(false), 120)}
        />
        {q && (
          <button type="button" className="th-search__clear" onMouseDown={(e) => e.preventDefault()} onClick={clear} aria-label="Очистить">
            <CloseIcon className="th-clear__icon" />
          </button>
        )}
        <button type="submit" className="th-search__btn" disabled={!q.trim()}>
          Найти
        </button>
      </form>

      {show && suggestions.length > 0 && (
        <ul className="th-suggestions">
          {suggestions.map((s, i) => (
            <li key={i} onMouseDown={() => clickSuggestion(s)}>{s}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
