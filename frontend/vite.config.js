import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['.ngrok-free.dev'],
    proxy: {
      // Forward standard API calls to the backend
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      // Forward WebSocket chat messages to the backend
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true
      }
    }
  }
})