"use client";
// Personal analytics (blueprint/20) — equity curve + R-multiple distribution + headline
// stats, all from real closed paper trades (Recharts, theme-token colored).
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Target, Percent, Gauge, Activity, Crown } from "lucide-react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar, Cell,
} from "recharts";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { DashboardShell } from "../../../components/DashboardShell";
import { StatCard, Skeleton } from "../../../components/dashboard-ui";

function AnalyticsInner() {
  const token = useAuth((s) => s.token);
  const { locale } = useParams<{ locale: string }>();
  const [summary, setSummary] = useState<any>(null);
  const [eq, setEq] = useState<any>(null);

  const load = useCallback(() => {
    if (!token) return;
    api.analytics(token).then(setSummary).catch(() => {});
    api.equityCurve(token).then(setEq).catch(() => {});
  }, [token]);
  useEffect(() => { load(); }, [load]);

  const hasTrades = summary?.trades > 0;
  const tip = { background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, color: "var(--foreground)" };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>

      {!summary ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}</div>
      ) : hasTrades ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Expectancy" value={`${summary.expectancy_r}R`} Icon={Target}
            tone={summary.expectancy_r > 0 ? "up" : summary.expectancy_r < 0 ? "down" : "default"} />
          <StatCard label="Win rate" value={`${summary.win_rate_pct}%`} Icon={Percent} />
          <StatCard label="Profit factor" value={String(summary.profit_factor ?? "—")} Icon={Gauge} />
          <StatCard label="Net P&L" value={`₹${Number(summary.total_pnl_inr).toLocaleString("en-IN")}`} Icon={Activity}
            tone={summary.total_pnl_inr > 0 ? "up" : summary.total_pnl_inr < 0 ? "down" : "default"} />
        </div>
      ) : (
        <Card className="p-6 text-sm text-muted-foreground">No closed trades yet — close some paper trades to see your equity curve and R-distribution.</Card>
      )}

      {eq?.locked ? (
        <Card className="flex flex-col items-center gap-3 p-8 text-center">
          <Crown size={28} className="text-primary" />
          <div className="font-semibold">Equity curve is a Pro feature</div>
          <p className="max-w-md text-sm text-muted-foreground">Track your cumulative P&L and R-multiple distribution over time. Start a free trial or upgrade to unlock.</p>
          <Link href={`/${locale}/billing`}><Button>See plans</Button></Link>
        </Card>
      ) : (
      <>
      {/* equity curve */}
      <Card className="p-5">
        <h2 className="mb-1 text-sm font-semibold">Equity curve</h2>
        <p className="mb-4 text-xs text-muted-foreground">Cumulative net P&L (₹) over your closed trades.</p>
        {!eq ? <Skeleton className="h-64" /> : eq.curve.length === 0 ? (
          <div className="grid h-48 place-items-center text-sm text-muted-foreground">No closed trades yet.</div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={eq.curve} margin={{ left: -8, right: 8, top: 8 }}>
              <defs>
                <linearGradient id="eq" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="var(--primary)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="i" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} />
              <YAxis stroke="var(--muted-foreground)" fontSize={11} tickLine={false} width={48} />
              <Tooltip contentStyle={tip} formatter={(v: any) => [`₹${v}`, "Cum P&L"]}
                labelFormatter={(i: any) => `Trade ${i}`} />
              <Area type="monotone" dataKey="pnl" stroke="var(--primary)" strokeWidth={2} fill="url(#eq)" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </Card>

      {/* R distribution */}
      <Card className="p-5">
        <h2 className="mb-1 text-sm font-semibold">R-multiple distribution</h2>
        <p className="mb-4 text-xs text-muted-foreground">How your trades landed in R — winners pay for losers when expectancy is positive.</p>
        {!eq ? <Skeleton className="h-48" /> : eq.distribution.every((d: any) => d.count === 0) ? (
          <div className="grid h-40 place-items-center text-sm text-muted-foreground">No closed trades yet.</div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={eq.distribution} margin={{ left: -8, right: 8, top: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="bucket" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} />
              <YAxis stroke="var(--muted-foreground)" fontSize={11} tickLine={false} width={28} allowDecimals={false} />
              <Tooltip contentStyle={tip} cursor={{ fill: "var(--muted)" }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {eq.distribution.map((d: any, i: number) => (
                  <Cell key={i} fill={d.bucket.includes("-") || d.bucket.startsWith("≤") ? "var(--destructive)" : "var(--success)"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>
      </>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  return <DashboardShell><AnalyticsInner /></DashboardShell>;
}
