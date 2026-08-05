#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


KINDS = {"tool", "dashboard", "eqai-ai", "presentation"}
ALLOWED_AI = {"text", "image"}
DIRECTION_SPECS = {
    "workbench": {
        "kind": "tool",
        "asset": "tool-starter",
        "use": "Converters, generators, inspectors, checklists, and repeated desktop tasks.",
    },
    "analytics": {
        "kind": "dashboard",
        "asset": "dashboard-starter",
        "use": "KPIs, comparisons, trends, exceptions, filters, and detailed data.",
    },
    "guided": {
        "kind": "tool",
        "asset": "guided-starter",
        "use": "Multi-step configuration, diagnosis, review, approval, and structured forms.",
    },
    "knowledge": {
        "kind": "tool",
        "asset": "knowledge-starter",
        "use": "Guides, document summaries, meeting notes, FAQs, and knowledge organization.",
    },
    "ai-studio": {
        "kind": "eqai-ai",
        "asset": "eqai-ai-starter",
        "use": "Prompt-driven text or image generation with Eqai AI Runtime.",
    },
    "presentation": {
        "kind": "presentation",
        "asset": "presentation-starter",
        "use": "Full-screen HTML decks with navigation, notes, deep links, and print/PDF output.",
    },
}
DEFAULT_DIRECTIONS = {
    "tool": "workbench",
    "dashboard": "analytics",
    "eqai-ai": "ai-studio",
    "presentation": "presentation",
}
FORBIDDEN_CONTRACT_KEYS = {
    "apikey", "api_key", "secret", "token", "baseurl", "base_url", "endpoint"
}
TOKEN_PATTERN = re.compile(r"__(?:APP_)?(?:NAME|TITLE|SUMMARY)__|\b(?:TODO|FILL_ME)\b", re.I)


class DocumentInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.attrs: list[tuple[str, dict[str, str]]] = []
        self.doctype = False
        self.title_depth = 0
        self.title_text: list[str] = []

    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower() == "doctype html":
            self.doctype = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {key.lower(): value or "" for key, value in attrs}
        self.tags.append(tag)
        self.attrs.append((tag, values))
        if tag == "title":
            self.title_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_text.append(data)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def find_html(target: Path) -> tuple[Path, Path]:
    if target.is_file():
        if target.suffix.lower() != ".html":
            raise ValueError(f"Expected an HTML file: {target}")
        return target, target.parent
    candidates = [target / "app" / "index.html", target / "index.html"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate, target
    raise ValueError(f"Could not find app/index.html or index.html under {target}")


def scaffold(args: argparse.Namespace) -> None:
    out = Path(args.out).expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"Output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    direction = DEFAULT_DIRECTIONS[args.kind] if args.direction == "auto" else args.direction
    direction_spec = DIRECTION_SPECS[direction]
    if direction_spec["kind"] != args.kind:
        raise SystemExit(
            f"Direction '{direction}' requires --kind {direction_spec['kind']}; "
            f"received --kind {args.kind}."
        )

    skill_root = Path(__file__).resolve().parents[1]
    source = skill_root / "assets" / direction_spec["asset"]
    if not source.is_dir():
        raise SystemExit(f"Missing scaffold asset: {source}")
    shutil.copytree(source, out, dirs_exist_ok=True)

    for path in out.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".html", ".css", ".js", ".md", ".json"}:
            content = read_text(path)
            is_html = path.suffix.lower() == ".html"
            replacements = {
                "__TITLE__": html.escape(args.title, quote=True) if is_html else args.title,
                "__SUMMARY__": html.escape(args.summary, quote=True) if is_html else args.summary,
            }
            for source_text, target_text in replacements.items():
                content = content.replace(source_text, target_text)
            write_text(path, content)

    if args.kind == "eqai-ai":
        requested = {part.strip() for part in args.ai.split(",") if part.strip()}
        invalid = requested - ALLOWED_AI
        if not requested or invalid:
            raise SystemExit("--ai must contain text, image, or text,image")
        contract_path = out / "eqai-tool.json"
        contract = json.loads(read_text(contract_path))
        profiles = contract["ai"]["profiles"]
        if "text" not in requested:
            profiles.pop("assistant", None)
            prompt = out / "prompts" / "assistant.md"
            if prompt.exists():
                prompt.unlink()
        if "image" not in requested:
            profiles.pop("illustration", None)
        write_text(contract_path, json.dumps(contract, indent=2, ensure_ascii=False) + "\n")

    print(f"Scaffolded {args.kind} with {direction} direction: {out}")
    print(f"HTML: {out / 'app' / 'index.html'}")


