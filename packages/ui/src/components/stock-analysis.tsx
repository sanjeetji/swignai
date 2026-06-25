// Presentational stock-analysis view — renders the deterministic math from
// GET /api/stocks/{symbol}. No hooks → usable in both server (marketing) and
// client (dashboard) components. Educational framing (blueprint/09).
import { Card } from "./card";

type Analysis = Record<string, number | boolean | null>;

export interface StockAnalysisData {
  symbol: string;
  as_of: string;
  analysis: Analysis;
  swing_screen: {
    meets_all_conditions: boolean;
    conditions: Record<string, boolean>;
    score: number;
    score_breakdown: Record<string, number>;
  };
  trade_plan: null | { entry: number; stop: number; target_1: number; target_2: number; rr_ratio: number };
  disclaimer: string;
}

const ROWS: [string, string][] = [
  ["close", "Close ₹"], ["ema20", "EMA 20"], ["ema50", "EMA 50"], ["ema100", "EMA 100"],
  ["ema200", "EMA 200"], ["rsi", "RSI(14)"], ["macd", "MACD"], ["adx", "ADX (trend)"],
  ["stoch_k", "Stoch %K"], ["bb_pct_b", "Bollinger %b"], ["atr_pct", "ATR %"],
  ["vol_ratio", "Vol vs 20d"], ["turnover_cr", "Turnover ₹cr"], ["rel_strength", "RS vs NIFTY"],
  ["pct_from_52w_high", "% from 52w high"], ["pct_from_52w_low", "% from 52w low"],
  ["dist_to_breakout_pct", "% to breakout"],
];

function fmt(v: number | boolean | null) {
  if (typeof v === "boolean") return v ? "Yes" : "No";
  return v === null || v === undefined ? "—" : String(v);
}

export function StockAnalysisView({ data }: { data: StockAnalysisData }) {
  const a = data.analysis;
  const cond = data.swing_screen.conditions || {};
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-2xl font-bold">{data.symbol}</h1>
        <span className="text-sm text-muted-foreground">as of {data.as_of}</span>
      </div>

      <Card className="p-5">
        <h2 className="mb-3 text-sm font-semibold text-muted-foreground">Technical analysis (computed from real prices)</h2>
        <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
          {ROWS.map(([k, label]) => (
            <div key={k} className="flex justify-between border-b border-border/50 py-1">
              <span className="text-muted-foreground">{label}</span><span className="font-medium">{fmt(a[k])}</span>
            </div>
          ))}
          <div className="flex justify-between border-b border-border/50 py-1">
            <span className="text-muted-foreground">Trend stack 20&gt;50&gt;200</span>
            <span className="font-medium">{fmt(a["trend_stack_bullish"])}</span>
          </div>
          <div className="flex justify-between border-b border-border/50 py-1">
            <span className="text-muted-foreground">OBV accumulating</span>
            <span className="font-medium">{fmt(a["obv_accumulating"])}</span>
          </div>
        </div>
      </Card>

      <Card className="p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-muted-foreground">Swing setup screen</h2>
          <span className={`text-sm font-semibold ${data.swing_screen.meets_all_conditions ? "text-success" : "text-destructive"}`}>
            {data.swing_screen.meets_all_conditions ? "✓ Meets all conditions" : "Does not meet all conditions"} · score {data.swing_screen.score}
          </span>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(cond).map(([k, ok]) => (
            <span key={k} className={`rounded-full px-2 py-0.5 text-xs ${ok ? "bg-success/15 text-success" : "bg-destructive/15 text-destructive"}`}>
              {k.replace(/_/g, " ")} {ok ? "✓" : "✗"}
            </span>
          ))}
        </div>
        {data.trade_plan && (
          <div className="mt-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-5">
            <div>Entry ₹{data.trade_plan.entry}</div>
            <div>Stop ₹{data.trade_plan.stop}</div>
            <div>T1 ₹{data.trade_plan.target_1}</div>
            <div>T2 ₹{data.trade_plan.target_2}</div>
            <div>R:R {data.trade_plan.rr_ratio}</div>
          </div>
        )}
      </Card>

      <p className="text-xs text-muted-foreground">{data.disclaimer}</p>
    </div>
  );
}
