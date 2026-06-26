"use client";
// ThemeProvider (blueprint/14) — light/dark/system via next-themes + applies the active
// preset's CSS-variable tokens REACTIVELY to the resolved mode, plus font switching.
// Exposes useThemeControls() so the Settings/Appearance UI can change preset/font, with
// per-user override persisted in localStorage. Resolution: user override → platform default.
import { ThemeProvider as NextThemes, useTheme } from "next-themes";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
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

export const FONTS: Record<string, { label: string; stack: string; note: string }> = {
  inter: { label: "Inter", stack: '"Inter", system-ui, sans-serif', note: "Data-dense, highly legible" },
  manrope: { label: "Manrope", stack: '"Manrope", system-ui, sans-serif', note: "Friendly, rounded" },
  jakarta: { label: "Plus Jakarta Sans", stack: '"Plus Jakarta Sans", system-ui, sans-serif', note: "Modern, geometric" },
};

function applyTokens(tokens: Record<string, string>) {
  const root = document.documentElement;
  Object.entries(tokens).forEach(([k, v]) => root.style.setProperty(`--${k}`, v));
  if (!tokens.radius) root.style.setProperty("--radius", "0.625rem");
}

type Controls = {
  presets: ThemePreset[];
  presetName: string; setPreset: (n: string) => void;
  font: string; setFont: (f: string) => void;
};
const ThemeControls = createContext<Controls | null>(null);
export const useThemeControls = () => useContext(ThemeControls);

const LS_PRESET = "swingai_preset";
const LS_FONT = "swingai_font";

function TokenApplier({ presets, defaultPreset, defaultFont, children }: {
  presets: ThemePreset[]; defaultPreset: string; defaultFont: string; children: React.ReactNode;
}) {
  const { resolvedTheme } = useTheme();
  const [presetName, setPresetName] = useState(defaultPreset);
  const [font, setFontState] = useState(defaultFont);

  // user override (persisted) wins over platform default
  useEffect(() => {
    const p = localStorage.getItem(LS_PRESET); if (p) setPresetName(p);
    const f = localStorage.getItem(LS_FONT); if (f) setFontState(f);
  }, []);

  const preset = presets.find((p) => p.name === presetName) || presets[0] || null;

  useEffect(() => {
    const isDark = resolvedTheme === "dark";
    const light = { ...FALLBACK_LIGHT, ...(preset?.tokensLight || {}) };
    const dark = { ...FALLBACK_DARK, ...(preset?.tokensDark || {}) };
    applyTokens(isDark ? dark : light);
  }, [preset, resolvedTheme]);

  useEffect(() => {
    document.documentElement.style.setProperty("--font-sans", (FONTS[font] || FONTS.inter).stack);
  }, [font]);

  const setPreset = useCallback((n: string) => { setPresetName(n); localStorage.setItem(LS_PRESET, n); }, []);
  const setFont = useCallback((f: string) => { setFontState(f); localStorage.setItem(LS_FONT, f); }, []);

  return (
    <ThemeControls.Provider value={{ presets, presetName, setPreset, font, setFont }}>
      {children}
    </ThemeControls.Provider>
  );
}

export function ThemeProvider({ children, preset, presets, defaults }: {
  children: React.ReactNode;
  preset?: ThemePreset | null;                 // back-compat: single platform-default preset
  presets?: ThemePreset[];                     // all curated presets (for the picker)
  defaults?: { preset?: string; font?: string };
}) {
  const allPresets = presets && presets.length ? presets : (preset ? [preset] : []);
  const defaultPreset = defaults?.preset || preset?.name || "default";
  const defaultFont = defaults?.font || "inter";
  return (
    <NextThemes attribute="class" defaultTheme="system" enableSystem>
      <TokenApplier presets={allPresets} defaultPreset={defaultPreset} defaultFont={defaultFont}>
        {children}
      </TokenApplier>
    </NextThemes>
  );
}
