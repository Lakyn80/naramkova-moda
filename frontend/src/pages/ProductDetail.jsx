// src/pages/ProductDetail.jsx
import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { products } from "../data/products";
import { useCart } from "../context/CartContext";

export default function ProductDetail() {
  const { slug } = useParams();
  const product = products.find(
    (p) => p.name.toLowerCase().replace(/\s+/g, "-") === slug
  );
  const { addToCart } = useCart();
  const [quantity, setQuantity] = useState(1);
  const [showModal, setShowModal] = useState(false);

  if (!product) {
    return (
      <section className="pt-24 pb-12 px-4 text-center text-pink-800">
        Produkt nenalezen.
      </section>
    );
  }

  const handleAddToCart = () => {
    addToCart(product, quantity);
  };

  return (
    <section className="pt-24 pb-12 px-4 min-h-screen bg-white text-pink-900 relative">
      <div className="max-w-4xl mx-auto flex flex-col md:flex-row gap-10 items-start">
        <img
          src={product.image}
          alt={product.name}
          className="w-full md:w-1/2 h-auto rounded-2xl shadow-md object-cover cursor-pointer"
          onClick={() => setShowModal(true)}
        />
        <div className="md:w-1/2">
          <h2 className="text-3xl font-bold mb-4">{product.name}</h2>
          <p className="text-xl font-semibold mb-2">{product.price} Kč</p>
          <p className="mb-6 text-sm text-gray-600">
            {product.description || "Ručně vyráběný náramek pro každou příležitost."}
          </p>
          <div className="mb-4">
            <label className="block text-sm font-semibold mb-1">Množství</label>
            <input
              type="number"
              value={quantity}
              min={1}
              onChange={(e) => setQuantity(parseInt(e.target.value))}
              className="w-24 border rounded px-2 py-1"
            />
          </div>
          <button
            onClick={handleAddToCart}
            className="bg-pink-600 hover:bg-pink-700 text-white py-2 px-6 rounded-lg text-lg transition"
          >
            Přidat do košíku
          </button>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div
          onClick={() => setShowModal(false)}
          className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center"
        >
          <img
            src={product.image}
            alt={product.name}
            className="max-w-full max-h-full rounded-lg shadow-xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </section>
  );
}
