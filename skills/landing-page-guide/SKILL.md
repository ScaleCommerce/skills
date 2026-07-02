---
name: landing-page-guide
description: Build high-converting landing pages with proven conversion psychology and layout patterns (9% → 20%+ conversion rates). Use this skill whenever the user wants to create, build, or optimize a landing page, lead generation page, squeeze page, opt-in page, or any single-page conversion-focused experience. Also trigger when the user asks about landing page copywriting (headlines, CTAs, benefit statements), conversion rate optimization for a landing page, A/B testing landing page elements, landing page layout or structure advice, or improving an existing page's conversion rate. Covers the full workflow from strategy to code (Nuxt4 + NuxtUI) to deployment, including AI-generated visuals via OpenRouter. Even if the user doesn't say "landing page" explicitly — if they're describing a page whose primary goal is capturing leads, driving signups, or getting a single conversion action, this skill applies.
---

# Landing Page Guide — Nuxt Edition (v4.0)

High-converting landing pages follow proven patterns that can roughly double typical conversion rates. The core insight: **pages fail due to weak offers, not bad design.** Strong offer + clear messaging + minimal friction + psychology = high conversion.

**One page, one goal.** Every element drives toward a single conversion action. If it doesn't serve that goal, remove it.

You are building this page, not advising someone who will. Work through the phases in order: strategy inputs → copy → layout → build → verify. Don't write code before the strategy questions are answered.

---

## Phase 1: Strategy Inputs (Before Any Code)

Establish these five things — from the user's brief, their existing materials, or by asking. If the user can't answer, propose a concrete assumption and state it rather than silently defaulting:

1. **The offer** — what does the visitor get, and why is it worth their email/money *today*? A weak offer can't be fixed downstream.
2. **The one conversion action** — form submit, signup, booking, purchase. Exactly one.
3. **Audience & awareness stage** — see below; this determines page length and messaging.
4. **Traffic source** — ads, organic, email, social. Paid traffic requires message match.
5. **Available proof** — real testimonials, client logos, numbers, certifications. Never invent these; if none exist, ask, or design the page to work without them.

Where the audience's actual pain points are unknown, research them (communities, reviews, competitor pages) before writing copy — specific pains beat generic benefit claims.

### The 5 Awareness Stages (Determines Messaging)

Over-explaining bores aware visitors; under-explaining loses unaware ones.

1. **Completely Unaware** → problem education (longest copy)
2. **Problem Aware** → agitate the pain
3. **Solution Aware** → position why yours is best *(most B2B traffic)*
4. **Product Aware** → social proof + urgency
5. **Most Aware** → remove friction (shortest copy — just the CTA)

Free offers convert with short copy; paid offers need longer copy — the higher the commitment, the more justification required.

### Message Match (Critical for Paid Traffic)

The landing page must mirror the ad that brought the click — same headline, same offer, same tone. This creates an instant "I'm in the right place" feeling. Mismatched messaging is a top reason paid campaigns fail despite good landing pages. Ask for the ad copy if the page serves a campaign.

---

## Phase 2: Layout Blueprint

Guide the eye deliberately — headline and CTA where attention naturally lands, one visual hierarchy, no competing focal points. Most visitors never scroll past the hero, so it does most of the work.

### 1. Hero Section (Does 70% of the Heavy Lifting)

Everything above the fold scannable in one glance: headline, subheadline, one compelling visual, CTA.

- **Headline**: the transformation/result, not the feature — aim for under ~8 words
  - ✅ "Get 30% more leads in 60 days"
  - ❌ "Web design service"
- **Sub-headline**: how you deliver it (answers "how?") — "With our proven 7-step framework"
- **CTA button**: first-person, benefit-focused — "Send me the free guide", never "Submit"
- **Trust text under the form**: "We'll never share your info"
- **Social proof near the CTA**: third-party reviews with star ratings, placed at the decision moment
- **Image**: show people experiencing the *result*, not just the product
- **NO navigation menu** — every link is a leak; remove exit paths

### 2. Benefits Bar (Features → Benefits)

List what features DO for the customer, leading with the benefit:
- ❌ "Customizable ingredients" → ✅ "Your dog stays healthy"

Use 3 benefits with icons — groups of three read naturally, and an icon makes each one far more likely to be scanned.

### 3. Testimonials (Grouped in 3s)

Social proof reliably lifts conversions when it's credible:
- Short (1–2 sentences), real photo + full name + job title, star ratings
- Choose testimonials showing **specific results** or **overcoming objections**
- Place high on the page AND again near CTAs
- Only real testimonials — fabricated proof is both unethical and (in the EU) illegal

