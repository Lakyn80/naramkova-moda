// src/pages/Checkout.jsx
import React, { useState } from "react";
import { useCart } from "../context/CartContext";
import { useNavigate } from "react-router-dom";

export default function Checkout() {
  const { cartItems } = useCart();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    address: "",
    note: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const total = cartItems.reduce(
    (sum, item) => sum + item.quantity * parseFloat(item.price),
    0
  );

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Zde by se volal backend nebo email endpoint (např. přes fetch nebo axios)
    console.log("Odesláno:", formData, cartItems);

    setSubmitted(true);
  };

  if (submitted) {
    return (
      <section className="pt-24 pb-12 px-4 min-h-screen text-center text-pink-900 bg-white">
        <h2 className="text-3xl font-bold mb-4">Děkujeme za objednávku!</h2>
        <p className="mb-6">Brzy se vám ozveme s potvrzením a detaily doručení.</p>
        <button
          onClick={() => navigate("/")}
          className="bg-pink-600 hover:bg-pink-700 text-white py-2 px-6 rounded-lg text-lg transition"
        >
          Zpět na hlavní stránku
        </button>
      </section>
    );
  }

  return (
    <section className="pt-24 pb-12 px-4 min-h-screen bg-white text-pink-900">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold mb-8 text-center">Pokladna</h2>

        {cartItems.length === 0 ? (
          <p className="text-center text-pink-600">Košík je prázdný.</p>
        ) : (
          <div className="grid md:grid-cols-2 gap-10">
            {/* Formulář */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="text"
                name="name"
                placeholder="Jméno a příjmení"
                required
                className="w-full border px-4 py-2 rounded-md"
                value={formData.name}
                onChange={handleChange}
              />
              <input
                type="email"
                name="email"
                placeholder="Email"
                required
                className="w-full border px-4 py-2 rounded-md"
                value={formData.email}
                onChange={handleChange}
              />
              <textarea
                name="address"
                placeholder="Adresa"
                required
                className="w-full border px-4 py-2 rounded-md"
                value={formData.address}
                onChange={handleChange}
              />
              <textarea
                name="note"
                placeholder="Poznámka (volitelné)"
                className="w-full border px-4 py-2 rounded-md"
                value={formData.note}
                onChange={handleChange}
              />
              <button
                type="submit"
                className="bg-pink-600 hover:bg-pink-700 text-white font-semibold py-2 px-6 rounded-md transition"
              >
                Odeslat objednávku
              </button>
            </form>

            {/* Shrnutí košíku */}
            <div>
              <h3 className="text-xl font-semibold mb-4">Vaše objednávka:</h3>
              <ul className="space-y-2 text-pink-800">
                {cartItems.map((item, index) => (
                  <li key={index} className="flex justify-between">
                    <span>
                      {item.quantity}× {item.name}
                    </span>
                    <span>{(item.quantity * parseFloat(item.price)).toFixed(2)} Kč</span>
                  </li>
                ))}
              </ul>
              <div className="mt-4 font-bold text-right text-lg">
                Celkem: {total.toFixed(2)} Kč
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
