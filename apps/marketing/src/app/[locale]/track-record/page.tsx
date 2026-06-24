// Public, honest track record (blueprint/00 #2, blueprint/08). Server-rendered for SEO.
// Win% = wins/(wins+losses+scratches), in R-multiples, net — never massaged.
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { api } from "@swingai/api-client";
import { Card } from "@swingai/ui";

export const revalidate = 600;

export const metadata: Metadata = {
  title: "Track Record — SwingAI",
  description: "Transparent, honest performance of our screened swing setups — every trade, in R-multiples, net of costs.",
};

export default async function TrackRecord() {
  const t = await getTranslations();
  const tr = await api.trackRecord().catch(() => null);
  const stat = (label: string, value: string) => (
    <Card className="p-5 text-center">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">{label}</div>
    </Card>
  );

  return (
    <main className="mx-auto min-h-screen max-w-4xl bg-background px-6 py-16 text-foreground">
      <h1 className="text-3xl font-bold">Track Record</h1>
      <p className="mt-2 text-muted-foreground">
        Every screened setup, counted honestly — wins, losses, and scratches all in the denominator.
      </p>

      {!tr || tr.trades === 0 ? (
        <Card className="mt-8 p-6 text-muted-foreground">
          {tr?.note ?? "No closed trades yet."} We publish results only when there are real, closed trades —
          we don't fabricate numbers.
        </Card>
      ) : (
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {stat("Expectancy (avg R)", String(tr.expectancy_r))}
          {stat("Win rate", `${tr.win_rate_pct}%`)}
          {stat("Profit factor", String(tr.profit_factor ?? "—"))}
          {stat("Trades", String(tr.trades))}
        </div>
      )}

      <p className="mt-10 border-t border-border pt-6 text-xs text-muted-foreground">{t("common.disclaimer")}</p>
    </main>
  );
}
