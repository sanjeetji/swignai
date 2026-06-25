"use client";
// Blocks protected pages until auth is confirmed. No flash of the dashboard shell
// for logged-out users — they're redirected to /login (blueprint/19, dev-grade auth).
import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "../lib/auth";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuth((s) => s.token);
  const loaded = useAuth((s) => s.loaded);
  const router = useRouter();
  const { locale } = useParams<{ locale: string }>();

  useEffect(() => {
    if (loaded && !token) router.replace(`/${locale}/login`);
  }, [loaded, token, locale, router]);

  if (!loaded) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading…</div>;
  }
  if (!token) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Redirecting to login…</div>;
  }
  return <>{children}</>;
}
