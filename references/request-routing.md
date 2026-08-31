# Brief Routing

Treat scenario and style as independent axes:

```text
request = one primary scenario + optional supporting scenarios + one style system
```

Run the machine-readable router when the user names a goal but does not specify an exact starter:

```bash
python3 scripts/webapp.py recommend --brief "<user request>"
python3 scripts/webapp.py recommend --brief "<user request>" --json
```

The router reads output-type and interaction signals, scenario keywords, style aliases, light/dark preference, and three inferred dials: visual variance, motion intensity, and information density. Explicit `--deliverable`, `--kind`, and `--scheme` values override inference.

All deterministic routing vocabulary is stored in `assets/request-routing/index.json`. Edit and review that registry instead of adding signal-word tuples to Python. Scenario domain terms remain owned by `assets/scenario-blueprints/index.json`, while style aliases remain owned by `assets/style-packs/index.json`.

When a request identifies a generic interaction but does not match a domain blueprint, the router returns a `base-<kind>` selection backed by the executable kind contract. This keeps a generic dashboard, tool, guide, game, or presentation from being forced into an unrelated benchmark story.

## Single Scenario

Use the selected scenario as the implementation contract. Its `defaultStyle` is only a fallback. Apply the selected style independently:

```bash
python3 scripts/webapp.py scaffold \
  --scenario prototype-route-planner \
  --style industrial-brutalism \
  --out <folder> \
  --title "<title>" \
  --summary "<purpose>"
```

Changing style must not remove the scenario's workflow, states, evidence, or required markers. A style changes composition, typography, geometry, density, imagery, and motion language—not the task contract.

## Scenario Composition

When one request contains materially different jobs, the router may return `mode: composition`:

- The first scenario is the page shell and owns the primary deliverable and interaction kind.
- Supporting scenarios are task-complete modules, not visual cameos.
- Use one style system across the complete artifact.
- Put the primary ID in `data-scenario` and all IDs, in assembly order, in `data-scenarios`.
- Preserve the union of `buildContract.requiredMarkers`; the validator checks every listed scenario.

Do not concatenate full HTML documents. Start with the primary template, transplant the supporting scenario's semantic module, behavior, states, and required markers, then adapt that module to the selected style tokens and signature.

## Judgment

The router is a deterministic prior, not an authority. Correct it when domain facts, brand constraints, accessibility, assets, or an explicit user preference point elsewhere. Keep the final routing decision inspectable in the body metadata and benchmark record.
