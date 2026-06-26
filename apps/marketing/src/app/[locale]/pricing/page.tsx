// Public pricing (blueprint/20) — plans are admin-managed in the dashboard and served
// from /api/billing/plans, so marketing pricing updates without a redeploy. SSR + ISR.
import type { Metadata } from "next";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";

export const revalidate = 600;

const DASH = process.env.NEXT_PUBLIC_DASHBOARD_URL || "http://localhost:9001";

export const metadata: Metadata = {
  title: "Pricing — SwingAI",
  description: "Simple plans for disciplined swing trading — daily picks, scanner, paper trading, journal and analytics.",
  alternates: { canonical: "/pricing" },
};

export default async function Pricing({ params: { locale } }: { params: { locale: string } }) {
  const data = await api.billingPlans().catch(() => ({ plans: [] as any[], currency: "INR", enabled: false }));

  const free = {
    id: "free", name: "Free", price_inr: 0,
    features: ["Daily picks + scanner", "Paper trading + journal", "Honest track record"], featured: false,
  };
  const all = [free, ...(data.plans || [])];

  return (
    <main className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-0 h-96 w-96 -translate-x-1/2 rounded-full bg-primary/10 blur-3xl" />
      </div>
      <div className="mx-auto max-w-5xl px-6 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight">Simple, honest pricing</h1>
          <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
            Start free. Upgrade when the discipline tools pay for themselves. Educational analysis — not advice.
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {all.map((p: any) => (
            <Card key={p.id} className={`relative flex flex-col p-6 ${p.featured ? "border-primary shadow-lg ring-1 ring-primary/20" : ""}`}>
              {p.featured && <div className="absolute right-0 top-0 rounded-bl-lg bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground">Most popular</div>}
              <div className="text-lg font-bold">{p.name}</div>
              <div className="mt-2 text-4xl font-bold">
                ₹{p.price_inr}<span className="text-sm font-normal text-muted-foreground">/{p.interval || "mo"}</span>
              </div>
              <ul className="mt-5 flex-1 space-y-2 text-sm text-muted-foreground">
                {(p.features || []).map((f: string, i: number) => (
                  <li key={i} className="flex gap-2"><span className="text-success">✓</span> {f}</li>
                ))}
              </ul>
              <a href={p.id === "free" ? `${DASH}/${locale}/signup` : `${DASH}/${locale}/billing`} className="mt-6">
                <Button className="w-full" variant={p.featured ? "default" : "outline"}>
                  {p.id === "free" ? "Start free" : `Choose ${p.name}`}
                </Button>
              </a>
            </Card>
          ))}
        </div>
        <p className="mt-10 text-center text-xs text-muted-foreground">Payments via Razorpay (UPI, cards, netbanking). Cancel anytime.</p>
      </div>
    </main>
  );
}
