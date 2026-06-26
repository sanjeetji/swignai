// Terms of Service (blueprint/09,13) — leads with the SEBI "analysis, not advice" stance.
// TEMPLATE: have a SEBI-specialist lawyer review before public launch.
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms & Disclaimer — SwingAI",
  description: "Terms of use and the educational-analysis (not investment advice) disclaimer for SwingAI.",
  alternates: { canonical: "/terms" },
};

const UPDATED = "2026-06-26";

export default function Terms() {
  return (
    <main className="mx-auto min-h-screen max-w-3xl bg-background px-6 py-16 text-foreground">
      <div className="mb-6 rounded-lg border border-warning/40 bg-warning/10 p-3 text-xs text-warning">
        Template pending legal review — have a SEBI-specialist lawyer finalise before public launch.
      </div>
      <h1 className="text-3xl font-bold">Terms &amp; Disclaimer</h1>
      <p className="mt-2 text-sm text-muted-foreground">Last updated {UPDATED}</p>

      <div className="mt-6 rounded-xl border border-border bg-card p-5">
        <h2 className="font-semibold">Important: educational analysis, not investment advice</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          SwingAI provides <b>deterministic technical analysis and educational tools</b>. Nothing on this platform is
          investment, trading, or financial advice, a recommendation, or a solicitation to buy or sell any security.
          We are not a SEBI-registered Research Analyst or Investment Adviser. Markets carry risk; you are solely
          responsible for your decisions. Past or backtested results do not guarantee future returns.
        </p>
      </div>

      <div className="mt-8 space-y-6 text-sm leading-relaxed text-muted-foreground">
        <section>
          <h2 className="text-lg font-semibold text-foreground">1. Eligibility &amp; account</h2>
          <p>You must be 18+ and provide accurate information. You’re responsible for your account and its activity.</p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">2. Paper trading only</h2>
          <p>Trades on SwingAI are simulated (“paper”) with real prices. We do <b>not</b> execute real orders or handle your funds.</p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">3. Subscriptions &amp; refunds</h2>
          <p>Paid plans renew per the interval shown. Free trials convert only if you choose to subscribe. Payments are handled by Razorpay. Refunds (if any) follow the policy stated at checkout.</p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">4. Acceptable use</h2>
          <p>No scraping, reverse-engineering, abuse, or unlawful use. We may suspend accounts that violate these terms.</p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">5. Liability</h2>
          <p>The service is provided “as is”. To the maximum extent permitted by law, we are not liable for trading losses or indirect damages.</p>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-foreground">6. Contact</h2>
          <p><b>support@swingai.in</b> (placeholder — replace before launch).</p>
        </section>
      </div>
    </main>
  );
}
