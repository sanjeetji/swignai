"use client";
// Thin top progress bar (YouTube/GitHub style) — visible whenever the app is fetching from
// the API or navigating between routes, so slow loads never feel frozen. No dependency.
import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { onApiActivity } from "@swingai/api-client";

export function TopProgress() {
  const pathname = usePathname();
  const [width, setWidth] = useState(0);
  const [visible, setVisible] = useState(false);
  const timers = useRef<any[]>([]);

  function clear() { timers.current.forEach(clearTimeout); timers.current = []; }
  function start() {
    clear(); setVisible(true); setWidth(8);
    timers.current.push(setTimeout(() => setWidth(45), 80));
    timers.current.push(setTimeout(() => setWidth(75), 300));
  }
  function done() {
    clear(); setWidth(100);
    timers.current.push(setTimeout(() => setVisible(false), 250));
    timers.current.push(setTimeout(() => setWidth(0), 500));
  }

  // Route changes: quick fill-and-finish.
  useEffect(() => { start(); const t = setTimeout(done, 500); return () => clearTimeout(t); }, [pathname]);

  // API activity: show while any request is in flight.
  useEffect(() => onApiActivity((n) => (n > 0 ? start() : done())), []);

  if (!visible && width === 0) return null;
  return (
    <div className="pointer-events-none fixed inset-x-0 top-0 z-[100] h-0.5">
      <div
        className="h-full bg-primary transition-all duration-200 ease-out"
        style={{ width: `${width}%`, opacity: visible ? 1 : 0, boxShadow: "0 0 8px var(--primary, #2563eb)" }}
      />
    </div>
  );
}
