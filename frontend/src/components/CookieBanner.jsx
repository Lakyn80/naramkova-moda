import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";          // SPA odkazy
import { getConsent, setConsent } from "../lib/consent";

// respektuj BASE_URL (Vite) pro návrat na domů
const HOME = (import.meta.env.BASE_URL || "/").replace(/\/+$/, "/");

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);
  const [showPrefs, setShowPrefs] = useState(false);
  const [analytics, setAnalytics] = useState(false);
  const [marketing, setMarketing] = useState(false);

  // 1) načtení souhlasu při startu
  useEffect(() => {
    const c = getConsent();
    if (!c) {
      setVisible(true);
    } else {
      setAnalytics(!!c.analytics);
      setMarketing(!!c.marketing);
    }
  }, []);

  // 2) zpřístupni globální otevření preferencí + event fallback
  useEffect(() => {
    const openPrefs = () => {
      const c = getConsent();
      if (c) {
        setAnalytics(!!c.analytics);
        setMarketing(!!c.marketing);
      }
      setVisible(true);
      setShowPrefs(true);
    };

    // funkce, kterou může volat footer
    window._openCookiePrefs = openPrefs;

    // kompatibilita s eventy
    const handler1 = () => openPrefs();
    const handler2 = () => openPrefs();
    window.addEventListener("cookie:open", handler1);
    window.addEventListener("open-cookie-prefs", handler2);

    return () => {
      try { delete window._openCookiePrefs; } catch {}
      window.removeEventListener("cookie:open", handler1);
      window.removeEventListener("open-cookie-prefs", handler2);
    };
  }, []);

  if (!visible) return null;

  const goHome = () => {
    try {
      if (location.pathname !== HOME) {
        window.location.assign(HOME);
      } else {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    } catch {
      window.location.href = HOME;
    }
  };

  const acceptAll = () => {
    setConsent({ analytics: true, marketing: true });
    setVisible(false);
    goHome();
  };

  const acceptNecessary = () => {
    setConsent({ analytics: false, marketing: false });
    setVisible(false);
    goHome();
  };

  const savePrefs = () => {
    setConsent({ analytics, marketing });
    setVisible(false);
    goHome();
  };

  // NOVÉ: zpět se chová stejně jako uložit (zavírá a vrací na domů)
  const backLikeSave = () => {
    // neukládáme změny, jen zavřeme a jdeme na domů
    setVisible(false);
    setShowPrefs(false);
    goHome();
  };

  return (
    <div
      data-cookie-banner-visible={visible ? "true" : "false"}
      style={{
        position: "fixed",
        left: 0, right: 0, bottom: 0,
        zIndex: 9999, // překryje i footer
      }}
      role="dialog"
      aria-live="polite"
      aria-label="Nastavení cookies"
      aria-modal="true"
    >
      <div
        className="w-full"
        style={{
          background: "rgba(17, 24, 39, 0.98)",
          color: "white",
          borderTop: "1px solid rgba(255,255,255,.08)",
          backdropFilter: "saturate(140%) blur(6px)",
          boxShadow: "0 -10px 30px rgba(0,0,0,.35)",
        }}
      >
        <div className="container mx-auto px-4 py-4" style={{ maxWidth: 960 }}>
          {!showPrefs ? (
            <div className="flex flex-wrap items-start gap-4">
              <div className="flex-1 min-w-[260px]">
                <strong className="block text-base">Cookies &amp; soukromí</strong>
                <p className="mt-1 opacity-90 text-sm leading-6">
                  Používáme nezbytné cookies pro provoz webu a volitelné (analytické/marketingové)
                  jen se souhlasem. Více v{" "}
                  <Link to="/privacy" className="underline text-pink-300 hover:text-pink-200">
                    Zásadách ochrany osobních údajů
                  </Link>{" "}
                  a{" "}
                  <Link to="/cookies" className="underline text-pink-300 hover:text-pink-200">
                    Zásadách cookies
                  </Link>.
                </p>
              </div>

              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={acceptAll}
                  className="px-4 py-2 rounded-md bg-pink-600 hover:bg-pink-700 text-white text-sm font-semibold"
                >
                  Přijmout vše
                </button>
                <button
                  onClick={acceptNecessary}
                  className="px-4 py-2 rounded-md bg-gray-200 hover:bg-gray-300 text-gray-900 text-sm font-semibold"
                >
                  Pouze nezbytné
                </button>
                <button
                  onClick={() => setShowPrefs(true)}
                  className="px-4 py-2 rounded-md border border-gray-400/50 hover:border-gray-300 text-sm"
                >
                  Nastavení
                </button>
              </div>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
              <div>
                <h2 className="text-base font-semibold mb-2">Nastavení cookies</h2>
                <div className="space-y-2 text-sm">
                  <label className="flex items-center gap-2 opacity-80">
                    <input type="checkbox" checked readOnly />
                    Nezbytné (vždy aktivní)
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={analytics}
                      onChange={(e) => setAnalytics(e.target.checked)}
                    />
                    Analytické
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={marketing}
                      onChange={(e) => setMarketing(e.target.checked)}
                    />
                    Marketingové
                  </label>
                </div>
              </div>

              <div className="flex gap-2 justify-end mt-2">
                <button
                  type="button"
                  onClick={backLikeSave}  // ← tady změna
                  className="px-4 py-2 rounded-md border border-gray-400/50 hover:border-gray-300 text-sm"
                >
                  Zpět
                </button>
                <button
                  type="button"
                  onClick={savePrefs}
                  className="px-4 py-2 rounded-md bg-pink-600 hover:bg-pink-700 text-white text-sm font-semibold"
                >
                  Uložit volby
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
