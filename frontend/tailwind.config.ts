import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "media",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef7ff",
          100: "#d9ecff",
          500: "#2f80ed",
          600: "#1f6fd6",
          700: "#1a5bb0",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
