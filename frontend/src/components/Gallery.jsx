// frontend/src/components/Gallery.jsx
import React, { useEffect, useState } from "react";
import Slider from "react-slick";
import { useNavigate } from "react-router-dom";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";

export default function Gallery() {
  const [products, setProducts] = useState([]);
  const navigate = useNavigate();

  const makeSlug = (s) =>
    String(s || "").toLowerCase().trim().replace(/\s+/g, "-");

  const toUploadUrl = (input) => {
    if (!input) return "";
    let u = String(input).trim();
    u = u.replace(/^https?:\/\/[^/]+/i, "");
    if (u.startsWith("/api/static/uploads/")) u = u.replace("/api", "");
    if (u.startsWith("/static/uploads/")) return u;
    if (u.startsWith("/")) return u;
    return `/static/uploads/${u}`;
  };

  const onImgError = (e) => {
    const el = e.currentTarget;
    try {
      const u = new URL(el.src, window.location.origin);
      const dir = u.pathname.substring(0, u.pathname.lastIndexOf("/") + 1);
      const name = u.pathname.split("/").pop() || "";
      const alt1 = name.includes("_") ? name.replace(/_/g, "-") : name.replace(/-/g, "_");
      if (alt1 !== name) {
        el.dataset.fallbackTried = "1";
        el.src = `${dir}${alt1}`;
        return;
      }
      const alt2 = name.toLowerCase();
      if (el.dataset.fallbackTried !== "2" && alt2 !== name) {
        el.dataset.fallbackTried = "2";
        el.src = `${dir}${alt2}`;
        return;
      }
    } catch (_) {}
    el.onerror = null;
    el.src = "/placeholder.png";
  };

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const res = await fetch("/api/products/");
        const data = await res.json();
        const mapped = (Array.isArray(data) ? data : []).map((p) => ({
          ...p,
          image_url: toUploadUrl(p.image_url || p.image),
        }));
        setProducts(mapped);
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
          {products.map((product) => (
            <div
              key={product.id ?? product.name}
              onClick={() => navigate(`/shop/${product.slug || makeSlug(product.name)}`)}
              className="px-3"
            >
              <div className="rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 cursor-pointer overflow-hidden bg-transparent">
                <div className="w-full aspect-square overflow-hidden">
                  <img
                    src={product.image_url}
                    alt={product.name}
                    loading="lazy"
                    decoding="async"
                    onError={onImgError}
                    className="block w-full h-full object-cover object-center"
                  />
                </div>
                <div className="px-2 sm:px-3 py-3 bg-transparent">
                  <p className="text-center text-pink-50 md:text-pink-100 font-semibold text-sm sm:text-base line-clamp-2">
                    {product.name}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </Slider>

        <div className="h-2 bg-pink-300/60 mt-6 rounded-full overflow-hidden">
          <div className="h-full bg-pink-500/80 transition-all duration-500 w-full animate-pulse" />
        </div>
      </div>
    </section>
  );
}
