#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from cover_engine import (
    build_cover_seed,
    choose_cover_variant,
    create_icon_png,
    create_thumbnail_png,
    infer_art_direction,
    pick_palette_for_metadata,
    slugify,
    vary_palette,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate optional local cover and icon PNG files for a web app."
    )
    parser.add_argument("project")
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument(
        "--kind",
        choices=["tool", "dashboard", "guided", "knowledge", "game", "presentation", "motion"],
        default="tool",
    )
    parser.add_argument("--capabilities", default="none")
    parser.add_argument("--slug")
    parser.add_argument("--motif")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    slug = slugify(args.slug or project.name or args.title) or "webapp"
    hint = " ".join([args.title, args.summary, args.kind, args.capabilities])
    motif = args.motif or infer_art_direction(args.kind, slug, hint)
    variant = choose_cover_variant(args.kind, slug, motif)
    seed = build_cover_seed(args.kind, slug, motif)
    metadata = {
        "title": args.title,
        "summary": args.summary,
        "kind": args.kind,
        "capabilities": args.capabilities,
        "slug": slug,
    }
    palette = vary_palette(pick_palette_for_metadata(metadata, motif), variant)

    assets = project / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    cover = assets / "cover.png"
    icon = assets / "icon.png"
    create_thumbnail_png(cover, palette, motif, variant, seed)
    create_icon_png(icon, palette, motif, variant, seed)
    print(f"Cover: {cover}")
    print(f"Icon: {icon}")


if __name__ == "__main__":
    main()
