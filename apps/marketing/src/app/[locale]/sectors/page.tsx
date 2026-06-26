// Public sector index (blueprint/12) — lists every NSE sector we cover, linking to
// each sector page. Server-rendered + ISR. Educational framing — not advice.
import type { Metadata } from "next";
import Link from "next/link";
import { api } from "@swingai/api-client";

export const revalidate = 3600;

export const metadata: Metadata = {
  title: "NSE sectors — swing-trade analysis by sector | SwingAI",
  description:
    "Browse swing-trade technical analysis across NSE sectors — Banking, IT, Pharma, Auto, Energy and more. Educational, computed from real prices.",
  alternates: { canonical: "/sectors" },
};

export default async function SectorsPage({ params }: { params: { locale: string } }) {
  const { sectors } = await api.sectors();
  const names = Object.keys(sectors);

  return (
    <main className="mx-auto min-h-screen max-w-3xl bg-background px-6 py-12 text-foreground">
      <h1 className="text-3xl font-bold">Swing-trade analysis by sector</h1>
      <p className="mt-2 text-muted-foreground">
        Educational technical screening across {names.length} NSE sectors — computed from real prices, not advice.
      </p>
      <ul className="mt-8 grid gap-3 sm:grid-cols-2">
        {names.map((name) => (
          <li key={name}>
            <Link
              href={`/${params.locale}/sectors/${encodeURIComponent(name.toLowerCase())}`}
              className="flex items-center justify-between rounded-lg border border-border px-4 py-3 hover:bg-muted"
            >
              <span className="font-medium">{name}</span>
              <span className="text-sm text-muted-foreground">{sectors[name].length} stocks</span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
