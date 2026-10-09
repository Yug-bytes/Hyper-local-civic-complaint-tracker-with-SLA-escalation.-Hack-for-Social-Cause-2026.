/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "#F6F7F4",
        ink: "#1E2A32",
        civic: {
          DEFAULT: "#1D5C8A",
          hover: "#16496E",
          light: "#EAF2F8",
        },
        line: "#D5DADD",
        status: {
          submitted: "#6B7785",
          assigned: "#1D5C8A",
          progress: "#B87600",
          resolved: "#2E7D4F",
          overdue: "#B3261E",
        },
      },
      fontFamily: {
        sans: [
          '"Public Sans"',
          '"Inter"',
          '"Noto Sans Devanagari"',
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
      maxWidth: {
        mobile: "440px",
      },
    },
  },
  plugins: [],
}
