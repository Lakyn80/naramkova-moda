import React from "react";

export default function Privacy() {
  return (
    <section className="pt-24 pb-12 px-4 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Zásady ochrany osobních údajů</h1>
      <p className="mb-3">
        Správcem je <b>Náramková Móda</b>. Zpracováváme jen údaje nutné k vyřízení objednávky
        (identifikace, kontakty, doručení, obsah objednávek a platby).
      </p>
      <p className="mb-3">
        Právní základ: plnění smlouvy (objednávka), oprávněný zájem (zlepšování služeb) a souhlas (marketingové cookies).
      </p>
      <p className="mb-3">
        Doba uchování: po dobu nezbytnou k vyřízení; účetnictví dle zákona. Svá práva (přístup, výmaz, omezení) uplatníš na
        <a className="underline ml-1" href="mailto:naramkovamoda@email.cz">
          naramkovamoda@email.cz
        </a>.
      </p>
      <p>
        Nepředáváme data mimo EU bez odpovídající ochrany. Více informací poskytneme na vyžádání.
      </p>
    </section>
  );
}
