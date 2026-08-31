# HTML Presentations

Treat a presentation as a narrative format with a delivery runtime, not as a theme. Derive its visual language from the subject, audience, venue, argument, and any active brand pack.

## Contents

1. Presentation contract
2. Visual discovery
3. Brand packs
4. Stage and density
5. Story and layout contract
6. Images and diagrams
7. Runtime
8. Validation

## Presentation Contract

Before styling, record:

- Audience and what they already know.
- Outcome: what they should understand, decide, or do.
- Venue: laptop review, meeting-room display, screen share, kiosk, phone, or PDF.
- Duration and approximate slide count.
- Narrative tension, evidence, development, decision, and close.
- Source material, citations, imagery, and sensitive-data boundaries.
- Brand pack or explicit statement that the deck is unbranded.

Give every slide one job. Use evidence to support a conclusion, not to fill space. End with a decision, implication, or next action.

## Visual Discovery

Infer the visual direction when the subject and brand make it clear. When aesthetic uncertainty is consequential, show real alternatives instead of asking for abstract adjectives:

```bash
python3 scripts/webapp.py styleboard \
  --out <folder> \
  --title "<actual deck title>" \
  --summary "<actual narrative purpose>"
```

The board compares three mechanisms using the real title and summary:

- `editorial-evidence`: editorial rhythm, evidence strips, restrained serif display roles, and paper-like surfaces.
- `international-grid`: strict grid, sans-serif hierarchy, square geometry, and one functional accent.
- A subject wildcard derived from a meaningful visual metaphor in the content.

Do not treat these as finished themes. After a direction is chosen, define named colors, type roles, composition rules, image treatment, and one subject-specific signature. Skip the board for quick requests, existing brand packs, or clearly specified directions.

## Brand Packs

A brand pack is a reusable directory containing `brand.json`, optional `brand.css`, and an optional local logo. It separates stable brand identity from slide content.

List built-in seeds:

```bash
python3 scripts/webapp.py brands
```

Create a reusable custom pack:

```bash
python3 scripts/webapp.py brand-init \
  --from neutral-corporate \
  --out <brand-folder> \
  --name "<brand name>"
```

Then edit `brand.json`, add a local logo if available, and refine `brand.css`. Scaffold with it:

```bash
python3 scripts/webapp.py scaffold \
  --kind presentation \
  --brand <brand-folder-or-brand.json> \
  --out <deck-folder> \
  --title "<title>" \
  --summary "<purpose>"
```

The pack owns:

- Brand name and visual-system identifier.
- Seven semantic colors: background, surface, text, muted, primary, secondary, and line.
- Display, body, and data font stacks.
- Optional logo and custom CSS.
- Approved `data-layout` names.

Keep logos and CSS inside the pack. The scaffold embeds the logo as a data URI and inlines custom CSS, preserving a portable single-file deck. Use only licensed local fonts or system font stacks; do not make delivery depend on a remote font service.

Brand rules override generic style preferences. They do not override accessibility, factual accuracy, slide safety, or the user's explicit requirements. If a provided corporate deck or style guide conflicts with a seed, update or replace the pack rather than layering one-off overrides across slides.

## Stage And Density

Use `data-stage-mode="fixed"` for slide-deck delivery. Keep a 16:9 canvas and scale the entire stage uniformly to the viewport; do not reflow the slide on phones. This preserves composition and print output.

Use `data-stage-mode="responsive"` only when the artifact is primarily a mobile reading experience rather than a projected deck. In that mode, test every layout at narrow widths and accept that pagination and composition may change.

Declare one density mode on `<body>`:

- `sparse`: keynote statements, product reveals, emotional openings, and image-led slides.
- `balanced`: ordinary executive, technical, or educational decks.
- `dense`: evidence reviews, reference material, and analytical comparisons; increase layout capacity before shrinking text.

Do not solve overflow by repeatedly reducing font size. Shorten copy, change the layout, split the slide, or move detail into notes.

## Story And Layout Contract

Before writing slide HTML, create a compact map:

| Slide id | `data-layout` | One job | Evidence | Image slot |
|---|---|---|---|---|
| opening | cover | Establish the central tension | One verified claim | hero-16x9 |
| tradeoff | comparison | Make the decision boundary visible | Two comparable facts | none |
| decision | closing | State the action | Owner and next step | none |

