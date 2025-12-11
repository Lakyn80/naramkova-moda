import React from "react";
import { useNavigate } from "react-router-dom";
import { slugify } from "../utils/slugify";

export default function Categories() {
  const navigate = useNavigate();

  const categories = [
    "Maminka", "Babička", "Bratr", "Sestra", "Děti", "Svatba", "Jen pro radost",
    "Tatínek", "Dědeček", "Kamarádka", "Láska", "Pro děti", "Pro páry", "Výročí", "Přátelství"
  ];

  const handleClick = (label) => {
    const slug = slugify(label || "");
    navigate(`/category/${encodeURIComponent(slug)}`);
  };

  return (
    <section id="kategorie" className="relative py-20 px-4 bg-gradient-to-b from-rose-mid to-rose-light overflow-hidden">
      <img
        src="/wave.svg"
        alt="Wave top"
        className="absolute -top-[1px] left-0 w-full pointer-events-none rotate-180 z-0"
      />

      <div className="backdrop-blur-sm bg-white/10 rounded-2xl shadow-2xl max-w-5xl mx-auto p-6 sm:p-10 relative z-10">
        <h2 className="text-3xl sm:text-4xl font-bold text-center mb-6 sm:mb-8 text-white drop-shadow-sm">
          Kategorie
        </h2>

        <div className="overflow-hidden relative">
          <div className="flex gap-3 sm:gap-6 animate-scroll whitespace-nowrap">
            {[...categories, ...categories].map((label, index) => (
              <button
                key={index}
                onClick={() => handleClick(label)}
                className="bg-white/20 hover:bg-pink-100 text-white shadow-md backdrop-blur-sm rounded-full px-4 sm:px-6 py-2 sm:py-3 text-sm font-medium transition-all duration-300 whitespace-nowrap"
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
