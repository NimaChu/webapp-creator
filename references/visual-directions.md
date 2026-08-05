# Visual Directions

Select a direction from the task, audience, and information structure. Do not expose these as a theme picker unless the user explicitly asks to compare alternatives.

## Routing Table

| Direction | Choose when | Avoid when | Scaffold |
| --- | --- | --- | --- |
| `workbench` | Repeated input, transform, inspect, copy, download, or batch actions | The task is primarily reading or a long guided process | `--kind tool --direction workbench` |
| `analytics` | Users compare measures, detect change, filter scope, and inspect details | Exact task completion matters more than monitoring | `--kind dashboard --direction analytics` |
| `guided` | Steps have dependencies, validation, review, or approval | Expert users repeat one compact action many times | `--kind tool --direction guided` |
| `knowledge` | Users search, read, summarize, connect, or organize information | The interface is mainly a calculator or generator | `--kind tool --direction knowledge` |
| `ai-studio` | Prompt, parameters, generation progress, result review, and export form one workflow | AI is a hidden implementation detail rather than the user's task | `--kind eqai-ai --direction ai-studio` |

Presentations use `--kind presentation --direction auto`. This selects a delivery engine rather than a visual theme. Define the deck's visual system from its subject, audience, venue, and narrative as described in [presentation-guide.md](presentation-guide.md).

## Shared KOSTAL Baseline

- Optimize internal tools for laptop and desktop use, then make them robust at narrow widths.
- Use light neutral surfaces and readable dark text.
- Use shallow green for normal actions and success. Use KOSTAL blue as a structural or informational color.
- Use red only for destructive actions and genuine errors.
- Prefer clear grids, compact labels, restrained borders, and deliberate whitespace.
- Keep wording factual, calm, and recognizable to the user.
- Use as many elements as necessary and as few as possible.

## Workbench

Make the input, primary command, output, and output actions visible in the first viewport. Use a compact toolbar or split workspace. Keep advanced options behind a disclosure, settings panel, or secondary row.

Useful signature: expose the transformation as a clear before/after structure, a validation rail, or a compact result anatomy related to the domain.

Avoid interchangeable card grids, oversized headings, and a large empty result panel with no guidance.

## Analytics

Start with scope and freshness, then orient with only the measures needed to interpret the main comparison. Show drivers and exceptions before the full detail table. Keep filters synchronized across charts and tables.

Useful signature: choose one domain-relevant comparison treatment such as a tolerance band, process stage strip, capacity map, or variance column.

Avoid filling the first viewport with equal KPI cards or decorating every metric with a different color.

## Guided

Show current position, completed steps, validation, and the final review state. Keep related controls together and preserve entered values when navigating backward or recovering from errors.

Useful signature: make the step model reflect the real process, not generic `01 / 02 / 03` decoration.

Avoid wizard behavior for a task that experts could complete faster in one compact form.

## Knowledge

Prioritize navigation, search, reading rhythm, and relationships between pieces of information. Use a restrained reading width, visible hierarchy, and adjacent notes or metadata only when they support comprehension.

Useful signature: use the subject's true structure, such as process stages, document sections, decision records, glossary links, or source traceability.

Avoid turning every paragraph into a card or using editorial decoration unrelated to the material.

## AI Studio

Treat the prompt, relevant parameters, progress, outputs, and reusable actions as one production workflow. Keep AI provider and model implementation details outside the interface unless the user controls them legitimately.

Useful signature: make result comparison, provenance, variation, or iteration history specific to the generated artifact.

Avoid purple gradients, chat bubbles for non-conversational tasks, fake assistant personalities, and controls that do not affect the result.

## Two-Pass Design Check

Before coding, define the direction, palette, type roles, layout, and one useful signature. Then challenge it:

1. Could this exact page fit a different domain after changing only the heading?
2. Does each structural device encode real meaning?
3. Is the memorable element helping users scan, decide, or complete work?
4. Is complexity proportional to the task?

Revise any generic answer before implementation. For operational interfaces, a memorable information treatment is enough; do not take a decorative visual risk merely to appear distinctive.
