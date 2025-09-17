import React, { useState, useEffect, forwardRef, useImperativeHandle } from "react";
import { Link, useLocation } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { emojify } from "../utils/emojify";
import { slugify } from "../utils/slugify"; // ✅ přidáno

// aliasy kategorií (ponecháno pro kompatibilitu)
const categoryAliases = {
  maminka: "maminka",
  babička: "babička",
  bratr: "bratr",
  sestra: "sestra",
  děti: "děti",
  svatba: "svatba",
  "jen pro radost": "jen pro radost",
  tatínek: "tatínek",
  dědeček: "dědeček",
  kamarádka: "kamarádka",
  láska: "láska",
  "pro děti": "pro děti",
  "pro páry": "pro páry",
  výročí: "výročí",
  přátelství: "přátelství",
};

const toAlias = (name) => categoryAliases[name] || name;

// === API base (LOCK na 5050) ===
// const API_BASE = `${window.location.protocol}//${window.location.hostname}:5050`;
const API_BASE = import.meta.env.VITE_API_BASE; // ✅ jen z env, žádný host/port

function absoluteUploadUrl(u) {
  if (!u) return null;
  if (/^https?:\/\//i.test(u)) return u;
  if (u.startsWith("/")) return u; // ✅ nepřidávej API prefix ke statice
  return `/static/uploads/${u}`; // ✅ statika není pod /api
}

// page size = 8 řádků × 3 sloupce
const COLS = 3;
const ROWS = 8;
const PAGE_SIZE = COLS * ROWS;

// pomocná funkce pro pěkné stránkování s elipsami
function getPageList(current, total) {
  const pages = [];
  const delta = 1; // sousedé kolem aktuální stránky
  const range = [];
  const rangeWithDots = [];
  let l;

  // vždy ukážeme 1, poslední, aktuální ±1 a „kotvy“ 2 a total-1 podle potřeby
  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || (i >= current - delta && i <= current + delta)) {
      range.push(i);
    }
  }

  // vložení teček
  for (let i of range) {
    if (l) {
      if (i - l === 2) {
        rangeWithDots.push(l + 1);
      } else if (i - l > 2) {
        rangeWithDots.push("…");
      }
    }
    rangeWithDots.push(i);
    l = i;
  }

  // jemné rozšíření na začátku/konce pro lepší UX
  if (rangeWithDots[1] === 3) rangeWithDots.splice(1, 1, 2);
  if (rangeWithDots[rangeWithDots.length - 2] === total - 2)
    rangeWithDots.splice(rangeWithDots.length - 2, 1, total - 1);

  return rangeWithDots;
}

