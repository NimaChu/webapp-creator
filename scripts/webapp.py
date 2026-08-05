#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
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
PRESENTATION_RATIOS = {
    "21x9",
    "16x9",
    "16x10",
    "4x3",
    "3x2",
    "1x1",
    "4x5",
    "9x16",
}
DEFAULT_PRESENTATION_LAYOUTS = [
    "cover",
    "section",
    "statement",
    "split",
    "comparison",
    "process",
    "timeline",
    "metrics",
    "evidence",
    "gallery",
    "diagram",
    "closing",
]
DEFAULT_BRAND = {
    "name": "Unbranded",
    "visualSystem": "custom",
    "colors": {
        "background": "#E8E8E3",
        "surface": "#FFFDF8",
        "text": "#18201C",
        "muted": "#667068",
        "primary": "#1D6552",
        "secondary": "#C8D8D0",
        "line": "#CFD4CC",
    },
    "fonts": {
        "display": '"Songti SC", "Noto Serif CJK SC", Georgia, serif',
        "body": '"PingFang SC", "Microsoft YaHei", system-ui, sans-serif',
        "data": 'ui-monospace, "Cascadia Code", Consolas, monospace',
    },
    "layouts": DEFAULT_PRESENTATION_LAYOUTS,
}


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


def _brand_pack_root() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "brand-packs"


def _resolve_brand_path(value: str) -> Path:
    built_in = _brand_pack_root() / value
    candidate = built_in if built_in.is_dir() else Path(value).expanduser().resolve()
    if candidate.is_dir():
        candidate = candidate / "brand.json"
    if not candidate.is_file():
        raise SystemExit(f"Could not find brand pack: {value}")
    return candidate


def _css_value(value: object, label: str) -> str:
    text = str(value).strip()
    if not text or any(token in text for token in ("{", "}", ";", "</style")):
        raise SystemExit(f"Invalid brand CSS value for {label}")
    return text


def _load_brand(value: str | None) -> tuple[dict[str, object], Path | None]:
    if not value:
        return json.loads(json.dumps(DEFAULT_BRAND)), None
    path = _resolve_brand_path(value)
    try:
        profile = json.loads(_read(path))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"Invalid brand profile {path}: {exc}") from exc
    if not isinstance(profile, dict):
        raise SystemExit("Brand profile must be a JSON object")
    for key in ("name", "visualSystem", "colors", "fonts", "layouts"):
        if key not in profile:
            raise SystemExit(f"Brand profile is missing {key}")
    colors = profile.get("colors")
    fonts = profile.get("fonts")
    layouts = profile.get("layouts")
    if not isinstance(colors, dict) or not isinstance(fonts, dict):
        raise SystemExit("Brand colors and fonts must be JSON objects")
    if not isinstance(layouts, list) or not layouts:
        raise SystemExit("Brand layouts must be a non-empty list")
    required_colors = set(DEFAULT_BRAND["colors"])
    required_fonts = set(DEFAULT_BRAND["fonts"])
    if required_colors - set(colors):
        raise SystemExit(
            f"Brand colors are missing: {', '.join(sorted(required_colors - set(colors)))}"
        )
    if required_fonts - set(fonts):
        raise SystemExit(
            f"Brand fonts are missing: {', '.join(sorted(required_fonts - set(fonts)))}"
        )
    for key, color in colors.items():
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(color)):
            raise SystemExit(f"Brand color {key} must be #RRGGBB")
    for key, font in fonts.items():
        _css_value(font, f"fonts.{key}")
    for layout in layouts:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", str(layout)):
            raise SystemExit(f"Invalid brand layout name: {layout}")
    return profile, path


