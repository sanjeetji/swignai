import "../globals.css";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { ThemeProvider } from "@swingai/ui";
import { api } from "@swingai/api-client";
import { Providers } from "../../components/Providers";

export default async function LocaleLayout({
  children, params: { locale },
}: { children: React.ReactNode; params: { locale: string } }) {
  const messages = await getMessages();
  const appearance = await api.appearance().catch(() => null);
  const preset = appearance?.presets.find((p) => p.name === appearance.defaults.preset) ?? null;
  return (
    <html lang={locale} suppressHydrationWarning>
      <body>
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider preset={preset}>
            <Providers>{children}</Providers>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
