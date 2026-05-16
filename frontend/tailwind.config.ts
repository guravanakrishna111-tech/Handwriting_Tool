import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f7f0df",
        ink: "#211b15",
        clay: "#a94734",
        moss: "#516a55",
        rule: "#7fa0c7"
      },
      boxShadow: {
        paper: "0 24px 70px rgba(57, 39, 19, 0.16)"
      },
      fontFamily: {
        studio: ["var(--font-studio)", "Georgia", "serif"],
        ui: ["var(--font-ui)", "Inter", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
