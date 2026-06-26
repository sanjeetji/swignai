"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@swingai/api-client";
import { Button, Card, ThemeToggle, LanguageSwitcher } from "@swingai/ui";

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
    <main className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
      <Card className="w-full max-w-sm p-6">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">{t("auth.forgot")}</h1>
          <div className="flex items-center gap-1"><LanguageSwitcher /><ThemeToggle /></div>
        </div>
        {sent ? (
          <div className="space-y-3 text-sm">
            <p className="text-muted-foreground">{t("auth.resetSent")}</p>
            {devToken && (
              <Link href={`/${locale}/reset-password?token=${devToken}`}
                className="block break-all rounded-md border border-border p-2 text-xs text-primary hover:underline">
                {t("auth.devResetLink")} →
              </Link>
            )}
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <input className="w-full rounded-md border border-border bg-transparent px-3 py-2"
              placeholder={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} />
            <Button type="submit" className="w-full">{t("auth.sendReset")}</Button>
          </form>
        )}
        <Link href={`/${locale}/login`} className="mt-4 block text-center text-sm text-muted-foreground hover:underline">
          {t("auth.backToLogin")}
        </Link>
      </Card>
    </main>
  );
}