def list_directions(args: argparse.Namespace) -> None:
    if args.json:
        print(json.dumps(DIRECTION_SPECS, ensure_ascii=False, indent=2))
        return
    for name, spec in DIRECTION_SPECS.items():
        print(f"{name:12} {spec['kind']:10} {spec['use']}")


def external_reference(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} or value.startswith("//")


def local_reference_exists(html_path: Path, value: str) -> bool:
    if not value or value.startswith(("#", "data:", "blob:", "mailto:", "tel:", "/")):
        return True
    parsed = urlparse(value)
    if parsed.scheme:
        return True
    return (html_path.parent / parsed.path).resolve().exists()


def walk_contract_keys(value: object, trail: str = "eqai-tool.json") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.lower() in FORBIDDEN_CONTRACT_KEYS:
                errors.append(f"{trail} contains forbidden secret/provider field: {key}")
            errors.extend(walk_contract_keys(nested, f"{trail}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(walk_contract_keys(nested, f"{trail}[{index}]"))
    return errors


def validate_contract(root: Path) -> tuple[list[str], list[str]]:
    contract_path = root / "eqai-tool.json"
    if not contract_path.exists():
        return [], []
    errors: list[str] = []
    warnings: list[str] = []
    try:
        contract = json.loads(read_text(contract_path))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Invalid eqai-tool.json: {exc}"], warnings
    errors.extend(walk_contract_keys(contract))
    if contract.get("schemaVersion") != 1:
        errors.append("eqai-tool.json schemaVersion must be 1")
    if contract.get("mode") != "ai-enabled":
        errors.append('eqai-tool.json mode must be "ai-enabled"')
    if contract.get("entry") != "index.html":
        errors.append('eqai-tool.json entry must be "index.html"')
    if contract.get("bridgeVersion") != 1:
        errors.append("eqai-tool.json bridgeVersion must be 1")
    profiles = contract.get("ai", {}).get("profiles")
    if not isinstance(profiles, dict) or not 1 <= len(profiles) <= 8:
        errors.append("eqai-tool.json must declare between 1 and 8 AI profiles")
        return errors, warnings
    for name, profile in profiles.items():
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name):
            errors.append(f"Invalid AI profile name: {name}")
        if not isinstance(profile, dict) or profile.get("type") not in ALLOWED_AI:
            errors.append(f"AI profile {name} type must be text or image")
            continue
        prompt = profile.get("systemPrompt")
        if prompt:
            resolved = (root / str(prompt)).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"AI profile {name} systemPrompt escapes the package")
            else:
                if not resolved.is_file():
                    errors.append(f"AI profile {name} systemPrompt was not found: {prompt}")
                elif resolved.stat().st_size > 20 * 1024:
                    errors.append(f"AI profile {name} systemPrompt exceeds 20 KB")
    return errors, warnings


