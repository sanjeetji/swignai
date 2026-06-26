// Programmatic sitemap (blueprint/12) — static marketing pages + one /stocks/[symbol]
// page per covered NSE symbol, for every locale, with hreflang alternates. The symbol
// list comes from the backend universe; if that fetch fails we still emit static routes.
import type { MetadataRoute } from "next";
import { api } from "@swingai/api-client";
import { locales, defaultLocale } from "../i18n";

const SITE = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:9002";

function withAlternates(path: string) {
  const languages: Record<string, string> = {};
  for (const l of locales) languages[l] = `${SITE}/${l}${path}`;
  return {
    url: `${SITE}/${defaultLocale}${path}`,
    alternates: { languages },
  };
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPaths = ["", "/stocks", "/track-record"];
  const entries: MetadataRoute.Sitemap = staticPaths.map((p) => ({
    ...withAlternates(p),
    changeFrequency: "daily",
    priority: p === "" ? 1 : 0.7,
  }));

  const { symbols } = await api.universe();
  for (const sym of symbols) {
    entries.push({
      ...withAlternates(`/stocks/${encodeURIComponent(sym)}`),
      changeFrequency: "daily",
      priority: 0.6,
    });
  }
  return entries;
}
