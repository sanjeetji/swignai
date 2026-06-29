"use client";
// NSE Scanner (blueprint/04) — rank the tradeable universe by deterministic score with
// trend / relative-strength / volume, and filter by score / sector / regime bias.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Radar, ArrowUpRight } from "lucide-react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { DashboardShell } from "../../../components/DashboardShell";
import { RegimeBanner, Skeleton } from "../../../components/dashboard-ui";
import { BuyButton } from "../../../components/paper-trade";

const MIN_SCORES = [
  { v: 0, label: "Any score" }, { v: 50, label: "> 50" }, { v: 65, label: "> 65 (solid)" }, { v: 80, label: "> 80 (high conviction)" },
];
const BIAS = [
  { v: "", label: "All setups" }, { v: "valid", label: "Valid setups only" }, { v: "bullish", label: "Bullish trend only" },
];
const UNIVERSES = [
  { v: "nifty50", label: "Nifty 50", n: 50 }, { v: "nifty100", label: "Nifty 100", n: 100 },
  { v: "nifty150", label: "Nifty 150", n: 150 }, { v: "nifty200", label: "Nifty 200", n: 200 },
  { v: "nifty250", label: "Nifty 250", n: 250 }, { v: "nifty300", label: "Nifty 300", n: 300 },
  { v: "nifty500", label: "Nifty 500", n: 500 },
];

function trendCls(t: string) {
  return t === "Strong Up" ? "bg-success/15 text-success" : t === "Up" ? "bg-success/10 text-success"
    : t === "Down" ? "bg-destructive/15 text-destructive" : "bg-muted text-muted-foreground";
}

