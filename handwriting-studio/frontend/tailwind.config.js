export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        "paper-cream": "#FAFAF2",
        "paper-aged": "#F5F0DC",
        "ink-blue": "#1a3a6e",
        "ink-black": "#0a0a0a",
        "ui-warm": "#8B7355",
        "ui-accent": "#C4995A",
        "bg-warm": "#F7F3EE",
        "border-warm": "#DDD5C8"
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        serif: ["Playfair Display", "serif"],
        mono: ["JetBrains Mono", "monospace"]
      },
      boxShadow: {
        warm: "0 2px 12px rgba(139,115,85,0.12)",
        page: "0 18px 45px rgba(78,64,46,0.22)"
      }
    }
  },
  plugins: []
};

