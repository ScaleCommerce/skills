---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build or restyle web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React/Vue components, HTML/CSS layouts), when they ask to theme, polish, or "make this look better", and when new UI has to sit inside an existing brand or design system. Generates creative, polished code and UI design that avoids generic AI aesthetics.
license: Adapted from the frontend-design skill in anthropics/skills (Apache 2.0) — https://github.com/anthropics/skills/tree/main/skills/frontend-design
---

# Frontend Design

Approach this as the design lead at a small studio known for giving every client a visual identity that could not be mistaken for anyone else's. This client has already rejected proposals that felt templated, and is paying for a distinctive point of view: make deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, and take one real aesthetic risk you can justify.

## Read the Room Before Designing Anything

**Find out whether a visual language already exists.** Inside an existing codebase it almost always does, and inventing a second one is a bug, not a point of view. Before writing any CSS, look for: a Tailwind `@theme` block or config, CSS custom properties, a UI framework config (`app.config.ts`, shadcn `components.json`, theme providers), existing components that solve the same problem, and any `DESIGN.md` / `BRAND.md` / style guide. If the project has tokens, use them by name — do not restate their values as literals, and do not add a parallel scale.

That constraint doesn't cancel the brief; it relocates the budget. When the palette and component vocabulary are given, distinctiveness has to come from composition, type detail, density, motion, and the one signature moment — which is harder and usually better than a new set of colors.

**Ask for real material when the subject is real.** A logo, product screenshots, real copy, a live URL, or an existing page to match beats anything invented. If the brief names a real product, company, or version you are not certain about, check before designing around a wrong premise.

## Ground It in the Subject

If the brief does not pin down what the product or subject is, pin it yourself before designing: name one concrete subject, its audience, and the page's single job, and state your choice. If there's any information available about the user's preferences, what they're building, or designs made before — use that as a hint. The subject's own world — its materials, instruments, artifacts, and vernacular — is where distinctive choices come from. Build with the brief's real content and subject matter throughout.

## Commit to a Direction

Choose a clear conceptual direction and execute it vigorously. There are infinite starting points: brutally minimal, maximalist chaos, luxury/refined, lo-fi/zine, dark/moody, soft/pastel, editorial/magazine, brutalist/raw, retro-futuristic, handcrafted/artisanal, organic/natural, art deco/geometric, playful/whimsical, industrial/utilitarian. Use these as inspiration, but the final design should feel singular, with every detail working in service of one cohesive direction. Ask: what makes this UNFORGETTABLE? What's the one thing someone will remember?

Bold maximalism and refined minimalism both work — the key is intentionality, not intensity.

## Design Principles

**The hero is a thesis.** Open with the most characteristic thing in the subject's world, in whatever form makes sense for it: a headline, an image, an animation, a live demo, an interactive moment. A big number with a small label, supporting stats, and a gradient accent is the template answer — only use it if it's truly the best option.

**Typography carries the personality of the page.** Pair the display and body faces deliberately — not the same families you would reach for on any other project. Default fonts signal default thinking: skip Arial, Inter, Roboto, Open Sans, Lato, Space Grotesk, and system stacks.

- **Pair across an axis**, so the contrast means something: display serif + geometric sans, grotesque + monospace, one variable face worked across its full range.
- **Use extremes.** Weight 100/200 against 800/900, not 400 against 600. Size jumps of 3× or more, not 1.5×. Then let optical detail carry the rest: tracking tightened on display sizes, measure held near 60–75 characters, line-height loosened as text gets smaller.
- **A font you can't load is a font you didn't choose.** Verify the source before naming it: Google Fonts (Fraunces, Newsreader, Bricolage Grotesque, Instrument Serif, EB Garamond, Playfair Display, Crimson Pro, Literata, Syne, Archivo, Sora, IBM Plex, Source Sans 3, JetBrains Mono, Fira Code) and Fontshare (Satoshi, Clash Display, Cabinet Grotesk, Switzer, General Sans, Gambetta, Zodiak, Sentient) are free and self-hostable. Faces from commercial foundries — Söhne, Tiempos, Domaine, GT Sectra, Untitled Sans, Obviously — will silently fall back to something generic and quietly undo the design. Always declare a real fallback stack and `font-display: swap`.
- Treat the names above as a floor, not a menu: they are the faces every model reaches for. One step further into the subject's own type world is usually the better answer.

