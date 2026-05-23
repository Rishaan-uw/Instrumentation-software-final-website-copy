/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ['"IBM Plex Sans"', "ui-sans-serif", "sans-serif"],
        sans: ['"IBM Plex Sans"', "ui-sans-serif", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      colors: {
        // Ground: Husky Robotics pure-black surface tones.
        umbra: "#000000",
        soil: "#08080A",
        rock: "#101012",
        dusk: "#1F1F23",
        hair: "#2A2A30",
        // Inked typography: white on black, with zinc-grey midtones.
        bone: "#FFFFFF",
        sand: "#D4D4D8",
        ash: "#8A8A92",
        // Primary accent: violet (Husky Robotics brand purple).
        rust: "#7C5CFF",
        ember: "#9B85FF",
        amber: "#B5A5FF",
        sage: "#10B981",
        blood: "#EF4444",
        lake: "#52525B",
      },
      letterSpacing: {
        widest: "0.22em",
      },
      animation: {
        "fade-up": "fadeUp 700ms cubic-bezier(0.2, 0.8, 0.2, 1) both",
        "sweep-in": "sweepIn 900ms cubic-bezier(0.2, 0.8, 0.2, 1) both",
        "breathe": "breathe 2.4s ease-in-out infinite",
        "scan": "scan 6s linear infinite",
        "flicker": "flicker 1.2s ease-out",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        sweepIn: {
          "0%": { opacity: "0", transform: "translateX(-24px) scaleX(0.98)" },
          "100%": { opacity: "1", transform: "translateX(0) scaleX(1)" },
        },
        breathe: {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 0 0 rgba(124,92,255,0.55)" },
          "50%": { opacity: "0.7", boxShadow: "0 0 0 10px rgba(124,92,255,0)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        flicker: {
          "0%, 100%": { opacity: "1" },
          "12%": { opacity: "0.4" },
          "25%": { opacity: "1" },
          "40%": { opacity: "0.7" },
          "55%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
