from __future__ import annotations

import argparse
import contextlib
import io
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


if __name__ == "__main__":
    unittest.main()
