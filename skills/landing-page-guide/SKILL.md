---
name: landing-page-guide
description: Build high-converting landing pages with proven conversion psychology and layout patterns (9% → 20%+ conversion rates). Use this skill whenever the user wants to create, build, or optimize a landing page, lead generation page, squeeze page, opt-in page, or any single-page conversion-focused experience. Also trigger when the user asks about landing page copywriting (headlines, CTAs, benefit statements), conversion rate optimization for a landing page, A/B testing landing page elements, landing page layout or structure advice, or improving an existing page's conversion rate. Covers the full workflow from strategy to code (Nuxt4 + NuxtUI) to deployment, including AI-generated visuals via OpenRouter. Even if the user doesn't say "landing page" explicitly — if they're describing a page whose primary goal is capturing leads, driving signups, or getting a single conversion action, this skill applies.
tags:
  - landing-pages
  - conversion-optimization
  - nuxt
  - nuxtui
  - ai-assisted-development
  - lead-generation
  - sales-funnels
version: 3.0
---

# Landing Page Guide - Nuxt Edition (v3.0)

## Overview
Based on testing 300+ landing pages, high-converting pages follow proven patterns that double average conversion rates (9% → 20%+).

**Critical Insight**: Pages fail due to weak offers, not bad design. Strong offer + clear messaging + minimal friction + psychology = high conversion.

**One Page, One Goal**: Every element on the page should drive toward a single conversion action. If it doesn't serve that goal, remove it.

---

## The 5 Customer Awareness Stages (Determines Your Messaging)

Match your messaging to where the visitor is in their journey — over-explaining to aware visitors bores them; under-explaining to unaware visitors confuses them.

1. **Completely Unaware** → Problem education (longest copy needed)
2. **Problem Aware** → Agitate the pain
3. **Solution Aware** → Position why yours is best *(most B2B traffic)*
4. **Product Aware** → Social proof + urgency
5. **Most Aware** → Remove friction (shortest copy — just the CTA)

---

## Message Match (Critical for Paid Traffic)

The landing page must mirror the ad that brought the click — same headline, same offer, same tone. This creates an instant "I'm in the right place" feeling that lowers bounce rate. Mismatched messaging is one of the top reasons paid campaigns fail despite good landing pages.

---

## Proven Landing Page Layout (20%+ Conversions)

Use a **Z-pattern visual hierarchy** — visitors scan top-left → top-right → diagonal to bottom-left → bottom-right. Place your headline top-left, logo/trust marks top-right, supporting content mid-page, and CTA bottom-right. This naturally guides attention toward conversion.

### 1. Hero Section (Does 70% of Heavy Lifting)

**Rule**: 80% of visitors never scroll past this. If they don't find what they need here, they leave.

Everything above the fold must be scannable in a single glance: headline, subheadline, one compelling visual, and CTA.

- **Headline**: The transformation/result (not feature) — optimal length is **under 8 words / 44 characters**
  - ✅ "Get 30% more leads in 60 days"
  - ❌ "Web design service"
- **Sub-headline**: How you deliver it (answers "how?")
  - ✅ "With our proven 7-step framework"
- **CTA button text** using "my/me" words (personalized CTAs = 202% better)
  - ✅ "Send me the free guide"
  - ❌ "Get started" / "Submit"
- **Trust text under form**
  - "We'll never share your info" = +7% conversions
- **Social proof**: Third-party reviews with star count — place near CTA to nudge at decision moment
- **Image**: Show people using/enjoying the result (not just the product) — images process 60,000x faster than text
- **NO navigation menu** (removes exit paths — every link is a leak)

### 2. Benefits Bar (Features → Benefits)

Don't list features. List what those features DO for the customer. Structure as "Feature → Benefit" pairs, always leading with the benefit.

- ❌ "Customizable ingredients"
- ✅ "Your dog stays healthy"

