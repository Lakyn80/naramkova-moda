import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Categories from "./components/Categories";
import Gallery from "./components/Gallery";
import Footer from "./components/Footer";
import Shop from "./pages/Shop";

function App() {
  return (
    <Router>
      <div className="bg-gradient-to-br from-pink-600 via-pink-200 via-30% via-white to-pink-300 min-h-screen overflow-hidden text-pink-900">
        <Navbar />

        <Routes>
          <Route
            path="/"
            element={
              <>
                <Hero />
                <Categories />
                <Gallery />
              </>
            }
          />
          <Route path="/shop" element={<Shop />} />
        </Routes>

        <Footer />
      </div>
    </Router>
  );
}

export default App;
