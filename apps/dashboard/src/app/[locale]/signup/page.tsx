"use client";
import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@swingai/api-client";
import { Button, Card, ThemeToggle, LanguageSwitcher } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";

export default function SignupPage() {
  const t = useTranslations();
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const setSession = useAuth((s) => s.setSession);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const tk = await api.register(email, password, name || undefined);
      setSession(tk.access_token, tk.refresh_token);
      router.push(`/${locale}/dashboard`);
    } catch (e: any) {
      setError(String(e?.message || "").includes("409") ? t("auth.exists") : t("auth.invalid"));
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
      <Card className="w-full max-w-sm p-6">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">{t("auth.signup")}</h1>
          <div className="flex items-center gap-1"><LanguageSwitcher /><ThemeToggle /></div>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <input className="w-full rounded-md border border-border bg-transparent px-3 py-2"
            placeholder={t("auth.name")} value={name} onChange={(e) => setName(e.target.value)} />
          <input className="w-full rounded-md border border-border bg-transparent px-3 py-2"
            placeholder={t("auth.email")} value={email} onChange={(e) => setEmail(e.target.value)} />
          <input type="password" className="w-full rounded-md border border-border bg-transparent px-3 py-2"
            placeholder={t("auth.password")} value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full">{t("auth.submitSignup")}</Button>
        </form>
        <Link href={`/${locale}/login`} className="mt-4 block text-center text-sm text-muted-foreground hover:underline">
          {t("auth.haveAccount")}
        </Link>
      </Card>
    </main>
  );
}
