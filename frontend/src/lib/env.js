// frontend/src/lib/env.js
export const API = import.meta.env.VITE_API_BASE || '/api';
export const UPLOADS = import.meta.env.VITE_UPLOAD_BASE || '/static/uploads';

/**
 * Vezme vstup (např. "babicka.jpg", "static/uploads/babicka.jpg",
 * "/static/uploads/babicka.jpg", nebo plnou URL) a vrátí URL,
 * která bude fungovat v DEV (Vite proxy) i v PROD (Nginx).
 */
export function toUploadUrl(input) {
  if (!input) return '';
  let s = String(input).trim();

  // Odstranit případnou doménu/protokol
  s = s.replace(/^https?:\/\/[^/]+/i, '');

  // Odstranit počáteční lomítka
  s = s.replace(/^\/+/, '');

  // Pokud začíná "static/uploads/", tak ten prefix odřízneme (přidáme ho z UPLOADS)
  if (/^static\/uploads\//i.test(s)) {
    s = s.replace(/^static\/uploads\//i, '');
  }

  const base = (UPLOADS || '/static/uploads').replace(/\/+$/, '');
  return `${base}/${s}`;
}
