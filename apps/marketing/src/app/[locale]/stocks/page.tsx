// Public stocks index (blueprint/12) — every NSE symbol we cover, linking to its full
// technical analysis. Server-rendered + ISR. Educational framing — not advice.
import type { Metadata } from "next";
import Link from "next/link";
import { api } from "@swingai/api-client";

export const revalidate = 3600;

export const metadata: Metadata = {
  title: "NSE stocks — swing-trade technical analysis | SwingAI",
  description:
    "Browse swing-trade technical analysis for the NSE stocks we cover — educational, computed from real prices, not advice.",
  alternates: { canonical: "/stocks" },
};

export default async function StocksPage({ params }: { params: { locale: string } }) {
  const { symbols } = await api.universe();

  return (
    <main className="mx-auto min-h-screen max-w-3xl bg-background px-6 py-12 text-foreground">
      <h1 className="text-3xl font-bold">Stocks we screen</h1>
      <p className="mt-2 text-muted-foreground">
        {symbols.length} NSE stocks with full swing-trade technical analysis. Educational, from real prices — not advice.
      </p>
      <p className="mt-4 text-sm">
        <Link href={`/${params.locale}/sectors`} className="text-primary hover:underline">
          Browse by sector →
        </Link>
      </p>
      <ul className="mt-8 grid gap-3 sm:grid-cols-3">
        {symbols.map((sym) => (
          <li key={sym}>
            <Link
              href={`/${params.locale}/stocks/${encodeURIComponent(sym)}`}
              className="block rounded-lg border border-border px-4 py-3 text-center font-medium hover:bg-muted"
            >
              {sym}
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
