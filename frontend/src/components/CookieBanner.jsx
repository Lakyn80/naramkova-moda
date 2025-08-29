// frontend/src/components/CookieBanner.jsx
import React, { useEffect, useState } from "react";
import { getConsent, setConsent } from "../lib/consent";

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);
  const [openPrefs, setOpenPrefs] = useState(false);
  const [analytics, setAnalytics] = useState(false);
  const [marketing, setMarketing] = useState(false);

  useEffect(() => {
    const c = getConsent();
    if (!c) setVisible(true);
  }, []);

  if (!visible) return null;

  const acceptAll = () => {
    setConsent({ analytics: true, marketing: true });
    setVisible(false);
  };
  const acceptNecessary = () => {
    setConsent({ analytics: false, marketing: false });
    setVisible(false);
  };
  const savePrefs = () => {
    setConsent({ analytics, marketing });
    setVisible(false);
  };

  return (
    <div
      style={{
        position: "fixed", left: 0, right: 0, bottom: 0, zIndex: 1000,
        background: "rgba(17, 24, 39, 0.95)", color: "white",
        padding: "16px"
      }}
    >
      <div className="container mx-auto" style={{maxWidth: 960}}>
        <div style={{display: "flex", gap: 16, alignItems: "start", flexWrap: "wrap"}}>
          <div style={{flex: 1, minWidth: 260}}>
            <strong>Cookies & soukromí</strong>
            <p style={{margin: "6px 0 0 0", opacity: .9}}>
              Používáme nezbytné cookies pro provoz webu a volitelné (analytické/marketingové)
              jen s tvým souhlasem. Více v <a href="/privacy" style={{color:"#f9a8d4"}}>Zásadách ochrany osobních údajů</a> a
              <a href="/cookies" style={{color:"#f9a8d4", marginLeft: 6}}>Zásadách cookies</a>.
            </p>
          </div>

          {!openPrefs && (
            <div style={{display:"flex", gap:8, flexWrap:"wrap"}}>
              <button onClick={acceptAll} className="btn btn-sm btn-primary">
                Přijmout vše
              </button>
              <button onClick={acceptNecessary} className="btn btn-sm btn-light">
                Pouze nezbytné
              </button>
              <button onClick={() => setOpenPrefs(true)} className="btn btn-sm btn-outline-light">
                Nastavení
              </button>
            </div>
          )}

          {openPrefs && (
            <div style={{background:"#111827", border:"1px solid #374151", borderRadius:8, padding:12}}>
              <div style={{marginBottom:8}}>
                <label style={{display:"flex", gap:8, alignItems:"center"}}>
                  <input type="checkbox" checked disabled />
                  <span>Nezbytné (vždy aktivní)</span>
                </label>
              </div>
              <div style={{marginBottom:8}}>
                <label style={{display:"flex", gap:8, alignItems:"center"}}>
                  <input type="checkbox" checked={analytics} onChange={e=>setAnalytics(e.target.checked)} />
                  <span>Analytické</span>
                </label>
              </div>
              <div style={{marginBottom:12}}>
                <label style={{display:"flex", gap:8, alignItems:"center"}}>
                  <input type="checkbox" checked={marketing} onChange={e=>setMarketing(e.target.checked)} />
                  <span>Marketingové</span>
                </label>
              </div>

              <div style={{display:"flex", gap:8, justifyContent:"flex-end"}}>
                <button onClick={() => setOpenPrefs(false)} className="btn btn-sm btn-outline-light">Zpět</button>
                <button onClick={savePrefs} className="btn btn-sm btn-primary">Uložit volby</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
