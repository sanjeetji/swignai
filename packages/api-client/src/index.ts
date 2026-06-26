// Typed client for the SwingAI FastAPI backend (blueprint/07).
// One place the frontend talks to the API; never hardcode fetch URLs in components.

export const API_BASE =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_BASE) || "http://localhost:9000";

export interface Tokens {
  access_token: string;
  refresh_token?: string;
  token_type?: string;
}

export interface Brand {
  name: string; shortName: string; legalName: string;
  tagline: string; domain: string; supportEmail: string;
}

export interface ThemePreset {
  name: string; label: string;
  tokensLight: Record<string, string>; tokensDark: Record<string, string>;
}

export interface Appearance {
  defaults: { mode: string; preset: string; font: string; locale: string };
  locked: Record<string, boolean>;
  enabledLocales: string[];
  maintenance: { on: boolean; message: string | null };
  presets: ThemePreset[];
}

export interface TradePlan {
  entry: number; stop: number; target_1: number; target_2: number;
  rr_ratio: number; quantity: number; position_size: number;
}
export interface Pick {
  symbol: string; score: number; breakdown: Record<string, number>;
  regime: string; rsi: number; rel_strength: number; plan: TradePlan; disclaimer: string;
}
export interface DailyPicks { date: string; regime: string; cash_mode: boolean; picks: Pick[] }

export interface MarketStatus {
  session: "open" | "pre-open" | "closed";
  is_open: boolean;
  regime: "bull" | "neutral" | "bear" | "unknown";
  trend: "up" | "down" | "flat";
  index: {
    symbol: string; level: number | null; ema20: number | null; last_close: number | null;
    change_pct: number | null; live: boolean; as_of: string | null;
  };
  server_time_ist: string;
  disclaimer: string;
}

// Default per-request timeout (ms) so a slow/hung backend never freezes SSR — the request
// aborts and the caller's `.catch(fallback)` kicks in instead of hanging the page forever.
const REQ_TIMEOUT_MS = 12000;

// Global in-flight counter so a UI progress bar can show whenever the app is talking to the
// API. Subscribe via onApiActivity; harmless on the server (no subscribers).
let _inflight = 0;
const _activitySubs = new Set<(n: number) => void>();
export function onApiActivity(cb: (n: number) => void): () => void {
  _activitySubs.add(cb);
  cb(_inflight);
  return () => { _activitySubs.delete(cb); };
}
function _bump(delta: number) {
  _inflight = Math.max(0, _inflight + delta);
  _activitySubs.forEach((cb) => cb(_inflight));
}

async function req<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json", ...(init.headers as any) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), REQ_TIMEOUT_MS);
  _bump(1);
  try {
    const res = await fetch(`${API_BASE}${path}`, { ...init, headers, cache: "no-store", signal: ctrl.signal });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timer);
    _bump(-1);
  }
}

