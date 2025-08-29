import { Link } from "react-router-dom";
import qrCode from "../assets/qr_code_fb.jpg";

const IconMail = ({ className = "h-4 w-4" }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
       strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
       className={className}>
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <path d="M3 7l9 6 9-6" />
  </svg>
);

const IconPhone = ({ className = "h-4 w-4" }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
       strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
       className={className}>
    <path d="M22 16.92v2a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07
             19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 3.18
             2 2 0 0 1 4.11 1h2a2 2 0 0 1 2 1.72c.12.86.32 1.7.6 2.5
             a2 2 0 0 1-.45 2.11L7.1 8.9a16 16 0 0 0 6 6l1.57-1.17
             a2 2 0 0 1 2.11-.45c.8.28 1.64.48 2.5.6A2 2 0 0 1 22 16.92z"/>
  </svg>
);

export default function Footer() {
  const year = new Date().getFullYear();

  const openCookiesPrefs = () => {
    try {
      if (typeof window !== "undefined") {
        if (typeof window._openCookiePrefs === "function") {
          window._openCookiePrefs();                 // přímé volání banneru
          return;
        }
        window.dispatchEvent(new Event("cookie:open")); // event fallback
        return;
      }
    } catch {}
    try { localStorage.removeItem("cookie_consent"); } catch {}
    window.location.reload();
  };

  return (
    <footer className="bg-black text-white px-4 py-3 text-center">
      <div className="max-w-6xl mx-auto">
        {/* horní řádek */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm">
          {/* Kontakt (kompaktní) */}
          <div className="space-y-1 md:text-left text-center">
            <p className="flex items-center gap-2 justify-center md:justify-start">
              <IconMail className="h-4 w-4 text-pink-400" />
              <a
                href="mailto:naramkovamoda@email.cz"
                className="font-medium text-pink-300 hover:text-pink-200"
              >
                naramkovamoda@email.cz
              </a>
            </p>
            <p className="flex items-center gap-2 justify-center md:justify-start">
              <IconPhone className="h-4 w-4 text-pink-400" />
              <a href="tel:+420776479747" className="font-medium text-pink-300 hover:text-pink-200">
                +420 776 47 97 47
              </a>
            </p>
          </div>

          {/* Slogan */}
          <div className="font-semibold text-pink-300 tracking-wide">
            NÁRAMKOVÁ MÓDA – Ozdobte se jedinečností
          </div>

          {/* QR menší */}
          <div className="text-center">
            <p className="text-gray-300 text-xs mb-1">Sledujte nás na Facebooku</p>
            <a
              href="https://www.facebook.com/groups/1051242036130223/?_rdr"
              target="_blank"
              rel="noopener noreferrer"
            >
              <img
                src={qrCode}
                alt="QR kód Facebook"
                className="h-16 w-16 mx-auto rounded shadow-md hover:scale-105 transition-transform"
              />
            </a>
          </div>
        </div>

        {/* spodní proužek s odkazy */}
        <div className="mt-3 pt-3 border-t border-white/10 text-xs text-gray-300 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="opacity-80">© {year} Náramková Móda</span>
          <nav className="flex items-center gap-4">
            {/* v rámci SPA použij Link, ne <a> */}
            <Link to="/privacy" className="hover:text-pink-200">Zásady ochrany osobních údajů</Link>
            <Link to="/cookies" className="hover:text-pink-200">Zásady cookies</Link>
            <button
              type="button"
              onClick={openCookiesPrefs}
              className="hover:text-pink-200 underline decoration-dotted"
              title="Upravit nastavení cookies"
            >
              Nastavení cookies
            </button>
          </nav>
        </div>
      </div>
    </footer>
  );
}
