# Machine-readable Style Registry

The canonical registry is [../assets/style-packs/index.json](../assets/style-packs/index.json). It contains deliberately separated visual families suitable for benchmark sampling, scaffold seeding, and deterministic filtering.

Run:

```bash
python3 scripts/webapp.py styles
python3 scripts/webapp.py styles --deliverable infographic --kind dashboard
python3 scripts/webapp.py styles --collection professional-workplace
python3 scripts/webapp.py styles --collection industrial-engineering
python3 scripts/webapp.py styles --json
```

## Selection Order

1. Choose the deliverable contract.
2. Choose the interaction kind.
3. Remove styles that conflict with content, audience, accessibility, or required asset availability.
4. Prefer a style with high HTML fidelity when the artifact cannot depend on custom illustration, photography, or generated media.
5. Use the selected family as a coherent system: hierarchy, spacing, geometry, information density, imagery, and motion—not merely its palette. For a `motion` deliverable, style is applied to the animated stage, timeline, and control states—not to a slide deck by default.
6. When brand requirements exist, brand identity wins. Use a style family only for composition vocabulary unless the brand explicitly permits token changes.

Scenario and style are independent. A scenario's `defaultStyle` is a useful prior, not a compatibility lock. Preserve the scenario's task and marker contract when changing its visual family.

The registry is a set of direction seeds, not finished themes. `scaffold --style <id>` writes semantic color, font, border, radius, and shadow tokens into the starter, then the implementation must express the family’s signature in the actual content and layout.

## Workplace Collections

- `professional-workplace`: executive briefings, institutional communication, finance, and quality management.
- `industrial-engineering`: industrial control, manufacturing quality, engineering blueprints, and intentionally raw industrial communication.
- `technology-operations`: future-facing product language, mission control, technical systems, and scientific analysis.
- `clean-product`: restrained SaaS interfaces, executive clarity, Swiss grids, and approachable data products.

Collections are discovery filters. They do not add another visual layer and do not prevent a style from being used outside its collection.

## Schema

The root object contains:

- `schemaVersion`: integer registry contract version.
- `defaultStyle`: fallback style ID for explicit registry consumers. Scaffolding does not apply it implicitly.
- `collections`: named arrays of style IDs for machine-readable discovery and filtering.
- `styles`: ordered array of style profiles.

Every style profile contains:

- `id`, `name`, `description`, and `signature`.
- `routingAliases`: multilingual brief cues used by deterministic style recommendation.
- `inspiration`: design traditions, not a license to imitate a named product.
- `compatibleDeliverables` and `compatibleKinds`: filtering priors, not hard restrictions.
- `mood`, `formality`, `density`, and `scheme`.
- `htmlFidelity`: 0–100 estimate of how faithfully the direction can be expressed in portable HTML without external media.
- `assetNeeds`: `none`, `optional`, `recommended`, or `required`.
- `bestFor` and `avoidFor`.
- `tokens.colors`: `background`, `surface`, `text`, `muted`, `accent`, `secondary`, and `line`, all `#RRGGBB`.
- `tokens.fonts`: portable CSS stacks for `display`, `body`, and `data`.
- `tokens.geometry`: CSS values for `radius`, `borderWidth`, and `shadow`.

## Benchmark Axes

Sample across more than style ID. At minimum record:

- deliverable type and interaction kind;
- style ID and whether requested assets were available;
- density target on a 1–10 scale;
- light, dark, or mixed scheme;
- responsive widths tested;
- task completion, content preservation, accessibility, overflow, and visual-family recognizability.

Do not reward superficial palette matching. A result belongs to a style family only when its composition, typography, geometry, density, and information treatment express the registered signature.

In the optimization repository, run `python3 benchmarks/style-recognizability/run.py` to enforce token fidelity, style-specific structural features, working interaction evidence, and pairwise structural diversity for the workplace validation set.
