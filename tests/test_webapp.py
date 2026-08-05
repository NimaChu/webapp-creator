from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import webapp  # noqa: E402


def scaffold_tool(project: Path) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        webapp.scaffold(
            argparse.Namespace(
                kind="tool",
                out=str(project),
                title="Test tool",
                summary="Exercise the primary workflow.",
                ai="none",
            )
        )


def scaffold_presentation(project: Path, brand: str | None = None) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        webapp.scaffold(
            argparse.Namespace(
                kind="presentation",
                out=str(project),
                title="Decision deck",
                summary="Choose the next action from verified evidence.",
                ai="none",
                brand=brand,
            )
        )


class HtmlCompletenessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        scaffold_tool(self.project)
        self.html_path = self.project / "index.html"
        self.source = self.html_path.read_text(encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def errors_for(self, source: str) -> list[str]:
        candidate = self.project / "candidate.html"
        candidate.write_text(source, encoding="utf-8")
        errors, _ = webapp.inspect_html(candidate)
        return errors

    def test_complete_document_passes(self) -> None:
        errors, warnings = webapp.inspect_html(self.html_path)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_rejects_duplicate_doctype(self) -> None:
        errors = self.errors_for("<!doctype html>\n" + self.source)
        self.assertTrue(any("exactly one <!doctype html>" in issue for issue in errors))

    def test_rejects_duplicate_html_root(self) -> None:
        errors = self.errors_for(self.source.replace("<html", "<html></html><html", 1))
        self.assertTrue(any("exactly one <html>" in issue for issue in errors))

    def test_rejects_missing_closing_tags(self) -> None:
        errors = self.errors_for(
            self.source.replace("</body>", "").replace("</html>", "")
        )
        self.assertTrue(any("closing </html>" in issue for issue in errors))
        self.assertTrue(any("complete <body>" in issue for issue in errors))

    def test_rejects_markdown_wrapped_html(self) -> None:
        errors = self.errors_for(f"```html\n{self.source}\n```")
        self.assertTrue(any("Markdown fences" in issue for issue in errors))


class BuildProtectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        scaffold_tool(self.project)
        self.output = self.project / "bundle.zip"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def build(self, force: bool) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            webapp.build(
                argparse.Namespace(
                    project=str(self.project),
                    out=str(self.output),
                    allow_warnings=False,
                    force=force,
                )
            )

    def test_refuses_overwrite_without_force(self) -> None:
        self.output.write_bytes(b"keep me")
        with self.assertRaisesRegex(SystemExit, "Use --force"):
            self.build(force=False)
        self.assertEqual(self.output.read_bytes(), b"keep me")

    def test_force_replaces_atomically_and_excludes_output(self) -> None:
        self.output.write_bytes(b"old archive")
        self.build(force=True)
        with zipfile.ZipFile(self.output) as archive:
            self.assertIn("index.html", archive.namelist())
            self.assertNotIn("bundle.zip", archive.namelist())


class PresentationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "deck"
        scaffold_presentation(self.project, brand="international-grid")
        self.html_path = self.project / "index.html"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_branded_presentation_passes_static_validation(self) -> None:
        errors, warnings = webapp.inspect_html(self.html_path)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        source = self.html_path.read_text(encoding="utf-8")
        self.assertIn('data-brand="International Grid"', source)
        self.assertNotIn("__BRAND_", source)

    def test_missing_layout_and_duplicate_slide_id_are_rejected(self) -> None:
        source = self.html_path.read_text(encoding="utf-8")
        source = source.replace(' data-layout="cover"', "", 1)
        source = source.replace('data-slide-id="evidence"', 'data-slide-id="opening"')
        candidate = self.project / "broken.html"
        candidate.write_text(source, encoding="utf-8")
        errors, _ = webapp.inspect_html(candidate)
        self.assertTrue(any("missing data-layout" in issue for issue in errors))
        self.assertTrue(any("Duplicate data-slide-id" in issue for issue in errors))

    def test_unregistered_brand_layout_is_rejected(self) -> None:
        source = self.html_path.read_text(encoding="utf-8")
        source = source.replace('data-layout="evidence"', 'data-layout="unregistered"')
        candidate = self.project / "unregistered.html"
        candidate.write_text(source, encoding="utf-8")
        errors, _ = webapp.inspect_html(candidate)
        self.assertTrue(any("not allowed by the active brand pack" in issue for issue in errors))


class StyleboardAndBrandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_styleboard_uses_real_content_and_protects_output(self) -> None:
        output = self.workspace / "styles"
        args = argparse.Namespace(
            out=str(output),
            title="Real title",
            summary="Real purpose",
            force=False,
        )
        with contextlib.redirect_stdout(io.StringIO()):
            webapp.styleboard(args)
        source = (output / "styleboard.html").read_text(encoding="utf-8")
        self.assertIn("Real title", source)
        self.assertIn("Real purpose", source)
        with self.assertRaisesRegex(SystemExit, "Use --force"):
            webapp.styleboard(args)

    def test_brand_init_creates_an_editable_pack(self) -> None:
        output = self.workspace / "brand"
        with contextlib.redirect_stdout(io.StringIO()):
            webapp.init_brand(
                argparse.Namespace(
                    out=str(output),
                    name="Example Brand",
                    from_pack="neutral-corporate",
                )
            )
        profile = json.loads((output / "brand.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["name"], "Example Brand")
        self.assertTrue((output / "brand.css").is_file())


if __name__ == "__main__":
    unittest.main()
