"use client";
// Analyze any stock — auth-gated. Data from /api/stocks/{symbol}.
import { useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@swingai/api-client";
import { Card, Button, StockAnalysisView, type StockAnalysisData } from "@swingai/ui";
import { DashboardShell } from "../../../components/DashboardShell";

function AnalyzeInner() {
  const t = useTranslations();
  const [symbol, setSymbol] = useState("HAL");
  const [data, setData] = useState<StockAnalysisData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(e?: React.FormEvent) {
    e?.preventDefault();
    setBusy(true); setErr(null); setData(null);
    try {
      setData(await api.stockAnalysis(symbol.trim()));
    } catch {
      setErr(t("analyze.error"));
    } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">{t("analyze.title")}</h1>
      <form onSubmit={run} className="flex gap-2">
        <input value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder={t("analyze.placeholder")}
          className="flex-1 rounded-lg border border-border bg-transparent px-4 py-2.5 text-sm" />
        <Button type="submit" disabled={busy}>{busy ? t("analyze.analyzing") : t("analyze.button")}</Button>
      </form>
      {err && <Card className="p-5 text-sm text-destructive">{err}</Card>}
      {data && <StockAnalysisView data={data} />}
    </div>
  );
}

export default function AnalyzePage() {
  return <DashboardShell><AnalyzeInner /></DashboardShell>;
}
