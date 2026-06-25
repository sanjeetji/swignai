"use client";
// Enforced position-size calculator → paper-trade buy (Layer 1, blueprint/04 §5).
// Size is derived from capital × risk% ÷ (entry-stop); the same guards the API enforces
// are previewed here (R:R ≥ 2, ≤20% concentration). On submit it calls the real API.
import { useMemo, useState } from "react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";

const RISK_PCT = 1;
const MIN_RR = 2;
const MAX_POS_PCT = 20;

export function RiskCalculator({ capital, token, onTraded }: {
  capital: number; token: string | null; onTraded?: () => void;
}) {
  const [symbol, setSymbol] = useState("HAL");
  const [entry, setEntry] = useState(100);
  const [stop, setStop] = useState(96);
  const [target, setTarget] = useState(108);
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const r = useMemo(() => {
    const risk = entry - stop;
    if (risk <= 0) return { valid: false, reason: "Stop must be below entry" } as const;
    const rr = (target - entry) / risk;
    const qty = Math.floor((capital * (RISK_PCT / 100)) / risk);
    const size = qty * entry;
    const concentration = (size / capital) * 100;
    const reasons: string[] = [];
    if (rr < MIN_RR) reasons.push(`R:R ${rr.toFixed(2)} < ${MIN_RR}`);
    if (concentration > MAX_POS_PCT) reasons.push(`Concentration ${concentration.toFixed(0)}% > ${MAX_POS_PCT}%`);
    if (qty <= 0) reasons.push("Quantity is 0 for this risk");
    return { valid: reasons.length === 0, reason: reasons.join(" · "), rr, qty, size, concentration, risk };
  }, [entry, stop, target, capital]);

  async function buy() {
    if (!token || !("qty" in r) || !r.valid) return;
    setBusy(true); setMsg(null);
    try {
      await api.paperBuy(token, {
        stock_symbol: symbol, entry_price: entry, stop_loss: stop,
        target, quantity: r.qty, entry_reason: reason || undefined,
      });
      setMsg({ ok: true, text: `Paper trade opened: ${r.qty} ${symbol}` });
      onTraded?.();
    } catch (e: any) {
      setMsg({ ok: false, text: String(e?.message || e).slice(0, 140) });
    } finally { setBusy(false); }
  }

  const Field = ({ label, value, set, type = "number" }: any) => (
    <label className="text-sm">
      <span className="text-muted-foreground">{label}</span>
      <input type={type} value={value} onChange={(e) => set(type === "number" ? Number(e.target.value) : e.target.value)}
        className="mt-1 w-full rounded-md border border-border bg-transparent px-2 py-1" />
    </label>
  );

  return (
    <Card className="p-5">
      <h3 className="font-semibold">Risk calculator → paper trade</h3>
      <p className="text-xs text-muted-foreground">1% risk of ₹{capital.toLocaleString("en-IN")} · enforced</p>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Field label="Symbol" value={symbol} set={setSymbol} type="text" />
        <Field label="Entry ₹" value={entry} set={setEntry} />
        <Field label="Stop ₹" value={stop} set={setStop} />
        <Field label="Target ₹" value={target} set={setTarget} />
      </div>
      <label className="mt-3 block text-sm">
        <span className="text-muted-foreground">Why this trade? (journal)</span>
        <input value={reason} onChange={(e) => setReason(e.target.value)}
          className="mt-1 w-full rounded-md border border-border bg-transparent px-2 py-1"
          placeholder="e.g. breakout above 20-day high on volume" />
      </label>
      <div className="mt-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <div>Qty <b>{"qty" in r ? r.qty : "—"}</b></div>
        <div>Size <b>₹{"size" in r && r.size ? Math.round(r.size).toLocaleString("en-IN") : "—"}</b></div>
        <div>R:R <b>{"rr" in r && r.rr ? r.rr.toFixed(2) : "—"}</b></div>
        <div>Risk/sh <b>₹{"risk" in r ? r.risk : "—"}</b></div>
      </div>
      <div className={`mt-3 text-sm ${r.valid ? "text-success" : "text-destructive"}`}>
        {r.valid ? "✓ Passes risk guards" : `✗ ${r.reason}`}
      </div>
      {msg && <div className={`mt-2 text-sm ${msg.ok ? "text-success" : "text-destructive"}`}>{msg.text}</div>}
      <Button className="mt-4" disabled={!r.valid || busy || !token} onClick={buy}>
        {busy ? "Placing…" : "Paper trade this"}
      </Button>
    </Card>
  );
}
