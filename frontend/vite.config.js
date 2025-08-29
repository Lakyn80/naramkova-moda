// frontend/vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Můžeš přepsat env proměnnou VITE_LAN_IP, jinak zůstane tato
const LAN_IP = process.env.VITE_LAN_IP || "172.20.10.4";

export default defineConfig({
  plugins: [react()],
  define: { global: "window" },
  base: "/",
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: {
    host: "0.0.0.0",
    port: 3000,
    strictPort: true,
    hmr: {
      protocol: "ws",
      host: LAN_IP,
      port: 3000,
    },
    proxy: {
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true,
        secure: false,
      },
      // ✅ DŮLEŽITÉ: přidej i /static, aby šly uploady přes backend (Flask)
      "/static": {
        target: "http://localhost:5001",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
