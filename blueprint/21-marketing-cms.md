# 21 — Marketing Website CMS (Dynamic, Admin-Controlled)

> 🧭 **Status:** 📝 Spec · **Tier:** 🏆 Best-in-class (design) → **Target: 🏆 Best-in-class** · **Phase 1→2** · live tracker: [STATUS.md](./STATUS.md) <!--STATUS-BADGE-->

> **Context:** The public marketing website (landing, feature pages, pricing, about, blog, stock/sector SEO pages) must be **fully controllable by the Super Admin** — edit content, SEO, testimonials, stats, categories, navigation, and **create new pages dynamically** — with everything **seeded on first boot** and editable thereafter. This doc defines that CMS: the content model, how it stays SEO-strong (the critical part), the admin editing experience, seeding, versioning, and the honest build-vs-buy decision. All content is **DB-driven, rendered server-side, no hardcoded marketing copy.**

---

## 1. Honest verdict & the 3 guardrails

Dynamic + admin-controlled is the right approach **only with these guardrails** (violate them and it backfires):

1. **Render server-side (SSR/ISR), never client-fetch.** Marketing content lives in the DB but is rendered by **server components / ISR** so Google and AI crawlers see full HTML. **On-demand revalidation** refreshes a page the instant admin publishes. Client-side-fetched marketing content = invisible to SEO = the whole point lost.
2. **Block/section content model, not freeform HTML.** Admin composes pages from **typed blocks** (Hero, Features, Testimonials, Stats, FAQ, CTA, Pricing, RichText, Media). Consistent, on-brand, responsive, dark/light-aware, animated, and XSS-safe. No blank HTML boxes.
3. **Seed-then-edit, and don't over-build.** Ship **real seeded content** so the site works on first run; ship a focused block set + per-page SEO first; expand later. Keep scope honest — this competes for time with proving the trading edge (the real #1 risk, doc 12 R1).

---

## 2. Build vs buy (honest)

| Option | Pros | Cons | When |
|---|---|---|---|
| **Custom DB-backed CMS** (this doc) | Full control, one stack, matches admin plane (doc 16), no extra vendor | You build/maintain the editor, versioning, media | If you want everything in-platform and have the OmniMark patterns to reuse |
| **Headless CMS — Payload** (self-host, Postgres, React admin) | Mature admin, versioning/drafts/preview built-in, blocks, access control; saves weeks | Another system to run; some lock-in | **Recommended to evaluate** — could replace half this doc's effort |
| **Sanity / Strapi / Contentful** | Hosted, fast start | SaaS cost, content lives outside your DB | If you want zero CMS maintenance |

**Recommendation:** if reusing OmniMark's existing CMS code, go **custom** (this doc). Otherwise seriously evaluate **Payload** before hand-building — it gives blocks, drafts, versioning, and a polished admin for free. Either way, the **content model (§3), SEO model (§5), and rendering rules (§4) below are the same.**

---

## 3. Content model (the data — see doc 06 for tables)

Typed, block-based, locale-aware, versioned:

```
cms_pages            -- slug, title, type(landing/feature/pricing/about/custom),
                     --   status(draft/published), locale, seo_meta_id, published_version_id,
                     --   nav_visible, sort_order, created/updated_by
cms_sections         -- page_id, block_type(hero/features/testimonials/stats/faq/cta/pricing/richtext/media),
                     --   sort_order, content(jsonb: typed per block_type), is_enabled, locale
content_categories   -- slug, name, description, parent_id, sort_order, seo_meta_id   (dynamic categories)
content_items        -- category_id, slug, title, body(jsonb/richtext), media, status, seo_meta_id, locale
testimonials         -- author_name, role, company, avatar_media_id, quote, rating, is_featured, sort_order, locale
stats_metrics        -- key, label, value, suffix, source, is_live(bool), sort_order, locale
                     --   (is_live → pull real number from backend, e.g. users count, track-record win% — doc 20)
faqs                 -- category, question, answer(richtext), sort_order, locale
navigation_menus     -- location(header/footer), items(jsonb: label/href/children), locale
media_assets         -- url, type, alt_text, width/height, uploaded_by   (media library)
seo_meta             -- owner_type/owner_id, title, description, canonical, og(jsonb), twitter(jsonb),
                     --   json_ld(jsonb), robots, keywords, hreflang(jsonb)
content_versions     -- owner_type/owner_id, snapshot(jsonb), version_no, created_by, created_at, note
                     --   (draft/publish history + rollback for ANY editable content)
```

