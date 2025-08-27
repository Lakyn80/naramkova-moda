// frontend/src/components/Hero.jsx
import React from "react";
import { useNavigate } from "react-router-dom";

export default function Hero() {
  const navigate = useNavigate();

  const handleExploreClick = () => {
    // relativní navigace vůči basename
    navigate("shop");
  };

  return (
    <section
      id="home"
      className="relative min-h-screen flex items-center justify-center px-4 pt-24 pb-10 sm:pt-32 sm:pb-16 overflow-hidden"
      style={{
        backgroundImage: `
          radial-gradient(circle at top left, #3b0764 0%, #6b21a8 30%, transparent 60%),
          linear-gradient(to right, #9d174d, #be185d, #f9a8d4)
        `,
      }}
    >
      <div className="backdrop-blur-sm bg-white/20 rounded-2xl p-6 sm:p-10 shadow-2xl w-full max-w-xl md:max-w-3xl text-center animate-float z-10">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-white bg-clip-text text-transparent bg-gradient-to-r from-pink-200 via-pink-300 to-pink-200 animate-gradient-x drop-shadow-lg">
          Náramková Móda
        </h1>
        <p className="mt-4 text-lg sm:text-xl text-pink-100 font-medium">
          Ozdobte se jedinečností ✨
        </p>
        <button
          onClick={handleExploreClick}
          className="mt-8 w-full sm:w-auto px-8 py-3 bg-pink-600 hover:bg-pink-700 text-white font-semibold rounded-full shadow-lg transition duration-300"
        >
          Prozkoumat nabídku
        </button>
      </div>

      {/* Vlna z public/ */}
      <img
        src={`${import.meta.env.BASE_URL || "/"}wave.svg`}
        alt="Wave bottom"
        className="absolute bottom-0 left-0 w-full h-auto block pointer-events-none z-0"
        loading="lazy"
        decoding="async"
      />
    </section>
  );
}
