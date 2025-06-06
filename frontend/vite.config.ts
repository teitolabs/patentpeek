import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy requests from /api to your backend server
      '/api': {
        target: 'http://127.0.0.1:8000', // <-- THIS MUST MATCH YOUR BACKEND ADDRESS
        changeOrigin: true,
        secure: false,      
      }
    }
  }
})