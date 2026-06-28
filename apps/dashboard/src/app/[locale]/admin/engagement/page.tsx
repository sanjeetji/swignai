"use client";
// Admin → Engagement & retention (blueprint/20). Answers "are users coming back?" — DAU/WAU/MAU,
// trial→paid funnel, weekly cohort retention, dormant churn. Theme/font-aware (design tokens).
import { useEffect, useState } from "react";
import { Activity, Users, CreditCard, Sparkles } from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell,
} from "recharts";
import { api } from "@swingai/api-client";
import { Card } from "@swingai/ui";
import { useAuth } from "../../../../lib/auth";
import { StatCard } from "../../../../components/dashboard-ui";

export default function AdminEngagement() {
  const token = useAuth((s) => s.token);
  const [d, setD] = useState<any>(null);
  const [denied, setDenied] = useState(false);

  useEffect(() => { if (token) api.adminEngagement(token).then((r) => r ? setD(r) : setDenied(true)).catch(() => setDenied(true)); }, [token]);
  if (denied) return <Card className="p-6">403 — admin access required.</Card>;

  const tip = { background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, color: "var(--foreground)" };
  const f = d?.funnel;
  const funnelData = f ? [
    { step: "Signups", count: f.signups }, { step: "Trials", count: f.trials }, { step: "Paid", count: f.paid },
  ] : [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Engagement &amp; retention</h1>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="DAU (1d active)" value={String(d?.dau ?? "…")} Icon={Activity} tone="up" />
        <StatCard label="WAU (7d active)" value={String(d?.wau ?? "…")} Icon={Activity} delay={0.05} />
        <StatCard label="MAU (30d active)" value={String(d?.mau ?? "…")} Icon={Users} delay={0.1} />
        <StatCard label="Dormant (30d)" value={`${d?.dormant_30d_pct ?? 0}%`} Icon={Activity} tone={d?.dormant_30d_pct > 50 ? "down" : undefined} delay={0.15} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Funnel */}
        <Card className="p-5">
          <h2 className="mb-1 font-semibold">Acquisition funnel</h2>
          <p className="mb-3 text-xs text-muted-foreground">
            {f ? `${f.trial_pct}% started a trial · ${f.paid_pct}% are paid · ${f.trial_to_paid_pct}% trial→paid` : ""}
          </p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={funnelData} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
              <XAxis type="number" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="step" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} width={64} />
              <Tooltip contentStyle={tip} cursor={{ fill: "var(--muted)" }} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {funnelData.map((_, i) => <Cell key={i} fill={["var(--muted-foreground)", "var(--warning)", "var(--success)"][i]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><Users size={13} /> {f?.signups ?? 0} signups</span>
            <span className="flex items-center gap-1"><Sparkles size={13} className="text-warning" /> {f?.trials ?? 0} trials</span>
            <span className="flex items-center gap-1"><CreditCard size={13} className="text-success" /> {f?.paid ?? 0} paid</span>
          </div>
        </Card>

        {/* Cohort retention */}
        <Card className="p-5">
          <h2 className="mb-1 font-semibold">Weekly cohort retention</h2>
          <p className="mb-3 text-xs text-muted-foreground">% of each week's signups still active in the last 14 days.</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={d?.cohorts || []} margin={{ left: -8, right: 8, top: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="week" stroke="var(--muted-foreground)" fontSize={10} tickLine={false} tickFormatter={(w) => String(w).slice(5)} />
              <YAxis stroke="var(--muted-foreground)" fontSize={11} tickLine={false} width={36} unit="%" domain={[0, 100]} />
              <Tooltip contentStyle={tip} cursor={{ fill: "var(--muted)" }} />
              <Bar dataKey="retention_pct" fill="var(--primary)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-2 grid grid-cols-3 gap-1 text-[11px] text-muted-foreground">
            {(d?.cohorts || []).slice(-3).map((c: any) => (
              <div key={c.week}>{String(c.week).slice(5)}: {c.retained}/{c.signups}</div>
            ))}
          </div>
        </Card>
      </div>

      <p className="text-xs text-muted-foreground">Activity = a session touched (login or token refresh). The Phase-2 goal is users returning 4+ days/week — watch DAU/WAU climb relative to signups.</p>
    </div>
  );
}
