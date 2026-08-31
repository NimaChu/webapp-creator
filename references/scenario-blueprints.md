# Scenario Blueprints

Scenario blueprints are benchmark fixtures with domain-specific implementation contracts. They prevent a deliverable type from becoming a generic starter with a new title.

List the machine-readable registry with:

```bash
python3 scripts/webapp.py scenarios --json
```

Scaffold a blueprint with `--scenario <id>`. The blueprint supplies its kind, deliverable type, default style family, HTML template, and required markers. `--style <id>` may freely replace `defaultStyle`; the validator preserves the scenario contract while independently checking that the selected style is registered.

Use `recommend --brief "<request>" --json` to select a single blueprint or a compatible composition. In a composition, use the first scenario as the page shell, add supporting scenarios as complete functional modules, record all IDs in `data-scenarios`, and preserve the union of their required markers. See [request-routing.md](request-routing.md).

Use the fixture as a working composition, not factual content. Replace explicitly labeled sample evidence, measures, sources, and decisions with traceable domain information before delivery. Keep the contract while adapting its visual direction and content density to the audience.

Registry version 2 fields separate concerns: `deliverable`, `kind`, `template`, `contract`, and `requiredMarkers` define the scenario; `defaultStyle` is a fallback only; `keywords` support brief matching; and `composeWith` declares safe composition candidates.

Current coverage:

- `marketing-event-launch`: an offer, proof, program, and single reservation action.
- `prototype-route-planner`: constraints, a controllable recommendation, and a visible explanation of the tradeoff.
- `infographic-energy-story`: a named takeaway, units, method/source, and an action-oriented reading path.
- `document-walkability-brief`: an outline, evidence, recommendations, limitations, and print-safe reading treatment.
- `motion-load-shift`: a timeline story with transport controls and reduced-motion fallback.
- `game-last-train-dispatch`: a playable final-train dispatch loop with explicit objective, immediate result states, replay, and local best-score persistence.
