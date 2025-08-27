// frontend/src/lib/api.js
// Jednoduchý wrapper pro volání backendu přes /api.

export const API_BASE = "/api";

export async function apiGet(path, options = {}) {
  const isAbsolute = /^https?:\/\//i.test(path);
  const url = isAbsolute
    ? path
    : `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;

  const res = await fetch(url, {
    credentials: "include",
    ...options,
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`GET ${url} -> ${res.status} ${res.statusText} ${txt}`);
  }
  return res.json();
}
