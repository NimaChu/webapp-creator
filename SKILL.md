---
name: html-design
description: Create, redesign, repair, validate, preview, and package lightweight standalone web apps as portable HTML. Use for single-file browser tools, calculators, converters, dashboards, guided workflows, knowledge interfaces, touch-friendly mini-games, full-screen HTML presentations, and local-model text, vision, image, or code tools that must run without a build chain or hosted service.
---

# HTML Design

Build the usable application, not a page that describes it. Default to one self-contained `index.html` with inline CSS and JavaScript. Keep the result inspectable, portable, and runnable from local storage.

## Route The Request

Choose an application kind independently from model capabilities.

Application kinds:

- `tool`: calculators, converters, generators, forms, inspectors, and focused utilities.
- `dashboard`: metrics, comparisons, trends, filters, and decision views.
- `guided`: multi-step configuration, diagnosis, review, and structured workflows.
- `knowledge`: guides, notes, FAQs, summaries, and organized reference material.
- `game`: lightweight touch-friendly games with a complete play loop.
- `presentation`: full-screen HTML narratives with keyboard navigation and print output.

Model capabilities:

- `none`: browser logic only. Use this by default.
- `text`: text generation or transformation.
- `vision`: image understanding, OCR, chart reading, or screenshot analysis.
- `image`: image generation through a configured local endpoint.
- `code`: code-oriented generation or explanation through the chat endpoint.

Read [references/design-workflow.md](references/design-workflow.md) before creating or substantially redesigning an interface. Read [references/visual-directions.md](references/visual-directions.md) to define a subject-specific visual direction.

For games, also read [references/games.md](references/games.md). For presentations, also read [references/presentations.md](references/presentations.md). For model-enabled apps, also read [references/local-models.md](references/local-models.md). Before delivery, read [references/quality-checklist.md](references/quality-checklist.md).

## Workflow

1. Inspect the audience, environment, core task, inputs, outputs, data sensitivity, and required states.
2. Write a compact product contract and choose one visual direction.
3. Preserve working domain logic when modifying an existing app.
4. Preserve all decision-relevant user content; do not invent data, metrics, or conclusions.
5. Scaffold only when no useful implementation exists.
6. Replace starter content and behavior with the actual task.
7. Implement empty, ready, working, success, partial, error, and reset states where relevant.
8. Validate with `scripts/webapp.py validate --strict`.
9. Run the primary workflow in a real browser at desktop, narrow mobile, and 320 px widths.
10. Build a zip only when the user needs a distributable package.

## Scaffold

List supported kinds:

```bash
python3 scripts/webapp.py kinds
```

Create a browser-only app:

```bash
python3 scripts/webapp.py scaffold \
  --kind tool \
  --out <folder> \
  --title "<title>" \
  --summary "<purpose>"
```

Create a model-enabled app:

```bash
python3 scripts/webapp.py scaffold \
  --kind tool \
  --ai text,vision \
  --out <folder> \
  --title "<title>" \
  --summary "<purpose>"
```

Supported kinds are `tool`, `dashboard`, `guided`, `knowledge`, `game`, and `presentation`. Supported model capabilities are `none`, `text`, `vision`, `image`, and `code`.

Do not scaffold over a non-empty directory. Treat starters as interaction engines, not finished themes or domain implementations.

## Architecture Threshold

- Use one `index.html` for browser APIs, modest state, local data, ordinary model tools, and lightweight games.
- Keep small SVG, CSS, and JavaScript inline when that improves portability.
- Use separate local files only for large media, complex game logic, workers, WASM, or an HTML file that has become difficult to maintain.
- Keep the project purely static even when files are split.
- Do not introduce React, Tailwind, npm, or a build chain solely for visual polish.
- Do not add a manifest unless the user's own workflow requires metadata.

## Local Models

Keep model credentials outside the app. Never embed keys, tokens, or authorization headers in HTML.

Copy `.webapp.local.example.json` to `.webapp.local.json`, configure an OpenAI-compatible local endpoint and model, then run:

```bash
python3 scripts/webapp.py serve <folder> --open
```

The local server exposes same-origin `/runtime/ai/chat`, `/runtime/ai/image`, and `/runtime/health` routes. It reads credentials only from the environment variable named by `apiKeyEnv`.

For model-free apps, direct file opening can work when browser security rules allow it. Prefer the local server for reliable module loading, file access, clipboard behavior, and browser testing.

## Validate And Build

Run:

```bash
python3 scripts/webapp.py validate <html-file-or-folder>
python3 scripts/webapp.py validate <html-file-or-folder> --strict
python3 scripts/webapp.py build <folder> --out <app.zip>
python3 scripts/webapp.py build <folder> --out <app.zip> --force
```

Treat strict static validation as the quality floor, not visual proof. Test real inputs, invalid inputs, reset, copy/download, persistence, asynchronous failure, and keyboard navigation as applicable.

The build command refuses to overwrite an existing archive unless `--force` is explicit. It excludes `.webapp.local.json`, Git data, caches, existing zip files, and development output.

Run the repository self-check after changing this skill, its scripts, or its starters:

```bash
python3 scripts/check_skill.py
```

## Optional Cover Assets

Generate a local fallback cover and icon only when the user needs them:

```bash
python3 scripts/generate_cover.py <folder> \
  --title "<title>" \
  --summary "<purpose>" \
  --kind <kind>
```

Treat generated artwork as a safe fallback. For presentation-sensitive work, create content-specific artwork based on the actual concept.
