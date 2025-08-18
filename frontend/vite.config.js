import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path"; // ← nutné pro alias

export default defineConfig(({ mode }) => {
  const isDev = mode === "development";

  return {
    plugins: [react()],
    define: {
      global: "window", // Fix pro react-image-lightbox
    },
    base: "/",
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"), // ✅ alias @ → src/
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
      proxy: isDev
        ? {
            "/api": {
              target: "http://localhost:5000",
              changeOrigin: true,
              secure: false,
            },
          }
        : undefined,
    },
  };
});
