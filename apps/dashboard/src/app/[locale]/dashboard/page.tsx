"use client";
// User dashboard — Layers 1-2 (risk + process). Auth-gated; fully localized chrome.
import { useCallback, useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api, type DailyPicks } from "@swingai/api-client";
import { Card, Button, ThemeToggle, LanguageSwitcher } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { RequireAuth } from "../../../components/RequireAuth";
import { RiskCalculator } from "../../../components/RiskCalculator";

function DashboardInner() {
  const t = useTranslations();
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
    if (!token) return;
    api.me(token).then(setMe).catch(() => { logout(); router.replace(`/${locale}/login`); });
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
        <h1 className="font-semibold">{t("dashboard.title")}</h1>
        <div className="flex items-center gap-3">
          <Link href={`/${locale}/analyze`} className="text-sm text-muted-foreground hover:underline">{t("nav.analyze")}</Link>
          <span className="hidden text-sm text-muted-foreground sm:inline">{me?.email}</span>
          <LanguageSwitcher />
          <ThemeToggle />
          <Button variant="outline" size="sm" onClick={() => { logout(); router.replace(`/${locale}/login`); }}>{t("nav.logout")}</Button>
        </div>
      </header>

      <section className="mx-auto max-w-5xl space-y-10 px-6 py-8">
        <div>
          <h2 className="mb-3 text-lg font-semibold">{t("dashboard.performance")}</h2>
          {analytics?.trades > 0 ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {kpi(t("dashboard.expectancy"), String(analytics.expectancy_r))}
              {kpi(t("dashboard.winRate"), `${analytics.win_rate_pct}%`)}
              {kpi(t("dashboard.profitFactor"), String(analytics.profit_factor ?? "—"))}
              {kpi(t("dashboard.trades"), String(analytics.trades))}
            </div>
          ) : <Card className="p-5 text-sm text-muted-foreground">{t("dashboard.noClosedTrades")}</Card>}
        </div>

        <div>
          <h2 className="mb-3 text-lg font-semibold">{t("dashboard.picks")}</h2>
          {picks?.cash_mode ? (
            <Card className="p-6 text-muted-foreground">{t("dashboard.cashMode")}</Card>
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
                    <div>Size ₹{p.plan.position_size}</div><div>RSI {(p as any).analysis?.rsi ?? "—"}</div>
                  </div>
                  {(p as any).explanation_hinglish && (
                    <p className="mt-3 rounded-md bg-muted/40 p-2 text-sm">{(p as any).explanation_hinglish}</p>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div>
            <h2 className="mb-3 text-lg font-semibold">{t("dashboard.portfolio")}</h2>
            <Card className="p-5 text-sm">
              {portfolio ? (
                <div className="flex flex-wrap gap-6">
                  <div>{t("dashboard.capital")}: ₹{Number(portfolio.capital).toLocaleString("en-IN")}</div>
                  <div>{t("dashboard.open")}: {portfolio.open_positions}</div>
                  <div>{t("dashboard.heat")}: {portfolio.portfolio_heat_pct}%</div>
                </div>
              ) : t("common.loading")}
            </Card>
          </div>
          <div>
            <h2 className="mb-3 text-lg font-semibold">{t("dashboard.positionSizing")}</h2>
            {me && <RiskCalculator capital={Number(me.capital_amount) || 100000} token={token}
              onTraded={() => token && refresh(token)} />}
          </div>
        </div>
        <p className="border-t border-border pt-6 text-xs text-muted-foreground">{t("common.disclaimer")}</p>
      </section>
    </main>
  );
}

export default function DashboardPage() {
  return <RequireAuth><DashboardInner /></RequireAuth>;
}
