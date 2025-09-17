// src/api.js
// Jednotný klient pro API (čistý JS).
// - chycení 400 z /api/orders s hláškou z BE
// - pomocná funkce na re-fetch produktů (kvůli srovnání košíku po chybě)

import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE, // ✅ jen z env, žádný fallback na localhost
  withCredentials: true,
});

export async function getProducts() {
  const { data } = await api.get("/products/");
  // BE posílá price jako číslo (Numeric). Pro jistotu převod.
  return (data || []).map((p) => ({
    ...p,
    price: typeof p.price === "string" ? parseFloat(p.price) : Number(p.price ?? 0),
  }));
}

export async function getProduct(id) {
  const { data } = await api.get(`/products/${id}`);
  return {
    ...data,
    price: typeof data.price === "string" ? parseFloat(data.price) : Number(data.price ?? 0),
  };
}

// Nový stock-safe endpoint
export async function createOrder(payload) {
  try {
    const { data } = await api.post("/orders", payload);
    return data;
  } catch (err) {
    const res = err?.response;
    if (res && res.status === 400) {
      const msg = res.data?.error || res.data?.message || "Nedostatečný sklad.";
      throw new Error(msg);
    }
    throw new Error("Chyba sítě nebo serveru při vytváření objednávky.");
  }
}

// Jednoduchý re-fetch všech produktů a mapování podle ID
export async function getProductsByIds(ids) {
  if (!ids?.length) return {};
  const list = await getProducts();
  const map = {};
  for (const p of list) map[p.id] = p;
  return map;
}
