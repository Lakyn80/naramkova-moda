import React from "react";
import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 w-full z-50 px-8 py-4 bg-white/10 backdrop-blur-md shadow-lg">
      <div className="flex justify-between items-center max-w-7xl mx-auto">
        {/* Logo */}
        <div className="text-2xl font-bold tracking-wider">
          <Link to="/" className="flex items-center gap-1">
            <span className="bg-gradient-to-r from-pink-300 via-white to-pink-300 bg-clip-text text-transparent animate-gradient-x">
              Náramková
            </span>
            <span className="text-white">Móda</span>
          </Link>
        </div>

        {/* Navigace */}
        <ul className="flex space-x-6 text-lg font-semibold">
          <li>
            <a
              href="#kategorie"
              className="text-pink-900 hover:text-pink-600 transition"
            >
              Kategorie
            </a>
          </li>
          <li>
            <a
              href="#galerie"
              className="text-pink-900 hover:text-pink-600 transition"
            >
              Galerie
            </a>
          </li>
          <li>
            <Link
              to="/shop"
              className="text-pink-900 hover:text-pink-600 transition"
            >
              Prozkoumat nabídku
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  );
}
