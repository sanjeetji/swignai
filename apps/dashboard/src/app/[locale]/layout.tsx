import "../globals.css";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { ThemeProvider, TopProgress } from "@swingai/ui";
import { api } from "@swingai/api-client";
import { Providers } from "../../components/Providers";

export default async function LocaleLayout({
  children, params: { locale },
}: { children: React.ReactNode; params: { locale: string } }) {
  const messages = await getMessages();
  const appearance = await api.appearance().catch(() => null);
  return (
    <html lang={locale} translate="no" suppressHydrationWarning>
      <head>
        {/* The app ships its own Hindi (next-intl). Tell browsers NOT to auto-translate —
            Google Translate rewrites the DOM and crashes React with "removeChild" NotFoundError. */}
        <meta name="google" content="notranslate" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <ThemeProvider presets={appearance?.presets ?? []} defaults={appearance?.defaults}>
            <TopProgress />
            <Providers>{children}</Providers>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
