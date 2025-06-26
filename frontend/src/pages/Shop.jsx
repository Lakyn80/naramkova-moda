// src/pages/Shop.jsx
import React, { useState, useEffect } from "react";
import { products, categoryTree } from "../data/products";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";

export default function Shop() {
  const location = useLocation();
  const navigate = useNavigate();
  const { addToCart } = useCart();

  const allSubcategories = Object.values(categoryTree).flat();
  const [selectedCategories, setSelectedCategories] = useState(allSubcategories);
  const [searchTerm, setSearchTerm] = useState("");

  // Vyčte kategorii z URL parametru (např. ?category=Maminka)
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const categoryFromURL = params.get("category");
    if (categoryFromURL && allSubcategories.includes(categoryFromURL)) {
      setSelectedCategories([categoryFromURL]);
    } else {
      setSelectedCategories(allSubcategories); // výchozí
    }
  }, [location.search]);

  const handleCheckboxChange = (subcategory) => {
    if (selectedCategories.includes(subcategory)) {
      setSelectedCategories(selectedCategories.filter((cat) => cat !== subcategory));
    } else {
      setSelectedCategories([...selectedCategories, subcategory]);
    }
  };

  const handleSelectAll = () => {
    setSelectedCategories(allSubcategories);
  };

  const handleDeselectAll = () => {
    setSelectedCategories([]);
  };

  const filteredProducts = products.filter(
    (product) =>
      product.categories.some((cat) => selectedCategories.includes(cat)) &&
      product.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <section className="pt-24 pb-12 px-4 bg-gradient-to-br from-pink-300 via-white via-30% to-pink-200 min-h-screen">
      <h2 className="text-3xl font-bold text-center text-pink-900 mb-8">E-shop</h2>
      <div className="flex max-w-7xl mx-auto gap-8">
        {/* Levý panel – Kategorie */}
        <aside className="w-1/4 bg-white/70 p-4 rounded-2xl shadow">
          <h3 className="text-xl font-semibold mb-4 text-pink-800">Kategorie</h3>

          <input
            type="text"
            placeholder="Hledat produkt..."
            className="w-full px-3 py-2 mb-4 border rounded-md"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />

          <ul className="space-y-4">
            {Object.entries(categoryTree).map(([mainCategory, subcats]) => (
              <li key={mainCategory}>
                <div className="flex justify-between items-center">
                  <strong className="text-pink-900">{mainCategory.toUpperCase()}</strong>
                  <button
                    onClick={() => {
                      const subs = subcats.length > 0 ? subcats : [mainCategory];
                      const allSelected = subs.every((c) => selectedCategories.includes(c));
                      if (allSelected) {
                        setSelectedCategories(selectedCategories.filter((c) => !subs.includes(c)));
                      } else {
                        setSelectedCategories([...new Set([...selectedCategories, ...subs])]);
                      }
                    }}
                    className="text-sm text-pink-600 hover:underline"
                  >
                    {subcats.every((c) => selectedCategories.includes(c)) ? "Odebrat" : "Vybrat"}
                  </button>
                </div>
                <ul className="ml-4 mt-1 space-y-1">
                  {(subcats.length > 0 ? subcats : [mainCategory]).map((subcat) => (
                    <li key={subcat}>
                      <label className="flex items-center space-x-2 text-pink-800">
                        <input
                          type="checkbox"
                          checked={selectedCategories.includes(subcat)}
                          onChange={() => handleCheckboxChange(subcat)}
                          className="accent-pink-600"
                        />
                        <span>{subcat.charAt(0).toUpperCase() + subcat.slice(1)}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>

          <div className="mt-6 space-y-2">
            <button
              onClick={handleSelectAll}
              className="w-full bg-pink-500 text-white font-semibold py-2 px-4 rounded-lg hover:bg-pink-600 transition"
            >
              Vybrat vše
            </button>
            <button
              onClick={handleDeselectAll}
              className="w-full bg-pink-100 text-pink-800 font-semibold py-2 px-4 rounded-lg hover:bg-pink-200 transition"
            >
              Odebrat vše
            </button>
          </div>
        </aside>

        {/* Pravý panel – Produkty */}
        <div className="w-3/4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProducts.map((product, index) => (
            <div
              key={index}
              className="bg-white/60 backdrop-blur-md rounded-2xl shadow-xl overflow-hidden text-center p-4 hover:shadow-2xl transition-all duration-300"
            >
              <img
                src={product.image}
                alt={product.name}
                className="w-full h-48 object-cover rounded-xl"
              />
              <Link
                to={`/shop/${product.name.toLowerCase().replace(/\s+/g, "-")}`}
                className="block mt-4 text-lg font-semibold text-pink-900 hover:underline"
              >
                {product.name}
              </Link>
              <p className="text-sm text-pink-700 mt-1">{product.price}</p>
              <button
                onClick={() => addToCart(product)}
                className="mt-2 bg-pink-600 hover:bg-pink-700 text-white py-1 px-3 rounded text-sm transition"
              >
                Přidat do košíku
              </button>
            </div>
          ))}

          {filteredProducts.length === 0 && (
            <div className="col-span-full text-center text-pink-800 font-medium">
              Nenalezeny žádné produkty pro vybrané filtry.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
