"use client";
// Trade journal + post-trade review (Layer 2 — the retention engine, blueprint/00).
// List trades, close open ones with an exit price + reason, and see honest behavioural
// insights (discipline score, "winners exited early", "stops respected").
import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { DashboardShell } from "../../../components/DashboardShell";

function JournalInner() {
  const t = useTranslations();
  const token = useAuth((s) => s.token);
  const [trades, setTrades] = useState<any[]>([]);
  const [review, setReview] = useState<any>(null);
  const [exit, setExit] = useState<Record<string, { price: string; reason: string }>>({});
  const [closing, setClosing] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    api.trades(token).then((r) => setTrades(r.trades)).catch(() => {});
    api.journalReview(token).then(setReview).catch(() => {});
  }, [token]);
  useEffect(() => { load(); }, [load]);

  async function close(tr: any) {
    if (!token) return;
    const px = Number(exit[tr.id]?.price);
    if (!px) return;
    setClosing(tr.id);
    try { await api.paperClose(token, tr.id, px, exit[tr.id]?.reason); load(); }
    finally { setClosing(null); }
  }

  const badge = (s: string) => {
    const map: Record<string, string> = {
      open: "bg-muted text-foreground", closed_profit: "bg-success/15 text-success",
      closed_loss: "bg-destructive/15 text-destructive", scratch: "bg-warning/15 text-warning",
    };
    const label: Record<string, string> = {
      open: t("journal.open"), closed_profit: t("journal.win"), closed_loss: t("journal.loss"), scratch: t("journal.scratch"),
    };
    return <span className={`rounded-full px-2 py-0.5 text-xs ${map[s] || "bg-muted"}`}>{label[s] || s}</span>;
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold tracking-tight">{t("journal.title")}</h1>
      {/* Review */}
      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("journal.review")}</h2>
          {review?.closed > 0 ? (
            <Card className="p-5">
              <div className="flex items-baseline gap-3">
                <div className="text-3xl font-bold">{review.discipline_score}</div>
                <div className="text-sm text-muted-foreground">/ 100 · {t("journal.discipline")}</div>
              </div>
              <ul className="mt-3 space-y-1 text-sm">
                {review.insights.map((ins: any) => (
                  <li key={ins.key} className={ins.good ? "text-success" : "text-destructive"}>
                    {ins.good ? "✓" : "•"} {ins.text}
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-muted-foreground">{review.note}</p>
            </Card>
          ) : <Card className="p-5 text-sm text-muted-foreground">{t("journal.noReview")}</Card>}
        </div>

      {/* Trades */}
      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("journal.title")}</h2>
          {trades.length === 0 ? (
            <Card className="p-5 text-sm text-muted-foreground">{t("journal.noTrades")}</Card>
          ) : (
            <div className="space-y-3">
              {trades.map((tr) => (
                <Card key={tr.id} className="p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{tr.symbol}</span>{badge(tr.status)}
                      <span className="text-xs text-muted-foreground">{tr.qty} @ ₹{tr.entry} · {tr.entry_date}</span>
                    </div>
                    {tr.status !== "open" && (
                      <div className="text-sm">
                        <span className={tr.r_multiple >= 0 ? "text-success" : "text-destructive"}>
                          {tr.r_multiple >= 0 ? "+" : ""}{tr.r_multiple}R · ₹{tr.pnl_inr}
                        </span>
                      </div>
                    )}
                  </div>
                  {tr.entry_reason && <p className="mt-1 text-xs text-muted-foreground">📝 {tr.entry_reason}</p>}
                  {tr.status === "open" && (
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <input type="number" placeholder={t("journal.exitPrice")}
                        value={exit[tr.id]?.price || ""}
                        onChange={(e) => setExit({ ...exit, [tr.id]: { ...exit[tr.id], price: e.target.value } })}
                        className="w-28 rounded-md border border-border bg-transparent px-2 py-1 text-sm" />
                      <input placeholder={t("journal.reason")}
                        value={exit[tr.id]?.reason || ""}
                        onChange={(e) => setExit({ ...exit, [tr.id]: { ...exit[tr.id], reason: e.target.value } })}
                        className="min-w-40 flex-1 rounded-md border border-border bg-transparent px-2 py-1 text-sm" />
                      <Button size="sm" disabled={closing === tr.id} onClick={() => close(tr)}>
                        {closing === tr.id ? t("journal.closing") : t("journal.close")}
                      </Button>
                    </div>
                  )}
                  {tr.exit_reason && <p className="mt-1 text-xs text-muted-foreground">↳ {tr.exit_reason}</p>}
                </Card>
              ))}
            </div>
          )}
      </div>
    </div>
  );
}

export default function JournalPage() {
  return <DashboardShell><JournalInner /></DashboardShell>;
}
