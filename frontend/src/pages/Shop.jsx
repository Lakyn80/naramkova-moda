import React, {
  useState,
  useEffect,
  forwardRef,
  useImperativeHandle,
  useMemo,
  useCallback,
} from "react";
import { Link, useLocation, useParams, useSearchParams } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { emojify } from "../utils/emojify";
import { slugify } from "../utils/slugify";

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

const API_BASE = import.meta.env.VITE_API_BASE || `${window.location.origin}/api`;

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
  const delta = 1; // sousedící kolem aktuální stránky
  const range = [];
  const rangeWithDots = [];
  let l;

  // vždy ukážeme 1, poslední, aktuální ±1 a případně 2 a total-1 podle potřeby
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

const Shop = forwardRef(function Shop({ categorySlug }, ref) {
  const { addToCart } = useCart();
  const params = useParams();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const routeCategorySlug = params?.slug;
  const forcedCategory = categorySlug || routeCategorySlug || null;
  const wristSizeParam = searchParams.get("wrist_size") || searchParams.get("wrist") || "";

  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("");
  const [wristFilter, setWristFilter] = useState("");

  // pagination
  const [page, setPage] = useState(1);

  const normalizeList = useCallback(
    (arr = []) => Array.from(new Set((arr || []).filter(Boolean))),
    []
  );

  useImperativeHandle(ref, () => ({
    scrollIntoView: () => {
      const el = document.getElementById("shop-root");
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    },
  }));

  useEffect(() => {
    fetch(`${API_BASE}/categories/`) // ✅ base je /api, proto bez dalšího /api
      .then((res) => res.json())
      .then((data) => {
        const mapped = (data || []).map((cat) => {
          const alias = toAlias((cat.name || "").toLowerCase());
          const slug = cat.slug || slugify(cat.name || "");
          const key = slug ? `${slug}-${cat.id || ""}` : `${alias}-${cat.id || ""}`;
          return { ...cat, alias, slug, key };
        });
        setCategories(mapped);
      })
      .catch((err) => console.error("Chyba při načtení kategorií:", err));
  }, []);

  useEffect(() => {
    const mapProduct = (p) => {
      const priceNumber =
        typeof p.price === "number"
          ? p.price
          : typeof p.price_czk === "number"
          ? p.price_czk
          : Number(p.price) || 0;

      const categorySlug = p.category_slug || slugify(p.category_name || "");
      const categoryKeyRaw =
        categorySlug || toAlias((p.category_name || "").toLowerCase());
      const categoryKey = `${categoryKeyRaw}-${p.category_id || p.id || ""}`;
      const variants = Array.isArray(p.variants)
        ? p.variants.map((v) => ({
            ...v,
            image_url: absoluteUploadUrl(v.image_url || v.image),
            media: Array.isArray(v.media)
              ? v.media.map((m) => ({
                  ...m,
                  image_url: absoluteUploadUrl(m.image_url || m.image),
                }))
              : [],
          }))
        : [];

      return {
        ...p,
        image: absoluteUploadUrl(p.image_url || p.image),
        price: priceNumber,
        stock: Number(p.stock ?? 0),
        category: { name: p.category_name || "", slug: categorySlug || categoryKey },
        category_key: categoryKey,
        media: Array.isArray(p.media) ? p.media.map((m) => absoluteUploadUrl(m)) : [],
        variants,
      };
    };

    const qs = wristSizeParam ? `?wrist_size=${encodeURIComponent(wristSizeParam)}` : "";
    fetch(`${API_BASE}/products/${qs}`)
      .then((res) => res.json())
      .then((data) => setProducts((data || []).map(mapProduct)))
      .catch((err) => console.error("Chyba načtení produktů:", err));
  }, [wristSizeParam]);

  useEffect(() => {
    const rawCats = searchParams.get("categories");
    const parsedCats =
      rawCats !== null
        ? rawCats
            .split(",")
            .map((v) => v.trim())
            .filter(Boolean)
        : null;
    const nextCats =
      parsedCats !== null
        ? parsedCats
        : forcedCategory
        ? [forcedCategory]
        : [];

    setSelectedCategories(normalizeList(nextCats));
    setSearchTerm(searchParams.get("q") || "");
    setSortBy(searchParams.get("sort") || "");
    setWristFilter(searchParams.get("wrist") || searchParams.get("wrist_size") || "");
    const pageParam = parseInt(searchParams.get("page") || "1", 10);
    setPage(Number.isFinite(pageParam) && pageParam > 0 ? pageParam : 1);
  }, [forcedCategory, normalizeList, searchParams]);

  const applyFilters = useCallback(
    (opts = {}) => {
      const cats =
        opts.categories !== undefined
          ? normalizeList(opts.categories)
          : normalizeList(selectedCategories);
      const qVal = opts.searchTerm !== undefined ? opts.searchTerm : searchTerm;
      const sortVal = opts.sortBy !== undefined ? opts.sortBy : sortBy;
      const wristVal = opts.wristFilter !== undefined ? opts.wristFilter : wristFilter;
      const pageVal = opts.page !== undefined ? opts.page : page;

      const params = new URLSearchParams();
      if (cats.length) {
        params.set("categories", cats.join(","));
      } else {
        params.set("categories", "");
      }
      if (qVal) params.set("q", qVal);
      if (sortVal) params.set("sort", sortVal);
      if (wristVal) params.set("wrist", wristVal);
      if (pageVal > 1) params.set("page", String(pageVal));

      setSelectedCategories(cats);
      setSearchTerm(qVal);
      setSortBy(sortVal);
      setWristFilter(wristVal);
      setPage(pageVal);
      setSearchParams(params, { replace: true });
    },
    [normalizeList, page, searchTerm, selectedCategories, setSearchParams, sortBy, wristFilter]
  );

  const toggleCat = (cat) => {
    const next = selectedCategories.includes(cat)
      ? selectedCategories.filter((c) => c !== cat)
      : [...selectedCategories, cat];
    applyFilters({ categories: next, page: 1 });
  };

  const selectAll = () => applyFilters({ categories: [], searchTerm: "", wristFilter: "", page: 1 });

  const deselectAll = () =>
    applyFilters({ categories: [], searchTerm: "", wristFilter: "", page: 1 });

  useEffect(() => {
    const url = `${location.pathname}${location.search || ""}` || "/shop";
    sessionStorage.setItem("lastShopUrl", url);
  }, [location.pathname, location.search]);

  const allWristSizes = useMemo(() => {
    const sizes = [];
    products.forEach((p) => {
      (p.variants || []).forEach((v) => {
        if (v.wrist_size) {
          sizes.push(v.wrist_size);
        }
      });
    });
    return Array.from(new Set(sizes.filter(Boolean))).sort();
  }, [products]);

  // groupy kategorií (podpora group z backendu)
  const groupedCategories = categories.reduce((acc, cat) => {
    const grp = cat.group || "Ostatní";
    if (!acc[grp]) acc[grp] = [];
    acc[grp].push(cat);
    return acc;
  }, {});

  const filteredProducts = products.filter((p) => {
    const catKey = p.category_key || "";
    const matchesCat =
      !selectedCategories.length ||
      !catKey ||
      selectedCategories.includes(catKey) ||
      !categories.length;
    const matchesText = (p.name || "").toLowerCase().includes(searchTerm.toLowerCase());
    const matchesWrist =
      !wristFilter ||
      (Array.isArray(p.variants) &&
        p.variants.some(
          (v) => (v.wrist_size || "").toLowerCase() === wristFilter.toLowerCase()
        ));
    return matchesCat && matchesText && matchesWrist;
  });

  const sortedProducts = useMemo(() => {
    const list = [...filteredProducts];
    switch (sortBy) {
      case "price_asc":
        return list.sort((a, b) => (Number(a.price) || 0) - (Number(b.price) || 0));
      case "price_desc":
        return list.sort((a, b) => (Number(b.price) || 0) - (Number(a.price) || 0));
      case "name_asc":
        return list.sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));
      case "name_desc":
        return list.sort((a, b) => String(b.name || "").localeCompare(String(a.name || "")));
      default:
        return list;
    }
  }, [filteredProducts, sortBy]);

  // reset stránkování při změně filtru/hledání
  const total = sortedProducts.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const start = (page - 1) * PAGE_SIZE;
  const pageItems = sortedProducts.slice(start, start + PAGE_SIZE);

  // pro status v patičce stránkování
  const shownFrom = total === 0 ? 0 : start + 1;
  const shownTo = Math.min(start + PAGE_SIZE, total);

  useEffect(() => {
    if (page > totalPages) {
      applyFilters({ page: totalPages });
    }
  }, [applyFilters, page, totalPages]);

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
              onChange={(e) => applyFilters({ searchTerm: e.target.value, page: 1 })}
            />
            <ul className="space-y-4 text-sm">
              {Object.entries(groupedCategories).map(([groupName, cats]) => (
                <li key={groupName}>
                  <div className="flex justify-between items-center">
                    <strong>{groupName.toUpperCase()}</strong>
                    <button
                      onClick={() => {
                        const allKeys = cats.map((c) => c.key);
                        const allSelected = cats.every((c) => selectedCategories.includes(c.key));
                        const next = allSelected
                          ? selectedCategories.filter((c) => !allKeys.includes(c))
                          : Array.from(new Set([...selectedCategories, ...allKeys]));
                        applyFilters({ categories: next, page: 1 });
                      }}
                      className="text-sm text-pink-200 hover:underline"
                    >
                      {cats.every((c) => selectedCategories.includes(c.key)) ? "Odebrat" : "Vybrat"}
                    </button>
                  </div>
                  <ul className="ml-4 mt-1 space-y-1">
                    {cats.map((cat) => (
                      <li key={cat.id}>
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={selectedCategories.includes(cat.key)}
                            onChange={() => toggleCat(cat.key)}
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
              {allWristSizes.length > 0 && (
                <div className="pt-2 space-y-1">
                  <label className="block text-sm font-semibold">Obvod</label>
                  <select
                    value={wristFilter}
                    onChange={(e) => applyFilters({ wristFilter: e.target.value, page: 1 })}
                    className="w-full px-3 py-2 border rounded text-black"
                  >
                    <option value="">Všechny obvody</option>
                    {allWristSizes.map((w) => (
                      <option key={w} value={w}>
                        {w}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div className="pt-2 space-y-1">
                <label className="block text-sm font-semibold">Řazení</label>
                <select
                  value={sortBy}
                  onChange={(e) => applyFilters({ sortBy: e.target.value, page: 1 })}
                  className="w-full px-3 py-2 border rounded text-black"
                >
                  <option value="">Dle výchozího</option>
                  <option value="price_asc">Cena: od nejnižší</option>
                  <option value="price_desc">Cena: od nejvyšší</option>
                  <option value="name_asc">Název: A -&gt; Z</option>
                  <option value="name_desc">Název: Z -&gt; A</option>
                </select>
              </div>
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
                        {/* ✅ Sjednoceno s Galerií: používáme slug */}
                    <Link
                      to={{
                        pathname: `/shop/${slugify(product.name)}`,
                        search: location.search || undefined,
                        state: { from: `${location.pathname}${location.search}` || "/shop" },
                      }}
                      onClick={() => {
                        const url = `${location.pathname}${location.search || ""}` || "/shop";
                        sessionStorage.setItem("lastShopUrl", url);
                      }}
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
                    {" "}
                    <span className="font-semibold">{shownTo}</span> z{" "}
                    <span className="font-semibold">{total}</span>
                  </div>

                  {/* ovládací lišta */}
                  <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-2 py-1 shadow-lg">
                    <button
                      disabled={page === 1}
                      onClick={() => applyFilters({ page: 1 })}
                      className="px-3 py-2 rounded-full bg-white/0 hover:bg-white/15 disabled:opacity-40 disabled:hover:bg-transparent transition"
                      aria-label="První stránka"
                      title="První stránka"
                    >
                      «
                    </button>
                    <button
                      disabled={page === 1}
                      onClick={() => applyFilters({ page: Math.max(1, page - 1) })}
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
                          onClick={() => applyFilters({ page: n })}
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
                      onClick={() => applyFilters({ page: Math.min(totalPages, page + 1) })}
                      className="px-3 py-2 rounded-full bg-white/0 hover:bg-white/15 disabled:opacity-40 disabled:hover:bg-transparent transition"
                      aria-label="Další"
                      title="Další"
                    >
                      ›
                    </button>
                    <button
                      disabled={page === totalPages}
                      onClick={() => applyFilters({ page: totalPages })}
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
