// frontend/vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// 🔧 Nastav si svou LAN IP (z předchozích logů to vypadalo na 172.20.10.4)
// Můžeš ji přepsat ručně níž, nebo spouštět s proměnnou VITE_LAN_IP.
const LAN_IP = process.env.VITE_LAN_IP || "172.20.10.4";

export default defineConfig({
  plugins: [react()],
  define: { global: "window" },
  base: "/", // bez prefixu
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: {
    host: "0.0.0.0", // umožní přístup z mobilu v LAN
    port: 3000,
    strictPort: true,
    hmr: {
      protocol: "ws",
      host: LAN_IP,   // <- TADY musí být tvoje LAN IP, ať funguje HMR na mobilu
      port: 3000,
    },
    proxy: {
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
