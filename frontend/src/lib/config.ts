const env = (k: string, def?: string) => import.meta.env[k as any] ?? def;

export const API_BASE = String(env('VITE_API_BASE', 'http://localhost:8000'));

export const SEARCH_PATH = String(env('VITE_SEARCH_PATH', '/user/search'));
export const HISTORY_PATH = String(env('VITE_HISTORY_PATH', '/user/history'));
export const HISTORY_SEARCH_PATH = String(env('VITE_HISTORY_SEARCH_PATH', '/user/history/search'));

export const FEEDBACK_PATH = String(env('VITE_FEEDBACK_PATH', '/user/feedback'));

export const HISTORY_LIMIT = Number(env('VITE_HISTORY_LIMIT', '100'));
export const SUGGEST_MIN_TOKEN = Number(env('VITE_SUGGEST_MIN_TOKEN', '2'));
export const SUGGEST_DEBOUNCE_MS = Number(env('VITE_SUGGEST_DEBOUNCE_MS', '250'));
export const SUGGEST_LIMIT = Number(env('VITE_SUGGEST_LIMIT', '50'));
