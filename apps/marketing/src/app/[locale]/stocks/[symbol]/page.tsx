// Public per-stock SEO page (blueprint/08,12). Server-rendered + ISR; deterministic
// technical analysis from real prices, with JSON-LD so Google / AI search can cite it.
// Educational framing — not advice (blueprint/09).
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { api } from "@swingai/api-client";
import { StockAnalysisView, type StockAnalysisData } from "@swingai/ui";

export const revalidate = 1800; // ISR — refresh every 30 min

async function load(symbol: string): Promise<StockAnalysisData | null> {
  try {
    return await api.stockAnalysis(symbol);
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: { params: { symbol: string } }): Promise<Metadata> {
  const d = await load(params.symbol);
  const sym = (d?.symbol || params.symbol).toUpperCase();
  const title = `${sym} — swing-trade technical analysis | SwingAI`;
  const description = d
    ? `${sym}: RSI ${d.analysis.rsi}, ADX ${d.analysis.adx}, ${d.swing_screen.meets_all_conditions ? "meets" : "does not meet"} swing conditions (score ${d.swing_screen.score}). Educational technical analysis from real prices — not advice.`
    : `Swing-trade technical analysis for ${sym} — educational, computed from real prices.`;
  return { title, description, alternates: { canonical: `/stocks/${sym}` } };
}

export default async function StockPage({ params }: { params: { symbol: string } }) {
  const d = await load(params.symbol);
  if (!d) notFound();

  // JSON-LD structured data (educational analysis, not a recommendation)
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: `${d.symbol} swing-trade technical analysis`,
    dateModified: d.as_of,
    about: { "@type": "Corporation", name: d.symbol },
    description: d.disclaimer,
  };

  return (
    <main className="mx-auto min-h-screen max-w-3xl bg-background px-6 py-12 text-foreground">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <StockAnalysisView data={d} />
    </main>
  );
}
