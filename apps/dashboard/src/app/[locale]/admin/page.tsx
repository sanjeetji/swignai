"use client";
// Admin overview — business analytics (blueprint/16,20). Theme/font-aware: all colors are CSS
// design tokens (var(--primary) etc.) so the charts follow the active theme + font automatically.
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Users, Activity, IndianRupee, TrendingUp, CreditCard, Sparkles, Wallet, Percent } from "lucide-react";
import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell,
} from "recharts";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { StatCard } from "../../../components/dashboard-ui";

const PLAN_COLORS: Record<string, string> = {
  premium: "var(--primary)", pro: "var(--success)", trial: "var(--warning)", free: "var(--muted-foreground)",
};

export default function AdminOverview() {
  const token = useAuth((s) => s.token);
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const [metrics, setMetrics] = useState<any>(null);
  const [series, setSeries] = useState<any>(null);
  const [denied, setDenied] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (token === null) return;
    if (!token) { router.push(`/${locale}/login`); return; }
    api.adminMetrics(token).then(setMetrics).catch(() => setDenied(true));
    api.adminMetricsSeries(token, 30).then(setSeries).catch(() => {});
  }, [token, locale, router]);

  if (denied) return <Card className="p-6">403 — you don't have admin access.</Card>;

  const tip = { background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, color: "var(--foreground)" };
  const revTotal = (series?.series || []).reduce((s: number, d: any) => s + (d.revenue || 0), 0);
  const suTotal = (series?.series || []).reduce((s: number, d: any) => s + (d.signups || 0), 0);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Overview</h1>

      <div>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Audience</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Users" value={String(metrics?.users ?? "…")} Icon={Users} delay={0} />
          <StatCard label="Paper trades" value={String(metrics?.paper_trades ?? "…")} Icon={Activity} delay={0.05} />
          <StatCard label="Paying customers" value={String(metrics?.paying_customers ?? "…")} Icon={CreditCard} delay={0.1} />
          <StatCard label="On trial" value={String(metrics?.trial_users ?? "…")} Icon={Sparkles} delay={0.15} />
        </div>
      </div>

      <div>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Revenue</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="MRR" value={`₹${Number(metrics?.mrr ?? 0).toLocaleString("en-IN")}`} Icon={IndianRupee} tone="up" delay={0} />
          <StatCard label="ARR" value={`₹${Number(metrics?.arr ?? 0).toLocaleString("en-IN")}`} Icon={TrendingUp} tone="up" delay={0.05} />
          <StatCard label="Total revenue" value={`₹${Number(metrics?.total_revenue ?? 0).toLocaleString("en-IN")}`} Icon={Wallet} delay={0.1} />
          <StatCard label="Conversion" value={`${metrics?.conversion_pct ?? 0}%`} Icon={Percent} delay={0.15} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Revenue trend */}
        <Card className="p-5 lg:col-span-2">
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="font-semibold">Revenue · last 30 days</h2>
            <span className="text-sm text-muted-foreground">₹{Number(revTotal).toLocaleString("en-IN")} captured</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={series?.series || []} margin={{ left: -8, right: 8, top: 8 }}>
              <defs>
                <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--success)" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="var(--success)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="date" stroke="var(--muted-foreground)" fontSize={10} tickLine={false} interval={4} />
              <YAxis stroke="var(--muted-foreground)" fontSize={11} tickLine={false} width={48} />
              <Tooltip contentStyle={tip} cursor={{ stroke: "var(--border)" }} />
              <Area type="monotone" dataKey="revenue" stroke="var(--success)" strokeWidth={2} fill="url(#rev)" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        {/* Plan mix */}
        <Card className="p-5">
          <h2 className="mb-3 font-semibold">Plan mix</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={series?.plan_mix || []} layout="vertical" margin={{ left: 8, right: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
              <XAxis type="number" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="plan" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} width={64} />
              <Tooltip contentStyle={tip} cursor={{ fill: "var(--muted)" }} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {(series?.plan_mix || []).map((d: any, i: number) => (
                  <Cell key={i} fill={PLAN_COLORS[d.plan] || "var(--primary)"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Signups */}
      <Card className="p-5">
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="font-semibold">New signups · last 30 days</h2>
          <span className="text-sm text-muted-foreground">{suTotal} total</span>
        </div>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={series?.series || []} margin={{ left: -8, right: 8, top: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="date" stroke="var(--muted-foreground)" fontSize={10} tickLine={false} interval={4} />
            <YAxis stroke="var(--muted-foreground)" fontSize={11} tickLine={false} width={28} allowDecimals={false} />
            <Tooltip contentStyle={tip} cursor={{ fill: "var(--muted)" }} />
            <Bar dataKey="signups" fill="var(--primary)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card className="p-5">
        <h2 className="font-semibold">Daily pipeline</h2>
        <p className="text-sm text-muted-foreground">{metrics?.note}</p>
        <Button className="mt-3" onClick={async () => {
          if (!token) return;
          setMsg("Running…");
          try { const r = await api.rerunPipeline(token); setMsg(`Done: ${r.picks} picks (${r.regime}) for ${r.date}`); }
          catch (e: any) { setMsg(String(e?.message || e).slice(0, 120)); }
        }}>Re-run pipeline</Button>
        {msg && <p className="mt-2 text-sm">{msg}</p>}
      </Card>
    </div>
  );
}
