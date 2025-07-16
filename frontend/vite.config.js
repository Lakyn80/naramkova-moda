import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const isDev = mode === 'development';

  return {
    plugins: [react()],
    define: {
      global: 'window', // Fix pro react-image-lightbox
    },
    base: '/', // důležité pro Railway nebo Netlify
    server: {
      proxy: isDev
        ? {
            '/api': {
              target: 'http://localhost:5000',
              changeOrigin: true,
              secure: false,
            },
          }
        : undefined, // proxy není potřeba v produkci
    },
  };
});
