"use client";
// Admin overview — platform KPIs + pipeline rerun (blueprint/16,20).
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";

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

  const kpi = (label: string, value: string) => (
    <Card className="p-5"><div className="text-sm text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div></Card>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Overview</h1>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {kpi("Users", String(metrics?.users ?? "…"))}
        {kpi("Paper trades", String(metrics?.paper_trades ?? "…"))}
        {kpi("MRR", `₹${metrics?.mrr ?? 0}`)}
        {kpi("ARR", `₹${metrics?.arr ?? 0}`)}
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
