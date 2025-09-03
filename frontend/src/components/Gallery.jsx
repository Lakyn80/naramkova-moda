import React, { useEffect, useState, useMemo } from "react";
import Slider from "react-slick";
import { useNavigate } from "react-router-dom";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import { slugify } from "../utils/slugify";
import { emojify } from "../utils/emojify";

// Hezká šipka mimo slider (bez dalších knihoven)
function Arrow({ className = "", onClick, direction = "next" }) {
  const isNext = direction === "next";
  const disabled = className.includes("slick-disabled");

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={isNext ? "Další" : "Předchozí"}
      // mimo slider (negativní odsazení), skryj na mobilech
      className={[
        "hidden sm:flex items-center justify-center",
        "absolute top-1/2 -translate-y-1/2 z-20",
        isNext ? "-right-14" : "-left-14",
        "h-12 w-12 rounded-full",
        "bg-gradient-to-br from-white/90 to-white/70 backdrop-blur",
        "shadow-xl border border-pink-200/60",
        "hover:from-white hover:to-white hover:shadow-2xl hover:scale-105",
        "transition-all duration-200",
        disabled ? "opacity-40 pointer-events-none" : "opacity-95",
        // pro jistotu – ať neovlivní kliknutí na karty
        "focus:outline-none focus:ring-2 focus:ring-pink-400/60",
      ].join(" ")}
      style={{ lineHeight: 0 }}
    >
      <svg
        width="22"
        height="22"
        viewBox="0 0 24 24"
        className="text-pink-700"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {isNext ? (
          <path
            d="M8 4l8 8-8 8"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ) : (
          <path
            d="M16 4L8 12l8 8"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}
      </svg>
    </button>
  );
}

export default function Gallery() {
  const [products, setProducts] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/products");
        const data = await res.json();
        setProducts(Array.isArray(data) ? data : []);
      } catch (e) {
        console.error("Chyba při načítání produktů:", e);
      }
    })();
  }, []);

  const count = products.length;

  const showDesktop = 3;
  const scrollDesktop = 3;
  const showTablet = 2;
  const scrollTablet = 2;
  const showMobile = 1;
  const scrollMobile = 1;

  const settings = useMemo(
    () => ({
      dots: false,
      arrows: true, // ✅ šipky
      nextArrow: <Arrow direction="next" />,
      prevArrow: <Arrow direction="prev" />,
      infinite: count > showDesktop,
      autoplay: count > 1,
      autoplaySpeed: 8000, // ✅ zpomaleno (12 s)
      speed: 900,
      cssEase: "ease-in-out",
      slidesToShow: Math.min(showDesktop, Math.max(1, count || 1)),
      slidesToScroll: Math.min(scrollDesktop, Math.max(1, count || 1)),
      pauseOnHover: true,
      swipeToSlide: true,
      draggable: true,
      touchMove: true,
      responsive: [
        {
          breakpoint: 1024,
          settings: {
            slidesToShow: Math.min(showTablet, Math.max(1, count || 1)),
            slidesToScroll: Math.min(scrollTablet, Math.max(1, count || 1)),
            infinite: count > showTablet,
          },
        },
        {
          breakpoint: 640,
          settings: {
            slidesToShow: showMobile,
            slidesToScroll: scrollMobile,
            infinite: count > showMobile,
          },
        },
      ],
    }),
    [count]
  );

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
        <Slider {...settings} key={`slider-${count}`}>
          {products.map((product) => (
            <div
              key={product.id ?? slugify(product.name)}
              onClick={() => navigate(`/shop/${slugify(product.name)}`)}
              className="px-3"
            >
              <div className="rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 cursor-pointer overflow-hidden bg-transparent">
                <div className="w-full aspect-square overflow-hidden">
                  <img
                    src={product.image_url}
                    alt={product.name}
                    loading="lazy"
                    decoding="async"
                    className="block w-full h-full object-cover object-center"
                  />
                </div>
                <div className="px-2 sm:px-3 py-3 bg-transparent">
                  <p className="text-center text-pink-50 md:text-pink-100 font-semibold text-sm sm:text-base line-clamp-2">
                    {emojify(product.name)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </Slider>
      </div>
    </section>
  );
}
