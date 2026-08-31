#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path


KINDS = {"tool", "dashboard", "guided", "knowledge", "game", "presentation", "motion"}
DELIVERABLE_TYPES = {
    "application", "marketing", "prototype", "infographic", "motion",
    "document", "game", "presentation",
}
DEFAULT_DELIVERABLE_FOR_KIND = {
    "tool": "application",
    "dashboard": "application",
    "guided": "application",
    "knowledge": "application",
    "game": "game",
    "presentation": "presentation",
    "motion": "motion",
}
DEFAULT_KIND_FOR_DELIVERABLE = {
    "application": "tool",
    "marketing": "knowledge",
    "prototype": "guided",
    "infographic": "dashboard",
    "motion": "motion",
    "document": "knowledge",
    "game": "game",
    "presentation": "presentation",
}


def _asset_path(*parts: str) -> Path:
    return Path(__file__).resolve().parents[1].joinpath("assets", *parts)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _load_json(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(_read(path))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"Invalid {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{label.title()} must be a JSON object")
    return value


def _css_value(value: object, label: str) -> str:
    text = str(value).strip()
    if not text or any(token in text for token in ("{", "}", ";", "</style")):
        raise SystemExit(f"Invalid CSS value for {label}")
    return text


def load_kind_contracts() -> dict[str, object]:
    path = _asset_path("kind-contracts", "index.json")
    registry = _load_json(path, "kind contract registry")
    contracts = registry.get("contracts")
    if registry.get("schemaVersion") != 1 or not isinstance(contracts, list) or not contracts:
        raise SystemExit("Kind contract registry must be a non-empty version 1 JSON object")
    required = {
        "id", "kind", "leadRole", "designRead", "dials", "signatureQuestion",
        "directionAxes", "requiredMarkers", "failureModes",
    }
    identifiers: set[str] = set()
    kinds: set[str] = set()
    for contract in contracts:
        if not isinstance(contract, dict) or required - set(contract):
            missing = sorted(required - set(contract)) if isinstance(contract, dict) else sorted(required)
            raise SystemExit(f"Kind contract is missing: {', '.join(missing)}")
        identifier = str(contract["id"])
        kind = str(contract["kind"])
        if not re.fullmatch(r"[a-z][a-z0-9-]*", identifier) or identifier in identifiers:
            raise SystemExit(f"Invalid or duplicate kind contract id: {identifier}")
        if kind not in KINDS or kind in kinds:
            raise SystemExit(f"Invalid or duplicate kind contract kind: {kind}")
        identifiers.add(identifier)
        kinds.add(kind)
        dials = contract["dials"]
        if not isinstance(dials, dict) or set(dials) != {"variance", "motion", "density"}:
            raise SystemExit(f"Kind contract {identifier} has invalid dials")
        if not all(isinstance(value, int) and 1 <= value <= 10 for value in dials.values()):
            raise SystemExit(f"Kind contract {identifier} dials must be integers from 1 to 10")
        for key in ("directionAxes", "requiredMarkers", "failureModes"):
            values = contract[key]
            if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
                raise SystemExit(f"Kind contract {identifier} has invalid {key}")
    return registry


def kind_contract(kind: str) -> dict[str, object]:
    contracts = load_kind_contracts()["contracts"]
    assert isinstance(contracts, list)
    for contract in contracts:
        if isinstance(contract, dict) and contract.get("kind") == kind:
            return contract
    raise SystemExit(f"No kind contract is registered for: {kind}")


def contract_by_id(value: str) -> dict[str, object]:
    contracts = load_kind_contracts()["contracts"]
    assert isinstance(contracts, list)
    for contract in contracts:
        if isinstance(contract, dict) and contract.get("id") == value:
            return contract
    raise SystemExit(f"Unknown kind contract: {value}")