Add icons/graphics with each benefit (80% greater chance of being read). Use 3 benefits maximum — the brain processes groups of 3 naturally.

### 3-4. Testimonials (Grouped in 3s)

Social proof delivers a **19–34% conversion lift** when done right:
- Keep short (1-2 sentences)
- Use person's actual photo + full name + job title
- Include 5-star ratings
- Choose testimonials that show **specific results** OR **overcome objections**
- Place both high on the page AND again near CTAs

### 5. Problem-Agitation (Only if Problem Aware traffic)

Paint the problem vividly, list symptoms, show the cost of inaction. Use loss aversion — the pain of losing something feels ~2x stronger than the pleasure of gaining something equivalent.

- ❌ "You'll gain efficiency"
- ✅ "Every day without this, you're losing 3 hours of productive time"

### 6. Open Loops (If lead magnet)

Tease information without revealing it all — creates curiosity that can only be resolved by converting.

Example: "Discover the 3 things NOT to put on your website (and if you have them, you're losing leads)"

### 7. Trust Badges & Risk Reversal

Go beyond just trust text. Include:
- Security badges (SSL, payment processor logos)
- Industry certifications or partner logos
- Money-back guarantee with specific terms ("30-day full refund, no questions asked")
- Client logos / "as seen in" press mentions

Risk reversal is powerful because it shifts the perceived risk from buyer to seller.

### 8. FAQ / Objection Handling

Remove final buying objections. Use FAQ schema markup (JSON-LD) — this also improves visibility in AI search results and voice assistants (AEO-friendly).

```vue
<script setup>
// Add FAQ schema for SEO + AEO
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

### 9. Final CTA

Same call-to-action as hero, with a benefit restatement. Visitors who scroll this far are interested — remove any remaining hesitation.

---

## Conversion Psychology Toolkit

These principles should inform every element on the page:

| Principle | What It Is | How to Apply |
|-----------|-----------|-------------|
| **Loss Aversion** | Losing feels 2x worse than gaining | Frame benefits as "stop losing X" not just "gain X" |
| **Social Proof** | We follow what others do | Testimonials, user counts, client logos near CTAs |
| **Cognitive Fluency** | Simple = trustworthy | Clean design, 8th-grade reading, ample whitespace |
| **Anchoring** | First number sets the reference | Show original price before discount; show competitor costs |
| **Reciprocity** | Give before asking | Free guide/tool/audit before requesting email |
| **Scarcity** | Limited = valuable | Genuine deadlines, limited spots (never fake urgency) |
| **Risk Reversal** | Remove buyer risk | Guarantees, free trials, "cancel anytime" |

---

## Micro-Conversions That Matter

**CTA Button Text**: Personalized CTAs = 202% better
- ✅ "Send me the free guide", "Book my consultation"
- ❌ "Submit", "Contact us"
- Changing "Sign up for free" → "Trial for free" = **104% increase** ("trial" implies temporary evaluation, lowering commitment)

**Form Fields**: ≤4 fields is optimal (reducing from 11→4 fields = **160% lift**)
- Name + email is usually enough at conversion
- Gather additional data post-conversion or during onboarding
- **Multi-step forms**: Progressive disclosure can increase conversions despite more total fields — easy questions first build momentum

**Copy**: 8th-grade reading level, 15-20 word sentences, active voice
- **Free offers** → short copy works better
- **Paid offers** → longer copy performs better (more money = more copy needed to justify)

**Visual Contrast**: CTA buttons must visually pop — use a color that contrasts with the page palette. Repeat the CTA at least 2x on the page.

---

## Mobile Optimization (Critical — 83% of Traffic)

Mobile converts 40-51% worse than desktop. Closing this gap is one of the highest-impact optimizations:

- **Touch targets**: Minimum 48×48dp for buttons/form fields, 8dp spacing between interactive elements
- **Page speed**: Target sub-2-second load. Every 0.1s improvement = 8-10% conversion lift. 53% of mobile users abandon after 3 seconds
  - Compress images (WebP format, lazy loading)
  - Minimize JavaScript bundles
  - Use a CDN
- **Design mobile-first**: Test on actual phones, not just browser resize
- **Thumb-friendly**: Place CTAs in the natural thumb zone (bottom-center of screen)
- **Readable without zoom**: Minimum 16px body text

```vue
<!-- Nuxt/NuxtUI mobile-optimized CTA example -->
<UButton
  size="xl"
  block
  class="sm:w-auto sm:inline-flex"
  label="Send Me the Free Guide"
