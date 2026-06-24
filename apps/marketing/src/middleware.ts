// Locale routing middleware (blueprint/15). User pref → default → Accept-Language → en.
import createMiddleware from "next-intl/middleware";
import { locales, defaultLocale } from "./i18n";

export default createMiddleware({ locales, defaultLocale, localePrefix: "always" });

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
