"use client";
// Analyze any stock — auth-gated. Leads with a clear swing-trade verdict, then the full
// deterministic parameter breakdown. Accepts ?symbol= (deep-link from the scanner).
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { CheckCircle2, AlertTriangle, XCircle, Search } from "lucide-react";
import { api } from "@swingai/api-client";
import { Card, Button, StockAnalysisView, type StockAnalysisData } from "@swingai/ui";
import { DashboardShell } from "../../../components/DashboardShell";

function Verdict({ data }: { data: StockAnalysisData }) {
  const valid = data.swing_screen.meets_all_conditions;
  const score = data.swing_screen.score;
  const v = valid
    ? { Icon: CheckCircle2, label: "Valid swing setup", note: "All knockout conditions pass — a clean entry exists with R:R ≥ 2.", cls: "from-success/20 to-success/5 border-success/30 text-success" }
    : score >= 50
      ? { Icon: AlertTriangle, label: "On the watchlist — wait", note: "Strong stock, but not a clean swing entry right now. Wait for the setup.", cls: "from-warning/20 to-warning/5 border-warning/30 text-warning" }
      : { Icon: XCircle, label: "Avoid for now", note: "Doesn't meet the swing criteria today.", cls: "from-destructive/20 to-destructive/5 border-destructive/30 text-destructive" };
  return (
    <div className={`flex items-center gap-4 rounded-2xl border bg-gradient-to-r p-5 ${v.cls}`}>
      <v.Icon size={32} />
      <div className="flex-1">
        <div className="text-lg font-bold">{v.label}</div>
        <div className="text-sm opacity-80">{v.note}</div>
      </div>
      <div className="text-right">
        <div className="text-3xl font-bold tabular-nums">{score}</div>
        <div className="text-xs uppercase opacity-70">score / 100</div>
      </div>
    </div>
  );
}

function AnalyzeInner() {
  const t = useTranslations();
  const initial = useSearchParams().get("symbol") || "";
  const [symbol, setSymbol] = useState(initial || "HAL");
  const [data, setData] = useState<StockAnalysisData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = useCallback(async (sym: string) => {
    if (!sym.trim()) return;
    setBusy(true); setErr(null); setData(null);
    try { setData(await api.stockAnalysis(sym.trim())); }
    catch { setErr(t("analyze.error")); }
    finally { setBusy(false); }
  }, [t]);

  // deep-link: auto-run when arriving with ?symbol=
  useEffect(() => { if (initial) run(initial); }, [initial, run]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">{t("analyze.title")}</h1>
      <form onSubmit={(e) => { e.preventDefault(); run(symbol); }} className="flex gap-2">
        <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder={t("analyze.placeholder")}
          className="flex-1 rounded-lg border border-border bg-background/60 px-4 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20" />
        <Button type="submit" disabled={busy}><Search size={15} className="mr-1.5" />{busy ? t("analyze.analyzing") : t("analyze.button")}</Button>
      </form>
      {err && <Card className="p-5 text-sm text-destructive">{err}</Card>}
      {data && (
        <div className="space-y-6">
          <Verdict data={data} />
          <StockAnalysisView data={data} />
        </div>
      )}
    </div>
  );
}

export default function AnalyzePage() {
  return <DashboardShell><AnalyzeInner /></DashboardShell>;
}
