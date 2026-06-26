"use client";
// Client auth store: JWT access + refresh in localStorage. Access is short-lived; on
// app load a stored refresh token is exchanged for a fresh access token so returning
// users stay signed in. Logout revokes the server session too (blueprint/19).
import { create } from "zustand";
import { api } from "@swingai/api-client";

const ACCESS = "swingai_token";
const REFRESH = "swingai_refresh";
const IMP = "swingai_imp";           // saved admin session while impersonating

interface AuthState {
  token: string | null;
  refresh: string | null;
  loaded: boolean;            // has localStorage been read yet?
  impersonating: string | null;   // email of the user being viewed-as
  setSession: (access: string | null, refresh?: string | null) => void;
  setToken: (t: string | null) => void;   // kept for back-compat callers
  startImpersonation: (access: string, refresh: string, email: string) => void;
  stopImpersonation: () => void;
  load: () => void;
  logout: () => void;
}

function persist(access: string | null, refresh: string | null | undefined) {
  if (typeof window === "undefined") return;
  if (access) localStorage.setItem(ACCESS, access); else localStorage.removeItem(ACCESS);
  if (refresh !== undefined) {
    if (refresh) localStorage.setItem(REFRESH, refresh); else localStorage.removeItem(REFRESH);
  }
}

export const useAuth = create<AuthState>((set, get) => ({
  token: null,
  refresh: null,
  loaded: false,
  impersonating: null,
  setSession: (access, refresh) => {
    persist(access, refresh);
    set({ token: access, ...(refresh !== undefined ? { refresh } : {}) });
  },
  setToken: (t) => { persist(t, undefined); set({ token: t }); },
  startImpersonation: (access, refresh, email) => {
    const { token, refresh: r } = get();
    if (typeof window !== "undefined") localStorage.setItem(IMP, JSON.stringify({ token, refresh: r, email }));
    persist(access, refresh);
    set({ token: access, refresh, impersonating: email });
  },
  stopImpersonation: () => {
    if (typeof window === "undefined") return;
    const saved = localStorage.getItem(IMP);
    localStorage.removeItem(IMP);
    if (saved) {
      const { token, refresh } = JSON.parse(saved);
      persist(token, refresh);
      set({ token, refresh, impersonating: null });
    } else {
      set({ impersonating: null });
    }
  },
  load: () => {
    if (typeof window === "undefined") return;
    const access = localStorage.getItem(ACCESS);
    const refresh = localStorage.getItem(REFRESH);
    let impersonating: string | null = null;
    const imp = localStorage.getItem(IMP);
    if (imp) { try { impersonating = JSON.parse(imp).email ?? null; } catch { impersonating = null; } }
    set({ token: access, refresh, loaded: true, impersonating });
    // self-heal an expired access token from a still-valid refresh token
    if (refresh) {
      api.refresh(refresh)
        .then((tk) => { persist(tk.access_token, tk.refresh_token ?? refresh); set({ token: tk.access_token }); })
        .catch(() => {});   // refresh invalid/expired — keep whatever access we had (or none)
    }
  },
  logout: () => {
    const { token } = get();
    if (token) api.logout(token);              // best-effort server-side session revoke
    if (typeof window !== "undefined") localStorage.removeItem(IMP);
    persist(null, null);
    set({ token: null, refresh: null, impersonating: null });
  },
}));
