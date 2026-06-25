"use client";
// Appearance editor — platform defaults for theme/font/locale (blueprint/14,16).
// Admin sets the default; users override their own unless an axis is locked.
import { useEffect, useState } from "react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../../lib/auth";

const MODES = ["light", "dark", "system"];
const PRESETS = ["default", "emerald", "violet", "amber"];
const FONTS = ["inter", "manrope", "jakarta"];
const LOCALES = ["en", "hi"];

export default function AdminAppearance() {
  const token = useAuth((s) => s.token);
  const [s, setS] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [denied, setDenied] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.getAppearance(token).then(setS).catch(() => setDenied(true));
  }, [token]);

  if (denied) return <Card className="p-6">403 — admin access required.</Card>;
  if (!s) return <Card className="p-6 text-muted-foreground">Loading…</Card>;

  const Select = ({ field, options }: { field: string; options: string[] }) => (
    <label className="text-sm">
      <span className="text-muted-foreground capitalize">{field.replace("default_", "").replace("_", " ")}</span>
      <select value={s[field] ?? ""} onChange={(e) => setS({ ...s, [field]: e.target.value })}
        className="mt-1 w-full rounded-md border border-border bg-background px-2 py-1">
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Appearance defaults</h1>
      <Card className="grid grid-cols-2 gap-4 p-5 sm:grid-cols-4">
        <Select field="default_theme_mode" options={MODES} />
        <Select field="default_preset" options={PRESETS} />
        <Select field="default_font" options={FONTS} />
        <Select field="default_locale" options={LOCALES} />
      </Card>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={!!s.maintenance_mode}
          onChange={(e) => setS({ ...s, maintenance_mode: e.target.checked })} />
        Maintenance mode
      </label>
      <div className="flex items-center gap-3">
        <Button onClick={async () => {
          if (!token) return;
          setMsg("Saving…");
          try {
            await api.setAppearance(token, {
              default_theme_mode: s.default_theme_mode, default_preset: s.default_preset,
              default_font: s.default_font, default_locale: s.default_locale,
              maintenance_mode: s.maintenance_mode,
            });
            setMsg("Saved — applies platform-wide.");
          } catch (e: any) { setMsg(String(e?.message || e).slice(0, 120)); }
        }}>Save defaults</Button>
        {msg && <span className="text-sm text-muted-foreground">{msg}</span>}
      </div>
    </div>
  );
}
