"use client";
// Analyze any stock — auth-gated, localized chrome. Data from /api/stocks/{symbol}.
import { useState } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@swingai/api-client";
import { Card, Button, ThemeToggle, LanguageSwitcher, StockAnalysisView, type StockAnalysisData } from "@swingai/ui";
import { RequireAuth } from "../../../components/RequireAuth";

function AnalyzeInner() {
  const t = useTranslations();
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
    } catch {
      setErr(t("analyze.error"));
    } finally { setBusy(false); }
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <Link href={`/${locale}/dashboard`} className="text-sm text-muted-foreground hover:underline">← {t("nav.dashboard")}</Link>
          <h1 className="font-semibold">{t("analyze.title")}</h1>
        </div>
        <div className="flex items-center gap-2"><LanguageSwitcher /><ThemeToggle /></div>
      </header>
      <section className="mx-auto max-w-3xl space-y-6 px-6 py-8">
        <form onSubmit={run} className="flex gap-2">
          <input value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder={t("analyze.placeholder")}
            className="flex-1 rounded-md border border-border bg-transparent px-3 py-2 text-sm" />
          <Button type="submit" disabled={busy}>{busy ? t("analyze.analyzing") : t("analyze.button")}</Button>
        </form>
        {err && <Card className="p-5 text-sm text-destructive">{err}</Card>}
        {data && <StockAnalysisView data={data} />}
      </section>
    </main>
  );
}

export default function AnalyzePage() {
  return <RequireAuth><AnalyzeInner /></RequireAuth>;
}