### 4. Problem-Agitation (Only for Problem-Aware Traffic)

Paint the problem vividly, list symptoms, show the cost of inaction. Loss aversion: losing feels ~2x stronger than gaining.
- ❌ "You'll gain efficiency" → ✅ "Every day without this, you're losing 3 hours"

### 5. Open Loops (If Lead Magnet)

Tease without revealing — curiosity resolved only by converting: "Discover the 3 things NOT to put on your website (if you have them, you're losing leads)."

### 6. Trust Badges & Risk Reversal

Security badges, certifications, partner/client logos, press mentions — and a guarantee with specific terms ("30-day full refund, no questions asked"). Risk reversal shifts perceived risk from buyer to seller.

### 7. FAQ / Objection Handling

Remove final objections. Add FAQ schema (JSON-LD) — improves visibility in search and AI assistants:

```vue
<script setup>
useHead({
  script: [{
    type: 'application/ld+json',
    innerHTML: JSON.stringify({
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": faqs.map(faq => ({
        "@type": "Question",
        "name": faq.question,
        "acceptedAnswer": { "@type": "Answer", "text": faq.answer }
      }))
    })
  }]
})
</script>
```

### 8. Final CTA

Same action as the hero, with a benefit restatement. Whoever scrolled this far is interested — remove the last hesitation.

---

## Phase 3: Copy Rules

