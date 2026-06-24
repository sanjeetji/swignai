"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth";

export function Providers({ children }: { children: React.ReactNode }) {
  const [qc] = useState(() => new QueryClient());
  const load = useAuth((s) => s.load);
  useEffect(() => load(), [load]);
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}
