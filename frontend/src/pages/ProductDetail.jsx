import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useCart } from "../context/CartContext";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";
import Thumbnails from "yet-another-react-lightbox/plugins/thumbnails";
import "yet-another-react-lightbox/plugins/thumbnails.css";
import Zoom from "yet-another-react-lightbox/plugins/zoom";

const API_BASE = `${window.location.protocol}//${window.location.hostname}:5000`;
function absoluteUploadUrl(u) {
  if (!u) return null;
  if (/^https?:\/\//i.test(u)) return u;
  if (u.startsWith("/")) return `${API_BASE}${u}`;
  return `${API_BASE}/static/uploads/${u}`;
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
        const res = await fetch("http://localhost:5000/api/products/");
        const data = await res.json();

        const found = (data || []).find(
          (p) => (p.name || "").toLowerCase().replace(/\s+/g, "-") === slug
        );
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

        const mainImage = absoluteUploadUrl(found.image_url || found.image);

        let mediaUrls = [];
        if (Array.isArray(found.media)) {
          mediaUrls = found.media
            .map((m) => {
              if (!m) return null;
              if (typeof m === "string") return absoluteUploadUrl(m);
              if (m.url && (!m.type || m.type === "image"))
                return absoluteUploadUrl(m.url);
              return null;
            })
            .filter(Boolean);
        }

        const images = [mainImage, ...mediaUrls]
          .filter(Boolean)
          .filter((v, i, a) => a.indexOf(v) === i);

        setProduct({
          ...found,
          price,
          images,
        });
        setPhotoIndex(0);
        setIsOpen(false);
      } catch (err) {
        console.error("Chyba při načítání produktu:", err);
      }
    })();
  }, [slug]);

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

  return (
    <section className="pt-28 pb-12 bg-gradient-to-br from-pink-300 to-pink-200 min-h-screen">
      <div className="container mx-auto max-w-4xl px-4">
        <div className="bg-white/20 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-white/40">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
            {/* Obrázky */}
            <div className="space-y-4">
              <img
                src={product.images[photoIndex] || "/placeholder.png"}
                alt={product.name}
                className="w-full h-[260px] sm:h-[300px] md:h-[360px] object-cover rounded-xl shadow-lg cursor-pointer transition-transform duration-300 hover:scale-[1.02]"
                onClick={() => setIsOpen(true)}
                onError={(e) => (e.currentTarget.src = "/placeholder.png")}
              />
              <div className="flex gap-2 flex-wrap justify-center sm:justify-start">
                {product.images.map((img, i) => (
                  <img
                    key={i}
                    src={img}
                    alt={`${product.name} ${i + 1}`}
                    onClick={() => setPhotoIndex(i)}
                    onError={(e) => (e.currentTarget.src = "/placeholder.png")}
                    className={`h-16 w-16 sm:h-20 sm:w-20 object-cover rounded-lg cursor-pointer border-2 ${
                      photoIndex === i
                        ? "border-pink-500 shadow-lg"
                        : "border-transparent"
                    } transition duration-300 hover:scale-105`}
                  />
                ))}
              </div>
            </div>

            {/* Popis */}
            <div className="flex flex-col justify-center">
              <h2 className="text-2xl sm:text-3xl font-extrabold bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent drop-shadow-lg">
                {product.name}
              </h2>
              <p className="text-xl font-semibold text-pink-700 mt-2 drop-shadow-sm">
                {product.price.toFixed(2)} Kč
              </p>
              <p className="mt-3 text-base sm:text-lg text-gray-800 leading-relaxed">
                {product.description || "Detail produktu zde."}
              </p>
              <button
                onClick={() =>
                  addToCart({
                    id: product.id,
                    name: product.name,
                    price: product.price,
                    quantity: 1,
                  })
                }
                className="mt-6 bg-gradient-to-r from-pink-600 to-pink-700 hover:from-pink-700 hover:to-pink-800 text-white py-2 px-5 rounded-lg shadow-lg hover:shadow-pink-400/60 transition-transform transform hover:-translate-y-0.5"
              >
                Přidat do košíku
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
