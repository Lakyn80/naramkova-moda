import React, { useEffect, useState } from "react";
import Slider from "react-slick";
import { useNavigate } from "react-router-dom";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";

export default function Gallery() {
  const [products, setProducts] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const res = await fetch("/api/products");
        const data = await res.json();
        setProducts(data);
      } catch (error) {
        console.error("Chyba při načítání produktů:", error);
      }
    };
    fetchProducts();
  }, []);

  const settings = {
    dots: false,
    infinite: true,
    autoplay: true,
    autoplaySpeed: 5000,
    speed: 1000,
    slidesToShow: 3,
    slidesToScroll: 1,
    pauseOnHover: true,
    responsive: [
      { breakpoint: 1024, settings: { slidesToShow: 2 } },
      { breakpoint: 640, settings: { slidesToShow: 1 } },
    ],
  };

  return (
    <section
      id="galerie"
      className="relative py-20 px-3 sm:px-4 bg-gradient-to-b from-rose-light to-rose-mid overflow-hidden"
    >
      <img
        src="/wave.svg"
        alt="Wave top"
        className="absolute -top-[1px] left-0 w-full pointer-events-none rotate-180 z-0"
      />

      <h2 className="text-4xl sm:text-5xl font-extrabold text-center mb-10 bg-gradient-to-r from-pink-600 via-pink-400 to-fuchsia-600 text-transparent bg-clip-text drop-shadow-sm relative z-10">
        Galerie
      </h2>

      <div className="max-w-6xl mx-auto relative z-10">
        <Slider {...settings}>
          {products.map((product, index) => (
            <div
              key={index}
              onClick={() =>
                navigate(`/shop/${product.name.toLowerCase().replace(/\s+/g, "-")}`)
              }
              className="px-3"
            >
              <div className="bg-white/60 backdrop-blur-md hover:bg-white/80 rounded-xl p-4 shadow-lg transition cursor-pointer">
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="w-full h-[300px] object-contain rounded-md"
                />
                <p className="text-center mt-3 text-pink-900 font-semibold text-base">
                  {product.name}
                </p>
              </div>
            </div>
          ))}
        </Slider>

        <div className="h-2 bg-pink-300 mt-6 rounded-full overflow-hidden">
          <div className="h-full bg-pink-500 transition-all duration-500 w-full animate-pulse"></div>
        </div>
      </div>
    </section>
  );
}
