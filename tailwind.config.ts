import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/app/**/*.{ts,tsx}", "./src/components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        forest: {
          50: "#edfdf6",
          100: "#d3f8e8",
          500: "#0f9f72",
          600: "#087f5b",
          700: "#056348",
          900: "#063b2d",
        },
        ink: "#17211d",
      },
      boxShadow: {
        phone: "0 28px 80px rgba(6, 59, 45, 0.26)",
        card: "0 16px 40px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
