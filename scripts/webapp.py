#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from local_runtime import run_server


KINDS = {"tool", "dashboard", "guided", "knowledge", "game", "presentation"}
AI_CAPABILITIES = {"none", "text", "vision", "image", "code"}
STARTERS = {
    "tool": "tool",
    "dashboard": "dashboard",
    "guided": "guided",
    "knowledge": "knowledge",
    "game": "game",
    "presentation": "presentation",
}
TOKEN_PATTERN = re.compile(r"__(?:TITLE|SUMMARY|KIND|AI_CAPABILITIES)__|\b(?:TODO|FILL_ME)\b", re.I)
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"api[_-]?key\s*[:=]\s*['\"][^'\"]+['\"]", re.I),
    re.compile(r"authorization\s*[:=]\s*['\"]bearer\s+[^'\"]+['\"]", re.I),
]


class Inspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doctype_count = 0
        self.tags: list[str] = []
        self.end_tags: list[str] = []
        self.attrs: list[tuple[str, dict[str, str]]] = []
        self.title_depth = 0
        self.title_parts: list[str] = []

    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower() == "doctype html":
            self.doctype_count += 1

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag = tag.lower()
        values = {key.lower(): value or "" for key, value in attrs}
        self.tags.append(tag)
        self.attrs.append((tag, values))
        if tag == "title":
            self.title_depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        self.end_tags.append(tag)
        if tag == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_parts.append(data)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.replace("\r\n", "\n"), encoding="utf-8")


def _parse_capabilities(value: str) -> list[str]:
    parts = [part.strip().lower() for part in value.split(",") if part.strip()]
    if not parts:
        return ["none"]
    invalid = set(parts) - AI_CAPABILITIES
    if invalid:
        raise argparse.ArgumentTypeError(
            f"Unknown AI capabilities: {', '.join(sorted(invalid))}"
        )
    if "none" in parts and len(parts) > 1:
        raise argparse.ArgumentTypeError("none cannot be combined with other capabilities")
    return list(dict.fromkeys(parts))


def _starter_for(kind: str, capabilities: list[str]) -> str:
    if kind == "tool" and capabilities != ["none"]:
        return "ai-tool"
    return STARTERS[kind]


def scaffold(args: argparse.Namespace) -> None:
    output = Path(args.out).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    capabilities = _parse_capabilities(args.ai)
    starter_name = _starter_for(args.kind, capabilities)
    source = Path(__file__).resolve().parents[1] / "assets" / "starters" / starter_name / "index.html"
    if not source.is_file():
        raise SystemExit(f"Missing starter: {source}")
    content = _read(source)
    replacements = {
        "__TITLE__": html.escape(args.title, quote=True),
        "__SUMMARY__": html.escape(args.summary, quote=True),
        "__KIND__": args.kind,
        "__AI_CAPABILITIES__": ",".join(capabilities),
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    _write(output / "index.html", content)

    if capabilities != ["none"]:
        example = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "local-config.example.json"
        )
        shutil.copy2(example, output / ".webapp.local.example.json")
        _write(output / ".gitignore", ".webapp.local.json\n")

    print(f"Scaffolded {args.kind}: {output}")
    print(f"Entry: {output / 'index.html'}")
    print(f"AI capabilities: {', '.join(capabilities)}")


def _external_reference(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} or value.startswith("//")


def _local_reference_exists(html_path: Path, value: str) -> bool:
    if not value or value.startswith(("#", "data:", "blob:", "mailto:", "tel:")):
        return True
    parsed = urlparse(value)
    if parsed.scheme or value.startswith("/runtime/"):
        return True
    if value.startswith("/"):
        return False
    return (html_path.parent / parsed.path).resolve().exists()


