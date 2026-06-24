// Shared Tailwind preset — token-driven (CSS variables), consumed by both apps.
// Colors map to CSS vars set by the ThemeProvider from the active preset (blueprint/14).
import type { Config } from "tailwindcss";

export const swingaiPreset: Partial<Config> = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: { DEFAULT: "var(--primary)", foreground: "var(--primary-foreground)" },
        muted: { DEFAULT: "var(--muted)", foreground: "var(--muted-foreground)" },
        card: "var(--card)",
        border: "var(--border)",
        success: "var(--success)",
        destructive: "var(--destructive)",
        warning: "var(--warning)",
      },
      borderRadius: { lg: "var(--radius)", md: "calc(var(--radius) - 2px)" },
      fontFamily: { sans: ["var(--font-sans)", "system-ui", "sans-serif"] },
    },
  },
};

export default swingaiPreset;
