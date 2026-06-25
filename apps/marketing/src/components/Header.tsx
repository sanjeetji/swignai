"use client";
// Marketing header — brand + language switcher + auth CTAs. In dev the dashboard is a
// separate app/port; in prod it's the same domain (/app). NEXT_PUBLIC_DASHBOARD_URL
// points at it so "Log in / Start free" actually lead somewhere.
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Button, LanguageSwitcher, ThemeToggle } from "@swingai/ui";

const DASH = process.env.NEXT_PUBLIC_DASHBOARD_URL || "http://localhost:9001";

export function Header() {
  const t = useTranslations();
  const { locale } = useParams<{ locale: string }>();
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-background/80 px-6 py-3 backdrop-blur">
      <a href={`/${locale}`} className="text-lg font-bold">{t("brand.name")}</a>
      <div className="flex items-center gap-2">
        <a href={`/${locale}/track-record`} className="hidden px-2 text-sm text-muted-foreground hover:underline sm:inline">
          {t("nav.trackRecord")}
        </a>
        <LanguageSwitcher />
        <ThemeToggle />
        <a href={`${DASH}/${locale}/login`}><Button variant="outline" size="sm">{t("nav.login")}</Button></a>
        <a href={`${DASH}/${locale}/signup`}><Button size="sm">{t("nav.signup")}</Button></a>
      </div>
    </header>
  );
}
