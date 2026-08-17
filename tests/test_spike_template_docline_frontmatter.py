"""Docline frontmatter conformance tests for ``templates/skills/spike/SKILL.md.tmpl``.

Protects the 128-F / 137-S fix: the Phase 5 findings-artifact YAML example must
carry docline-required top-level fields (``title``, ``source``,
``doc_type: decision``, ``description``) and nest the spike-specific fields
(``type``, ``date``, ``time_box``, ``conclusion``, ``confidence``,
``linked_parent_work_item``, ``promoted_to``, ``tags``) under a ``docline``
mapping -- the shape validated by ``backlogit docs lint --profile authoring``.

Before this fix, every findings artifact generated from this template failed
authoring lint with 2 violations (missing ``source``, missing ``doc_type``),
because the spike-specific fields lived at the top level instead of nested
under ``docline``. See:

* docs/plans/2026-08-16-spike-template-docline-conformance-plan.md
* docs/reviews/2026-08-16-spike-template-docline-conformance-review.md
* .backlogit/queue/128.001-T.md, .backlogit/queue/128.002-T.md

Does NOT modify or import from ``tests/test_verify_workspace.py``.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "templates" / "skills" / "spike" / "SKILL.md.tmpl"
_DOCS_DECISIONS = _REPO_ROOT / "docs" / "decisions"

_BACKLOGIT = shutil.which("backlogit")

_PHASE5_MARKER = "### Phase 5: Write Findings Artifact"
_STEP_42_MARKER = "#### Step 4.2: Promote to Implementation Plan (When Applicable)"
_STEP_43_MARKER = "#### Step 4.3: Create Backlog Item (When Applicable)"

_DOCLINE_NESTED_FIELDS = (
    "type",
    "date",
    "time_box",
    "conclusion",
    "confidence",
    "linked_parent_work_item",
    "promoted_to",
    "tags",
)


def _read_template() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


def _extract_phase5_example_block(text: str) -> str:
    """Return the contents of the fenced ```markdown findings-artifact example
    inside Phase 5 (the block that documents the artifact the agent writes)."""
    marker_idx = text.index(_PHASE5_MARKER)
    tail = text[marker_idx:]
    fence_open = tail.index("```markdown")
    fence_body_start = fence_open + len("```markdown")
    fence_close = tail.index("\n```", fence_body_start)
    return tail[fence_body_start:fence_close]


def _extract_frontmatter_text(block: str) -> str:
    """Return the raw YAML text between the first pair of ``---`` delimiters
    in a findings-artifact example block."""
    match = re.search(r"^\s*\n?---\n(.*?)\n---\n", block, re.DOTALL)
    if match is None:
        raise AssertionError(
            "Could not locate a '---'-delimited frontmatter block in the "
            "Phase 5 findings-artifact example"
        )
    return match.group(1)


def _extract_step_section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


