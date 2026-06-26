"use client";
// In-app notification bell (blueprint/20) — unread count + dropdown of target/stop-hit
// alerts. Polls every 60s. Mark-read on open.
import { useCallback, useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";
import { api } from "@swingai/api-client";
import { useAuth } from "../lib/auth";

function label(n: any): { text: string; tone: string } {
  const p = n.payload || {};
  if (n.type === "trade.target") return { text: `🎯 ${p.symbol} hit target — +₹${p.pnl_inr} (${p.r_multiple}R)`, tone: "text-success" };
  if (n.type === "trade.stoploss") return { text: `🛑 ${p.symbol} hit stop — ₹${p.pnl_inr} (${p.r_multiple}R)`, tone: "text-destructive" };
  return { text: `${n.type}: ${JSON.stringify(p)}`, tone: "text-muted-foreground" };
}

export function NotificationBell() {
  const token = useAuth((s) => s.token);
  const [data, setData] = useState<{ unread: number; notifications: any[] }>({ unread: 0, notifications: [] });
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const load = useCallback(() => { if (token) api.notifications(token).then(setData); }, [token]);
  useEffect(() => { load(); const id = setInterval(load, 60000); return () => clearInterval(id); }, [load]);
  useEffect(() => {
    const onClick = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", onClick); return () => document.removeEventListener("mousedown", onClick);
  }, []);

  async function toggle() {
    const next = !open; setOpen(next);
    if (next && token && data.unread > 0) { await api.readAllNotifications(token); load(); }
  }

  return (
    <div className="relative" ref={ref}>
      <button onClick={toggle} className="relative rounded-md p-2 text-muted-foreground hover:bg-muted" aria-label="Notifications">
        <Bell size={18} />
        {data.unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-destructive px-1 text-[10px] font-bold text-white">
            {data.unread > 9 ? "9+" : data.unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-border bg-card shadow-xl">
          <div className="border-b border-border px-4 py-2.5 text-sm font-semibold">Notifications</div>
          <div className="max-h-80 divide-y divide-border overflow-y-auto">
            {data.notifications.length === 0 ? (
              <div className="px-4 py-6 text-center text-sm text-muted-foreground">No notifications yet. You'll be alerted when a position hits its target or stop.</div>
            ) : data.notifications.map((n) => {
              const l = label(n);
              return (
                <div key={n.id} className={`px-4 py-2.5 text-sm ${n.read ? "opacity-60" : ""}`}>
                  <div className={l.tone}>{l.text}</div>
                  <div className="text-xs text-muted-foreground">{String(n.at).slice(0, 16)}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
