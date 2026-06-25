"use client";
// Analyze any stock — on-demand deterministic technical analysis (blueprint/08).
// Reuses the shared StockAnalysisView; data from /api/stocks/{symbol} (real prices).
import { useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@swingai/api-client";
import { Card, Button, ThemeToggle, StockAnalysisView, type StockAnalysisData } from "@swingai/ui";
import Link from "next/link";

export default function AnalyzePage() {
  const { locale } = useParams<{ locale: string }>();
  const [symbol, setSymbol] = useState("HAL");
  const [data, setData] = useState<StockAnalysisData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(e?: React.FormEvent) {
    e?.preventDefault();
    setBusy(true); setErr(null); setData(null);
    try {
      setData(await api.stockAnalysis(symbol.trim()));
    } catch (e: any) {
      setErr("No analysis available for that symbol (need enough price history).");
    } finally { setBusy(false); }
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <Link href={`/${locale}/dashboard`} className="text-sm text-muted-foreground hover:underline">← Dashboard</Link>
          <h1 className="font-semibold">Analyze a stock</h1>
        </div>
        <ThemeToggle />
      </header>
      <section className="mx-auto max-w-3xl space-y-6 px-6 py-8">
        <form onSubmit={run} className="flex gap-2">
          <input value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="e.g. HAL, INFY, SBIN"
            className="flex-1 rounded-md border border-border bg-transparent px-3 py-2 text-sm" />
          <Button type="submit" disabled={busy}>{busy ? "Analyzing…" : "Analyze"}</Button>
        </form>
        {err && <Card className="p-5 text-sm text-destructive">{err}</Card>}
        {data && <StockAnalysisView data={data} />}
      </section>
    </main>
  );
}
