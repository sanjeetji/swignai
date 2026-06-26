"use client";
// Super Admin shell — full-page sections (blueprint/16). RBAC enforced server-side
// (non-admins get 403 from the API); this is the navigation chrome.
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { ThemeToggle, LanguageSwitcher } from "@swingai/ui";
import { RequireAuth } from "../../../components/RequireAuth";

const NAV = [
  ["", "Overview"], ["users", "Users"], ["plans", "Plans"], ["flags", "Feature Flags"],
  ["appearance", "Appearance"], ["integrations", "Integrations"], ["events", "Event Logs"],
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { locale } = useParams<{ locale: string }>();
  const pathname = usePathname();
  const base = `/${locale}/admin`;
  return (
    <RequireAuth>
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-card/60 px-6 py-3 backdrop-blur">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary font-bold text-primary-foreground shadow-sm shadow-primary/30">S</span>
          <span className="font-semibold tracking-tight">SwingAI <span className="text-muted-foreground">Admin</span></span>
        </div>
        <div className="flex items-center gap-3">
          <Link href={`/${locale}/dashboard`} className="text-sm text-muted-foreground transition-colors hover:text-foreground">← Dashboard</Link>
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
      </header>
      <div className="mx-auto flex max-w-6xl gap-6 px-6 py-6">
        <nav className="w-44 shrink-0 space-y-1">
          {NAV.map(([slug, label]) => {
            const href = slug ? `${base}/${slug}` : base;
            const active = pathname === href;
            return (
              <Link key={slug} href={href}
                className={`block rounded-md px-3 py-2 text-sm ${active ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}>
                {label}
              </Link>
            );
          })}
        </nav>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
    </RequireAuth>
  );
}
