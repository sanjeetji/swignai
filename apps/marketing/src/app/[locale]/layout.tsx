import "../globals.css";
import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { ThemeProvider } from "@swingai/ui";
import { api } from "@swingai/api-client";
import { Header } from "../../components/Header";

export async function generateMetadata(): Promise<Metadata> {
  const brand = await api.brand().catch(() => null);
  return {
    title: brand ? `${brand.name} — ${brand.tagline}` : "SwingAI",
    description: brand?.tagline,
  };
}

export default async function LocaleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const messages = await getMessages();
  // platform default preset for first paint (user override applied client-side later)
  const appearance = await api.appearance().catch(() => null);

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider presets={appearance?.presets ?? []} defaults={appearance?.defaults}>
            <Header />
            {children}
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