const Shop = forwardRef(function Shop(_, ref) {
  const { addToCart } = useCart();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const urlCategory = params.get("category");

  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  // pagination
  const [page, setPage] = useState(1);

  useImperativeHandle(ref, () => ({
    scrollIntoView: () => {
      const el = document.getElementById("shop-root");
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    },
  }));

  useEffect(() => {
    // fetch(`${API_BASE}/api/categories/`)
    fetch(`${API_BASE}/categories/`) // ✅ base je /api, proto bez dalšího /api
      .then((res) => res.json())
      .then((data) => {
        setCategories(data);
        const all = data.map((cat) => toAlias((cat.name || "").toLowerCase()));
        if (urlCategory && all.includes(urlCategory)) {
          setSelectedCategories([urlCategory]);
        } else {
          setSelectedCategories(all);
        }
      })
      .catch((err) => console.error("Chyba při načítání kategorií:", err));
  }, [urlCategory]);

  useEffect(() => {
    // fetch(`${API_BASE}/api/products/`)
    fetch(`${API_BASE}/products/`) // ✅ base je /api, proto bez dalšího /api
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
            image: absoluteUploadUrl(p.image_url || p.image),
            price: priceNumber,
            stock: Number(p.stock ?? 0), // ✅ přenést stock
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
    const all = categories.map((cat) => toAlias((cat.name || "").toLowerCase()));
    setSelectedCategories(all);
  };

  const deselectAll = () => setSelectedCategories([]);

  // groupy kategorií (podpora group z backendu)
  const groupedCategories = categories.reduce((acc, cat) => {
    const aliased = toAlias((cat.name || "").toLowerCase());
    const grp = cat.group || "Ostatní";
    if (!acc[grp]) acc[grp] = [];
    acc[grp].push({ ...cat, alias: aliased });
    return acc;
  }, {});

  const filteredProducts = products.filter((p) => {
    const raw = p?.category?.name?.toLowerCase().trim() || "";
    const cat = toAlias(raw);
    const matchesCat = selectedCategories.includes(cat);
    const matchesText = (p.name || "")
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    return matchesCat && matchesText;
  });

  // reset stránkování při změně filtru/hladání
  useEffect(() => {
    setPage(1);
  }, [searchTerm, selectedCategories]);

  const total = filteredProducts.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const start = (page - 1) * PAGE_SIZE;
  const pageItems = filteredProducts.slice(start, start + PAGE_SIZE);

  // pro status v patičce stránkování
  const shownFrom = total === 0 ? 0 : start + 1;
  const shownTo = Math.min(start + PAGE_SIZE, total);

  return (
    <section
      id="shop-root"
      className="pt-24 pb-12 bg-gradient-to-br from-[#3b0764] via-[#9d174d] to-[#f9a8d4] min-h-screen text-white"
    >
      <div className="mx-auto max-w-7xl px-4">
        <h2 className="text-4xl font-extrabold text-center mb-10">E-shop</h2>

        <div className="flex flex-col md:flex-row gap-8 items-start">
          {/* Sidebar */}
          <aside className="w-full md:w-1/4 bg-white/10 backdrop-blur-sm p-4 rounded-2xl shadow-lg">
            <h3 className="text-lg font-semibold mb-4">Kategorie</h3>
            <input
              type="text"
              placeholder="Hledat produkt..."
              className="w-full mb-4 px-3 py-2 border rounded text-black"
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
                            prev.filter((c) => !allAliases.includes(c)
                          ));
                        } else {
                          setSelectedCategories((prev) => [
                            ...new Set([...prev, ...allAliases]),
                          ]);
                        }
                      }}
                      className="text-sm text-pink-200 hover:underline"
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

          {/* Produkty + stránkování */}
          <main className="flex-1">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {pageItems.map((product) => {
                const inStock = Number(product.stock ?? 0) > 0;

                // ✅ NOVÉ: hezčí badge podle množství
                const badgeClass = !inStock
                  ? // vyprodáno
                    "bg-gradient-to-r from-rose-500 to-rose-700 text-white shadow-lg shadow-rose-700/30 ring-1 ring-white/10"
                  : product.stock <= 5
                  ? // nízký stav – amber + jemný puls
                    "bg-gradient-to-r from-amber-400 to-amber-600 text-black shadow-lg shadow-amber-700/20 ring-1 ring-white/10 animate-pulse"
                  : // dostatek – emerald/green
                    "bg-gradient-to-r from-emerald-400 to-green-600 text-white shadow-lg shadow-emerald-700/30 ring-1 ring-white/10";

                return (
                  <div
                    key={product.id}
                    className="bg-white/10 backdrop-blur-sm rounded-2xl shadow-lg overflow-hidden flex flex-col"
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
                      <div className="flex items-start justify-between gap-2">
                        {/* ✅ Sjednocení s Galerií: používáme slug */}
                        <Link
                          to={`/shop/${slugify(product.name)}`}
                          className="text-lg font-semibold mb-2 hover:underline text-white"
                        >
                          {emojify(product.name)}
                        </Link>

                        {/* ✅ jen vizuální úprava badge */}
                        <span
                          className={`text-[11px] px-2.5 py-1 rounded-full whitespace-nowrap ${badgeClass}`}
                          title={inStock ? `Skladem: ${product.stock}` : "Vyprodáno"}
                        >
                          {inStock ? `Skladem: ${product.stock}` : "Vyprodáno"}
                        </span>
                      </div>

                      <p className="text-pink-200 mb-4">
                        {(Number(product.price) || 0).toFixed(2)} Kč
                      </p>
                      <button
                        onClick={() =>
                          inStock &&
                          addToCart({
                            id: product.id,
                            name: product.name,
                            price: Number(product.price) || 0,
                            image: product.image,
                            stock: product.stock, // ✅ posíláme do košíku informaci o skladu
                          })
                        }
                        disabled={!inStock}
                        className={`mt-auto text-white py-2 rounded-lg transition ${
                          inStock ? "bg-pink-600 hover:bg-pink-700" : "bg-gray-300 cursor-not-allowed"
                        }`}
                      >
                        {inStock ? "Přidat do košíku" : "Vyprodáno"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {filteredProducts.length === 0 && (
              <div className="text-center text-pink-200 font-medium mt-6">
                Nenalezeny žádné produkty pro vybrané filtry.
              </div>
            )}

            {/* Hezčí stránkování (jen dole), 8 řádků na stránku zachováno */}
            {totalPages > 1 && (
              <div className="mt-10">
                <div className="flex flex-col items-center gap-3">
                  {/* status řádku */}
                  <div className="text-sm text-pink-100/90">
                    Zobrazeno <span className="font-semibold">{shownFrom}</span>
                    {"–"}
                    <span className="font-semibold">{shownTo}</span> z{" "}
                    <span className="font-semibold">{total}</span>
                  </div>

                  {/* ovládací lišta */}
                  <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-2 py-1 shadow-lg">
                    <button
                      disabled={page === 1}
                      onClick={() => setPage(1)}
                      className="px-3 py-2 rounded-full bg-white/0 hover:bg-white/15 disabled:opacity-40 disabled:hover:bg-transparent transition"
                      aria-label="První stránka"
                      title="První stránka"
                    >
                      «
                    </button>
                    <button
                      disabled={page === 1}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      className="px-3 py-2 rounded-full bg-white/0 hover:bg-white/15 disabled:opacity-40 disabled:hover:bg-transparent transition"
                      aria-label="Předchozí"
                      title="Předchozí"
                    >
                      ‹
                    </button>

                    {getPageList(page, totalPages).map((n, idx) =>
                      n === "…" ? (
                        <span
                          key={`dots-${idx}`}
                          className="px-2 select-none text-pink-100/70"
                        >
                          …
                        </span>
                      ) : (
                        <button
                          key={n}
                          onClick={() => setPage(n)}
                          className={`px-3 py-2 rounded-full transition ${
                            n === page
                              ? "bg-pink-600 text-white shadow-md"
                              : "bg-white/0 hover:bg-white/15"
                          }`}
                          aria-current={n === page ? "page" : undefined}
                          title={`Stránka ${n}`}
                        >
                          {n}
                        </button>
                      )
                    )}

                    <button
                      disabled={page === totalPages}
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      className="px-3 py-2 rounded-full bg-white/0 hover:bg-white/15 disabled:opacity-40 disabled:hover:bg-transparent transition"
                      aria-label="Další"
                      title="Další"
                    >
                      ›
                    </button>
                    <button
                      disabled={page === totalPages}
                      onClick={() => setPage(totalPages)}
                      className="px-3 py-2 rounded-full bg-white/0 hover:bg-white/15 disabled:opacity-40 disabled:hover:bg-transparent transition"
                      aria-label="Poslední stránka"
                      title="Poslední stránka"
                    >
                      »
                    </button>
                  </div>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </section>
  );
});

export default Shop;
