import React, { useEffect } from "react";
import { useCart } from "../context/CartContext";
import { Link } from "react-router-dom";
import { absoluteUploadUrl } from "../utils/image";
import { emojify } from "../utils/emojify";

const SHIPPING_FEE_CZK = Number(import.meta.env.VITE_SHIPPING_FEE_CZK ?? 89); // ✅

function toMoney(n) {
  const cents = Math.round(Number(n) * 100);
  return cents / 100;
}

export default function Cart() {
  const { cartItems, removeFromCart, increaseQuantity, decreaseQuantity } = useCart();

  const subtotal = cartItems.reduce((sum, item) => {
    const q = Number(item.quantity) || 0;
    const p = Number(item.price) || 0;
    return sum + q * p;
  }, 0);

  const grandTotal = toMoney(subtotal + SHIPPING_FEE_CZK); // ✅

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
                const max = Number.isFinite(Number(item.stock)) ? Number(item.stock) : undefined;
                const atMax = typeof max === "number" ? Number(item.quantity) >= max : false;
                return (
                  <li key={index} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-2">
                    <img
                      src={imageUrl || "/placeholder.png"}
                      alt={item.name}
                      className="w-full sm:w-20 sm:h-20 h-auto object-cover rounded-lg"
                      onError={(e) => { e.currentTarget.src = "/placeholder.png"; }}
                    />
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{emojify(item.name)}</h3>
                      <div className="flex items-center gap-2 text-sm text-pink-700 mt-2 flex-wrap">
                        <button onClick={() => decreaseQuantity(item)} className="px-2 py-1 bg-pink-100 hover:bg-pink-200 rounded">−</button>
                        <span>{Number(item.quantity)}</span>
                        <button
                          onClick={() => !atMax && increaseQuantity(item)}
                          disabled={atMax}
                          className={`px-2 py-1 rounded ${atMax ? "bg-gray-200 text-gray-500 cursor-not-allowed" : "bg-pink-100 hover:bg-pink-200"}`}
                          title={atMax ? "Nelze přidat víc kusů, než je skladem." : ""}
                        >
                          +
                        </button>
                        <span>× {toMoney(item.price).toFixed(2)} Kč</span>
                        {typeof max === "number" && (
                          <span className="ml-2 text-xs px-2 py-0.5 rounded bg-pink-100 text-pink-800">
                            Skladem: {max}
                          </span>
                        )}
                      </div>
                    </div>
                    <button onClick={() => removeFromCart(item)} className="text-sm text-red-600 hover:underline self-start sm:self-auto">
                      Odebrat
                    </button>
                  </li>
                );
              })}
            </ul>

            <div className="mt-6 text-right text-base">Mezisoučet: {toMoney(subtotal).toFixed(2)} Kč</div>
            <div className="text-right text-base">Poštovné: {toMoney(SHIPPING_FEE_CZK).toFixed(2)} Kč</div>
            <div className="mt-2 text-right text-xl font-bold">Celkem k úhradě: {toMoney(grandTotal).toFixed(2)} Kč</div>

            <div className="mt-6 text-right">
              <Link to="/checkout" className="bg-pink-600 hover:bg-pink-700 text-white font-semibold py-2 px-6 rounded-md transition inline-block">
                Přejít k pokladně
              </Link>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
