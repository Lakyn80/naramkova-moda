// frontend/src/lib/consent.js
const KEY = "COOKIE_CONSENT_V1";

function writeCookie(valueObj, months = 6) {
  try {
    const v = encodeURIComponent(JSON.stringify(valueObj));
    const d = new Date();
    d.setMonth(d.getMonth() + months);
    document.cookie =
      `cookie_consent=${v}; Expires=${d.toUTCString()}; Path=/; SameSite=Lax; Secure`;
  } catch {}
}

export function getConsent() {
  try {
    const ls = localStorage.getItem(KEY);
    if (ls) return JSON.parse(ls);
  } catch {}
  // fallback z cookie
  try {
    const m = document.cookie.match(/(?:^|;\s*)cookie_consent=([^;]+)/);
    if (m) return JSON.parse(decodeURIComponent(m[1]));
  } catch {}
  return null;
}

export function setConsent(consent) {
  const payload = {
    necessary: true,
    analytics: !!consent.analytics,
    marketing: !!consent.marketing,
    timestamp: new Date().toISOString(),
    version: 1,
  };
  localStorage.setItem(KEY, JSON.stringify(payload));
  writeCookie(payload);
  window.dispatchEvent(new CustomEvent("cookie-consent", { detail: payload }));
  return payload;
}

export function hasConsent(cat) {
  const c = getConsent();
  if (!c) return false;
  if (cat === "necessary") return true;
  return !!c[cat];
}

export function onConsentChange(cb) {
  const handler = (e) => cb(e.detail);
  window.addEventListener("cookie-consent", handler);
  return () => window.removeEventListener("cookie-consent", handler);
}
