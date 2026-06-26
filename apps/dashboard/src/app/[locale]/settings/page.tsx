"use client";
// Settings & Appearance (blueprint/14,16) — user controls theme mode, font, accent preset.
// Live: changes apply instantly via the theme system and persist (localStorage override).
import { useCallback, useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Sun, Moon, Monitor, Palette, Check, Type, Gift, Copy } from "lucide-react";
import { useThemeControls, FONTS, Card } from "@swingai/ui";
import { api } from "@swingai/api-client";
import { useAuth } from "../../../lib/auth";
import { DashboardShell } from "../../../components/DashboardShell";

const MODES = [
  { key: "light", label: "Light", Icon: Sun },
  { key: "dark", label: "Dark", Icon: Moon },
  { key: "system", label: "System", Icon: Monitor },
];

function SettingsInner() {
  const { theme, setTheme } = useTheme();
  const tc = useThemeControls();
  const token = useAuth((s) => s.token);
  const [mounted, setMounted] = useState(false);
  const [ref, setRef] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  useEffect(() => setMounted(true), []);

  const loadRef = useCallback(() => { if (token) api.referral(token).then(setRef).catch(() => {}); }, [token]);
  useEffect(() => { loadRef(); }, [loadRef]);

  if (!mounted) return null;

  const swatch = (p: any) => (p.tokensLight?.primary || p.tokensDark?.primary || "#2563eb");
  const refLink = ref?.code && typeof window !== "undefined" ? `${window.location.origin}${window.location.pathname.replace(/\/settings$/, "/signup")}?ref=${ref.code}` : "";
  const copy = () => { if (refLink) { navigator.clipboard?.writeText(refLink); setCopied(true); setTimeout(() => setCopied(false), 1500); } };

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

      {/* referrals */}
      <Card className="p-6">
        <div className="mb-1 flex items-center gap-2 font-semibold"><Gift size={18} className="text-primary" /> Refer &amp; share</div>
        <p className="mb-4 text-sm text-muted-foreground">Share your link — friends who sign up are credited to you. {ref?.count ? <span className="font-medium text-foreground">{ref.count} joined so far.</span> : null}</p>
        <div className="flex flex-wrap items-center gap-3">
          <code className="rounded-lg bg-muted px-3 py-2 text-sm font-semibold tracking-wider">{ref?.code || "…"}</code>
          <button onClick={copy} disabled={!refLink}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted">
            <Copy size={14} /> {copied ? "Copied!" : "Copy invite link"}
          </button>
        </div>
        {ref?.referred?.length > 0 && (
          <div className="mt-4 space-y-1 text-xs text-muted-foreground">
            <div className="font-semibold uppercase tracking-wide">Referred</div>
            {ref.referred.slice(0, 5).map((r: any, i: number) => (
              <div key={i} className="flex justify-between"><span>{r.email}</span><span>{r.at}</span></div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

export default function SettingsPage() {
  return <DashboardShell><SettingsInner /></DashboardShell>;
}
