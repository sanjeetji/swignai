// Locale root → send users to the dashboard (which redirects to /login if not authed).
import { redirect } from "next/navigation";

export default function LocaleIndex({ params: { locale } }: { params: { locale: string } }) {
  redirect(`/${locale}/dashboard`);
}
