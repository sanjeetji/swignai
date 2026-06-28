"use client";
// Watchlist & price alerts (blueprint/13 retention) — track stocks + "alert me at ₹X".
// Theme/font-aware via design tokens. All data is live from the API (no hardcoding).
import { useCallback, useEffect, useState } from "react";
import { Star, Trash2, Bell, BellRing, Plus } from "lucide-react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { DashboardShell } from "../../../components/DashboardShell";

function Inner() {
  const token = useAuth((s) => s.token);
  const [symbols, setSymbols] = useState<string[]>([]);
  const [watch, setWatch] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [newSym, setNewSym] = useState("");
  const [aSym, setASym] = useState("");
  const [aDir, setADir] = useState("above");
  const [aPrice, setAPrice] = useState("");
  const [digest, setDigest] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    if (!token) return;
    api.watchlist(token).then((r) => setWatch(r.items || [])).catch(() => {});
    api.alerts(token).then((r) => setAlerts(r.alerts || [])).catch(() => {});
  }, [token]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { api.universe().then((r) => setSymbols(r.symbols || [])).catch(() => {}); }, []);
  useEffect(() => { if (token) api.getPrefs(token).then((p) => setDigest(p?.email_digest !== false)).catch(() => {}); }, [token]);

  async function addWatch() {
    if (!token || !newSym.trim()) return;
    setBusy(true);
    try { await api.watchAdd(token, newSym.trim().toUpperCase()); setNewSym(""); load(); } finally { setBusy(false); }
  }
  async function addAlert() {
    if (!token || !aSym.trim() || !aPrice) return;
    setBusy(true);
    try { await api.alertCreate(token, { symbol: aSym.trim().toUpperCase(), direction: aDir, target_price: Number(aPrice) }); setASym(""); setAPrice(""); load(); }
    finally { setBusy(false); }
  }
  async function toggleDigest() {
    if (!token) return;
    const next = !digest; setDigest(next);
    try { await api.setDigest(token, next); } catch { setDigest(!next); }
  }

  const inp = "rounded-md border border-border bg-transparent px-3 py-2 text-sm";

  return (
    <div className="space-y-6">
      {/* Digest toggle */}
      <Card className="flex flex-wrap items-center justify-between gap-3 p-4">
        <div className="flex items-center gap-2 text-sm">
          <Bell size={16} className="text-primary" />
          <span><span className="font-medium">Email digest</span> — daily picks + weekly performance to your inbox.</span>
        </div>
        <Button size="sm" variant={digest ? "default" : "outline"} onClick={toggleDigest}>
          {digest ? "On" : "Off"}
        </Button>
      </Card>

      {/* Watchlist */}
      <Card className="p-5">
        <div className="mb-3 flex items-center gap-2">
          <Star size={18} className="text-warning" />
          <h2 className="font-semibold">Watchlist</h2>
          <span className="text-xs text-muted-foreground">({watch.length})</span>
        </div>
        <div className="mb-4 flex flex-wrap gap-2">
          <input list="universe" value={newSym} onChange={(e) => setNewSym(e.target.value)}
            placeholder="Add a stock (e.g. HAL)" className={`${inp} flex-1 min-w-[180px]`}
            onKeyDown={(e) => e.key === "Enter" && addWatch()} />
          <datalist id="universe">{symbols.map((s) => <option key={s} value={s} />)}</datalist>
          <Button size="sm" disabled={busy} onClick={addWatch}><Plus size={15} /> Add</Button>
        </div>
        {watch.length === 0 ? (
          <p className="text-sm text-muted-foreground">No stocks yet. Add ones you want to keep an eye on — you'll see their latest price and screener score here.</p>
        ) : (
          <div className="divide-y divide-border">
            {watch.map((w) => (
              <div key={w.symbol} className="flex items-center justify-between gap-2 py-2.5 text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{w.symbol}</span>
                  {typeof w.score === "number" && (
                    <span className="rounded-full bg-primary/15 px-1.5 py-0.5 text-[10px] font-medium text-primary">score {Math.round(w.score)}</span>
                  )}
                  {w.regime_ok && <span className="rounded-full bg-success/15 px-1.5 py-0.5 text-[10px] font-medium text-success">valid setup</span>}
                </div>
                <div className="flex items-center gap-3">
                  <span className="tabular-nums text-muted-foreground">{w.price ? `₹${Number(w.price).toLocaleString("en-IN")}` : "—"}</span>
                  <button onClick={() => token && api.watchRemove(token, w.symbol).then(load)} className="text-muted-foreground hover:text-destructive" aria-label="remove">
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Price alerts */}
      <Card className="p-5">
        <div className="mb-3 flex items-center gap-2">
          <BellRing size={18} className="text-primary" />
          <h2 className="font-semibold">Price alerts</h2>
          <span className="text-xs text-muted-foreground">({alerts.filter((a) => a.is_active).length} active)</span>
        </div>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <input list="universe" value={aSym} onChange={(e) => setASym(e.target.value)} placeholder="Stock" className={`${inp} w-32`} />
          <select value={aDir} onChange={(e) => setADir(e.target.value)} className={inp}>
            <option value="above">goes above</option>
            <option value="below">goes below</option>
          </select>
          <input type="number" value={aPrice} onChange={(e) => setAPrice(e.target.value)} placeholder="₹ price" className={`${inp} w-28`} />
          <Button size="sm" disabled={busy} onClick={addAlert}><Plus size={15} /> Set alert</Button>
        </div>
        {alerts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No alerts. Set one and we'll notify you (in-app + email/SMS if configured) the moment a stock crosses your price.</p>
        ) : (
          <div className="divide-y divide-border">
            {alerts.map((a) => (
              <div key={a.id} className="flex items-center justify-between gap-2 py-2.5 text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{a.symbol}</span>
                  <span className="text-muted-foreground">{a.direction} ₹{Number(a.target_price).toLocaleString("en-IN")}</span>
                  {a.is_active
                    ? <span className="rounded-full bg-warning/15 px-1.5 py-0.5 text-[10px] font-medium text-warning">watching</span>
                    : <span className="rounded-full bg-success/15 px-1.5 py-0.5 text-[10px] font-medium text-success">triggered</span>}
                </div>
                <button onClick={() => token && api.alertDelete(token, a.id).then(load)} className="text-muted-foreground hover:text-destructive" aria-label="delete">
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>

      <p className="text-xs text-muted-foreground">Prices update with the daily screener run. Educational technical screening, not investment advice.</p>
    </div>
  );
}

export default function WatchlistPage() {
  return <DashboardShell><Inner /></DashboardShell>;
}
