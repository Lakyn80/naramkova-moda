// src/App.jsx
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
import { CartProvider } from "./context/CartContext";
import ScrollToTop from "./components/ScrollToTop";

// ✅ WhatsApp widget
import WhatsAppWidget from "./components/WhatsAppWidget";

export default function App() {
  const heroRef = useRef();
  const shopRef = useRef();

  return (
    <CartProvider>
      {/* ✅ Aplikace běží na kořeni domény → basename jen "/" */}
      <Router basename="/">
        <ScrollToTop />
        <div className="bg-gradient-to-b from-pink-800 via-pink-600 to-pink-400 min-h-screen overflow-hidden text-pink-50">
          <Navbar heroRef={heroRef} shopRef={shopRef} />
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
          </Routes>
          <Footer />
        </div>

        {/* Plovoucí WhatsApp tlačítko (ladí s designem, bez QR) */}
        <WhatsAppWidget
          phone="420776479747"
          defaultMessage="Dobrý den, rád/a bych se zeptal/a na…"
          position="right"
        />
      </Router>
    </CartProvider>
  );
}
