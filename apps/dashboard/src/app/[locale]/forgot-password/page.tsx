"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@swingai/api-client";
import { Button } from "@swingai/ui";
import { AuthShell, authInput } from "../../../components/AuthShell";

export default function ForgotPasswordPage() {
  const t = useTranslations();
  const { locale } = useParams<{ locale: string }>();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const r = await api.forgotPassword(email);
      setSent(true);
      if (r.dev_token) setDevToken(r.dev_token);   // dev only — lets you test without email
    } catch { setSent(true); }                       // never reveal whether the email exists
  }

  return (
    <AuthShell title={t("auth.forgot")} subtitle={t("auth.forgotSub")}
      footer={<Link href={`/${locale}/login`} className="text-muted-foreground hover:text-foreground hover:underline">{t("auth.backToLogin")}</Link>}>
      {sent ? (
        <div className="space-y-3 text-sm">
          <p className="rounded-lg bg-success/10 p-3 text-success">{t("auth.resetSent")}</p>
          {devToken && (
            <Link href={`/${locale}/reset-password?token=${devToken}`}
              className="block break-all rounded-lg border border-border p-2 text-xs text-primary hover:underline">
              {t("auth.devResetLink")} →
            </Link>
          )}
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-3">
          <input className={authInput} placeholder={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} />
          <Button type="submit" className="w-full">{t("auth.sendReset")}</Button>
        </form>
      )}
    </AuthShell>
  );
}
