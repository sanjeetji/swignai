// Privacy policy (blueprint/09) — DPDP-aware. TEMPLATE: have a lawyer review before launch.
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy — SwingAI",
  description: "How SwingAI collects, uses, and protects your data under India's DPDP Act.",
  alternates: { canonical: "/privacy" },
};

const UPDATED = "2026-06-26";

export default function Privacy() {
  return (
    <main className="mx-auto min-h-screen max-w-3xl bg-background px-6 py-16 text-foreground">
      <div className="mb-6 rounded-lg border border-warning/40 bg-warning/10 p-3 text-xs text-warning">
        Template pending legal review — not yet a binding policy. Have a DPDP/SEBI lawyer finalise before public launch.
      </div>
      <h1 className="text-3xl font-bold">Privacy Policy</h1>
      <p className="mt-2 text-sm text-muted-foreground">Last updated {UPDATED}</p>

      <div className="prose mt-8 max-w-none space-y-6 text-sm leading-relaxed text-muted-foreground">
        <section>
          <h2 className="text-lg font-semibold text-foreground">1. Who we are</h2>
          <p>SwingAI (“we”, “us”) provides educational technical analysis and paper-trading tools for NSE swing trading. We are the data fiduciary for the personal data described here under India’s Digital Personal Data Protection Act, 2023 (DPDP).</p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">2. What we collect</h2>
          <ul className="list-disc pl-5">
            <li><b>Account:</b> name, email, password (hashed), preferences.</li>
            <li><b>Usage:</b> paper trades, journal entries, settings you create.</li>
            <li><b>Technical:</b> IP address, approximate city/region (derived from IP), device/browser, session times — for security and fraud prevention.</li>
            <li><b>Payments:</b> processed by Razorpay; we store only a payment reference and plan, never card details.</li>
          </ul>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">3. Why we use it</h2>
          <p>To run your account, provide the service, keep it secure, comply with law, and (with consent) understand product usage. We do <b>not</b> sell your personal data.</p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">4. Consent &amp; your rights (DPDP)</h2>
          <p>You may access, correct, or delete your data, withdraw consent, and export your data from Settings. Account deletion removes your personal data subject to legal retention. Contact us to exercise any right.</p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">5. Retention</h2>
          <p>We keep data only as long as needed: sessions and login history are auto-purged on a schedule; account data is removed on deletion (some records retained where law requires).</p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">6. Security &amp; processors</h2>
          <p>Passwords are hashed; integration secrets are encrypted at rest. We use processors including Razorpay (payments), our LLM/data providers, and error monitoring — bound to protect your data.</p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">7. Contact / Grievance Officer</h2>
          <p>Questions or DPDP requests: <b>privacy@swingai.in</b> (placeholder — replace before launch).</p>
        </section>
      </div>
    </main>
  );
}
