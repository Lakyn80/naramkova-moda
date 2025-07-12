import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { products } from "../data/products";
import { useCart } from "../context/CartContext";

// Lightbox a pluginy
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
    const found = products.find(
      (p) => p.name.toLowerCase().replace(/\s+/g, "-") === slug
    );
    setProduct(found);
    setPhotoIndex(0);
    setIsOpen(false);
  }, [slug]);

  if (!product) {
    return (
      <section className="pt-24 pb-12 px-3 sm:px-4 min-h-screen bg-white text-pink-900">
        <div className="text-center text-lg">Produkt nenalezen.</div>
      </section>
    );
  }

  const images = product.images || [product.image];
  const slides = images.map((src) => ({ src }));

  return (
    <section className="pt-24 pb-12 px-3 sm:px-4 min-h-screen bg-white text-pink-900">
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        {/* Obrázky produktu */}
        <div className="space-y-4">
          <img
            src={images[photoIndex]}
            alt={product.name}
            className="w-full h-[280px] sm:h-[350px] md:h-[450px] object-cover rounded-xl shadow-md cursor-pointer"
            onClick={() => setIsOpen(true)}
          />

          <div className="flex gap-3 flex-wrap justify-center sm:justify-start">
            {images.map((img, index) => (
              <img
                key={index}
                src={img}
                alt={`thumbnail-${index}`}
                onClick={() => setPhotoIndex(index)}
                className={`h-20 w-20 sm:h-24 sm:w-24 object-cover rounded cursor-pointer border ${
                  photoIndex === index ? "border-pink-500" : "border-transparent"
                } transition duration-300`}
              />
            ))}
          </div>
        </div>

        {/* Popis produktu */}
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold">{product.name}</h2>
          <p className="text-lg sm:text-xl text-pink-700 mt-2">{product.price}</p>
          <p className="mt-4 text-pink-800">
            {product.description || "Detail produktu zde."}
          </p>
          <button
            className="mt-6 bg-pink-600 hover:bg-pink-700 text-white py-2 px-4 rounded-lg transition"
            onClick={() => addToCart(product)}
          >
            Přidat do košíku
          </button>
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
