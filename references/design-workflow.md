# HTML Design Workflow

## 1. Define The Product Contract

Before styling, write down:

- Audience and environment: desktop browser, mobile, offline file, Eqai iframe, or another host.
- Primary job: one sentence beginning with a verb.
- Inputs: type, validation, examples, maximum size, and sensitive-data considerations.
- Outputs: what appears, what can be copied/downloaded, and how errors are recovered.
- State: empty, ready, working, success, partial success, error, and reset.
- Delivery: one HTML file, an asset folder, an HTML presentation, or an Eqai AI package.

If the contract is unclear, infer reversible details and build the core workflow first. Ask only when an assumption would change data handling, security, or the fundamental interaction.

## 2. Choose Complexity Deliberately

Use one self-contained HTML file when the tool can be expressed with browser APIs and modest JavaScript. This is the default for Eqai HTML tools because it is portable and easy to inspect.

Use separate local CSS/JS assets when the file is becoming difficult to maintain. Use a framework only when the request genuinely needs complex state, routing, a component ecosystem, or an existing project already uses it. Do not introduce a build chain for a small form-and-result utility.

## 3. Establish Visual Direction

Derive one coherent direction from the brief:

- `density`: compact, balanced, or spacious
- `tone`: operational, analytical, editorial, playful, or technical
- `scheme`: light, dark, or system-aware
- `brand`: existing product/company palette or a restrained neutral palette
- `emphasis`: the one action or data point that should win first glance

Select one of the five interface directions in [visual-directions.md](visual-directions.md), then write a compact design brief before coding. For a presentation, use [presentation-guide.md](presentation-guide.md) to derive a subject-specific deck system instead of selecting an interface direction:

- `subject`: the concrete domain and its real vocabulary
- `direction`: workbench, analytics, guided, knowledge, or ai-studio
- `density`: compact, balanced, or spacious
- `palette`: 4-6 named colors with hex values
- `type`: display, body, and utility/data roles
- `layout`: one sentence describing the information structure
- `signature`: one useful, subject-specific treatment the interface will be remembered by

Use this as a constraint, not as a style catalog. Keep typography, spacing, borders, color, and interaction states consistent throughout the artifact. If the same design brief could fit an unrelated tool after changing only the title, revise the layout or signature before coding.

For KOSTAL-facing tools, use neutral white/gray surfaces, dark readable text, blue as an optional structural color, and shallow green for normal actions and success. Avoid red except for genuine destructive/error states.

## 4. Compose The Interface

Tool layout:

1. Compact header with the literal tool name and optional one-line context.
2. Input controls grouped by the user's mental model.
3. Primary action adjacent to the controls it acts on.
4. Output region with copy/download actions near the output.
5. Secondary settings hidden behind tabs, details, or a compact settings panel when they are not part of the main path.

Operational interfaces should prioritize scanning and repeated action. Avoid oversized hero text, decorative page sections, and marketing-style copy.

## 5. Interaction Quality

- Disable or explain unavailable actions.
- Preserve the user's input after recoverable errors.
- Put error text next to the failed field or result area.
- Use `aria-live="polite"` for asynchronous status and output summaries.
- Keep pointer targets at least 40x40px; use 44px where the interface is touch-oriented.
- Make keyboard order match visual order.
- Use `:focus-visible` with a high-contrast outline.
- Confirm dialogs only for destructive or irreversible actions.
- Provide copy/download feedback without blocking modal dialogs.

## 6. Responsive Rules

Design desktop first for internal Eqai usage, then verify narrow layouts:

- Use `minmax(0, 1fr)` for flexible grid tracks.
- Let tool panels collapse to one column before text or controls become cramped.
- Avoid fixed page widths; constrain content with `max-width` plus fluid side padding.
- Give tables an intentional overflow strategy.
- Give charts/canvases a stable aspect ratio or explicit responsive height.
- At 320px, the longest label and button text must fit without clipping.

## 7. Validation And Browser QA

Run the static validator, then verify at minimum:

- Desktop: 1440x900 or the user's primary browser size.
- Narrow: 390x844 and 320px width.
- Empty input, realistic input, invalid input, reset, copy/download, and asynchronous failure states.
- No horizontal page overflow, overlapping controls, clipped labels, blank charts, or console errors.
- Tab navigation reaches every interactive control and focus remains visible.
- Reduced-motion mode still communicates state.

For existing tools, preserve domain logic while improving presentation. Diff the behavior, not only the markup.

Run one final genericity check: remove any element whose only purpose is to make the page look designed, and strengthen any structural treatment that helps the user scan, compare, decide, or complete the task.

For presentations, additionally verify every slide, direct hash navigation, presenter controls, notes, fullscreen fallback, and one-slide-per-page print output. Narrative clarity and projection legibility matter more than preserving starter compositions.
