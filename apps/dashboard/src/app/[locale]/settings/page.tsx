"use client";
// Settings & Appearance (blueprint/14,16) — user controls theme mode, font, accent preset.
// Live: changes apply instantly via the theme system and persist (localStorage override).
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Sun, Moon, Monitor, Palette, Check, Type } from "lucide-react";
import { useThemeControls, FONTS, Card } from "@swingai/ui";
import { DashboardShell } from "../../../components/DashboardShell";

const MODES = [
  { key: "light", label: "Light", Icon: Sun },
  { key: "dark", label: "Dark", Icon: Moon },
  { key: "system", label: "System", Icon: Monitor },
];

function SettingsInner() {
  const { theme, setTheme } = useTheme();
  const tc = useThemeControls();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  const swatch = (p: any) => (p.tokensLight?.primary || p.tokensDark?.primary || "#2563eb");

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings &amp; Appearance</h1>
        <p className="text-sm text-muted-foreground">Manage your workspace theme, accent color, and typography.</p>
      </div>

      <Card className="p-6">
        <div className="mb-5 flex items-center gap-2 font-semibold"><Palette size={18} className="text-primary" /> Appearance</div>

        {/* theme mode */}
        <div className="mb-6">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Theme mode</div>
          <div className="grid grid-cols-3 gap-3">
            {MODES.map(({ key, label, Icon }) => {
              const active = theme === key;
              return (
                <button key={key} onClick={() => setTheme(key)}
                  className={`relative flex flex-col items-center gap-2 rounded-xl border p-5 transition-all ${
                    active ? "border-primary bg-primary/5 ring-2 ring-primary/20" : "border-border hover:bg-muted"
                  }`}>
                  {active && <span className="absolute right-2 top-2 grid h-4 w-4 place-items-center rounded-full bg-primary text-primary-foreground"><Check size={11} /></span>}
                  <Icon size={22} className={active ? "text-primary" : "text-muted-foreground"} />
                  <span className="text-sm font-medium">{label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* typography */}
        {tc && (
          <div className="mb-6">
            <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground"><Type size={13} /> Typography</div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {Object.entries(FONTS).map(([key, f]) => {
                const active = tc.font === key;
                return (
                  <button key={key} onClick={() => tc.setFont(key)}
                    className={`flex items-center justify-between rounded-xl border p-4 text-left transition-all ${
                      active ? "border-primary bg-primary/5 ring-2 ring-primary/20" : "border-border hover:bg-muted"
                    }`}>
                    <div>
                      <div className="font-semibold" style={{ fontFamily: f.stack }}>{f.label}</div>
                      <div className="text-xs text-muted-foreground">{f.note}</div>
                    </div>
                    {active && <Check size={16} className="text-primary" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* accent / preset */}
        {tc && tc.presets.length > 0 && (
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Accent color</div>
            <div className="flex flex-wrap gap-3">
              {tc.presets.map((p) => {
                const active = tc.presetName === p.name;
                return (
                  <button key={p.name} onClick={() => tc.setPreset(p.name)} title={p.label}
                    className={`grid h-10 w-10 place-items-center rounded-full ring-2 ring-offset-2 ring-offset-background transition ${active ? "ring-foreground" : "ring-transparent hover:ring-border"}`}
                    style={{ background: swatch(p) }}>
                    {active && <Check size={16} className="text-white" />}
                  </button>
                );
              })}
            </div>
            <p className="mt-2 text-xs text-muted-foreground">Your choices are saved to this device. Admins set the platform default.</p>
          </div>
        )}
      </Card>
    </div>
  );
}

export default function SettingsPage() {
  return <DashboardShell><SettingsInner /></DashboardShell>;
}