def _brand_replacements(value: str | None) -> dict[str, str]:
    profile, path = _load_brand(value)
    colors = profile["colors"]
    fonts = profile["fonts"]
    assert isinstance(colors, dict) and isinstance(fonts, dict)
    logo_markup = ""
    logo = str(profile.get("logo", "")).strip()
    if logo:
        if path is None:
            raise SystemExit("A logo requires a file-backed brand pack")
        logo_path = (path.parent / logo).resolve()
        if not logo_path.is_file() or not logo_path.is_relative_to(path.parent.resolve()):
            raise SystemExit(f"Brand logo is missing or outside the brand pack: {logo}")
        mime = mimetypes.guess_type(logo_path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        data_uri = f"data:{mime};base64,{encoded}"
        logo_markup = (
            f'<img class="brand-logo" src="{data_uri}" '
            f'alt="{html.escape(str(profile["name"]), quote=True)}">'
        )

    custom_css = ""
    css_file = str(profile.get("customCss", "")).strip()
    if css_file:
        if path is None:
            raise SystemExit("customCss requires a file-backed brand pack")
        css_path = (path.parent / css_file).resolve()
        if not css_path.is_file() or not css_path.is_relative_to(path.parent.resolve()):
            raise SystemExit(f"Brand CSS is missing or outside the brand pack: {css_file}")
        custom_css = _read(css_path)
        if "</style" in custom_css.lower():
            raise SystemExit("Brand CSS must not contain a closing style tag")

    layouts = profile["layouts"]
    assert isinstance(layouts, list)
    return {
        "__BRAND_NAME__": html.escape(str(profile["name"]), quote=True),
        "__VISUAL_SYSTEM__": html.escape(
            str(profile["visualSystem"]), quote=True
        ),
        "__BRAND_LAYOUTS__": html.escape(
            ",".join(str(layout) for layout in layouts), quote=True
        ),
        "__BRAND_BACKGROUND__": _css_value(colors["background"], "background"),
        "__BRAND_SURFACE__": _css_value(colors["surface"], "surface"),
        "__BRAND_TEXT__": _css_value(colors["text"], "text"),
        "__BRAND_MUTED__": _css_value(colors["muted"], "muted"),
        "__BRAND_PRIMARY__": _css_value(colors["primary"], "primary"),
        "__BRAND_SECONDARY__": _css_value(colors["secondary"], "secondary"),
        "__BRAND_LINE__": _css_value(colors["line"], "line"),
        "__BRAND_DISPLAY_FONT__": _css_value(fonts["display"], "display font"),
        "__BRAND_BODY_FONT__": _css_value(fonts["body"], "body font"),
        "__BRAND_DATA_FONT__": _css_value(fonts["data"], "data font"),
        "__BRAND_LOGO_MARKUP__": logo_markup,
        "__BRAND_CSS__": custom_css,
    }


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
    brand = getattr(args, "brand", None)
    if brand and args.kind != "presentation":
        raise SystemExit("Brand packs are currently supported for presentation scaffolds")
    if args.kind == "presentation":
        replacements.update(_brand_replacements(brand))
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


def styleboard(args: argparse.Namespace) -> None:
    output = Path(args.out).expanduser().resolve()
    html_path = output if output.suffix.lower() in {".html", ".htm"} else output / "styleboard.html"
    if html_path.exists() and not args.force:
        raise SystemExit(f"Output already exists: {html_path}. Use --force to replace it.")
    if html_path.exists() and not html_path.is_file():
        raise SystemExit(f"Styleboard output is not a file: {html_path}")

    source = (
        Path(__file__).resolve().parents[1]
        / "assets"
        / "presentation-styleboard"
        / "index.html"
    )
    if not source.is_file():
        raise SystemExit(f"Missing presentation styleboard: {source}")
    content = _read(source)
    replacements = {
        "__TITLE__": html.escape(args.title, quote=True),
        "__SUMMARY__": html.escape(args.summary, quote=True),
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    _write(html_path, content)
    print(f"Styleboard: {html_path}")


def list_brands(args: argparse.Namespace) -> None:
    brands: dict[str, dict[str, object]] = {}
    for path in sorted(_brand_pack_root().glob("*/brand.json")):
        profile, _ = _load_brand(str(path))
        brands[path.parent.name] = {
            "name": profile["name"],
            "visualSystem": profile["visualSystem"],
        }
    if args.json:
        print(json.dumps(brands, ensure_ascii=False, indent=2))
        return
    for identifier, profile in brands.items():
        print(f"{identifier:24} {profile['name']} ({profile['visualSystem']})")


def init_brand(args: argparse.Namespace) -> None:
    source = _brand_pack_root() / args.from_pack
    if not (source / "brand.json").is_file():
        raise SystemExit(f"Unknown built-in brand pack: {args.from_pack}")
    output = Path(args.out).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    for path in source.iterdir():
        if path.is_file():
            shutil.copy2(path, output / path.name)
    brand_path = output / "brand.json"
    profile = json.loads(_read(brand_path))
    profile["name"] = args.name
    _write(brand_path, json.dumps(profile, ensure_ascii=False, indent=2) + "\n")
    print(f"Brand pack: {output}")


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


def _tag_attribute(tag: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*(['\"])(.*?)\1", tag, re.I | re.S)
    return match.group(2).strip() if match else ""


def _presentation_static_checks(
    source: str, body_values: dict[str, str]
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    slide_pattern = re.compile(
        r"<section\b(?=[^>]*\bclass\s*=\s*(['\"])[^'\"]*\bslide\b[^'\"]*\1)[^>]*>[\s\S]*?</section>",
        re.I,
    )
    slides = list(slide_pattern.finditer(source))
    slide_ids: list[str] = []
    active_count = 0
    allowed_brand_layouts = {
        item.strip()
        for item in body_values.get("data-brand-layouts", "").split(",")
        if item.strip()
    }

    for number, match in enumerate(slides, start=1):
        block = match.group(0)
        tag = block[: block.find(">") + 1]
        classes = _tag_attribute(tag, "class").split()
        active_count += int("active" in classes)
        layout = _tag_attribute(tag, "data-layout")
        slide_id = _tag_attribute(tag, "data-slide-id")
        if not layout:
            errors.append(f"Slide {number} is missing data-layout")
        elif not re.fullmatch(r"[a-z][a-z0-9-]*", layout):
            warnings.append(
                f"Slide {number} data-layout should be a descriptive kebab-case name"
            )
        elif allowed_brand_layouts and layout not in allowed_brand_layouts:
            errors.append(
                f"Slide {number} layout {layout} is not allowed by the active brand pack"
            )
        if not slide_id:
            errors.append(f"Slide {number} is missing data-slide-id")
        elif not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slide_id):
            errors.append(f"Slide {number} has an invalid data-slide-id: {slide_id}")
        else:
            slide_ids.append(slide_id)
        if not re.search(r"<h[1-3]\b", block, re.I):
            warnings.append(f"Slide {number} has no h1, h2, or h3 heading")

        for image_tag in re.findall(r"<img\b[^>]*>", block, re.I | re.S):
            src = _tag_attribute(image_tag, "src")
            if not src or src.startswith(("data:", "blob:")) or _external_reference(src):
                continue
            slot = _tag_attribute(image_tag, "data-image-slot")
            if not slot:
                warnings.append(
                    f"Slide {number} local image is missing data-image-slot"
                )
                continue
            ratio = slot.rsplit("-", 1)[-1].lower()
            if ratio not in PRESENTATION_RATIOS:
                warnings.append(
                    f"Slide {number} image slot should end in a supported ratio such as hero-16x9"
                )

    duplicates = sorted({slide_id for slide_id in slide_ids if slide_ids.count(slide_id) > 1})
    if duplicates:
        errors.append(f"Duplicate data-slide-id values: {', '.join(duplicates)}")
    if slides and active_count != 1:
        errors.append("Presentation must have exactly one initially active slide")

    stage_mode = body_values.get("data-stage-mode", "")
    if stage_mode not in {"fixed", "responsive"}:
        warnings.append("Declare data-stage-mode as fixed or responsive")
    if not body_values.get("data-visual-system"):
        warnings.append("Declare a subject-specific data-visual-system")
    if not body_values.get("data-brand"):
        warnings.append("Declare data-brand, using Unbranded when no brand pack applies")
    if body_values.get("data-density") not in {"sparse", "balanced", "dense"}:
        warnings.append("Declare data-density as sparse, balanced, or dense")

    runtime_markers = {
        "shareable slide hashes": r"location\.hash|hashchange|#slide-",
        "wheel navigation": r"\bwheel\b",
        "touch or pointer swipe navigation": r"touchstart|pointerdown",
    }
    for label, pattern in runtime_markers.items():
        if not re.search(pattern, source, re.I):
            warnings.append(f"Presentation is missing {label}")

    if re.search(r"<svg\b[\s\S]*?<text\b", source, re.I):
        warnings.append(
            "Keep presentation labels in semantic HTML; use SVG primarily for geometry"
        )
    return errors, warnings


def inspect_rendered_presentation(path: Path) -> tuple[list[str], list[str]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [
            "Rendered validation requested but Playwright is unavailable; install playwright and its Chromium browser"
        ], []

    errors: list[str] = []
    warnings: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            page.goto(path.resolve().as_uri(), wait_until="load")
            page.emulate_media(reduced_motion="reduce")
            slide_count = page.locator("section.slide").count()
            for index in range(slide_count):
                metrics = page.evaluate(
                    """
                    index => {
                      const slides = [...document.querySelectorAll('section.slide')];
                      slides.forEach((slide, slideIndex) => {
                        const active = slideIndex === index;
                        slide.classList.toggle('active', active);
                        slide.toggleAttribute('inert', !active);
                        slide.setAttribute('aria-hidden', String(!active));
                      });
                      const slide = slides[index];
                      const rect = slide.getBoundingClientRect();
                      const scaleX = rect.width / (slide.offsetWidth || rect.width || 1);
                      const scaleY = rect.height / (slide.offsetHeight || rect.height || 1);
                      const selector = 'h1,h2,h3,p,li,img,svg,canvas,table,figure,[data-content],[data-image-slot]';
                      const nodes = [...slide.querySelectorAll(selector)].filter(node => {
                        const style = getComputedStyle(node);
                        return style.display !== 'none' && style.visibility !== 'hidden' &&
                          !node.closest('[data-overflow-ok]') && !node.closest('.slide-note');
                      });
                      let top = Infinity;
                      let bottom = -Infinity;
                      let left = Infinity;
                      let right = -Infinity;
                      for (const node of nodes) {
                        const box = node.getBoundingClientRect();
                        top = Math.min(top, (box.top - rect.top) / scaleY);
                        bottom = Math.max(bottom, (box.bottom - rect.top) / scaleY);
                        left = Math.min(left, (box.left - rect.left) / scaleX);
                        right = Math.max(right, (box.right - rect.left) / scaleX);
                      }
                      if (!nodes.length) top = bottom = left = right = 0;
                      return {
                        id: slide.dataset.slideId || String(index + 1),
                        width: slide.offsetWidth,
                        height: slide.offsetHeight,
                        scrollX: Math.max(0, slide.scrollWidth - slide.clientWidth),
                        scrollY: Math.max(0, slide.scrollHeight - slide.clientHeight),
                        top, bottom, left, right,
                      };
                    }
                    """,
                    index,
                )
                label = f"Slide {index + 1} ({metrics['id']})"
                overflow = max(
                    metrics["scrollX"],
                    metrics["scrollY"],
                    -metrics["top"],
                    -metrics["left"],
                    metrics["right"] - metrics["width"],
                    metrics["bottom"] - metrics["height"],
                )
                if overflow > 4:
                    errors.append(f"{label} rendered content overflows by {round(overflow)}px")
                safe_bottom = metrics["height"] * 0.93
                if metrics["bottom"] > safe_bottom and overflow <= 4:
                    warnings.append(
                        f"{label} content crosses the 93% navigation-safe line"
                    )
        finally:
            browser.close()
    return errors, warnings


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
        presentation_errors, presentation_warnings = _presentation_static_checks(
            source, body_values
        )
        errors.extend(presentation_errors)
        warnings.extend(presentation_warnings)

    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


def validate_path(target: Path, strict: bool, rendered: bool = False) -> bool:
    target = target.expanduser().resolve()
    html_path = target if target.is_file() else target / "index.html"
    if not html_path.is_file():
        raise SystemExit(f"Could not find index.html: {html_path}")
    errors, warnings = inspect_html(html_path)
    if rendered and re.search(
        r"data-webapp-kind\s*=\s*(['\"])presentation\1", _read(html_path), re.I
    ):
        rendered_errors, rendered_warnings = inspect_rendered_presentation(html_path)
        errors.extend(rendered_errors)
        warnings.extend(rendered_warnings)
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
    if not validate_path(Path(args.target), args.strict, args.rendered):
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
    create.add_argument(
        "--brand",
        help="Built-in brand-pack id or path to a brand-pack folder/brand.json (presentations only).",
    )
    create.set_defaults(func=scaffold)

    board = commands.add_parser(
        "styleboard", help="Create three real-content presentation style previews."
    )
    board.add_argument("--out", required=True)
    board.add_argument("--title", required=True)
    board.add_argument("--summary", required=True)
    board.add_argument("--force", action="store_true")
    board.set_defaults(func=styleboard)

    brands = commands.add_parser("brands", help="List built-in presentation brand packs.")
    brands.add_argument("--json", action="store_true")
    brands.set_defaults(func=list_brands)

    brand_init = commands.add_parser(
        "brand-init", help="Create a reusable brand pack from a built-in seed."
    )
    brand_init.add_argument("--out", required=True)
    brand_init.add_argument("--name", required=True)
    brand_init.add_argument(
        "--from",
        dest="from_pack",
        default="neutral-corporate",
        choices=[path.parent.name for path in _brand_pack_root().glob("*/brand.json")],
    )
    brand_init.set_defaults(func=init_brand)

    check = commands.add_parser("validate", help="Validate a standalone HTML app.")
    check.add_argument("target")
    check.add_argument("--strict", action="store_true")
    check.add_argument(
        "--rendered",
        action="store_true",
        help="Measure presentation overflow in Chromium through Playwright.",
    )
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
