"use client";
// Super Admin shell — full-page sections (blueprint/16). RBAC enforced server-side
// (non-admins get 403 from the API); this is the navigation chrome.
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { ThemeToggle } from "@swingai/ui";

const NAV = [
  ["", "Overview"], ["users", "Users"], ["appearance", "Appearance"],
  ["integrations", "Integrations"], ["events", "Event Logs"],
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { locale } = useParams<{ locale: string }>();
  const pathname = usePathname();
  const base = `/${locale}/admin`;
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border px-6 py-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold">SwingAI Admin</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href={`/${locale}/dashboard`} className="text-sm text-muted-foreground hover:underline">← Dashboard</Link>
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
  );
}
