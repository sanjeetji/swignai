"use client";
// Paper-trade widgets (blueprint/04): one-tap BuyButton (real price + plan) and a full
// PositionCard — live P&L/R, progress to target & stop, exit-at-market, and a trailing
// stop (move to breakeven / custom). Reused on Analyze, Scanner, Dashboard.
import { useState } from "react";
import { ShoppingCart, LogOut, MoveUp, Target, ShieldAlert } from "lucide-react";
import { api } from "@swingai/api-client";
import { Button } from "@swingai/ui";

export function BuyButton({ symbol, plan, token, onDone, size = "sm" }: {
  symbol: string; plan: any; token: string | null; onDone?: () => void; size?: "sm" | "default";
}) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  if (!plan) return <span className="text-xs text-muted-foreground">no setup</span>;

  async function buy() {
    if (!token) return;
    setBusy(true); setMsg(null);
    try {
      await api.paperBuy(token, {
        stock_symbol: symbol, entry_price: plan.entry, stop_loss: plan.stop,
        target: plan.target_1, quantity: plan.quantity, entry_reason: "paper trade",
      });
      setMsg({ ok: true, text: `Bought ${plan.quantity} @ ₹${plan.entry}` });
      onDone?.();
    } catch (e: any) {
      setMsg({ ok: false, text: String(e?.message || e).replace(/API \d+:/, "").slice(0, 70) });
    } finally { setBusy(false); }
  }

  return (
    <span className="inline-flex items-center gap-2">
      <Button size={size} disabled={busy} onClick={buy}><ShoppingCart size={14} className="mr-1" />{busy ? "Buying…" : "Paper trade"}</Button>
      {msg && <span className={`text-xs ${msg.ok ? "text-success" : "text-destructive"}`}>{msg.text}</span>}
    </span>
  );
}

function Bar({ pct, tone }: { pct: number; tone: string }) {
  return (
    <div className="h-1.5 overflow-hidden rounded-full bg-muted">
      <div className={`h-full rounded-full ${tone}`} style={{ width: `${Math.max(0, Math.min(100, pct))}%` }} />
    </div>
  );
}

export function PositionCard({ pos, token, onChange }: { pos: any; token: string | null; onChange?: () => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const cur = pos.current_price;
  const up = (pos.unrealized_inr ?? 0) >= 0;

  async function exit() {
    if (!token) return;
    setBusy("exit");
    try { await api.paperClose(token, pos.id, cur ?? pos.entry, "exited from analysis"); onChange?.(); }
    finally { setBusy(null); }
  }
  async function trail(newStop: number) {
    if (!token) return;
    setBusy("trail");
    try { await api.paperTrail(token, pos.id, newStop); onChange?.(); }
    catch { /* ignore (e.g. stop not above current) */ }
    finally { setBusy(null); }
  }

  return (
    <div className="rounded-2xl border border-primary/30 bg-primary/5 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-semibold">
          <span className="rounded-full bg-primary/15 px-2 py-0.5 text-xs text-primary">● Holding</span>
          {pos.symbol} · {pos.qty} @ ₹{pos.entry}
        </div>
        {cur != null && (
          <div className={`text-right ${up ? "text-success" : "text-destructive"}`}>
            <div className="text-lg font-bold tabular-nums">{up ? "+" : ""}₹{pos.unrealized_inr} ({pos.unrealized_pct}%)</div>
            <div className="text-xs">{pos.r_now}R · now ₹{cur}</div>
          </div>
        )}
      </div>

      {cur != null && (
        <div className="mt-4 space-y-2 text-xs">
          <div className="flex items-center justify-between text-muted-foreground"><span className="flex items-center gap-1"><Target size={12} /> To target ₹{pos.target}</span><span>{pos.pct_to_target}%</span></div>
          <Bar pct={pos.pct_to_target} tone="bg-success" />
          <div className="flex items-center justify-between text-muted-foreground"><span className="flex items-center gap-1"><ShieldAlert size={12} /> To stop ₹{pos.stop}{pos.breakeven ? " (breakeven)" : ""}</span><span>{pos.pct_to_stop}%</span></div>
          <Bar pct={pos.pct_to_stop} tone="bg-destructive" />
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button size="sm" variant="outline" disabled={busy === "exit"} onClick={exit}>
          <LogOut size={14} className="mr-1" />{busy === "exit" ? "Exiting…" : `Exit at ₹${cur ?? pos.entry}`}
        </Button>
        {cur != null && cur > pos.entry && !pos.breakeven && (
          <Button size="sm" variant="ghost" disabled={busy === "trail"} onClick={() => trail(pos.entry)}>
            <MoveUp size={14} className="mr-1" />Move stop to breakeven
          </Button>
        )}
        {cur != null && cur > pos.stop && (
          <Button size="sm" variant="ghost" disabled={busy === "trail"} onClick={() => trail(Math.max(pos.entry, Number((cur * 0.97).toFixed(2))))}>
            <MoveUp size={14} className="mr-1" />Trail stop (-3%)
          </Button>
        )}
      </div>
      <p className="mt-2 text-xs text-muted-foreground">Trailing only ratchets the stop up — it never increases your risk.</p>
    </div>
  );
}
