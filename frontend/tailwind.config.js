/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Definujeme vlastní růžové odstíny pro konzistentní gradienty
        "rose-dark": "#881337",     // tmavě růžová
        "rose-mid": "#be185d",      // střední růžová
        "rose-light": "#f9a8d4",    // světle růžová
      },
      backgroundImage: {
        // Přímé gradienty pro použití přes Tailwind třídy
        "gradient-hero": "linear-gradient(to bottom, #881337, #be185d)",
        "gradient-categories": "linear-gradient(to bottom, #be185d, #f472b6)",
        "gradient-gallery": "linear-gradient(to bottom, #f472b6, #f9a8d4)",
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        "gradient-x": "gradient-x 6s ease infinite",
        shimmer: "shimmer 2s infinite linear",
        scroll: "scroll 40s linear infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "gradient-x": {
          "0%, 100%": {
            backgroundPosition: "0% 50%",
          },
          "50%": {
            backgroundPosition: "100% 50%",
          },
        },
        shimmer: {
          "0%": {
            backgroundPosition: "-100% 0",
          },
          "100%": {
            backgroundPosition: "100% 0",
          },
        },
        scroll: {
          "0%": { transform: "translateX(0%)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
    },
  },
  plugins: [],
};
