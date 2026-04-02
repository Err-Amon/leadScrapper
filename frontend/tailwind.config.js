/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["'DM Sans'", "sans-serif"],
        mono:    ["'JetBrains Mono'", "monospace"],
      },
      colors: {
        brand: {
          50:  "#f0fdf4",
          100: "#dcfce7",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          900: "#14532d",
        },
        surface: {
          900: "#0a0f0d",
          800: "#111812",
          700: "#1a2318",
          600: "#243020",
          500: "#2e3d28",
        },
      },
      animation: {
        "pulse-slow":    "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in":       "fadeIn 0.4s ease forwards",
        "slide-up":      "slideUp 0.35s ease forwards",
        "slide-down":    "slideDown 0.3s ease forwards",
        "shimmer":       "shimmer 1.6s infinite linear",
        "toast-in":      "toastIn 0.35s cubic-bezier(0.34,1.56,0.64,1) forwards",
        "toast-out":     "toastOut 0.25s ease forwards",
        "scale-in":      "scaleIn 0.2s ease forwards",
        "counter-up":    "counterUp 0.5s ease forwards",
      },
      keyframes: {
        fadeIn:    { from: { opacity: "0" },
                     to:   { opacity: "1" } },
        slideUp:   { from: { opacity: "0", transform: "translateY(14px)" },
                     to:   { opacity: "1", transform: "translateY(0)" } },
        slideDown: { from: { opacity: "0", transform: "translateY(-10px)" },
                     to:   { opacity: "1", transform: "translateY(0)" } },
        shimmer:   {
          "0%":   { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
        toastIn:   { from: { opacity: "0", transform: "translateX(110%)" },
                     to:   { opacity: "1", transform: "translateX(0)" } },
        toastOut:  { from: { opacity: "1", transform: "translateX(0)" },
                     to:   { opacity: "0", transform: "translateX(110%)" } },
        scaleIn:   { from: { opacity: "0", transform: "scale(0.92)" },
                     to:   { opacity: "1", transform: "scale(1)" } },
        counterUp: { from: { opacity: "0", transform: "translateY(6px)" },
                     to:   { opacity: "1", transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};