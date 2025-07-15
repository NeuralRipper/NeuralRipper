/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        'terminus': ['Terminus', 'monospace'],
        'matrix': ['JetBrains Mono', 'Fira Code', 'Source Code Pro', 'monospace'],
        'cyber': ['Space Mono', 'Roboto Mono', 'monospace'],
        'console': ['Consolas', 'Monaco', 'Courier New', 'monospace'],
      }
    }
  },
  plugins: [],
}