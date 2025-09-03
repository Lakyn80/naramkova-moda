import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());
  const isDev = mode === "development";

  // 👇 jediná přidaná věc: default na localhost:5050, když není VITE_API_BASE_URL
  const apiBase = env.VITE_API_BASE_URL || "http://localhost:5050";
  

  return {
    plugins: [react()],
    define: {
      global: "window",
    },
    base: isDev ? "/" : "/naramkova-moda/",
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
        "/api": {
          target: apiBase,      // 👈 jen tohle jsem upravil
          changeOrigin: true,
          secure: false,
        },
      },
    },
  };
});
