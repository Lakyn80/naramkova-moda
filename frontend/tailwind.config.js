/** @type {import('tailwindcss').Config} */

import withMT from "@material-tailwind/react/utils/withMT";

export default withMT({
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",

    // Preline UI – verze 2.x
    "./node_modules/preline/**/*.js",
  ],

  theme: {
    extend: {
      // TVÉ BARVY A SHADCN PROMĚNNÉ
      colors: {
        'rose-dark': '#881337',
        'rose-mid': '#be185d',
        'rose-light': '#f9a8d4',

        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',

        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))'
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))'
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))'
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))'
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))'
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))'
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))'
        },

        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',

        chart: {
          1: 'hsl(var(--chart-1))',
          2: 'hsl(var(--chart-2))',
          3: 'hsl(var(--chart-3))',
          4: 'hsl(var(--chart-4))',
          5: 'hsl(var(--chart-5))'
        }
      },

      // GRADIENTY
      backgroundImage: {
        'gradient-hero': 'linear-gradient(to bottom, #881337, #be185d)',
        'gradient-categories': 'linear-gradient(to bottom, #be185d, #f472b6)',
        'gradient-gallery': 'linear-gradient(to bottom, #f9a8d4, #f472b6)'
      },

      // ANIMACE
      animation: {
        float: 'float 6s ease-in-out infinite',
        'gradient-x': 'gradient-x 6s ease infinite',
        shimmer: 'shimmer 2s infinite linear',
        scroll: 'scroll 40s linear infinite'
      },

      // KEYFRAMES
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" }
        },
        'gradient-x': {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" }
        },
        shimmer: {
          "0%": { backgroundPosition: "-100% 0" },
          "100%": { backgroundPosition: "100% 0" }
        },
        scroll: {
          "0%": { transform: "translateX(0%)" },
          "100%": { transform: "translateX(-50%)" }
        }
      },

      // SHADCN border radius
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)"
      },

      // FONT
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
    },
  },

  plugins: [
    require("tailwindcss-animate"),
    require("preline/plugin"), // <<< upraveno
  ],
});
