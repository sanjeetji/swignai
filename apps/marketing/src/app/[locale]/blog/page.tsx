// Blog index (blueprint/12) — weekly auto-generated "top setups" posts. SSR + ISR.
import type { Metadata } from "next";
import Link from "next/link";
import { api } from "@swingai/api-client";
import { Card } from "@swingai/ui";

export const revalidate = 1800;

export const metadata: Metadata = {
  title: "Blog — SwingAI",
  description: "Weekly NSE swing-trade setups and market-regime notes — deterministic analysis, educational, not advice.",
  alternates: { canonical: "/blog" },
};

export default async function Blog({ params: { locale } }: { params: { locale: string } }) {
  const { posts } = await api.blogList(locale);
  return (
    <main className="mx-auto min-h-screen max-w-3xl bg-background px-6 py-16 text-foreground">
      <h1 className="text-3xl font-bold tracking-tight">Blog</h1>
      <p className="mt-2 text-muted-foreground">Weekly setups &amp; market-regime notes — educational, not advice.</p>
      <div className="mt-8 space-y-3">
        {posts.length === 0 ? (
          <Card className="p-6 text-sm text-muted-foreground">No posts yet — the weekly digest publishes every Monday.</Card>
        ) : posts.map((p: any) => (
          <Link key={p.slug} href={`/${locale}/blog/${p.slug}`}>
            <Card className="p-5 transition-shadow hover:shadow-md">
              <div className="font-semibold">{p.title}</div>
              {p.description && <p className="mt-1 text-sm text-muted-foreground">{p.description}</p>}
            </Card>
          </Link>
        ))}
      </div>
    </main>
  );
}
