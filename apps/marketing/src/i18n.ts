// next-intl config — EN + HI, extensible (blueprint/15). Add a locale = add to
// `locales` + a messages file; no component changes.
import { getRequestConfig } from "next-intl/server";
import { notFound } from "next/navigation";

export const locales = ["en", "hi"] as const;
export const defaultLocale = "en";

export default getRequestConfig(async ({ locale }) => {
  if (!locales.includes(locale as any)) notFound();
  return { messages: (await import(`./messages/${locale}.json`)).default };
});
