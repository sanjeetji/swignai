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
import { SubscriptionWall } from "./SubscriptionWall";
import { NotificationBell } from "./NotificationBell";

type NavItem = { slug: string; label: string; Icon: typeof LayoutDashboard; admin?: boolean };

// Per-route header title + subtitle (Title Case), shown in the sticky top bar on every page.
const PAGE_META: Record<string, { title: string; sub: string }> = {
  dashboard: { title: "Dashboard", sub: "Your swing setups, risk & performance" },
  scan: { title: "Scanner", sub: "Screen NSE stocks for valid swing setups" },
  analyze: { title: "Analyze", sub: "Deep-dive any stock's swing setup" },
  journal: { title: "Journal", sub: "Your trades & post-trade review" },
  analytics: { title: "Analytics", sub: "Expectancy, win rate & equity curve" },
  billing: { title: "Plans & Billing", sub: "Manage your subscription & payments" },
  settings: { title: "Settings & Appearance", sub: "Theme, language, security & referrals" },
  admin: { title: "Admin Console", sub: "Platform management" },
};
const titleCase = (s: string) => s.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

function ShellInner({ children }: { children: React.ReactNode }) {
  const t = useTranslations();
  const router = useRouter();
  const pathname = usePathname();
  const { locale } = useParams<{ locale: string }>();
  const token = useAuth((s) => s.token);
  const logout = useAuth((s) => s.logout);
  const impersonating = useAuth((s) => s.impersonating);
  const stopImpersonation = useAuth((s) => s.stopImpersonation);
  const [me, setMe] = useState<any>(undefined);          // undefined = still loading
  const [sub, setSub] = useState<any>(undefined);

  const loadSub = () => { if (token) api.subscription(token).then(setSub).catch(() => setSub(null)); };
  useEffect(() => {
    if (token) {
      api.me(token).then(setMe).catch(() => setMe(null));
      loadSub();
    }
  }, [token]);

  const isAdmin = (me?.roles || []).some((r: string) => r === "super_admin" || r === "admin");
  // Hard paywall: block the app when a trial/paid plan has lapsed (admins bypass). Wait for both
  // me + sub so we never flash the wall while loading.
  const gateReady = me !== undefined && sub !== undefined;
  const walled = gateReady && !isAdmin && sub?.walled === true;

  // Days left on a free trial / paid grace (for the banner).
  const trialDaysLeft = sub?.status === "trialing" && sub?.current_period_end
    ? Math.ceil((new Date(sub.current_period_end).getTime() - Date.now()) / 86400000) : null;
  const graceDaysLeft = sub?.state === "grace" ? sub?.days_left : null;

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
  // Current page header (Title Case) from the route, e.g. /hi/settings → "Settings & Appearance".
  const seg = pathname.split("/")[2] || "dashboard";
  const meta = PAGE_META[seg] || { title: titleCase(seg), sub: "" };
  const doLogout = () => { logout(); router.replace(`/${locale}/login`); };

  // Hard paywall — a lapsed/absent plan blocks the whole app until they pick a plan. The
  // billing page is exempt so a walled user can always reach checkout to pay/renew.
  if (walled && seg !== "billing") return <SubscriptionWall reason={sub?.reason} onResolved={loadSub} />;

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-border bg-card/40 backdrop-blur lg:flex">
        <Link href={href("dashboard")} className="flex items-center gap-2 px-5 py-5 transition-opacity hover:opacity-80" aria-label="SwingAI — dashboard home">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground font-bold">S</div>
          <span className="text-lg font-semibold tracking-tight">SwingAI</span>
        </Link>
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
        <div className="flex min-w-0 items-center gap-2">
          <Link href={href("dashboard")} aria-label="SwingAI — dashboard home" className="shrink-0 transition-opacity hover:opacity-80">
            <div className="grid h-7 w-7 place-items-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">S</div>
          </Link>
          <span className="truncate font-semibold">{meta.title}</span>
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
        {/* desktop top bar — sticky page title (left) + actions (right) */}
        <header className="sticky top-0 z-20 hidden items-center justify-between gap-4 border-b border-border bg-background/80 px-10 py-3 backdrop-blur lg:flex">
          <div className="min-w-0">
            <h1 className="truncate text-lg font-semibold tracking-tight">{meta.title}</h1>
            {meta.sub && <p className="truncate text-xs text-muted-foreground">{meta.sub}</p>}
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <NotificationBell /><LanguageSwitcher /><ThemeToggle />
          </div>
        </header>
        {impersonating && (
          <div className="flex flex-wrap items-center justify-center gap-3 bg-warning/15 px-4 py-2 text-center text-sm text-warning">
            <span>Viewing as <b>{impersonating}</b> (admin impersonation)</span>
            <button onClick={stopImpersonation} className="rounded-md border border-warning/40 px-2 py-0.5 text-xs font-medium hover:bg-warning/20">Exit</button>
          </div>
        )}
        {trialDaysLeft != null && trialDaysLeft > 0 && (
          <div className={`flex flex-wrap items-center justify-center gap-3 px-4 py-2 text-center text-sm ${
            trialDaysLeft <= 3 ? "bg-destructive/10 text-destructive" : "bg-primary/10 text-primary"}`}>
            <span>🎉 Free trial — <b>{trialDaysLeft} day{trialDaysLeft === 1 ? "" : "s"} left</b>. Upgrade to keep full access.</span>
            <Link href={href("billing")} className="rounded-md bg-primary px-2.5 py-0.5 text-xs font-semibold text-primary-foreground hover:opacity-90">Upgrade</Link>
          </div>
        )}
        {graceDaysLeft != null && (
          <div className="flex flex-wrap items-center justify-center gap-3 bg-destructive/10 px-4 py-2 text-center text-sm text-destructive">
            <span>⚠️ Your subscription has lapsed — <b>{graceDaysLeft} day{graceDaysLeft === 1 ? "" : "s"} of grace left</b>. Renew to avoid losing access.</span>
            <Link href={href("billing")} className="rounded-md bg-destructive px-2.5 py-0.5 text-xs font-semibold text-destructive-foreground hover:opacity-90">Renew</Link>
          </div>
        )}
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