class Phase5FrontmatterShapeTests(unittest.TestCase):
    """Assert the Phase 5 findings-artifact example uses the docline-nested
    contract: docline-required fields at top level, spike-specific fields
    nested under ``docline``."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.template_text = _read_template()
        cls.example_block = _extract_phase5_example_block(cls.template_text)
        cls.frontmatter_text = _extract_frontmatter_text(cls.example_block)
        cls.frontmatter = yaml.safe_load(cls.frontmatter_text)

    def test_frontmatter_parses_as_a_mapping(self) -> None:
        self.assertIsInstance(
            self.frontmatter,
            dict,
            "Phase 5 findings-artifact frontmatter must parse as a YAML mapping",
        )

    def test_top_level_docline_required_fields_present(self) -> None:
        for field in ("title", "source", "doc_type", "description"):
            self.assertIn(
                field,
                self.frontmatter,
                f"Phase 5 frontmatter is missing required top-level field {field!r}",
            )

    def test_doc_type_is_decision(self) -> None:
        self.assertEqual(
            self.frontmatter.get("doc_type"),
            "decision",
            "Phase 5 frontmatter must declare doc_type: decision "
            "(confirmed in the linter's closed vocabulary)",
        )

    def test_source_uses_docs_decisions_template_variable(self) -> None:
        source_value = self.frontmatter.get("source")
        self.assertIsInstance(source_value, str)
        self.assertIn(
            "{{DOCS_DECISIONS}}",
            source_value,
            "source must use the already-registered {{DOCS_DECISIONS}} "
            "template variable, not a hardcoded docs/decisions path",
        )

    def test_docline_mapping_present(self) -> None:
        self.assertIn(
            "docline",
            self.frontmatter,
            "Phase 5 frontmatter must nest spike-specific fields under a "
            "top-level 'docline' mapping",
        )
        self.assertIsInstance(self.frontmatter["docline"], dict)

    def test_spike_specific_fields_nested_under_docline(self) -> None:
        docline = self.frontmatter["docline"]
        for field in _DOCLINE_NESTED_FIELDS:
            self.assertIn(
                field,
                docline,
                f"docline mapping is missing nested field {field!r}",
            )

    def test_docline_type_is_spike(self) -> None:
        self.assertEqual(self.frontmatter["docline"].get("type"), "spike")

    def test_no_residual_top_level_spike_fields(self) -> None:
        """Regression guard against a partial fix: none of the
        spike-specific fields may remain at the top level once they are
        nested under docline."""
        for field in _DOCLINE_NESTED_FIELDS:
            self.assertNotIn(
                field,
                self.frontmatter,
                f"{field!r} must not remain at the top level -- it belongs "
                "under docline (partial-fix regression)",
            )

    def test_no_residual_top_level_key_lines_in_raw_text(self) -> None:
        """Belt-and-suspenders textual check (independent of YAML parsing):
        no line in the frontmatter text may declare a bare, unindented
        ``type:``, ``conclusion:``, or ``promoted_to:`` key -- those may only
        appear indented beneath ``docline:``."""
        for line in self.frontmatter_text.splitlines():
            for bad_key in ("type:", "conclusion:", "promoted_to:"):
                if line.startswith(bad_key):
                    self.fail(
                        f"Found top-level (unindented) {bad_key!r} line in "
                        f"Phase 5 frontmatter: {line!r}"
                    )

    def test_inputs_section_untouched(self) -> None:
        """The Inputs section describes skill inputs (time_box,
        linked_parent_work_item as parameters), not frontmatter fields, and
        must not be altered by this fix."""
        self.assertIn(
            "* `time_box`: (Optional) Maximum duration for the investigation.",
            self.template_text,
        )
        self.assertIn(
            "* `linked_parent_work_item`: (Optional) Path or ID of a feature "
            "or chore this spike informs.",
            self.template_text,
        )


class Step42PromotionInstructionTests(unittest.TestCase):
    """Assert Step 4.2's promotion instructions were re-pointed to reference
    the docline-nested fields -- the 'coherence trap' the plan calls out:
    fixing the example alone would leave the template instructing a
    top-level ``promoted_to`` that no longer exists."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.template_text = _read_template()
        cls.step_42_text = _extract_step_section(
            cls.template_text, _STEP_42_MARKER, _STEP_43_MARKER
        )

    def test_step_references_docline_promoted_to(self) -> None:
        self.assertIn(
            "docline.promoted_to",
            self.step_42_text,
            "Step 4.2 must reference docline.promoted_to, not a top-level "
            "promoted_to field",
        )

    def test_step_references_docline_plan_artifact(self) -> None:
        self.assertIn(
            "docline.plan_artifact",
            self.step_42_text,
            "Step 4.2 must reference docline.plan_artifact, not a top-level "
            "plan_artifact field",
        )

    def test_no_residual_top_level_promoted_to_instruction(self) -> None:
        """Regression guard: the pre-fix instruction text referenced a bare
        (non-docline-scoped) 'promoted_to' frontmatter field. That exact
        phrasing must not survive the fix."""
        self.assertNotIn(
            "spike findings artifact's `promoted_to` frontmatter field",
            self.step_42_text,
            "Step 4.2 still contains the stale, non-docline-scoped "
            "'promoted_to' instruction (coherence-trap regression)",
        )


