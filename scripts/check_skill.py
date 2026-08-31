#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import local_runtime  # noqa: E402
import request_router  # noqa: E402
import webapp  # noqa: E402


def check_metadata() -> None:
    source = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", source, re.S)
    if not match:
        raise AssertionError("SKILL.md has no valid YAML frontmatter block")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise AssertionError(f"Invalid frontmatter line: {line}")
        fields[key.strip()] = value.strip()
    if set(fields) != {"name", "description"}:
        raise AssertionError("Frontmatter must contain only name and description")
    if fields["name"] != "html-design":
        raise AssertionError("Skill name must be html-design")
    if len(fields["description"]) < 80:
        raise AssertionError("Skill description is too short to trigger reliably")

    agent_source = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    for expected in ("display_name:", "short_description:", "$html-design"):
        if expected not in agent_source:
            raise AssertionError(f"agents/openai.yaml is missing {expected}")


def check_python_sources() -> None:
    for path in sorted(SCRIPTS.glob("*.py")):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def check_runtime_config() -> None:
    path = ROOT / "assets" / "local-config.example.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise AssertionError("Local runtime example must be a non-empty JSON object")
    if local_runtime._contains_forbidden_secret(data):
        raise AssertionError("Local runtime example contains a credential-like field")


def check_brand_packs() -> None:
    brand_root = ROOT / "assets" / "brand-packs"
    packs = sorted(brand_root.glob("*/brand.json"))
    if len(packs) < 3:
        raise AssertionError("Expected at least three reusable presentation brand packs")
    for path in packs:
        profile, resolved = webapp._load_brand(str(path))
        if resolved != path.resolve():
            raise AssertionError(f"Brand pack resolved unexpectedly: {path}")
        if not profile.get("layouts"):
            raise AssertionError(f"Brand pack has no layouts: {path}")


def check_style_registry() -> None:
    registry = webapp._load_style_registry()
    styles = registry["styles"]
    if not isinstance(styles, list) or len(styles) < 20:
        raise AssertionError("Expected at least twenty deliberately distinct style families")
    identifiers = {style["id"] for style in styles}
    workplace = {
        "executive-briefing", "saas-minimal", "engineering-blueprint",
        "industrial-control", "manufacturing-quality", "future-lab",
        "mission-control", "financial-analyst",
    }
    if workplace - identifiers:
        raise AssertionError(
            f"Workplace style families are missing: {', '.join(sorted(workplace - identifiers))}"
        )
    collections = registry["collections"]
    required_collections = {
        "professional-workplace", "industrial-engineering",
        "technology-operations", "clean-product",
    }
    if required_collections - set(collections):
        raise AssertionError("Workplace style collections are incomplete")
    deliverables = {
        deliverable
        for style in styles
        for deliverable in style["compatibleDeliverables"]
    }
    required = {"marketing", "prototype", "infographic", "motion", "document", "game"}
    if required - deliverables:
        raise AssertionError(
            f"Style registry does not cover: {', '.join(sorted(required - deliverables))}"
        )


def check_request_routing() -> None:
    registry = request_router.load_request_routing()
    if set(registry["deliverableSignals"]) != webapp.DELIVERABLE_TYPES:
        raise AssertionError("Routing vocabulary does not cover every deliverable")
    if set(registry["kindSignals"]) != webapp.KINDS:
        raise AssertionError("Routing vocabulary does not cover every interaction kind")
    source = (SCRIPTS / "request_router.py").read_text(encoding="utf-8")
    forbidden_tables = {"DELIVERABLE_SIGNALS", "KIND_SIGNALS", "GENERIC_SCENARIO_TERMS"}
    present = sorted(name for name in forbidden_tables if name in source)
    if present:
        raise AssertionError(f"Routing vocabulary leaked back into Python: {', '.join(present)}")
    result = request_router.recommend_for_brief("做一个深色实时设备监控台")
    signals = result["inferredSignals"]
    if signals["scheme"] != "dark" or "dashboard" not in signals["kinds"]:
        raise AssertionError("JSON-backed routing smoke test failed")


def check_kind_contracts() -> None:
    registry = webapp._load_kind_contracts()
    contracts = registry["contracts"]
    required = {"tool", "dashboard", "guided", "knowledge", "game", "presentation"}
    covered = {contract["kind"] for contract in contracts}
    if covered != required:
        raise AssertionError(f"Kind contracts must cover exactly: {', '.join(sorted(required))}")
    with tempfile.TemporaryDirectory() as temporary:
        workspace = Path(temporary)
        for kind in sorted(required):
            project = workspace / kind
            with contextlib.redirect_stdout(io.StringIO()):
                webapp.scaffold(
                    argparse.Namespace(
                        kind=kind,
                        deliverable=None,
                        scenario=None,
                        style=None,
                        out=str(project),
                        title=f"{kind.title()} contract fixture",
                        summary="Exercise the upgraded kind-specific workflow contract.",
                        ai="none",
                        brand=None,
                    )
                )
            if not webapp.validate_path(project, strict=True):
                raise AssertionError(f"Kind contract strict validation failed: {kind}")


