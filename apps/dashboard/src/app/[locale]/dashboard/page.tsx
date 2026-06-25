"use client";
// User dashboard — Layers 1-2 (risk + process). Picks + score breakdown, enforced
// risk calculator → paper buy, portfolio, personal analytics. All from the API.
import { useCallback, useEffect, useState } from "react";
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
  const [analytics, setAnalytics] = useState<any>(null);

  const refresh = useCallback((tok: string) => {
    api.portfolio(tok).then(setPortfolio).catch(() => {});
    api.analytics(tok).then(setAnalytics).catch(() => {});
  }, []);

  useEffect(() => {
    if (token === null) return;
    if (!token) { router.push(`/${locale}/login`); return; }
    api.me(token).then(setMe).catch(() => { logout(); router.push(`/${locale}/login`); });
    api.dailyPicks().then(setPicks).catch(() => {});
    refresh(token);
  }, [token, locale, router, logout, refresh]);

  const kpi = (label: string, value: string) => (
    <Card className="p-4"><div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div></Card>
  );

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <h1 className="font-semibold">{t("title")}</h1>
        <div className="flex items-center gap-3">
          <a href={`/${locale}/analyze`} className="text-sm text-muted-foreground hover:underline">Analyze</a>
          <span className="text-sm text-muted-foreground">{me?.email}</span>
          <ThemeToggle />
          <Button variant="outline" size="sm" onClick={() => { logout(); router.push(`/${locale}/login`); }}>Logout</Button>
        </div>
      </header>

      <section className="mx-auto max-w-5xl space-y-10 px-6 py-8">
        {/* Personal analytics — expectancy is the headline (blueprint/20) */}
        <div>
          <h2 className="mb-3 text-lg font-semibold">Your performance</h2>
          {analytics?.trades > 0 ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {kpi("Expectancy (R)", String(analytics.expectancy_r))}
              {kpi("Win rate", `${analytics.win_rate_pct}%`)}
              {kpi("Profit factor", String(analytics.profit_factor ?? "—"))}
              {kpi("Trades", String(analytics.trades))}
            </div>
          ) : <Card className="p-5 text-sm text-muted-foreground">No closed trades yet — your honest stats appear here.</Card>}
        </div>

        {/* Picks */}
        <div>
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
                    <div>Entry ₹{p.plan.entry}</div><div>Stop ₹{p.plan.stop}</div>
                    <div>T1 ₹{p.plan.target_1}</div><div>T2 ₹{p.plan.target_2}</div>
                    <div>R:R {p.plan.rr_ratio}</div><div>Qty {p.plan.quantity}</div>
                    <div>Size ₹{p.plan.position_size}</div><div>RSI {p.rsi}</div>
                  </div>
                  {(p as any).explanation_hinglish && (
                    <p className="mt-3 rounded-md bg-muted/40 p-2 text-sm">{(p as any).explanation_hinglish}</p>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Portfolio + Risk calculator */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div>
            <h2 className="mb-3 text-lg font-semibold">{t("portfolio")}</h2>
            <Card className="p-5 text-sm">
              {portfolio ? (
                <>
                  <div className="flex flex-wrap gap-6">
                    <div>Capital: ₹{Number(portfolio.capital).toLocaleString("en-IN")}</div>
                    <div>Open: {portfolio.open_positions}</div>
                    <div>Heat: {portfolio.portfolio_heat_pct}%</div>
                  </div>
                  {portfolio.trades?.length > 0 && (
                    <div className="mt-3 divide-y divide-border">
                      {portfolio.trades.map((tr: any) => (
                        <div key={tr.id} className="flex items-center justify-between py-2">
                          <span>{tr.symbol} · {tr.qty} @ ₹{tr.entry}</span>
                          <span className="text-muted-foreground">SL {tr.stop} · T {tr.target}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : "Loading…"}
            </Card>
          </div>
          <div>
            <h2 className="mb-3 text-lg font-semibold">Position sizing</h2>
            {me && <RiskCalculator capital={Number(me.capital_amount) || 100000} token={token}
              onTraded={() => token && refresh(token)} />}
          </div>
        </div>
      </section>
    </main>
  );
}
