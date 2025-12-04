import React, { useEffect, useState, useMemo } from "react";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";
import Thumbnails from "yet-another-react-lightbox/plugins/thumbnails";
import "yet-another-react-lightbox/plugins/thumbnails.css";
import Zoom from "yet-another-react-lightbox/plugins/zoom";
import { useParams } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { slugify } from "../utils/slugify";
import { emojify } from "../utils/emojify";

const API_BASE = `${window.location.origin}/api`;

// ✅ emoji vykreslí mimo gradient
function renderEmojiSafe(text) {
  const s = String(text ?? "");
  const parts = s.split(/([\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}])/gu);
  const isEmoji = (t) => /^[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]$/u.test(t);
  return parts.map((chunk, i) =>
    isEmoji(chunk) ? <span key={`e${i}`} className="text-white">{chunk}</span> : <span key={`t${i}`}>{chunk}</span>
  );
}

export default function ProductDetail() {
  const { slug } = useParams();
  const { addToCart } = useCart();

  const [product, setProduct] = useState(null);
  const [photoIndex, setPhotoIndex] = useState(0);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/products/`);
        const data = await res.json();

        const found = (data || []).find((p) => slugify(p?.name || "") === slug);
        if (!found) {
          setProduct(null);
          return;
        }

        const price =
          typeof found.price === "number"
            ? found.price
            : typeof found.price_czk === "number"
            ? found.price_czk
            : Number(found.price) || 0;

        const mediaUrls = Array.isArray(found.media) ? found.media.filter(Boolean) : [];
        const images = [found.image_url, ...mediaUrls]
          .filter(Boolean)
          .filter((v, i, a) => a.indexOf(v) === i);

        // 💡 doplněn stock (default 1 pokud BE neposlal)
        const stockNumber = Number(found.stock ?? 1);

        setProduct({
          ...found,
          stock: Number.isFinite(stockNumber) && stockNumber >= 0 ? stockNumber : 1,
          price,
          image_url: found.image_url,
          images,
        });
        setPhotoIndex(0);
        setIsOpen(false);
      } catch (err) {
        console.error("Chyba při načítání produktu:", err);
      }
    })();
  }, [slug]);

  const handleAddToCart = () => {
    if (!product || Number(product.stock) === 0) return;
    addToCart({
      id: product.id,
      name: product.name,
      price: product.price,
      quantity: 1,
      image: product.image_url,
    });
  };

  if (!product) {
    return (
      <section className="pt-28 pb-12 bg-gradient-to-br from-pink-300 to-pink-200 min-h-screen flex items-center justify-center">
        <div className="text-center text-lg text-pink-900">
          Produkt nenalezen.
        </div>
      </section>
    );
  }

  const slides = product.images.map((src) => ({ src }));
  const out = Number(product.stock) === 0;

  return (
    <section className="pt-28 pb-12 bg-gradient-to-br from-pink-300 to-pink-200 min-h-screen">
      <div className="container mx-auto max-w-4xl px-4">
        <div className="bg-white/20 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-white/40">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
            {/* Obrázky */}
            <div className="space-y-4 relative">
              {/* Odznak skladu v detailu */}
              <div className="absolute top-2 left-2 z-10">
                {out ? (
                  <span className="px-2 py-1 text-xs font-semibold rounded bg-red-600/90 text-white">
                    Vyprodáno
                  </span>
                ) : (
                  <span className="px-2 py-1 text-xs font-semibold rounded bg-emerald-600/90 text-white">
                    Skladem: {product.stock}
                  </span>
                )}
              </div>

              <img
                src={product.images[photoIndex]}
                alt={product.name}
                className="w-full h-[260px] sm:h-[300px] md:h-[360px] object-cover rounded-xl shadow-lg cursor-pointer transition-transform duration-300 hover:scale-[1.02]"
                onClick={() => setIsOpen(true)}
              />
              <div className="flex gap-2 flex-wrap justify-center sm:justify-start">
                {product.images.map((img, i) => (
                  <img
                    key={i}
                    src={img}
                    alt={`${product.name} ${i + 1}`}
                    onClick={() => setPhotoIndex(i)}
                    className={`h-16 w-16 sm:h-20 sm:w-20 object-cover rounded-lg cursor-pointer border-2 ${
                      photoIndex === i ? "border-pink-500 shadow-lg" : "border-transparent"
                    } transition duration-300 hover:scale-105`}
                  />
                ))}
              </div>
            </div>

            {/* Popis */}
            <div className="flex flex-col justify-center">
              <h2 className="text-2xl sm:text-3xl font-extrabold bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent drop-shadow-lg">
                {renderEmojiSafe(emojify(product.name))}
              </h2>
              <p className="text-xl font-semibold text-pink-700 mt-2 drop-shadow-sm">
                {product.price.toFixed(2)} Kč
              </p>
              <p className="mt-3 text-base sm:text-lg text-gray-800 leading-relaxed">
                {emojify(product.description || "Detail produktu zde.")}
              </p>

              <button
                onClick={handleAddToCart}
                disabled={out}
                className={`mt-6 py-2 px-5 rounded-lg shadow-lg transition-transform transform hover:-translate-y-0.5 ${
                  out
                    ? "bg-gray-400 cursor-not-allowed text-white"
                    : "bg-gradient-to-r from-pink-600 to-pink-700 hover:from-pink-700 hover:to-pink-800 text-white"
                }`}
                title={out ? "Produkt je vyprodaný" : "Přidat do košíku"}
              >
                {out ? "Vyprodáno" : "Přidat do košíku"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {isOpen && (
        <Lightbox
          open={isOpen}
          close={() => setIsOpen(false)}
          slides={slides}
          index={photoIndex}
          plugins={[Thumbnails, Zoom]}
          on={{ view: ({ index }) => setPhotoIndex(index) }}
        />
      )}
    </section>
  );
}
