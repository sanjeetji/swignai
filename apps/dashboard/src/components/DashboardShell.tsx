"use client";
// Responsive app shell (blueprint/14 §6): desktop left sidebar + mobile bottom-tab bar,
// sticky top bar, active-route highlight, admin link for privileged users. Wraps every
// authed page so navigation is consistent. Auth-gated via RequireAuth.
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { LayoutDashboard, LineChart, Radar, BookOpenText, BarChart3, CreditCard, Settings, ShieldCheck, LogOut } from "lucide-react";
import { ThemeToggle, LanguageSwitcher } from "@swingai/ui";
import { api } from "@swingai/api-client";
import { useAuth } from "../lib/auth";
import { RequireAuth } from "./RequireAuth";
import { NotificationBell } from "./NotificationBell";

type NavItem = { slug: string; label: string; Icon: typeof LayoutDashboard; admin?: boolean };

function ShellInner({ children }: { children: React.ReactNode }) {
  const t = useTranslations();
  const router = useRouter();
  const pathname = usePathname();
  const { locale } = useParams<{ locale: string }>();
  const token = useAuth((s) => s.token);
  const logout = useAuth((s) => s.logout);
  const [me, setMe] = useState<any>(null);

  useEffect(() => {
    if (token) api.me(token).then(setMe).catch(() => {});
  }, [token]);

  const isAdmin = (me?.roles || []).some((r: string) => r === "super_admin" || r === "admin");
  const items: NavItem[] = [
    { slug: "dashboard", label: t("nav.dashboard"), Icon: LayoutDashboard },
    { slug: "scan", label: t("nav.scan"), Icon: Radar },
    { slug: "analyze", label: t("nav.analyze"), Icon: LineChart },
    { slug: "journal", label: t("nav.journal"), Icon: BookOpenText },
    { slug: "analytics", label: t("nav.analytics"), Icon: BarChart3 },
    { slug: "billing", label: t("nav.billing"), Icon: CreditCard },
    { slug: "settings", label: t("nav.settings"), Icon: Settings },
    ...(isAdmin ? [{ slug: "admin", label: t("nav.admin"), Icon: ShieldCheck, admin: true } as NavItem] : []),
  ];
  const active = (slug: string) => pathname === `/${locale}/${slug}` || pathname.startsWith(`/${locale}/${slug}/`);
  const href = (slug: string) => `/${locale}/${slug}`;
  const doLogout = () => { logout(); router.replace(`/${locale}/login`); };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-border bg-card/40 backdrop-blur lg:flex">
        <div className="flex items-center gap-2 px-5 py-5">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground font-bold">S</div>
          <span className="text-lg font-semibold tracking-tight">SwingAI</span>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {items.map(({ slug, label, Icon }) => (
            <Link key={slug} href={href(slug)}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                active(slug) ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}>
              <Icon size={18} /> {label}
            </Link>
          ))}
        </nav>
        <div className="space-y-3 border-t border-border p-3">
          {me?.email && <div className="truncate px-1 text-xs text-muted-foreground" title={me.email}>{me.email}</div>}
          <button onClick={doLogout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
            <LogOut size={16} /> {t("nav.logout")}
          </button>
        </div>
      </aside>

      {/* mobile top bar */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-card/70 px-4 py-3 backdrop-blur lg:hidden">
        <div className="flex items-center gap-2">
          <div className="grid h-7 w-7 place-items-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">S</div>
          <span className="font-semibold">SwingAI</span>
        </div>
        <div className="flex items-center gap-1">
          <NotificationBell /><LanguageSwitcher /><ThemeToggle />
          <button onClick={doLogout} className="ml-1 rounded-md p-2 text-muted-foreground hover:bg-muted" aria-label={t("nav.logout")}>
            <LogOut size={18} />
          </button>
        </div>
      </header>

      {/* content */}
      <div className="lg:ml-60">
        {/* desktop top bar — notifications top-right */}
        <header className="sticky top-0 z-20 hidden items-center justify-end gap-1 border-b border-border bg-background/70 px-10 py-2.5 backdrop-blur lg:flex">
          <NotificationBell /><LanguageSwitcher /><ThemeToggle />
        </header>
        <main className="px-4 pb-24 pt-5 sm:px-6 lg:px-10 lg:pb-10 lg:pt-8">
          <div className="mx-auto max-w-5xl">{children}</div>
        </main>
      </div>

      {/* mobile bottom tabs */}
      <nav className="fixed inset-x-0 bottom-0 z-30 flex border-t border-border bg-card/90 backdrop-blur lg:hidden">
        {items.map(({ slug, label, Icon }) => (
          <Link key={slug} href={href(slug)}
            className={`flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium transition-colors ${
              active(slug) ? "text-primary" : "text-muted-foreground"
            }`}>
            <Icon size={20} /> {label}
          </Link>
        ))}
      </nav>
    </div>
  );
}

export function DashboardShell({ children }: { children: React.ReactNode }) {
  return <RequireAuth><ShellInner>{children}</ShellInner></RequireAuth>;
}
