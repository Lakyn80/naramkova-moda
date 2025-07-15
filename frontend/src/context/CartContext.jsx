// src/context/CartContext.jsx

import React, { createContext, useContext, useState, useEffect } from "react";

// 🟩 Vytvoření kontextu pro košík
const CartContext = createContext();

// 🟩 Poskytovatel CartContextu pro obalení celé aplikace
export function CartProvider({ children }) {
  // 🟩 Inicializace košíku z localStorage
  const [cartItems, setCartItems] = useState(() => {
    const stored = localStorage.getItem("cartItems");
    return stored ? JSON.parse(stored) : [];
  });

  // 🟩 Ukládání změn do localStorage
  useEffect(() => {
    localStorage.setItem("cartItems", JSON.stringify(cartItems));
  }, [cartItems]);

  // 🟩 Přidání produktu do košíku (nebo navýšení množství)
  const addToCart = (product, quantity = 1) => {
    setCartItems((prev) => {
      const existing = prev.find((item) => item.name === product.name);
      if (existing) {
        return prev.map((item) =>
          item.name === product.name
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      } else {
        return [...prev, { ...product, quantity }];
      }
    });
  };

  // 🟩 Odebrání produktu z košíku
  const removeFromCart = (product) => {
    setCartItems((prev) =>
      prev.filter((item) => item.name !== product.name)
    );
  };

  // 🟩 Zvýšení množství
  const increaseQuantity = (product) => {
    setCartItems((prev) =>
      prev.map((item) =>
        item.name === product.name
          ? { ...item, quantity: item.quantity + 1 }
          : item
      )
    );
  };

  // 🟩 Snížení množství, a odstranění, pokud by bylo 0
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

  // 🟩 Vymazání celého košíku
  const clearCart = () => {
    setCartItems([]); // smazání ze state
    localStorage.removeItem("cartItems"); // smazání z localStorage
  };

  // 🟩 Kontextové hodnoty
  return (
    <CartContext.Provider
      value={{
        cartItems,
        addToCart,
        removeFromCart,
        increaseQuantity,
        decreaseQuantity,
        clearCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

// 🟩 Hook pro použití košíku v komponentách
export const useCart = () => useContext(CartContext);
