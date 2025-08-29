// frontend/src/components/ProductGallery.jsx
import React, { useState } from "react";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";
import Thumbnails from "yet-another-react-lightbox/plugins/thumbnails";
import "yet-another-react-lightbox/plugins/thumbnails.css";
import Zoom from "yet-another-react-lightbox/plugins/zoom";

export default function ProductGallery({ images, productName }) {
  const [photoIndex, setPhotoIndex] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const slides = images.map((src) => ({ src }));

  const onImgError = (e) => {
    const el = e.currentTarget;
    try {
      const u = new URL(el.src, window.location.origin);
      const dir = u.pathname.substring(0, u.pathname.lastIndexOf("/") + 1);
      const name = u.pathname.split("/").pop() || "";
      const alt1 = name.includes("_") ? name.replace(/_/g, "-") : name.replace(/-/g, "_");
      if (alt1 !== name) { el.dataset.fallbackTried="1"; el.src = `${dir}${alt1}`; return; }
      const alt2 = name.toLowerCase();
      if (el.dataset.fallbackTried !== "2" && alt2 !== name) { el.dataset.fallbackTried="2"; el.src = `${dir}${alt2}`; return; }
    } catch (_) {}
    el.onerror = null;
    el.src = "/placeholder.png";
  };

  return (
    <div className="space-y-4">
      <img
        src={images[photoIndex]}
        alt={productName}
        className="w-full h-[300px] sm:h-[400px] md:h-[450px] object-cover rounded-xl shadow-md cursor-pointer"
        onClick={() => setIsOpen(true)}
        onError={onImgError}
      />

      <div className="flex gap-3 flex-wrap justify-center sm:justify-start">
        {images.map((img, index) => (
          <img
            key={index}
            src={img}
            alt={`thumbnail-${index}`}
            onClick={() => setPhotoIndex(index)}
            onError={onImgError}
            className={`h-20 w-20 sm:h-24 sm:w-24 object-cover rounded cursor-pointer border ${
              photoIndex === index ? "border-pink-500" : "border-transparent"
            } transition duration-300`}
          />
        ))}
      </div>

      {isOpen && (
        <Lightbox
          open={isOpen}
          close={() => setIsOpen(false)}
          slides={slides}
          index={photoIndex}
          plugins={[Thumbnails, Zoom]}
          on={{ view: ({ index }) => setPhotoIndex(index) }}
        />
      )}
    </div>
  );
}