function ScanInner() {
  const { locale } = useParams<{ locale: string }>();
  const token = useAuth((s) => s.token);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [universe, setUniverse] = useState("nifty50");
  const [minScore, setMinScore] = useState(0);
  const [bias, setBias] = useState("");
  const [sector, setSector] = useState("");
  const [sectors, setSectors] = useState<string[]>([]);
  const [held, setHeld] = useState<Set<string>>(new Set());

  const loadHeld = useCallback(() => {
    if (token) api.portfolio(token).then((p) => setHeld(new Set((p.trades || []).map((t: any) => t.symbol)))).catch(() => {});
  }, [token]);

  // Fetch the FULL ranked universe (filters are applied client-side below, so a dropdown
  // change costs zero network calls). Depends only on `universe`. A run-token cancels stale
  // poll loops on unmount / universe change so we never spam /api/scan (mirrors loadPicks).
  const runTok = useRef(0);
  const run = useCallback(async () => {
    const myTok = ++runTok.current;
    const alive = () => myTok === runTok.current;
    setLoading(true); setScanning(false);
    let d = await api.scan({ universe }).catch(() => null);
    if (!alive()) return;
    setData(d);
    // A tier that isn't cached yet is scanned in the background — poll until results land.
    if (d?.scanning) {
      setScanning(true);
      const maxPolls = universe === "nifty500" ? 110 : universe === "nifty50" ? 18 : 60;
      for (let i = 0; i < maxPolls && alive(); i++) {
        await new Promise((r) => setTimeout(r, 4000));
        if (!alive()) return;
        d = await api.scan({ universe }).catch(() => null);
        if (!alive()) return;
        if (d && !d.scanning) { setData(d); break; }   // includes degraded (rate-limited) → stop
      }
      if (alive()) setScanning(false);
    }
    if (alive()) setLoading(false);
  }, [universe]);

  // Client-side filters over the fetched results — instant, no network call.
  const results = useMemo(() => {
    let rows = data?.results || [];
    if (minScore) rows = rows.filter((r: any) => r.score >= minScore);
    if (sector) rows = rows.filter((r: any) => (r.sector || "") === sector);
    if (bias === "valid") rows = rows.filter((r: any) => r.plan);
    else if (bias === "bullish") rows = rows.filter((r: any) => /up/i.test(r.trend || ""));
    return rows;
  }, [data, minScore, sector, bias]);

  useEffect(() => { api.sectors().then((r) => setSectors(Object.keys(r.sectors))).catch(() => {}); }, []);
  useEffect(() => { run(); return () => { runTok.current++; }; }, [run]);   // refetch on universe change; cancel stale polls
  useEffect(() => { loadHeld(); }, [loadHeld]);

  const selCls = "rounded-lg border border-border bg-background px-3 py-2 text-sm";

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Radar className="text-primary" size={18} />
        <span>Screening the <span className="font-medium text-foreground">{UNIVERSES.find((u) => u.v === universe)?.label}</span> — <span className="font-medium text-foreground">{data ? results.length : "…"}</span> stocks ranked for swing setups</span>
      </div>

      <RegimeBanner regime={data?.regime}
        note={data?.regime === "bull" ? "Bullish regime — screening for trend-following setups."
          : data?.regime === "bear" ? "Bearish regime — capital-preservation mode." : undefined} />

      <Card className="flex flex-wrap items-end gap-3 p-4">
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">Universe
          <select className={selCls} value={universe} onChange={(e) => setUniverse(e.target.value)}>
            {UNIVERSES.map((u) => <option key={u.v} value={u.v}>{u.label}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">Min AI score
          <select className={selCls} value={minScore} onChange={(e) => setMinScore(Number(e.target.value))}>
            {MIN_SCORES.map((o) => <option key={o.v} value={o.v}>{o.label}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">Regime bias
          <select className={selCls} value={bias} onChange={(e) => setBias(e.target.value)}>
            {BIAS.map((o) => <option key={o.v} value={o.v}>{o.label}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">Sector
          <select className={selCls} value={sector} onChange={(e) => setSector(e.target.value)}>
            <option value="">All sectors</option>
            {sectors.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <Button onClick={run} className="ml-auto"><Radar size={15} className="mr-1.5" /> Run scan</Button>
      </Card>

      {loading && scanning ? (
        <Card className="flex flex-col items-center gap-3 py-14 text-center">
          <div className="h-9 w-9 animate-spin rounded-full border-2 border-muted border-t-primary" />
          <div className="text-sm font-medium">Scanning the {UNIVERSES.find((u) => u.v === universe)?.label}…</div>
          <div className="max-w-md text-xs text-muted-foreground">
            Running the deterministic screener across {UNIVERSES.find((u) => u.v === universe)?.n} NSE stocks on live prices.
            {universe === "nifty500" ? " The full scan takes a few minutes — smaller universes finish faster." : " This takes a moment."}
          </div>
        </Card>
      ) : loading ? (
        <div className="space-y-2">{[0, 1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-12" />)}</div>
      ) : (
        <Card className="overflow-hidden p-0">
          <div className="hidden grid-cols-[1.3fr_0.8fr_1.1fr_0.8fr_0.9fr_0.7fr_auto] gap-3 border-b border-border px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground sm:grid">
            <div>Symbol</div><div>Price</div><div>Quant score</div><div>Rel str</div><div>Trend</div><div>Vol</div><div className="text-right">Action</div>
          </div>
          <div className="divide-y divide-border">
            {results.map((r: any) => (
              <div key={r.symbol} className="grid grid-cols-2 items-center gap-3 px-4 py-3 text-sm sm:grid-cols-[1.3fr_0.8fr_1.1fr_0.8fr_0.9fr_0.7fr_auto]">
                <div>
                  <div className="font-semibold">{r.symbol}</div>
                  <div className="text-xs text-muted-foreground">{r.sector || "—"}</div>
                </div>
                <div className="tabular-nums">₹{r.price}</div>
                <div className="flex items-center gap-2">
                  <span className={`w-8 font-bold tabular-nums ${r.score >= 65 ? "text-success" : r.score < 45 ? "text-destructive" : ""}`}>{r.score}</span>
                  <div className="hidden h-1.5 flex-1 overflow-hidden rounded-full bg-muted sm:block">
                    <div className={`h-full rounded-full ${r.score >= 65 ? "bg-success" : r.score < 45 ? "bg-destructive" : "bg-primary"}`} style={{ width: `${Math.min(100, r.score)}%` }} />
                  </div>
                </div>
                <div className={`tabular-nums ${r.rel_strength >= 0 ? "text-success" : "text-destructive"}`}>
                  {r.rel_strength >= 0 ? "+" : ""}{r.rel_strength}
                </div>
                <div><span className={`rounded-full px-2 py-0.5 text-xs font-medium ${trendCls(r.trend)}`}>{r.trend}</span></div>
                <div className="tabular-nums text-muted-foreground">{r.vol_ratio}x</div>
                <div className="flex items-center justify-end gap-2">
                  {held.has(r.symbol) ? (
                    <span className="rounded-full bg-primary/15 px-2 py-0.5 text-xs text-primary">● Holding</span>
                  ) : r.plan ? (
                    <BuyButton symbol={r.symbol} plan={r.plan} token={token} onDone={loadHeld} />
                  ) : (
                    <span title="Strong stock, but no clean entry right now (over-extended / no valid stop). Wait for a pullback."
                      className="rounded-full bg-warning/15 px-2 py-0.5 text-xs font-medium text-warning">Watchlist</span>
                  )}
                  <Link href={`/${locale}/analyze?symbol=${r.symbol}`}>
                    <Button size="sm" variant="ghost"><ArrowUpRight size={14} /></Button>
                  </Link>
                </div>
              </div>
            ))}
            {!results.length && (
              <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                {data?.degraded
                  ? "Live scan is busy (data provider rate-limited). Showing nothing right now — please run the scan again in a few minutes."
                  : !data?.results?.length ? "No scan data yet for this universe — try Run scan." : "No stocks match these filters."}
              </div>
            )}
          </div>
        </Card>
      )}
      <p className="text-xs text-muted-foreground">Deterministic technical screening over {results.length} NIFTY 500 stocks. <b className="text-foreground">Quant score</b> ranks strength; a <b className="text-foreground">Paper trade</b> button means a clean entry exists now (R:R ≥ 2). <span className="text-warning">Watchlist</span> = strong but wait for a setup. Educational, not advice.</p>
    </div>
  );
}

export default function ScanPage() {
  return <DashboardShell><ScanInner /></DashboardShell>;
}
