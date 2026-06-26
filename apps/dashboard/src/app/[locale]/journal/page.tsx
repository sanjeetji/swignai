"use client";
// Trade journal + post-trade review (Layer 2 — the retention engine, blueprint/00).
// Rich detail for open positions (entry/stop/T1-T3, live price, unrealized P&L, R-now,
// progress to target) with an exit control, and a full post-trade review of closed trades
// with a P&L summary + filters. Shows worked examples when a section is empty.
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { Search, TrendingUp, TrendingDown } from "lucide-react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { DashboardShell } from "../../../components/DashboardShell";

const inr = (n: number | null | undefined) =>
  n == null ? "—" : `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
const signed = (n: number | null | undefined, suffix = "") =>
  n == null ? "—" : `${n >= 0 ? "+" : ""}${n}${suffix}`;

function StatusBadge({ s }: { s: string }) {
  const map: Record<string, string> = {
    open: "bg-primary/15 text-primary", closed_profit: "bg-success/15 text-success",
    closed_loss: "bg-destructive/15 text-destructive", scratch: "bg-warning/15 text-warning",
  };
  const label: Record<string, string> = {
    open: "Open", closed_profit: "Win", closed_loss: "Loss", scratch: "Scratch",
  };
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${map[s] || "bg-muted"}`}>{label[s] || s}</span>;
}

// One key/value cell in the detail grid.
function Cell({ label, value, cls = "" }: { label: string; value: React.ReactNode; cls?: string }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={`tabular-nums font-medium ${cls}`}>{value}</div>
    </div>
  );
}

