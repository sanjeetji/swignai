"use client";
// Super Admin shell — users + event logs (full-page, blueprint/16,18,22). RBAC enforced
// server-side; non-admins get 403 from the API. Sub-pages (appearance, integrations,
// CMS, sessions, analytics) follow the same pattern — see STATUS.md for what's pending.
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { api } from "@swingai/api-client";
import { Card, ThemeToggle } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";

export default function AdminPage() {
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const token = useAuth((s) => s.token);
  const [users, setUsers] = useState<any>(null);
  const [events, setEvents] = useState<any>(null);
  const [denied, setDenied] = useState(false);

  useEffect(() => {
    if (token === null) return;
    if (!token) { router.push(`/${locale}/login`); return; }
    api.adminUsers(token).then(setUsers).catch(() => setDenied(true));
    api.eventLogs(token).then(setEvents).catch(() => {});
  }, [token, locale, router]);

  if (denied) return <main className="p-10">403 — you don't have admin access.</main>;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <h1 className="font-semibold">Admin</h1>
        <ThemeToggle />
      </header>
      <section className="mx-auto max-w-5xl space-y-8 px-6 py-8">
        <div>
          <h2 className="mb-3 text-lg font-semibold">Users ({users?.total ?? "…"})</h2>
          <Card className="divide-y divide-border">
            {users?.users?.map((u: any) => (
              <div key={u.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <span>{u.email}</span>
                <span className="text-muted-foreground">{u.tier} {u.blocked ? "· blocked" : ""}</span>
              </div>
            ))}
          </Card>
        </div>
        <div>
          <h2 className="mb-3 text-lg font-semibold">Event Logs</h2>
          <Card className="divide-y divide-border">
            {events?.events?.slice(0, 20).map((e: any) => (
              <div key={e.id} className="flex items-center justify-between px-4 py-2 text-xs">
                <span className="font-mono">{e.type}</span>
                <span className="text-muted-foreground">{e.category}/{e.level} · {e.created_at?.slice(0, 19)}</span>
              </div>
            ))}
          </Card>
        </div>
      </section>
    </main>
  );
}
