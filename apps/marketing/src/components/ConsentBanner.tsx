"use client";
// DPDP consent banner (blueprint/09) — first-visit notice for analytics/usage cookies.
// Choice persists in localStorage; no analytics fire until accepted.
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

const KEY = "swingai_consent";

export function ConsentBanner() {
  const { locale } = useParams<{ locale: string }>();
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem(KEY)) setShow(true);
  }, []);

  function choose(v: "accepted" | "declined") {
    localStorage.setItem(KEY, v);
    setShow(false);
  }

  if (!show) return null;
  return (
    <div className="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-card/95 px-4 py-3 backdrop-blur">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-3 sm:flex-row">
        <p className="flex-1 text-xs text-muted-foreground">
          We use essential cookies to run the site and, with your consent, usage analytics to improve it. See our{" "}
          <a href={`/${locale}/privacy`} className="text-primary hover:underline">Privacy Policy</a>.
        </p>
        <div className="flex gap-2">
          <button onClick={() => choose("declined")} className="rounded-md border border-border px-3 py-1.5 text-xs hover:bg-muted">Decline</button>
          <button onClick={() => choose("accepted")} className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground">Accept</button>
        </div>
      </div>
    </div>
  );
}
