---
name: html-design
description: Create, redesign, repair, and validate practical HTML tools, single-file web apps, data dashboards, bilingual HTML presentations that replace slide decks, guided workflows, knowledge interfaces, and Eqai AI-enabled web tools with task-specific visual direction. Use for HTML utilities, interactive browser tools, data reports, full-screen Chinese-English presentations, polished single-file artifacts, frontend usability or accessibility improvements, responsive repairs, and tools that call Eqai-hosted text or image generation.
---

# HTML Design

Build the usable experience, not a landing page describing it. Prefer one self-contained HTML file for ordinary tools, dashboards, and presentations. Use the Eqai AI package shape only when platform-hosted model access is required.

## Route The Request

Choose the technical kind and visual direction separately. Infer both from the user's task; do not ask the user to choose a template unless the brief genuinely leaves multiple consequential directions open.

Technical kinds:

- `tool`: calculators, converters, generators, forms, checklists, inspectors, guided workflows, and knowledge interfaces.
- `dashboard`: KPI views, comparisons, operational summaries, visual reports, and data exploration.
- `eqai-ai`: tools requiring Eqai-hosted text generation, image generation, or both.
- `presentation`: full-screen, bilingual slide narratives intended to present live or export to PDF instead of authoring a PPT file.
- Existing HTML: improve the supplied implementation in place and preserve working domain logic.

Visual directions:

- `workbench`: compact repeated-action tools.
- `analytics`: decision-oriented dashboards and reports.
- `guided`: multi-step configuration, diagnosis, review, and structured forms.
- `knowledge`: guides, summaries, meeting notes, FAQs, and knowledge organization.
- `ai-studio`: prompt-driven text and image creation.

`presentation` is a delivery format, not a visual direction. Read [references/presentation-guide.md](references/presentation-guide.md) whenever creating or redesigning a presentation. Derive the deck's visual language from its subject, audience, venue, and narrative; the starter is an interaction engine, not a theme.

Read [references/visual-directions.md](references/visual-directions.md) before creating or substantially redesigning an interface. Use it to select one direction and define its density, hierarchy, palette, layout, and useful signature.

For technical architecture, sequence, workflow, data-flow, or lifecycle diagrams, use a dedicated diagram skill when available. Do not rebuild a specialist diagram engine inside a general HTML tool.

## Workflow

1. Inspect the audience, environment, real content, core task, inputs, outputs, and required states.
2. Write a compact internal contract and select one visual direction.
3. Check whether the direction is specific to the subject; revise generic card-grid or generic AI styling before coding.
4. Scaffold only when no useful implementation exists.
5. Implement the complete primary workflow, including empty, loading, success, partial, and error states where relevant.
6. Validate with `scripts/html_design.py validate --strict`.
7. Open the result in a real browser and exercise the primary interaction at desktop and narrow widths.
8. Remove placeholder content, dead controls, debug output, and fake data that is not explicitly identified.

Read [references/design-workflow.md](references/design-workflow.md) for the product contract and implementation process. For dashboards, also read [references/dashboard-patterns.md](references/dashboard-patterns.md). For presentations, also read [references/presentation-guide.md](references/presentation-guide.md). Before delivery, read [references/quality-checklist.md](references/quality-checklist.md). For Eqai model access, also read [references/eqai-ai-bridge.md](references/eqai-ai-bridge.md).

## Scaffold

List visual directions:

```bash
python scripts/html_design.py directions
```

Create a tool with the inferred direction:

```bash
python scripts/html_design.py scaffold --kind tool --direction workbench --out <folder> --title "<title>" --summary "<purpose>"
```

Other supported combinations:

```bash
python scripts/html_design.py scaffold --kind tool --direction guided --out <folder> --title "<title>" --summary "<purpose>"
python scripts/html_design.py scaffold --kind tool --direction knowledge --out <folder> --title "<title>" --summary "<purpose>"
python scripts/html_design.py scaffold --kind dashboard --direction analytics --out <folder> --title "<title>" --summary "<decision supported>"
python scripts/html_design.py scaffold --kind eqai-ai --direction ai-studio --out <folder> --title "<title>" --summary "<purpose>" --ai text,image
python scripts/html_design.py scaffold --kind presentation --direction auto --out <folder> --title "<title>" --summary "<narrative purpose>"
```

`--direction auto` selects the default starter for the technical kind. For presentations it selects the style-neutral presentation runtime. Replace the starter workflow and sample content with the user's actual domain before delivery. Do not scaffold over an existing implementation.

## Architecture Threshold

- Use one HTML file for browser APIs, modest state, local data, ordinary Eqai tools, and most presentations.
- Use separate local CSS or JavaScript when a single file becomes difficult to navigate.
- Use React or another framework only for genuinely complex shared state, routing, component ecosystems, or an existing framework project.
- Keep framework dependencies out of portable single-file tools. Do not introduce Tailwind, shadcn, or a build chain solely for visual polish.

## Design Baseline

- Make the primary task immediately available and use realistic domain wording.
- Use neutral light surfaces, dark text, shallow green for normal actions and success, and KOSTAL blue for structure or information emphasis.
- Reserve red for genuine error or destructive states.
- Use a consistent spacing and type scale. Keep radii at 8 px or less unless an existing system requires otherwise.
- Keep cards for repeated items and genuine work panels. Do not nest cards or make every section float.
- Use semantic HTML, native controls, visible focus, readable contrast, and labels for every control.
- Use stable dimensions for toolbars, charts, canvases, counters, and dynamic output.
- Avoid generic AI aesthetics, decorative gradients, stock hero sections, oversized padding, excessive centering, and one-hue interfaces.
- Spend visual distinctiveness on one subject-relevant information treatment, not on decoration.
- Respect reduced motion and ensure the longest label fits at 320 px.

## Validate

```bash
python scripts/html_design.py validate <html-file-or-folder>
python scripts/html_design.py validate <html-file-or-folder> --strict
```

Static validation is the quality floor, not visual proof. Test desktop at 1440x900 and narrow layouts at 390x844 and 320 px. Exercise empty input, realistic input, invalid input, reset, copy/download, and asynchronous failures where applicable. For presentations, also test every slide, Chinese-English switching, arrow/Page/Home/End keys, controls, direct slide hashes, notes, fullscreen fallback, swipe, reduced motion, and print/PDF layout.

## Eqai Boundary

This skill owns HTML design, scaffolding, frontend behavior, and validation. The `eqai` skill owns discovery, upload, update, archive, installation, and opening published tools.

For Eqai AI tools, never embed model URLs, provider names, API keys, tokens, or credentials. Declare capabilities in `eqai-tool.json` and call `/runtime-sdk/v1/eqai.js`.

## Source Notes

The design method incorporates selected principles from KOSTAL Frontend Design, Addy Osmani's Frontend UI Engineering, and Anthropic's Web Artifacts Builder and Frontend Design skills. No external template, component archive, framework bundle, or proprietary asset is redistributed. See [references/research-notes.md](references/research-notes.md).
