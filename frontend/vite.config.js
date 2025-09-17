import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());
  const isDev = mode === "development";

  // Dev proxy cíl – když není definováno, spadne to na localhost:5050
  const apiBase = env.VITE_API_BASE_URL || "http://localhost:5050";

  return {
    plugins: [react()],
    define: {
      global: "window",
    },
    // ✅ V produkci servírujeme z kořene domény
    base: isDev ? "/" : "/",
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
      },
    },
    server: {
      port: 3000,
      strictPort: true,
      hmr: {
        protocol: "ws",
        host: "localhost",
        port: 3000,
      },
      proxy: {
        // FE volá /api → v devu proxy na backend; v produkci to řeší Nginx
        "/api": {
          target: apiBase,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  };
});
