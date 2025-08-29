// frontend/src/lib/loaders.js
const LS_KEY = "cookieConsent"; // "all" | "essential"

export function setupOptionalScripts() {
  const load = () => {
    const consent = localStorage.getItem(LS_KEY);
    if (consent === "all") {
      // Sem případně vlož skripty, které chceš pouštět až po souhlasu
      // Příklad (zatím zakomentováno):
      // if (!window.__gaLoaded) {
      //   const s = document.createElement("script");
      //   s.async = true;
      //   s.src = "https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX";
      //   document.head.appendChild(s);
      //   window.dataLayer = window.dataLayer || [];
      //   function gtag(){dataLayer.push(arguments);}
      //   window.gtag = gtag;
      //   gtag("js", new Date());
      //   gtag("config", "G-XXXXXXX");
      //   window.__gaLoaded = true;
      // }
    }
  };

  try { load(); } catch {}
  window.addEventListener("cookie-consent-change", () => {
    try { load(); } catch {}
  });
}
