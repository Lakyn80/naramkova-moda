// vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// ✅ Exportuje widget jako IIFE do global scope
export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: "src/index.jsx",
      name: "ChatWidget", // ✅ důležité – export jako window.ChatWidget
      fileName: () => "chat-widget.js",
    },
    rollupOptions: {
      output: {
        globals: {
          react: "React",
          "react-dom": "ReactDOM",
        },
      },
      external: ["react", "react-dom"],
    },
  },
});
