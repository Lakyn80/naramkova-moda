import React, { useEffect, useState } from "react";
import Slider from "react-slick";
import { useNavigate } from "react-router-dom";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";

export default function Gallery() {
  const [products, setProducts] = useState([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("/api/products")
      .then((res) => res.json())
      .then((data) => setProducts(data))
      .catch((err) => console.error("❌ Chyba při načítání produktů:", err));
  }, []);

  const totalSlides = products.length;

  const settings = {
    dots: false,
    infinite: true,
    autoplay: true,
    autoplaySpeed: 6000, // 🔧 Pomalejší posun
    speed: 900,
    slidesToShow: 3,     // 🔧 Tři produkty na slide
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
    <section id="galerie" className="py-16 sm:py-20 px-3 sm:px-4 bg-pink-50">
      <h2 className="text-2xl sm:text-3xl font-bold text-center mb-6 sm:mb-8 text-pink-900">
        Galerie
      </h2>

      <div className="max-w-6xl mx-auto relative">
        <Slider {...settings}>
          {products.map((product) => (
            <div
              key={product.id}
              onClick={() => navigate(`/shop/${product.id}`)}
              className="cursor-pointer px-2"
            >
              <div className="p-4 bg-white border rounded-xl shadow-md hover:shadow-lg transition-all duration-300">
                <div className="w-full h-[260px] overflow-hidden rounded-md bg-white flex items-center justify-center">
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="object-contain max-h-full max-w-full"
                  />
                </div>
                <p className="text-center text-pink-800 font-medium mt-2 text-sm sm:text-base">
                  {product.name}
                </p>
              </div>
            </div>
          ))}
        </Slider>

        {/* Progress bar pod sliderem */}
        <div className="h-2 bg-pink-100 mt-6 rounded-full overflow-hidden">
          <div
            className="h-full bg-pink-500 transition-all duration-500"
            style={{ width: `${percent}%` }}
          ></div>
        </div>
      </div>
    </section>
  );
}