**Color takes a position.** Bold and saturated, moody and restrained, or high-contrast and minimal — lead with a dominant color and punctuate with sharp accents; avoid timid, non-committal distributions. Source the palette from something real: the subject's own materials and artifacts, an IDE theme, a print tradition, a place. Define it as CSS custom properties with semantic names (`--accent`, `--surface`, `--text-primary`) so it stays consistent, and prefer `oklch()` so lightness steps and `color-mix()` derivations behave predictably. In Tailwind projects, replace the palette in the theme (`@theme` in v4) rather than extending it — renaming `indigo-600` to "primary" preserves the recognizable default; custom tokens force custom choices.

**Structure is information.** Structural devices — numbering, eyebrows, dividers, labels — should encode something true about the content, not decorate it. Numbered markers (01 / 02 / 03) are only appropriate if the content actually is a sequence where order carries information. Question each device before incorporating it.

**Compose space with intent.** Asymmetry, overlap and z-depth, diagonal flow, grid-breaking elements, dramatic scale jumps, full-bleed moments, generous negative space OR controlled density. Stacked, centered, full-width sections are the safest structure and read as machine output; off-center compositions and elements that bleed past column bounds signal intent.

**Keep one component vocabulary.** Pick one radius language, one shadow/border approach, one spacing rhythm, and hold them site-wide. Components drifting each toward their own `rounded-2xl shadow-lg p-6` defaults is a hallmark of unedited generation — but so is the opposite failure, one radius and one padding value applied to every surface regardless of role. Decide what a card, a control, and a panel each are, and let the difference show.

**Leverage motion deliberately.** Think about where — and whether — animation serves the subject: a page-load sequence with staggered reveals (`animation-delay`), a scroll-triggered moment, hover micro-interactions, ambient atmosphere. One well-orchestrated moment lands harder than scattered effects, and a fade-in on every element in document order is the tell that no one chose anything. Motion should report state — pressed, loading, saved, arrived — and every interactive element needs a real hover, active and focus state that eases rather than snaps. Prefer CSS-only solutions for plain HTML; use the Motion library for React when available. Sometimes less is more: extra animation contributes to the feeling that a design is AI-generated. Always respect `prefers-reduced-motion`.

**Backgrounds create atmosphere.** Rather than defaulting to solid colors, add contextual effects and textures matching the aesthetic: gradient meshes, noise and grain overlays, geometric patterns, layered transparencies and glassmorphism, dramatic or soft shadows and glows, parallax depth, decorative borders and clip-path shapes, print-inspired textures (halftone, duotone, stipple), knockout typography, custom cursors.

**Imagery is content, not filler.** A real screenshot, a real photograph, or a made-for-this diagram carries information; a stock team-around-a-laptop and a too-smooth AI illustration both announce that nothing here is real. If a placeholder is unavoidable, make it read as structure — a labelled block, a wireframe, a solid field — rather than fake gloss.

**Match complexity to the vision.** Maximalist directions need elaborate execution; minimal directions need precision in spacing, type, and detail. Elegance is executing the chosen vision well.

## Calibration: What Machine Design Looks Like Right Now

Concrete tells, worth checking your own output against:

- Blue-to-purple (or purple-to-pink) gradient on white, in the hero and on the primary button
- Inter or a system stack throughout, at 400 and 600, with no display face
- One radius (`rounded-2xl` / 16px) and one padding (24px) on every surface
- A three-column feature grid of icon-title-sentence cards, icons chosen decoratively
- Untouched component-library defaults — shadcn buttons, Lucide icons, stock Nuxt UI or MUI colors
- Vague aspirational headlines: "Build the future of X", "Your all-in-one platform", "Scale without limits"
- Stock photography or glossy AI illustration where a screenshot belongs

There is a second, more recent cluster — the one that appears when a model has been told to avoid the first. It looks like: (1) a warm cream background near `#F4F1EA` with a high-contrast serif display and a terracotta accent; (2) a near-black background with a single acid-green or vermilion accent; (3) a broadsheet layout with hairline rules, zero border-radius, and dense newspaper columns. All three are legitimate for some briefs, and all three now arrive regardless of subject — including from this skill. Where the brief pins down a visual direction, follow it exactly; the brief's own words always win, including when they ask for one of these looks. Where it leaves an axis free, don't spend that freedom on a default. Like any designer for hire, balance what you're good at against taking the project as a chance to try something you haven't.

