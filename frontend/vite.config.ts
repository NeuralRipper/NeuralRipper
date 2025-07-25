import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import wasm from 'vite-plugin-wasm'
import topLevelAwait from 'vite-plugin-top-level-await'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), wasm(), topLevelAwait()],
  preview: {
    allowedHosts: true  // Allow all hosts
  },
  optimizeDeps: {
    exclude: ['@rerun-io/web-viewer-react']
  },
  server: {
    allowedHosts: true  // Allow all hosts
  }
})
