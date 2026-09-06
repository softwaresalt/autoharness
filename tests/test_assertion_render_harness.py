"""Self-tests for the render-aware assertion harness (151.003-T).

Task 3a of the SHIP-1 v1.5.0 guardrail-contract-restoration shipment. These
tests validate the *harness itself* -- enumeration, source-of-truth resolution,
caching, variable-table reuse and the role-scoped overlay. The table-driven
assertion sweep that consumes the harness is task 3b (`151.004-T`) and lives in
its own module.

Freeze-scope (SHIP-1 plan H7): `tests/` only. Nothing here writes to the
repository or mutates a template, verifier assertion, or installed artifact.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from _assertion_render import (
    KIND_INSTALLED,
    KIND_TEMPLATE,
    REPO_ROOT,
    VARIANT_BACKLOGIT,
    VARIANT_NON_BACKLOGIT,
    RenderedCorpus,
    corpus_for,
    iter_assertions,
    render_source,
    resolve_source_of_truth,
    unresolved_placeholders,
)

# The 5 autoharness *engine* artifacts that have no `.tmpl` at all: they are the
# installer/tuner/discovery surfaces, not generated harness output. For these
# the installed file IS the source of truth (151.006-T deliverable 2).
EXPECTED_INSTALLED_ONLY_PATHS = {
    ".github/agents/auto-tune.agent.md",
    ".github/instructions/harness-architecture.instructions.md",
    ".github/skills/install-harness/SKILL.md",
    ".github/skills/tune-harness/SKILL.md",
    ".github/skills/workspace-discovery/SKILL.md",
}


class AssertionEnumerationTests(unittest.TestCase):
    """The harness enumerates the live verifier tables with no exemption list."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.assertions = iter_assertions()

    def test_every_assertion_key_is_unique(self) -> None:
        keys = [assertion.key for assertion in self.assertions]
        self.assertEqual(
            len(keys),
            len(set(keys)),
            "assertion keys must be unique so a sweep can key by assertion key",
        )

    def test_tables_are_read_live_not_copied(self) -> None:
        from autoharness.verify_workspace import (
            DARK_FACTORY_ASSERTIONS,
            FOUNDATION_ASSERTIONS,
            PACK_ASSERTIONS,
        )

        expected = (
            sum(len(entries) for entries in PACK_ASSERTIONS.values())
            + len(FOUNDATION_ASSERTIONS)
            + len(DARK_FACTORY_ASSERTIONS)
        )
        self.assertEqual(
            len(self.assertions),
            expected,
            "the harness must enumerate every live table entry, with no local "
            "copy and no exemption list",
        )

    def test_every_assertion_carries_its_contract(self) -> None:
        for assertion in self.assertions:
            with self.subTest(assertion=assertion.key):
                self.assertTrue(assertion.must_contain, "must_contain may not be empty")
                self.assertIn(assertion.source_kind, {KIND_TEMPLATE, KIND_INSTALLED})