// Rich card for an OPEN position.
function OpenCard({ tr, exit, setExit, onClose, closing }: any) {
  const e = exit[tr.id] || {};
  const up = (tr.r_now ?? 0) >= 0;
  return (
    <Card className="space-y-3 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-base font-semibold">{tr.symbol}</span><StatusBadge s={tr.status} />
          <span className="text-xs text-muted-foreground">entered {tr.entry_at ? new Date(tr.entry_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : tr.entry_date}</span>
        </div>
        {tr.current_price != null && (
          <div className="text-right">
            <div className="flex items-center justify-end gap-1 font-semibold tabular-nums">
              {up ? <TrendingUp size={14} className="text-success" /> : <TrendingDown size={14} className="text-destructive" />}
              {inr(tr.current_price)}
            </div>
            <div className={`text-xs ${up ? "text-success" : "text-destructive"}`}>
              {signed(tr.unrealized_inr)} ({signed(tr.unrealized_pct, "%")}) · {signed(tr.r_now, "R")}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3 text-sm sm:grid-cols-6">
        <Cell label="Entry" value={inr(tr.entry)} />
        <Cell label="Qty" value={tr.qty} />
        <Cell label="Size" value={inr(tr.position_size)} />
        <Cell label="Stop" value={inr(tr.stop)} cls="text-destructive" />
        <Cell label="T1 · 2R" value={inr(tr.target_1)} cls="text-success" />
        <Cell label="T2 · 3R" value={inr(tr.target_2)} cls="text-success" />
      </div>

      {tr.pct_to_target != null && (
        <div>
          <div className="mb-1 flex justify-between text-[11px] text-muted-foreground"><span>Stop</span><span>{tr.pct_to_target}% to T1</span><span>Target</span></div>
          <div className="relative h-1.5 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-success" style={{ width: `${tr.pct_to_target}%` }} />
          </div>
        </div>
      )}

      {tr.entry_reason && <p className="text-xs text-muted-foreground">📝 {tr.entry_reason}</p>}

      <div className="flex flex-wrap items-center gap-2 border-t border-border pt-3">
        <input type="number" placeholder={`Exit price (T1 ${inr(tr.target_1)})`}
          value={e.price ?? ""} onChange={(ev) => setExit({ ...exit, [tr.id]: { ...e, price: ev.target.value } })}
          className="w-40 rounded-md border border-border bg-transparent px-2 py-1 text-sm" />
        <input placeholder="Exit reason (e.g. hit target, trailed stop)"
          value={e.reason ?? ""} onChange={(ev) => setExit({ ...exit, [tr.id]: { ...e, reason: ev.target.value } })}
          className="min-w-44 flex-1 rounded-md border border-border bg-transparent px-2 py-1 text-sm" />
        <Button size="sm" variant="ghost" onClick={() => setExit({ ...exit, [tr.id]: { ...e, price: String(tr.target_1 ?? tr.target) } })}>Use T1</Button>
        <Button size="sm" disabled={closing === tr.id || !e.price} onClick={() => onClose(tr)}>
          {closing === tr.id ? "Closing…" : "Close trade"}
        </Button>
      </div>
    </Card>
  );
}

// Rich card for a CLOSED position (post-trade review).
function ClosedCard({ tr }: any) {
  const win = (tr.r_multiple ?? 0) >= 0;
  return (
    <Card className="space-y-2 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold">{tr.symbol}</span><StatusBadge s={tr.status} />
          <span className="text-xs text-muted-foreground">held {tr.hold_days ?? "—"}d</span>
        </div>
        <div className={`text-right text-sm font-semibold ${win ? "text-success" : "text-destructive"}`}>
          {signed(tr.r_multiple, "R")} · {signed(tr.pnl_inr)} ({signed(tr.pnl_percent, "%")})
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3 text-sm sm:grid-cols-5">
        <Cell label="Entry" value={inr(tr.entry)} />
        <Cell label="Exit" value={inr(tr.exit)} />
        <Cell label="Qty" value={tr.qty} />
        <Cell label="Entered" value={<span className="text-xs">{tr.entry_date}</span>} />
        <Cell label="Exited" value={<span className="text-xs">{tr.exit_date}</span>} />
      </div>
      {tr.entry_reason && <p className="text-xs text-muted-foreground">📝 {tr.entry_reason}</p>}
      {tr.exit_reason && <p className="text-xs text-muted-foreground">↳ {tr.exit_reason}</p>}
    </Card>
  );
}

// Worked examples shown when a section is empty, so the user sees what they'll get.
const EXAMPLE_OPEN = {
  id: "ex", symbol: "TATASTEEL", status: "open", entry: 165.4, stop: 158.2, target: 179.8,
  target_1: 179.8, target_2: 187, qty: 60, position_size: 9924, entry_at: new Date().toISOString(),
  entry_date: "—", current_price: 171.2, unrealized_inr: 348, unrealized_pct: 3.5, r_now: 0.8,
  pct_to_target: 40, entry_reason: "Breakout above base with rising volume.",
};
const EXAMPLE_CLOSED = {
  id: "exc", symbol: "INFY", status: "closed_profit", entry: 1480, exit: 1560, qty: 30,
  r_multiple: 2.0, pnl_inr: 2400, pnl_percent: 5.4, hold_days: 8, entry_date: "—", exit_date: "—",
  entry_reason: "Pullback to 20-EMA in an uptrend.", exit_reason: "Hit target 1 (2R).",
};

function Example({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative">
      <div className="pointer-events-none opacity-50 blur-[0.3px]">{children}</div>
      <span className="absolute right-3 top-3 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Example</span>
    </div>
  );
}

function JournalInner() {
  const t = useTranslations();
  const token = useAuth((s) => s.token);
  const [trades, setTrades] = useState<any[]>([]);
  const [review, setReview] = useState<any>(null);
  const [exit, setExit] = useState<Record<string, { price: string; reason: string }>>({});
  const [closing, setClosing] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const load = useCallback(() => {
    if (!token) return;
    api.trades(token).then((r) => setTrades(r.trades || [])).catch(() => {});
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

  const filtered = useMemo(
    () => trades.filter((tr) => !q || tr.symbol.toLowerCase().includes(q.toLowerCase())),
    [trades, q]);
  const open = filtered.filter((tr) => tr.status === "open");
  const closed = filtered.filter((tr) => tr.status !== "open");

  // P&L summary (all trades, ignores the symbol filter so totals stay meaningful).
  const pnl = useMemo(() => {
    const c = trades.filter((tr) => tr.status !== "open");
    const realized = c.reduce((s, tr) => s + (tr.pnl_inr || 0), 0);
    const unreal = trades.filter((tr) => tr.status === "open").reduce((s, tr) => s + (tr.unrealized_inr || 0), 0);
    const wins = c.filter((tr) => (tr.r_multiple ?? 0) > 0).length;
    return { realized, unreal, wins, losses: c.length - wins, openCount: trades.length - c.length };
  }, [trades]);

  const SummaryCard = ({ label, value, cls = "" }: any) => (
    <Card className="p-4"><div className="text-xs text-muted-foreground">{label}</div>
      <div className={`mt-0.5 text-xl font-bold tabular-nums ${cls}`}>{value}</div></Card>
  );

  return (
    <div className="space-y-8">
      {/* P&L summary */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <SummaryCard label="Realized P&L" value={inr(pnl.realized)} cls={pnl.realized >= 0 ? "text-success" : "text-destructive"} />
        <SummaryCard label="Open P&L (unrealized)" value={inr(pnl.unreal)} cls={pnl.unreal >= 0 ? "text-success" : "text-destructive"} />
        <SummaryCard label="Open positions" value={pnl.openCount} />
        <SummaryCard label="Win / Loss" value={`${pnl.wins} / ${pnl.losses}`} />
      </div>

      {/* filter */}
      <div className="relative max-w-xs">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by stock…"
          className="w-full rounded-lg border border-border bg-background px-3 py-2 pl-9 text-sm" />
      </div>

      {/* Open positions */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Open positions ({open.length})</h2>
        {open.length === 0 ? (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">No open paper trades. Buy a setup from the Dashboard or Scanner — it'll appear here with full detail like this:</p>
            <Example><OpenCard tr={EXAMPLE_OPEN} exit={{}} setExit={() => {}} onClose={() => {}} closing={null} /></Example>
          </div>
        ) : (
          <div className="space-y-3">{open.map((tr) => (
            <OpenCard key={tr.id} tr={tr} exit={exit} setExit={setExit} onClose={close} closing={closing} />
          ))}</div>
        )}
      </section>

      {/* Post-trade review */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("journal.review")}</h2>
        {review?.closed > 0 && (
          <Card className="mb-3 p-5">
            <div className="flex items-baseline gap-3">
              <div className="text-3xl font-bold">{review.discipline_score}</div>
              <div className="text-sm text-muted-foreground">/ 100 · {t("journal.discipline")}</div>
            </div>
            <ul className="mt-3 space-y-1 text-sm">
              {review.insights?.map((ins: any) => (
                <li key={ins.key} className={ins.good ? "text-success" : "text-destructive"}>{ins.good ? "✓" : "•"} {ins.text}</li>
              ))}
            </ul>
            {review.note && <p className="mt-3 text-xs text-muted-foreground">{review.note}</p>}
          </Card>
        )}
        {closed.length === 0 ? (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">No closed trades yet. When you close a position, it lands here with entry/exit, hold time, reason and the result — like this:</p>
            <Example><ClosedCard tr={EXAMPLE_CLOSED} /></Example>
          </div>
        ) : (
          <div className="space-y-3">{closed.map((tr) => <ClosedCard key={tr.id} tr={tr} />)}</div>
        )}
      </section>
    </div>
  );
}

export default function JournalPage() {
  return <DashboardShell><JournalInner /></DashboardShell>;
}
