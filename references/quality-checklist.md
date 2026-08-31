# Quality Checklist

## Product

- The primary task is available immediately.
- Real domain language replaces starter copy.
- All decision-relevant source content is represented; nothing is silently dropped to fit a preset card, section, step, or slide count.
- Metrics, examples, trends, citations, and conclusions come from user input or actual computation; intentional sample data is clearly labeled.
- Every visible control works.
- Empty, valid, invalid, working, success, error, and reset states are handled as needed.
- Copy, download, import, export, and persistence behavior is honest.

## Portability

- `index.html` is the entry.
- Required assets are local or embedded.
- Root-absolute asset paths are absent.
- External dependencies are removed unless the user explicitly accepts them.
- No credential or machine-specific path appears in delivered files.
- `.webapp.local.json` is excluded from archives.

## Interaction

- Controls have labels and correct button types.
- Focus remains visible and keyboard order is logical.
- Touch targets are large enough.
- Errors preserve recoverable input.
- Async work prevents duplicate submission and supports cancellation when useful.
- Model output is rendered as untrusted content.
- Normal text and essential control text meet a contrast ratio of at least 4.5:1.
- Color is not the only signal for state or validation.

## Responsive

- Test at 1440×900, 390×844, and 320 px wide.
- No unintended horizontal page overflow exists.
- Labels, buttons, charts, canvases, and tables remain usable.
- Charts have an explicit responsive height or `min-height` and do not trigger resize loops.
- The primary action appears early on mobile.
- Reduced-motion mode still communicates state.

## Delivery

- Chinese interfaces use a local CJK-first font stack with system fallbacks.
- Run `python3 scripts/webapp.py validate <target> --strict`.
- Exercise the primary workflow in a real browser.
- Remove placeholder content, dead code, debug output, and fake data not explicitly labeled as sample data.
- Build the archive and inspect its file list when a zip is requested.

## Scenario Blueprints

- A scenario-generated artifact retains its `data-scenario` marker and all blueprint-required markers.
- Replace the template's labeled sample content with traceable domain material before a real delivery; never present sample figures, sources, or decisions as factual.
- Verify the scenario's actual contract: conversion offer and proof for marketing; a controllable decision and explainable result for prototypes; units, source, and method for infographics; evidence, recommendations, and print treatment for documents; timeline, controls, and reduced-motion fallback for motion.

## Base Kind Contracts

- The body records the expected kind contract and its variance, motion, and density dials.
- Tool output is real and reversible; dashboard evidence includes period, units, threshold, provenance, and exceptions; guided flows branch and support inline recovery; knowledge interfaces expose taxonomy, result count, source status, and a useful no-result state.
- Games pause fairly when hidden and include objective, input, result, replay, and persistence; presentations vary composition across tension, comparison, evidence, and a close with owner and completion signal.

## Presentations

- The audience, outcome, venue, duration, narrative, and brand status are explicit.
- The active brand pack owns stable colors, fonts, logo treatment, and approved layouts; slide-local CSS does not silently contradict it.
- Every slide has one job, a unique `data-slide-id`, a registered `data-layout`, a semantic heading, and a `data-title`.
- Fixed-stage decks preserve one 16:9 composition at every viewport; responsive decks are deliberately tested as reflowing reading experiences.
- Local images declare a named ratio slot such as `hero-16x9`; generated images do not contain duplicated slide chrome.
- Exactly one slide starts active; inactive slides are hidden from interaction with `aria-hidden` and `inert`.
- Keyboard, wheel, swipe, boundary states, progress, deep links, fullscreen fallback, reduced motion, and print output work.
- Run `python3 scripts/webapp.py validate <deck> --strict --rendered` when Playwright is available, then visually inspect every slide.
