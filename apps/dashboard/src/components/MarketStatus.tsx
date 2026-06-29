"use client";
// Market-status banner — shows whether the NSE is open right now, the NIFTY level + trend,
// and the regime. Refreshes on mount (every page load) and, while the market is open, polls
// every 60s so the level stays fresh. Honest when closed: shows the last close + date.
import { useCallback, useEffect, useState } from "react";
import { Activity, TrendingUp, TrendingDown, Minus, RefreshCw } from "lucide-react";
import { api, type MarketStatus as MS } from "@swingai/api-client";

const SESSION_LABEL: Record<string, string> = {
  open: "Market open", "pre-open": "Pre-open", closed: "Market closed",
};
const REGIME_LABEL: Record<string, string> = {
  bull: "Bullish — trades allowed", neutral: "Neutral — selective",
  bear: "Bearish — capital protection", unknown: "—",
};

export function MarketStatus() {
  const [ms, setMs] = useState<MS | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try { setMs(await api.marketStatus()); } catch { /* keep last */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 60_000); // refresh while mounted
    return () => clearInterval(id);
  }, [load]);

  if (loading && !ms) {
    return <div className="h-[68px] animate-pulse rounded-xl border border-border bg-card/40" />;
  }
  if (!ms) return null;

  const open = ms.is_open;
  const lvl = ms.index.level;
  // Color + arrow follow TODAY'S move (change vs previous close), not the regime — so a red day
  // shows red/down even when the regime is still bull (price above EMA20).
  const chg = ms.index.change_abs ?? ms.index.change_pct ?? 0;
  const dir = chg > 0 ? "up" : chg < 0 ? "down" : "flat";
  const TrendIcon = dir === "up" ? TrendingUp : dir === "down" ? TrendingDown : Minus;
  const trendCls = dir === "up" ? "text-success" : dir === "down" ? "text-destructive" : "text-muted-foreground";
  const sign = (n: number) => (n > 0 ? "+" : "");   // negatives already carry "−"

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card/60 px-4 py-3 backdrop-blur">
      <div className="flex items-center gap-3">
        <span className="relative flex h-2.5 w-2.5">
          {open && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />}
          <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${open ? "bg-success" : "bg-muted-foreground"}`} />
        </span>
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Activity size={15} className={open ? "text-success" : "text-muted-foreground"} />
            {SESSION_LABEL[ms.session] ?? ms.session}
            {!open && ms.index.as_of && <span className="text-xs font-normal text-muted-foreground">· as of {ms.index.as_of}</span>}
          </div>
          <div className="text-xs text-muted-foreground">{ms.server_time_ist}</div>
        </div>
      </div>

      <div className="flex items-center gap-5">
        <div className="text-right">
          <div className="text-xs text-muted-foreground">{ms.index.symbol}</div>
          <div className={`flex items-center justify-end gap-1 font-semibold tabular-nums ${trendCls}`}>
            <TrendIcon size={15} />
            {lvl != null ? lvl.toLocaleString("en-IN") : "—"}
            {(ms.index.change_abs != null || ms.index.change_pct != null) && (
              <span className="text-xs">
                ({ms.index.change_abs != null && <>{sign(ms.index.change_abs)}{ms.index.change_abs.toLocaleString("en-IN")} · </>}
                {ms.index.change_pct != null ? `${sign(ms.index.change_pct)}${ms.index.change_pct}%` : ""})
              </span>
            )}
          </div>
        </div>
        <div className="hidden text-right sm:block">
          <div className="text-xs text-muted-foreground">Regime</div>
          <div className="text-sm font-medium capitalize">{REGIME_LABEL[ms.regime] ?? ms.regime}</div>
        </div>
        <button onClick={load} aria-label="Refresh market status"
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
          <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
        </button>
      </div>
    </div>
  );
}
