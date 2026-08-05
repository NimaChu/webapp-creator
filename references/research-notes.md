# Reference Review And Adoption Boundary

This skill uses lessons from several references and local examples without merging their codebases.

## Local `html-templates`

Useful idea: convert the brief into explicit visual signals such as audience, density, tone, scheme, and formality, then keep one coherent visual direction.

Adopted: the brief-to-visual-direction step and consistency checks.

Not adopted: the 32-profile `visual_dna.json` dataset, hard profile matching, and its template-specific decoration vocabulary. The local copy has encoding damage and refers to an upstream license file that is not present beside the dataset, so redistribution would be brittle. A general HTML skill should also follow an existing product design system before selecting a style profile.

## Local `data-dashboard`

Useful ideas: decision-oriented hierarchy, locale-aware formatting, deterministic chart initialization, chart resize handling, and separating data from rendering.

Adopted: dashboard information architecture, chart selection guidance, formatter rules, and deterministic validation.

Not adopted: its full template and fragment-merging implementation. The source copy has encoding damage, assumes a specific ECharts/CDN stack, and is heavier than most single-page Eqai tools need.

## Local `artifacts-builder`

Useful idea: route simple artifacts to plain HTML and reserve React/shadcn bundling for genuinely complex interfaces.

Adopted: explicit complexity selection and packaging awareness.

Not adopted: shell-only setup scripts, embedded component archive, and a mandatory React/Vite toolchain. Eqai's common HTML utilities should remain portable and inspectable.

## `tt-a1i/archify`

Archify is MIT licensed and purpose-built for technical diagrams. Its strongest reusable method is: typed intent, deterministic rendering, structural validation, browser verification, and accessibility-aware interaction.

Adopted: contract-first design, deterministic checks, reduced-motion guidance, keyboard access, stable responsive geometry, and the principle that validation precedes delivery.

Not adopted: Archify's renderer code, schemas, 500 KB template, diagram interaction runtime, or visual presets. Those belong in the specialist Archify skill and would make a general HTML skill slower and less maintainable.

## KOSTAL Frontend Design

Useful ideas: establish precedence between official assets, existing product patterns, and fallback rules; choose an intentional enterprise direction; optimize internal tools laptop-first; and provide canonical structures for tables, long forms, and dashboards.

Adopted: the KOSTAL enterprise baseline, calm engineering tone, clear grids, reusable tokens, and the distinction between structural blue and shallow-green normal actions.

Not adopted: treating any fallback color or component rule as an official universal KOSTAL product design system. Task-provided and product-local systems still take precedence.

## Addy Osmani `frontend-ui-engineering`

Useful ideas: production UI requires complete states, semantic tokens, realistic content, WCAG-aware controls, deliberate responsive testing, and the absence of generic AI styling.

Adopted: the production quality checklist, four-scale responsive checks, state completeness, meaningful empty/error states, and semantic design-system discipline.

Not adopted: React-specific folder structures, state libraries, Tailwind examples, and fixed component line limits for ordinary single-file HTML tools.

## Anthropic `web-artifacts-builder`

Useful idea: reserve React, TypeScript, routing, and component libraries for artifacts whose complexity needs them, while still supporting a final portable bundle.

Adopted: an explicit complexity threshold and the warning against centered, purple, uniformly rounded AI-generated layouts.

Not adopted: the React/Tailwind/shadcn toolchain, initialization scripts, component bundle, or Claude-specific delivery runtime.

## Anthropic `frontend-design`

Useful ideas: ground visual decisions in the subject, treat structure and copy as design material, define one memorable signature, and critique genericity before and after implementation.

Adopted: the two-pass direction and genericity check, subject-specific information treatment, intentional interface copy, and the rule to spend distinctiveness in one useful place.

Not adopted: a requirement for decorative aesthetic risk, unusual typography, hero-first composition, or studio-style expression in operational enterprise tools. No external code, templates, or proprietary assets are redistributed.

## Eqai Agent Ecosystem Showcase

Useful ideas: a single-file full-viewport slide runtime, semantic slide sections, keyboard/wheel/swipe navigation, URL hash state, progress and counting, fullscreen fallback, speaker notes, accessible inactive states, and one-slide-per-page print output.

Adopted: the reusable presentation runtime contract and validation targets.

Not adopted: the showcase's dark neon palette, decorative grid/orbit background, Eqai-specific slide compositions, bilingual content table, giant indices, glow effects, or fixed typography. The presentation starter is deliberately style-neutral so each deck can derive an identity from its own subject and audience.