/>
```

---

## Page Speed Checklist

Speed directly impacts conversions — you lose ~7% of conversions for every additional second of load time.

- [ ] Images: WebP format, compressed, lazy-loaded below fold
- [ ] Fonts: Preload critical fonts, limit to 2 families
- [ ] CSS: Inline critical CSS, defer non-critical
- [ ] JS: Minimize bundles, defer non-essential scripts
- [ ] CDN: Serve assets from edge locations
- [ ] Target: < 2s on mobile, < 1.5s on desktop

In Nuxt, use `nuxi analyze` to identify bundle size issues.

---

## A/B Testing Priorities

Test in this order (highest impact first, top-down on the page):

1. **Headline** — 27-104% conversion lift potential
2. **CTA text + color** — Easiest to test, often significant impact
3. **Hero image** — Relevant image vs. stock photo = up to 27% lift
4. **Form fields** — Reduce count, test multi-step vs. single
5. **Social proof placement** — Above fold vs. near CTA vs. both
6. **Page length** — Short vs. long (depends on offer type)

**Methodology**:
- Test ONE element at a time
- Need minimum ~1,000 weekly visitors for statistical validity
- Run tests 2-4 weeks minimum (avoid peeking bias)
- Use ICE scoring: **I**mpact × **C**onfidence × **E**ase → test highest score first
- < 1,000 weekly visitors? Apply proven practices first, test later

---

## AI-Assisted Development Workflow

Build landing pages 10x faster using Claude/Gemini with the 3D Framework:

### Design → Data → Deploy

#### Phase 1: Design (Generate beautiful Nuxt + NuxtUI code)
**Input**: Design references + brand guidelines

**Prompting**:
1. Provide 3-5 design code samples (HTML, not just screenshots)
2. Include brand guidelines (fonts, colors, logo)
3. Specify sections (hero, benefits, testimonials, CTA, form)
4. Request specific effects (animations, spacing, interactions)

**Example**:
```
Build Nuxt 3 landing page with NuxtUI:
- Hero: animated gradient + cosmic blue background, Z-pattern layout
- Benefits: 3 sections with icons addressing [pain points]
- Testimonials: 3 with photos + 5-star ratings + job titles
- Trust bar: client logos + security badges
- Form: email + name only (multi-step if qualifying needed)
- CTA: benefit-focused "Send me..." — high contrast button
- Mobile-first, sub-2s load target

Design references: [include HTML code from inspiring sites]
Brand: [colors], [fonts], [logo description]
```

#### Phase 2: Data (Optimize copy for target audience + integrate CRM)
**Pre-step**: Research top 3-5 pain points from Reddit/communities

**Prompting** (Use extended thinking mode):
```
Target avatar: [industry, revenue, challenges]
Awareness stage: [unaware / problem-aware / solution-aware / product-aware / most-aware]
Traffic source: [Google Ads / Facebook / organic / email] (for message match)
Pain points:
1. [specific problem]
2. [specific problem]
3. [specific problem]

Please:
1. Value-based hero headline (benefit, not feature — under 8 words)
2. Rewrite 3 benefit sections (one per pain point, use loss aversion framing)
3. Form field recommendations (minimum viable for conversion)
4. 3 CTA button text variations (benefit-focused, first-person)
5. Trust message under form
6. FAQ addressing top 3 objections (with schema markup)
7. Social proof placement strategy

