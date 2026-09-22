/** @type {import('tailwindcss').Config} */

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {
    extend: {
      colors: {
        docsure: {
          50: "#f4f8ff",
          100: "#e9f1ff",
          200: "#cfe0ff",
          300: "#a9c8ff",
          400: "#78a9ff",
          500: "#4d87f7",
          600: "#356de0",
          700: "#2856b8",
          800: "#254995",
          900: "#233f78",
        },
      },

      boxShadow: {
        soft: "0 10px 35px rgba(15, 23, 42, 0.07)",
        card: "0 4px 20px rgba(15, 23, 42, 0.06)",
      },

      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.35s ease-out",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },

      keyframes: {
        fadeIn: {
          "0%": {
            opacity: "0",
          },
          "100%": {
            opacity: "1",
          },
        },

        slideUp: {
          "0%": {
            opacity: "0",
            transform: "translateY(8px)",
          },
          "100%": {
            opacity: "1",
            transform: "translateY(0)",
          },
        },

        pulseSoft: {
          "0%, 100%": {
            opacity: "1",
          },
          "50%": {
            opacity: "0.55",
          },
        },
      },
    },
  },

  plugins: [],
};