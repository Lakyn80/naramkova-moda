import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";
import logo from "../assets/logo.jpg";

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === "/";

  const { cartItems } = useCart();
  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);

  const handleHomeClick = () => {
    // zavři mobilní menu
    setMenuOpen(false);

    // Pokud jsme na / a je tam hash nebo query, smaž je a nahoru
    if (isHome && (location.hash || location.search)) {
      // vyčištění URL bez reloadu
      window.history.replaceState(null, "", "/");
      // vyvoláme změnu historie, aby se případné posluchače probudily
      window.dispatchEvent(new PopStateEvent("popstate"));
      // scroll nahoru
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    // Pokud nejsme na / → přejdi na / (replace, ať zbytečně nenafukujeme historii)
    if (!isHome) {
      navigate("/", { replace: true });
      // po navigaci nahoru
      // (RR v9 přeroluje sám po změně cesty; přesto explicitně)
      requestAnimationFrame(() =>
        window.scrollTo({ top: 0, behavior: "smooth" })
      );
      return;
    }

    // Jsme už čistě na / → jen nahoru
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav className="fixed top-0 left-0 w-full z-50 px-4 sm:px-8 py-3 bg-white/10 backdrop-blur-md shadow-lg transition-all duration-300">
      <div className="flex justify-between items-center max-w-7xl mx-auto">
        {/* Logo + Nápis (klik = Domů) */}
        <div
          className="text-2xl font-bold tracking-wider cursor-pointer flex items-center gap-3"
          onClick={handleHomeClick}
        >
          <img src={logo} alt="Logo" className="h-14 w-14 object-contain" />
          <span
            className={`transition-all duration-500 font-bold ${
              scrolled
                ? "text-pink-900"
                : "bg-gradient-to-r from-pink-700 via-pink-400 to-pink-700 bg-clip-text text-transparent animate-gradient-x"
            }`}
          >
            Náramková Móda
          </span>
        </div>

        {/* Hamburger */}
        <div className="sm:hidden relative">
          <button
            className="text-pink-900 text-3xl focus:outline-none relative"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            ☰
            {cartCount > 0 && (
              <span className="absolute -top-2 -right-3 bg-pink-600 text-white text-xs rounded-full px-1.5 py-0.5">
                {cartCount}
              </span>
            )}
          </button>
        </div>

        {/* Navigace (desktop) */}
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
            <Link to="/shop" className="text-pink-900 hover:text-pink-600 transition">
              E-shop
            </Link>
          </li>
          <li>
            <Link to="/cart" className="text-pink-900 hover:text-pink-600 transition relative">
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
          <div onClick={handleHomeClick} className="cursor-pointer hover:text-pink-600 transition">
            Domů
          </div>

          {isHome && (
            <>
              <a
                href="#kategorie"
                onClick={() => setMenuOpen(false)}
                className="block hover:text-pink-600"
              >
                Kategorie
              </a>
              <a
                href="#galerie"
                onClick={() => setMenuOpen(false)}
                className="block hover:text-pink-600"
              >
                Galerie
              </a>
            </>
          )}

          <Link to="/shop" onClick={() => setMenuOpen(false)} className="block hover:text-pink-600">
            E-shop
          </Link>
          <Link to="/cart" onClick={() => setMenuOpen(false)} className="block hover:text-pink-600">
            🛒 Košík {cartCount > 0 && `(${cartCount})`}
          </Link>
        </div>
      )}
    </nav>
  );
}
