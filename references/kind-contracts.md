# Executable Kind Contracts

The canonical registry is [../assets/kind-contracts/index.json](../assets/kind-contracts/index.json). It upgrades base starters from layout shells into distinct interaction contracts.

Run:

```bash
python3 scripts/webapp.py contracts
python3 scripts/webapp.py contracts --json
```

Each contract records:

- the discipline that leads the artifact, such as interaction engineering, information design, service design, or editorial direction;
- a one-line design read and three 1-10 dials for variance, motion, and density;
- the subject-specific question that should shape the composition;
- useful axes for genuinely different design directions;
- required implementation markers and known failure modes.

The dials are decision defaults, not visual decoration. A dashboard starts dense and restrained because its job is comparison; a game starts more kinetic because feedback is part of the mechanic. Scaffolding writes the chosen contract and dials onto `<body>`, and strict validation checks that the starter's required workflow markers remain present.

Base contracts apply to `tool`, `dashboard`, `guided`, `knowledge`, `game`, and `presentation`. Domain-specific scenario blueprints take precedence because their content contract is stronger. `motion` keeps its dedicated timeline contract.

Before adapting a base starter, state its design read in project terms and answer its signature question. Replace sample content with real vocabulary and evidence. Do not preserve a marker by leaving an irrelevant control or section in place.
