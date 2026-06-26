// Landing page — DB-driven content, server-rendered (ISR) for SEO (blueprint/08,21).
// generateMetadata reads the page's SEO from the CMS; content comes from blocks.
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { api } from "@swingai/api-client";
import { BlockRenderer } from "../../components/BlockRenderer";

export const revalidate = 3600; // ISR — refreshed on publish via on-demand revalidation

export async function generateMetadata({ params: { locale } }: { params: { locale: string } }): Promise<Metadata> {
  const page = await api.cmsPage("home", locale).catch(() => null);
  return {
    title: page?.seo?.title ?? "SwingAI",
    description: page?.seo?.description,
    alternates: { canonical: page?.seo?.canonical },
  };
}

export default async function Home({ params: { locale } }: { params: { locale: string } }) {
  const t = await getTranslations();
  const [page, stats, testimonials] = await Promise.all([
    api.cmsPage("home", locale).catch(() => ({ sections: [] as any[] })),
    api.stats(locale).then((r) => r.stats ?? []).catch(() => []),
    api.testimonials(locale).then((r) => r.testimonials ?? []).catch(() => []),
  ]);

  // Safety fallback so the landing is never blank (e.g. backend momentarily down).
  const sections = page.sections?.length ? page.sections : [{
    type: "hero",
    content: {
      heading: "Disciplined swing trading, proven honestly.",
      subheading: "Risk-managed NSE swing setups, transparent track record, and paper trading to prove it.",
      cta: { label: "Start free", href: `/${locale}/signup` },
    },
  }];

  return (
    <main className="min-h-screen bg-background text-foreground">
      <BlockRenderer blocks={sections} stats={stats} testimonials={testimonials} locale={locale} />
    </main>
  );
}