export const api = {
  // public
  brand: () => req<Brand>("/api/platform/brand"),
  appearance: () => req<Appearance>("/api/platform/appearance"),
  dailyPicks: (limit = 5) => req<DailyPicks>(`/api/daily-picks?limit=${limit}`),
  marketStatus: () => req<MarketStatus>("/api/market-status"),
  refreshPicks: (token: string, force = false) =>
    req<{ ran: boolean; reason?: string; regime?: string; count?: number }>(
      `/api/daily-picks/refresh?force=${force}`, { method: "POST" }, token),
  universe: () => req<{ symbols: string[]; count: number }>("/api/universe").catch(() => ({ symbols: [], count: 0 })),
  sectors: () => req<{ sectors: Record<string, string[]>; count: number }>("/api/sectors").catch(() => ({ sectors: {} as Record<string, string[]>, count: 0 })),
  scan: (params?: { min_score?: number; sector?: string; regime_bias?: string }) => {
    const q = new URLSearchParams();
    if (params?.min_score) q.set("min_score", String(params.min_score));
    if (params?.sector) q.set("sector", params.sector);
    if (params?.regime_bias) q.set("regime_bias", params.regime_bias);
    return req<{ date: string; regime: string; count: number; results: any[] }>(`/api/scan?${q.toString()}`);
  },
  cmsPage: (slug: string, locale = "en") => req<any>(`/api/cms/page/${slug}?locale=${locale}`),
  stockAnalysis: (symbol: string) => req<any>(`/api/stocks/${encodeURIComponent(symbol)}`),
  testimonials: (locale = "en") => req<any>(`/api/cms/testimonials?locale=${locale}`),
  stats: (locale = "en") => req<any>(`/api/cms/stats?locale=${locale}`),
  faqs: (locale = "en") => req<{ faqs: any[] }>(`/api/cms/faqs?locale=${locale}`).catch(() => ({ faqs: [] })),
  blogList: (locale = "en") => req<{ posts: any[] }>(`/api/cms/blog?locale=${locale}`).catch(() => ({ posts: [] })),
  trackRecord: () => req<any>("/api/track-record").catch(() => null),

  // auth
  register: (email: string, password: string, name?: string, referral_code?: string) =>
    req<Tokens>("/api/auth/register", { method: "POST", body: JSON.stringify({ email, password, name, referral_code }) }),
  referral: (token: string) => req<{ code: string; count: number; referred: any[] }>("/api/me/referral", {}, token).catch(() => ({ code: "", count: 0, referred: [] })),
  twoFactorSetup: (token: string) => req<{ secret: string; otpauth_uri: string }>("/api/me/2fa/setup", { method: "POST" }, token),
  twoFactorVerify: (token: string, code: string) => req<any>("/api/me/2fa/verify", { method: "POST", body: JSON.stringify({ code }) }, token),
  twoFactorDisable: (token: string) => req<any>("/api/me/2fa/disable", { method: "POST" }, token),
  login: (email: string, password: string) =>
    req<Tokens>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  refresh: (refresh_token: string) =>
    req<Tokens>("/api/auth/refresh", { method: "POST", body: JSON.stringify({ refresh_token }) }),
  logout: (token: string) => req<any>("/api/auth/logout", { method: "POST" }, token).catch(() => null),
  forgotPassword: (email: string) =>
    req<{ ok: boolean; message: string; dev_token?: string }>("/api/auth/forgot-password", { method: "POST", body: JSON.stringify({ email }) }),
  resetPassword: (token: string, new_password: string) =>
    req<Tokens>("/api/auth/reset-password", { method: "POST", body: JSON.stringify({ token, new_password }) }),
  me: (token: string) => req<any>("/api/auth/me", {}, token),
  notifications: (token: string) => req<{ unread: number; notifications: any[] }>("/api/notifications", {}, token).catch(() => ({ unread: 0, notifications: [] })),
  readNotification: (token: string, id: string) => req<any>(`/api/notifications/${id}/read`, { method: "POST" }, token).catch(() => null),
  readAllNotifications: (token: string) => req<any>("/api/notifications/read-all", { method: "POST" }, token).catch(() => null),

  // user
  analytics: (token: string) => req<any>("/api/analytics", {}, token),
  // billing
  billingPlans: () => req<{ plans: any[]; currency: string; enabled: boolean }>("/api/billing/plans").catch(() => ({ plans: [], currency: "INR", enabled: false })),
  subscription: (token: string) => req<any>("/api/billing/subscription", {}, token).catch(() => null),
  createOrder: (token: string, plan: string) => req<any>("/api/billing/create-order", { method: "POST", body: JSON.stringify({ plan }) }, token),
  startTrial: (token: string) => req<any>("/api/billing/start-trial", { method: "POST" }, token),
  verifyPayment: (token: string, body: any) => req<any>("/api/billing/verify", { method: "POST", body: JSON.stringify(body) }, token),
  equityCurve: (token: string) =>
    req<{ closed: number; curve: any[]; distribution: any[] }>("/api/analytics/equity", {}, token)
      .then((d) => ({ ...d, locked: false }))
      .catch((e: any) => ({ closed: 0, curve: [], distribution: [], locked: String(e?.message || "").includes("402") })),
  portfolio: (token: string) => req<any>("/api/paper-trade/portfolio", {}, token),
  trades: (token: string) => req<any>("/api/trades", {}, token),
  journalReview: (token: string) => req<any>("/api/journal/review", {}, token),
  paperBuy: (token: string, body: any) =>
    req<any>("/api/paper-trade/buy", { method: "POST", body: JSON.stringify(body) }, token),
  paperClose: (token: string, id: string, exit_price: number, exit_reason?: string) =>
    req<any>(`/api/paper-trade/${id}/close`, { method: "POST", body: JSON.stringify({ exit_price, exit_reason }) }, token),
  paperTrail: (token: string, id: string, new_stop: number) =>
    req<any>(`/api/paper-trade/${id}/trail`, { method: "POST", body: JSON.stringify({ new_stop }) }, token),

  // admin
  adminUsers: (token: string, q = "") => req<any>(`/api/admin/users?q=${encodeURIComponent(q)}`, {}, token),
  adminMetrics: (token: string) => req<any>("/api/admin/metrics", {}, token),
  blockUser: (token: string, id: string) => req<any>(`/api/admin/users/${id}/block`, { method: "POST" }, token),
  unblockUser: (token: string, id: string) => req<any>(`/api/admin/users/${id}/unblock`, { method: "POST" }, token),
  forceLogout: (token: string, id: string) => req<any>(`/api/admin/users/${id}/force-logout`, { method: "POST" }, token),
  impersonate: (token: string, id: string) => req<{ access_token: string; refresh_token: string; email: string }>(`/api/admin/users/${id}/impersonate`, { method: "POST" }, token),
  eventLogs: (token: string, category?: string, level?: string) => {
    const q = new URLSearchParams();
    if (category) q.set("category", category);
    if (level) q.set("level", level);
    return req<any>(`/api/admin/event-logs?${q.toString()}`, {}, token);
  },
  getAppearance: (token: string) => req<any>("/api/admin/settings/appearance", {}, token),
  setAppearance: (token: string, body: any) =>
    req<any>("/api/admin/settings/appearance", { method: "PUT", body: JSON.stringify(body) }, token),
  adminIntegrations: (token: string) => req<any>("/api/admin/integrations", {}, token),
  upsertIntegration: (token: string, provider: string, body: any) =>
    req<any>(`/api/admin/integrations/${provider}`, { method: "PUT", body: JSON.stringify(body) }, token),
  testIntegration: (token: string, provider: string) =>
    req<any>(`/api/admin/integrations/${provider}/test`, { method: "POST" }, token),
  rerunPipeline: (token: string) => req<any>("/api/admin/rerun-pipeline", { method: "POST" }, token),
  adminPlans: (token: string) => req<{ plans: any[] }>("/api/admin/plans", {}, token),
  upsertPlan: (token: string, slug: string, body: any) =>
    req<any>(`/api/admin/plans/${encodeURIComponent(slug)}`, { method: "PUT", body: JSON.stringify(body) }, token),
  deletePlan: (token: string, slug: string) =>
    req<any>(`/api/admin/plans/${encodeURIComponent(slug)}`, { method: "DELETE" }, token),
  adminUserDetail: (token: string, id: string) => req<any>(`/api/admin/users/${id}`, {}, token),
  featureFlags: (token: string) => req<any>("/api/admin/feature-flags", {}, token),
  upsertFlag: (token: string, key: string, body: any) =>
    req<any>(`/api/admin/feature-flags/${encodeURIComponent(key)}`, { method: "PUT", body: JSON.stringify(body) }, token),
  deleteFlag: (token: string, key: string) =>
    req<any>(`/api/admin/feature-flags/${encodeURIComponent(key)}`, { method: "DELETE" }, token),
  // CSV download — needs the auth header, so fetch as a blob (not a plain <a href>)
  eventLogsExport: async (token: string, category?: string, level?: string): Promise<Blob> => {
    const q = new URLSearchParams();
    if (category) q.set("category", category);
    if (level) q.set("level", level);
    const res = await fetch(`${API_BASE}/api/admin/event-logs/export?${q.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`export ${res.status}`);
    return res.blob();
  },
};
