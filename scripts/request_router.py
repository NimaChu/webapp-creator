#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from design_registry import (
    DEFAULT_DELIVERABLE_FOR_KIND,
    DEFAULT_KIND_FOR_DELIVERABLE,
    DELIVERABLE_TYPES,
    KINDS,
    kind_contract,
    load_scenario_blueprints,
    load_style_registry,
)


def _matched_phrases(text: str, phrases: list[str]) -> list[str]:
    lowered = text.casefold()
    return [phrase for phrase in phrases if phrase.casefold() in lowered]


def load_request_routing() -> dict[str, object]:
    path = Path(__file__).resolve().parents[1] / "assets" / "request-routing" / "index.json"
    try:
        registry = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"Invalid request routing registry {path}: {exc}") from exc
    if not isinstance(registry, dict) or registry.get("schemaVersion") != 1:
        raise SystemExit("Request routing registry must be a version 1 JSON object")
    required = {
        "deliverableSignals", "kindSignals", "genericScenarioTerms",
        "compositionSignals", "schemeSignals", "dials",
    }
    if required - set(registry):
        raise SystemExit("Request routing registry is incomplete")
    deliverable_signals = registry["deliverableSignals"]
    kind_signals = registry["kindSignals"]
    if not isinstance(deliverable_signals, dict) or set(deliverable_signals) != DELIVERABLE_TYPES:
        raise SystemExit("Request routing deliverableSignals must cover every deliverable")
    if not isinstance(kind_signals, dict) or set(kind_signals) != KINDS:
        raise SystemExit("Request routing kindSignals must cover every kind")
    for group_name in ("deliverableSignals", "kindSignals", "schemeSignals"):
        group = registry[group_name]
        if not isinstance(group, dict):
            raise SystemExit(f"Request routing {group_name} must be an object")
        for key, phrases in group.items():
            if not isinstance(phrases, list) or not phrases or not all(isinstance(item, str) and item for item in phrases):
                raise SystemExit(f"Request routing {group_name}.{key} must contain phrases")
    for key in ("genericScenarioTerms", "compositionSignals"):
        phrases = registry[key]
        if not isinstance(phrases, list) or not phrases or not all(isinstance(item, str) and item for item in phrases):
            raise SystemExit(f"Request routing {key} must contain phrases")
    dials = registry["dials"]
    if not isinstance(dials, dict) or "defaults" not in dials:
        raise SystemExit("Request routing dials are incomplete")
    defaults = dials["defaults"]
    if not isinstance(defaults, dict) or set(defaults) != {"variance", "motion", "density"}:
        raise SystemExit("Request routing dial defaults are invalid")
    return registry


def infer_request_signals(brief: str) -> dict[str, object]:
    routing = load_request_routing()
    deliverable_signals = routing["deliverableSignals"]
    kind_signals = routing["kindSignals"]
    assert isinstance(deliverable_signals, dict) and isinstance(kind_signals, dict)
    deliverables = [
        name for name, phrases in deliverable_signals.items()
        if isinstance(phrases, list) and _matched_phrases(brief, phrases)
    ]
    kinds = [
        name for name, phrases in kind_signals.items()
        if isinstance(phrases, list) and _matched_phrases(brief, phrases)
    ]
    scheme = None
    scheme_signals = routing["schemeSignals"]
    assert isinstance(scheme_signals, dict)
    for candidate, phrases in scheme_signals.items():
        assert isinstance(phrases, list)
        if _matched_phrases(brief, phrases):
            scheme = candidate
            break

    dial_config = routing["dials"]
    assert isinstance(dial_config, dict)
    defaults = dial_config["defaults"]
    assert isinstance(defaults, dict)
    dials = {key: int(value) for key, value in defaults.items()}
    for key, dial_name, mode in (
        ("varianceHigh", "variance", "max"),
        ("varianceLow", "variance", "min"),
        ("motionMedium", "motion", "set"),
        ("motionLow", "motion", "set"),
        ("densityHigh", "density", "max"),
        ("densityLow", "density", "set"),
    ):
        rule = dial_config[key]
        assert isinstance(rule, dict)
        phrases = rule["signals"]
        assert isinstance(phrases, list)
        if _matched_phrases(brief, phrases):
            target = int(rule["target"])
            if mode == "max":
                dials[dial_name] = max(dials[dial_name], target)
            elif mode == "min":
                dials[dial_name] = min(dials[dial_name], target)
            else:
                dials[dial_name] = target
    high_kinds = dial_config["motionHighKinds"]
    high_deliverables = dial_config["motionHighDeliverables"]
    assert isinstance(high_kinds, list) and isinstance(high_deliverables, list)
    if set(kinds) & set(high_kinds) or set(deliverables) & set(high_deliverables):
        dials["motion"] = int(dial_config["motionHighTarget"])
    dense_kinds = dial_config["densityHighKinds"]
    assert isinstance(dense_kinds, list)
    if set(kinds) & set(dense_kinds):
        density_rule = dial_config["densityHigh"]
        assert isinstance(density_rule, dict)
        dials["density"] = max(dials["density"], int(density_rule["target"]))
    return {"deliverables": deliverables, "kinds": kinds, "scheme": scheme, "dials": dials}


