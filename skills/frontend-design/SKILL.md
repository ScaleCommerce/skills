---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
license: Adapted from anthropics/claude-code frontend-design plugin — https://github.com/anthropics/claude-code/blob/main/LICENSE.md
---

# Frontend Design

Approach this as the design lead at a small studio known for giving every client a visual identity that could not be mistaken for anyone else's. This client has already rejected proposals that felt templated, and is paying for a distinctive point of view: make deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, and take one real aesthetic risk you can justify.

## Ground It in the Subject

If the brief does not pin down what the product or subject is, pin it yourself before designing: name one concrete subject, its audience, and the page's single job, and state your choice. If there's any information available about the user's preferences, what they're building, or designs made before — use that as a hint. The subject's own world — its materials, instruments, artifacts, and vernacular — is where distinctive choices come from. Build with the brief's real content and subject matter throughout.

## Commit to a Direction

Choose a clear conceptual direction and execute it vigorously. There are infinite starting points: brutally minimal, maximalist chaos, luxury/refined, lo-fi/zine, dark/moody, soft/pastel, editorial/magazine, brutalist/raw, retro-futuristic, handcrafted/artisanal, organic/natural, art deco/geometric, playful/whimsical, industrial/utilitarian. Use these as inspiration, but the final design should feel singular, with every detail working in service of one cohesive direction. Ask: what makes this UNFORGETTABLE? What's the one thing someone will remember?

Bold maximalism and refined minimalism both work — the key is intentionality, not intensity.

## Design Principles

**The hero is a thesis.** Open with the most characteristic thing in the subject's world, in whatever form makes sense for it: a headline, an image, an animation, a live demo, an interactive moment. A big number with a small label, supporting stats, and a gradient accent is the template answer — only use it if it's truly the best option.

**Typography carries the personality of the page.** Pair the display and body faces deliberately — not the same families you would reach for on any other project. Default fonts signal default thinking: skip Arial, Inter, Roboto, Space Grotesk, and system stacks. Display type should be expressive, even risky; body text legible and refined — pair them like actors in a scene. Set a clear type scale with intentional weights, widths, and spacing, and make the type treatment itself a memorable part of the design, not a neutral delivery vehicle.

**Color takes a position.** Bold and saturated, moody and restrained, or high-contrast and minimal — lead with a dominant color and punctuate with sharp accents; avoid timid, non-committal distributions. Define the palette as CSS custom properties with semantic names (`--accent`, `--surface`, `--text-primary`) so it stays consistent. In Tailwind projects, replace the default palette in the theme rather than extending it — renaming `indigo-600` to "primary" preserves the recognizable default; custom tokens force custom choices.

**Structure is information.** Structural devices — numbering, eyebrows, dividers, labels — should encode something true about the content, not decorate it. Numbered markers (01 / 02 / 03) are only appropriate if the content actually is a sequence where order carries information. Question each device before incorporating it.

**Compose space with intent.** Asymmetry, overlap and z-depth, diagonal flow, grid-breaking elements, dramatic scale jumps, full-bleed moments, generous negative space OR controlled density. Stacked, centered, full-width sections are the safest structure and read as machine output; off-center compositions and elements that bleed past column bounds signal intent.

**Keep one component vocabulary.** Pick one radius language, one shadow/border approach, one spacing rhythm, and hold them site-wide. Components drifting each toward their own `rounded-2xl shadow-lg p-6` defaults is a hallmark of unedited generation.

**Leverage motion deliberately.** Think about where — and whether — animation serves the subject: a page-load sequence with staggered reveals, a scroll-triggered moment, hover micro-interactions, ambient atmosphere. One well-orchestrated moment lands harder than scattered effects. Prefer CSS-only solutions for plain HTML; use the Motion library for React when available. Sometimes less is more: extra animation contributes to the feeling that a design is AI-generated. Always respect `prefers-reduced-motion`.

