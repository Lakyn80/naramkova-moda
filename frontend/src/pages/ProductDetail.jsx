import React from "react";
import { useParams } from "react-router-dom";
import { products } from "../data/products";
import { useCart } from "../context/CartContext";
import ProductGallery from "../components/ProductGallery";

export default function ProductDetail() {
  const { slug } = useParams();
  const { addToCart } = useCart();

  const product = products.find(
    (p) => p.name.toLowerCase().replace(/\s+/g, "-") === slug
  );

  if (!product) {
    return (
      <section className="pt-24 pb-12 px-4 min-h-screen bg-white text-pink-900">
        <div className="text-center text-lg">Produkt nenalezen.</div>
      </section>
    );
  }

  const images = product.images || [product.image];

  return (
    <section className="pt-24 pb-12 px-4 min-h-screen bg-white text-pink-900">
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        {/* Galerie s obrázky */}
        <ProductGallery images={images} productName={product.name} />

        {/* Popis produktu */}
        <div>
          <h2 className="text-3xl font-bold">{product.name}</h2>
          <p className="text-xl text-pink-700 mt-2">{product.price}</p>
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
    </section>
  );
}
