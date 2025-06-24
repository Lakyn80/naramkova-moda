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
import { CartProvider } from "./context/CartContext";
import Checkout from "./pages/Checkout";


function App() {
  const heroRef = useRef();
  const shopRef = useRef();

  return (
    <CartProvider>
      <Router>
        <div className="bg-gradient-to-br from-pink-600 via-pink-200 via-30% via-white to-pink-300 min-h-screen overflow-hidden text-pink-900">
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
      </Router>
    </CartProvider>
  );
}

export default App;
