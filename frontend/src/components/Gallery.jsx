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
    dots: false,
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

  const percent = ((activeIndex % totalSlides) / totalSlides) * 100;

  return (
    // 🟩 Stejné pozadí jako sekce Kategorie
    <section
      id="galerie"
      className="py-16 sm:py-20 px-3 sm:px-4 bg-[#fbe8f2]" // <- stejné jako Kategorie
    >
      <div className="max-w-6xl mx-auto relative">
        {/* 🎀 Rámeček – glassmorphism styl */}
        <div className="backdrop-blur-sm bg-white/30 rounded-2xl shadow-xl px-6 py-8 sm:px-10 sm:py-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-6 sm:mb-8 text-pink-900">
            Galerie
          </h2>

          {/* 🖼️ Karusel */}
          <Slider {...settings}>
            {products.map((product, index) => (
              <div
                key={index}
                onClick={() =>
                  navigate(
                    `/shop/${product.name.toLowerCase().replace(/\s+/g, "-")}`
                  )
                }
              >
                <div className="flex justify-center">
                  <div className="p-2 cursor-pointer w-full max-w-[280px]">
                    <div className="rounded-xl overflow-hidden shadow-md">
                      <img
                        src={product.images?.[0]}
                        alt={product.name}
                        className="w-full h-[240px] sm:h-[260px] object-cover"
                      />
                    </div>
                    <p className="text-center mt-2 text-pink-800 font-semibold text-sm sm:text-base">
                      {product.name}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </Slider>

          {/* 📉 Progress bar */}
          <div className="h-2 bg-pink-100 mt-6 rounded-full overflow-hidden">
            <div
              className="h-full bg-pink-500 transition-all duration-500"
              style={{ width: `${percent}%` }}
            ></div>
          </div>
        </div>
      </div>
    </section>
  );
}