def _score_scenario(
    scenario: dict[str, object], brief: str, signals: dict[str, object],
    deliverable: str | None, kind: str | None,
) -> tuple[int, list[str]]:
    score = 1
    reasons: list[str] = []
    keywords = scenario["keywords"]
    assert isinstance(keywords, list)
    matches = _matched_phrases(brief, keywords)
    if matches:
        score += min(24, len(matches) * 6)
        reasons.append(f"brief keywords: {', '.join(matches[:4])}")
    inferred_deliverables = signals["deliverables"]
    inferred_kinds = signals["kinds"]
    assert isinstance(inferred_deliverables, list) and isinstance(inferred_kinds, list)
    if deliverable:
        if scenario["deliverable"] == deliverable:
            score += 24
            reasons.append(f"requested deliverable: {deliverable}")
        else:
            score -= 10
    elif scenario["deliverable"] in inferred_deliverables:
        score += 12
        reasons.append(f"inferred deliverable: {scenario['deliverable']}")
    if kind:
        if scenario["kind"] == kind:
            score += 18
            reasons.append(f"requested kind: {kind}")
        else:
            score -= 8
    elif scenario["kind"] in inferred_kinds:
        score += 8
        reasons.append(f"inferred kind: {scenario['kind']}")
    return score, reasons


