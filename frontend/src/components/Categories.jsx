import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { slugify } from "../utils/slugify";

const API_BASE = import.meta.env.VITE_API_BASE || `${window.location.origin}/api`;

export default function Categories() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/categories/`)
      .then((res) => res.json())
      .then((data) => {
        const mapped = (data || [])
          .map((cat) => {
            const label = cat?.name || "";
            const slug = cat?.slug || slugify(label);
            return label ? { label, slug } : null;
          })
          .filter(Boolean);
        setCategories(mapped);
      })
      .catch((err) => {
        console.error("Chyba načtení kategorií:", err);
        setCategories([]);
      });
  }, []);

  const handleClick = (slug) => {
    navigate(`/category/${encodeURIComponent(slug)}`);
  };

  const marqueeList = categories.length ? [...categories, ...categories] : [];

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

      <div className="backdrop-blur-sm bg-white/10 rounded-2xl shadow-2xl max-w-5xl mx-auto p-6 sm:p-10 relative z-10">
        <h2 className="text-3xl sm:text-4xl font-bold text-center mb-6 sm:mb-8 text-white drop-shadow-sm">
          Kategorie
        </h2>

        {marqueeList.length ? (
          <div className="overflow-hidden relative">
            <div className="flex gap-3 sm:gap-6 animate-scroll whitespace-nowrap">
              {marqueeList.map((cat, index) => (
                <button
                  key={`${cat.slug}-${index}`}
                  onClick={() => handleClick(cat.slug)}
                  className="bg-white/20 hover:bg-pink-100 text-white shadow-md backdrop-blur-sm rounded-full px-4 sm:px-6 py-2 sm:py-3 text-sm font-medium transition-all duration-300 whitespace-nowrap"
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-center text-white/80">Načítám kategorie…</p>
        )}
      </div>

      <img
        src="/wave.svg"
        alt="Wave bottom"
        className="absolute bottom-0 left-0 w-full pointer-events-none z-0"
      />
    </section>
  );
}