## Process: Brainstorm, Plan, Critique, Build, Critique Again

Work in two passes.

**First, brainstorm a compact design plan** from the brief — a small token system:

- **Color**: the palette as 4–6 named hex or `oklch()` values
- **Type**: typefaces for 2+ roles (a characterful display face used with restraint, a complementary body face, a utility face for captions or data if needed), with the scale and weights
- **Layout**: a layout concept — one-sentence prose descriptions and ASCII wireframes to ideate and compare
- **Signature**: the single unique element this page will be remembered by, embodying the brief

**Then review the plan against the brief before building.** If any part reads like the generic default you would produce for any similar page (mentally run a similar prompt — would you arrive somewhere close?), revise that part and note what changed and why. Only then write the code, following the revised plan exactly and deriving every color and type decision from it.

Do most of this planning and iteration in your thinking; show ideas to the user once you have confidence they'll delight.

**Write the plan down somewhere it survives.** You cannot see your previous generations, and a design that exists only in one reply drifts by the second screen and vanishes by the next session. Land the tokens in the artifact itself — a `@theme` block, a `:root` custom-property set, a short `design-notes.md` — and read that file first when extending the work. Keeping a note of directions already used is also the only defence against your own signature style becoming the new default.

When writing the code, watch CSS selector specificity: it's easy to generate classes that cancel each other out (especially a type-based selector like `.section` against an element-based one like `.cta`), which shows up as broken paddings/margins between sections.

Reach for CSS that is actually current — fluid type with `clamp()`, container queries for components that must work at several widths, `:has()`, `@layer` to keep specificity flat, `color-mix()` and `light-dark()` for theming. Features still landing across browsers (`@scope`, view transitions, scroll-driven animations) are worth using behind an `@supports` fallback, not as the only path to a working page.

## Restraint and Self-Critique

Spend your boldness in one place. Let the signature element be the one memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief. Not taking a risk can be a risk itself.

Build to a quality floor without announcing it:

- Responsive with no horizontal scroll — check 390px, 768px and 1440px, not just a desktop viewport
- Text contrast at least 4.5:1 (3:1 for large text, and for UI component and graphical boundaries)
- Visible `:focus-visible` styling on every interactive element, never an outline removed without a replacement
- Real semantics: landmarks, one `h1` and a sane heading order, buttons that are `<button>`, labels tied to inputs, `alt` text that says something
- Interactive targets around 24×24px minimum, with adequate spacing
- `prefers-reduced-motion` respected

Critique your own work as you build — take screenshots if your environment supports it; a picture is worth 1000 tokens. Look at the render rather than the code: tab through it once, read it at mobile width, and run it past the tells above. Consider Chanel's advice: before leaving the house, look in the mirror and remove one accessory.

## Writing in Design

Words appear in a design for one reason: to make it easier to understand, and therefore easier to use. They are design material, not decoration. Briefs often arrive without real content — then the copy is yours to design, and it can make a page feel as templated as the visuals.

- **Write from the end user's side of the screen.** Name things by what people control and recognize, never by how the system is built: a person manages notifications, not webhook config. Describe what something does in plain terms rather than selling it. Specific beats clever.
- **Ban the AI-copy register.** No sentences starting with "Empower," "Unlock," "Transform"; no feature titles like "Seamless Integration"; no abstract-noun pairings; no borrowed superlatives ("best-in-class," "cutting-edge") and no hedging ("may help you," "can potentially"). Include at least one concrete, specific claim — numbers, names, real capabilities. A useful test on any headline: would a named person at this company actually say this sentence out loud?
- **Active voice, exact verbs.** A control says exactly what happens: "Save changes," not "Submit." An action keeps its name through the whole flow — the button that says "Publish" produces a toast that says "Published." Consistent vocabulary is how people learn their way around.
- **Failure and emptiness are moments for direction, not mood.** Explain what went wrong and how to fix it, in the interface's voice. Errors don't apologize and are never vague. An empty screen is an invitation to act.
- **Keep the register conversational and tuned**: plain verbs, sentence case, no filler, tone matched to brand and audience. Each element does exactly one job — a label labels, an example demonstrates, nothing quietly does double duty.

Remember: extraordinary, award-worthy creative work is possible here. Commit relentlessly to a distinctive vision — and edit it like a professional.
