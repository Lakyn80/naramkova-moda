import React, { useState } from "react";
import Slider from "react-slick";
import { useNavigate } from "react-router-dom";
import { products } from "../data/products";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";

export default function Gallery() {
  const navigate = useNavigate();
  const [activeIndex, setActiveIndex] = useState(0);

  const totalSlides = products.length;

  const settings = {
    dots: false, // vypneme tečky
    infinite: true,
    autoplay: true,
    autoplaySpeed: 3000,
    speed: 600,
    slidesToShow: 3,
    slidesToScroll: 1,
    pauseOnHover: true,
    afterChange: (index) => setActiveIndex(index),
    responsive: [
      { breakpoint: 1024, settings: { slidesToShow: 2 } },
      { breakpoint: 640, settings: { slidesToShow: 1 } },
    ],
  };

  // Výpočet procenta průběhu (pro progress bar)
  const percent = ((activeIndex % totalSlides) / totalSlides) * 100;

  return (
    <section id="galerie" className="py-20 px-4 bg-white">
      <h2 className="text-3xl font-bold text-center mb-8">Galerie</h2>
      <div className="max-w-6xl mx-auto relative">
        <Slider {...settings}>
          {products.map((product, index) => (
            <div
              key={index}
              className="p-3 cursor-pointer"
              onClick={() =>
                navigate(`/shop/${product.name.toLowerCase().replace(/\s+/g, "-")}`)
              }
            >
              <div className="rounded-xl overflow-hidden shadow-md">
                <img
                  src={product.images?.[0]}
                  alt={product.name}
                  className="w-full h-[300px] object-cover"
                />
              </div>
              <p className="text-center mt-2 text-pink-800 font-semibold">{product.name}</p>
            </div>
          ))}
        </Slider>

        {/* Progres bar pod sliderem */}
        <div className="h-2 bg-pink-100 mt-4 rounded-full overflow-hidden">
          <div
            className="h-full bg-pink-500 transition-all duration-500"
            style={{ width: `${percent}%` }}
          ></div>
        </div>
      </div>
    </section>
  );
}
