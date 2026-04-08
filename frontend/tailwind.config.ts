import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "kipiai-dark": "#080808",
        "kipiai-dark-blue": "#0a0e1a",
        "kipiai-blue": "#116dff",
        "kipiai-blue-hover": "#3899ec",
        "kipiai-blue-light": "#7fccf7",
        "kipiai-blue-50": "#e8f1ff",
        "kipiai-blue-900": "#0a2d6e",
        "kipiai-purple": "#7c3aed",
        "kipiai-gray": "#6c757d",
        "kipiai-gray-50": "#f8f9fb",
        "kipiai-gray-800": "#1a1d2e",
        "kipiai-gray-900": "#0f1219",
        "kipiai-green": "#28a745",
        "kipiai-yellow": "#ffc107",
        "kipiai-red": "#dc3545",
      },
      fontFamily: {
        sans: ["Inter", "Arial", "sans-serif"],
      },
      backgroundImage: {
        "kipiai-gradient": "linear-gradient(135deg, #116dff 0%, #7c3aed 100%)",
        "kipiai-gradient-subtle":
          "linear-gradient(135deg, rgba(17,109,255,0.06) 0%, rgba(124,58,237,0.06) 100%)",
        "kipiai-sidebar":
          "linear-gradient(180deg, #0a0e1a 0%, #080808 100%)",
      },
      boxShadow: {
        "kipiai-sm": "0 1px 3px 0 rgba(17,109,255,0.06)",
        "kipiai-md": "0 4px 12px -2px rgba(17,109,255,0.08)",
        "kipiai-lg": "0 12px 32px -4px rgba(17,109,255,0.12)",
        "kipiai-glow": "0 0 20px -4px rgba(17,109,255,0.3)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 12px -2px rgba(17,109,255,0.2)" },
          "50%": { boxShadow: "0 0 20px -2px rgba(17,109,255,0.4)" },
        },
      },
      animation: {
        shimmer: "shimmer 2s ease-in-out infinite",
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
