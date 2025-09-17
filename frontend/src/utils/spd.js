// SPD 1.0 payload for CZK QR payments: https://qr-platba.cz
export function buildSpdPayload({ iban, amount, vs, msg }) {
  if (!iban) throw new Error("Chybí IBAN.");
  const normIban = iban.replace(/\s+/g, "").toUpperCase();

  const parts = ["SPD*1.0", `ACC:${normIban}`, `AM:${Number(amount).toFixed(2)}`, "CC:CZK"];
  if (vs) parts.push(`X-VS:${String(vs).trim()}`);
  if (msg) {
    const safe = (msg + "").replace(/[^\x20-\x7E]/g, ""); // ASCII only
    parts.push(`MSG:${safe.slice(0, 60)}`);
  }
  return parts.join("*");
}
