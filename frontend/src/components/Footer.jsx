// src/components/Footer.jsx
import React, { useEffect, useRef, useState } from "react";
import qrCode from "../assets/qr_code_fb.jpg";
import { Mail, Phone, Cookie, Shield, X } from "lucide-react";

export default function Footer() {
  const PHONE_DISPLAY = "+420 776 47 97 47";
  const PHONE_TEL = "+420776479747";
  const EMAIL = "naramkovamoda@email.cz";

  const [consent, setConsent] = useState({ analytics: false, marketing: false });
  const [openCookies, setOpenCookies] = useState(false);
  const [openGdpr, setOpenGdpr] = useState(false);
  const [showCookiesText, setShowCookiesText] = useState(false);
  const [showGdprText, setShowGdprText] = useState(false);

  const cookiesRef = useRef(null);
  const gdprRef = useRef(null);

  // Zavření při kliknutí mimo bublinu
  useEffect(() => {
    const onDocClick = (e) => {
      if (openCookies && cookiesRef.current && !cookiesRef.current.contains(e.target)) {
        setOpenCookies(false);
      }
      if (openGdpr && gdprRef.current && !gdprRef.current.contains(e.target)) {
        setOpenGdpr(false);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("touchstart", onDocClick, { passive: true });
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("touchstart", onDocClick);
    };
  }, [openCookies, openGdpr]);

  return (
    <>
      <footer className="bg-black text-white py-[7px] px-4 text-center">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3 md:gap-5 text-[11px] sm:text-sm">
          {/* Kontakt (klikací) */}
          <div className="space-y-0.5 text-left">
            <p className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-pink-400" aria-hidden="true" />
              <a href={`mailto:${EMAIL}`} className="font-semibold text-pink-500 hover:text-pink-300">
                {EMAIL}
              </a>
            </p>
            <p className="flex items-center gap-2">
              <Phone className="w-4 h-4 text-pink-400" aria-hidden="true" />
              <a href={`tel:${PHONE_TEL}`} className="font-semibold text-pink-500 hover:text-pink-300">
                {PHONE_DISPLAY}
              </a>
            </p>
          </div>

          {/* Slogan */}
          <div className="font-semibold text-pink-300 tracking-wide text-center leading-tight">
            NÁRAMKOVÁ MÓDA – Ozdobte se jedinečností
          </div>

          {/* QR */}
          <div className="text-center">
            <p className="text-gray-300 mb-1">Sledujte nás na Facebooku:</p>
            <a
              href="https://www.facebook.com/groups/1051242036130223/?_rdr"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block"
            >
              <img
                src={qrCode}
                alt="QR kód Facebook"
                className="h-14 w-14 sm:h-16 sm:w-16 mx-auto rounded shadow-md hover:scale-105 transition-transform duration-300"
              />
            </a>
          </div>
        </div>

        {/* Odkazy + bubliny (toggle klikem) */}
        <div className="max-w-6xl mx-auto mt-3 flex flex-wrap items-center justify-center gap-5 text-[11px] sm:text-xs">
          {/* Cookies */}
          <div className="relative" ref={cookiesRef}>
            <button
              type="button"
              className="flex items-center gap-1 underline underline-offset-2 decoration-pink-500/60 hover:text-pink-300"
              aria-expanded={openCookies}
              aria-controls="cookies-popover"
              onClick={() => setOpenCookies((v) => !v)}
            >
              <Cookie className="w-4 h-4 text-pink-400" />
              Zásady cookies
            </button>

            {openCookies && (
              <div
                id="cookies-popover"
                className="absolute left-1/2 -translate-x-1/2 bottom-[120%] z-50 w-[19rem] rounded-lg bg-gray-900 text-gray-100 text-xs shadow-2xl p-4"
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  type="button"
                  aria-label="Zavřít"
                  className="absolute top-2 right-2 p-1 rounded hover:bg-white/10"
                  onClick={() => setOpenCookies(false)}
                >
                  <X className="w-4 h-4 text-gray-300" />
                </button>

                {!showCookiesText ? (
                  <>
                    <p className="mb-2">🍪 Vyberte, s čím souhlasíte:</p>
                    <label className="flex items-center gap-2 mb-1">
                      <input
                        type="checkbox"
                        checked={consent.analytics}
                        onChange={(e) => setConsent({ ...consent, analytics: e.target.checked })}
                      />
                      Analytické cookies
                    </label>
                    <label className="flex items-center gap-2 mb-3">
                      <input
                        type="checkbox"
                        checked={consent.marketing}
                        onChange={(e) => setConsent({ ...consent, marketing: e.target.checked })}
                      />
                      Marketingové cookies
                    </label>

                    <button
                      type="button"
                      className="text-pink-400 underline hover:text-pink-300"
                      onClick={() => setShowCookiesText(true)}
                    >
                      Přečíst celé zásady cookies
                    </button>
                  </>
                ) : (
                  <div className="max-h-64 overflow-auto pr-1 space-y-2">
                    <h4 className="font-semibold text-pink-300">Zásady používání cookies</h4>
                    <p>
                      Cookies používáme pro zajištění základních funkcí webu a anonymní statistiky.
                      Analytické a marketingové cookies se ukládají pouze na základě vašeho souhlasu.
                    </p>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>Nezbytné: chod webu, bezpečnost, košík.</li>
                      <li>Analytické: anonymní měření návštěvnosti.</li>
                      <li>Marketingové: personalizace nabídek/reklamy.</li>
                    </ul>
                    <p>Souhlas můžete kdykoliv změnit v této bublině v patičce.</p>
                    <button
                      type="button"
                      className="mt-2 inline-block text-pink-400 underline hover:text-pink-300"
                      onClick={() => setShowCookiesText(false)}
                    >
                      Zpět na volby cookies
                    </button>
                  </div>
                )}

                <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-gray-900" />
              </div>
            )}
          </div>

          {/* Oddělovač */}
          <span className="text-white/40 select-none">•</span>

          {/* GDPR */}
          <div className="relative" ref={gdprRef}>
            <button
              type="button"
              className="flex items-center gap-1 underline underline-offset-2 decoration-pink-500/60 hover:text-pink-300"
              aria-expanded={openGdpr}
              aria-controls="gdpr-popover"
              onClick={() => setOpenGdpr((v) => !v)}
            >
              <Shield className="w-4 h-4 text-pink-400" />
              Ochrana osobních údajů (GDPR)
            </button>

            {openGdpr && (
              <div
                id="gdpr-popover"
                className="absolute left-1/2 -translate-x-1/2 bottom-[120%] z-50 w-[19rem] rounded-lg bg-gray-900 text-gray-100 text-xs shadow-2xl p-4"
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  type="button"
                  aria-label="Zavřít"
                  className="absolute top-2 right-2 p-1 rounded hover:bg-white/10"
                  onClick={() => setOpenGdpr(false)}
                >
                  <X className="w-4 h-4 text-gray-300" />
                </button>

                {!showGdprText ? (
                  <>
                    <p className="mb-2">
                      🔐 Vaše údaje zpracováváme pouze pro vyřízení objednávek a komunikaci.
                      Údaje nesdílíme mimo nezbytné zpracovatele (doprava, platby).
                    </p>
                    <button
                      type="button"
                      className="text-pink-400 underline hover:text-pink-300"
                      onClick={() => setShowGdprText(true)}
                    >
                      Přečíst celé podmínky GDPR
                    </button>
                  </>
                ) : (
                  <div className="max-h-64 overflow-auto pr-1 space-y-2">
                    <h4 className="font-semibold text-pink-300">Informace o zpracování osobních údajů</h4>
                    <p>
                      Správce: Náramková Móda, kontakt {EMAIL}, {PHONE_DISPLAY}.
                    </p>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>Účel: vyřízení objednávek, komunikace, účetní evidence.</li>
                      <li>Právní základ: plnění smlouvy, oprávněný zájem, zákonná povinnost.</li>
                      <li>Doba uchování: dle zákonných lhůt (typicky 5–10 let u účetních dokladů).</li>
                      <li>Práva subjektu: přístup, oprava, výmaz, omezení, námitka, přenositelnost.</li>
                    </ul>
                    <p>Požadavky zasílejte na {EMAIL}. Odpovíme bez zbytečného odkladu.</p>
                    <button
                      type="button"
                      className="mt-2 inline-block text-pink-400 underline hover:text-pink-300"
                      onClick={() => setShowGdprText(false)}
                    >
                      Zpět na shrnutí
                    </button>
                  </div>
                )}

                <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-gray-900" />
              </div>
            )}
          </div>
        </div>
      </footer>
    </>
  );
}
