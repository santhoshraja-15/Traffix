import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
        },
        traffic: {
          low: "#22c55e",
          moderate: "#eab308",
          high: "#f97316",
          congested: "#ef4444",
          emergency: "#dc2626",
        },
      },
    },
  },
  plugins: [],
};

export default config;
