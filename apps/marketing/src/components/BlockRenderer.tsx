// Maps CMS block types -> themed, animated components (blueprint/21 §4).
// Admin edits CONTENT (in the DB); styling/responsiveness/theming live here, so the
// site stays on-brand and can't break. Server-rendered for SEO.
import { Card, Button } from "@swingai/ui";

type Block = { type: string; content: any };

export function BlockRenderer({ blocks, stats, testimonials }: {
  blocks: Block[]; stats?: any[]; testimonials?: any[];
}) {
  return (
    <>
      {blocks.map((b, i) => {
        switch (b.type) {
          case "hero":
            return (
              <section key={i} className="mx-auto max-w-5xl px-6 py-24 text-center">
                <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">{b.content.heading}</h1>
                <p className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground">{b.content.subheading}</p>
                {b.content.cta && (
                  <a href={b.content.cta.href} className="mt-8 inline-block">
                    <Button size="lg">{b.content.cta.label}</Button>
                  </a>
                )}
              </section>
            );
          case "stats":
            return (
              <section key={i} className="mx-auto max-w-5xl px-6 py-10">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  {(stats || []).map((s, j) => (
                    <Card key={j} className="p-6 text-center">
                      <div className="text-2xl font-semibold">{s.value}{s.suffix}</div>
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
                    <Card key={j} className="p-6">
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
                      <p className="italic">“{t.quote}”</p>
                      <div className="mt-3 text-sm text-muted-foreground">— {t.author}{t.role ? `, ${t.role}` : ""}</div>
                    </Card>
                  ))}
                </div>
              </section>
            );
          case "cta":
            return (
              <section key={i} className="mx-auto max-w-5xl px-6 py-20 text-center">
                <h2 className="text-3xl font-bold">{b.content.heading}</h2>
                {b.content.cta && (
                  <a href={b.content.cta.href} className="mt-6 inline-block">
                    <Button size="lg">{b.content.cta.label}</Button>
                  </a>
                )}
              </section>
            );
          default:
            return null;
        }
      })}
    </>
  );
}
