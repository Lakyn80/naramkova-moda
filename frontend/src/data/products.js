// src/data/products.js
export const products = [
  {
    name: "Náramek Maminka",
    price: "89 Kč",
    image: "/products/maminka.jpg",
    categories: ["maminka"],
  },
  {
    name: "Náramek pro Babičku",
    price: "89 Kč",
    image: "/products/babicka.jpg",
    categories: ["babička"],
  },
  {
    name: "Náramek Bratr",
    price: "79 Kč",
    image: "/products/bratr.jpg",
    categories: ["bratr"],
  },
  {
    name: "Náramek Sestra",
    price: "79 Kč",
    image: "/products/sestra.jpg",
    categories: ["sestra"],
  },
  {
    name: "Dětský náramek",
    price: "59 Kč",
    image: "/products/deti.jpg",
    categories: ["děti", "pro děti"],
  },
  {
    name: "Náramek Svatba",
    price: "99 Kč",
    image: "/products/svatba.jpg",
    categories: ["svatba", "výročí"],
  },
  {
    name: "Náramek pro radost",
    price: "69 Kč",
    image: "/products/radost.jpg",
    categories: ["jen pro radost"],
  },
  {
    name: "Náramek Tatínek",
    price: "89 Kč",
    image: "/products/tatinek.jpg",
    categories: ["tatínek"],
  },
  {
    name: "Náramek Dědeček",
    price: "89 Kč",
    image: "/products/dedecek.jpg",
    categories: ["dědeček"],
  },
  {
    name: "Náramek Kamarádka",
    price: "79 Kč",
    image: "/products/kamaradka.jpg",
    categories: ["kamarádka", "přátelství"],
  },
  {
    name: "Náramek Láska",
    price: "109 Kč",
    image: "/products/laska.jpg",
    categories: ["láska", "pro páry"],
  },
];

export const categoryTree = {
  rodina: ["maminka", "tatínek", "dědeček", "babička", "bratr", "sestra"],
  děti: ["děti", "pro děti"],
  vztahy: ["láska", "pro páry", "výročí", "přátelství", "kamarádka"],
  svatba: ["svatba"],
  ostatní: ["jen pro radost"],
};
