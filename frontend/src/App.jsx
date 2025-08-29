import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import React, { useRef } from "react";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Categories from "./components/Categories";
import Gallery from "./components/Gallery";
import Footer from "./components/Footer";
import Shop from "./pages/Shop";
import ProductDetail from "./pages/ProductDetail";
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";
import Privacy from "./pages/Privacy";
import CookiesPolicy from "./pages/CookiesPolicy";
import { CartProvider } from "./context/CartContext";
import ScrollToTop from "./components/ScrollToTop";

export default function App() {
  const heroRef = useRef();
  const shopRef = useRef();

  const basename = import.meta.env.BASE_URL || "/";

  return (
    <CartProvider>
      <Router basename={basename}>
        <ScrollToTop />
        {/* === Sticky layout: flex column, main flex-1, footer na dně === */}
        <div className="min-h-screen flex flex-col bg-gradient-to-b from-pink-800 via-pink-600 to-pink-400 text-pink-50">
          <Navbar heroRef={heroRef} shopRef={shopRef} />

          <main className="flex-1 overflow-hidden">
            <Routes>
              <Route
                path="/"
                element={
                  <>
                    <Hero ref={heroRef} />
                    <Categories />
                    <Gallery />
                  </>
                }
              />
              <Route path="/shop" element={<Shop ref={shopRef} />} />
              <Route path="/shop/:slug" element={<ProductDetail />} />
              <Route path="/cart" element={<Cart />} />
              <Route path="/checkout" element={<Checkout />} />

              {/* stránky pro odkazy ve footeru */}
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/cookies" element={<CookiesPolicy />} />
            </Routes>
          </main>

          <Footer />
        </div>
      </Router>
    </CartProvider>
  );
}
