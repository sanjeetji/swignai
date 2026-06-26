"use client";
// Users — list, search, block/unblock, force-logout (blueprint/18). All API-driven.
import { useCallback, useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../../lib/auth";

export default function AdminUsers() {
  const token = useAuth((s) => s.token);
  const startImpersonation = useAuth((s) => s.startImpersonation);
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const [data, setData] = useState<any>(null);
  const [q, setQ] = useState("");
  const [denied, setDenied] = useState(false);
  const [open, setOpen] = useState<string | null>(null);   // expanded user id
  const [detail, setDetail] = useState<any>(null);

  const load = useCallback(() => {
    if (!token) return;
    api.adminUsers(token, q).then(setData).catch(() => setDenied(true));
  }, [token, q]);

  useEffect(() => { if (token) load(); }, [token, load]);

  async function openDetail(id: string) {
    if (!token) return;
    if (open === id) { setOpen(null); setDetail(null); return; }
    setOpen(id); setDetail(null);
    try { setDetail(await api.adminUserDetail(token, id)); } catch {}
  }

  if (denied) return <Card className="p-6">403 — admin access required.</Card>;

  async function act(fn: Promise<any>) { try { await fn; load(); if (open && token) setDetail(await api.adminUserDetail(token, open)); } catch {} }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Users ({data?.total ?? "…"})</h1>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search email…"
        className="w-full max-w-sm rounded-md border border-border bg-transparent px-3 py-2 text-sm" />
      <Card className="divide-y divide-border">
        {data?.users?.map((u: any) => (
          <div key={u.id} className="px-4 py-3 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <button className="text-left" onClick={() => openDetail(u.id)}>
                <div>{u.email} {u.blocked && <span className="text-destructive">· blocked</span>}</div>
                <div className="text-xs text-muted-foreground">
                  {u.tier} · joined {String(u.created_at).slice(0, 10)} · {open === u.id ? "▲ hide" : "▼ sessions"}
                </div>
              </button>
              <div className="flex gap-2">
                {u.blocked
                  ? <Button size="sm" variant="outline" onClick={() => token && act(api.unblockUser(token, u.id))}>Unblock</Button>
                  : <Button size="sm" variant="outline" onClick={() => token && act(api.blockUser(token, u.id))}>Block</Button>}
                <Button size="sm" variant="ghost" onClick={() => token && act(api.forceLogout(token, u.id))}>Force-logout</Button>
                <Button size="sm" variant="ghost" onClick={async () => {
                  if (!token) return;
                  try { const r = await api.impersonate(token, u.id); startImpersonation(r.access_token, r.refresh_token, r.email); router.push(`/${locale}/dashboard`); } catch {}
                }}>View as</Button>
              </div>
            </div>
            {open === u.id && (
              <div className="mt-3 rounded-md bg-muted/40 p-3 text-xs">
                {!detail ? <div className="text-muted-foreground">Loading…</div> : (
                  <>
                    <div className="mb-2 font-medium">Sessions ({detail.sessions?.length ?? 0})</div>
                    {detail.sessions?.length ? detail.sessions.map((s: any) => (
                      <div key={s.id} className="flex justify-between gap-2 py-0.5">
                        <span>{[s.device, s.os, s.browser].filter(Boolean).join(" · ") || "unknown"}{s.active ? "" : " · revoked"}</span>
                        <span className="text-muted-foreground">
                          {s.ip}{s.geo?.city ? ` · ${s.geo.city}, ${s.geo.country}` : ""} · {String(s.last_active_at).slice(0, 16)}
                        </span>
                      </div>
                    )) : <div className="text-muted-foreground">No sessions.</div>}
                    <div className="mb-1 mt-3 font-medium">Recent logins ({detail.login_history?.length ?? 0})</div>
                    {detail.login_history?.slice(0, 5).map((h: any, i: number) => (
                      <div key={i} className="flex justify-between gap-2 py-0.5">
                        <span className={h.success ? "" : "text-destructive"}>{h.success ? "ok" : `failed (${h.reason || "?"})`}</span>
                        <span className="text-muted-foreground">{h.ip} · {String(h.at).slice(0, 16)}</span>
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>
        ))}
      </Card>
    </div>
  );
}
