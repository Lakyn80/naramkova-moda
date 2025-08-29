// frontend/src/lib/normalize.js
import { toUploadUrl } from '@/lib/env';

export function normalizeProduct(p) {
  if (!p) return p;
  return {
    ...p,
    image: toUploadUrl(p.image),
    // pokud máš víc obrázků v poli:
    images: Array.isArray(p.images) ? p.images.map(toUploadUrl) : p.images,
  };
}

export function normalizeProducts(list) {
  return Array.isArray(list) ? list.map(normalizeProduct) : list;
}
