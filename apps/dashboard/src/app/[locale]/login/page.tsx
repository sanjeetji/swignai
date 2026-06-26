"use client";
import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@swingai/api-client";
import { Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { AuthShell, authInput, PasswordInput } from "../../../components/AuthShell";

export default function LoginPage() {
  const t = useTranslations();
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const setSession = useAuth((s) => s.setSession);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const tk = await api.login(email, password);
      setSession(tk.access_token, tk.refresh_token);
      router.push(`/${locale}/dashboard`);
    } catch {
      setError(t("auth.invalid"));
    }
  }

  return (
    <AuthShell title={t("auth.login")} subtitle={t("auth.loginSub")}
      footer={
        <div className="flex items-center justify-between">
          <Link href={`/${locale}/signup`} className="text-muted-foreground hover:text-foreground hover:underline">{t("auth.noAccount")}</Link>
          <Link href={`/${locale}/forgot-password`} className="text-muted-foreground hover:text-foreground hover:underline">{t("auth.forgot")}</Link>
        </div>
      }>
      <form onSubmit={submit} className="space-y-3">
        <input className={authInput} placeholder={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} />
        <PasswordInput placeholder={t("auth.password")} value={password} onChange={setPassword} />
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full">{t("auth.submit")}</Button>
      </form>
    </AuthShell>
  );
}
