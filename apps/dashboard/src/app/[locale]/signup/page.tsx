"use client";
import { Suspense, useState } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@swingai/api-client";
import { Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { AuthShell, authInput } from "../../../components/AuthShell";

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
  const [referral, setReferral] = useState(useSearchParams().get("ref") || "");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const tk = await api.register(email, password, name || undefined, referral.trim() || undefined);
      setSession(tk.access_token, tk.refresh_token);
      router.push(`/${locale}/dashboard`);
    } catch (e: any) {
      setError(String(e?.message || "").includes("409") ? t("auth.exists") : t("auth.invalid"));
    }
  }

  return (
    <AuthShell title={t("auth.signup")} subtitle={t("auth.signupSub")}
      footer={<Link href={`/${locale}/login`} className="text-muted-foreground hover:text-foreground hover:underline">{t("auth.haveAccount")}</Link>}>
      <form onSubmit={submit} className="space-y-3">
        <input className={authInput} placeholder={t("auth.name")} value={name} onChange={(e) => setName(e.target.value)} />
        <input className={authInput} placeholder={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} />
        <input type="password" className={authInput} placeholder={t("auth.password")} value={password} onChange={(e) => setPassword(e.target.value)} />
        <input className={authInput} placeholder={t("auth.referralOptional")} value={referral} onChange={(e) => setReferral(e.target.value.toUpperCase())} />
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full">{t("auth.submitSignup")}</Button>
      </form>
    </AuthShell>
  );
}