- **8th-grade reading level**, 15–20 word sentences, active voice
- **First-person CTAs** ("Book my consultation") consistently outperform generic ones in published tests; low-commitment verbs ("Try", "See") outperform high-commitment ones ("Sign up")
- **Form fields**: ≤4, ideally name + email. Every extra field costs conversions — gather the rest post-conversion. Multi-step forms can beat single-step despite more total fields: easy questions first build momentum
- **No AI-copy register**: no "Empower/Unlock/Transform", no "Seamless Integration", at least one concrete claim with real numbers or names (see the frontend-design skill's writing section — it applies to landing page copy fully)
- **CTA contrast**: the button color must pop against the palette; repeat the CTA at least twice on the page

### Conversion Psychology Toolkit

| Principle | What It Is | How to Apply |
|-----------|-----------|-------------|
| **Loss Aversion** | Losing feels 2x worse than gaining | Frame as "stop losing X", not just "gain X" |
| **Social Proof** | We follow what others do | Testimonials, user counts, logos near CTAs |
| **Cognitive Fluency** | Simple = trustworthy | Clean design, plain language, whitespace |
| **Anchoring** | First number sets the reference | Original price before discount; competitor costs |
| **Reciprocity** | Give before asking | Free guide/tool/audit before requesting email |
| **Scarcity** | Limited = valuable | Genuine deadlines only — fake urgency destroys trust and is illegal in the EU |
| **Risk Reversal** | Remove buyer risk | Guarantees, free trials, "cancel anytime" |

---

## Phase 4: Build (Nuxt 4 + Nuxt UI)

Use **Nuxt 4 with @nuxt/ui v4**. If the `nuxt-ui` skill is available, consult it for components, forms, and theming. For the visual design itself — typography, palette, distinctive aesthetics — apply the **frontend-design** skill: a landing page must convert, but a page that looks like every AI-generated template undermines the trust the conversion depends on. The conversion layout rules in this skill win wherever the two conflict (e.g., hero clarity beats artistic ambiguity).

```vue
<!-- Mobile-optimized CTA: full-width in the thumb zone on mobile -->
<UButton size="xl" block class="sm:w-auto sm:inline-flex" label="Send Me the Free Guide" />
```

**Form handling essentials:**
- Honeypot field or similar spam protection on every public form
- Client + server validation; specific, helpful error messages
- Redirect to a **thank-you page** after submit — it's the cleanest conversion-tracking trigger and prime real estate for a next step (calendar booking, share, upsell)
- Wire the form to the CRM/email tool via webhook (e.g. Make, n8n, GoHighLevel) for follow-up sequences

### Compliance (Non-Negotiable for EU/DACH Traffic)

Lead capture in the EU has legal requirements — a non-compliant page is a liability regardless of conversion rate:

- **Double opt-in for email marketing**: form submit → confirmation email → only after the click is the address added to the list. Effectively mandatory in Germany (UWG case law), best practice EU-wide. Store timestamp + IP of consent.
- **Unticked consent checkbox** with specific wording about what the user consents to. Pre-checked boxes are illegal (Planet49 ruling). A privacy-policy link alone is not sufficient for marketing consent.
- **Legal links**: privacy policy (Datenschutzerklärung) and — for DACH — Impressum, reachable from the page. Exception: these footer links are allowed despite the "no navigation" rule.
- **Cookie consent** only if you actually set tracking cookies — prefer cookieless/consent-free analytics on landing pages to keep friction zero.
- **Real proof only**: fabricated testimonials and fake urgency violate EU consumer protection law (and destroy trust).

### Mobile (Most of Your Traffic)

Mobile is >80% of traffic but converts 40–51% worse than desktop — closing that gap is the highest-leverage optimization:

- Touch targets ≥ 48×48dp, ≥8dp spacing between interactive elements
- CTAs in the natural thumb zone (bottom-center), full-width buttons on mobile
- Body text ≥16px — readable without zoom
- Design mobile-first; verify on a real phone, not just a resized browser

### Performance (Core Web Vitals)

Slow pages bleed conversions — sites loading in ~1s convert several times better than ones loading in 5s. Target Google's "Good" thresholds:

- **LCP < 2.5s** — compress hero images (WebP/AVIF), preload the LCP image, use a CDN
- **INP < 200ms** — minimize JS bundles, defer non-essential scripts (the most commonly failed vital)
- **CLS < 0.1** — set width/height on images, reserve space for late-loading embeds/fonts

Checklist: WebP/AVIF images + lazy-load below the fold · ≤2 font families, preloaded · critical CSS inline · `nuxi analyze` for bundle issues · Lighthouse ≥90 after deploy.

---

## Phase 5: Visuals

For hero images, benefit graphics, and mockups, use the **nano-banana** skill (image generation via OpenRouter):

- Describe the scene from the customer's perspective — person experiencing the transformation, not a product floating in space
- Specify brand style and palette; avoid generic stock-photo aesthetics
- 16:9 for hero images; request "no text in image" — overlay text in code
- Generate 2–3 variants and pick against the page's aesthetic direction

---

## Phase 6: Verify & Launch

Before calling it done:

- [ ] Submit the form end-to-end: validation, spam protection, webhook delivery, double-opt-in email, thank-you page
- [ ] Conversion event fires on the thank-you page (analytics + ad platform if paid traffic)
- [ ] Real-phone check: thumb-zone CTA, no zoom needed, nothing clipped
- [ ] Lighthouse ≥90 performance; LCP/INP/CLS in "Good" range
- [ ] Message match against the actual ad copy (paid traffic)
- [ ] Legal links present and correct; consent checkbox unticked
- [ ] Every element serves the one conversion goal — remove anything that doesn't

---

## A/B Testing Priorities

Test in this order (highest impact first):

1. **Headline** — the biggest lever on the page
2. **CTA text + color** — easiest to test, often significant
3. **Hero image** — contextual image vs. stock photo
4. **Form fields** — count, single vs. multi-step
5. **Social proof placement** — above fold vs. near CTA vs. both
6. **Page length** — short vs. long (depends on offer)

**Methodology**: one element at a time · ~1,000 weekly visitors minimum for validity · run 2–4 weeks (no peeking) · prioritize by ICE score (Impact × Confidence × Ease) · below 1,000 weekly visitors, apply proven practices instead of testing.

---

## Post-Launch: Beyond Conversion Rate

**Lead quality scoring (B2B)**: score title seniority, company-size match, and intent signals (visited pricing); high scores get immediate follow-up, mid scores a nurture sequence. A page converting 15% high-quality leads beats one converting 25% junk.

**Revenue attribution**: UTM parameters on all traffic sources, mapped through the full sales cycle.

---

## Key Principles

1. **Offer strength > design** — a strong offer on an ugly page beats a beautiful page with a weak offer
2. **Message match** — mirror the ad/source that brought the visitor
3. **Match awareness stage** — don't over-explain to people who already know
4. **Minimize friction** — every field, link, and choice costs conversions
5. **Use psychology** — loss aversion, social proof, risk reversal, reciprocity, genuine scarcity
6. **Mobile-first** — most traffic, worst conversion; close the gap
7. **Speed is conversion** — Core Web Vitals in the "Good" range, always
8. **Compliant by default** — double opt-in, honest proof, legal links; a lead you can't legally email is worthless
9. **Test, don't guess** — headlines first, then CTAs, then everything else
10. **Verify end-to-end** — a broken form on a perfect page converts at exactly 0%
