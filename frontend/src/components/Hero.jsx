import React from "react";
import { useNavigate } from "react-router-dom";

export default function Hero() {
  const navigate = useNavigate();

  const handleExploreClick = () => {
    navigate("/shop");
  };

  return (
    <section
      id="home"
      className="relative min-h-screen flex items-center justify-center px-4 pt-24 pb-10 sm:pt-32 sm:pb-16 overflow-hidden"
    >
      <div className="backdrop-blur-sm bg-white/20 rounded-2xl p-6 sm:p-10 shadow-2xl w-full max-w-xl md:max-w-3xl text-center animate-float z-10">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-pink-900 bg-clip-text text-transparent bg-gradient-to-r from-pink-700 via-pink-400 to-pink-700 animate-gradient-x drop-shadow-lg">
          Náramková Móda
        </h1>
        <p className="mt-4 text-lg sm:text-xl text-pink-800 font-medium">
          Ozdobte se jedinečností ✨
        </p>
        <button
          onClick={handleExploreClick}
          className="mt-8 w-full sm:w-auto px-8 py-3 bg-pink-500 text-white font-semibold rounded-full hover:bg-pink-600 shadow-lg transition duration-300"
        >
          Prozkoumat nabídku
        </button>
      </div>
    </section>
  );
}
