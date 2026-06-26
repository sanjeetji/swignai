// next-intl config — EN + HI, extensible (blueprint/15). Add a locale = add to
// `locales` + a messages file; no component changes.
import { getRequestConfig } from "next-intl/server";

export const locales = ["en", "hi"] as const;
export const defaultLocale = "en";

// next-intl 3.22+: read via `requestLocale` and RETURN `locale` (required, else the intl
// context is null and client hooks crash).
export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !locales.includes(locale as any)) locale = defaultLocale;
  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default,
  };
});
