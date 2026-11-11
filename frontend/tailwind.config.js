/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        elevated: "var(--elevated)",
        card: "var(--card)",
        lime: "var(--lime)",
        ink: "var(--ink)",
        muted: "var(--muted)",
        good: "var(--good)",
        warn: "var(--warn)",
        bad: "var(--bad)",
        panel: "var(--panel)",
        pine: "var(--pine)",
      },
      boxShadow: {
        frame: "0 30px 80px rgba(18, 22, 28, 0.28)",
      },
      fontFamily: {
        sans: ['"Segoe UI"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