def load_style_registry() -> dict[str, object]:
    path = _asset_path("style-packs", "index.json")
    registry = _load_json(path, "style registry")
    if registry.get("schemaVersion") != 3:
        raise SystemExit("Style registry must be a version 3 JSON object")
    styles = registry.get("styles")
    if not isinstance(styles, list) or not styles:
        raise SystemExit("Style registry must contain a non-empty styles array")
    required = {
        "id", "name", "description", "inspiration", "compatibleDeliverables",
        "compatibleKinds", "mood", "formality", "density", "scheme",
        "htmlFidelity", "assetNeeds", "bestFor", "avoidFor", "signature",
        "routingAliases", "tokens",
    }
    color_keys = {"background", "surface", "text", "muted", "accent", "secondary", "line"}
    font_keys = {"display", "body", "data"}
    geometry_keys = {"radius", "borderWidth", "shadow"}
    identifiers: set[str] = set()
    for style in styles:
        if not isinstance(style, dict) or required - set(style):
            missing = sorted(required - set(style)) if isinstance(style, dict) else sorted(required)
            raise SystemExit(f"Style registry entry is missing: {', '.join(missing)}")
        identifier = str(style["id"])
        if not re.fullmatch(r"[a-z][a-z0-9-]*", identifier) or identifier in identifiers:
            raise SystemExit(f"Invalid or duplicate style id: {identifier}")
        identifiers.add(identifier)
        deliverables = style["compatibleDeliverables"]
        kinds = style["compatibleKinds"]
        if not isinstance(deliverables, list) or set(deliverables) - DELIVERABLE_TYPES:
            raise SystemExit(f"Style {identifier} has invalid deliverable compatibility")
        if not isinstance(kinds, list) or set(kinds) - KINDS:
            raise SystemExit(f"Style {identifier} has invalid kind compatibility")
        density = style["density"]
        if not isinstance(density, dict) or set(density) != {"min", "default", "max"}:
            raise SystemExit(f"Style {identifier} has an invalid density range")
        values = [density["min"], density["default"], density["max"]]
        if not all(isinstance(item, int) for item in values) or not (1 <= values[0] <= values[1] <= values[2] <= 10):
            raise SystemExit(f"Style {identifier} density must be ordered from 1 to 10")
        if style["scheme"] not in {"light", "dark", "mixed"}:
            raise SystemExit(f"Style {identifier} has an invalid scheme")
        if style["assetNeeds"] not in {"none", "optional", "recommended", "required"}:
            raise SystemExit(f"Style {identifier} has invalid assetNeeds")
        aliases = style["routingAliases"]
        if not isinstance(aliases, list) or not aliases or not all(isinstance(item, str) and item for item in aliases):
            raise SystemExit(f"Style {identifier} has invalid routingAliases")
        fidelity = style["htmlFidelity"]
        if not isinstance(fidelity, int) or not 0 <= fidelity <= 100:
            raise SystemExit(f"Style {identifier} htmlFidelity must be from 0 to 100")
        tokens = style["tokens"]
        if not isinstance(tokens, dict):
            raise SystemExit(f"Style {identifier} tokens must be an object")
        colors, fonts, geometry = tokens.get("colors"), tokens.get("fonts"), tokens.get("geometry")
        if not isinstance(colors, dict) or set(colors) != color_keys:
            raise SystemExit(f"Style {identifier} colors must use the semantic color schema")
        if not isinstance(fonts, dict) or set(fonts) != font_keys:
            raise SystemExit(f"Style {identifier} fonts must use the semantic font schema")
        if not isinstance(geometry, dict) or set(geometry) != geometry_keys:
            raise SystemExit(f"Style {identifier} geometry must use the geometry schema")
        for key, color in colors.items():
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(color)):
                raise SystemExit(f"Style {identifier} color {key} must be #RRGGBB")
        for key, item in {**fonts, **geometry}.items():
            _css_value(item, f"styles.{identifier}.{key}")
    default_style = str(registry.get("defaultStyle", ""))
    if default_style not in identifiers:
        raise SystemExit("Style registry defaultStyle does not identify a registered style")
    collections = registry.get("collections")
    if not isinstance(collections, dict) or not collections:
        raise SystemExit("Style registry must define non-empty collections")
    for name, members in collections.items():
        if not re.fullmatch(r"[a-z][a-z0-9-]*", str(name)):
            raise SystemExit(f"Invalid style collection id: {name}")
        if not isinstance(members, list) or not members or len(members) != len(set(members)) or set(members) - identifiers:
            raise SystemExit(f"Style collection {name} has invalid members")
    return registry


def style_by_id(value: str) -> dict[str, object]:
    styles = load_style_registry()["styles"]
    assert isinstance(styles, list)
    for style in styles:
        if isinstance(style, dict) and style.get("id") == value:
            return style
    raise SystemExit(f"Unknown style: {value}")


