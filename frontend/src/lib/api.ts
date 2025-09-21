// src/lib/api.ts

import {
  API_BASE, SEARCH_PATH,
  SUGGEST_METHOD, SUGGEST_MODE_KEY, SUGGEST_MODE_VALUE, SUGGEST_QUERY_KEY,
  ANALYZE_METHOD, ANALYZE_BODY_KEY, ANALYZE_EXTRA_JSON,
  USE_MOCK, MOCK_URL, MOCK_SUGGEST_URL
} from '@/lib/config';

export type BackendEnvelope = {
  status: 'success' | 'error';
  response: { type: string; data: any };
  ml_data: { intent: string; confidence: number | null; entities: Record<string, any> };
};

type SuggestItem = { label: string; payload: any };

const makeURL = (base: string, params: Record<string, any>) => {
  const u = new URL(base, window.location.origin);
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    u.searchParams.set(k, String(v));
  });
  return u.toString();
};

// Читает мок: массив JSON или несколько JSON-объектов, разделённых переносами
async function loadMockArray(url: string): Promise<BackendEnvelope[]> {
  const text = await fetch(url).then(r => r.text());
  try {
    const data = JSON.parse(text);
    if (Array.isArray(data)) return data as BackendEnvelope[];
    if (data && typeof data === 'object') return [data as BackendEnvelope];
  } catch { /* ignore */ }

  const matches = text.match(/{[\s\S]*?}(?=\s*{|\s*$)/g);
  if (matches) {
    const arr: BackendEnvelope[] = [];
    for (const chunk of matches) {
      try { arr.push(JSON.parse(chunk)); } catch { /* ignore bad chunk */ }
    }
    if (arr.length) return arr;
  }
  return [];
}

export async function analyzeQuery(q: string): Promise<BackendEnvelope[]> {
  if (USE_MOCK) {
    return loadMockArray(MOCK_URL);
  }

  const url = `${API_BASE}${SEARCH_PATH}`;

  if (ANALYZE_METHOD === 'GET') {
    // Добавляем query в URL
    const full = makeURL(url, { query: q, [ANALYZE_BODY_KEY]: q, ...ANALYZE_EXTRA_JSON });
    const resp = await fetch(full);
    if (!resp.ok) throw new Error(String(resp.status));
    const data = await resp.json();
    return Array.isArray(data) ? data : [data];
  }

  // Для POST тоже добавим query в URL
  const full = makeURL(url, { query: q });
  const resp = await fetch(full, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ [ANALYZE_BODY_KEY]: q, ...ANALYZE_EXTRA_JSON }),
  });
  if (!resp.ok) throw new Error(String(resp.status));
  const data = await resp.json();
  return Array.isArray(data) ? data : [data];
}

// Подсказки: при USE_MOCK читаем из MOCK_SUGGEST_URL (если задан) или собираем из MOCK_URL
export async function getSuggest(q: string): Promise<SuggestItem[]> {
  if (USE_MOCK) {
    if (MOCK_SUGGEST_URL) {
      const text = await fetch(MOCK_SUGGEST_URL).then(r => r.text());
      try {
        const data = JSON.parse(text);
        if (Array.isArray(data)) {
          return data.map((x: any) => (typeof x === 'string' ? { label: x, payload: {} } : x));
        }
        if (data && typeof data === 'object') return [data];
      } catch { /* try multi-json below */ }
      const parts = text.match(/{[\s\S]*?}(?=\s*{|\s*$)/g);
      if (parts) {
        const out: any[] = [];
        for (const chunk of parts) {
          try { out.push(JSON.parse(chunk)); } catch { /* ignore */ }
        }
        if (out.length) return out;
      }
      return [];
    }

    const items = await loadMockArray(MOCK_URL);
    // НЕ обрезаем список; добавляем тип и сырые entities в payload
    return items.map((it) => {
      const t = it?.response?.type ?? it?.ml_data?.intent ?? 'suggest';
      const ent = it?.ml_data?.entities ?? {};
      const title =
        ent.company_name || ent.name || ent.session_name || ent.contract_id || t;

      return {
        label: `${String(title)}`.slice(0, 140),
        payload: {
          __type: t,
          title: ent.session_name || ent.company_name || ent.name || '',
          customer: ent.customer_name || '',
          price: ent.contract_amount ?? ent.session_amount ?? '',
          deadline: (ent.contract_date || ent.session_completed_date || '').toString().slice(0, 10),
          rawEntities: ent,
        },
      };
    });
  }

  const url = `${API_BASE}${SEARCH_PATH}`;

  if (SUGGEST_METHOD === 'GET') {
    // Добавляем query в URL
    const full = makeURL(url, {
      query: q,
      [SUGGEST_MODE_KEY]: SUGGEST_MODE_VALUE,
      [SUGGEST_QUERY_KEY]: q
    });
    const resp = await fetch(full);
    if (!resp.ok) return [];
    const data = await resp.json().catch(() => []);
    return (Array.isArray(data) ? data : []).map((x: any) =>
      typeof x === 'string' ? { label: x, payload: {} } : x
    );
  }

  // Для POST тоже добавим query в URL
  const full = makeURL(url, { query: q });
  const resp = await fetch(full, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ [SUGGEST_MODE_KEY]: SUGGEST_MODE_VALUE, [SUGGEST_QUERY_KEY]: q }),
  });
  if (!resp.ok) return [];
  const data = await resp.json().catch(() => []);
  return (Array.isArray(data) ? data : []).map((x: any) =>
    typeof x === 'string' ? { label: x, payload: {} } : x
  );
}
