import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";
import logo from "../assets/logo 1.svg";

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === "/";
  const { cartItems } = useCart();

  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);

  const handleHomeClick = () => {
    setMenuOpen(false);
    if (isHome) {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      navigate("/");
    }
  };

  return (
    <nav className="fixed top-0 left-0 w-full z-50 px-4 py-3 sm:px-8 bg-white/10 backdrop-blur-md shadow-lg">
      <div className="flex justify-between items-center max-w-7xl mx-auto">
        {/* Logo + Název */}
        <div
          className="text-xl sm:text-2xl font-bold tracking-wider cursor-pointer flex items-center gap-2"
          onClick={handleHomeClick}
        >
          <img
            src={logo}
            alt="Logo"
            className="h-12 w-12 sm:h-14 sm:w-14 object-contain"
          />
          <div className="flex items-center gap-1">
            <span className="bg-gradient-to-r from-pink-300 via-white to-pink-300 bg-clip-text text-transparent animate-gradient-x">
              Náramková
            </span>
            <span className="text-white">Móda</span>
          </div>
        </div>

        {/* Hamburger pro mobily */}
        <button
          className="sm:hidden text-pink-900 text-3xl focus:outline-none"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          ☰
        </button>

        {/* Navigace pro desktop */}
        <ul className="hidden sm:flex space-x-6 text-lg font-semibold items-center">
          <li>
            <span
              onClick={handleHomeClick}
              className="cursor-pointer text-pink-900 hover:text-pink-600 transition"
            >
              Domů
            </span>
          </li>
          {isHome && (
            <>
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
            </>
          )}
          <li>
            <Link
              to="/shop"
              className="text-pink-900 hover:text-pink-600 transition"
            >
              E-shop
            </Link>
          </li>
          <li>
            <Link
              to="/cart"
              className="text-pink-900 hover:text-pink-600 transition relative"
            >
              🛒 Košík
              {cartCount > 0 && (
                <span className="absolute -top-2 -right-3 bg-pink-600 text-white text-xs rounded-full px-2 py-0.5">
                  {cartCount}
                </span>
              )}
            </Link>
          </li>
        </ul>
      </div>

      {/* Mobilní menu */}
      {menuOpen && (
        <div className="sm:hidden mt-3 space-y-3 bg-white/70 text-pink-900 rounded-xl shadow px-6 py-4">
          <div
            onClick={handleHomeClick}
            className="cursor-pointer hover:text-pink-600 transition"
          >
            Domů
          </div>
          {isHome && (
            <>
              <a
                href="#kategorie"
                className="block hover:text-pink-600 transition"
                onClick={() => setMenuOpen(false)}
              >
                Kategorie
              </a>
              <a
                href="#galerie"
                className="block hover:text-pink-600 transition"
                onClick={() => setMenuOpen(false)}
              >
                Galerie
              </a>
            </>
          )}
          <Link
            to="/shop"
            className="block hover:text-pink-600 transition"
            onClick={() => setMenuOpen(false)}
          >
            E-shop
          </Link>
          <Link
            to="/cart"
            className="block hover:text-pink-600 transition"
            onClick={() => setMenuOpen(false)}
          >
            🛒 Košík {cartCount > 0 && `(${cartCount})`}
          </Link>
        </div>
      )}
    </nav>
  );
}
