"use client";
// Minimal client auth store for the scaffold (token in localStorage). Production
// upgrades to Supabase Auth / httpOnly cookies + middleware session check (blueprint/19).
import { create } from "zustand";

const KEY = "swingai_token";

interface AuthState {
  token: string | null;
  loaded: boolean;            // has localStorage been read yet? (distinguishes "no token" from "not loaded")
  setToken: (t: string | null) => void;
  load: () => void;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  token: null,
  loaded: false,
  setToken: (t) => {
    if (typeof window !== "undefined") {
      if (t) localStorage.setItem(KEY, t);
      else localStorage.removeItem(KEY);
    }
    set({ token: t });
  },
  load: () => {
    if (typeof window !== "undefined") {
      set({ token: localStorage.getItem(KEY), loaded: true });
    }
  },
  logout: () => {
    if (typeof window !== "undefined") localStorage.removeItem(KEY);
    set({ token: null });
  },
}));
