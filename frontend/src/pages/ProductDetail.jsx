import React, { useEffect, useState, useMemo } from "react";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";
import Thumbnails from "yet-another-react-lightbox/plugins/thumbnails";
import "yet-another-react-lightbox/plugins/thumbnails.css";
import Zoom from "yet-another-react-lightbox/plugins/zoom";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { slugify } from "../utils/slugify";
import { emojify } from "../utils/emojify";
import { absoluteUploadUrl } from "../utils/image";

const API_BASE = import.meta.env.VITE_API_BASE || `${window.location.origin}/api`;

function renderEmojiSafe(text) {
  const s = String(text ?? "");
  const parts = s.split(/([\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}])/gu);
  const isEmoji = (t) => /^[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]$/u.test(t);
  return parts.map((chunk, i) =>
    isEmoji(chunk) ? <span key={`e${i}`} className="text-white">{chunk}</span> : <span key={`t${i}`}>{chunk}</span>
  );
}

export default function ProductDetail() {
  const { slug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const backTarget = location.state?.from || "/shop";

  const [product, setProduct] = useState(null);
  const [photoIndex, setPhotoIndex] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedVariantId, setSelectedVariantId] = useState(null);
  const [variantsOpen, setVariantsOpen] = useState(false);
  const variantParam = searchParams.get("variant");
  const wristParam = searchParams.get("wrist") || searchParams.get("wrist_size");

  const variantOptions = useMemo(() => {
    if (!product) return [];

    const basePrice = Number(product.price ?? product.price_czk ?? 0);

    const baseImage =
      (Array.isArray(product.images) ? product.images[0] : null) || product.image_url;
    const baseVariant = {
      id: "__base__",
      variant_name: product.name || "Puvodni varianta",
      wrist_size: "",
      image_url: baseImage,
      image: baseImage,
      media: Array.isArray(product.media) ? product.media : [],
      stock: Number(product.stock ?? 0),
      isBase: true,
      price_czk: basePrice,
      description: product.description || "",
    };

    const normalizedVariants = Array.isArray(product.variants)
      ? product.variants.map((v) => ({
          ...v,
          image_url: v.image_url || v.image,
          stock: Number(v.stock ?? 0),
          price_czk: Number(v.price_czk ?? v.price ?? product.price ?? product.price_czk ?? 0),
          description: v.description || "",
        }))
      : [];

    return [baseVariant, ...normalizedVariants];
  }, [product]);

  useEffect(() => {
    let isMounted = true;

    (async () => {
      try {
        const res = await fetch(`${API_BASE}/products/`);
        const data = await res.json();

        if (!isMounted) return;

        const found = (data || []).find(
          (p) => slugify(p?.name || "").replace(/-+/g, "-") === slug
        );
        if (!found) {
          setProduct(null);
          return;
        }

        const price =
          typeof found.price === "number"
            ? found.price
            : typeof found.price_czk === "number"
            ? found.price_czk
            : Number(found.price) || 0;

        const normalizeImageUrl = (u) => {
          if (!u) return null;
          return absoluteUploadUrl(u);
        };

        const mapMediaEntry = (m) => {
          if (!m) return null;
          if (typeof m === "string") return normalizeImageUrl(m);
          return normalizeImageUrl(m.image_url || m.image);
        };

        const variants = Array.isArray(found.variants)
          ? found.variants.map((v) => ({
              ...v,
              image_url: normalizeImageUrl(v.image_url || v.image),
              image: normalizeImageUrl(v.image || v.image_url),
              media: Array.isArray(v.media)
                ? v.media.map((m) => ({
                    ...m,
                    image_url: mapMediaEntry(m),
                    image: mapMediaEntry(m),
                  }))
                : [],
            }))
          : [];

        const baseMediaRaw = Array.isArray(found.media)
          ? found.media
          : Array.isArray(found.images)
          ? found.images
          : [];

        const baseMedia = baseMediaRaw.map(mapMediaEntry).filter(Boolean);

        const baseImages = [
          normalizeImageUrl(found.image_url || found.image),
          ...baseMedia,
        ]
          .filter(Boolean)
          .filter((v, i, a) => a.indexOf(v) === i);

        const stockNumber = Number(found.stock ?? 1);

        setProduct({
          ...found,
          stock: Number.isFinite(stockNumber) && stockNumber >= 0 ? stockNumber : 1,
          price,
          image_url: baseImages[0] || null,
          images: baseImages,
          media: baseMedia,
          variants,
        });

        setPhotoIndex(0);
        setIsOpen(false);
      } catch (err) {
        console.error("Chyba pri nacitani produktu:", err);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [slug]);

  useEffect(() => {
    if (!variantOptions.length) return;

    const next =
      variantOptions.find((v) => String(v.id) === String(variantParam)) ||
      variantOptions.find(
        (v) =>
          wristParam &&
          v.wrist_size &&
          v.wrist_size.toLowerCase() === String(wristParam).toLowerCase()
      ) ||
      variantOptions[0];

    if (next && String(next.id) !== String(selectedVariantId)) {
      setSelectedVariantId(String(next.id));
      setVariantsOpen(false);
    }
  }, [variantOptions, variantParam, wristParam]);

  const selectedVariant = useMemo(
    () =>
      variantOptions.find((v) => String(v.id) === String(selectedVariantId)) ||
      null,
    [variantOptions, selectedVariantId]
  );

  const activePrice = useMemo(() => {
    if (selectedVariant) {
      const priceVal = selectedVariant.price_czk ?? selectedVariant.price;
      const parsed = Number(priceVal);
      if (Number.isFinite(parsed)) return parsed;
    }
    const fallback = Number(product?.price ?? product?.price_czk);
    return Number.isFinite(fallback) ? fallback : 0;
  }, [selectedVariant, product]);

  const activeDescription = useMemo(
    () => (selectedVariant?.description || product?.description || "").trim(),
    [selectedVariant, product]
  );

  const baseImages = useMemo(() => {
    if (!product) return [];
    const baseList = Array.isArray(product.images) ? product.images : [];
    const fallback = product.image_url ? [product.image_url] : [];
    return Array.from(new Set([...fallback, ...baseList].filter(Boolean)));
  }, [product]);

  const displayImages = useMemo(() => {
    if (!product) return [];
    const variantImages = [];

    if (selectedVariant) {
      const preferred = selectedVariant.image_url || selectedVariant.image;
      if (preferred) variantImages.push(preferred);

      if (Array.isArray(selectedVariant.media)) {
        selectedVariant.media.forEach((m) => {
          const img = m?.image_url || m?.image;
          if (img) variantImages.push(img);
        });
      }
    }

    const uniqueVariantImages = Array.from(new Set(variantImages.filter(Boolean)));
    if (uniqueVariantImages.length) {
      const merged = [...uniqueVariantImages];
      baseImages.forEach((img) => {
        if (!merged.includes(img)) merged.push(img);
      });
      return merged;
    }

    return baseImages;
  }, [product, selectedVariant, baseImages]);

  useEffect(() => {
    if (!displayImages.length) {
      setPhotoIndex(0);
      return;
    }

    const preferred =
      selectedVariant?.image_url || selectedVariant?.image;

    if (preferred) {
      const idx = displayImages.indexOf(preferred);
      if (idx !== -1) {
        setPhotoIndex(idx);
        return;
      }
    }

    setPhotoIndex((idx) => Math.min(idx, displayImages.length - 1));
  }, [displayImages, selectedVariant]);

  const handleAddToCart = () => {
    const activeStock = Number.isFinite(Number(selectedVariant?.stock))
      ? Number(selectedVariant.stock)
      : Number(product?.stock);
    if (!product || activeStock === 0) return;

    const activeVariant = selectedVariant || variantOptions[0] || null;
    const isBase = activeVariant?.id === "__base__";

    const variantPayload =
      activeVariant && !isBase
        ? {
            variantId: activeVariant.id,
            variantName: activeVariant.variant_name,
            wristSize: activeVariant.wrist_size,
            image: activeVariant.image_url || activeVariant.image,
            stock: activeStock,
          }
        : {};

    addToCart({
      id: product.id,
      name: product.name,
      price: activePrice,
      quantity: 1,
      image: variantPayload.image || product.image_url,
      stock: activeStock,
      ...variantPayload,
    });
  };

  if (!product) {
    return (
      <section className="pt-28 pb-12 bg-gradient-to-br from-pink-300 to-pink-200 min-h-screen flex items-center justify-center">
        <div className="text-center text-lg text-pink-900">
          Produkt nenalezen.
        </div>
      </section>
    );
  }

  const slides = displayImages.map((src) => ({ src }));
  const activeStock = Number.isFinite(Number(selectedVariant?.stock))
    ? Number(selectedVariant.stock)
    : Number(product.stock);
  const out = Number(activeStock) === 0;

  const handleBack = () => {
    const lastShop = sessionStorage.getItem("lastShopUrl");
    const target = location.state?.from || lastShop || backTarget || "/shop";
    navigate(target, { replace: false });
  };

  return (
    <section className="pt-28 pb-12 bg-gradient-to-br from-pink-300 to-pink-200 min-h-screen">
      <div className="container mx-auto max-w-4xl px-4">
        <div className="mb-4">
          <button
            type="button"
            onClick={handleBack}
            className="inline-flex items-center gap-2 text-pink-800 font-semibold hover:underline"
          >
            Zpet do obchodu
          </button>
        </div>

        <div className="bg-white/20 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-white/40">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">

              {/* Obrazky */}
            <div className="space-y-4 relative">
              <div className="absolute top-2 left-2 z-10">
                {out ? (
                  <span className="px-2 py-1 text-xs font-semibold rounded bg-red-600/90 text-white">
                    Vyprodano
                  </span>
                ) : (
                  <span className="px-2 py-1 text-xs font-semibold rounded bg-emerald-600/90 text-white">
                    Skladem: {activeStock}
                  </span>
                )}
              </div>

              <img
                src={displayImages[photoIndex] || "/placeholder.png"}
                alt={product.name}
                className="w-full h-[260px] sm:h-[300px] md:h-[360px] object-cover rounded-xl shadow-lg cursor-pointer transition-transform duration-300 hover:scale-[1.02]"
                onClick={() => displayImages.length && setIsOpen(true)}
              />

              <div className="flex gap-2 flex-wrap justify-center sm:justify-start">
                {displayImages.map((img, i) => (
                  <img
                    key={i}
                    src={img}
                    alt={`${product.name} ${i + 1}`}
                    onClick={() => setPhotoIndex(i)}
                    className={`h-16 w-16 sm:h-20 sm:w-20 object-cover rounded-lg cursor-pointer border-2 ${
                      photoIndex === i ? "border-pink-500 shadow-lg" : "border-transparent"
                    } transition duration-300 hover:scale-105`}
                  />
                ))}
              </div>
            </div>

            {/* Popis */}
            <div className="flex flex-col justify-center">
              <h2 className="text-2xl sm:text-3xl font-extrabold bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent drop-shadow-lg">
                {renderEmojiSafe(emojify(product.name))}
              </h2>

              <p className="text-xl font-semibold text-pink-700 mt-2 drop-shadow-sm">
                {Number.isFinite(activePrice) ? activePrice.toFixed(2) : product.price} Kč
              </p>

              <button
                type="button"
                onClick={handleBack}
                className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-pink-800 hover:text-pink-900 underline decoration-2"
              >
                Zpet do obchodu
              </button>

              {/* --- ZDE NOVE VARIANTY --- */}
              {variantOptions.length > 1 && (
                <div className="mt-4 relative">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Vyberte variantu
                  </label>

                  <button
                    type="button"
                    onClick={() => setVariantsOpen((v) => !v)}
                    className="w-full border border-amber-300 rounded-xl bg-gradient-to-r from-stone-100 to-amber-50 px-4 py-3 shadow-sm hover:shadow-md flex items-center justify-between gap-3 transition"
                  >
                    <div className="flex items-center gap-3 text-left">
                      {selectedVariant?.image_url && (
                        <img
                          src={selectedVariant.image_url}
                          alt={selectedVariant.variant_name}
                          className="w-12 h-12 object-cover rounded-lg border border-amber-200"
                        />
                      )}
                      <div>
                        <div className="text-sm font-semibold text-gray-900">
                          {selectedVariant?.variant_name || "Varianta"}
                        </div>
                        {selectedVariant?.wrist_size && (
                          <div className="text-xs text-gray-600">
                            {selectedVariant.wrist_size}
                          </div>
                        )}
                        {Number.isFinite(Number(selectedVariant?.stock)) && (
                          <div className="text-xs text-emerald-700">
                            Skladem: {Number(selectedVariant.stock)}
                          </div>
                        )}
                      </div>
                    </div>
                    <span className="text-amber-700 text-lg leading-none">
                      {variantsOpen ? "^" : "v"}
                    </span>
                  </button>

                  {variantsOpen && (
                    <div className="absolute z-30 mt-2 w-full rounded-xl border border-amber-200 bg-white shadow-xl max-h-64 overflow-auto">
                      {variantOptions.map((v) => {
                        const active = String(v.id) === String(selectedVariantId);
                        return (
                          <button
                            type="button"
                            key={v.id}
                            onClick={() => {
                              setSelectedVariantId(String(v.id));
                              setVariantsOpen(false);
                            }}
                            className={`w-full px-4 py-3 flex items-center gap-3 text-left transition ${
                              active
                                ? "bg-gradient-to-r from-amber-100 to-orange-50 border-l-4 border-amber-500"
                                : "hover:bg-amber-50"
                            }`}
                          >
                            {v.image_url && (
                              <img
                                src={v.image_url}
                                alt={v.variant_name}
                                className="w-10 h-10 object-cover rounded-md border border-amber-100"
                              />
                            )}
                            <div className="text-sm font-medium text-gray-900">
                            {v.variant_name || "Varianta"}
                            {v.wrist_size && (
                              <span className="text-xs text-gray-600 block">
                                {v.wrist_size}
                              </span>
                            )}
                            {Number.isFinite(Number(v.stock)) && (
                              <span className="text-[11px] text-emerald-700 block">
                                Skladem: {Number(v.stock)}
                              </span>
                            )}
                          </div>
                        </button>
                      );
                    })}
                    </div>
                  )}
                </div>
              )}

              <p className="mt-3 text-base sm:text-lg text-gray-800 leading-relaxed" style={{ whiteSpace: "pre-line" }}>
                {emojify(activeDescription || "Detail produktu zde.")}
              </p>

              <button
                onClick={handleAddToCart}
                disabled={out}
                className={`mt-6 py-2 px-5 rounded-lg shadow-lg transition-transform transform hover:-translate-y-0.5 ${
                  out
                    ? "bg-gray-400 cursor-not-allowed text-white"
                    : "bg-gradient-to-r from-pink-600 to-pink-700 hover:from-pink-700 hover:to-pink-800 text-white"
                }`}
                title={out ? "Produkt je vyprodany" : "Pridat do kosiku"}
              >
                {out ? "Vyprodano" : "Pridat do kosiku"}
              </button>

            </div>
          </div>
        </div>
      </div>

      {isOpen && slides.length > 0 && (
        <Lightbox
          open={isOpen}
          close={() => setIsOpen(false)}
          slides={slides}
          index={photoIndex}
          plugins={[Thumbnails, Zoom]}
          on={{ view: ({ index }) => setPhotoIndex(index) }}
        />
      )}
    </section>
  );
}
