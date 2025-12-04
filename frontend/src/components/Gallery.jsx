import React, { useState, useEffect, useMemo, useRef } from "react";
import Slider from "react-slick";
import { useNavigate, useLocation } from "react-router-dom";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import { slugify } from "../utils/slugify";
import { emojify } from "../utils/emojify";

// API base follows current origin so it works on localhost:3000 behind nginx proxy
const API_BASE = `${window.location.origin}/api`;

// Hezká šipka mimo slider (bez dalších knihoven)
function Arrow({ className = "", onClick, direction = "next" }) {
  const isNext = direction === "next";
  const disabled = className.includes("slick-disabled");

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={isNext ? "Další" : "Předchozí"}
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
          <path d="M8 4l8 8-8 8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        ) : (
          <path d="M16 4L8 12l8 8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        )}
      </svg>
    </button>
  );
}

export default function Gallery() {
  const [products, setProducts] = useState([]);
  const navigate = useNavigate();
  const location = useLocation();
  const sliderRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/products/`);
        const data = await res.json();
        setProducts(Array.isArray(data) ? data : []);
      } catch (e) {
        console.error("Chyba při načítání produktů:", e);
      }
    })();
  }, []);

  const count = products.length;

  // Max 4 celé karty na desktopu, žádné „napůl“ karty
  const slidesToShowDesktop = Math.min(4, Math.max(1, count));
  const slidesToScrollDesktop = Math.min(4, Math.max(1, count));

  const settings = useMemo(
    () => ({
      dots: false,
      arrows: true,
      nextArrow: <Arrow direction="next" />,
      prevArrow: <Arrow direction="prev" />,
      infinite: count > 1,
      autoplay: count > 1,
      autoplaySpeed: 4000,
      speed: 600,
      cssEase: "ease-in-out",
      waitForAnimate: false,
      lazyLoad: "ondemand",
      slidesToShow: slidesToShowDesktop,
      slidesToScroll: slidesToScrollDesktop,
      pauseOnHover: true,
      swipeToSlide: true,
      draggable: true,
      touchMove: true,
      // ⚠️ centerMode vypnuto, aby nikdy „netrčela“ půlka karty
      centerMode: false,
      responsive: [
        {
          breakpoint: 1280,
          settings: {
            slidesToShow: Math.min(4, count),
            slidesToScroll: Math.min(4, count),
            infinite: count > 1,
          },
        },
        {
          breakpoint: 1024,
          settings: {
            slidesToShow: Math.min(3, count),
            slidesToScroll: Math.min(3, count),
            infinite: count > 1,
          },
        },
        {
          breakpoint: 640,
          settings: {
            slidesToShow: Math.min(2, count),
            slidesToScroll: 1,
            infinite: count > 1,
          },
        },
        {
          breakpoint: 480,
          settings: {
            slidesToShow: 1,
            slidesToScroll: 1,
            infinite: count > 1,
          },
        },
      ],
    }),
    [count]
  );

  // Reflow + rozjet autoplay po návratu
  useEffect(() => {
    const tick = () => window.dispatchEvent(new Event("resize"));
    const t1 = setTimeout(tick, 30);
    const t2 = setTimeout(tick, 180);
    const t3 = setTimeout(() => {
      try {
        sliderRef.current?.slickGoTo(0, true);
        sliderRef.current?.slickPlay?.();
      } catch {}
    }, 220);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [count, location.key]);

  return (
    <section
      id="galerie"
      className="relative py-20 px-3 sm:px-4 bg-gradient-to-b from-rose-light to-rose-mid overflow-hidden"
    >
      <style>{`
        .slick-slide > div { height: 100%; }
        @keyframes nmGlow {
          0%, 100% { box-shadow: 0 10px 25px rgba(236,72,153,0.15); }
          50%      { box-shadow: 0 16px 40px rgba(217,70,239,0.28); }
        }
        @keyframes nmShine {
          0%   { transform: translateX(-120%); }
          100% { transform: translateX(120%); }
        }
        @media (prefers-reduced-motion: reduce) {
          .nm-anim { animation: none !important; transition: none !important; }
        }
      `}</style>

      <img
        src="/wave.svg"
        alt="Wave top"
        className="absolute -top-[1px] left-0 w-full pointer-events-none rotate-180 z-0"
      />
      <h2 className="text-4xl sm:text-5xl font-extrabold text-center mb-10 bg-gradient-to-r from-pink-600 via-pink-400 to-fuchsia-600 text-transparent bg-clip-text drop-shadow-sm relative z-10">
        Galerie
      </h2>

      <div className="max-w-6xl mx-auto relative z-10">
        <Slider ref={sliderRef} {...settings} key={`slider-${location.key}-${count}`}>
          {products.map((product) => (
            <div
              key={product.id ?? slugify(product.name)}
              onClick={() => navigate(`/shop/${slugify(product.name)}`)}
              className="px-3 h-full"
            >
              <div className="max-w-[22rem] sm:max-w-[24rem] mx-auto">
                <div
                  className={[
                    "group h-full p-[1.5px] rounded-2xl",
                    "bg-gradient-to-br from-pink-400/70 via-fuchsia-500/60 to-rose-400/70",
                    "transition-all duration-300 nm-anim",
                    "hover:from-pink-400 hover:via-fuchsia-500 hover:to-rose-400",
                    "animate-[nmGlow_6s_ease-in-out_infinite]",
                  ].join(" ")}
                >
                  <div
                    className={[
                      "relative h-full flex flex-col rounded-2xl overflow-hidden cursor-pointer",
                      "bg-white/5 backdrop-blur-sm",
                      "shadow-lg transition-all duration-300 nm-anim",
                      "group-hover:-translate-y-0.5 group-hover:shadow-2xl",
                    ].join(" ")}
                  >
                    <span
                      aria-hidden
                      className={[
                        "pointer-events-none absolute inset-0 rounded-2xl opacity-0",
                        "bg-[linear-gradient(120deg,transparent_30%,rgba(255,255,255,0.22)_50%,transparent_70%)]",
                        "transition-opacity duration-300",
                        "group-hover:opacity-100",
                      ].join(" ")}
                      style={{ animation: "nmShine 1.2s ease-in-out 1" }}
                    />
                    <div className="w-full aspect-square overflow-hidden">
                      <img
                        src={product.image_url}
                        alt={product.name}
                        loading="lazy"
                        decoding="async"
                        className="block w-full h-full object-cover object-center transition-transform duration-500 nm-anim group-hover:scale-[1.04]"
                      />
                    </div>
                    <div className="px-2 sm:px-3 py-3 bg-transparent">
                      <p className="text-center text-pink-50 md:text-pink-100 font-semibold text-sm sm:text-base line-clamp-2 leading-snug min-h-[2.75rem] sm:min-h-[3.25rem]">
                        {emojify(product.name)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </Slider>
      </div>
    </section>
  );
}
