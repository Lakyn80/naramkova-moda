import React, { useState } from "react";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";
import Thumbnails from "yet-another-react-lightbox/plugins/thumbnails";
import "yet-another-react-lightbox/plugins/thumbnails.css";
import Zoom from "yet-another-react-lightbox/plugins/zoom";
import { slugify } from "../utils/slugify"; // ✅ přidáno

export default function ProductGallery({ images, productName }) {
  const [photoIndex, setPhotoIndex] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const slides = images.map((src) => ({ src }));

  return (
    <div className="space-y-4">
      <img
        src={images[photoIndex]}
        alt={productName}
        className="w-full h-[300px] sm:h-[400px] md:h-[450px] object-cover rounded-xl shadow-md cursor-pointer"
        onClick={() => setIsOpen(true)}
      />

      <div className="flex gap-3 flex-wrap justify-center sm:justify-start">
        {images.map((img, index) => (
          <img
            key={index}
            src={img}
            alt={`thumbnail-${index}`}
            onClick={() => setPhotoIndex(index)}
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
