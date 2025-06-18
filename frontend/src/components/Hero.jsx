import React from "react";

export default function Hero() {
  return (
    <section
      id="home"
      className="relative min-h-screen flex items-center justify-center px-4 pt-32 pb-10 overflow-hidden"
    >
      <div className="backdrop-blur-sm bg-white/20 rounded-2xl p-10 shadow-2xl max-w-3xl text-center animate-float z-10">
        <h1 className="text-5xl sm:text-6xl font-extrabold text-pink-900 bg-clip-text text-transparent bg-gradient-to-r from-pink-700 via-pink-400 to-pink-700 animate-gradient-x drop-shadow-lg">
          Náramková Móda
        </h1>
        <p className="mt-4 text-xl text-pink-800 font-medium">
          Ozdobte se jedinečností ✨
        </p>
        <button className="mt-8 px-8 py-3 bg-pink-500 text-white font-semibold rounded-full hover:bg-pink-600 shadow-lg transition duration-300">
          Prozkoumat nabídku
        </button>
      </div>
    </section>
  );
}
