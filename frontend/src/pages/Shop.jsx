import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { useCart } from "../context/CartContext";

// 🟩 Alias → pod jakým jménem se kategorie filtruje
const categoryAliases = {
  "pro maminku": "maminka",
  "pro tatínka": "tatínek",
  "pro babičku": "babička",
  "pro dědečka": "dědeček",
  "pro děti": "děti",
  "pro sestru": "sestra",
  "pro bratra": "bratr",
  "kamarádka": "kamarádka",
  "jen pro radost": "jen pro radost",
  "přátelství": "přátelství",
  "výročí": "výročí",
  "láska": "láska",
  "svatba": "svatba",
  "pro páry": "pro páry",
  "jméno": "jméno",
  "ostatní": "ostatní"
};

// 🟦 Alias → skupina (pro rozřazení do hlavních sekcí)
const categoryGroups = {
  maminka: "Rodina",
  tatínek: "Rodina",
  babička: "Rodina",
  dědeček: "Rodina",
  děti: "Rodina",
  sestra: "Rodina",
  bratr: "Rodina",
  svatba: "Svatba",
  "pro nevěstu": "Svatba",
  "pro ženicha": "Svatba",
  "pro svědky": "Svatba",
  "jen pro radost": "Dárky",
  jméno: "Dárky",
  přátelství: "Ostatní",
  láska: "Ostatní",
  výročí: "Ostatní",
  "pro páry": "Ostatní",
  kamarádka: "Ostatní",
  ostatní: "Ostatní"
};

export default function Shop() {
  const { addToCart } = useCart();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const urlCategory = params.get("category");

  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  // 🔁 Načtení kategorií z API
  useEffect(() => {
    fetch("http://localhost:5000/api/categories/")
      .then((res) => res.json())
      .then((data) => {
        setCategories(data);
        const all = data.map((cat) => alias(cat.name.toLowerCase()));
        if (urlCategory && all.includes(urlCategory)) {
          setSelectedCategories([urlCategory]);
        } else {
          setSelectedCategories(all);
        }
      })
      .catch((err) => console.error("Chyba při načítání kategorií:", err));
  }, [urlCategory]);

  // 🔁 Načtení produktů
  useEffect(() => {
    fetch("http://localhost:5000/api/products/")
      .then((res) => res.json())
      .then((data) => setProducts(data))
      .catch((err) => console.error("Chyba načítání produktů:", err));
  }, []);

  // ⛏️ Pomocné funkce
  const alias = (name) => categoryAliases[name] || name;
  const group = (alias) => categoryGroups[alias] || "Ostatní";

  const toggleCat = (cat) =>
    setSelectedCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );

  const selectAll = () => {
    const all = categories.map((cat) => alias(cat.name.toLowerCase()));
    setSelectedCategories(all);
  };

  const deselectAll = () => setSelectedCategories([]);

  // 🗂️ Dynamické seskupení podle skupin
  const groupedCategories = categories.reduce((acc, cat) => {
    const aliased = alias(cat.name.toLowerCase());
    const grp = group(aliased);
    if (!acc[grp]) acc[grp] = [];
    acc[grp].push({ ...cat, alias: aliased });
    return acc;
  }, {});

  // 🔍 Filtrování produktů
  const filteredProducts = products.filter((p) => {
    const raw = p.category?.name?.toLowerCase().trim() || "";
    const cat = alias(raw);
    return (
      selectedCategories.includes(cat) &&
      p.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <section className="pt-24 pb-12 bg-gradient-to-br from-pink-300 to-pink-200 min-h-screen">
      <div className="mx-auto max-w-7xl px-4">
        <h2 className="text-4xl font-extrabold text-center mb-10">E-shop</h2>

        <div className="flex flex-wrap items-start gap-6">
          {/* 📂 Levý panel – KATEGORIE */}
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
              {Object.entries(groupedCategories).map(([groupName, cats]) => (
                <li key={groupName}>
                  <div className="flex justify-between items-center">
                    <strong>{groupName.toUpperCase()}</strong>
                    <button
                      onClick={() => {
                        const allSelected = cats.every((c) =>
                          selectedCategories.includes(c.alias)
                        );
                        if (allSelected) {
                          setSelectedCategories((prev) =>
                            prev.filter((c) => !cats.map((c) => c.alias).includes(c))
                          );
                        } else {
                          setSelectedCategories((prev) => [
                            ...new Set([
                              ...prev,
                              ...cats.map((c) => c.alias)
                            ])
                          ]);
                        }
                      }}
                      className="text-sm hover:underline"
                    >
                      {cats.every((c) => selectedCategories.includes(c.alias))
                        ? "Odebrat"
                        : "Vybrat"}
                    </button>
                  </div>
                  <ul className="ml-4 mt-1 space-y-1">
                    {cats.map((cat) => (
                      <li key={cat.id}>
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={selectedCategories.includes(cat.alias)}
                            onChange={() => toggleCat(cat.alias)}
                          />
                          <span>{cat.name}</span>
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

          {/* 🛍️ Pravý panel – PRODUKTY */}
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
