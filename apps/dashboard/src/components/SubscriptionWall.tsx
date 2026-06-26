"use client";
// Hard paywall shown when a user's trial/paid plan has lapsed (blueprint/20). Blocks the
// dashboard until they pick a plan again: continue on Free (basic), or upgrade to a paid plan.
// Marketing stays public; admins never see this (handled by the caller).
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Check, Lock, LogOut } from "lucide-react";
import { api } from "@swingai/api-client";
import { Button, ThemeToggle, LanguageSwitcher } from "@swingai/ui";
import { useAuth } from "../lib/auth";

export function SubscriptionWall({ reason, onResolved }: { reason?: string; onResolved: () => void }) {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const token = useAuth((s) => s.token);
  const logout = useAuth((s) => s.logout);
  const [plans, setPlans] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.billingPlans().then((r) => setPlans((r.plans || []).filter((p: any) => (p.price_inr ?? 0) > 0))).catch(() => {}); }, []);

  const headline = reason === "plan_lapsed" ? "Your subscription has ended"
    : reason === "trial_ended" ? "Your free trial has ended" : "Choose a plan to continue";

  async function chooseFree() {
    if (!token) return;
    setBusy(true);
    try { await api.activateFree(token); onResolved(); } finally { setBusy(false); }
  }

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-background px-6 py-12 text-foreground">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-primary/20 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-success/10 blur-3xl" />
      </div>
      <div className="absolute right-4 top-4 flex items-center gap-1"><LanguageSwitcher /><ThemeToggle /></div>

      <div className="w-full max-w-3xl text-center">
        <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-primary/15 text-primary"><Lock size={22} /></div>
        <h1 className="text-2xl font-bold tracking-tight">{headline}</h1>
        <p className="mt-2 text-sm text-muted-foreground">Pick a plan to keep using SwingAI. You can continue on the free plan with basic access, or upgrade for the full screener, alerts and analytics.</p>

        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {/* Free */}
          <div className="flex flex-col rounded-2xl border border-border bg-card/70 p-5 text-left">
            <div className="font-semibold">Free</div>
            <div className="mt-1 text-2xl font-bold">₹0</div>
            <ul className="mt-3 flex-1 space-y-1 text-sm text-muted-foreground">
              <li>Daily picks (limited)</li><li>Paper trading + journal</li><li>Nifty 50 scanner</li>
            </ul>
            <Button variant="outline" className="mt-4 w-full" disabled={busy} onClick={chooseFree}>
              {busy ? "Activating…" : "Continue on Free"}
            </Button>
          </div>
          {/* Paid plans */}
          {plans.map((p: any) => (
            <div key={p.id} className={`flex flex-col rounded-2xl border p-5 text-left ${p.featured ? "border-primary ring-1 ring-primary/30" : "border-border bg-card/70"}`}>
              <div className="flex items-center gap-2 font-semibold">{p.name}{p.featured && <span className="rounded-full bg-primary/15 px-2 text-[10px] font-semibold text-primary">POPULAR</span>}</div>
              <div className="mt-1 text-2xl font-bold">₹{p.price_inr}<span className="text-sm font-normal text-muted-foreground">/{p.interval}</span></div>
              <ul className="mt-3 flex-1 space-y-1 text-sm text-muted-foreground">
                {(p.features || []).slice(0, 4).map((f: string, i: number) => (
                  <li key={i} className="flex gap-1.5"><Check size={15} className="mt-0.5 shrink-0 text-success" />{f}</li>
                ))}
              </ul>
              <Button className="mt-4 w-full" onClick={() => router.push(`/${locale}/billing`)}>Upgrade</Button>
            </div>
          ))}
        </div>

        <button onClick={() => { logout(); router.replace(`/${locale}/login`); }}
          className="mt-8 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
          <LogOut size={14} /> Log out
        </button>
      </div>
    </main>
  );
}
