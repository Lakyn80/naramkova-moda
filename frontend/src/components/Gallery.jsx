import React from "react";
import nar1 from "../assets/naramky_1.jpg";
import nar2 from "../assets/naramky_2.jpg";
import nar3 from "../assets/naramky_3.jpg";
import nar4 from "../assets/naramky_4.jpg";

const images = [nar1, nar2, nar3, nar4];

export default function Gallery() {
  return (
    <section id="galerie" className="py-20 px-4">
      <h2 className="text-3xl font-bold text-center mb-8">Galerie</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 max-w-6xl mx-auto">
        {images.map((src, index) => (
          <img
            key={index}
            src={src}
            alt={`Náramek ${index + 1}`}
            className="rounded shadow-md object-cover aspect-square"
          />
        ))}
      </div>
    </section>
  );
}
