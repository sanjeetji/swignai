"use client";
// NSE Scanner (blueprint/04) — rank the tradeable universe by deterministic score with
// trend / relative-strength / volume, and filter by score / sector / regime bias.
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Radar, ArrowUpRight } from "lucide-react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { DashboardShell } from "../../../components/DashboardShell";
import { RegimeBanner, Skeleton } from "../../../components/dashboard-ui";

const MIN_SCORES = [
  { v: 0, label: "Any score" }, { v: 50, label: "> 50" }, { v: 65, label: "> 65 (solid)" }, { v: 80, label: "> 80 (high conviction)" },
];
const BIAS = [
  { v: "", label: "All setups" }, { v: "valid", label: "Valid setups only" }, { v: "bullish", label: "Bullish trend only" },
];

function trendCls(t: string) {
  return t === "Strong Up" ? "bg-success/15 text-success" : t === "Up" ? "bg-success/10 text-success"
    : t === "Down" ? "bg-destructive/15 text-destructive" : "bg-muted text-muted-foreground";
}

function ScanInner() {
  const { locale } = useParams<{ locale: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [minScore, setMinScore] = useState(0);
  const [bias, setBias] = useState("");
  const [sector, setSector] = useState("");
  const [sectors, setSectors] = useState<string[]>([]);

  const run = useCallback(() => {
    setLoading(true);
    api.scan({ min_score: minScore || undefined, sector: sector || undefined, regime_bias: bias || undefined })
      .then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, [minScore, sector, bias]);

  useEffect(() => { api.sectors().then((r) => setSectors(Object.keys(r.sectors))).catch(() => {}); }, []);
  useEffect(() => { run(); }, [run]);

  const selCls = "rounded-lg border border-border bg-background px-3 py-2 text-sm";

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <Radar className="text-primary" size={22} />
        <h1 className="text-2xl font-bold tracking-tight">NSE Scanner</h1>
        <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">{data?.count ?? "…"} stocks</span>
      </div>

      <RegimeBanner regime={data?.regime}
        note={data?.regime === "bull" ? "Bullish regime confirmed — scanning for trend-following breakouts."
          : data?.regime === "bear" ? "Bearish regime — capital-preservation mode." : undefined} />

      <Card className="flex flex-wrap items-end gap-3 p-4">
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

      {loading ? (
        <div className="space-y-2">{[0, 1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-12" />)}</div>
      ) : (
        <Card className="overflow-hidden p-0">
          <div className="hidden grid-cols-[1.4fr_1.2fr_0.9fr_1fr_0.8fr_auto] gap-3 border-b border-border px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground sm:grid">
            <div>Symbol</div><div>AI score</div><div>Rel strength</div><div>Trend</div><div>Vol ratio</div><div className="text-right">Action</div>
          </div>
          <div className="divide-y divide-border">
            {data?.results?.map((r: any) => (
              <div key={r.symbol} className="grid grid-cols-2 items-center gap-3 px-4 py-3 text-sm sm:grid-cols-[1.4fr_1.2fr_0.9fr_1fr_0.8fr_auto]">
                <div>
                  <div className="font-semibold">{r.symbol}</div>
                  <div className="text-xs text-muted-foreground">{r.sector || "—"}</div>
                </div>
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
                <div className="text-right">
                  <Link href={`/${locale}/analyze?symbol=${r.symbol}`}>
                    <Button size="sm" variant="ghost">Analyze <ArrowUpRight size={13} className="ml-1" /></Button>
                  </Link>
                </div>
              </div>
            ))}
            {!data?.results?.length && <div className="px-4 py-8 text-center text-sm text-muted-foreground">No stocks match these filters.</div>}
          </div>
        </Card>
      )}
      <p className="text-xs text-muted-foreground">Deterministic technical screening over {data?.count ?? 0} NSE large/mid-caps — educational, not advice.</p>
    </div>
  );
}

export default function ScanPage() {
  return <DashboardShell><ScanInner /></DashboardShell>;
}
