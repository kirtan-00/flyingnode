import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        fn: {
          blue: "#001B94",
          "blue-dark": "#00137A",
          orange: "#FF6B00",
          bg: "#F6F7FB",
          ink: "#0B1020",
          muted: "#6B7385",
          card: "#FFFFFF",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui"],
        body: ["var(--font-body)", "system-ui"],
      },
      boxShadow: {
        fn: "0 8px 32px rgba(0, 27, 148, 0.08)",
        "fn-hover": "0 12px 40px rgba(0, 27, 148, 0.14)",
      },
      borderRadius: {
        card: "16px",
      },
    },
  },
} satisfies Config;
