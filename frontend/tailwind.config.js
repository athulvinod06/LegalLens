/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        legal: {
          50: '#f8fafc',
          100: '#f1f5f9',
          500: '#1e293b',
          700: '#0f172a',
          900: '#020617',
        }
      }
    },
  },
  plugins: [],
}
