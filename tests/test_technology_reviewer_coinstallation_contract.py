"""Contract tests for 154.004-T (SHIP-4, F0ADCC03): Decision F co-installation
invariant between the technology-reviewer persona and its matching language
instruction file.

Covers the BINDING OUTCOME MATRIX (M1-M5) with the KIND declared on each row
in the task: CONTRACT (assertion over install-harness/SKILL.md text), SET
(assertion over the template set on disk), or RENDER (assertion over
`_render_template` output). No composer or installer exists in this product
(measured at HEAD: src/autoharness/ contains cli, verify_workspace,
backlog_root, schema_contracts, startup_script_contract, detectors/, eval/,
gates/, telemetry/ — no install/compose entry point), so no row asserts a
composition exit code or a composed-workspace filesystem effect; M5 is the
one row with a real executable observable (a template render).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml
from autoharness.verify_workspace import _derive_template_variables, _render_template

_REPO_ROOT = Path(__file__).resolve().parents[1]
_INSTALL_SKILL = _REPO_ROOT / ".github" / "skills" / "install-harness" / "SKILL.md"
_TECH_REVIEWER_TEMPLATE = (
    _REPO_ROOT / "templates" / "agents" / "review" / "technology-reviewer.agent.md.tmpl"
)
_PYTHON_REVIEWER_DOGFOOD = (
    _REPO_ROOT / ".github" / "agents" / "subagents" / "python-reviewer.agent.md"
)
_PYTHON_INSTRUCTIONS = _REPO_ROOT / ".github" / "instructions" / "python.instructions.md"

_TEMPLATE_INSTRUCTIONS_DIR = _REPO_ROOT / "templates" / "instructions"


def _lf_text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def _extract_decision_f_block(text: str) -> str:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().startswith("**Decision F"):
            start = index
            break
    if start is None:
        raise AssertionError("Decision F block not found in install-harness/SKILL.md")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("5. **Orchestrating review skills**"):
            end = index
            break
    return "\n".join(lines[start:end])


class DecisionFCoInstallationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_text = _lf_text(_INSTALL_SKILL)
        cls.decision_f = _extract_decision_f_block(cls.skill_text)

    def test_files_exist(self) -> None:
        self.assertTrue(_INSTALL_SKILL.is_file())
        self.assertTrue(_TECH_REVIEWER_TEMPLATE.is_file())
        self.assertTrue(_PYTHON_REVIEWER_DOGFOOD.is_file())

    def test_m1_variant_first_choice_contract_and_set(self) -> None:
        """M1: CONTRACT — variant template is the first-choice source, named
        explicitly. SET — the template set actually contains a variant for at
        least one measured language, carrying a marker unique to the variant."""
        self.assertIn("technology-{L}.instructions.md.tmpl", self.decision_f)
        self.assertIn("first choice", self.decision_f)
        self.assertRegex(self.decision_f, r"variant.*first choice|first choice.*variant")

        variant = _TEMPLATE_INSTRUCTIONS_DIR / "technology-python.instructions.md.tmpl"
        generic = _TEMPLATE_INSTRUCTIONS_DIR / "technology.instructions.md.tmpl"
        self.assertTrue(variant.is_file())
        self.assertTrue(generic.is_file())
        variant_text = variant.read_text(encoding="utf-8")
        generic_text = generic.read_text(encoding="utf-8")
        # The variant must carry content the generic skeleton does not (a
        # marker unique to the variant, not merely file existence).
        self.assertNotEqual(variant_text.strip(), generic_text.strip())
        self.assertGreater(len(variant_text), len(generic_text))

    def test_m2_ordered_fallback_contract_and_set(self) -> None:
        """M2: CONTRACT — ordered fallback is explicit and locatable (variant
        first, generic only when no variant exists). SET — a language with NO
        variant in the measured set resolves to the generic skeleton, which
        carries a marker distinct from every variant marker."""
        self.assertIn("otherwise from the generic", self.decision_f)
        self.assertIn("fallback, only when no variant exists", self.decision_f)

        variant_languages = {
            p.name[len("technology-"):-len(".instructions.md.tmpl")]
            for p in _TEMPLATE_INSTRUCTIONS_DIR.glob("technology-*.instructions.md.tmpl")
        }
        # A language with no variant in the measured set (naming python here
        # would make M2 indistinguishable from M1 per the task's own note).
        no_variant_language = "ruby"
        self.assertNotIn(no_variant_language, variant_languages)

        generic = _TEMPLATE_INSTRUCTIONS_DIR / "technology.instructions.md.tmpl"
        self.assertTrue(generic.is_file())
        generic_text = generic.read_text(encoding="utf-8")
        # Generic skeleton carries a marker unique to it — its own template
        # provenance footer names "technology.instructions.md.tmpl" (no
        # language qualifier), distinct from every variant's footer, which
        # names "technology-{lang}.instructions.md.tmpl".
        self.assertIn("Template: technology.instructions.md.tmpl", generic_text)
        for variant_language in variant_languages:
            variant_path = (
                _TEMPLATE_INSTRUCTIONS_DIR / f"technology-{variant_language}.instructions.md.tmpl"
            )
            variant_text = variant_path.read_text(encoding="utf-8")
            self.assertNotIn("Template: technology.instructions.md.tmpl", variant_text)
            self.assertIn(f"Template: technology-{variant_language}.instructions.md.tmpl", variant_text)
            self.assertNotEqual(variant_text.strip(), generic_text.strip())

    def test_m3_halt_with_named_error_both_negatives(self) -> None:
        """M3: CONTRACT — halt with a named error identifying both missing
        template paths; both negatives stated (not silently dropped, not
        installed dangling)."""
        self.assertIn("HALTS WITH A NAMED ERROR", self.decision_f)
        self.assertIn("identifying both missing template paths", self.decision_f)
        self.assertIn("does NOT silently drop the reviewer", self.decision_f)
        self.assertIn("does NOT silently install a dangling one", self.decision_f)

    def test_m4_scoped_to_reviewer_selection_non_interference(self) -> None:
        """M4: CONTRACT — F1 rule scoped explicitly to reviewer-selected
        compositions; explicit non-interference with Step 2.2 item 1's
        unconditional install."""
        self.assertIn("the F1 rule does not fire", self.decision_f)
        self.assertIn("Step 2.2 item 1", self.decision_f)
        self.assertIn(
            "Decision F neither adds to nor suppresses that",
            self.decision_f,
        )

    def test_m5_render_graceful_reference(self) -> None:
        """M5: RENDER — the one row with a real executable observable. Render
        technology-reviewer.agent.md.tmpl with PRIMARY_LANGUAGE_LOWER=python
        and assert the output degrades to generic guidance with no
        unconditional reference to a non-existent
        .github/instructions/python.instructions.md; assert the installed
        mirror agrees; assert python.instructions.md is still absent."""
        autoharness_dir = _REPO_ROOT / ".autoharness"
        load_yaml = lambda name: yaml.safe_load(
            (autoharness_dir / name).read_text(encoding="utf-8")
        )
        variables = _derive_template_variables(
            _REPO_ROOT,
            load_yaml("harness-manifest.yaml"),
            load_yaml("config.yaml"),
            load_yaml("workspace-profile.yaml"),
            load_yaml("backlog-registry.yaml"),
        )
        self.assertEqual(variables.get("PRIMARY_LANGUAGE_LOWER"), "python")
        template_text = _lf_text(_TECH_REVIEWER_TEMPLATE)
        rendered = _render_template(template_text, variables)

        # Negative assertion: no unconditional reference — the "authoritative
        # style guide" clause must always be paired with a "when present" /
        # "when it is not present" conditional, never a bare citation.
        self.assertIn("python.instructions.md", rendered)
        self.assertIn("when it is present in this composed workspace", rendered)
        self.assertIn("degrade to generic coding-discipline guidance", rendered)
        self.assertNotRegex(
            rendered,
            r"Reference the workspace's `python\.instructions\.md` as the authoritative style guide\s*$",
            "found an unconditional style-guide reference with no fallback clause",
        )

        dogfood = _lf_text(_PYTHON_REVIEWER_DOGFOOD)
        self.assertIn("when it is present in this composed workspace", dogfood)
        self.assertIn("degrade to generic coding-discipline guidance", dogfood)

        # F2 alone closes this — it must not have slid into rejected
        # strategy (a) (installing the file).
        self.assertFalse(
            _PYTHON_INSTRUCTIONS.exists(),
            "python.instructions.md must remain absent in this repository (F2, not strategy (a))",
        )

    def test_f1_scope_is_forward_and_not_retroactive(self) -> None:
        self.assertIn("forward, at composition time, and NOT retroactive", self.decision_f)
        self.assertIn("does not recompose an existing workspace", self.decision_f)


if __name__ == "__main__":
    unittest.main()
