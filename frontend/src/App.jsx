// frontend/src/App.jsx
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
import CookieBanner from "./components/CookieBanner";

export default function App() {
  const heroRef = useRef();
  const shopRef = useRef();

  // BASE_URL je z Vite (base:"/"), takže funguje v dev i prod
  const basename = import.meta.env.BASE_URL || "/";

  return (
    <CartProvider>
      <Router basename={basename}>
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
                  <CookieBanner />
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
      </Router>
    </CartProvider>
  );
}
