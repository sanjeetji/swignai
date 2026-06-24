"use client";
import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { api } from "@swingai/api-client";
import { Button, Card } from "@swingai/ui";
import { useAuth } from "../../../lib/auth";

export default function LoginPage() {
  const t = useTranslations("auth");
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();
  const setToken = useAuth((s) => s.setToken);
  const [email, setEmail] = useState("admin@swingai.in");
  const [password, setPassword] = useState("admin12345");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      router.push(`/${locale}/dashboard`);
    } catch {
      setError("Invalid email or password");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
      <Card className="w-full max-w-sm p-6">
        <h1 className="text-xl font-semibold">{t("login")}</h1>
        <form onSubmit={submit} className="mt-4 space-y-3">
          <input className="w-full rounded-md border border-border bg-transparent px-3 py-2"
            placeholder={t("email")} value={email} onChange={(e) => setEmail(e.target.value)} />
          <input type="password" className="w-full rounded-md border border-border bg-transparent px-3 py-2"
            placeholder={t("password")} value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full">{t("submit")}</Button>
        </form>
      </Card>
    </main>
  );
}
