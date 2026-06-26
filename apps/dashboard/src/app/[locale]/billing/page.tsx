"use client";
// Billing / Upgrade (blueprint/20) — plans + Razorpay Checkout. create-order on the
// server, open Checkout, verify the signed result, activate the tier.
import { useCallback, useEffect, useState } from "react";
import { Check, Crown, Sparkles } from "lucide-react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { DashboardShell } from "../../../components/DashboardShell";

function loadCheckout(): Promise<boolean> {
  return new Promise((resolve) => {
    if ((window as any).Razorpay) return resolve(true);
    const s = document.createElement("script");
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.body.appendChild(s);
  });
}

function BillingInner() {
  const token = useAuth((s) => s.token);
  const [data, setData] = useState<any>(null);
  const [sub, setSub] = useState<any>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(() => {
    api.billingPlans().then(setData).catch(() => {});
    if (token) api.subscription(token).then(setSub).catch(() => {});
  }, [token]);
  useEffect(() => { load(); }, [load]);

  async function subscribe(plan: string, price: number) {
    if (!token) return;
    setBusy(plan); setMsg(null);
    try {
      const ok = await loadCheckout();
      if (!ok) throw new Error("Could not load Razorpay");
      const order = await api.createOrder(token, plan);
      const rzp = new (window as any).Razorpay({
        key: order.key_id, amount: order.amount, currency: order.currency,
        name: order.name, description: `SwingAI ${plan} — ₹${price}/mo`, order_id: order.order_id,
        prefill: { email: order.prefill_email },
        theme: { color: "#2563eb" },
        handler: async (resp: any) => {
          try {
            await api.verifyPayment(token, {
              plan, razorpay_order_id: resp.razorpay_order_id,
              razorpay_payment_id: resp.razorpay_payment_id, razorpay_signature: resp.razorpay_signature,
            });
            setMsg({ ok: true, text: `You're on ${plan.toUpperCase()} 🎉` });
            load();
          } catch {
            setMsg({ ok: false, text: "Payment captured but verification failed — contact support." });
          }
        },
        modal: { ondismiss: () => setBusy(null) },
      });
      rzp.on("payment.failed", () => setMsg({ ok: false, text: "Payment failed or cancelled." }));
      rzp.open();
    } catch (e: any) {
      setMsg({ ok: false, text: String(e?.message || e).slice(0, 100) });
    } finally { setBusy(null); }
  }

  async function startTrial() {
    if (!token) return;
    setBusy("trial"); setMsg(null);
    try {
      const r = await api.startTrial(token);
      setMsg({ ok: true, text: `Free trial started — full access for ${r.days} days 🎉` });
      load();
    } catch (e: any) {
      setMsg({ ok: false, text: String(e?.message || e).replace(/API \d+:/, "").slice(0, 100) });
    } finally { setBusy(null); }
  }

  const tier = sub?.tier || "free";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Plans &amp; Billing</h1>
        <p className="text-sm text-muted-foreground">
          You're on <span className="font-semibold text-foreground capitalize">{tier}</span>.
          {sub?.current_period_end ? ` Renews ${String(sub.current_period_end).slice(0, 10)}.` : ""}
        </p>
      </div>

      {data && !data.enabled && (
        <Card className="p-4 text-sm text-warning">Payments are not configured yet — add Razorpay keys in the Integrations tab or .env.</Card>
      )}
      {msg && <Card className={`p-4 text-sm ${msg.ok ? "text-success" : "text-destructive"}`}>{msg.text}</Card>}

      <div className="grid gap-5 md:grid-cols-3">
        {data?.plans?.map((p: any) => {
          const active = tier === p.id;
          const isTrial = p.trial_days > 0;
          return (
            <Card key={p.id} className={`relative flex flex-col overflow-hidden p-6 ${p.featured ? "border-primary ring-1 ring-primary/20" : ""}`}>
              {p.featured && <div className="absolute right-0 top-0 bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground">Best value</div>}
              <div className="flex items-center gap-2 text-lg font-bold">
                {isTrial ? <Sparkles size={18} className="text-success" /> : <Crown size={18} className="text-primary" />} {p.name}
              </div>
              <div className="mt-2 text-3xl font-bold">
                ₹{p.price_inr}<span className="text-sm font-normal text-muted-foreground">{isTrial ? ` · ${p.trial_days} days` : "/mo"}</span>
              </div>
              <ul className="mt-4 flex-1 space-y-2 text-sm text-muted-foreground">
                {p.features.map((f: string, i: number) => <li key={i} className="flex gap-2"><Check size={16} className="text-success" /> {f}</li>)}
              </ul>
              {isTrial ? (
                <Button className="mt-6 w-full" variant="outline"
                  disabled={active || busy === "trial" || sub?.trial_used}
                  onClick={startTrial}>
                  {active ? "Trial active" : sub?.trial_used ? "Trial used" : busy === "trial" ? "Starting…" : "Start free trial"}
                </Button>
              ) : (
                <Button className="mt-6 w-full" disabled={active || busy === p.id || !data?.enabled}
                  onClick={() => subscribe(p.id, p.price_inr)}>
                  {active ? "Current plan" : busy === p.id ? "Opening checkout…" : `Upgrade to ${p.name}`}
                </Button>
              )}
            </Card>
          );
        })}
      </div>
      <p className="text-xs text-muted-foreground">Secure payments via Razorpay (UPI, cards, netbanking). Test mode uses Razorpay test cards — no real charge.</p>
    </div>
  );
}

export default function BillingPage() {
  return <DashboardShell><BillingInner /></DashboardShell>;
}
