"use client";
import { useState } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@swingai/api-client";
import { Button } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";
import { AuthShell, authInput } from "../../../components/AuthShell";

export default function ResetPasswordPage() {
  const t = useTranslations();
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const token = useSearchParams().get("token") || "";
  const setSession = useAuth((s) => s.setSession);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const tk = await api.resetPassword(token, password);
      setSession(tk.access_token, tk.refresh_token);   // reset signs them straight in
      router.push(`/${locale}/dashboard`);
    } catch {
      setError(t("auth.resetInvalid"));
    }
  }

  return (
    <AuthShell title={t("auth.resetTitle")} subtitle={t("auth.resetSub")}
      footer={<Link href={`/${locale}/login`} className="text-muted-foreground hover:text-foreground hover:underline">{t("auth.backToLogin")}</Link>}>
      {!token ? (
        <p className="text-sm text-destructive">{t("auth.resetNoToken")}</p>
      ) : (
        <form onSubmit={submit} className="space-y-3">
          <input type="password" className={authInput} placeholder={t("auth.newPassword")} value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full">{t("auth.resetSubmit")}</Button>
        </form>
      )}
    </AuthShell>
  );
}
