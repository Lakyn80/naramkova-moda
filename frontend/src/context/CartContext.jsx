import React, { createContext, useContext, useState, useEffect } from "react";

const CartContext = createContext();

export function CartProvider({ children }) {
  const [cartItems, setCartItems] = useState(() => {
    const stored = localStorage.getItem("cartItems");
    return stored ? JSON.parse(stored) : [];
  });

  useEffect(() => {
    localStorage.setItem("cartItems", JSON.stringify(cartItems));
  }, [cartItems]);

  const addToCart = (product, quantity = 1) => {
    // force number
    const priceNum = typeof product.price === "number"
      ? product.price
      : parseFloat(String(product.price || product.price_czk || 0).toString().replace(",", "."));

    const itemToAdd = { ...product, price: priceNum, quantity };

    setCartItems((prev) => {
      const existing = prev.find((item) => item.name === itemToAdd.name);
      if (existing) {
        return prev.map((item) =>
          item.name === itemToAdd.name
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      } else {
        return [...prev, itemToAdd];
      }
    });
  };

  const removeFromCart = (product) => {
    setCartItems((prev) => prev.filter((item) => item.name !== product.name));
  };

  const increaseQuantity = (product) => {
    setCartItems((prev) =>
      prev.map((item) =>
        item.name === product.name
          ? { ...item, quantity: item.quantity + 1 }
          : item
      )
    );
    };

  const decreaseQuantity = (product) => {
    setCartItems((prev) =>
      prev
        .map((item) =>
          item.name === product.name
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
      value={{ cartItems, addToCart, removeFromCart, increaseQuantity, decreaseQuantity, clearCart }}
    >
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
