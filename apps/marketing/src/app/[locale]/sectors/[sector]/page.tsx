// Public per-sector SEO page (blueprint/12) — the stocks we cover in one NSE sector,
// each linking to its full technical analysis. Server-rendered + ISR + JSON-LD.
// Educational framing — not advice (blueprint/09).
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { api } from "@swingai/api-client";

export const revalidate = 3600;

async function resolve(sectorSlug: string): Promise<{ name: string; symbols: string[] } | null> {
  const { sectors } = await api.sectors();
  const slug = decodeURIComponent(sectorSlug).toLowerCase();
  const name = Object.keys(sectors).find((s) => s.toLowerCase() === slug);
  return name ? { name, symbols: sectors[name] } : null;
}

export async function generateMetadata({ params }: { params: { sector: string } }): Promise<Metadata> {
  const found = await resolve(params.sector);
  const name = found?.name || params.sector;
  return {
    title: `${name} sector — swing-trade analysis | SwingAI`,
    description: `Swing-trade technical analysis for ${name} stocks on NSE — educational, computed from real prices, not advice.`,
    alternates: { canonical: `/sectors/${params.sector.toLowerCase()}` },
  };
}

export default async function SectorPage({ params }: { params: { locale: string; sector: string } }) {
  const found = await resolve(params.sector);
  if (!found) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: `${found.name} sector swing-trade analysis`,
    about: { "@type": "Thing", name: `${found.name} sector (NSE)` },
    hasPart: found.symbols.map((s) => ({ "@type": "Corporation", name: s })),
  };

  return (
    <main className="mx-auto min-h-screen max-w-3xl bg-background px-6 py-12 text-foreground">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <Link href={`/${params.locale}/sectors`} className="text-sm text-muted-foreground hover:underline">
        ← All sectors
      </Link>
      <h1 className="mt-3 text-3xl font-bold">{found.name} — swing-trade analysis</h1>
      <p className="mt-2 text-muted-foreground">
        {found.symbols.length} {found.name} stocks we screen on NSE. Educational technical analysis from real prices — not advice.
      </p>
      <ul className="mt-8 grid gap-3 sm:grid-cols-2">
        {found.symbols.map((sym) => (
          <li key={sym}>
            <Link
              href={`/${params.locale}/stocks/${encodeURIComponent(sym)}`}
              className="block rounded-lg border border-border px-4 py-3 font-medium hover:bg-muted"
            >
              {sym}
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
