/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          500: '#0284c7',
          600: '#0369a1',
          700: '#075985',
          800: '#0c4a6e',
          900: '#082f49',
        },
        heat: {
          low: '#22c55e',
          medium: '#eab308',
          high: '#f97316',
          extreme: '#ef4444',
          critical: '#991b1b',
        }
      }
    },
  },
  plugins: [],
}
