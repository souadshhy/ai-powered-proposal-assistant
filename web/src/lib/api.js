const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    const detail = data?.detail || data || `HTTP ${res.status}`;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return data;
}

export const api = {
  health: () => request('/health'),
  products: (params = {}) => request(`/products?${new URLSearchParams(clean(params))}`),
  createProduct: (payload) => request('/products', { method: 'POST', body: JSON.stringify(payload) }),
  knowledge: (params = {}) => request(`/knowledge?${new URLSearchParams(clean(params))}`),
  createKnowledge: (payload) => request('/knowledge', { method: 'POST', body: JSON.stringify(payload) }),
  quotes: () => request('/quotes'),
  quote: (id) => request(`/quotes/${encodeURIComponent(id)}`),
  updateQuoteItem: (quoteId, payload) => request(`/quotes/${encodeURIComponent(quoteId)}/items`, { method: 'PATCH', body: JSON.stringify(payload) }),
  toolLogs: () => request('/admin/tool-logs'),
  sessions: () => request('/admin/chat-sessions'),
};

function clean(obj) {
  return Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== undefined && v !== null && v !== ''));
}

export function formatTry(value) {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(Number(value || 0));
}
