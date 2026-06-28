"use client";
// Integrations & secrets vault UI (blueprint/17). Secrets are write-only + masked;
// the plaintext is never returned by the API. Test-Connection decrypts server-side.
import { useCallback, useEffect, useState } from "react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../../lib/auth";

const KNOWN = [
  { provider: "gemini", category: "llm" },
  { provider: "openrouter", category: "llm" },
  { provider: "angelone", category: "data" },
  { provider: "razorpay", category: "payments" },
];

export default function AdminIntegrations() {
  const token = useAuth((s) => s.token);
  const [list, setList] = useState<any[]>([]);
  const [secret, setSecret] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<Record<string, string>>({});
  const [denied, setDenied] = useState(false);

  const load = useCallback(() => {
    if (!token) return;
    api.adminIntegrations(token).then((r) => setList(r.integrations)).catch(() => setDenied(true));
  }, [token]);
  useEffect(() => { if (token) load(); }, [token, load]);

  if (denied) return <Card className="p-6">403 — admin access required.</Card>;

  const byProvider = (p: string) => list.find((i) => i.provider === p);

  async function save(provider: string, category: string) {
    if (!token) return;
    await api.upsertIntegration(token, provider, {
      category, provider, enabled: true,
      secret: secret[provider] || undefined,
    });
    setSecret({ ...secret, [provider]: "" });
    load();
  }
  async function test(provider: string) {
    if (!token) return;
    const r = await api.testIntegration(token, provider);
    setStatus({ ...status, [provider]: r.status });
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">Integrations &amp; secrets</h1>
      <p className="text-sm text-muted-foreground">Keys are encrypted at rest and never shown again.</p>
      {KNOWN.map(({ provider, category }) => {
        const row = byProvider(provider);
        return (
          <Card key={provider} className="p-4">
            <div className="flex items-center justify-between">
              <div className="font-medium capitalize">{provider} <span className="text-xs text-muted-foreground">({category})</span></div>
              <div className="text-xs text-muted-foreground">
                {row?.secret_set ? `key set ${row.secret_hint}` : "no key"} {row?.last_status ? `· ${row.last_status}` : ""}
              </div>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <input type="password" placeholder="paste API key" value={secret[provider] || ""}
                onChange={(e) => setSecret({ ...secret, [provider]: e.target.value })}
                className="min-w-48 flex-1 rounded-md border border-border bg-transparent px-2 py-1 text-sm" />
              <Button size="sm" onClick={() => save(provider, category)}>Save</Button>
              <Button size="sm" variant="outline" onClick={() => test(provider)}>Test</Button>
              {status[provider] && <span className="text-sm">{status[provider]}</span>}
            </div>
          </Card>
        );
      })}
    </div>
  );
}
