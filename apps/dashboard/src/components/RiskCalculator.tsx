"use client";
// Enforced position-size calculator — Layer 1, the moat (blueprint/04 §5, blueprint/00).
// The user never sizes by gut: size is derived from capital × risk% ÷ (entry-stop),
// and the same guards the API enforces are previewed here (R:R ≥ 2, ≤20% concentration).
import { useMemo, useState } from "react";
import { Card, Button } from "@swingai/ui";

const RISK_PCT = 1;          // % of capital per trade (matches backend default)
const MIN_RR = 2;
const MAX_POS_PCT = 20;

export function RiskCalculator({ capital }: { capital: number }) {
  const [entry, setEntry] = useState(100);
  const [stop, setStop] = useState(96);
  const [target, setTarget] = useState(108);

  const r = useMemo(() => {
    const risk = entry - stop;
    if (risk <= 0) return { valid: false, reason: "Stop must be below entry" };
    const rr = (target - entry) / risk;
    const qty = Math.floor((capital * (RISK_PCT / 100)) / risk);
    const size = qty * entry;
    const concentration = (size / capital) * 100;
    const reasons: string[] = [];
    if (rr < MIN_RR) reasons.push(`R:R ${rr.toFixed(2)} < ${MIN_RR}`);
    if (concentration > MAX_POS_PCT) reasons.push(`Concentration ${concentration.toFixed(0)}% > ${MAX_POS_PCT}%`);
    return { valid: reasons.length === 0, reason: reasons.join(" · "), rr, qty, size, concentration, risk };
  }, [entry, stop, target, capital]);

  const Field = ({ label, value, set }: { label: string; value: number; set: (n: number) => void }) => (
    <label className="text-sm">
      <span className="text-muted-foreground">{label}</span>
      <input type="number" value={value} onChange={(e) => set(Number(e.target.value))}
        className="mt-1 w-full rounded-md border border-border bg-transparent px-2 py-1" />
    </label>
  );

  return (
    <Card className="p-5">
      <h3 className="font-semibold">Risk calculator</h3>
      <p className="text-xs text-muted-foreground">1% risk of ₹{capital.toLocaleString("en-IN")} capital · enforced</p>
      <div className="mt-3 grid grid-cols-3 gap-3">
        <Field label="Entry ₹" value={entry} set={setEntry} />
        <Field label="Stop ₹" value={stop} set={setStop} />
        <Field label="Target ₹" value={target} set={setTarget} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <div>Qty <b>{r.qty ?? "—"}</b></div>
        <div>Size <b>₹{r.size ? Math.round(r.size).toLocaleString("en-IN") : "—"}</b></div>
        <div>R:R <b>{r.rr ? r.rr.toFixed(2) : "—"}</b></div>
        <div>Risk/sh <b>₹{r.risk ?? "—"}</b></div>
      </div>
      <div className={`mt-3 text-sm ${r.valid ? "text-success" : "text-destructive"}`}>
        {r.valid ? "✓ Passes risk guards" : `✗ ${r.reason}`}
      </div>
      <Button className="mt-4" disabled={!r.valid}>Paper trade this</Button>
    </Card>
  );
}
