# Design Workflow

## Define The Product Contract

Before styling, write down:

- Audience and environment: desktop, phone, local file, or local server.
- Primary job: one sentence beginning with a verb.
- Inputs: types, examples, validation, limits, and sensitive-data considerations.
- Outputs: results, copy/download behavior, and error recovery.
- States: empty, ready, working, success, partial, error, and reset.
- Persistence: none, local storage, IndexedDB, or exported files.

Infer reversible details and build the core workflow first. Ask only when an assumption changes data handling, security, or the fundamental interaction.

## Choose Complexity Deliberately

Use one self-contained HTML file when browser APIs and modest JavaScript are sufficient. Split local CSS, JavaScript, or media only when the single file becomes difficult to maintain. Keep split projects static and dependency-light.

## Compose The Interface

Preserve the user's information hierarchy and all decision-relevant content. Let the
amount of real content determine the number of sections, cards, steps, or slides.
Never manufacture measurements, trends, testimonials, citations, or conclusions.
Clearly label intentional demonstration data as sample data.

For tools:

1. Use a compact literal title and one-line purpose.
2. Group inputs by the user's mental model.
3. Place the primary action beside the controls it affects.
4. Keep output and copy/download actions together.
5. Hide secondary settings until needed.

For data views:

1. Lead with decision-relevant metrics.
2. Show comparison context and units.
3. Use charts for shape and tables for precise lookup.
4. Surface exceptions before decoration.
5. Give every chart an explicit responsive height or `min-height`; do not rely on an unconstrained parent.

Avoid marketing-style hero sections, decorative feature grids, and controls without working behavior.

## Interaction Quality

- Preserve input after recoverable errors.
- Put field errors next to the failed control.
- Use `aria-live="polite"` for asynchronous status and result summaries.
- Keep pointer targets at least 40×40 px; use 44 px for touch-oriented apps.
- Match keyboard order to visual order.
- Use visible `:focus-visible` treatment.
- Confirm only destructive or irreversible actions.
- Provide non-blocking copy/download feedback.

## Responsive Rules

- Use fluid widths and `minmax(0, 1fr)`.
- Collapse panels before controls or labels become cramped.
- Give tables an intentional overflow strategy.
- Give canvases and charts stable responsive dimensions.
- Keep the main action visible early on mobile.
- Ensure the longest control label fits at 320 px.

## Typography And Contrast

- For Chinese interfaces, use a local CJK-first stack such as `"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", system-ui, sans-serif`.
- Use local system fonts by default; do not make legibility depend on a font download.
- Keep normal text and essential control text at a contrast ratio of at least 4.5:1.
- Do not use color alone to communicate state, category, or validation.

## Existing Apps

Preserve working domain behavior while improving structure and presentation. Test behavior before and after the change. Remove dead controls, placeholder data, debug output, and fake success states.
