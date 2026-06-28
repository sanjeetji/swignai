"use client";
// Feature flags — toggle runtime kill-switches (blueprint/16). All API-driven.
import { useCallback, useEffect, useState } from "react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../../lib/auth";

export default function AdminFlags() {
  const token = useAuth((s) => s.token);
  const [flags, setFlags] = useState<any[]>([]);
  const [denied, setDenied] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    api.featureFlags(token).then((r) => setFlags(r.flags)).catch(() => setDenied(true));
  }, [token]);
  useEffect(() => { if (token) load(); }, [token, load]);

  if (denied) return <Card className="p-6">403 — admin access required.</Card>;

  async function toggle(key: string, enabled: boolean) {
    if (!token) return;
    setBusy(key);
    try { await api.upsertFlag(token, key, { enabled }); load(); } finally { setBusy(null); }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">Feature flags</h1>
      <p className="text-sm text-muted-foreground">
        Runtime kill-switches. Turning a flag off makes its feature read as unavailable (404) instantly.
      </p>
      <Card className="divide-y divide-border">
        {flags.map((f) => (
          <div key={f.key} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm">
            <div>
              <div className="font-mono">{f.key} {f.enabled
                ? <span className="text-success">· on</span>
                : <span className="text-muted-foreground">· off</span>}</div>
              {f.description && <div className="text-xs text-muted-foreground">{f.description}</div>}
            </div>
            <Button size="sm" variant={f.enabled ? "outline" : "default"} disabled={busy === f.key}
              onClick={() => toggle(f.key, !f.enabled)}>
              {f.enabled ? "Disable" : "Enable"}
            </Button>
          </div>
        ))}
        {flags.length === 0 && <div className="px-4 py-6 text-sm text-muted-foreground">No flags defined.</div>}
      </Card>
    </div>
  );
}
