import { defineConfig } from 'vite';

// 0.0.0.0 so ngrok (and LAN) can reach the console; API stays on 127.0.0.1 via proxy.
export default defineConfig({
  esbuild: { jsx: 'automatic' },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    // ngrok free/paid hostnames change; allow any tunnel host.
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
