import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useCart } from "../context/CartContext";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";
import Thumbnails from "yet-another-react-lightbox/plugins/thumbnails";
import "yet-another-react-lightbox/plugins/thumbnails.css";
import Zoom from "yet-another-react-lightbox/plugins/zoom";

export default function ProductDetail() {
  const { slug } = useParams();
  const { addToCart } = useCart();
  const [product, setProduct] = useState(null);
  const [photoIndex, setPhotoIndex] = useState(0);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/products");
        const data = await res.json();
        const found = data.find(
          (p) => p.name.toLowerCase().replace(/\s+/g, "-") === slug
        );
        setProduct(found);
      } catch (err) {
        console.error("Chyba při načítání produktu:", err);
      }
    })();
  }, [slug]);

  if (!product) {
    return (
      <section className="pt-24 pb-12 bg-white min-h-screen flex items-center justify-center">
        <div className="text-center text-lg text-pink-900">
          Produkt nenalezen.
        </div>
      </section>
    );
  }

  // Extrahujeme obrázky
  const images = product.media
    .filter((m) => m.type === "image")
    .map((m) => m.url);
  const slides = images.map((src) => ({ src }));

  return (
    <section className="pt-24 pb-12 bg-white">
      {/* container teď drží max šířku a centrování */}
      <div className="container mx-auto max-w-4xl px-4">
        <div className="bg-gray-100 rounded-lg shadow-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
            {/* Obrázky */}
            <div className="space-y-4">
              <img
                src={images[photoIndex] || product.image}
                alt={product.name}
                className="w-full h-[280px] sm:h-[350px] md:h-[450px] object-cover rounded-xl shadow-md cursor-pointer"
                onClick={() => setIsOpen(true)}
              />
              <div className="flex gap-3 flex-wrap justify-center sm:justify-start">
                {images.map((img, i) => (
                  <img
                    key={i}
                    src={img}
                    alt={`${product.name} ${i + 1}`}
                    onClick={() => setPhotoIndex(i)}
                    className={`h-20 w-20 sm:h-24 sm:w-24 object-cover rounded cursor-pointer border ${
                      photoIndex === i ? "border-pink-500" : "border-transparent"
                    } transition`}
                  />
                ))}
              </div>
            </div>

            {/* Popis */}
            <div>
              <h2 className="text-2xl sm:text-3xl font-bold">
                {product.name}
              </h2>
              <p className="text-lg sm:text-xl text-pink-700 mt-2">
                {product.price.toFixed(2)} Kč
              </p>
              <p className="mt-4 text-pink-800">
                {product.description}
              </p>
              <button
                onClick={() => addToCart(product)}
                className="mt-6 bg-pink-600 hover:bg-pink-700 text-white py-2 px-4 rounded-lg"
              >
                Přidat do košíku
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Lightbox */}
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
