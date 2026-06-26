"use client";
// Language switcher — the industry-standard way to change locale (a dropdown, not by
// typing the URL). The locale stays in the path (best for SEO / shareable links), but
// the user never edits it manually. Works in both apps (next/navigation, transpiled).
import { useState, useTransition } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Globe } from "lucide-react";
import { Button } from "./button";

const LABELS: Record<string, string> = { en: "English", hi: "हिंदी" };

export function LanguageSwitcher({ locales = ["en", "hi"] }: { locales?: string[] }) {
  const pathname = usePathname() || "/";
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const current = pathname.split("/")[1] || "en";

  function switchTo(loc: string) {
    if (loc === current) { setOpen(false); return; }
    const segs = pathname.split("/");
    segs[1] = loc;                 // replace the locale segment
    // Read query via window (click-time only) — avoids useSearchParams, which would force a
    // Suspense boundary on every page that renders this switcher.
    const qs = typeof window !== "undefined" ? window.location.search : "";
    const url = (segs.join("/") || `/${loc}`) + qs;
    setOpen(false);
    // useTransition keeps the UI interactive during the locale swap (no hard-reload flash)
    // and drives the top progress bar instead of a blank screen.
    startTransition(() => router.replace(url));
  }

  return (
    <div className="relative">
      <Button variant="ghost" size="sm" aria-label="Change language" onClick={() => setOpen((o) => !o)}>
        <Globe className={`mr-1 h-4 w-4 ${pending ? "animate-spin" : ""}`} />
        <span className="text-xs uppercase">{current}</span>
      </Button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-1 min-w-32 rounded-md border border-border bg-card p-1 shadow-md">
            {locales.map((loc) => (
              <button
                key={loc}
                onClick={() => switchTo(loc)}
                className={`block w-full rounded px-3 py-1.5 text-left text-sm hover:bg-muted ${loc === current ? "font-semibold text-primary" : ""}`}
              >
                {LABELS[loc] ?? loc}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
