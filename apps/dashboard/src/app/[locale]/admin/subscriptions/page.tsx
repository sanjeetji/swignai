"use client";
// Admin → Subscriptions & revenue ops (blueprint/20). Recent transactions + revenue KPIs.
// Theme/font-aware (design tokens). Per-user plan changes live in Admin → Users (detail drawer).
import { useEffect, useState } from "react";
import { IndianRupee, TrendingUp, Wallet, CreditCard } from "lucide-react";
import { api } from "@swingai/api-client";
import { Card } from "@swingai/ui";
import { useAuth } from "../../../../lib/auth";
import { StatCard } from "../../../../components/dashboard-ui";

const statusCls: Record<string, string> = {
  captured: "bg-success/15 text-success", created: "bg-warning/15 text-warning",
  failed: "bg-destructive/15 text-destructive", refunded: "bg-muted text-muted-foreground",
};

export default function AdminSubscriptions() {
  const token = useAuth((s) => s.token);
  const [pay, setPay] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [denied, setDenied] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.adminPayments(token, 100).then(setPay).catch(() => setDenied(true));
    api.adminMetrics(token).then(setMetrics).catch(() => setDenied(true));
  }, [token]);

  if (denied) return <Card className="p-6">403 — admin access required.</Card>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Subscriptions &amp; revenue</h1>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="MRR" value={`₹${Number(metrics?.mrr ?? 0).toLocaleString("en-IN")}`} Icon={IndianRupee} tone="up" />
        <StatCard label="ARR" value={`₹${Number(metrics?.arr ?? 0).toLocaleString("en-IN")}`} Icon={TrendingUp} tone="up" delay={0.05} />
        <StatCard label="Total revenue" value={`₹${Number(metrics?.total_revenue ?? 0).toLocaleString("en-IN")}`} Icon={Wallet} delay={0.1} />
        <StatCard label="Paying customers" value={String(metrics?.paying_customers ?? "…")} Icon={CreditCard} delay={0.15} />
      </div>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Recent transactions</h2>
        <Card className="overflow-hidden p-0">
          <div className="hidden grid-cols-[1.6fr_0.8fr_0.8fr_1.2fr_1fr] gap-3 border-b border-border px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground sm:grid">
            <div>Customer</div><div>Amount</div><div>Status</div><div>Payment ID</div><div className="text-right">When</div>
          </div>
          <div className="divide-y divide-border">
            {pay?.payments?.length ? pay.payments.map((p: any) => (
              <div key={p.id} className="grid grid-cols-2 items-center gap-3 px-4 py-3 text-sm sm:grid-cols-[1.6fr_0.8fr_0.8fr_1.2fr_1fr]">
                <div className="truncate">{p.email}</div>
                <div className="tabular-nums">₹{Number(p.amount_inr).toLocaleString("en-IN")}</div>
                <div><span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusCls[p.status] || "bg-muted"}`}>{p.status}</span></div>
                <div className="truncate text-xs text-muted-foreground">{p.razorpay_payment_id || "—"}</div>
                <div className="text-right text-xs text-muted-foreground">{p.at}</div>
              </div>
            )) : (
              <div className="px-4 py-10 text-center text-sm text-muted-foreground">
                No transactions yet. Captured Razorpay payments will appear here. To grant or change a
                user's plan manually, use <b className="text-foreground">Admin → Users</b> → expand a user → Plan.
              </div>
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}
