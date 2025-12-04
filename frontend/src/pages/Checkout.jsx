import React, { useEffect, useMemo, useRef, useState } from "react";
import { useCart } from "../context/CartContext";
import { useNavigate } from "react-router-dom";
import QRCode from "qrcode";

const MERCHANT_IBAN = (import.meta.env.VITE_IBAN || "CZ6508000000001234567899").toUpperCase();
const SHIPPING_FEE_CZK = Number(import.meta.env.VITE_SHIPPING_FEE_CZK ?? 89); // ✅ čte z .env, fallback 89

function toMoney(n) {
  // bezpečné zaokrouhlení na 2 decimály
  const cents = Math.round(Number(n) * 100);
  return cents / 100;
}

function buildSpdPayload({ iban, amount, vs, msg }) {
  if (!iban) throw new Error("Chybí IBAN.");
  const normIban = iban.replace(/\s+/g, "").toUpperCase();
  const parts = ["SPD*1.0", `ACC:${normIban}`, `AM:${toMoney(amount).toFixed(2)}`, "CC:CZK"];
  if (vs) parts.push(`X-VS:${String(vs).trim()}`);
  if (msg) {
    const safe = String(msg).replace(/[^\x20-\x7E]/g, "");
    parts.push(`MSG:${safe.slice(0, 60)}`);
  }
  return parts.join("*");
}

