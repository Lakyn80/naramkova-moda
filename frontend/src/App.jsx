import React from "react";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Categories from "./components/Categories";
import Gallery from "./components/Gallery";
import Footer from "./components/Footer";

function App() {
  return (
    <div className="bg-gradient-to-br from-pink-600 via-white via-30% to-pink-300 bg-fixed text-pink-900">
      <Navbar />
      <Hero />
      <Categories />
      <Gallery />
      <Footer />
    </div>
  );
}

export default App;