Use descriptive layout names rather than numbered template positions. The built-in brand seeds register:

- `cover`, `section`, `statement`, and `closing` for narrative transitions.
- `split`, `comparison`, `process`, and `timeline` for relationships and sequence.
- `metrics`, `evidence`, `gallery`, and `diagram` for proof and explanation.

Add a layout to a brand pack before using it. Do not invent an unregistered layout halfway through a branded deck. Reuse a skeleton when its information topology matches, but vary the composition across the story; avoid repeating title-plus-three-cards on every slide.

Use a stable theme rhythm. Avoid three consecutive slides with indistinguishable composition or contrast. For decks of eight or more slides, include at least one strong opening/reveal, one evidence-heavy page, one visual relationship page, and one decisive close when the content supports them.

Each slide must include:

- A unique kebab-case `data-slide-id` for shareable `#slide-<id>` URLs.
- A descriptive registered `data-layout`.
- One semantic `h1`, `h2`, or `h3` stating the point.
- A `data-title` used to update the document title.

## Images And Diagrams

Choose the target slot before generating, searching for, or adapting an image. Bind every local presentation image with `data-image-slot="<role>-<ratio>"`, for example:

- `hero-21x9` for an ultra-wide visual field.
- `evidence-16x10` for screenshots and UI evidence.
- `comparison-left-4x3` and `comparison-right-4x3` for paired evidence.
- `portrait-4x5` for a person or product portrait.

Supported ratio suffixes are `21x9`, `16x9`, `16x10`, `4x3`, `3x2`, `1x1`, `4x5`, and `9x16`.

Generated images are slide ingredients, not complete slides. Do not generate page numbers, headers, footers, logos, title bars, decorative frames, or deck chrome inside the image. Keep key subjects and labels inside a central safe area. Use consistent ratio, visual scale, padding, and annotation density across an image group.

Preserve important screenshot text. Use `object-fit: contain` for uncontrolled screenshots and diagrams; use `cover` for photos or imagery generated specifically for a known slot. Keep labels in semantic HTML when practical. Use SVG for geometry and connectors; putting essential labels in HTML improves accessibility, search, translation, and validation.

## Runtime

Preserve these capabilities unless the user explicitly requests a simpler artifact:

- Exactly one initially active slide; inactive slides use `aria-hidden` and `inert`.
- Previous/next controls with disabled boundary states.
- Arrow, Page Up/Down, Space, Home, and End keys.
- Debounced wheel navigation that ignores interactive and scrollable content.
- Horizontal pointer/touch swipe navigation.
- Visible count, progress, and `#slide-<id>` deep links.
- Fullscreen with graceful failure.
- One slide per printed page.
- Visible focus and reduced-motion behavior.

Add speaker notes, bilingual switching, overview mode, or inline editing only when the request benefits from them. Keep presenter-only instructions out of visible slide content.

## Validation

Run static validation first:

```bash
python3 scripts/webapp.py validate <deck> --strict
```

When Playwright is installed, measure rendered overflow and the navigation-safe line:

```bash
python3 scripts/webapp.py validate <deck> --strict --rendered
```

Then open the deck in a real browser and:

1. Visit every slide with buttons and keyboard controls.
2. Refresh a direct URL such as `#slide-evidence`.
3. Test wheel lock, swipe, Home, End, and fullscreen fallback.
4. Inspect every slide at the intended venue size and at a small viewport.
5. Emulate reduced motion.
6. Print or emulate print media and confirm one complete 16:9 slide per page.
7. Check for clipped text, broken assets, weak contrast, accidental blank space, and inconsistent image treatment.

## Method Sources

The visual-preview workflow and fixed-stage principle were informed by [Frontend Slides](https://github.com/zarazhangrui/frontend-slides). The layout contract, image-slot-first workflow, and measurable presentation checks were informed by [Guizang PPT Skill](https://github.com/op7418/guizang-ppt-skill). This skill independently implements those general methods; it does not include Guizang templates, validator code, images, or other AGPL-covered assets, and it does not redistribute the Frontend Slides template pack.
