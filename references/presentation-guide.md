# HTML Presentation Guide

Use this guide for `--kind presentation`. The presentation starter supplies a delivery engine; it does not prescribe a visual identity.

## 1. Define The Deck Before Styling

Write a compact presentation contract:

- Audience: who is in the room and what they already know.
- Outcome: what they should understand, decide, or do afterward.
- Venue: laptop review, meeting-room display, screen share, kiosk, or exported PDF.
- Duration: target speaking time and approximate slide count.
- Narrative: opening tension, evidence, development, decision, and close.
- Source material: facts, images, diagrams, citations, and sensitive-data boundaries.

One slide should make one primary point. The title should state that point when possible, not merely name a topic.

## 2. Derive A Visual System

Do not inherit the starter's appearance unchanged. Define the deck from its subject and audience:

- Tone: executive, technical, instructional, editorial, product-focused, or celebratory.
- Scheme: light, dark, or venue-aware.
- Typography: one display role, one reading role, and an optional data/code role.
- Palette: neutral foundation plus restrained semantic and emphasis colors.
- Composition: choose layouts that fit the evidence, not a repeated card template.
- Signature: one subject-relevant device such as a process rail, annotated object, evidence strip, timeline, comparison field, or spatial map.

Keep the runtime class names and IDs stable while replacing visual tokens, slide layouts, and content. Avoid making every slide a title plus equal cards. Use deliberate variation: statement, evidence, comparison, process, demonstration, and close.

## 3. Runtime Contract

Preserve these capabilities unless the user explicitly requests a simpler artifact:

- Semantic `<section class="slide">` pages inside the deck.
- Exactly one initially active slide; inactive slides use `aria-hidden` and `inert` at runtime.
- Previous/next controls and disabled boundary states.
- Arrow, Page Up/Down, Space, Home, and End keyboard navigation.
- Debounced vertical-wheel navigation that does not hijack interactive or scrollable content.
- Horizontal touch swipe navigation.
- A counter, progress bar, and shareable `#slide-N` URL state.
- Fullscreen with graceful fallback when the host blocks it.
- Per-slide `.slide-note` speaker notes toggled with `N`.
- Complete Chinese-English switching for visible content, document titles, controls, accessible labels, and speaker notes; use `L` as the keyboard shortcut.
- Print CSS that emits one slide per page for PDF output.
- Responsive layouts, visible focus, and reduced-motion behavior.

Update the document title from each slide's `data-title-key`. Keep critical content in the DOM so print, accessibility tools, and browser search can reach it.

## 4. Content And Media

- Use real, inspectable images or diagrams when the subject depends on visual evidence.
- Add meaningful `alt` text; decorative media uses empty alt text.
- Prefer local assets for portable or offline decks.
- Cite claims close to the evidence or in a compact source line.
- Do not shrink dense content until it technically fits. Split it into another slide.
- Keep presenter-only cues in `.slide-note`, not hidden visual text.
- Keep the `en` and `zh` message dictionaries complete and structurally equivalent. Every `data-i18n`, `data-i18n-aria-label`, `data-i18n-title`, and slide `data-title-key` must resolve in both languages.
- Translate meaning rather than mirroring word order. Preserve figures, citations, and technical terms consistently across languages.

## 5. Validation

Run strict static validation, then test the complete deck in a browser:

1. Visit every slide with buttons and keyboard controls.
2. Load a direct hash such as `#slide-3` and refresh it.
3. Switch between Chinese and English on several slides; verify content, page title, controls, accessible labels, and notes all change together.
4. Test Home, End, notes, fullscreen fallback, wheel lock, and touch swipe.
5. Verify every slide at 1440x900, 390x844, and 320 px without overlap or clipped controls in both languages.
6. Emulate `prefers-reduced-motion` and confirm state remains understandable.
7. Print to PDF or emulate print media and confirm one complete slide per page.
8. Check for console errors, broken assets, blank slides, and mojibake.

The final deck should feel authored for its subject. If changing only the title would make it fit an unrelated presentation, revise the visual system and narrative compositions.
