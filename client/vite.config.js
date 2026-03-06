import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  envDir: '../',
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': 'http://server:5000',
      '/auth': 'http://server:5000'
    }
  }
})