import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  preview: {
    allowedHosts: true  // Allow all hosts
  },
  server: {
    allowedHosts: true  // Allow all hosts
  }
})
