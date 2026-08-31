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


def scaffold_tool(
    project: Path,
    *,
    deliverable: str | None = None,
    style: str | None = None,
) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        webapp.scaffold(
            argparse.Namespace(
                kind="tool",
                out=str(project),
                title="Test tool",
                summary="Exercise the primary workflow.",
                ai="none",
                deliverable=deliverable,
                style=style,
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


def scaffold_motion(project: Path) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        webapp.scaffold(
            argparse.Namespace(
                kind="motion",
                deliverable="motion",
                out=str(project),
                title="Load shift",
                summary="Explain a state change over time.",
                ai="none",
                style="retro-system",
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


class DeliverableAndStyleRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_registry_contains_distinct_filterable_families(self) -> None:
        registry = webapp._load_style_registry()
        styles = registry["styles"]
        self.assertGreaterEqual(len(styles), 20)
        identifiers = {style["id"] for style in styles}
        self.assertTrue(
            {
                "scientific-figure",
                "japanese-retro-catalog",
                "pixel-arcade",
                "warm-hospitality",
                "industrial-brutalism",
                "executive-briefing",
                "saas-minimal",
                "engineering-blueprint",
                "industrial-control",
                "manufacturing-quality",
                "future-lab",
                "mission-control",
                "financial-analyst",
            }.issubset(identifiers)
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            webapp.list_styles(
                argparse.Namespace(
                    deliverable="motion",
                    kind="game",
                    scheme="dark",
                    json=True,
                )
            )
        filtered = json.loads(output.getvalue())
        self.assertIn("pixel-arcade", {style["id"] for style in filtered["styles"]})
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            webapp.list_styles(
                argparse.Namespace(
                    deliverable=None,
                    kind=None,
                    scheme=None,
                    collection="industrial-engineering",
                    json=True,
                )
            )
        industrial = json.loads(output.getvalue())
        self.assertEqual(
            {style["id"] for style in industrial["styles"]},
            {
                "industrial-control",
                "manufacturing-quality",
                "engineering-blueprint",
                "industrial-brutalism",
            },
        )

    def test_base_kinds_apply_executable_contracts(self) -> None:
        contracts = webapp._load_kind_contracts()["contracts"]
        self.assertEqual(
            {contract["kind"] for contract in contracts},
            {"tool", "dashboard", "guided", "knowledge", "game", "presentation"},
        )
        for contract in contracts:
            project = self.workspace / str(contract["kind"])
            with contextlib.redirect_stdout(io.StringIO()):
                webapp.scaffold(
                    argparse.Namespace(
                        kind=contract["kind"],
                        deliverable=None,
                        scenario=None,
                        style=None,
                        out=str(project),
                        title=f"{contract['kind']} contract",
                        summary="Validate the kind-specific workflow.",
                        ai="none",
                        brand=None,
                    )
                )
            source = (project / "index.html").read_text(encoding="utf-8")
            self.assertIn(f'data-kind-contract="{contract["id"]}"', source)
            errors, warnings = webapp.inspect_html(project / "index.html")
            self.assertEqual(errors, [], contract["kind"])
            self.assertEqual(warnings, [], contract["kind"])

    def test_scaffold_records_deliverable_and_applies_style_seed(self) -> None:
        project = self.workspace / "prototype"
        scaffold_tool(
            project,
            deliverable="prototype",
            style="industrial-brutalism",
        )
        source = (project / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-deliverable-type="prototype"', source)
        self.assertIn('data-style="industrial-brutalism"', source)
        self.assertIn("Registry style seed: Industrial Brutalism", source)
        errors, warnings = webapp.inspect_html(project / "index.html")
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_kind_infers_existing_deliverable_and_unknown_style_fails(self) -> None:
        project = self.workspace / "deck"
        scaffold_presentation(project)
        source = (project / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-deliverable-type="presentation"', source)
        with self.assertRaisesRegex(SystemExit, "Unknown style"):
            scaffold_tool(self.workspace / "unknown", style="not-registered")

    def test_brand_and_registry_style_are_mutually_exclusive(self) -> None:
        with self.assertRaisesRegex(SystemExit, "either --brand or --style"):
            webapp.scaffold(
                argparse.Namespace(
                    kind="presentation",
                    deliverable="presentation",
                    out=str(self.workspace / "conflict"),
                    title="Conflict",
                    summary="Conflicting visual systems.",
                    ai="none",
                    brand="neutral-corporate",
                    style="neo-swiss-editorial",
                )
            )

    def test_motion_uses_animation_engine_and_contract(self) -> None:
        project = self.workspace / "motion"
        scaffold_motion(project)
        source = (project / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-webapp-kind="motion"', source)
        self.assertIn('data-deliverable-type="motion"', source)
        self.assertIn("requestAnimationFrame", source)
        self.assertIn("prefers-reduced-motion", source)
        errors, warnings = webapp.inspect_html(project / "index.html")
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_scenarios_scaffold_domain_contracts(self) -> None:
        registry = webapp._load_scenario_blueprints()
        scenarios = registry["scenarios"]
        self.assertIsInstance(scenarios, list)
        for scenario in scenarios:
            self.assertIsInstance(scenario, dict)
            project = self.workspace / str(scenario["id"])
            with contextlib.redirect_stdout(io.StringIO()):
                webapp.scaffold(
                    argparse.Namespace(
                        kind=None,
                        deliverable=None,
                        scenario=scenario["id"],
                        style=None,
                        out=str(project),
                        title=f"{scenario['name']} test",
                        summary="Validate a scenario-specific implementation contract.",
                        ai="none",
                    )
                )
            source = (project / "index.html").read_text(encoding="utf-8")
            self.assertIn(f'data-scenario="{scenario["id"]}"', source)
            errors, warnings = webapp.inspect_html(project / "index.html")
            self.assertEqual(errors, [], scenario["id"])
            self.assertEqual(warnings, [], scenario["id"])

    def test_scenario_accepts_independent_style_override(self) -> None:
        project = self.workspace / "independent-style"
        with contextlib.redirect_stdout(io.StringIO()):
            webapp.scaffold(
                argparse.Namespace(
                    kind=None,
                    deliverable=None,
                    scenario="prototype-route-planner",
                    style="neo-swiss-editorial",
                    out=str(project),
                    title="Independent axes",
                    summary="Apply a visual family without changing the scenario contract.",
                    ai="none",
                )
            )
        source = (project / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-scenario="prototype-route-planner"', source)
        self.assertIn('data-scenarios="prototype-route-planner"', source)
        self.assertIn('data-style="neo-swiss-editorial"', source)
        errors, warnings = webapp.inspect_html(project / "index.html")
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_recommend_routes_single_scenario_and_style_cues(self) -> None:
        result = webapp.recommend_for_brief("做一个像素复古的末班车调度游戏")
        self.assertEqual(result["mode"], "single")
        self.assertEqual(result["scenarios"][0]["id"], "game-last-train-dispatch")
        self.assertEqual(result["selectedStyle"]["id"], "pixel-arcade")

    def test_recommend_uses_base_kind_for_generic_application(self) -> None:
        result = webapp.recommend_for_brief(
            "做一个数据密集的运营仪表盘，支持指标筛选和趋势比较"
        )
        self.assertEqual(result["scenarios"][0]["id"], "base-dashboard")
        self.assertEqual(result["scenarios"][0]["sourceType"], "kind-contract")
        self.assertEqual(result["selectedStyle"]["id"], "scientific-figure")

    def test_recommend_routes_workplace_style_families(self) -> None:
        cases = {
            "做一个专业的季度经营汇报，给管理层看": "executive-briefing",
            "做一个工业控制设备监控仪表盘，包含 SCADA 告警": "industrial-control",
            "做一个简洁干净的 SaaS 管理后台": "saas-minimal",
            "做一个科技感 AI 产品原型": "future-lab",
            "做一个工厂质检良率看板": "manufacturing-quality",
            "做一个实时运维指挥中心": "mission-control",
            "做一个工程蓝图式设备架构说明": "engineering-blueprint",
            "做一个财务预算与风控分析看板": "financial-analyst",
        }
        for brief, expected_style in cases.items():
            with self.subTest(brief=brief):
                result = webapp.recommend_for_brief(brief)
                self.assertEqual(result["selectedStyle"]["id"], expected_style)

    def test_recommend_composes_scenarios_but_keeps_one_style_axis(self) -> None:
        result = webapp.recommend_for_brief(
            "做一个博物馆夜游活动落地页，同时用数据图解释夜间能耗"
        )
        self.assertEqual(result["mode"], "composition")
        self.assertEqual(
            result["buildContract"]["scenarioIds"],
            ["marketing-event-launch", "infographic-energy-story"],
        )
        self.assertEqual(result["selectedStyle"]["id"], "mid-century-tactile")
        self.assertIn(
            "data-infographic-takeaway",
            result["buildContract"]["requiredMarkers"],
        )

    def test_validator_enforces_supporting_scenario_markers(self) -> None:
        project = self.workspace / "incomplete-composition"
        with contextlib.redirect_stdout(io.StringIO()):
            webapp.scaffold(
                argparse.Namespace(
                    kind=None,
                    deliverable=None,
                    scenario="marketing-event-launch",
                    style="japanese-retro-catalog",
                    out=str(project),
                    title="Incomplete composition",
                    summary="The supporting scenario has not been implemented.",
                    ai="none",
                )
            )
        path = project / "index.html"
        source = path.read_text(encoding="utf-8").replace(
            'data-scenarios="marketing-event-launch"',
            'data-scenarios="marketing-event-launch,infographic-energy-story"',
        )
        path.write_text(source, encoding="utf-8")
        errors, _ = webapp.inspect_html(path)
        self.assertTrue(
            any("infographic-energy-story is missing required marker" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
