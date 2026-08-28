/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        background: "#151515",
        card: "#1b1b1b",
        "card-hover": "#252525",
        border: "#343434",
        textPrimary: "#f1efed",
        textSecondary: "#a7a29f",
        brandBlue: "#f0eeeb",
        brandGreen: "#bdb8b2",
        brandPurple: "#aaa09a",
        brandRed: "#e58a83",
        brandYellow: "#f0eeeb",
      },
      backdropBlur: {
        xs: "2px",
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
        "glass-inset": "none",
      }
    },
  },
  plugins: [],
}
