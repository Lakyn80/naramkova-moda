import React, { useEffect } from "react";
import { useCart } from "../context/CartContext";
import { Link } from "react-router-dom";
import { absoluteUploadUrl } from "../utils/image";

export default function Cart() {
  const {
    cartItems,
    removeFromCart,
    increaseQuantity,
    decreaseQuantity,
  } = useCart();

  const total = cartItems.reduce(
    (sum, item) => sum + item.quantity * parseFloat(item.price),
    0
  );

  useEffect(() => {
    console.log("🛒 cartItems:", cartItems);
    cartItems.forEach((item) => {
      console.log(`🖼️ ${item.name} →`, item.image);
    });
  }, [cartItems]);

  return (
    <section className="pt-24 pb-12 px-3 sm:px-4 min-h-screen bg-gradient-to-br from-pink-300 via-white via-30% to-pink-200 text-pink-900">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold mb-8 text-center">Košík</h2>

        {cartItems.length === 0 ? (
          <p className="text-center text-pink-600">Košík je prázdný.</p>
        ) : (
          <>
            <ul className="space-y-6">
              {cartItems.map((item, index) => {
                const imageUrl = absoluteUploadUrl(item.image);
                return (
                  <li
                    key={index}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-2"
                  >
                    {/* ✅ OBRÁZEK */}
                    <img
                      src={imageUrl || "/placeholder.png"}
                      alt={item.name}
                      className="w-full sm:w-20 sm:h-20 h-auto object-cover rounded-lg"
                      onError={(e) => {
                        e.currentTarget.src = "/placeholder.png";
                      }}
                    />

                    {/* ✅ INFO */}
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{item.name}</h3>
                      <div className="flex items-center gap-2 text-sm text-pink-700 mt-2 flex-wrap">
                        <button
                          onClick={() => decreaseQuantity(item)}
                          className="px-2 py-1 bg-pink-100 hover:bg-pink-200 rounded"
                        >
                          −
                        </button>
                        <span>{item.quantity}</span>
                        <button
                          onClick={() => increaseQuantity(item)}
                          className="px-2 py-1 bg-pink-100 hover:bg-pink-200 rounded"
                        >
                          +
                        </button>
                        <span>× {item.price} Kč</span>
                      </div>
                    </div>

                    {/* ✅ ODEBRAT */}
                    <button
                      onClick={() => removeFromCart(item)}
                      className="text-sm text-red-600 hover:underline self-start sm:self-auto"
                    >
                      Odebrat
                    </button>
                  </li>
                );
              })}
            </ul>

            <div className="mt-6 text-right text-xl font-bold">
              Celkem: {total.toFixed(2)} Kč
            </div>

            <div className="mt-6 text-right">
              <Link
                to="/checkout"
                className="bg-pink-600 hover:bg-pink-700 text-white font-semibold py-2 px-6 rounded-md transition inline-block"
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
