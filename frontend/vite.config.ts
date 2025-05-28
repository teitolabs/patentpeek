import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy /api requests to your Flask backend
      '/api': {
        target: 'http://localhost:5001', // Your Flask server address
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, '') // Optional: if your Flask routes don't start with /api
      }
    }
  }
})