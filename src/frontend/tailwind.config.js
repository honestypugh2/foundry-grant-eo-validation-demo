/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        azure: {
          50: '#e6f2ff',
          100: '#cce5ff',
          200: '#99ccff',
          300: '#66b2ff',
          400: '#3399ff',
          500: '#0078D4',
          600: '#0066b3',
          700: '#005299',
          800: '#003d80',
          900: '#002966',
        },
      },
    },
  },
  plugins: [],
}
