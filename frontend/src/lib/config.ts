export const API_BASE = import.meta.env.VITE_API_BASE ?? '';
export const SEARCH_PATH = import.meta.env.VITE_SEARCH_PATH ?? '/search';

export const SUGGEST_METHOD = (import.meta.env.VITE_SUGGEST_METHOD ?? 'GET').toUpperCase(); // GET|POST
export const SUGGEST_MODE_KEY = import.meta.env.VITE_SUGGEST_MODE_KEY ?? 'mode';
export const SUGGEST_MODE_VALUE = import.meta.env.VITE_SUGGEST_MODE_VALUE ?? 'suggest';
export const SUGGEST_QUERY_KEY = import.meta.env.VITE_SUGGEST_QUERY_KEY ?? 'q';

export const ANALYZE_METHOD = (import.meta.env.VITE_ANALYZE_METHOD ?? 'POST').toUpperCase(); // GET|POST
export const ANALYZE_BODY_KEY = import.meta.env.VITE_ANALYZE_BODY_KEY ?? 'text';
export const ANALYZE_EXTRA_JSON = (() => {
  try { return JSON.parse(import.meta.env.VITE_ANALYZE_EXTRA_JSON ?? '{}'); } catch { return {}; }
})();

export const USE_MOCK = (import.meta.env.VITE_USE_MOCK ?? '0') === '1';
export const MOCK_URL = import.meta.env.VITE_MOCK_URL ?? '/mocks/ml_responses.json';
export const MOCK_SUGGEST_URL = import.meta.env.VITE_MOCK_SUGGEST_URL ?? ''; // опционально