def style_replacements(value: str | None) -> dict[str, str]:
    if not value:
        return {"__STYLE_ID__": "custom", "__STYLE_CSS__": ""}
    style = style_by_id(value)
    tokens = style["tokens"]
    assert isinstance(tokens, dict)
    colors, fonts, geometry = tokens["colors"], tokens["fonts"], tokens["geometry"]
    assert isinstance(colors, dict) and isinstance(fonts, dict) and isinstance(geometry, dict)
    css = f"""
    /* Registry style seed: {style['name']} ({style['id']}). Adapt composition to its signature. */
    :root {{
      --bg: {colors['background']}; --paper: {colors['background']};
      --surface: {colors['surface']}; --text: {colors['text']}; --ink: {colors['text']};
      --muted: {colors['muted']}; --accent: {colors['accent']};
      --secondary: {colors['secondary']}; --line: {colors['line']};
      --display-font: {fonts['display']}; --body-font: {fonts['body']}; --data-font: {fonts['data']};
      --style-radius: {geometry['radius']}; --style-border-width: {geometry['borderWidth']};
      --style-shadow: {geometry['shadow']};
    }}
    body {{ font-family: var(--body-font); }}
    h1, h2, h3, .display {{ font-family: var(--display-font); }}
    code, pre, output, .metric, .eyebrow {{ font-family: var(--data-font); }}
    button, input, select, textarea, .card, .panel {{ border-radius: var(--style-radius); border-width: var(--style-border-width); }}
    .card, .panel {{ box-shadow: var(--style-shadow); }}
    """.strip()
    return {
        "__STYLE_ID__": html.escape(str(style["id"]), quote=True),
        "__STYLE_CSS__": css,
    }


def load_scenario_blueprints() -> dict[str, object]:
    path = _asset_path("scenario-blueprints", "index.json")
    registry = _load_json(path, "scenario blueprint registry")
    scenarios = registry.get("scenarios")
    if registry.get("schemaVersion") != 2 or not isinstance(scenarios, list) or not scenarios:
        raise SystemExit("Scenario blueprint registry must be a non-empty version 2 JSON object")
    required = {
        "id", "name", "deliverable", "kind", "defaultStyle", "template",
        "contract", "requiredMarkers", "keywords", "composeWith",
    }
    identifiers: set[str] = set()
    asset_root = path.parents[1].resolve()
    for scenario in scenarios:
        if not isinstance(scenario, dict) or required - set(scenario):
            missing = sorted(required - set(scenario)) if isinstance(scenario, dict) else sorted(required)
            raise SystemExit(f"Scenario blueprint is missing: {', '.join(missing)}")
        identifier = str(scenario["id"])
        if not re.fullmatch(r"[a-z][a-z0-9-]*", identifier) or identifier in identifiers:
            raise SystemExit(f"Invalid or duplicate scenario id: {identifier}")
        identifiers.add(identifier)
        if scenario["deliverable"] not in DELIVERABLE_TYPES or scenario["kind"] not in KINDS:
            raise SystemExit(f"Scenario {identifier} has an invalid deliverable or kind")
        style_by_id(str(scenario["defaultStyle"]))
        template = (path.parent / str(scenario["template"])).resolve()
        if not template.is_file() or not template.is_relative_to(asset_root):
            raise SystemExit(f"Scenario {identifier} template is missing or outside assets")
        markers = scenario["requiredMarkers"]
        if not isinstance(markers, list) or not markers or not all(isinstance(item, str) and item for item in markers):
            raise SystemExit(f"Scenario {identifier} must define non-empty requiredMarkers")
        if any(marker not in _read(template) for marker in markers):
            raise SystemExit(f"Scenario {identifier} template is missing a required marker")
        keywords = scenario["keywords"]
        if not isinstance(keywords, list) or not keywords or not all(isinstance(item, str) and item for item in keywords):
            raise SystemExit(f"Scenario {identifier} must define non-empty keywords")
        compose_with = scenario["composeWith"]
        if not isinstance(compose_with, list) or not all(isinstance(item, str) and item for item in compose_with):
            raise SystemExit(f"Scenario {identifier} has invalid composeWith")
    for scenario in scenarios:
        identifier = str(scenario["id"])
        unknown = set(scenario["composeWith"]) - identifiers
        if identifier in scenario["composeWith"] or unknown:
            raise SystemExit(f"Scenario {identifier} has invalid composeWith references")
    return registry


def scenario_by_id(value: str) -> dict[str, object]:
    scenarios = load_scenario_blueprints()["scenarios"]
    assert isinstance(scenarios, list)
    for scenario in scenarios:
        if isinstance(scenario, dict) and scenario.get("id") == value:
            return scenario
    raise SystemExit(f"Unknown scenario: {value}")


def scenario_template_path(scenario: dict[str, object]) -> Path:
    return (_asset_path("scenario-blueprints") / str(scenario["template"])).resolve()
