// Locale routing middleware (blueprint/15). Default English; user's explicit choice persists
// via next-intl's NEXT_LOCALE cookie. localeDetection:false so we don't auto-redirect Indian
// browsers to /hi (which triggered Chrome's translate popup + React DOM crashes).
import createMiddleware from "next-intl/middleware";
import { locales, defaultLocale } from "./i18n";

export default createMiddleware({ locales, defaultLocale, localePrefix: "always", localeDetection: false });

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