export default function Checkout() {
  const { cartItems, clearCart, shippingMode } = useCart();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({ name: "", email: "", address: "", note: "" });
  const [phase, setPhase] = useState("form");
  const [vs, setVs] = useState(null);
  const [qrError, setQrError] = useState("");
  const canvasRef = useRef(null);

  // ── Výpočty ────────────────────────────────────────────────────────────────
  const subtotal = useMemo(() => {
    return cartItems.reduce((sum, item) => {
      const q = Number(item.quantity) || 0;
      const p = Number(item.price) || 0;
      return sum + q * p;
    }, 0);
  }, [cartItems]);

  const total = useMemo(() => {
    const shipping = shippingMode === "pickup" ? 0 : SHIPPING_FEE_CZK;
    return toMoney(subtotal + shipping); // ✅ vč. poštovného/pickupu
  }, [subtotal, shippingMode]);

  // ── Form ──────────────────────────────────────────────────────────────────
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleShowQr = (e) => {
    e.preventDefault();
    if (!cartItems.length) return;
    const newVs = Math.floor(100000 + Math.random() * 900000);
    setVs(newVs);
    setPhase("qr");
  };

  // ── QR generování ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (phase !== "qr") return;
    (async () => {
      setQrError("");
      try {
        if (!MERCHANT_IBAN || !total || total <= 0 || !vs) return;
        const payload = buildSpdPayload({
          iban: MERCHANT_IBAN,
          amount: total, // ✅ QR AM = total vč. poštovného
          vs,
          msg: `Objednavka ${vs}`,
        });
        await QRCode.toCanvas(canvasRef.current, payload, { width: 256, margin: 1 });
      } catch (e) {
        setQrError(String(e?.message || e));
      }
    })();
  }, [phase, total, vs]);

  // ── Odeslání objednávky ───────────────────────────────────────────────────
  const handleConfirmPaidAndSubmit = async () => {
    try {
      const orderData = {
        name: formData.name,
        email: formData.email,
        address: formData.address,
        note: formData.note,
        vs,
        totalCzk: total,              // ✅ posíláme vč. poštovného
        shippingCzk: shippingMode === "pickup" ? 0 : SHIPPING_FEE_CZK, // (volitelné) pro přehled v adminu
        shippingMode,
        items: cartItems.map((item) => ({
          id: item.id,
          name: item.name,
          quantity: Number(item.quantity) || 0,
          price: Number(item.price) || 0,
        })),
      };

      const response = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(orderData),
      });

      if (response.ok) {
        clearCart();
        setPhase("submitted");
      } else {
        // 🔒 zachytit chybu skladu / jinou zprávu z BE a jen zobrazit
        let msg = "Nepodařilo se odeslat objednávku. Zkuste to prosím znovu.";
        try {
          const data = await response.json();
          msg = data?.error || data?.message || msg;
        } catch (_) {}
        console.error("❌ Chyba při odesílání objednávky");
        alert(msg);
      }
    } catch (error) {
      console.error("❌ Fetch error:", error);
      alert("Došlo k chybě při odesílání. Zkuste to prosím znovu.");
    }
  };

  // ── UI ────────────────────────────────────────────────────────────────────
  if (phase === "submitted") {
    return (
      <section className="pt-24 pb-12 px-3 sm:px-4 min-h-screen text-center text-pink-900 bg-gradient-to-br from-pink-300 via-white to-pink-200">
        <h2 className="text-2xl sm:text-3xl font-bold mb-4">Děkujeme za objednávku!</h2>
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

  if (phase === "qr") {
    return (
      <section className="pt-24 pb-12 px-3 sm:px-4 min-h-screen text-pink-900 bg-gradient-to-br from-pink-300 via-white to-pink-200">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold mb-4 text-center">Platba objednávky</h2>
          <p className="text-center text-pink-800 mb-6">
            Naskenujte QR kód ve své bankovní aplikaci. <br />
            Částka: <b>{toMoney(total).toFixed(2)} CZK</b>
          </p>

          <div className="flex flex-col items-center gap-4 bg-white rounded-2xl shadow p-6">
            {qrError ? (
              <div className="text-red-600">{qrError}</div>
            ) : (
              <canvas ref={canvasRef} className="border rounded-lg shadow w-64 h-64" />
            )}

            <div className="flex gap-3 pt-2">
              <button onClick={() => setPhase("form")} className="px-4 py-2 rounded-md border">
                Zpět
              </button>
              <button
                onClick={handleConfirmPaidAndSubmit}
                className="bg-pink-600 hover:bg-pink-700 text-white font-semibold py-2 px-4 rounded-md transition"
              >
                Potvrzuji platbu, odeslat objednávku
              </button>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
      <section className="pt-24 pb-12 px-3 sm:px-4 min-h-screen text-pink-900 bg-gradient-to-br from-pink-300 via-white to-pink-200">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold mb-8 text-center">Pokladna</h2>
          {cartItems.length === 0 ? (
            <p className="text-center text-pink-600">Košík je prázdný.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <form onSubmit={handleShowQr} className="space-y-4">
              <input type="text" name="name" placeholder="Jméno a příjmení" required className="w-full border px-4 py-2 rounded-md" value={formData.name} onChange={handleChange} />
              <input type="email" name="email" placeholder="Email" required className="w-full border px-4 py-2 rounded-md" value={formData.email} onChange={handleChange} />
              <textarea name="address" placeholder="Adresa" required className="w-full border px-4 py-2 rounded-md" value={formData.address} onChange={handleChange} />
              <textarea name="note" placeholder="Poznámka (volitelné)" className="w-full border px-4 py-2 rounded-md" value={formData.note} onChange={handleChange} />
              <button type="submit" className="bg-pink-600 hover:bg-pink-700 text-white font-semibold py-2 px-6 rounded-md transition w-full sm:w-auto">
                Zaplatit QR
              </button>
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="inline-flex items-center justify-center gap-2 rounded-md bg-white/70 border border-pink-200 text-pink-700 px-4 py-2 font-semibold shadow-sm hover:bg-white transition w-full sm:w-auto mt-3 sm:mt-0 sm:ml-3"
              >
                ⬅︎ Zpět do košíku
              </button>
            </form>

            <div>
              <h3 className="text-xl font-semibold mb-4">Vaše objednávka:</h3>
              <ul className="space-y-2 text-pink-800 text-sm">
                {cartItems.map((item, index) => (
                  <li key={index} className="flex justify-between">
                    <span>{Number(item.quantity)}× {item.name}</span>
                    <span>{toMoney(Number(item.quantity) * Number(item.price)).toFixed(2)} Kč</span>
                  </li>
                ))}
              </ul>
              <div className="mt-4 text-right text-sm">Mezisoučet: {toMoney(subtotal).toFixed(2)} Kč</div>
              <div className="text-right text-sm">
                Doprava: {shippingMode === "pickup" ? "Osobní vyzvednutí (0 Kč)" : `Poštou: ${toMoney(SHIPPING_FEE_CZK).toFixed(2)} Kč`}
              </div>
              <div className="mt-1 font-bold text-right text-lg">Celkem: {toMoney(total).toFixed(2)} Kč</div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
