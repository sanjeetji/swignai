// Blog post (blueprint/12) — renders a published CmsPage(type=blog) with a 'prose' section.
// Minimal markdown (bold + bullets) — no markdown dependency. SSR + ISR + JSON-LD.
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { api } from "@swingai/api-client";

export const revalidate = 1800;

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const page = await api.cmsPage(params.slug).catch(() => null);
  if (!page) return { title: "Blog — SwingAI" };
  return { title: page.seo?.title ?? page.title, description: page.seo?.description,
           alternates: { canonical: `/blog/${params.slug}` } };
}

function renderMarkdown(md: string) {
  return md.split("\n").map((line, i) => {
    if (!line.trim()) return <div key={i} className="h-3" />;
    const html = line.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
    if (line.startsWith("- ")) {
      return <li key={i} className="ml-5 list-disc text-muted-foreground"
        dangerouslySetInnerHTML={{ __html: html.slice(2) }} />;
    }
    return <p key={i} className="text-muted-foreground" dangerouslySetInnerHTML={{ __html: html }} />;
  });
}

export default async function BlogPost({ params }: { params: { locale: string; slug: string } }) {
  const page = await api.cmsPage(params.slug).catch(() => null);
  if (!page || page.type !== "blog") notFound();
  const body: string = page.sections?.find((s: any) => s.type === "prose")?.content?.markdown ?? "";
  const jsonLd = {
    "@context": "https://schema.org", "@type": "Article", headline: page.title,
    description: page.seo?.description, about: { "@type": "Thing", name: "NSE swing trading" },
  };
  return (
    <main className="mx-auto min-h-screen max-w-3xl bg-background px-6 py-16 text-foreground">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <a href={`/${params.locale}/blog`} className="text-sm text-muted-foreground hover:underline">← All posts</a>
      <h1 className="mt-3 text-3xl font-bold tracking-tight">{page.title}</h1>
      <div className="mt-6 space-y-1 text-sm leading-relaxed">{renderMarkdown(body)}</div>
    </main>
  );
}