- **Block content is typed JSON** per `block_type` (a Hero has heading/subheading/cta/media; Stats references `stats_metrics`; Testimonials selects featured ones). Validated by schema so admin can't break layout.
- **Everything is locale-aware** (doc 15) — content authored per language; falls back to default locale if a translation is missing.
- **`stats_metrics.is_live`** lets a stat pull a *real* number (e.g. "₹X tracked", "N users", honest track-record win%) from the backend — no fake numbers (doc 00 #2, doc 20).

---

## 4. Rendering & SEO performance (the critical part)

- Marketing routes (`/[locale]/...`, doc 08) render via **server components + ISR**. A `BlockRenderer` maps each `cms_section.block_type` → a themed, animated React component (doc 14).
- **On-demand revalidation:** when admin publishes a page, the backend triggers Next.js revalidation for that path (revalidate tag/path) → live within seconds, no redeploy.
- **Draft preview:** admins view unpublished drafts via a preview route (token-gated, `noindex`) before publishing.
- Blocks are **responsive + dark/light/system + animated** out of the box (doc 14) — admin picks content, not styling, so the site can't go off-brand or break on mobile.
- Public reads come from cache (Redis/ISR); admin writes invalidate the relevant cache/path.

---

## 5. SEO & AI-LLM control (per page, admin-editable)

This is the genuinely high-value part — fully editable from the panel (`seo_meta` per page/category/item):

- **Core meta:** title, meta description, canonical URL, robots (index/noindex), keywords.
- **Social:** Open Graph + Twitter card (title, description, image) per page.
- **Structured data (JSON-LD):** editable per page (Organization, Product, FAQPage, Article, BreadcrumbList…). This is what makes **Google rich results** AND lets **ChatGPT/Perplexity/Claude cite you** with clean facts.
- **Sitemap.xml** auto-generated from published pages/categories/items; **robots.txt** managed.
- **hreflang** emitted from locale variants (doc 15) so the right language ranks.
- **AI-LLM optimization:** clean semantic HTML, factual structured data, and an optional **`llms.txt`** / AI-friendly summary endpoint describing the platform + honest track record for LLM ingestion.
- `generateMetadata()` in Next reads `seo_meta` server-side per page — no hardcoded meta tags anywhere.

---

## 6. Admin experience (full-page, per doc 16)

Under `/admin/marketing/*` (RBAC-gated, full pages, never dialogs — doc 16):

```
/admin/marketing/pages              → list all pages; create new page (slug + template)
/admin/marketing/pages/[id]         → block composer: add/reorder/edit/enable blocks (full page)
/admin/marketing/pages/[id]/seo     → per-page SEO + JSON-LD editor (full page)
/admin/marketing/pages/[id]/preview → live draft preview before publish
/admin/marketing/categories         → manage dynamic categories + their content
/admin/marketing/testimonials       → CRUD testimonials, feature/order
/admin/marketing/stats              → CRUD stat tiles (static or live-bound)
/admin/marketing/faqs               → CRUD FAQs
/admin/marketing/navigation         → header/footer menu builder
/admin/marketing/media              → media library (upload, alt text)
/admin/marketing/seo-defaults       → site-wide SEO defaults, sitemap/robots, llms.txt
```

- **Block composer:** drag-reorder sections (**@hello-pangea/dnd**), edit typed fields, rich text via **TipTap** (reused from OmniMark — doc OMNIMARK-REUSE), toggle visibility, **live preview**, then **publish** (writes a `content_version`).
- **Versioning + rollback:** every publish snapshots to `content_versions`; admin can diff and **roll back** a bad edit (protects the live site).
- **Dynamic pages:** create a new page with a slug + starting template; it's instantly routable and SEO-managed.
- **Audit-logged** (doc 18); role-gated (doc 19); content **sanitized** server-side.

---

## 7. Seeding (works on first boot, editable forever)

- A **seed migration** populates real default content: landing page (hero/features/stats/testimonials/CTA), pricing, about, FAQ, header/footer nav, and sensible SEO defaults + JSON-LD.
- Seeds are **realistic, on-brand, honest** (no "guaranteed profit" copy — doc 09 framing) so the site is launch-ready day one.
- After first boot, **Super Admin can change/replace/extend everything** and add new pages — the seed is just the starting state, never hardcoded into components.
- Re-running seeds is idempotent (won't clobber admin edits — seed only if empty / explicit reseed).

---

## 8. Security & integrity

- All marketing-admin routes RBAC-gated (`content.manage`, doc 19); every change audit-logged (doc 18).
- **Block content validated** against per-type schemas; rich text sanitized (no raw script injection).
- Versioning gives rollback; draft/publish prevents accidental live breakage.
- Media uploads validated (type/size), served via CDN.
- Live-bound stats read real backend numbers — **honest, not fabricated** (doc 00 #2).

---

## 9. Phase evolution

| Phase | Deliverable |
|---|---|
| 1 | Content model + **seeded** landing/pricing/about, core blocks (hero/features/stats/testimonials/CTA/FAQ), per-page SEO + JSON-LD, ISR rendering + on-demand revalidation, basic admin editors, sitemap/robots |
| 2 | Block composer with drag-reorder + live preview, versioning/rollback, dynamic page creation, categories + content items, media library, nav builder, hreflang at scale |
| 3 | A/B testing of blocks, scheduled publish, advanced JSON-LD templates, `llms.txt` + AI-citation tuning, multi-locale content workflows, (optional) migrate to/ from Payload |
| Future | Visual page builder, personalization, content recommendations |

---

*Next: [`HOW-TO-BUILD.md`](./HOW-TO-BUILD.md) — build order and the resume prompt. Back to the [README index](./README.md).*
