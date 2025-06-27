export const products = [
  {
    name: "Náramek Maminka",
    price: "89 Kč",
    description: "Jemný náramek jako ideální dárek pro maminku.",
    categories: ["Maminka"],
    images: ["/products/maminka.jpg"]
  },
  {
    name: "Náramek Svatba",
    price: "99 Kč",
    description: "Elegantní náramek pro svatební den.",
    categories: ["Svatba"],
    images: ["/products/svatba.jpg"]
  },
  {
    name: "Dětský náramek",
    price: "59 Kč",
    description: "Hrací náramek pro děti s veselým motivem.",
    categories: ["Děti", "Pro děti"],
    images: ["/products/deti.jpg"]
  },
  {
    name: "Klíčenka se jménem",
    price: "149 Kč",
    description: "Silikonová klíčenka s možností vlastního jména.",
    categories: ["Jen pro radost", "Jméno"],
    images: ["/products/klicenka.jpg"]
  },
  {
    name: "Náramek Romantika",
    price: "149 Kč",
    description: "Elegantní náramek ideální jako dárek z lásky.",
    categories: ["Láska"],
    images: [
      "/products/naramek_romantika_1.jpg",
      "/products/naramek_romantika_2.jpg",
      "/products/naramek_romantika_3.jpg",
      "/products/naramek_romantika_4.jpg"
    ]
  }
];

export const categoryTree = {
  Rodina: ["Maminka", "Babička", "Bratr", "Sestra", "Tatínek", "Dědeček"],
  Svatba: ["Svatba"],
  Dárky: ["Jen pro radost"],
  Láska: ["Láska"],
  Děti: ["Děti", "Pro děti"],
  Páry: ["Pro páry", "Výročí", "Přátelství"]
};
