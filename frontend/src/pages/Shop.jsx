import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { useCart } from "../context/CartContext";

// ── pomocné mapy (beze změny) ────────────────────────────────────────────────
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
  "ostatní": "ostatní",
};
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
  ostatní: "Ostatní",
};

// ── absolutizace URL obrázků (to opravuje placeholdery) ──────────────────────
const API_BASE = `${window.location.protocol}//${window.location.hostname}:5000`;
function absoluteUploadUrl(u) {
  if (!u) return null;
  if (/^https?:\/\//i.test(u)) return u;                 // už je absolutní
  if (u.startsWith("/")) return `${API_BASE}${u}`;       // např. /static/uploads/a.jpg
  return `${API_BASE}/static/uploads/${u}`;              // jen název souboru
}
const toAlias = (name) => categoryAliases[name] || name;
const toGroup = (alias) => categoryGroups[alias] || "Ostatní";

export default function Shop() {
  const { addToCart } = useCart();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const urlCategory = params.get("category");

  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  // Načtení kategorií
  useEffect(() => {
    fetch("http://localhost:5000/api/categories/")
      .then((res) => res.json())
      .then((data) => {
        setCategories(data);
        const all = data.map((cat) => toAlias((cat.name || "").toLowerCase()));
        if (urlCategory && all.includes(urlCategory)) {
          setSelectedCategories([urlCategory]);
        } else {
          setSelectedCategories(all); // defaultně vybrat vše
        }
      })
      .catch((err) => console.error("Chyba při načítání kategorií:", err));
  }, [urlCategory]);

  // Načtení produktů + mapování na starý tvar (image, price, category.name)
  useEffect(() => {
    fetch("http://localhost:5000/api/products/")
      .then((res) => res.json())
      .then((data) => {
        const mapped = (data || []).map((p) => {
          const priceNumber =
            typeof p.price === "number"
              ? p.price
              : typeof p.price_czk === "number"
              ? p.price_czk
              : Number(p.price) || 0;

          return {
            ...p,
            image: absoluteUploadUrl(p.image_url || p.image), // ← FIX
            price: priceNumber,
            category: { name: p.category_name || "" },
          };
        });
        setProducts(mapped);
      })
      .catch((err) => console.error("Chyba načítání produktů:", err));
  }, []);

  const toggleCat = (cat) =>
    setSelectedCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );

  const selectAll = () => {
    const all = categories.map((cat) =>
      toAlias((cat.name || "").toLowerCase())
    );
    setSelectedCategories(all);
  };
  const deselectAll = () => setSelectedCategories([]);

  // Seskupení kategorií
  const groupedCategories = categories.reduce((acc, cat) => {
    const aliased = toAlias((cat.name || "").toLowerCase());
    const grp = toGroup(aliased);
    if (!acc[grp]) acc[grp] = [];
    acc[grp].push({ ...cat, alias: aliased });
    return acc;
  }, {});

  // Filtrování (původní logika)
  const filteredProducts = products.filter((p) => {
    const raw = p?.category?.name?.toLowerCase().trim() || "";
    const cat = toAlias(raw);
    const matchesCat = selectedCategories.includes(cat);
    const matchesText = (p.name || "")
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    return matchesCat && matchesText;
  });

  return (
    <section className="pt-24 pb-12 bg-gradient-to-br from-pink-300 to-pink-200 min-h-screen">
      <div className="mx-auto max-w-7xl px-4">
        <h2 className="text-4xl font-extrabold text-center mb-10">E-shop</h2>

        <div className="flex flex-wrap items-start gap-6">
          {/* Sidebar */}
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
                        const allAliases = cats.map((c) => c.alias);
                        const allSelected = cats.every((c) =>
                          selectedCategories.includes(c.alias)
                        );
                        if (allSelected) {
                          setSelectedCategories((prev) =>
                            prev.filter((c) => !allAliases.includes(c))
                          );
                        } else {
                          setSelectedCategories((prev) => [
                            ...new Set([...prev, ...allAliases]),
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

          {/* Produkty */}
          <div className="flex flex-wrap items-start gap-6 justify-start">
            {filteredProducts.map((product) => (
              <div
                key={product.id}
                className="bg-white rounded-2xl shadow-lg overflow-hidden flex flex-col flex-shrink-0"
                style={{ width: 280 }}
              >
                <img
                  src={product.image || "/placeholder.png"}
                  alt={product.name}
                  className="w-full h-48 object-cover"
                  onError={(e) => {
                    e.currentTarget.src = "/placeholder.png";
                  }}
                />
                <div className="p-4 flex flex-col flex-grow">
                  <Link
                    to={`/shop/${(product.name || "")
                      .toLowerCase()
                      .replace(/\s+/g, "-")}`}
                    className="text-lg font-semibold mb-2 hover:underline"
                  >
                    {product.name}
                  </Link>
                  <p className="text-pink-700 mb-4">
                    {(Number(product.price) || 0).toFixed(2)} Kč
                  </p>
                  <button
                    onClick={() =>
                      addToCart({
                        id: product.id,
                        name: product.name,
                        price: Number(product.price) || 0,
                      })
                    }
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
