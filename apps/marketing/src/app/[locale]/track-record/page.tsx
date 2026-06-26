// Public, honest track record (blueprint/00 #2, blueprint/08). Server-rendered for SEO.
// Win% = wins/(wins+losses+scratches), in R-multiples, net — never massaged. Two records:
// the SCREENER's own resolved picks (the moat) and what users did in paper trading.
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { api } from "@swingai/api-client";
import { Card } from "@swingai/ui";

export const revalidate = 600;

export const metadata: Metadata = {
  title: "Track Record — SwingAI",
  description: "Transparent, honest performance of our screened swing setups — every trade, in R-multiples, net of costs.",
};

function Stat({ label, value, tone }: { label: string; value: string; tone?: "up" | "down" }) {
  const cls = tone === "up" ? "text-success" : tone === "down" ? "text-destructive"
    : "bg-gradient-to-br from-foreground to-foreground/60 bg-clip-text text-transparent";
  return (
    <Card className="relative overflow-hidden p-5 text-center">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary to-success" />
      <div className={`text-2xl font-bold tabular-nums ${cls}`}>{value}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
    </Card>
  );
}

function Record({ title, sub, summary, isPaper }: { title: string; sub: string; summary: any; isPaper?: boolean }) {
  const n = isPaper ? summary?.trades : summary?.resolved;
  return (
    <section className="mt-10">
      <h2 className="text-xl font-semibold">{title}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{sub}</p>
      {!summary || !n ? (
        <Card className="mt-4 p-6 text-sm text-muted-foreground">
          {summary?.note ?? "No closed trades yet."} We publish results only when there are real, closed trades — never fabricated.
        </Card>
      ) : (
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat label="Expectancy (avg R)" value={`${summary.expectancy_r}R`}
            tone={summary.expectancy_r > 0 ? "up" : summary.expectancy_r < 0 ? "down" : undefined} />
          <Stat label="Win rate" value={`${summary.win_rate_pct}%`} />
          <Stat label={isPaper ? "Profit factor" : "Targets hit"} value={String(isPaper ? (summary.profit_factor ?? "—") : summary.hit_target)} />
          <Stat label={isPaper ? "Trades" : "Resolved picks"} value={String(n)} />
        </div>
      )}
    </section>
  );
}

export default async function TrackRecord() {
  const t = await getTranslations();
  const tr = await api.trackRecord().catch(() => null);

  return (
    <main className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-0 h-96 w-96 -translate-x-1/2 rounded-full bg-primary/10 blur-3xl" />
      </div>
      <div className="mx-auto max-w-4xl px-6 py-16">
        <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-success" /> Honest · net of costs · in R-multiples
        </span>
        <h1 className="mt-5 text-4xl font-bold tracking-tight">Track Record</h1>
        <p className="mt-3 max-w-2xl text-muted-foreground">
          Every screened setup, counted honestly — wins, losses, and scratches all in the denominator. No metric massaging.
        </p>

        <Record title="The screener's own picks" sub="Did our deterministic setups actually work? This is the moat."
          summary={tr?.screener} />
        <Record title="What users did (paper trades)" sub="Real paper trades placed from picks — the human result."
          summary={tr?.paper_trades} isPaper />

        <p className="mt-12 border-t border-border pt-6 text-xs text-muted-foreground">{tr?.disclaimer ?? t("common.disclaimer")}</p>
      </div>
    </main>
  );
}
