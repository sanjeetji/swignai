import { getRequestConfig } from "next-intl/server";

export const locales = ["en", "hi"] as const;
export const defaultLocale = "en";

// next-intl 3.22+: read the locale via `requestLocale` and RETURN it (required — a missing
// `locale` makes the intl context null and crashes client hooks like usePathname/useRouter).
export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !locales.includes(locale as any)) locale = defaultLocale;
  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default,
  };
});
