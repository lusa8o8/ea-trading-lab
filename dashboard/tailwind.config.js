/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0a0a0a',
        card: '#111111',
        positive: '#00ff88',
        negative: '#ff4444',
        line: '#1f1f1f',
        muted: '#666666',
      },
    },
  },
  plugins: [],
}
