"use client";
// Admin overview — platform KPIs + pipeline rerun (blueprint/16,20).
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Users, Activity, IndianRupee, TrendingUp, CreditCard, Sparkles, Wallet, Percent } from "lucide-react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { StatCard } from "../../../components/dashboard-ui";

export default function AdminOverview() {
  const token = useAuth((s) => s.token);
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const [metrics, setMetrics] = useState<any>(null);
  const [denied, setDenied] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (token === null) return;
    if (!token) { router.push(`/${locale}/login`); return; }
    api.adminMetrics(token).then(setMetrics).catch(() => setDenied(true));
  }, [token, locale, router]);

  if (denied) return <Card className="p-6">403 — you don't have admin access.</Card>;

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
