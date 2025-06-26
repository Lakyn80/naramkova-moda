import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === "/";
  const { cartItems } = useCart();

  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);

  const handleHomeClick = () => {
    if (isHome) {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      navigate("/");
    }
  };

  return (
    <nav className="fixed top-0 left-0 w-full z-50 px-8 py-4 bg-white/10 backdrop-blur-md shadow-lg transition-all duration-300">
      <div className="flex justify-between items-center max-w-7xl mx-auto">
        {/* Logo */}
        <div
          className="text-2xl font-bold tracking-wider cursor-pointer"
          onClick={handleHomeClick}
        >
          <div className="flex items-center gap-1">
            <span className="bg-gradient-to-r from-pink-300 via-white to-pink-300 bg-clip-text text-transparent animate-gradient-x">
              Náramková
            </span>
            <span className="text-white">Móda</span>
          </div>
        </div>

        {/* Navigace */}
        <ul className="flex space-x-6 text-lg font-semibold items-center">
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
    </nav>
  );
}
