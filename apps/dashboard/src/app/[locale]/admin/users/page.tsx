"use client";
// Users — list, search, block/unblock, force-logout (blueprint/18). All API-driven.
import { useCallback, useEffect, useState } from "react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../../lib/auth";

export default function AdminUsers() {
  const token = useAuth((s) => s.token);
  const [data, setData] = useState<any>(null);
  const [q, setQ] = useState("");
  const [denied, setDenied] = useState(false);

  const load = useCallback(() => {
    if (!token) return;
    api.adminUsers(token, q).then(setData).catch(() => setDenied(true));
  }, [token, q]);

  useEffect(() => { if (token) load(); }, [token, load]);

  if (denied) return <Card className="p-6">403 — admin access required.</Card>;

  async function act(fn: Promise<any>) { try { await fn; load(); } catch {} }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Users ({data?.total ?? "…"})</h1>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search email…"
        className="w-full max-w-sm rounded-md border border-border bg-transparent px-3 py-2 text-sm" />
      <Card className="divide-y divide-border">
        {data?.users?.map((u: any) => (
          <div key={u.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm">
            <div>
              <div>{u.email} {u.blocked && <span className="text-destructive">· blocked</span>}</div>
              <div className="text-xs text-muted-foreground">{u.tier} · joined {String(u.created_at).slice(0, 10)}</div>
            </div>
            <div className="flex gap-2">
              {u.blocked
                ? <Button size="sm" variant="outline" onClick={() => token && act(api.unblockUser(token, u.id))}>Unblock</Button>
                : <Button size="sm" variant="outline" onClick={() => token && act(api.blockUser(token, u.id))}>Block</Button>}
              <Button size="sm" variant="ghost" onClick={() => token && act(api.forceLogout(token, u.id))}>Force-logout</Button>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
