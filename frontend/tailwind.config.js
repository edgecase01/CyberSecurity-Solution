/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        slate: {
          950: "#020617",
        },
        cyber: {
          400: "#22d3ee",
          500: "#06b6d4",
          600: "#0891b2",
        },
        threat: {
          400: "#fb7185",
          500: "#f43f5e",
        },
      },
      boxShadow: {
        glow: "0 0 40px rgba(34, 211, 238, 0.12)",
      },
    },
  },
  plugins: [],
};
