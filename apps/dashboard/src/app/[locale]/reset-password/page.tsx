"use client";
import { useState } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@swingai/api-client";
import { Button, Card, ThemeToggle, LanguageSwitcher } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";

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
    <main className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
      <Card className="w-full max-w-sm p-6">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">{t("auth.resetTitle")}</h1>
          <div className="flex items-center gap-1"><LanguageSwitcher /><ThemeToggle /></div>
        </div>
        {!token ? (
          <p className="text-sm text-destructive">{t("auth.resetNoToken")}</p>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <input type="password" className="w-full rounded-md border border-border bg-transparent px-3 py-2"
              placeholder={t("auth.newPassword")} value={password} onChange={(e) => setPassword(e.target.value)} />
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full">{t("auth.resetSubmit")}</Button>
          </form>
        )}
        <Link href={`/${locale}/login`} className="mt-4 block text-center text-sm text-muted-foreground hover:underline">
          {t("auth.backToLogin")}
        </Link>
      </Card>
    </main>
  );
}
