# Deliverable Types

Choose a deliverable type before choosing the interaction kind. The deliverable describes what the artifact must accomplish; the kind describes the HTML interaction engine used to accomplish it. They are orthogonal.

The complete taxonomy is:

- `application`: an operational browser app. Inferred for `tool`, `dashboard`, `guided`, and `knowledge` when no type is supplied.
- `marketing`: persuasion, launch, conversion, campaign, or brand storytelling.
- `prototype`: a testable product concept, service flow, or interaction hypothesis.
- `infographic`: visual explanation, comparison, process, map, timeline, or data story.
- `motion`: a time-based HTML composition, animated explainer, kinetic poster, or interactive sequence. Use the dedicated `motion` kind for actual animation; `presentation` remains a slide narrative.
- `document`: a reading-first report, guide, case study, manual, or long-form narrative.
- `game`: a closed play loop. Inferred for the `game` kind.
- `presentation`: a navigable slide narrative. Inferred for the `presentation` kind.

## Routing Matrix

Use the existing kinds as starter topologies rather than as visual themes.

| Deliverable | Common kinds | Primary contract |
| --- | --- | --- |
| `marketing` | `knowledge`, `guided`, `presentation` | One audience, one proposition, one primary action, evidence before decoration. |
| `prototype` | `tool`, `guided`, `dashboard`, `knowledge` | The riskiest interaction must be functional and testable with realistic states. |
| `infographic` | `dashboard`, `knowledge`, `presentation` | Reading order, labels, units, sources, and a plain-language takeaway must survive at narrow width. |
| `motion` | `motion`, `presentation`, `game`, `knowledge` | Motion must carry meaning, have deterministic timing, and respect reduced-motion preferences. |
| `document` | `knowledge`, `presentation` | Strong outline, stable anchors, readable measure, print behavior, and source/evidence treatment. |

Do not reject an unusual combination automatically. A marketing calculator may legitimately use `tool`; an interactive document may use `guided`. Treat the matrix as a routing prior and record the reason when departing from it.

## Deliverable Contracts

### Marketing

- Establish the audience, offer, proof, objections, and primary conversion action.
- Create a narrative sequence instead of a generic stack of feature cards.
- Use repeated calls to action sparingly and keep their wording consistent.
- Distinguish factual proof from aspirational language. Never invent customers, metrics, or endorsements.
- Test whether the value proposition is still clear with imagery hidden.

### Prototype

- State the hypothesis and the user decision or behavior being tested.
- Implement the critical path and its empty, ready, success, partial, error, and reset states.
- Use realistic content and data shape; label simulations clearly.
- Keep secondary navigation and settings shallow unless they are part of the hypothesis.
- Capture observable test points such as completion, comprehension, confidence, or recovery.

### Infographic

- Write the takeaway before choosing a chart or diagram.
- Use position and length before area, angle, or decorative volume for quantitative comparison.
- Label units, periods, baselines, uncertainty, and sources near the evidence they qualify.
- Preserve semantic HTML for labels; use SVG primarily for geometry and relationships.
- Provide a linear mobile reading order and a text equivalent for essential visual conclusions.

### Motion

- Define a scene list, timeline, and end state before animating.
- Animate changes of state, causality, sequence, attention, or spatial relationship.
- Avoid perpetual motion that competes with reading or control use.
- Implement `prefers-reduced-motion`; the reduced version must retain the narrative and controls.
- Make replay, pause, or direct navigation available when the sequence carries essential information.
- Prefer `--kind motion` for a true animation. Use `--kind presentation` only when the primary unit is a slide and motion is subordinate to slide transitions.

### Document

- Build an outline that remains understandable without decoration.
- Keep body measure near 55–75 characters and use stable heading anchors.
- Separate summary, evidence, interpretation, recommendation, and appendix when relevant.
- Provide print styles and prevent important figures, tables, or callouts from splitting badly.
- Preserve citation labels, source notes, and accessible table structure.

## Scaffold Examples

```bash
python3 scripts/webapp.py scaffold \
  --deliverable prototype \
  --kind guided \
  --style crafted-research \
  --out <folder> \
  --title "<title>" \
  --summary "<testable hypothesis>"
```

```bash
python3 scripts/webapp.py scaffold \
  --deliverable infographic \
  --kind dashboard \
  --style scientific-figure \
  --out <folder> \
  --title "<title>" \
  --summary "<evidence takeaway>"
```