def validate(args: argparse.Namespace) -> None:
    target = Path(args.target).expanduser().resolve()
    try:
        html_path, root = find_html(target)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    source = read_text(html_path)
    inspector = DocumentInspector()
    try:
        inspector.feed(source)
    except Exception as exc:
        raise SystemExit(f"Could not parse {html_path}: {exc}") from exc

    errors: list[str] = []
    warnings: list[str] = []
    tags = inspector.tags
    attrs = inspector.attrs

    if not inspector.doctype:
        errors.append("Missing <!doctype html>")
    html_nodes = [values for tag, values in attrs if tag == "html"]
    if not html_nodes or not html_nodes[0].get("lang"):
        warnings.append("Set a language on the <html> element")
    if not any(tag == "meta" and values.get("charset") for tag, values in attrs):
        errors.append("Missing a charset meta tag")
    if not any(tag == "meta" and values.get("name", "").lower() == "viewport" for tag, values in attrs):
        errors.append("Missing the viewport meta tag")
    if not "".join(inspector.title_text).strip():
        errors.append("Missing a non-empty <title>")
    if "main" not in tags:
        warnings.append("Use a <main> landmark for the primary experience")
    if "h1" not in tags:
        warnings.append("Add one clear <h1> for the tool or dashboard title")
    if TOKEN_PATTERN.search(source):
        errors.append("Unresolved scaffold token or TODO marker remains")

    labels_for = {values.get("for") for tag, values in attrs if tag == "label" and values.get("for")}
    for tag, values in attrs:
        if tag in {"input", "select", "textarea"}:
            control_id = values.get("id")
            has_name = values.get("aria-label") or values.get("aria-labelledby") or (control_id and control_id in labels_for)
            if not has_name and values.get("type", "").lower() != "hidden":
                errors.append(f"Unlabelled <{tag}> control" + (f" #{control_id}" if control_id else ""))
        if tag == "button" and not values.get("type"):
            warnings.append("Set type=button or type=submit on every button")
        if tag == "img" and "alt" not in values:
            errors.append("Image is missing alt text")
        if tag in {"script", "link", "img", "source", "iframe"}:
            value = values.get("src") or values.get("href") or ""
            if value and external_reference(value):
                warnings.append(f"External dependency: {value}")
            elif value and not local_reference_exists(html_path, value):
                errors.append(f"Missing local asset: {value}")
        for key in values:
            if key.startswith("on"):
                warnings.append(f"Inline event handler {key} reduces maintainability and CSP compatibility")

    if re.search(r"letter-spacing\s*:\s*-", source, re.I):
        errors.append("Negative letter-spacing is not allowed")
    if not re.search(r"@media\b", source, re.I):
        warnings.append("No responsive media query found")
    if not re.search(r":focus-visible|:focus\b", source, re.I):
        warnings.append("No explicit keyboard focus treatment found")
    if re.search(r"animation\s*:|transition\s*:", source, re.I) and not re.search(
        r"prefers-reduced-motion", source, re.I
    ):
        warnings.append("Motion exists without prefers-reduced-motion handling")
    if re.search(r"linear-gradient|radial-gradient", source, re.I):
        warnings.append("Review gradients and remove purely decorative blob/orb treatments")

    body_nodes = [values for tag, values in attrs if tag == "body"]
    is_presentation = any(
        values.get("data-html-design-kind") == "presentation" for values in body_nodes
    )
    if is_presentation:
        slide_nodes = [
            values
            for tag, values in attrs
            if tag == "section" and "slide" in values.get("class", "").split()
        ]
        active_slides = [
            values for values in slide_nodes if "active" in values.get("class", "").split()
        ]
        ids = {values.get("id") for _, values in attrs if values.get("id")}
        required_ids = {
            "prevBtn",
            "nextBtn",
            "notesBtn",
            "fullBtn",
            "languageBtn",
            "progressBar",
            "slideCount",
            "notesPanel",
        }
        missing_ids = sorted(required_ids - ids)
        if len(slide_nodes) < 2:
            errors.append("Presentation must contain at least two <section class=\"slide\"> elements")
        if len(active_slides) != 1:
            errors.append("Presentation must have exactly one initially active slide")
        if missing_ids:
            errors.append(f"Presentation runtime controls are missing: {', '.join(missing_ids)}")
        if not any("slide-note" in values.get("class", "").split() for _, values in attrs):
            warnings.append("Presentation has no speaker notes (.slide-note)")
        presentation_markers = {
            "print stylesheet": r"@media\s+print",
            "keyboard navigation": r"addEventListener\(\s*['\"]keydown['\"]",
            "hash navigation": r"hashchange|location\.hash",
            "wheel navigation": r"addEventListener\(\s*['\"]wheel['\"]",
            "touch navigation": r"addEventListener\(\s*['\"]touchstart['\"]",
            "fullscreen support": r"requestFullscreen",
            "accessible slide state": r"aria-hidden",
            "bilingual content bindings": r"data-i18n",
            "English language dictionary": r"\ben\s*:\s*\{",
            "Chinese language dictionary": r"\bzh\s*:\s*\{",
            "language switching": r"function\s+applyLanguage",
        }
        for capability, pattern in presentation_markers.items():
            if not re.search(pattern, source, re.I):
                errors.append(f"Presentation is missing {capability}")

        bound_keys = set(
            re.findall(r'data-i18n(?:-aria-label|-title)?=["\']([A-Za-z][A-Za-z0-9]*)["\']', source)
        )
        bound_keys.update(
            re.findall(r'data-title-key=["\']([A-Za-z][A-Za-z0-9]*)["\']', source)
        )
        dictionaries = re.search(
            r"const\s+messages\s*=\s*\{\s*en\s*:\s*\{(?P<en>.*?)\n\s*\},\s*"
            r"zh\s*:\s*\{(?P<zh>.*?)\n\s*\}\s*\};",
            source,
            re.S,
        )
        if dictionaries:
            key_pattern = re.compile(r"^\s*([A-Za-z][A-Za-z0-9]*)\s*:", re.M)
            en_keys = set(key_pattern.findall(dictionaries.group("en")))
            zh_keys = set(key_pattern.findall(dictionaries.group("zh")))
            missing_en = sorted(bound_keys - en_keys)
            missing_zh = sorted(bound_keys - zh_keys)
            if missing_en:
                errors.append(f"English presentation dictionary is missing: {', '.join(missing_en)}")
            if missing_zh:
                errors.append(f"Chinese presentation dictionary is missing: {', '.join(missing_zh)}")
            if en_keys != zh_keys:
                only_en = sorted(en_keys - zh_keys)
                only_zh = sorted(zh_keys - en_keys)
                details = []
                if only_en:
                    details.append(f"only in English: {', '.join(only_en)}")
                if only_zh:
                    details.append(f"only in Chinese: {', '.join(only_zh)}")
                errors.append(f"Presentation dictionaries are not structurally equivalent ({'; '.join(details)})")

    contract_errors, contract_warnings = validate_contract(root)
    errors.extend(contract_errors)
    warnings.extend(contract_warnings)
    if (root / "eqai-tool.json").exists() and "/runtime-sdk/v1/eqai.js" not in source:
        errors.append("Eqai AI tool does not load /runtime-sdk/v1/eqai.js")

    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))
    for issue in errors:
        print(f"ERROR: {issue}")
    for issue in warnings:
        print(f"WARN: {issue}")
    if errors or (args.strict and warnings):
        raise SystemExit(1)
    print(f"OK: {html_path}")
    print(f"Checks: {len(errors)} error(s), {len(warnings)} warning(s)")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Scaffold and validate HTML Design artifacts.")
    commands = root.add_subparsers(dest="command", required=True)

    create = commands.add_parser("scaffold", help="Create a practical HTML starter.")
    create.add_argument("--kind", required=True, choices=sorted(KINDS))
    create.add_argument("--out", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--summary", required=True)
    create.add_argument(
        "--direction",
        default="auto",
        choices=["auto", *sorted(DIRECTION_SPECS)],
        help="Visual direction. auto selects the default for the chosen kind.",
    )
    create.add_argument("--ai", default="text,image", help="Eqai AI capabilities: text, image, or text,image")
    create.set_defaults(func=scaffold)

    directions = commands.add_parser("directions", help="List available visual directions.")
    directions.add_argument("--json", action="store_true")
    directions.set_defaults(func=list_directions)

    check = commands.add_parser("validate", help="Validate an HTML file or artifact folder.")
    check.add_argument("target")
    check.add_argument("--strict", action="store_true")
    check.set_defaults(func=validate)
    return root


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
