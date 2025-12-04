// utils/image.js

// Use current origin so it works behind nginx proxy (frontend on 3000, proxied to backend)
const API_BASE = window.location.origin;

/**
 * Vrátí absolutní URL obrázku pro React (aby fungovalo z 3000 → 5000).
 * - Pokud je to už URL → vrátí ji rovnou
 * - Pokud začíná / → přidá host (např. /static/uploads/x.jpg)
 * - Pokud je to jen název → přidá /static/uploads/
 */
export function absoluteUploadUrl(u) {
  if (!u) return null;
  if (/^https?:\/\//i.test(u)) return u;
  if (u.startsWith("/")) return `${API_BASE}${u}`;
  return `${API_BASE}/static/uploads/${u}`;
}
