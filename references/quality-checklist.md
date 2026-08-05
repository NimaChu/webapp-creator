# Frontend Quality Checklist

Use this checklist after implementation and before delivery.

## Product And Content

- The first viewport exposes the real task, not marketing copy.
- Labels and commands use the user's vocabulary and active verbs.
- Realistic content has tested wrapping, overflow, empty values, and long labels.
- Empty states explain the next useful action.
- Error states say what failed and how to recover.
- Loading states preserve layout and identify what is working.

## Structure And State

- Use local state for component-specific interaction and URL state for shareable filters or views.
- Separate data transformation from DOM rendering when logic is nontrivial.
- Keep repeated render functions focused; split a large script into local modules or files before it becomes difficult to inspect.
- Use a framework only when routing, complex shared state, or an existing component system justifies it.
- Preserve user input after recoverable errors.

## Visual System

- Use semantic color, spacing, type, radius, and motion tokens.
- Follow one spacing scale instead of arbitrary values.
- Keep heading levels meaningful and do not style body text as headings.
- Direct-label important values; add legends only when needed.
- Use icons, text, shape, or line style alongside color for status meaning.
- Remove generic hero sections, excessive centered layouts, uniform card grids, heavy shadows, and decorative gradients.
- Keep one subject-relevant visual signature and make the surrounding interface quiet.

## Accessibility

- Every control works with a keyboard and has a visible focus state.
- Every form control has a visible label or accessible name.
- Icon-only controls have an accessible name and tooltip.
- Dialogs move focus inside, keep it trapped, and restore focus on close.
- Normal text meets 4.5:1 contrast; large text and essential graphics meet 3:1.
- Status does not rely on color alone.
- Dynamic results use an appropriate live region without announcing every minor change.
- Motion respects `prefers-reduced-motion`.

## Responsive And Runtime

- Verify at 320 px, 390x844, 768 px, 1024 px, and 1440x900.
- No page-level horizontal scrolling, overlap, clipped labels, or text outside controls.
- Tables have an intentional narrow-screen strategy.
- Charts and canvases have stable dimensions and render nonblank pixels.
- The browser console has no uncaught errors.
- Empty, realistic, invalid, reset, copy/download, and asynchronous failure paths work.
- External dependencies are intentional, disclosed, and compatible with offline requirements.

## Presentation Delivery

- The deck has a clear audience, outcome, narrative arc, and speaking-time target.
- Each slide makes one primary point and uses a composition suited to its evidence.
- Buttons, keyboard, wheel, swipe, Home/End, and direct `#slide-N` links reach the correct slide.
- Inactive slides are hidden from assistive interaction; the current slide remains readable and focusable.
- Counter, progress, boundary states, notes, and fullscreen fallback work without layout shift.
- Chinese-English switching updates all visible copy, document titles, controls, accessible labels, and speaker notes without missing keys or mixed-language residue.
- Print/PDF output places one complete slide on each page.
- The visual system belongs to the subject and is not an unchanged starter theme.
