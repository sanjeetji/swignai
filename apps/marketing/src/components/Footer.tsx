// Marketing footer (blueprint/09) — legal links + the educational-not-advice disclaimer.
import { getTranslations } from "next-intl/server";

export async function Footer({ locale }: { locale: string }) {
  const t = await getTranslations();
  const link = "text-muted-foreground transition-colors hover:text-foreground";
  return (
    <footer className="border-t border-border bg-card/30">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">S</span>
            <span className="font-semibold">{t("brand.name")}</span>
          </div>
          <nav className="flex flex-wrap gap-x-5 gap-y-2">
            <a href={`/${locale}/pricing`} className={link}>Pricing</a>
            <a href={`/${locale}/track-record`} className={link}>Track Record</a>
            <a href={`/${locale}/stocks`} className={link}>Stocks</a>
            <a href={`/${locale}/privacy`} className={link}>Privacy</a>
            <a href={`/${locale}/terms`} className={link}>Terms &amp; Disclaimer</a>
          </nav>
        </div>
        <p className="mt-6 text-xs leading-relaxed text-muted-foreground">
          Educational technical analysis — <b>not investment advice</b>. SwingAI is not a SEBI-registered Research
          Analyst or Investment Adviser and does not execute trades. Markets carry risk; past results don’t guarantee
          future returns. © {new Date().getFullYear()} {t("brand.name")}.
        </p>
      </div>
    </footer>
  );
}
