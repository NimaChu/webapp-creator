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
    if fields["name"] != "webapp-creator":
        raise AssertionError("Skill name must be webapp-creator")
    if len(fields["description"]) < 80:
        raise AssertionError("Skill description is too short to trigger reliably")

    agent_source = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    for expected in ("display_name:", "short_description:", "$webapp-creator"):
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
