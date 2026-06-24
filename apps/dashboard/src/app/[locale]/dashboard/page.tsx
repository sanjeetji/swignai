"use client";
// User dashboard — Layers 1-2 (risk + process). Picks with score breakdown, enforced
// risk plan, portfolio heat. All data from the API (blueprint/08,20). No hardcoded data.
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { api, type DailyPicks } from "@swingai/api-client";
import { Card, Button, ThemeToggle } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { RiskCalculator } from "../../../components/RiskCalculator";

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const token = useAuth((s) => s.token);
  const logout = useAuth((s) => s.logout);
  const [me, setMe] = useState<any>(null);
  const [picks, setPicks] = useState<DailyPicks | null>(null);
  const [portfolio, setPortfolio] = useState<any>(null);

  useEffect(() => {
    if (token === null) return; // wait for hydration
    if (!token) { router.push(`/${locale}/login`); return; }
    api.me(token).then(setMe).catch(() => { logout(); router.push(`/${locale}/login`); });
    api.dailyPicks().then(setPicks).catch(() => {});
    api.portfolio(token).then(setPortfolio).catch(() => {});
  }, [token, locale, router, logout]);

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <h1 className="font-semibold">{t("title")}</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">{me?.email}</span>
          <ThemeToggle />
          <Button variant="outline" size="sm" onClick={() => { logout(); router.push(`/${locale}/login`); }}>
            Logout
          </Button>
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-6 py-8">
        <h2 className="mb-3 text-lg font-semibold">{t("picks")}</h2>
        {picks?.cash_mode ? (
          <Card className="p-6 text-muted-foreground">{t("cashMode")}</Card>
        ) : (
          <div className="space-y-4">
            {picks?.picks.map((p) => (
              <Card key={p.symbol} className="p-5">
                <div className="flex items-center justify-between">
                  <div className="text-lg font-semibold">{p.symbol}</div>
                  <div className="text-sm text-muted-foreground">Score {p.score} · {p.regime}</div>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
                  <div>Entry ₹{p.plan.entry}</div>
                  <div>Stop ₹{p.plan.stop}</div>
                  <div>T1 ₹{p.plan.target_1}</div>
                  <div>T2 ₹{p.plan.target_2}</div>
                  <div>R:R {p.plan.rr_ratio}</div>
                  <div>Qty {p.plan.quantity}</div>
                  <div>Size ₹{p.plan.position_size}</div>
                  <div>RSI {p.rsi}</div>
                </div>
                <p className="mt-3 text-xs text-muted-foreground">{p.disclaimer}</p>
              </Card>
            ))}
          </div>
        )}

        <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div>
            <h2 className="mb-3 text-lg font-semibold">{t("portfolio")}</h2>
            <Card className="p-5 text-sm">
              {portfolio ? (
                <div className="flex flex-wrap gap-6">
                  <div>Capital: ₹{Number(portfolio.capital).toLocaleString("en-IN")}</div>
                  <div>Open: {portfolio.open_positions}</div>
                  <div>Heat: {portfolio.portfolio_heat_pct}%</div>
                </div>
              ) : "Loading…"}
            </Card>
          </div>
          <div>
            <h2 className="mb-3 text-lg font-semibold">Position sizing</h2>
            {me && <RiskCalculator capital={Number(me.capital_amount) || 100000} />}
          </div>
        </div>
      </section>
    </main>
  );
}