@unittest.skipUnless(_BACKLOGIT, "backlogit CLI not found on PATH")
class BacklogitLintAcceptanceTests(unittest.TestCase):
    """Acceptance evidence: render a fixture findings artifact using the
    corrected docline-nested shape into the IN-SCOPE docs/decisions/ surface
    and confirm the real installed `backlogit docs lint` linter is satisfied.

    The path qualifier is load-bearing (measured: `--path docs/plans`
    returns empty output and exit 1 because it is not an in-scope
    documentation surface -- a fixture linted from the wrong directory would
    pass vacuously). The fixture is written to, and removed from,
    docs/decisions/ for the duration of this test only.
    """

    def setUp(self) -> None:
        self.slug = f"test-spike-docline-fixture-{uuid.uuid4().hex[:8]}"
        self.date = "2026-08-17"
        self.fixture_relpath = f"docs/decisions/{self.date}-{self.slug}.md"
        self.fixture_path = _REPO_ROOT / self.fixture_relpath
        self.addCleanup(self._remove_fixture)

    def _remove_fixture(self) -> None:
        if self.fixture_path.exists():
            self.fixture_path.unlink()

    def _write_fixture(self, doc_type: str = "decision") -> None:
        # A concrete, non-vacuous rendering of the target docline-nested
        # shape -- substituted date/slug (per the P1-1 review finding) and a
        # real recommendation, not a copy-pasted placeholder string.
        content = f"""---
title: "Is the docline-nested spike frontmatter shape lint-clean?"
source: {self.fixture_relpath}
doc_type: {doc_type}
description: "Test fixture for 128.002-T: renders the corrected spike Phase 5 frontmatter shape and confirms it satisfies backlogit docs lint."
docline:
  type: spike
  date: {self.date}
  time_box: "1h"
  conclusion: "proceed"
  confidence: "high"
  linked_parent_work_item: "128-F"
  promoted_to: ["none"]
  tags:
    - "templates"
    - "docline"
---

## Goal

Does the docline-nested findings-artifact shape pass `backlogit docs lint --profile authoring`?

## Recommendation

**Conclusion**: proceed
**Confidence**: high

Yes -- confirmed by this fixture.
"""
        self.fixture_path.write_text(content, encoding="utf-8")

    def _run_lint(self, profile: str) -> dict:
        result = subprocess.run(
            [
                _BACKLOGIT,
                "docs",
                "lint",
                "--profile",
                profile,
                "--path",
                self.fixture_relpath,
                "--format",
                "json",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        import json

        self.assertTrue(
            result.stdout.strip(),
            f"backlogit docs lint produced no output (stderr: {result.stderr!r})",
        )
        return json.loads(result.stdout)

    def test_authoring_profile_reports_zero_findings(self) -> None:
        self._write_fixture()
        payload = self._run_lint("authoring")
        self.assertEqual(
            payload.get("violation_count"),
            0,
            f"Expected zero authoring-lint findings for the docline-nested "
            f"fixture, got: {payload.get('findings')}",
        )
        self.assertTrue(payload.get("valid"))

    def test_ingestion_profile_accepts_doc_type_decision(self) -> None:
        self._write_fixture()
        payload = self._run_lint("ingestion")
        unknown_doc_type_findings = [
            f
            for f in payload.get("findings", [])
            if f.get("rule") == "unknown_doc_type"
        ]
        self.assertEqual(
            unknown_doc_type_findings,
            [],
            "doc_type: decision must be in the ingestion profile's closed "
            f"vocabulary; got: {unknown_doc_type_findings}",
        )


if __name__ == "__main__":
    unittest.main()
