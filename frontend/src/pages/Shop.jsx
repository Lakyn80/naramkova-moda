import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useCart } from "../context/CartContext";

// Kategorie – statický strom (pro filtraci)
const categoryTree = {
  rodina: ["maminka", "děti", "tatínek", "dědeček", "babička", "bratr", "sestra"],
  svatba: ["svatba", "pro nevěstu", "pro ženicha", "pro svědky"],
  dárky: ["jen pro radost", "jméno", "ostatní"],
  ostatní: ["přátelství", "láska", "výročí", "pro páry", "kamarádka"]
};

// Mapování názvů z API na interní názvy v Reactu
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
  "svatba": "svatba",
  "pro nevěstu": "pro nevěstu",
  "pro ženicha": "pro ženicha",
  "pro svědky": "pro svědky"
};

export default function Shop() {
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
  const { addToCart } = useCart();
  const navigate = useNavigate();

  // Načtení produktů z API
  useEffect(() => {
    fetch("/api/products/")
      .then((res) => res.json())
      .then((data) => setProducts(data))
      .catch((err) => console.error("Chyba při načítání produktů:", err));
  }, []);

  // Sleduj změnu URL parametru `category`
  useEffect(() => {
    if (urlCategory && allSubcategories.includes(urlCategory)) {
      setSelectedCategories([urlCategory]);
    }
  }, [urlCategory]);

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

  // 🔍 Filtrace produktů podle vybraných kategorií a hledaného názvu
  const filteredProducts = products.filter((product) => {
    const rawCategory = product.category?.name.toLowerCase().trim() || "";
    const normalized = categoryAliases[rawCategory] || rawCategory;

    return (
      selectedCategories.includes(normalized) &&
      product.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <section className="pt-24 pb-12 px-3 sm:px-4 bg-gradient-to-br from-pink-300 via-white via-30% to-pink-200 min-h-screen">
      <h2 className="text-4xl sm:text-5xl font-extrabold text-center text-transparent bg-gradient-to-r from-pink-800 via-pink-500 to-pink-800 bg-clip-text animate-gradient-x drop-shadow-lg mb-10">
        E-shop
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
        {/* Levý panel – Kategorie */}
        <aside className="bg-white/70 p-4 rounded-2xl shadow lg:col-span-1">
          <h3 className="text-lg sm:text-xl font-semibold mb-4 text-pink-800">
            Kategorie
          </h3>

          <input
            type="text"
            placeholder="Hledat produkt..."
            className="w-full px-3 py-2 mb-4 border rounded-md"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />

          <ul className="space-y-4 text-sm sm:text-base">
            {Object.entries(categoryTree).map(([mainCategory, subcats]) => (
              <li key={mainCategory}>
                <div className="flex justify-between items-center">
                  <strong className="text-pink-900">{mainCategory.toUpperCase()}</strong>
                  <button
                    onClick={() => {
                      const subs = subcats.length > 0 ? subcats : [mainCategory];
                      const allSelected = subs.every((c) => selectedCategories.includes(c));
                      if (allSelected) {
                        setSelectedCategories(
                          selectedCategories.filter((c) => !subs.includes(c))
                        );
                      } else {
                        setSelectedCategories([
                          ...new Set([...selectedCategories, ...subs]),
                        ]);
                      }
                    }}
                    className="text-sm text-pink-700 hover:underline"
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
                          className="accent-pink-700"
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
              className="w-full bg-pink-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-pink-700 transition"
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
        <div className="lg:col-span-3 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6 content-start">
          {filteredProducts.map((product, index) => (
            <div
              key={index}
              className="bg-white/60 backdrop-blur-md rounded-2xl shadow-xl overflow-hidden text-center p-4 hover:shadow-2xl transition-all duration-300 h-full flex flex-col justify-between"
            >
              <img
                src={product.image}
                alt={product.name}
                className="w-full h-48 object-cover rounded-xl"
              />
              <Link
                to={`/shop/${product.name.toLowerCase().replace(/\s+/g, "-")}`}
                className="block mt-4 text-lg font-semibold text-pink-800 hover:underline"
              >
                {product.name}
              </Link>
              <p className="text-sm text-pink-700 mt-1">{product.price} Kč</p>
              <button
                onClick={() => addToCart(product)}
                className="mt-2 bg-pink-700 hover:bg-pink-800 text-white py-1 px-3 rounded text-sm transition"
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