def inspect_html(path: Path) -> tuple[list[str], list[str]]:
    source = _read(path)
    inspector = Inspector()
    try:
        inspector.feed(source)
    except Exception as exc:
        return [f"Could not parse HTML: {exc}"], []

    errors: list[str] = []
    warnings: list[str] = []
    tags = inspector.tags
    attrs = inspector.attrs

    if inspector.doctype_count == 0:
        errors.append("Missing <!doctype html>")
    elif inspector.doctype_count > 1:
        errors.append("Document must contain exactly one <!doctype html>")
    html_nodes = [values for tag, values in attrs if tag == "html"]
    if len(html_nodes) != 1:
        errors.append("Document must contain exactly one <html> root element")
    if inspector.end_tags.count("html") != 1:
        errors.append("Document must contain exactly one closing </html> tag")
    body_nodes = [values for tag, values in attrs if tag == "body"]
    if len(body_nodes) != 1 or inspector.end_tags.count("body") != 1:
        errors.append("Document must contain one complete <body> element")
    if not re.match(r"^\s*<!doctype\s+html\b", source, re.I):
        errors.append("HTML must begin with <!doctype html>")
    if re.search(r"^\s*```", source):
        errors.append("Markdown fences must not wrap delivered HTML")
    if not html_nodes or not html_nodes[0].get("lang"):
        errors.append("Set a language on the <html> element")
    if not any(tag == "meta" and values.get("charset") for tag, values in attrs):
        errors.append("Missing a charset meta tag")
    if not any(
        tag == "meta" and values.get("name", "").lower() == "viewport"
        for tag, values in attrs
    ):
        errors.append("Missing the viewport meta tag")
    if not "".join(inspector.title_parts).strip():
        errors.append("Missing a non-empty <title>")
    if "main" not in tags:
        warnings.append("Use a <main> landmark")
    if "h1" not in tags:
        warnings.append("Add one clear <h1>")
    if TOKEN_PATTERN.search(source):
        errors.append("Unresolved scaffold token or TODO marker remains")
    if any(pattern.search(source) for pattern in SECRET_PATTERNS):
        errors.append("Possible credential embedded in HTML")

    labels_for = {
        values.get("for")
        for tag, values in attrs
        if tag == "label" and values.get("for")
    }
    body_values = next((values for tag, values in attrs if tag == "body"), {})
    kind = body_values.get("data-webapp-kind", "")
    capabilities = {
        part.strip()
        for part in body_values.get("data-ai-capabilities", "none").split(",")
        if part.strip()
    }

    for tag, values in attrs:
        if tag in {"input", "select", "textarea"}:
            control_id = values.get("id")
            named = (
                values.get("aria-label")
                or values.get("aria-labelledby")
                or (control_id and control_id in labels_for)
            )
            if not named and values.get("type", "").lower() != "hidden":
                errors.append(f"Unlabelled <{tag}> control")
        if tag == "button" and not values.get("type"):
            warnings.append("Set type on every button")
        if tag == "img" and "alt" not in values:
            errors.append("Image is missing alt text")
        if tag in {"script", "link", "img", "source", "audio", "video", "iframe"}:
            value = values.get("src") or values.get("href") or ""
            if value and _external_reference(value):
                warnings.append(f"External dependency prevents full portability: {value}")
            elif value and not _local_reference_exists(path, value):
                errors.append(f"Missing local asset: {value}")
        if any(key.startswith("on") for key in values):
            warnings.append("Avoid inline event handlers")

    if not re.search(r":focus-visible|:focus\b", source, re.I):
        warnings.append("No explicit keyboard focus treatment")
    if not re.search(r"@media\b", source, re.I):
        warnings.append("No responsive media query")
    if re.search(r"animation\s*:|transition\s*:", source, re.I) and not re.search(
        r"prefers-reduced-motion", source, re.I
    ):
        warnings.append("Motion exists without reduced-motion handling")
    if re.search(r"\binnerHTML\s*=", source) and re.search(
        r"/runtime/ai/|fetch\s*\(", source
    ):
        errors.append("Do not assign model or remote output directly to innerHTML")

    if capabilities and capabilities != {"none"}:
        if "/runtime/ai/" not in source:
            warnings.append("AI capabilities are declared but no local runtime call was found")
        if not (path.parent / ".webapp.local.example.json").is_file():
            warnings.append("AI app has no .webapp.local.example.json")

    if kind == "game":
        checks = {
            "start or restart control": r"\bstart\b|\brestart\b|开始|重新",
            "pointer, touch, or keyboard input": r"pointer|touch|keydown|click",
            "local persistence": r"localStorage|indexedDB",
            "result or game-over state": r"game.?over|result|结束|得分",
        }
        for label, pattern in checks.items():
            if not re.search(pattern, source, re.I):
                warnings.append(f"Game is missing {label}")

    if kind == "presentation":
        markers = {
            "multiple slides": len(
                [
                    values
                    for tag, values in attrs
                    if tag == "section" and "slide" in values.get("class", "").split()
                ]
            )
            >= 2,
            "keyboard navigation": bool(re.search(r"keydown", source, re.I)),
            "print layout": bool(re.search(r"@media\s+print", source, re.I)),
        }
        for label, present in markers.items():
            if not present:
                errors.append(f"Presentation is missing {label}")

    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


