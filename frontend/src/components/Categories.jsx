import React from "react";
import { useNavigate } from "react-router-dom";

export default function Categories() {
  const navigate = useNavigate();

  const categories = [
    "Maminka", "Babička", "Bratr", "Sestra", "Děti", "Svatba", "Jen pro radost",
    "Tatínek", "Dědeček", "Kamarádka", "Láska", "Pro děti", "Pro páry", "Výročí", "Přátelství"
  ];

  const categoryAliases = {
    "maminka": "maminka",
    "babička": "babička",
    "bratr": "bratr",
    "sestra": "sestra",
    "děti": "děti",
    "svatba": "svatba",
    "jen pro radost": "jen pro radost",
    "tatínek": "tatínek",
    "dědeček": "dědeček",
    "kamarádka": "kamarádka",
    "láska": "láska",
    "pro děti": "pro děti",
    "pro páry": "pro páry",
    "výročí": "výročí",
    "přátelství": "přátelství",
  };

  const handleClick = (label) => {
    const key = (label || "").toLowerCase().trim();
    const alias = categoryAliases[key] || key;
    navigate(`/shop?category=${encodeURIComponent(alias)}`);
  };

  return (
    <section
      id="kategorie"
      className="relative py-20 px-4 bg-gradient-to-b from-rose-mid to-rose-light overflow-hidden"
    >
      <img
        src="/wave.svg"
        alt="Wave top"
        className="absolute -top-[1px] left-0 w-full pointer-events-none rotate-180 z-0"
      />

      <div
        className="backdrop-blur-sm bg-white/10 rounded-2xl shadow-2xl max-w-5xl mx-auto p-6 sm:p-10 relative z-10"
      >
        <h2 className="text-3xl sm:text-4xl font-bold text-center mb-6 sm:mb-8 text-white drop-shadow-sm">
          Kategorie
        </h2>

        <div className="overflow-hidden relative">
          <div className="flex gap-3 sm:gap-6 animate-scroll whitespace-nowrap">
            {[...categories, ...categories].map((label, index) => (
              <button
                key={index}
                onClick={() => handleClick(label)}
                className="
                  inline-flex items-center
                  rounded-full
                  px-6 sm:px-8 py-3 sm:py-4
                  text-sm font-semibold tracking-wide
                  whitespace-nowrap select-none

                  bg-white/15
                  text-white
                  border border-white/30
                  shadow-[0_2px_6px_rgba(0,0,0,0.25)]

                  hover:bg-white/25 hover:border-white/50
                  active:scale-[.97]

                  focus-visible:outline-none
                  focus-visible:ring-2 focus-visible:ring-rose-300/40

                  transition-all duration-300
                "
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <img
        src="/wave.svg"
        alt="Wave bottom"
        className="absolute bottom-0 left-0 w-full pointer-events-none z-0"
      />
    </section>
  );
}
