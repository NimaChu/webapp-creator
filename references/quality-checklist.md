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
