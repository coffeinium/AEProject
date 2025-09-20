const API_BASE = import.meta.env.VITE_API_BASE || '';
export async function search(q: string) {
  const url = `${API_BASE}/api/search?q=${encodeURIComponent(q)}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}
