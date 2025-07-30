// 📁 src/App.jsx

// ✅ Import React a potřebných knihoven
import React, { useRef, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// ✅ Import komponent
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Categories from "./components/Categories";
import Gallery from "./components/Gallery";
import Footer from "./components/Footer";
import Shop from "./pages/Shop";
import ProductDetail from "./pages/ProductDetail";
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";

// ✅ Kontext pro košík a pomocné komponenty
import { CartProvider } from "./context/CartContext";
import ScrollToTop from "./components/ScrollToTop";

export default function App() {
  // 🟨 Refy pro scrollování na sekce (Hero, Shop)
  const heroRef = useRef();
  const shopRef = useRef();

  // 🟩 Automatické načtení Chat Widgetu z GitHub Pages
  useEffect(() => {
    const script = document.createElement("script");

    // 🔗 Odkaz na veřejně hostovaný widget build (GitHub Pages)
    script.src = "https://lakyn80.github.io/ai_chatbot_widget/chat-widget.js";
    script.async = true;

    // 🧠 Po načtení skriptu se spustí widget s konfigurací
    script.onload = () => {
      if (window.ChatbotWidget) {
        window.ChatbotWidget.init({
          welcomeMessage: "Dobrý den! Rádi vám pomůžeme s výběrem náramku 💝",
          accentColor: "#ec4899", // 💖 Barva ladící s Náramkovou Módou
          position: "right",      // 💬 Plovoucí bublina vpravo
        });
      }
    };

    // 🧩 Vložíme <script> do těla dokumentu
    document.body.appendChild(script);

    // 🧼 Úklid při odstranění komponenty (není nutné, ale dobrá praxe)
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  return (
    <CartProvider>
      <Router>
        <ScrollToTop />

        {/* 🎨 Celkový layout s gradientem a tmavým textem */}
        <div className="bg-gradient-to-br from-pink-600 via-pink-200 via-30% via-white to-pink-300 min-h-screen overflow-hidden text-pink-900">

          {/* 🧭 Navigace */}
          <Navbar heroRef={heroRef} shopRef={shopRef} />

          {/* 📦 Routing mezi stránkami */}
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

          {/* 🦶 Patička */}
          <Footer />
        </div>
      </Router>
    </CartProvider>
  );
}
