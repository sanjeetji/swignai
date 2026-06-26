// Maps CMS block types -> themed, animated components (blueprint/21 §4).
// Admin edits CONTENT (in the DB); styling/responsiveness/theming live here, so the
// site stays on-brand and can't break. Server-rendered for SEO.
import { Card, Button } from "@swingai/ui";

type Block = { type: string; content: any };

const DASH = process.env.NEXT_PUBLIC_DASHBOARD_URL || "http://localhost:9001";

// Auth CTAs (/signup, /login) live in the dashboard app; everything else stays local.
function resolveHref(href: string | undefined, locale: string): string {
  if (!href) return "#";
  if (href.includes("signup")) return `${DASH}/${locale}/signup`;
  if (href.includes("login")) return `${DASH}/${locale}/login`;
  return href;
}

export function BlockRenderer({ blocks, stats, testimonials, locale = "en" }: {
  blocks: Block[]; stats?: any[]; testimonials?: any[]; locale?: string;
}) {
  return (
    <>
      {blocks.map((b, i) => {
        switch (b.type) {
          case "hero":
            return (
              <section key={i} className="relative overflow-hidden">
                <div className="pointer-events-none absolute inset-0 -z-10">
                  <div className="absolute left-1/2 top-0 h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-primary/15 blur-3xl" />
                  <div className="absolute bottom-0 right-0 h-72 w-72 rounded-full bg-success/10 blur-3xl" />
                </div>
                <div className="mx-auto max-w-5xl px-6 py-24 text-center sm:py-32">
                  <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-success" /> Educational · risk-first · transparent
                  </span>
                  <h1 className="mx-auto mt-6 max-w-3xl bg-gradient-to-br from-foreground to-foreground/60 bg-clip-text text-4xl font-bold tracking-tight text-transparent sm:text-6xl">
                    {b.content.heading}
                  </h1>
                  <p className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground">{b.content.subheading}</p>
                  <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
                    {b.content.cta && (
                      <a href={resolveHref(b.content.cta.href, locale)}><Button size="lg">{b.content.cta.label}</Button></a>
                    )}
                    <a href={`/${locale}/track-record`}><Button size="lg" variant="outline">See the track record</Button></a>
                  </div>
                  <p className="mt-4 text-xs text-muted-foreground">No credit card · paper trading · honest, net-of-cost results</p>
                </div>
              </section>
            );
          case "stats":
            return (
              <section key={i} className="mx-auto max-w-5xl px-6 py-10">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  {(stats || []).map((s, j) => (
                    <Card key={j} className="relative overflow-hidden p-6 text-center transition-shadow hover:shadow-md">
                      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary to-success" />
                      <div className="bg-gradient-to-br from-foreground to-foreground/60 bg-clip-text text-3xl font-bold text-transparent">{s.value}{s.suffix}</div>
                      <div className="mt-1 text-sm text-muted-foreground">{s.label}</div>
                    </Card>
                  ))}
                </div>
              </section>
            );
          case "features":
            return (
              <section key={i} className="mx-auto max-w-5xl px-6 py-16">
                <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                  {(b.content.items || []).map((f: any, j: number) => (
                    <Card key={j} className="group p-6 transition-all hover:-translate-y-1 hover:shadow-lg">
                      <div className="mb-3 grid h-10 w-10 place-items-center rounded-xl bg-primary/10 font-bold text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                        {j + 1}
                      </div>
                      <h3 className="font-semibold">{f.title}</h3>
                      <p className="mt-2 text-sm text-muted-foreground">{f.body}</p>
                    </Card>
                  ))}
                </div>
              </section>
            );
          case "testimonials":
            return (
              <section key={i} className="mx-auto max-w-5xl px-6 py-16">
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  {(testimonials || []).map((t, j) => (
                    <Card key={j} className="p-6">
                      <div className="text-4xl leading-none text-primary/30">“</div>
                      <p className="-mt-3 italic">{t.quote}</p>
                      <div className="mt-3 text-sm font-medium text-muted-foreground">— {t.author}{t.role ? `, ${t.role}` : ""}</div>
                    </Card>
                  ))}
                </div>
              </section>
            );
          case "cta":
            return (
              <section key={i} className="mx-auto max-w-5xl px-6 py-20">
                <div className="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-br from-primary/15 via-card to-success/10 p-12 text-center">
                  <h2 className="text-3xl font-bold tracking-tight">{b.content.heading}</h2>
                  {b.content.cta && (
                    <a href={resolveHref(b.content.cta.href, locale)} className="mt-6 inline-block">
                      <Button size="lg">{b.content.cta.label}</Button>
                    </a>
                  )}
                </div>
              </section>
            );
          default:
            return null;
        }
      })}
    </>
  );
}
