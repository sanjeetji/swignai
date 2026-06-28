"use client";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { Check } from "lucide-react";
import { api } from "@swingai/api-client";
import { Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { AuthShell, authInput, PasswordInput } from "../../../components/AuthShell";

export default function SignupPage() {
  // useSearchParams() must be under a Suspense boundary (Next.js requirement).
  return <Suspense fallback={null}><SignupInner /></Suspense>;
}

function SignupInner() {
  const t = useTranslations();
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const setSession = useAuth((s) => s.setSession);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [referral, setReferral] = useState(useSearchParams().get("ref") || "");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [plans, setPlans] = useState<any[]>([]);
  const [plan, setPlan] = useState<string>("trial");

  useEffect(() => { api.billingPlans().then((r) => setPlans(r.plans || [])).catch(() => {}); }, []);

  // Free + the DB plans (trial / pro / premium), ordered for the chooser.
  const options = [
    { slug: "free", name: "Free", price: 0, note: "Daily picks + paper trading" },
    ...plans.map((p) => ({
      slug: p.id ?? p.slug, name: p.name, price: p.price_inr ?? p.price ?? 0, trial_days: p.trial_days,
      note: p.trial_days ? `${p.trial_days} days full access · no card` : "Full access + alerts",
    })),
  ];
  const selected = options.find((o) => o.slug === plan);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    if (password !== confirm) { setError("Passwords do not match."); return; }
    setBusy(true);
    try {
      const tk = await api.register(email, password, name || undefined, referral.trim() || undefined);
      setSession(tk.access_token, tk.refresh_token);
      const token = tk.access_token;
      if (plan === "trial") { try { await api.startTrial(token); } catch { /* keep going */ } router.push(`/${locale}/dashboard`); }
      else if (selected && selected.price > 0) router.push(`/${locale}/billing?checkout=${plan}`);   // auto-open Razorpay
      else { try { await api.activateFree(token); } catch { /* keep going */ } router.push(`/${locale}/dashboard`); }
    } catch (e: any) {
      setError(String(e?.message || "").includes("409") ? t("auth.exists") : t("auth.invalid"));
    } finally { setBusy(false); }
  }

  return (
    <AuthShell title={t("auth.signup")} subtitle="Create your account & pick a plan"
      footer={<Link href={`/${locale}/login`} className="text-muted-foreground hover:text-foreground hover:underline">{t("auth.haveAccount")}</Link>}>
      <form onSubmit={submit} className="space-y-3">
        <input className={authInput} placeholder={t("auth.name")} value={name} onChange={(e) => setName(e.target.value)} />
        <input className={authInput} placeholder={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} />
        <PasswordInput placeholder={t("auth.password")} value={password} onChange={setPassword} />
        <PasswordInput placeholder="Confirm password" value={confirm} onChange={setConfirm} />
        {confirm.length > 0 && password !== confirm && <p className="text-xs text-destructive">Passwords don't match</p>}
        <input className={authInput} placeholder={t("auth.referralOptional")} value={referral} onChange={(e) => setReferral(e.target.value.toUpperCase())} />

        <div className="space-y-1.5 pt-1">
          <div className="text-xs font-medium text-muted-foreground">Choose a plan</div>
          {options.map((o) => {
            const active = o.slug === plan;
            return (
              <button type="button" key={o.slug} onClick={() => setPlan(o.slug)}
                className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left transition-colors ${
                  active ? "border-primary bg-primary/5 ring-1 ring-primary/30" : "border-border hover:bg-muted"}`}>
                <div>
                  <div className="flex items-center gap-1.5 text-sm font-medium">
                    {o.name}{o.slug === "trial" && <span className="rounded-full bg-success/15 px-1.5 text-[10px] font-semibold text-success">FREE TRIAL</span>}
                  </div>
                  <div className="text-xs text-muted-foreground">{o.note}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold tabular-nums">{o.price > 0 ? `₹${o.price}` : "₹0"}</span>
                  {active && <span className="grid h-4 w-4 place-items-center rounded-full bg-primary text-primary-foreground"><Check size={11} /></span>}
                </div>
              </button>
            );
          })}
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Creating…" : selected && selected.price > 0 ? `Continue to payment (₹${selected.price})` : plan === "trial" ? "Start free trial" : t("auth.submitSignup")}
        </Button>
      </form>
    </AuthShell>
  );
}
