import React from "react";

export default function Categories() {
  const categories = [
    "Maminka", "Babička", "Bratr", "Sestra", "Děti", "Svatba", "Jen pro radost",
    "Tatínek", "Dědeček", "Kamarádka", "Láska", "Pro děti", "Pro páry", "Výročí", "Přátelství"
  ];

  return (
    <section id="kategorie" className="relative py-20 px-4 overflow-hidden">
      <div className="backdrop-blur-sm bg-white/30 rounded-2xl shadow-2xl max-w-5xl mx-auto p-10">
        <h2 className="text-3xl font-bold text-center mb-8 drop-shadow-sm">
          Kategorie
        </h2>

        {/* ORLOJ EFEKT */}
        <div className="overflow-hidden relative">
          <div className="flex gap-6 animate-scroll whitespace-nowrap">
            {categories.map((label, index) => (
              <button
                key={index}
                className="bg-white/70 hover:bg-pink-100 shadow-md backdrop-blur-sm rounded-full px-6 py-3 text-sm font-medium text-pink-800 transition-all duration-300"
              >
                {label}
              </button>
            ))}
            {/* Druhá kopie pro plynulý loop */}
            {categories.map((label, index) => (
              <button
                key={`copy-${index}`}
                className="bg-white/70 hover:bg-pink-100 shadow-md backdrop-blur-sm rounded-full px-6 py-3 text-sm font-medium text-pink-800 transition-all duration-300"
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
