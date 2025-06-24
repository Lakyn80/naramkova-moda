// src/pages/ProductDetail.jsx
import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { products } from "../data/products";
import { useCart } from "../context/CartContext";

export default function ProductDetail() {
  const { slug } = useParams();
  const product = products.find((p) => p.name.toLowerCase().replace(/\s+/g, "-") === slug);
  const { addToCart } = useCart();
  const navigate = useNavigate();

  if (!product) {
    return <div className="p-10 text-center text-pink-800">Produkt nenalezen.</div>;
  }

  return (
    <section className="pt-24 pb-12 px-4 min-h-screen bg-white text-pink-900">
      <div className="max-w-4xl mx-auto flex flex-col md:flex-row gap-10 items-start">
        <img
          src={product.image}
          alt={product.name}
          className="w-full md:w-1/2 h-auto rounded-2xl shadow-md object-cover"
        />
        <div className="md:w-1/2">
          <h2 className="text-3xl font-bold mb-4">{product.name}</h2>
          <p className="text-xl font-semibold mb-2">{product.price}</p>
          <p className="mb-6 text-sm text-gray-600">
            Krásný ručně vyráběný náramek pro každou příležitost.
          </p>
          <button
            onClick={() => {
            }}
            className="bg-pink-600 hover:bg-pink-700 text-white py-2 px-6 rounded-lg text-lg transition"
          >
            Přidat do košíku
          </button>
        </div>
      </div>
    </section>
  );
}