def check_scenario_blueprints() -> None:
    registry = webapp._load_scenario_blueprints()
    scenarios = registry["scenarios"]
    if not isinstance(scenarios, list) or len(scenarios) < 5:
        raise AssertionError("Expected five or more scenario-specific blueprints")
    covered = {scenario["deliverable"] for scenario in scenarios}
    required = {"marketing", "prototype", "infographic", "motion", "document"}
    if required - covered:
        raise AssertionError(
            f"Scenario blueprints do not cover: {', '.join(sorted(required - covered))}"
        )
    with tempfile.TemporaryDirectory() as temporary:
        workspace = Path(temporary)
        for scenario in scenarios:
            project = workspace / str(scenario["id"])
            with contextlib.redirect_stdout(io.StringIO()):
                webapp.scaffold(
                    argparse.Namespace(
                        kind=None,
                        deliverable=None,
                        scenario=scenario["id"],
                        style=None,
                        out=str(project),
                        title=f"{scenario['name']} fixture",
                        summary="Exercise the scenario contract with local sample content.",
                        ai="none",
                    )
                )
            if not webapp.validate_path(project, strict=True):
                raise AssertionError(f"Scenario strict validation failed: {scenario['id']}")
        override = workspace / "scenario-style-override"
        with contextlib.redirect_stdout(io.StringIO()):
            webapp.scaffold(
                argparse.Namespace(
                    kind=None,
                    deliverable=None,
                    scenario="prototype-route-planner",
                    style="neo-swiss-editorial",
                    out=str(override),
                    title="Independent scenario and style axes",
                    summary="Verify a blueprint can adopt a non-default registered style.",
                    ai="none",
                )
            )
        if not webapp.validate_path(override, strict=True):
            raise AssertionError("Scenario style override strict validation failed")
    route = webapp.recommend_for_brief(
        "做一个博物馆夜游活动落地页，同时用数据图解释夜间能耗"
    )
    if route["mode"] != "composition":
        raise AssertionError("Brief router did not create a multi-scenario composition")
    if route["buildContract"]["scenarioIds"] != [
        "marketing-event-launch", "infographic-energy-story"
    ]:
        raise AssertionError("Brief router selected unexpected composition scenarios")


def _scaffold(
    output: Path,
    *,
    kind: str,
    ai: str = "none",
) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        webapp.scaffold(
            argparse.Namespace(
                kind=kind,
                out=str(output),
                title=f"{kind.title()} validation fixture",
                summary="Exercise the complete primary workflow with real input.",
                ai=ai,
                deliverable=None,
                style=None,
            )
        )


def check_starters_and_build() -> None:
    expected_starters = {
        path.parent.name
        for path in (ROOT / "assets" / "starters").glob("*/index.html")
    }
    routed_starters = {
        webapp._starter_for(kind, ["none"]) for kind in sorted(webapp.KINDS)
    }
    routed_starters.add(webapp._starter_for("tool", ["text"]))
    if expected_starters != routed_starters:
        missing = expected_starters - routed_starters
        extra = routed_starters - expected_starters
        raise AssertionError(
            f"Starter routing mismatch; unrouted={sorted(missing)}, missing={sorted(extra)}"
        )

    with tempfile.TemporaryDirectory() as temporary:
        workspace = Path(temporary)
        cases = [(kind, "none") for kind in sorted(webapp.KINDS)]
        cases.append(("tool", "text,vision,image,code"))
        projects: list[Path] = []
        for index, (kind, ai) in enumerate(cases):
            project = workspace / f"{index}-{kind}"
            _scaffold(project, kind=kind, ai=ai)
            projects.append(project)
            with contextlib.redirect_stdout(io.StringIO()):
                if not webapp.validate_path(project, strict=True):
                    raise AssertionError(f"Strict validation failed for {kind} with {ai}")

        archive = workspace / "smoke.zip"
        with contextlib.redirect_stdout(io.StringIO()):
            webapp.build(
                argparse.Namespace(
                    project=str(projects[0]),
                    out=str(archive),
                    allow_warnings=False,
                    force=False,
                )
            )
        with zipfile.ZipFile(archive) as package:
            if "index.html" not in package.namelist():
                raise AssertionError("Smoke archive has no index.html")


def check_tests() -> None:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise AssertionError(stream.getvalue().strip())


def main() -> None:
    checks = [
        ("metadata", check_metadata),
        ("Python sources", check_python_sources),
        ("runtime config", check_runtime_config),
        ("brand packs", check_brand_packs),
        ("style registry", check_style_registry),
        ("request routing", check_request_routing),
        ("kind contracts", check_kind_contracts),
        ("scenario blueprints", check_scenario_blueprints),
        ("starters and build", check_starters_and_build),
        ("unit tests", check_tests),
    ]
    failures: list[str] = []
    for label, check in checks:
        try:
            check()
            print(f"OK: {label}")
        except Exception as exc:
            failures.append(f"{label}: {exc}")
            print(f"ERROR: {label}: {exc}")
    if failures:
        print(f"Self-check failed: {len(failures)} check(s)")
        raise SystemExit(1)
    print(f"Self-check passed: {len(checks)} check(s)")


if __name__ == "__main__":
    main()
