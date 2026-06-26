// Locale routing (blueprint/15). Auth/RBAC/block-gate are enforced server-side by the
// API on every request; client route-guards live in the (protected) layout. A production
// build moves the session check here too (Supabase cookie / httpOnly token).
import createMiddleware from "next-intl/middleware";
import { locales, defaultLocale } from "./i18n";

// localeDetection:false → always default to English; do NOT auto-redirect based on the
// browser's Accept-Language (that sent Indian browsers to /hi, which triggered Chrome's
// Google-Translate popup AND the React removeChild crash). A user's explicit choice still
// persists via next-intl's NEXT_LOCALE cookie, so switching to हिंदी sticks across refreshes.
export default createMiddleware({ locales, defaultLocale, localePrefix: "always", localeDetection: false });

export const config = { matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"] };
