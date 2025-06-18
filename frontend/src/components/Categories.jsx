import React from "react";

export default function Categories() {
  const categories = [
    "Maminka", "Babička", "Bratr", "Sestra",
    "Děti", "Svatba", "Jen pro radost",
  ];

  return (
    <section id="kategorie" className="relative py-20 px-4 overflow-hidden">
      <div className="backdrop-blur-sm bg-white/30 rounded-2xl shadow-2xl max-w-5xl mx-auto p-10">
        <h2 className="text-3xl font-bold text-center mb-8 drop-shadow-sm">
          Kategorie
        </h2>
        <div className="flex flex-wrap justify-center gap-4">
          {categories.map((label, index) => (
            <button
              key={index}
              className="bg-white/70 hover:bg-pink-100 shadow-md backdrop-blur-sm rounded-full px-6 py-3 text-sm font-medium text-pink-800 transition-all duration-300"
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
