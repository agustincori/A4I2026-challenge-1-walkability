import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    host: true,
    proxy: {
      '/api/cloudrun': {
        target: 'https://atlanta-heat-advisor-hxywpvumaq-uc.a.run.app',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/cloudrun/, ''),
      },
    },
  },
  preview: {
    port: 8080,
    host: true,
    proxy: {
      '/api/cloudrun': {
        target: 'https://atlanta-heat-advisor-hxywpvumaq-uc.a.run.app',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/cloudrun/, ''),
      },
    },
  },
});
