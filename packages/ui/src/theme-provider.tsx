"use client";
// ThemeProvider — light/dark/system via next-themes + applies the active preset's
// CSS-variable tokens (blueprint/14). Resolution: user override → platform default → fallback.
import { ThemeProvider as NextThemes } from "next-themes";
import { useEffect } from "react";
import type { ThemePreset } from "@swingai/api-client";

const FALLBACK_LIGHT: Record<string, string> = {
  background: "#ffffff", foreground: "#0f172a", primary: "#2563eb",
  "primary-foreground": "#ffffff", muted: "#f1f5f9", "muted-foreground": "#64748b",
  card: "#ffffff", border: "#e2e8f0", success: "#16a34a", destructive: "#dc2626", warning: "#d97706",
};
const FALLBACK_DARK: Record<string, string> = {
  background: "#0b1120", foreground: "#e2e8f0", primary: "#3b82f6",
  "primary-foreground": "#0b1120", muted: "#1e293b", "muted-foreground": "#94a3b8",
  card: "#111827", border: "#1f2937", success: "#22c55e", destructive: "#ef4444", warning: "#f59e0b",
};

function applyTokens(tokens: Record<string, string>) {
  const root = document.documentElement;
  Object.entries(tokens).forEach(([k, v]) => root.style.setProperty(`--${k}`, v));
  if (!tokens.radius) root.style.setProperty("--radius", "0.625rem");
}

export function ThemeProvider({
  children, preset, isDark = false,
}: { children: React.ReactNode; preset?: ThemePreset | null; isDark?: boolean }) {
  useEffect(() => {
    const light = { ...FALLBACK_LIGHT, ...(preset?.tokensLight || {}) };
    const dark = { ...FALLBACK_DARK, ...(preset?.tokensDark || {}) };
    applyTokens(isDark ? dark : light);
  }, [preset, isDark]);

  return (
    <NextThemes attribute="class" defaultTheme="system" enableSystem>
      {children}
    </NextThemes>
  );
}
