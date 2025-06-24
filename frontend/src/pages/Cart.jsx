// src/pages/Cart.jsx
import React from "react";
import { useCart } from "../context/CartContext";
import { Link } from "react-router-dom";

export default function Cart() {
  const { cartItems, removeFromCart } = useCart();

  const total = cartItems.reduce(
    (sum, item) => sum + item.quantity * parseFloat(item.price),
    0
  );

  return (
    <section className="pt-24 pb-12 px-4 min-h-screen bg-white text-pink-900">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold mb-8 text-center">Košík</h2>

        {cartItems.length === 0 ? (
          <p className="text-center text-pink-600">Košík je prázdný.</p>
        ) : (
          <>
            <ul className="space-y-4">
              {cartItems.map((item, index) => (
                <li
                  key={index}
                  className="flex justify-between items-center border-b pb-2"
                >
                  <div>
                    <h3 className="font-semibold">{item.name}</h3>
                    <p className="text-sm text-pink-700">
                      {item.quantity} × {item.price} Kč
                    </p>
                  </div>
                  <button
                    onClick={() => removeFromCart(item)}
                    className="text-sm text-red-600 hover:underline"
                  >
                    Odebrat
                  </button>
                </li>
              ))}
            </ul>

            <div className="mt-6 text-right text-xl font-bold">
              Celkem: {total.toFixed(2)} Kč
            </div>

            <div className="mt-6 text-right">
              <Link
                to="/checkout"
                className="bg-pink-600 hover:bg-pink-700 text-white font-semibold py-2 px-6 rounded-md transition"
              >
                Přejít k pokladně
              </Link>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
