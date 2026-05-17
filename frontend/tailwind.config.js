/** @type {import('tailwindcss').Config} */
import typography from "@tailwindcss/typography";
import flowbite from "flowbite/plugin";

export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts}", "./node_modules/flowbite/**/*.js"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Source Sans 3", "sans-serif"],
      },
      colors: {
        ink: {
          900: "#0b0f1a",
          800: "#111827",
        },
        glow: {
          500: "#36c2ff",
          700: "#0ea5e9",
        },
      },
    },
  },
  plugins: [typography, flowbite],
};
