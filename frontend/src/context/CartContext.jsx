import React, { createContext, useContext, useState, useEffect } from "react";

const CartContext = createContext();

export function CartProvider({ children }) {
  const buildLineKey = (item) => {
    if (!item) return "";
    if (item.variantId) return `variant-${item.variantId}`;
    if (item.id) return `product-${item.id}`;
    return `name-${item.name || Math.random()}`;
  };

  const normalizeItem = (item) => {
    if (!item) return null;
    return { ...item, lineKey: item.lineKey || buildLineKey(item) };
  };

  const [cartItems, setCartItems] = useState(() => {
    const stored = localStorage.getItem("cartItems");
    const parsed = stored ? JSON.parse(stored) : [];
    return Array.isArray(parsed) ? parsed.map(normalizeItem).filter(Boolean) : [];
  });
  const [shippingMode, setShippingMode] = useState(() => {
    const stored = localStorage.getItem("shippingMode");
    return stored || "post"; // "post" | "pickup"
  });

  useEffect(() => {
    localStorage.setItem("cartItems", JSON.stringify(cartItems));
  }, [cartItems]);

  useEffect(() => {
    localStorage.setItem("shippingMode", shippingMode);
  }, [shippingMode]);

  const addToCart = (product, quantity = 1) => {
    // force number
    const priceNum = typeof product.price === "number"
      ? product.price
      : parseFloat(String(product.price || product.price_czk || 0).toString().replace(",", "."));

    const itemToAdd = normalizeItem({ ...product, price: priceNum, quantity });
    if (!itemToAdd) return;

    setCartItems((prev) => {
      const existing = prev.find((item) => item.lineKey === itemToAdd.lineKey);
      if (existing) {
        const max = Number.isFinite(Number(existing.stock)) ? Number(existing.stock) : undefined;
        const nextQty = existing.quantity + quantity;
        const cappedQty = typeof max === "number" ? Math.min(nextQty, max) : nextQty;
        return prev.map((item) =>
          item.lineKey === itemToAdd.lineKey
            ? { ...item, quantity: cappedQty }
            : item
        );
      } else {
        return [...prev, itemToAdd];
      }
    });
  };

  const removeFromCart = (product) => {
    const key = product?.lineKey || buildLineKey(product);
    setCartItems((prev) => prev.filter((item) => item.lineKey !== key));
  };

  const increaseQuantity = (product) => {
    const key = product?.lineKey || buildLineKey(product);
    setCartItems((prev) =>
      prev.map((item) => {
        if (item.lineKey !== key) return item;
        const max = Number.isFinite(Number(item.stock)) ? Number(item.stock) : undefined;
        const next = item.quantity + 1;
        return typeof max === "number" ? { ...item, quantity: Math.min(next, max) } : { ...item, quantity: next };
      })
    );
  };

  const decreaseQuantity = (product) => {
    const key = product?.lineKey || buildLineKey(product);
    setCartItems((prev) =>
      prev
        .map((item) =>
          item.lineKey === key
            ? { ...item, quantity: item.quantity - 1 }
            : item
        )
        .filter((item) => item.quantity > 0)
    );
  };

  const clearCart = () => {
    setCartItems([]);
    localStorage.removeItem("cartItems");
  };

  return (
    <CartContext.Provider
      value={{
        cartItems,
        addToCart,
        removeFromCart,
        increaseQuantity,
        decreaseQuantity,
        clearCart,
        shippingMode,
        setShippingMode,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
