"use client";
// Admin plan editor (blueprint/20) — create/edit/delete subscription plans (price +
// features). Active plans show on marketing + the dashboard billing page. All API-driven.
import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2, Star } from "lucide-react";
import { api } from "@swingai/api-client";
import { Card, Button } from "@swingai/ui";
import { useAuth } from "../../../../lib/auth";

type Editing = {
  slug: string; name: string; price_inr: number; interval: string;
  features: string; is_active: boolean; is_featured: boolean; sort_order: number;
};

const blank: Editing = { slug: "", name: "", price_inr: 0, interval: "month", features: "", is_active: true, is_featured: false, sort_order: 0 };

export default function AdminPlans() {
  const token = useAuth((s) => s.token);
  const [plans, setPlans] = useState<any[]>([]);
  const [denied, setDenied] = useState(false);
  const [edit, setEdit] = useState<Editing | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    api.adminPlans(token).then((r) => setPlans(r.plans)).catch(() => setDenied(true));
  }, [token]);
  useEffect(() => { load(); }, [load]);

  if (denied) return <Card className="p-6">403 — admin access required.</Card>;

  function startEdit(p?: any) {
    setMsg(null);
    setEdit(p ? { ...p, features: (p.features || []).join("\n") } : { ...blank });
  }

  async function save() {
    if (!token || !edit) return;
    const slug = (edit.slug || edit.name).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    if (!slug || !edit.name) { setMsg("Name is required."); return; }
    try {
      await api.upsertPlan(token, slug, {
        name: edit.name, price_inr: Number(edit.price_inr), interval: edit.interval,
        features: edit.features.split("\n").map((f) => f.trim()).filter(Boolean),
        is_active: edit.is_active, is_featured: edit.is_featured, sort_order: Number(edit.sort_order),
      });
      setEdit(null); setMsg("Saved."); load();
    } catch (e: any) { setMsg(String(e?.message || e).slice(0, 120)); }
  }

  async function remove(slug: string) {
    if (!token || !confirm(`Delete plan "${slug}"?`)) return;
    try { await api.deletePlan(token, slug); load(); } catch {}
  }

  const field = "w-full rounded-md border border-border bg-background px-3 py-2 text-sm";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Plans &amp; Pricing</h1>
        <Button size="sm" onClick={() => startEdit()}><Plus size={15} className="mr-1" /> New plan</Button>
      </div>
      {msg && <p className="text-sm text-muted-foreground">{msg}</p>}

      {edit && (
        <Card className="space-y-3 p-5">
          <div className="font-semibold">{edit.slug ? `Edit ${edit.slug}` : "New plan"}</div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="text-xs text-muted-foreground">Name
              <input className={field} value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} placeholder="Pro" />
            </label>
            <label className="text-xs text-muted-foreground">Price (₹ / {edit.interval})
              <input type="number" className={field} value={edit.price_inr} onChange={(e) => setEdit({ ...edit, price_inr: Number(e.target.value) })} />
            </label>
            <label className="text-xs text-muted-foreground">Billing interval
              <select className={field} value={edit.interval} onChange={(e) => setEdit({ ...edit, interval: e.target.value })}>
                <option value="month">Monthly</option><option value="year">Yearly</option>
              </select>
            </label>
            <label className="text-xs text-muted-foreground">Sort order
              <input type="number" className={field} value={edit.sort_order} onChange={(e) => setEdit({ ...edit, sort_order: Number(e.target.value) })} />
            </label>
          </div>
          <label className="block text-xs text-muted-foreground">Features (one per line)
            <textarea className={`${field} h-28`} value={edit.features} onChange={(e) => setEdit({ ...edit, features: e.target.value })}
              placeholder={"Daily picks + scanner\nPaper trading + journal"} />
          </label>
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <label className="flex items-center gap-2"><input type="checkbox" checked={edit.is_active} onChange={(e) => setEdit({ ...edit, is_active: e.target.checked })} /> Active</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={edit.is_featured} onChange={(e) => setEdit({ ...edit, is_featured: e.target.checked })} /> Featured (highlight)</label>
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={save}>Save plan</Button>
            <Button size="sm" variant="ghost" onClick={() => setEdit(null)}>Cancel</Button>
          </div>
        </Card>
      )}

      <Card className="divide-y divide-border">
        {plans.map((p) => (
          <div key={p.slug} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm">
            <div>
              <div className="flex items-center gap-2 font-semibold">
                {p.name} {p.is_featured && <Star size={13} className="text-primary" fill="currentColor" />}
                {!p.is_active && <span className="text-xs text-muted-foreground">· hidden</span>}
              </div>
              <div className="text-xs text-muted-foreground">₹{p.price_inr}/{p.interval} · {(p.features || []).length} features · slug {p.slug}</div>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => startEdit(p)}>Edit</Button>
              <Button size="sm" variant="ghost" onClick={() => remove(p.slug)}><Trash2 size={14} /></Button>
            </div>
          </div>
        ))}
        {plans.length === 0 && <div className="px-4 py-6 text-sm text-muted-foreground">No plans yet — create one.</div>}
      </Card>
    </div>
  );
}
