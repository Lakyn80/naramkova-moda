import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { useCart } from "../context/CartContext";

// Kategorie – statický strom (pro filtraci)
const categoryTree = {
  rodina: ["maminka", "děti", "tatínek", "dědeček", "babička", "bratr", "sestra"],
  svatba: ["svatba", "pro nevěstu", "pro ženicha", "pro svědky"],
  dárky: ["jen pro radost", "jméno"],
  ostatní: ["přátelství", "láska", "výročí", "pro páry", "kamarádka"],
};

// Převod názvů kategorií z API na interní tagy
const categoryAliases = {
  "pro maminku": "maminka",
  "pro babičku": "babička",
  "pro tatínka": "tatínek",
  "pro dědečka": "dědeček",
  "pro děti": "děti",
  "pro bratra": "bratr",
  "pro sestru": "sestra",
  "pro kamarádku": "kamarádka",
  "pro páry": "pro páry",
  "jen pro radost": "jen pro radost",
  "výročí": "výročí",
  "přátelství": "přátelství",
  "láska": "láska",
  "jméno": "jméno",
  "ostatní": "ostatní",
  svatba: "svatba",
  "pro nevěstu": "pro nevěstu",
  "pro ženicha": "pro ženicha",
  "pro svědky": "pro svědky",
};

export default function Shop() {
  const { addToCart } = useCart();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const urlCategory = params.get("category");

  const allSubcategories = Object.values(categoryTree).flat();
  const [selectedCategories, setSelectedCategories] = useState(
    urlCategory && allSubcategories.includes(urlCategory)
      ? [urlCategory]
      : allSubcategories
  );
  const [searchTerm, setSearchTerm] = useState("");
  const [products, setProducts] = useState([]);

  // Načtení produktů z API
  useEffect(() => {
    fetch("/api/products/")
      .then((res) => res.json())
      .then((data) => setProducts(data))
      .catch((err) => console.error("Chyba načítání produktů:", err));
  }, []);

  // Aplikace URL filtru
  useEffect(() => {
    if (urlCategory && allSubcategories.includes(urlCategory)) {
      setSelectedCategories([urlCategory]);
    }
  }, [urlCategory]);

  // Správa výběru kategorií
  const toggleCat = (subcat) =>
    setSelectedCategories((prev) =>
      prev.includes(subcat) ? prev.filter((c) => c !== subcat) : [...prev, subcat]
    );
  const selectAll = () => setSelectedCategories(allSubcategories);
  const deselectAll = () => setSelectedCategories([]);

  // Filtrování produktů
  const filteredProducts = products.filter((p) => {
    const raw = p.category?.name.toLowerCase().trim() || "";
    const cat = categoryAliases[raw] || raw;
    return (
      selectedCategories.includes(cat) &&
      p.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <section className="pt-24 pb-12 bg-gradient-to-br from-pink-300 to-pink-200 min-h-screen">
      {/* pevný wrapper */}
      <div className="mx-auto max-w-7xl px-4">
        <h2 className="text-4xl font-extrabold text-center mb-10">E-shop</h2>

        <div className="flex flex-wrap items-start gap-6">
          {/* Levý panel – filtry */}
          <aside className="flex-shrink-0 w-64 bg-white/80 p-4 rounded-2xl shadow">
            <h3 className="text-lg font-semibold mb-4">Kategorie</h3>
            <input
              type="text"
              placeholder="Hledat produkt..."
              className="w-full mb-4 px-3 py-2 border rounded"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <ul className="space-y-4 text-sm">
              {Object.entries(categoryTree).map(([main, subs]) => (
                <li key={main}>
                  <div className="flex justify-between items-center">
                    <strong>{main.toUpperCase()}</strong>
                    <button
                      onClick={() => {
                        const allSel = subs.every((s) =>
                          selectedCategories.includes(s)
                        );
                        if (allSel) {
                          setSelectedCategories((prev) =>
                            prev.filter((c) => !subs.includes(c))
                          );
                        } else {
                          setSelectedCategories((prev) => [
                            ...new Set([...prev, ...subs]),
                          ]);
                        }
                      }}
                      className="text-sm hover:underline"
                    >
                      {subs.every((s) => selectedCategories.includes(s))
                        ? "Odebrat"
                        : "Vybrat"}
                    </button>
                  </div>
                  <ul className="ml-4 mt-1 space-y-1">
                    {subs.map((sub) => (
                      <li key={sub}>
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={selectedCategories.includes(sub)}
                            onChange={() => toggleCat(sub)}
                          />
                          <span>
                            {sub.charAt(0).toUpperCase() + sub.slice(1)}
                          </span>
                        </label>
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
            <div className="mt-6 space-y-2">
              <button
                onClick={selectAll}
                className="w-full bg-pink-600 text-white py-2 rounded"
              >
                Vybrat vše
              </button>
              <button
                onClick={deselectAll}
                className="w-full bg-pink-200 text-pink-800 py-2 rounded"
              >
                Odebrat vše
              </button>
            </div>
          </aside>

          {/* Pravý panel – karty produktů */}
          <div className="flex flex-wrap items-start gap-6 justify-start">
            {filteredProducts.map((product) => (
              <div
                key={product.id}
                className="bg-white rounded-2xl shadow-lg overflow-hidden flex flex-col flex-shrink-0"
                style={{ width: 280 }}
              >
                <img
                  src={product.image}
                  alt={product.name}
                  className="w-full h-48 object-cover"
                />
                <div className="p-4 flex flex-col flex-grow">
                  <Link
                    to={`/shop/${product.name
                      .toLowerCase()
                      .replace(/\s+/g, "-")}`}
                    className="text-lg font-semibold mb-2 hover:underline"
                  >
                    {product.name}
                  </Link>
                  <p className="text-pink-700 mb-4">
                    {product.price.toFixed(2)} Kč
                  </p>
                  <button
                    onClick={() => addToCart(product)}
                    className="mt-auto bg-pink-600 text-white py-2 rounded-lg hover:bg-pink-700 transition"
                  >
                    Přidat do košíku
                  </button>
                </div>
              </div>
            ))}

            {filteredProducts.length === 0 && (
              <div className="w-full text-center text-pink-800 font-medium">
                Nenalezeny žádné produkty pro vybrané filtry.
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
