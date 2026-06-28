"use client";
// User dashboard — Layers 1-2 (risk + process). Rich, responsive, fully API-driven (blueprint/14).
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { Target, Percent, Gauge, Activity, Wallet, ArrowRight } from "lucide-react";
import { api, type DailyPicks } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { DashboardShell } from "../../../components/DashboardShell";
import { RiskCalculator } from "../../../components/RiskCalculator";
import { RegimeBanner, StatCard, ScoreBar, HeatMeter, Skeleton } from "../../../components/dashboard-ui";
import { MarketStatus } from "../../../components/MarketStatus";

function DashboardInner() {
  const t = useTranslations();
  const { locale } = useParams<{ locale: string }>();
  const token = useAuth((s) => s.token);
  const [me, setMe] = useState<any>(null);
  const [picks, setPicks] = useState<DailyPicks | null>(null);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [tradeMsg, setTradeMsg] = useState<{ symbol: string; ok: boolean; text: string } | null>(null);
  const [tradingSym, setTradingSym] = useState<string | null>(null);
  const [fetchingData, setFetchingData] = useState(false);

  const refresh = useCallback((tok: string) => {
    api.portfolio(tok).then(setPortfolio).catch(() => {});
    api.analytics(tok).then(setAnalytics).catch(() => {});
  }, []);

  // Load picks; if the DB is empty (first run / after `fresh`), kick off the screener pipeline
  // and poll until today's picks land — the server keeps running even if the trigger request
  // exceeds the client timeout. The top progress bar shows throughout (each call is in-flight).
  // `alive()` lets the effect cancel all polling on unmount / token change, so loops never
  // accumulate across mounts (which was hammering /api/daily-picks, even after logout).
  const loadPicks = useCallback(async (tok: string, alive: () => boolean) => {
    const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
    let p = await api.dailyPicks().catch(() => null);
    if (!alive()) return;
    if (p?.picks?.length) { setPicks(p); return; }   // already have picks → done, no polling
    if (!tok) { setPicks(p); return; }

    // Empty DB (first run only): the server scans NIFTY 50 first (fast paint), then the full universe.
    setFetchingData(true);
    api.refreshPicks(tok).catch(() => {});
    for (let i = 0; i < 30 && alive(); i++) {          // wait ~90s for the fast NIFTY 50 picks
      await sleep(3000);
      if (!alive()) break;
      p = await api.dailyPicks().catch(() => null);
      if (p?.picks?.length) { setPicks(p); break; }
    }
    if (!alive()) return;
    setFetchingData(false);

    // Quietly upgrade to the broader NIFTY 500 picks when the full scan finishes (no loader).
    const key = p?.picks?.map((x: any) => x.symbol).join(",") || "";
    for (let i = 0; i < 40 && alive(); i++) {          // up to ~5 min, then stop
      await sleep(7000);
      if (!alive()) return;
      const np = await api.dailyPicks().catch(() => null);
      const k = np?.picks?.map((x: any) => x.symbol).join(",") || "";
      if (k && k !== key) { setPicks(np); break; }
    }
  }, []);

  async function paperTrade(p: any) {
    if (!token) return;
    setTradingSym(p.symbol); setTradeMsg(null);
    try {
      await api.paperBuy(token, {
        stock_symbol: p.symbol, entry_price: p.plan.entry, stop_loss: p.plan.stop,
        target: p.plan.target_1, quantity: p.plan.quantity, entry_reason: "from daily pick",
      });
      setTradeMsg({ symbol: p.symbol, ok: true, text: `${t("dashboard.tradeOpened")}: ${p.plan.quantity} ${p.symbol}` });
      refresh(token);
    } catch (e: any) {
      setTradeMsg({ symbol: p.symbol, ok: false, text: `${t("dashboard.tradeFailed")}: ${String(e?.message || e).slice(0, 90)}` });
    } finally { setTradingSym(null); }
  }

  useEffect(() => {
    if (!token) return;
    let alive = true;
    api.me(token).then(setMe).catch(() => {});
    loadPicks(token, () => alive);
    refresh(token);
    return () => { alive = false; };   // cancel polling on unmount / token change
  }, [token, refresh, loadPicks]);

  const hasTrades = analytics?.trades > 0;

  return (
    <div className="space-y-8">
      {me?.name && <p className="text-sm text-muted-foreground">{t("dashboard.welcome", { name: me.name })}</p>}

      <MarketStatus />

      {fetchingData && (
        <div className="flex items-center gap-3 rounded-xl border border-primary/30 bg-primary/5 px-4 py-3">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary/30 border-t-primary" />
          <div>
            <div className="text-sm font-medium">Finding today's top setups…</div>
            <div className="text-xs text-muted-foreground">Scanning the Nifty 50 first for a quick read, then widening to the full Nifty 500 in the background. Picks appear here automatically — you can keep using the app.</div>
          </div>
        </div>
      )}

      <RegimeBanner regime={picks?.picks?.[0]?.regime} cashMode={picks?.cash_mode}
        note={picks?.cash_mode ? t("dashboard.cashMode") : undefined} />

      {/* performance KPIs */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("dashboard.performance")}</h2>
        {!analytics ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}</div>
        ) : hasTrades ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard label={t("dashboard.expectancy")} value={`${analytics.expectancy_r}R`} Icon={Target}
              tone={analytics.expectancy_r > 0 ? "up" : analytics.expectancy_r < 0 ? "down" : "default"} delay={0} />
            <StatCard label={t("dashboard.winRate")} value={`${analytics.win_rate_pct}%`} Icon={Percent} delay={0.05} />
            <StatCard label={t("dashboard.profitFactor")} value={String(analytics.profit_factor ?? "—")} Icon={Gauge} delay={0.1} />
            <StatCard label={t("dashboard.trades")} value={String(analytics.trades)} Icon={Activity} delay={0.15} />
          </div>
        ) : (
          <Card className="p-5 text-sm text-muted-foreground">{t("dashboard.noClosedTrades")}</Card>
        )}
      </section>

      {/* daily picks */}
      <section>
        <div className="mb-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("dashboard.picks")}</h2>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Top swing-trade setups for this session — the highest-conviction stocks with a clean entry right now,
            screened from the <b className="text-foreground">NIFTY 500</b> on live prices.
            {picks?.date ? <> As of <span className="text-foreground">{picks.date}</span>.</> : null}
            {" "}Browse the full universe by tier on the <Link href={`/${locale}/scan`} className="text-primary hover:underline">Scanner</Link>.
          </p>
        </div>
        {!picks ? (
          <div className="space-y-3">{[0, 1].map((i) => <Skeleton key={i} className="h-40" />)}</div>
        ) : picks.cash_mode ? (
          <Card className="p-6 text-muted-foreground">{t("dashboard.cashMode")}</Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {picks.picks.map((p, i) => (
              <motion.div key={p.symbol} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <Card className="overflow-hidden p-0">
                  <div className="flex items-center justify-between bg-gradient-to-r from-primary/10 to-transparent px-5 py-3">
                    <div className="text-lg font-bold">{p.symbol}</div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-primary/15 px-2 py-0.5 text-xs font-semibold text-primary">Score {Math.round(p.score)}</span>
                      <span className="rounded-full bg-success/15 px-2 py-0.5 text-xs font-semibold text-success">R:R {p.plan.rr_ratio}</span>
                    </div>
                  </div>
                  <div className="px-5 py-4">
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm sm:grid-cols-4">
                      <Field label={t("dashboard.entry")} value={`₹${p.plan.entry}`} />
                      <Field label={t("dashboard.stop")} value={`₹${p.plan.stop}`} tone="down" />
                      <Field label="T1" value={`₹${p.plan.target_1}`} tone="up" />
                      <Field label="T2" value={`₹${p.plan.target_2}`} tone="up" />
                      <Field label={t("dashboard.qty")} value={String(p.plan.quantity)} />
                      <Field label={t("dashboard.size")} value={`₹${Number(p.plan.position_size).toLocaleString("en-IN")}`} />
                      <Field label="RSI" value={String((p as any).analysis?.rsi ?? "—")} />
                      <Field label="Regime" value={p.regime} />
                    </div>
                    <ScoreBar breakdown={(p as any).score_breakdown} />
                    {(p as any).explanation_hinglish && (
                      <p className="mt-3 rounded-lg bg-muted/50 p-3 text-sm leading-relaxed">{(p as any).explanation_hinglish}</p>
                    )}
                    <div className="mt-4 flex items-center gap-3">
                      <Button size="sm" disabled={tradingSym === p.symbol} onClick={() => paperTrade(p)}>
                        {tradingSym === p.symbol ? t("dashboard.placing") : t("dashboard.paperTrade")} <ArrowRight size={14} className="ml-1" />
                      </Button>
                      {tradeMsg?.symbol === p.symbol && (
                        <span className={`text-sm ${tradeMsg.ok ? "text-success" : "text-destructive"}`}>{tradeMsg.text}</span>
                      )}
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </section>

      {/* portfolio + risk calculator */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("dashboard.portfolio")}</h2>
          <Card className="space-y-4 p-5">
            {!portfolio ? <Skeleton className="h-20" /> : (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <StatCard label={t("dashboard.capital")} value={`₹${Number(portfolio.capital).toLocaleString("en-IN")}`} Icon={Wallet} />
                  <StatCard label={t("dashboard.open")} value={String(portfolio.open_positions)} Icon={Activity} />
                </div>
                <HeatMeter pct={Number(portfolio.portfolio_heat_pct) || 0} />
              </>
            )}
          </Card>
        </div>
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("dashboard.positionSizing")}</h2>
          {me && <RiskCalculator capital={Number(me.capital_amount) || 100000} token={token} onTraded={() => token && refresh(token)} />}
        </div>
      </section>

      <p className="border-t border-border pt-6 text-xs text-muted-foreground">{t("common.disclaimer")}</p>
    </div>
  );
}

function Field({ label, value, tone }: { label: string; value: string; tone?: "up" | "down" }) {
  const cls = tone === "up" ? "text-success" : tone === "down" ? "text-destructive" : "text-foreground";
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={`font-semibold tabular-nums ${cls}`}>{value}</div>
    </div>
  );
}

export default function DashboardPage() {
  return <DashboardShell><DashboardInner /></DashboardShell>;
}
