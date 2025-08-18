import React from "react";
import { useNavigate } from "react-router-dom";

export default function Categories() {
  const navigate = useNavigate();

  const categories = [
    "Maminka", "Babička", "Bratr", "Sestra", "Děti", "Svatba", "Jen pro radost",
    "Tatínek", "Dědeček", "Kamarádka", "Láska", "Pro děti", "Pro páry", "Výročí", "Přátelství"
  ];

  const categoryAliases = {
    "pro maminku": "maminka",
    "pro tatínka": "tatínek",
    "pro babičku": "babička",
    "pro dědečka": "dědeček",
    "pro děti": "děti",
    "pro sestru": "sestra",
    "pro bratra": "bratr",
    "kamarádka": "kamarádka",
    "jen pro radost": "jen pro radost",
    "přátelství": "přátelství",
    "výročí": "výročí",
    "láska": "láska",
    "svatba": "svatba",
    "pro páry": "pro páry",
    "jméno": "jméno",
    "ostatní": "ostatní",
    "maminka": "maminka",
    "babička": "babička",
    "bratr": "bratr",
    "sestra": "sestra",
    "děti": "děti",
    "tatínek": "tatínek",
    "dědeček": "dědeček",
    "láska": "láska",
    "výročí": "výročí",
    "přátelství": "přátelství",
    "pro páry": "pro páry",
  };

  const toAlias = (label) => {
    const key = (label || "").toLowerCase().trim();
    return categoryAliases[key] || key;
  };

  const handleClick = (categoryLabel) => {
    const alias = toAlias(categoryLabel);
    const encoded = encodeURIComponent(alias);
    navigate(`/shop?category=${encoded}`);
  };

  return (
    <section
      id="kategorie"
      className="relative pt-16 pb-0 sm:pt-20 sm:pb-0 px-3 sm:px-4 overflow-hidden"
    >
      <div className="backdrop-blur-sm bg-white/30 rounded-2xl shadow-2xl max-w-5xl mx-auto p-6 sm:p-10">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-6 sm:mb-8 drop-shadow-sm">
          Kategorie
        </h2>

        <div className="overflow-hidden relative">
          <div className="flex gap-3 sm:gap-6 animate-scroll whitespace-nowrap">
            {[...categories, ...categories].map((label, index) => (
              <button
                key={index}
                onClick={() => handleClick(label)}
                className="bg-white/70 hover:bg-pink-100 shadow-md backdrop-blur-sm rounded-full px-4 sm:px-6 py-2 sm:py-3 text-sm font-medium text-pink-800 transition-all duration-300 whitespace-nowrap"
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <img
        src="/wave.svg"
        alt="Wave transition"
        className="absolute bottom-0 left-0 w-full pointer-events-none opacity-40 z-0"
      />
    </section>
  );
}
