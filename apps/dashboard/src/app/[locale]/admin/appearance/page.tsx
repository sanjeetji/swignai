"use client";
// Appearance editor (blueprint/14,16) — platform DEFAULT theme/accent/font + per-axis
// LOCKS (force a setting platform-wide) + maintenance mode. Card-based, like the user
// Settings page. Admin sets defaults; users override unless an axis is locked.
import { useEffect, useState } from "react";
import { Sun, Moon, Monitor, Check, Lock, Palette, Type } from "lucide-react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../../lib/auth";

const MODES = [{ k: "light", L: "Light", Icon: Sun }, { k: "dark", L: "Dark", Icon: Moon }, { k: "system", L: "System", Icon: Monitor }];
const FONTS = [{ k: "inter", L: "Inter", note: "Data-dense, legible" }, { k: "manrope", L: "Manrope", note: "Friendly, rounded" }, { k: "jakarta", L: "Plus Jakarta Sans", note: "Modern, geometric" }];

export default function AdminAppearance() {
  const token = useAuth((s) => s.token);
  const [s, setS] = useState<any>(null);
  const [presets, setPresets] = useState<any[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [denied, setDenied] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.getAppearance(token).then((d) => setS({ ...d, locked_axes: d.locked_axes || {} })).catch(() => setDenied(true));
    api.appearance().then((a) => setPresets(a.presets)).catch(() => {});
  }, [token]);

  if (denied) return <Card className="p-6">403 — admin access required.</Card>;
  if (!s) return <Card className="p-6 text-muted-foreground">Loading…</Card>;

  const set = (patch: any) => setS({ ...s, ...patch });
  const lock = (axis: string) => set({ locked_axes: { ...s.locked_axes, [axis]: !s.locked_axes?.[axis] } });
  const swatch = (p: any) => p.tokensLight?.primary || p.tokensDark?.primary || "#2563eb";

  async function save() {
    if (!token) return;
    setMsg("Saving…");
    try {
      await api.setAppearance(token, {
        default_theme_mode: s.default_theme_mode, default_preset: s.default_preset,
        default_font: s.default_font, default_locale: s.default_locale,
        locked_axes: s.locked_axes, maintenance_mode: s.maintenance_mode,
      });
      setMsg("Saved — applies platform-wide.");
    } catch (e: any) { setMsg(String(e?.message || e).slice(0, 120)); }
  }

  const LockBtn = ({ axis }: { axis: string }) => (
    <button onClick={() => lock(axis)} title={s.locked_axes?.[axis] ? "Locked platform-wide" : "Unlocked (users can override)"}
      className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs ${s.locked_axes?.[axis] ? "bg-primary/15 text-primary" : "text-muted-foreground hover:bg-muted"}`}>
      <Lock size={12} /> {s.locked_axes?.[axis] ? "Locked" : "Lock"}
    </button>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Appearance &amp; Defaults</h1>

      <Card className="space-y-6 p-6">
        <div className="flex items-center gap-2 font-semibold"><Palette size={18} className="text-primary" /> Platform defaults</div>

        {/* theme mode */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Default theme mode</span>
            <LockBtn axis="mode" />
          </div>
          <div className="grid grid-cols-3 gap-3">
            {MODES.map(({ k, L, Icon }) => {
              const active = s.default_theme_mode === k;
              return (
                <button key={k} onClick={() => set({ default_theme_mode: k })}
                  className={`relative flex flex-col items-center gap-2 rounded-xl border p-4 transition-all ${active ? "border-primary bg-primary/5 ring-2 ring-primary/20" : "border-border hover:bg-muted"}`}>
                  {active && <Check size={13} className="absolute right-2 top-2 text-primary" />}
                  <Icon size={20} className={active ? "text-primary" : "text-muted-foreground"} /><span className="text-sm">{L}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* accent */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Default accent color</span>
            <LockBtn axis="preset" />
          </div>
          <div className="flex flex-wrap gap-3">
            {presets.map((p) => {
              const active = s.default_preset === p.name;
              return (
                <button key={p.name} onClick={() => set({ default_preset: p.name })} title={p.label}
                  className={`grid h-10 w-10 place-items-center rounded-full ring-2 ring-offset-2 ring-offset-background transition ${active ? "ring-foreground" : "ring-transparent hover:ring-border"}`}
                  style={{ background: swatch(p) }}>{active && <Check size={15} className="text-white" />}</button>
              );
            })}
          </div>
        </div>

        {/* font */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground"><Type size={13} /> Default font</span>
            <LockBtn axis="font" />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {FONTS.map(({ k, L, note }) => {
              const active = s.default_font === k;
              return (
                <button key={k} onClick={() => set({ default_font: k })}
                  className={`flex items-center justify-between rounded-xl border p-3 text-left transition-all ${active ? "border-primary bg-primary/5 ring-2 ring-primary/20" : "border-border hover:bg-muted"}`}>
                  <div><div className="text-sm font-semibold">{L}</div><div className="text-xs text-muted-foreground">{note}</div></div>
                  {active && <Check size={15} className="text-primary" />}
                </button>
              );
            })}
          </div>
        </div>
      </Card>

      <Card className="space-y-3 p-6">
        <div className="font-semibold">Maintenance</div>
        <label className="flex items-center justify-between text-sm">
          <span><span className="font-medium">Maintenance mode</span><br /><span className="text-xs text-muted-foreground">Shows a maintenance banner to all users.</span></span>
          <input type="checkbox" className="h-5 w-5" checked={!!s.maintenance_mode} onChange={(e) => set({ maintenance_mode: e.target.checked })} />
        </label>
      </Card>

      <div className="flex items-center gap-3">
        <Button onClick={save}>Save defaults</Button>
        {msg && <span className="text-sm text-muted-foreground">{msg}</span>}
      </div>
    </div>
  );
}
