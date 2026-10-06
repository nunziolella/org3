/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        dark: {
          950: "#050505",
          900: "#0A0A0A",
          850: "#0F0F0F",
          800: "#141414",
          700: "#1F1F1F",
          600: "#2E2E2E",
        },
        accent: {
          orange: "#F97316",
          orangeHover: "#EA580C",
          emerald: "#10B981",
          cyan: "#06B6D4",
          violet: "#8B5CF6",
          amber: "#F59E0B",
          rose: "#F43F5E",
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