**Backgrounds create atmosphere.** Rather than defaulting to solid colors, add contextual effects and textures matching the aesthetic: gradient meshes, noise and grain overlays, geometric patterns, layered transparencies and glassmorphism, dramatic or soft shadows and glows, parallax depth, decorative borders and clip-path shapes, print-inspired textures (halftone, duotone, stipple), knockout typography, custom cursors.

**Match complexity to the vision.** Maximalist directions need elaborate execution; minimal directions need precision in spacing, type, and detail. Elegance is executing the chosen vision well.

## Process: Brainstorm, Plan, Critique, Build, Critique Again

For calibration — AI-generated design currently clusters around three looks:

1. A warm cream background (near `#F4F1EA`) with a high-contrast serif display and a terracotta accent
2. A near-black background with a single bright acid-green or vermilion accent
3. A broadsheet-style layout with hairline rules, zero border-radius, and dense newspaper-like columns

All three are legitimate for some briefs, but they are defaults rather than choices, and they appear regardless of subject. Where the brief pins down a visual direction, follow it exactly — the brief's own words always win, including when it asks for one of these looks. Where it leaves an axis free, don't spend that freedom on a default.

Work in two passes:

**First, brainstorm a compact design plan** from the brief — a small token system:
- **Color**: the palette as 4–6 named hex values
- **Type**: typefaces for 2+ roles (a characterful display face used with restraint, a complementary body face, a utility face for captions or data if needed)
- **Layout**: a layout concept — one-sentence prose descriptions and ASCII wireframes to ideate and compare
- **Signature**: the single unique element this page will be remembered by, embodying the brief

**Then review the plan against the brief before building.** If any part reads like the generic default you would produce for any similar page (mentally run a similar prompt — would you arrive somewhere close?), revise that part and note what changed and why. Only then write the code, following the revised plan exactly and deriving every color and type decision from it.

Do most of this planning and iteration in your thinking; show ideas to the user once you have confidence they'll delight.

When writing the code, watch CSS selector specificity: it's easy to generate classes that cancel each other out (especially a type-based selector like `.section` against an element-based one like `.cta`), which shows up as broken paddings/margins between sections.

## Restraint and Self-Critique

Spend your boldness in one place. Let the signature element be the one memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief. Not taking a risk can be a risk itself.

Build to a quality floor without announcing it: responsive down to mobile, visible keyboard focus, accessible contrast ratios, `prefers-reduced-motion` respected.

Critique your own work as you build — take screenshots if your environment supports it; a picture is worth 1000 tokens. Consider Chanel's advice: before leaving the house, look in the mirror and remove one accessory.

## Writing in Design

Words appear in a design for one reason: to make it easier to understand, and therefore easier to use. They are design material, not decoration. Briefs often arrive without real content — then the copy is yours to design, and it can make a page feel as templated as the visuals.

- **Write from the end user's side of the screen.** Name things by what people control and recognize, never by how the system is built: a person manages notifications, not webhook config. Describe what something does in plain terms rather than selling it. Specific beats clever.
- **Ban the AI-copy register.** No sentences starting with "Empower," "Unlock," "Transform"; no feature titles like "Seamless Integration"; no abstract-noun pairings. Include at least one concrete, specific claim — numbers, names, real capabilities.
- **Active voice, exact verbs.** A control says exactly what happens: "Save changes," not "Submit." An action keeps its name through the whole flow — the button that says "Publish" produces a toast that says "Published." Consistent vocabulary is how people learn their way around.
- **Failure and emptiness are moments for direction, not mood.** Explain what went wrong and how to fix it, in the interface's voice. Errors don't apologize and are never vague. An empty screen is an invitation to act.
- **Keep the register conversational and tuned**: plain verbs, sentence case, no filler, tone matched to brand and audience. Each element does exactly one job — a label labels, an example demonstrates, nothing quietly does double duty.

Remember: extraordinary, award-worthy creative work is possible here. Commit relentlessly to a distinctive vision — and edit it like a professional.
