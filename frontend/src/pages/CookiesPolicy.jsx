import React from "react";

export default function CookiesPolicy() {
  return (
    <section className="pt-24 pb-12 px-4 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Zásady používání cookies</h1>
      <p className="mb-3">
        Používáme tyto kategorie cookies:
      </p>
      <ul className="list-disc ml-6 mb-3">
        <li><b>Nezbytné</b> – provoz webu, košík, bezpečnost (nelze vypnout).</li>
        <li><b>Analytické</b> – měření návštěvnosti a výkonu (pouze se souhlasem).</li>
        <li><b>Marketingové</b> – personalizace a reklama (pouze se souhlasem).</li>
      </ul>
      <p className="mb-3">
        Nastavení souhlasu můžeš kdykoli změnit smazáním souboru <code>cookie_consent</code> nebo přes odkaz v patičce „Nastavení cookies“.
      </p>
      <p>
        Dotazy k souborům cookies:{" "}
        <a className="underline" href="mailto:naramkovamoda@email.cz">
          naramkovamoda@email.cz
        </a>.
      </p>
    </section>
  );
}
