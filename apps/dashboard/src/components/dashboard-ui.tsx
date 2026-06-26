"use client";
// Reusable dashboard widgets (blueprint/14 §3): regime banner, KPI stat card, score
// breakdown bar, portfolio heat meter, skeleton. Token-driven (theme-aware), motion via
// Framer Motion, and strictly real-data — empty/loading states are first-class.
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, type LucideIcon } from "lucide-react";

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-muted/60 ${className}`} />;
}

const REGIME: Record<string, { label: string; cls: string; Icon: LucideIcon }> = {
  bull: { label: "Bullish — trend is up", cls: "from-success/20 to-success/5 border-success/30 text-success", Icon: TrendingUp },
  bear: { label: "Bearish — sitting in cash", cls: "from-destructive/20 to-destructive/5 border-destructive/30 text-destructive", Icon: TrendingDown },
  neutral: { label: "Neutral — selective", cls: "from-warning/20 to-warning/5 border-warning/30 text-warning", Icon: Minus },
};

export function RegimeBanner({ regime, cashMode, note }: { regime?: string; cashMode?: boolean; note?: string }) {
  const key = cashMode ? "bear" : (regime || "neutral");
  const r = REGIME[key] || REGIME.neutral;
  return (
    <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
      className={`flex items-center gap-3 rounded-xl border bg-gradient-to-r p-4 ${r.cls}`}>
      <r.Icon size={22} />
      <div>
        <div className="text-sm font-semibold">{note || r.label}</div>
        <div className="text-xs opacity-70">NIFTY regime gate · educational, not advice</div>
      </div>
    </motion.div>
  );
}

export function StatCard({ label, value, sub, Icon, tone = "default", delay = 0 }: {
  label: string; value: string; sub?: string; Icon?: LucideIcon;
  tone?: "default" | "up" | "down"; delay?: number;
}) {
  const toneCls = tone === "up" ? "text-success" : tone === "down" ? "text-destructive" : "text-foreground";
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
      className="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
        {Icon && <Icon size={16} className="text-muted-foreground" />}
      </div>
      <div className={`mt-2 text-2xl font-bold tabular-nums ${toneCls}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-muted-foreground">{sub}</div>}
    </motion.div>
  );
}

// Score breakdown bars from the pick's real score_breakdown JSON (RS / Trend / Volume…).
export function ScoreBar({ breakdown }: { breakdown?: Record<string, number> }) {
  const entries = Object.entries(breakdown || {}).filter(([, v]) => typeof v === "number");
  if (!entries.length) return null;
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <div className="mt-3 space-y-1.5">
      {entries.map(([k, v]) => (
        <div key={k} className="flex items-center gap-2">
          <span className="w-24 shrink-0 truncate text-[11px] capitalize text-muted-foreground">{k.replace(/_/g, " ")}</span>
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
            <motion.div initial={{ width: 0 }} animate={{ width: `${(v / max) * 100}%` }}
              transition={{ duration: 0.5 }} className="h-full rounded-full bg-primary" />
          </div>
          <span className="w-7 text-right text-[11px] tabular-nums text-muted-foreground">{Math.round(v)}</span>
        </div>
      ))}
    </div>
  );
}

export function HeatMeter({ pct }: { pct: number }) {
  const clamped = Math.max(0, Math.min(100, pct));
  const tone = clamped > 80 ? "bg-destructive" : clamped > 50 ? "bg-warning" : "bg-success";
  return (
    <div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Portfolio heat</span><span className="tabular-nums">{clamped.toFixed(1)}%</span>
      </div>
      <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
        <motion.div initial={{ width: 0 }} animate={{ width: `${clamped}%` }} transition={{ duration: 0.6 }}
          className={`h-full rounded-full ${tone}`} />
      </div>
    </div>
  );
}