def validate_path(target: Path, strict: bool) -> bool:
    target = target.expanduser().resolve()
    html_path = target if target.is_file() else target / "index.html"
    if not html_path.is_file():
        raise SystemExit(f"Could not find index.html: {html_path}")
    errors, warnings = inspect_html(html_path)
    for issue in errors:
        print(f"ERROR: {issue}")
    for issue in warnings:
        print(f"WARN: {issue}")
    passed = not errors and not (strict and warnings)
    if passed:
        print(f"OK: {html_path}")
    print(f"Checks: {len(errors)} error(s), {len(warnings)} warning(s)")
    return passed


def validate(args: argparse.Namespace) -> None:
    if not validate_path(Path(args.target), args.strict):
        raise SystemExit(1)


def serve(args: argparse.Namespace) -> None:
    run_server(
        Path(args.project),
        config_path=Path(args.config) if args.config else None,
        host=args.host,
        port=args.port,
        open_browser=args.open,
        allowed_hosts=args.allow_host,
    )


def _include_in_build(path: Path, root: Path, excluded: set[Path]) -> bool:
    resolved = path.resolve()
    if resolved in excluded:
        return False
    relative = path.relative_to(root)
    ignored_parts = {".git", "__pycache__", "dist"}
    if any(part in ignored_parts for part in relative.parts):
        return False
    if path.name in {".DS_Store", ".webapp.local.json"}:
        return False
    if path.suffix in {".pyc", ".zip"}:
        return False
    return True


def build(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser().resolve()
    if not (project / "index.html").is_file():
        raise SystemExit(f"Could not find index.html under {project}")
    if not validate_path(project, strict=not args.allow_warnings):
        raise SystemExit("Build stopped because validation failed.")

    output = (
        Path(args.out).expanduser().resolve()
        if args.out
        else project.parent / f"{project.name}.zip"
    )
    if output.exists() and not args.force:
        raise SystemExit(f"Output already exists: {output}. Use --force to replace it.")
    if output.exists() and not output.is_file():
        raise SystemExit(f"Build output is not a file: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        excluded = {output.resolve(), temporary_path.resolve()}
        with zipfile.ZipFile(
            temporary_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path in sorted(project.rglob("*")):
                if path.is_file() and _include_in_build(path, project, excluded):
                    archive.write(path, path.relative_to(project).as_posix())
        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    print(f"Built: {output}")


def list_kinds(args: argparse.Namespace) -> None:
    details = {
        "tool": "Calculators, converters, generators, inspectors, and focused utilities.",
        "dashboard": "Metrics, comparisons, filters, trends, and decision views.",
        "guided": "Multi-step forms, configuration, diagnosis, and review workflows.",
        "knowledge": "Guides, notes, FAQs, summaries, and organized reference material.",
        "game": "Touch-friendly lightweight games with a closed play loop.",
        "presentation": "Full-screen HTML narratives with keyboard and print support.",
    }
    if args.json:
        print(json.dumps(details, ensure_ascii=False, indent=2))
        return
    for name, description in details.items():
        print(f"{name:14} {description}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Create, validate, serve, and package standalone HTML web apps."
    )
    commands = root.add_subparsers(dest="command", required=True)

    create = commands.add_parser("scaffold", help="Create a single-file HTML starter.")
    create.add_argument("--kind", choices=sorted(KINDS), required=True)
    create.add_argument("--out", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--summary", required=True)
    create.add_argument(
        "--ai",
        default="none",
        help="Comma-separated capabilities: none, text, vision, image, code.",
    )
    create.set_defaults(func=scaffold)

    check = commands.add_parser("validate", help="Validate a standalone HTML app.")
    check.add_argument("target")
    check.add_argument("--strict", action="store_true")
    check.set_defaults(func=validate)

    preview = commands.add_parser(
        "serve", help="Serve the app with an optional local model proxy."
    )
    preview.add_argument("project")
    preview.add_argument("--config")
    preview.add_argument("--host", default="127.0.0.1")
    preview.add_argument(
        "--allow-host",
        action="append",
        default=[],
        help="Additional accepted Host header. Repeat for more than one host.",
    )
    preview.add_argument("--port", type=int, default=4327)
    preview.add_argument("--open", action="store_true")
    preview.set_defaults(func=serve)

    package = commands.add_parser("build", help="Build a portable zip.")
    package.add_argument("project")
    package.add_argument("--out")
    package.add_argument("--allow-warnings", action="store_true")
    package.add_argument(
        "--force", action="store_true", help="Replace an existing output archive."
    )
    package.set_defaults(func=build)

    kinds = commands.add_parser("kinds", help="List supported app kinds.")
    kinds.add_argument("--json", action="store_true")
    kinds.set_defaults(func=list_kinds)
    return root


def main() -> None:
    args = parser().parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        raise SystemExit(130)


if __name__ == "__main__":
    main()