def recommend_for_brief(
    brief: str,
    *,
    deliverable: str | None = None,
    kind: str | None = None,
    scheme: str | None = None,
    max_scenarios: int = 3,
    style_count: int = 3,
) -> dict[str, object]:
    routing = load_request_routing()
    signals = infer_request_signals(brief)
    scenarios = load_scenario_blueprints()["scenarios"]
    assert isinstance(scenarios, list)
    ranked_scenarios: list[tuple[int, dict[str, object], list[str]]] = []
    for scenario in scenarios:
        assert isinstance(scenario, dict)
        score, reasons = _score_scenario(scenario, brief, signals, deliverable, kind)
        ranked_scenarios.append((score, scenario, reasons))
    ranked_scenarios.sort(key=lambda item: item[0], reverse=True)
    primary_score, primary, primary_reasons = ranked_scenarios[0]

    primary_keywords = primary["keywords"]
    generic_terms = routing["genericScenarioTerms"]
    assert isinstance(primary_keywords, list) and isinstance(generic_terms, list)
    generic_casefold = {term.casefold() for term in generic_terms}
    has_domain_evidence = any(
        value.casefold() not in generic_casefold
        for value in _matched_phrases(brief, primary_keywords)
    )
    inferred_kinds = signals["kinds"]
    inferred_deliverables = signals["deliverables"]
    assert isinstance(inferred_kinds, list) and isinstance(inferred_deliverables, list)
    inferred_primary_deliverable = deliverable or (
        str(inferred_deliverables[0]) if inferred_deliverables else None
    )
    fallback_kind = kind or (str(inferred_kinds[0]) if inferred_kinds else None) or (
        DEFAULT_KIND_FOR_DELIVERABLE[inferred_primary_deliverable]
        if inferred_primary_deliverable else None
    )
    if fallback_kind and not has_domain_evidence:
        fallback_deliverable = deliverable or (
            str(inferred_deliverables[0])
            if inferred_deliverables else DEFAULT_DELIVERABLE_FOR_KIND[fallback_kind]
        )
        contract = kind_contract(fallback_kind) if fallback_kind != "motion" else None
        primary = {
            "id": f"base-{fallback_kind}",
            "name": f"{fallback_kind.title()} base contract",
            "deliverable": fallback_deliverable,
            "kind": fallback_kind,
            "defaultStyle": str(load_style_registry()["defaultStyle"]),
            "composeWith": [],
            "contract": contract["designRead"] if contract else "A real time-based HTML composition with playback and reduced-motion access.",
            "requiredMarkers": contract["requiredMarkers"] if contract else ["data-motion-story"],
            "sourceType": "kind-contract",
        }
        primary_score = 20
        primary_reasons = [f"generic {fallback_kind} request; use the base contract"]

    composition_signals = routing["compositionSignals"]
    assert isinstance(composition_signals, list)
    composition_signal = len(inferred_deliverables) > 1 or bool(
        _matched_phrases(brief, composition_signals)
    )
    selected_scenarios = [(primary_score, primary, primary_reasons)]
    if composition_signal and max_scenarios > 1 and primary.get("sourceType") != "kind-contract":
        composable = set(primary["composeWith"])
        for candidate in ranked_scenarios[1:]:
            score, scenario, _ = candidate
            if score >= 8 and scenario["id"] in composable and scenario["deliverable"] != primary["deliverable"]:
                selected_scenarios.append(candidate)
            if len(selected_scenarios) >= max_scenarios:
                break

    selected_deliverables = {str(item[1]["deliverable"]) for item in selected_scenarios}
    selected_kinds = {str(item[1]["kind"]) for item in selected_scenarios}
    requested_scheme = scheme or (str(signals["scheme"]) if signals["scheme"] else None)
    dials = signals["dials"]
    assert isinstance(dials, dict)
    style_registry = load_style_registry()
    styles = style_registry["styles"]
    assert isinstance(styles, list)
    ranked_styles: list[tuple[int, dict[str, object], list[str]]] = []
    for style in styles:
        assert isinstance(style, dict)
        style_score = 0
        reasons: list[str] = []
        delivery_matches = selected_deliverables & set(style["compatibleDeliverables"])
        kind_matches = selected_kinds & set(style["compatibleKinds"])
        style_score += len(delivery_matches) * 4 + len(kind_matches) * 3
        if delivery_matches:
            reasons.append("deliverable compatibility")
        if kind_matches:
            reasons.append("kind compatibility")
        aliases = style["routingAliases"]
        assert isinstance(aliases, list)
        alias_matches = _matched_phrases(brief, aliases)
        if alias_matches:
            style_score += min(36, len(alias_matches) * 12)
            reasons.append(f"style cues: {', '.join(alias_matches[:3])}")
        if style["id"] == primary["defaultStyle"]:
            style_score += 3
            reasons.append("scenario default")
        if requested_scheme:
            if style["scheme"] in {requested_scheme, "mixed"}:
                style_score += 6
                reasons.append(f"{requested_scheme} scheme")
            else:
                style_score -= 4
        density = style["density"]
        assert isinstance(density, dict)
        style_score += max(0, 4 - abs(int(density["default"]) - int(dials["density"])))
        avoid_for = style["avoidFor"]
        assert isinstance(avoid_for, list)
        if _matched_phrases(brief, avoid_for):
            style_score -= 8
            reasons.append("avoid-for conflict")
        ranked_styles.append((style_score, style, reasons))
    ranked_styles.sort(key=lambda item: item[0], reverse=True)
    style_options = [
        {"id": style["id"], "name": style["name"], "score": score,
         "reasons": reasons, "signature": style["signature"]}
        for score, style, reasons in ranked_styles[:style_count]
    ]
    selected_style = style_options[0]
    scenario_options = [
        {
            "id": scenario["id"], "name": scenario["name"],
            "role": "shell" if index == 0 else "module",
            "deliverable": scenario["deliverable"], "kind": scenario["kind"],
            "score": score, "reasons": reasons, "contract": scenario["contract"],
            "sourceType": scenario.get("sourceType", "scenario-blueprint"),
        }
        for index, (score, scenario, reasons) in enumerate(selected_scenarios)
    ]
    required_markers = list(dict.fromkeys(
        marker for _, scenario, _ in selected_scenarios for marker in scenario["requiredMarkers"]
    ))
    scenario_ids = [
        str(item[1]["id"]) for item in selected_scenarios
        if item[1].get("sourceType") != "kind-contract"
    ]
    primary_scenario_id = scenario_ids[0] if scenario_ids else "custom"
    return {
        "schemaVersion": 1,
        "brief": brief,
        "designRead": f"{primary['deliverable']}/{primary['kind']} via {primary['name']}; apply {selected_style['name']} as an independent visual system.",
        "inferredSignals": signals,
        "mode": "composition" if len(selected_scenarios) > 1 else "single",
        "scenarios": scenario_options,
        "selectedStyle": selected_style,
        "styleOptions": style_options,
        "buildContract": {
            "primaryDeliverable": primary["deliverable"],
            "primaryKind": primary["kind"],
            "scenarioIds": scenario_ids,
            "bodyAttributes": {
                "data-scenario": primary_scenario_id,
                "data-scenarios": ",".join(scenario_ids),
                "data-style": selected_style["id"],
            },
            "requiredMarkers": required_markers,
            "assemblyRule": "Use the primary scenario as the page shell; integrate supporting scenarios as task-complete modules, then apply one style system across the whole artifact.",
        },
        "scaffoldCommand": (
            "python3 scripts/webapp.py scaffold "
            + (f"--scenario {scenario_ids[0]} " if scenario_ids else f"--kind {primary['kind']} --deliverable {primary['deliverable']} ")
            + f"--style {selected_style['id']} "
            + '--out <folder> --title "<title>" --summary "<purpose>"'
        ),
    }
