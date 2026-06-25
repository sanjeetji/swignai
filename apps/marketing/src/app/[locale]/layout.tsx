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
  const preset = appearance?.presets.find((p) => p.name === appearance.defaults.preset) ?? null;

  return (
    <html lang={locale} suppressHydrationWarning>
      <body>
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider preset={preset}>
            <Header />
            {children}
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
