import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "kipiai-dark": "#080808",
        "kipiai-blue": "#116dff",
        "kipiai-blue-hover": "#3899ec",
        "kipiai-blue-light": "#7fccf7",
        "kipiai-gray": "#6c757d",
        "kipiai-green": "#28a745",
        "kipiai-yellow": "#ffc107",
        "kipiai-red": "#dc3545",
      },
      fontFamily: {
        sans: ["Inter", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