class SourceOfTruthResolutionTests(unittest.TestCase):
    """Binding H2: resolve to the `.tmpl` when one exists, installed only when not."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.assertions = iter_assertions()

    def test_every_assertion_resolves_to_an_existing_file(self) -> None:
        for assertion in self.assertions:
            with self.subTest(assertion=assertion.key):
                self.assertTrue(
                    assertion.source_path.is_file(),
                    f"{assertion.key} resolved to a nonexistent source "
                    f"{assertion.source_path}",
                )

    def test_template_resolution_is_preferred_over_the_installed_copy(self) -> None:
        for assertion in self.assertions:
            if assertion.source_kind != KIND_INSTALLED:
                continue
            with self.subTest(assertion=assertion.key):
                self.assertIn(
                    assertion.path,
                    EXPECTED_INSTALLED_ONLY_PATHS,
                    f"{assertion.key} fell back to the installed copy "
                    f"({assertion.path}); reading a dogfood mirror when a "
                    "template exists reproduces the exact blindness H2 fixes",
                )

    def test_installed_only_paths_genuinely_have_no_template(self) -> None:
        for path in sorted(EXPECTED_INSTALLED_ONLY_PATHS):
            with self.subTest(path=path):
                source, kind = resolve_source_of_truth(path)
                self.assertEqual(kind, KIND_INSTALLED)
                self.assertEqual(source, REPO_ROOT / path)

    def test_role_bearing_agents_resolve_to_their_templates(self) -> None:
        # The two v1.5.0 defects both hid behind a lagging dogfood mirror, so
        # these three paths in particular must never read the installed copy.
        for path in (
            ".github/agents/_ship.agent.md",
            ".github/agents/_stage.agent.md",
            ".github/skills/operational-closure/SKILL.md",
        ):
            with self.subTest(path=path):
                source, kind = resolve_source_of_truth(path)
                self.assertEqual(kind, KIND_TEMPLATE)
                self.assertEqual(source.suffix, ".tmpl")

    def test_unknown_path_falls_back_to_the_installed_location(self) -> None:
        source, kind = resolve_source_of_truth("docs/ARCHITECTURE.md")
        self.assertEqual(kind, KIND_INSTALLED)
        self.assertEqual(source, REPO_ROOT / "docs/ARCHITECTURE.md")


class RenderHarnessTests(unittest.TestCase):
    """Variable-table reuse, caching, and read-only behaviour."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = corpus_for(VARIANT_BACKLOGIT)

    def test_corpus_is_cached_per_variant(self) -> None:
        self.assertIs(self.corpus, corpus_for(VARIANT_BACKLOGIT))
        self.assertIsNot(self.corpus, corpus_for(VARIANT_NON_BACKLOGIT))

    def test_render_is_memoised_per_source(self) -> None:
        assertion = next(
            a for a in iter_assertions() if a.path == ".github/agents/_ship.agent.md"
        )
        first = self.corpus.render_assertion(assertion)
        # Second call must hit the cache: assert identity, not just equality.
        self.assertIs(first, self.corpus.render_assertion(assertion))

    def test_rendering_resolves_placeholders_from_the_verifier_tables(self) -> None:
        from autoharness.verify_workspace import _derive_template_variables

        self.assertTrue(callable(_derive_template_variables))
        self.assertGreater(len(self.corpus.variables), 100)
        rendered = self.corpus.render(
            REPO_ROOT / "templates/skills/operational-closure/SKILL.md.tmpl",
            ".github/skills/operational-closure/SKILL.md",
        )
        self.assertNotIn("{{DOCS_CLOSURE}}", rendered)
        self.assertIn(self.corpus.variables["DOCS_CLOSURE"], rendered)

    def test_installed_only_sources_are_returned_verbatim(self) -> None:
        path = ".github/instructions/harness-architecture.instructions.md"
        source, kind = resolve_source_of_truth(path)
        self.assertEqual(kind, KIND_INSTALLED)
        self.assertEqual(
            self.corpus.render(source, path),
            source.read_text(encoding="utf-8"),
        )

    def test_role_overlay_composes_without_mutating_the_base_table(self) -> None:
        base_snapshot = dict(self.corpus.variables)
        ship_variables = self.corpus.variables_for(".github/agents/_ship.agent.md")
        stage_variables = self.corpus.variables_for(".github/agents/_stage.agent.md")
        for variables in (ship_variables, stage_variables):
            for key in (
                "ESCALATION_FAMILY",
                "ESCALATION_PROVIDER",
                "ESCALATION_REASONING_EFFORT",
            ):
                self.assertIn(key, variables)
        self.assertEqual(base_snapshot, self.corpus.variables)

    def test_role_neutral_artifacts_reuse_the_base_table(self) -> None:
        self.assertIs(
            self.corpus.variables_for("AGENTS.md"),
            self.corpus.variables,
        )

    def test_rendering_never_writes_to_the_repository(self) -> None:
        template = REPO_ROOT / "templates/skills/operational-closure/SKILL.md.tmpl"
        before = template.read_bytes()
        mtime_before = template.stat().st_mtime_ns
        self.corpus.render(template, ".github/skills/operational-closure/SKILL.md")
        self.assertEqual(before, template.read_bytes())
        self.assertEqual(mtime_before, template.stat().st_mtime_ns)


class VariableSetTests(unittest.TestCase):
    """Both variable sets required by the 151.001-T acceptance criteria."""

    def test_backlogit_and_non_backlogit_sets_differ_on_the_backlog_axis(self) -> None:
        backlogit = corpus_for(VARIANT_BACKLOGIT).variables
        non_backlogit = corpus_for(VARIANT_NON_BACKLOGIT).variables
        self.assertEqual(backlogit["BACKLOG_DIRECTORY"], ".backlogit")
        self.assertEqual(non_backlogit["BACKLOG_DIRECTORY"], "backlog")
        self.assertEqual(backlogit["BACKLOG_TOOL_NAME"], "backlogit")
        self.assertEqual(non_backlogit["BACKLOG_TOOL_NAME"], "backlog-md")

    def test_unknown_variant_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RenderedCorpus("backlog-md-ish")

    def test_unresolved_placeholder_helper_detects_tokens(self) -> None:
        self.assertEqual(
            unresolved_placeholders("a {{BACKLOG_DIRECTORY}} b {{DOCS_CLOSURE}}"),
            ["{{BACKLOG_DIRECTORY}}", "{{DOCS_CLOSURE}}"],
        )
        self.assertEqual(unresolved_placeholders("no placeholders here"), [])

    def test_operational_closure_template_leaves_no_unresolved_placeholder_under_either_variant(
        self,
    ) -> None:
        """151.001-T acceptance (plan lines 211-215): a real render of the
        edited ``operational-closure`` template under BOTH the backlogit and
        the non-backlogit variable sets must leave zero unresolved ``{{``
        tokens. The helper-on-synthetic-strings test above proves the scanner
        works; this test proves the actual template output is clean (Copilot
        review finding on this feature's own PR: checking only four variable
        map entries would let a real unresolved token through undetected).
        """
        installed_path = ".github/skills/operational-closure/SKILL.md"
        for variant in (VARIANT_BACKLOGIT, VARIANT_NON_BACKLOGIT):
            with self.subTest(variant=variant):
                rendered = render_source(installed_path, variant)
                self.assertEqual(
                    unresolved_placeholders(rendered),
                    [],
                    f"unresolved {{{{...}}}} placeholder(s) remain in the "
                    f"{variant!r}-variant render of {installed_path}",
                )
                self.assertIn("Source artifact cleanup", rendered)
                self.assertIn("source_stash_id", rendered)
                self.assertIn("source_deliberation_id", rendered)
                self.assertNotIn("{{FEATURE_", rendered)


class HarnessLocationTests(unittest.TestCase):
    """The harness must live under `tests/` (freeze-scope guard)."""

    def test_harness_module_is_inside_the_tests_package(self) -> None:
        import _assertion_render

        module_path = Path(_assertion_render.__file__).resolve()
        self.assertEqual(module_path.parent, REPO_ROOT / "tests")


if __name__ == "__main__":
    unittest.main()