Sell transformation, not mechanism.
Write at 8th-grade reading level, active voice, 15-20 word sentences max.
```

**CRM Integration**: Connect form via webhook to GoHighLevel/Make for email sequences

#### Phase 3: Deploy
Pipeline: Code → GitHub → Vercel → Live site
- Claude commits changes
- Vercel auto-deploys
- Test on actual mobile device (not just browser resize)
- Run Lighthouse audit: target 90+ Performance score
- Iterate based on visual feedback + analytics

#### Visual & Image Generation (Gemini 3.1 Flash + OpenRouter)

For landing page visuals (hero images, benefit graphics, mockups):

**Primary**: Use **Gemini 3.1 Flash Image Preview** model
- Fast, high-quality image generation
- Excellent for visual iteration

**Setup**:
1. Check for environment variable: `OPENROUTER_API_KEY`
2. **If set**: Use OpenRouter (unified API supporting Gemini, Midjourney, DALL-E)
   ```javascript
   const imageResponse = await fetch("https://openrouter.ai/api/v1/images/generations", {
     method: "POST",
     headers: {
       "Authorization": `Bearer ${process.env.OPENROUTER_API_KEY}`,
       "Content-Type": "application/json"
     },
     body: JSON.stringify({
       model: "google/gemini-3.1-flash-image-preview",
       prompt: "Your detailed image prompt",
       width: 1600,
       height: 900
     })
   });
   ```
3. **If not set**: Fall back to alternative image generation APIs (Unsplash API, stock photos, or manual generation)

**Prompting Visuals**:
```
"Generate a landing page hero image:
- Show [description: person using product, result transformation]
- Style: [brand style - minimalist/bold/organic]
- Color palette: [primary: #color, secondary: #color]
- Aspect ratio: 16:9
- Real-world context, customer perspective (not product focus)
- No text in image (we'll overlay text in code)"
```

### Key Prompting Rules

**Do This**:
- ✅ Provide actual code samples (not descriptions)
- ✅ Research audience pain points first
- ✅ Use extended thinking for strategy
- ✅ Test generated code on actual mobile devices
- ✅ Iterate with visual feedback
- ✅ Generate visuals with brand context (not generic)
- ✅ Run Lighthouse after deploy

**Don't Do This**:
- ❌ Generic "build a landing page" requests
- ❌ Skip audience research
- ❌ Add form fields without justification
- ❌ Assume AI knows your brand/positioning
- ❌ Generate images without style/context guidance
- ❌ Skip mobile testing

---

## Post-Launch: Beyond Conversion Rate

Track more than just conversion rate to understand true performance:

**Lead Quality Scoring** (for B2B):
- VP/C-level title: +15 points
- Target company size match: +8 points
- Purchase intent signals (visited pricing): +10 points
- Score 40+ = immediate follow-up; 20-39 = nurture sequence

**Revenue Attribution**: Map leads through the full sales cycle with UTM parameters. A page with 15% conversion of high-quality leads beats 25% conversion of junk leads.

---

## Key Principles

1. **Offer strength > Design** — Strong offer on ugly page beats beautiful page with weak offer
2. **Message match** — Mirror the ad/source that brought the visitor
3. **Match awareness stage** — Don't over-explain to people who already know
4. **Minimize friction** — Every field, link, and choice reduces conversions
5. **Use psychology** — Loss aversion, social proof, risk reversal, reciprocity, scarcity
6. **Mobile-first** — 83% of traffic, 40-51% worse conversion — close the gap
7. **Speed kills (slowness kills more)** — Sub-2s load, every 0.1s = 8-10% lift
8. **Simple > Complex** — Every element must serve the single conversion goal
9. **Test, don't guess** — A/B test headlines first, then CTAs, then everything else
10. **AI speeds execution** — But strategy + psychology determine success
