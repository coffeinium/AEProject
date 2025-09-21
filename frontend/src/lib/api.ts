// src/lib/api.ts
import { API_BASE, SEARCH_PATH, HISTORY_PATH, HISTORY_SEARCH_PATH, SUGGEST_LIMIT } from '@/lib/config';

export type MLData = {
  intent: string;
  confidence: number | null;
  entities: Record<string, any>;
  details?: any | null;
};

export type ResponseData<T = any> = {
  type: string;
  data: T | null;
};

export type SearchResponse<T = any> = {
  status: string;
  response: ResponseData<T>;
  ml_data?: MLData;
};

export type HistoryRecord = {
  id: number;
  timestamp: string;
  text: string;
  intent: string | null;
  confidence: number | null;
  entities: Record<string, any>;
  created_at: string;
};

const makeURL = (path: string, params?: Record<string, any>) => {
  const u = new URL(path, API_BASE);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v === undefined || v === null) return;
      u.searchParams.set(k, String(v));
    });
  }
  return u.toString();
};

// Поиск
export async function search(query: string, detailed = true, writeInHistory = true) {
  const url = makeURL(SEARCH_PATH, { query, detailed, write_in_history: writeInHistory });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return (await res.json()) as SearchResponse;
}

// История (нижний блок)
export async function fetchHistory(limit = 100) {
  const url = makeURL(HISTORY_PATH, { limit });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`History failed: ${res.status}`);
  const json = (await res.json()) as SearchResponse<{
    records: HistoryRecord[];
    total_count: number;
    filters: any;
  }>;
  return Array.isArray(json?.response?.data?.records) ? json.response.data.records : [];
}

// Подсказки ДЛЯ ВЫПАДАШКИ — из ИСТОРИИ
export async function searchHistorySuggestions(q: string, limit = SUGGEST_LIMIT) {
  const url = makeURL(HISTORY_SEARCH_PATH, { q, limit });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`History search failed: ${res.status}`);
  const json = (await res.json()) as SearchResponse<{
    query: string;
    records: HistoryRecord[];
    total_count: number;
    limit: number;
  }>;
  const recs = json?.response?.data?.records ?? [];
  // Возвращаем массив строк (text) — для выпадашки
  return recs.map(r => r.text).filter(Boolean);
}
