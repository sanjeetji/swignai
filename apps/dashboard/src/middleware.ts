// Locale routing (blueprint/15). Auth/RBAC/block-gate are enforced server-side by the
// API on every request; client route-guards live in the (protected) layout. A production
// build moves the session check here too (Supabase cookie / httpOnly token).
import createMiddleware from "next-intl/middleware";
import { locales, defaultLocale } from "./i18n";

export default createMiddleware({ locales, defaultLocale, localePrefix: "always" });

export const config = { matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"] };
