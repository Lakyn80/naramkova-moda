import React from "react";

const products = [
  {
    name: "Náramek Maminka",
    price: "89 Kč",
    image: "/products/maminka.jpg",
  },
  {
    name: "Náramek Svatba",
    price: "99 Kč",
    image: "/products/svatba.jpg",
  },
  {
    name: "Dětský náramek",
    price: "59 Kč",
    image: "/products/deti.jpg",
  },
  {
    name: "Klíčenka se jménem",
    price: "149 Kč",
    image: "/products/klicenka.jpg",
  },
];

export default function Shop() {
  return (
    <section className="relative py-20 px-4 bg-gradient-to-br from-pink-300 via-white via-30% to-pink-200 overflow-hidden">
      <h2 className="text-3xl font-bold text-center text-pink-900 mb-12 drop-shadow-sm">
        E-shop
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8 max-w-6xl mx-auto">
        {products.map((product, index) => (
          <div
            key={index}
            className="bg-white/60 backdrop-blur-md rounded-2xl shadow-xl overflow-hidden text-center p-4 hover:shadow-2xl transition-all duration-300"
          >
            <img
              src={product.image}
              alt={product.name}
              className="w-full h-48 object-cover rounded-xl"
            />
            <h3 className="mt-4 text-lg font-semibold text-pink-900">
              {product.name}
            </h3>
            <p className="text-sm text-pink-700 mt-1">{product.price}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
