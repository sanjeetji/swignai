"use client";
import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@swingai/api-client";
import { Button, Card, ThemeToggle, LanguageSwitcher } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";

export default function LoginPage() {
  const t = useTranslations();
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const setSession = useAuth((s) => s.setSession);
  const [email, setEmail] = useState("admin@swingai.in");
  const [password, setPassword] = useState("admin12345");
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
    <main className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
      <Card className="w-full max-w-sm p-6">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">{t("auth.login")}</h1>
          <div className="flex items-center gap-1"><LanguageSwitcher /><ThemeToggle /></div>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <input className="w-full rounded-md border border-border bg-transparent px-3 py-2"
            placeholder={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} />
          <input type="password" className="w-full rounded-md border border-border bg-transparent px-3 py-2"
            placeholder={t("auth.password")} value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full">{t("auth.submit")}</Button>
        </form>
        <div className="mt-4 flex items-center justify-between text-sm">
          <Link href={`/${locale}/signup`} className="text-muted-foreground hover:underline">
            {t("auth.noAccount")}
          </Link>
          <Link href={`/${locale}/forgot-password`} className="text-muted-foreground hover:underline">
            {t("auth.forgot")}
          </Link>
        </div>
      </Card>
    </main>
  );
}
