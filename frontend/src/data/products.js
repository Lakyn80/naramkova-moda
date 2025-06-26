// src/data/products.js
export const products = [
  {
    name: "Náramek Maminka",
    price: "89",
    image: "/public/naramky_1.jpg",
    categories: ["Maminka"],
    description: "Stylový náramek ideální jako dárek pro maminku.",
  },
  {
    name: "Náramek Svatba",
    price: "99",
    image: "/products/svatba.jpg",
    categories: ["Svatba"],
    description: "Elegantní náramek vhodný na svatební příležitosti.",
  },
  {
    name: "Dětský náramek",
    price: "59",
    image: "/products/deti.jpg",
    categories: ["Děti", "Pro děti"],
    description: "Barevný náramek pro nejmenší.",
  },
  {
    name: "Klíčenka se jménem",
    price: "149",
    image: "/products/klicenka.jpg",
    categories: ["Pro páry", "Výročí"],
    description: "Unikátní klíčenka s možností personalizace.",
  },
];

export const categoryTree = {
  Rodina: ["Maminka", "Babička", "Bratr", "Sestra", "Tatínek", "Dědeček"],
  Svatba: ["Svatba"],
  Dárky: ["Jen pro radost"],
  Láska: ["Láska"],
  Děti: ["Děti", "Pro děti"],
  Páry: ["Pro páry", "Výročí", "Přátelství"],
};
