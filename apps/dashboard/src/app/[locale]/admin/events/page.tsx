"use client";
// Event-log viewer with filters (blueprint/22). Unified stream; audit = admin+security.
import { useCallback, useEffect, useState } from "react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../../lib/auth";

const CATEGORIES = ["", "security", "admin", "system", "integration", "product", "data"];
const LEVELS = ["", "info", "warning", "error", "critical"];

export default function AdminEvents() {
  const token = useAuth((s) => s.token);
  const [events, setEvents] = useState<any[]>([]);
  const [category, setCategory] = useState("");
  const [level, setLevel] = useState("");
  const [denied, setDenied] = useState(false);

  const load = useCallback(() => {
    if (!token) return;
    api.eventLogs(token, category || undefined, level || undefined)
      .then((r) => setEvents(r.events)).catch(() => setDenied(true));
  }, [token, category, level]);
  useEffect(() => { if (token) load(); }, [token, load]);

  if (denied) return <Card className="p-6">403 — admin access required.</Card>;

  const color = (lvl: string) =>
    lvl === "critical" || lvl === "error" ? "text-destructive"
      : lvl === "warning" ? "text-warning" : "text-muted-foreground";

  async function exportCsv() {
    if (!token) return;
    try {
      const blob = await api.eventLogsExport(token, category || undefined, level || undefined);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "event-logs.csv"; a.click();
      URL.revokeObjectURL(url);
    } catch {}
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Event logs</h1>
      <div className="flex flex-wrap items-center gap-3">
        <select value={category} onChange={(e) => setCategory(e.target.value)}
          className="rounded-md border border-border bg-background px-2 py-1 text-sm">
          {CATEGORIES.map((c) => <option key={c} value={c}>{c || "all categories"}</option>)}
        </select>
        <select value={level} onChange={(e) => setLevel(e.target.value)}
          className="rounded-md border border-border bg-background px-2 py-1 text-sm">
          {LEVELS.map((l) => <option key={l} value={l}>{l || "all levels"}</option>)}
        </select>
        <Button size="sm" variant="outline" onClick={exportCsv}>Export CSV</Button>
      </div>
      <Card className="divide-y divide-border">
        {events.map((e) => (
          <div key={e.id} className="flex items-center justify-between px-4 py-2 text-xs">
            <span className="font-mono">{e.type}</span>
            <span className={color(e.level)}>{e.category}/{e.level} · {String(e.created_at).slice(0, 19)}</span>
          </div>
        ))}
        {events.length === 0 && <div className="px-4 py-6 text-sm text-muted-foreground">No events match.</div>}
      </Card>
    </div>
  );
}
