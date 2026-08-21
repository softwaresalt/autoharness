"""Docline frontmatter conformance tests for
``templates/skills/compound/SKILL.md.tmpl`` (140.002-T / 148-S).

Protects the fix: the Phase 3 learnings-file YAML example must carry
``source`` and ``doc_type`` (docline base frontmatter contract fields), and
the accompanying guidance must remain CAPABILITY-NEUTRAL -- naming no
specific backlog tool or CLI command -- because ``compound`` is a base
Primitive 1 artifact installed into workspaces that may have no backlogit
(and no backlog tool at all).

See:
* docs/plans/2026-08-21-docs-compound-docline-conformance-plan.md (Task 2, amendment C3)
* docs/reviews/2026-08-21-docs-compound-docline-conformance-review.md (P1-3)
* .backlogit/queue/140.002-T.md
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "templates" / "skills" / "compound" / "SKILL.md.tmpl"
_INSTALLED_SKILLS_DIR = _REPO_ROOT / ".github" / "skills"
_HARNESS_MANIFEST = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"

_PHASE3_MARKER = "### Phase 3: Write"
_QUALITY_CRITERIA_MARKER = "## Quality Criteria"

# A future edit must not reintroduce a hard-coded backlog-tool name or CLI
# invocation into the doc_type/source guidance (amendment C3 / AC8b).
_FORBIDDEN_TOOL_TOKENS = (
    "backlogit",
    "docs classify",
    "docs migrate",
    "docs lint",
    "docs scope",
)


def _read_template() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


def _extract_phase3_yaml_block(text: str) -> str:
    """Return the contents of the fenced ```yaml Phase 3 frontmatter example."""
    marker_idx = text.index(_PHASE3_MARKER)
    tail = text[marker_idx:]
    fence_open = tail.index("```yaml")
    fence_body_start = fence_open + len("```yaml")
    fence_close = tail.index("\n```", fence_body_start)
    return tail[fence_body_start:fence_close]


def _extract_frontmatter_keys(yaml_block: str) -> set[str]:
    """Top-level (unindented) 'key:' lines within the ---/--- delimiters."""
    match = re.search(r"^\s*\n?---\n(.*?)\n---\n", yaml_block, re.DOTALL)
    assert match is not None, "Phase 3 example must contain a ---/--- frontmatter block"
    body = match.group(1)
    keys: set[str] = set()
    for line in body.splitlines():
        key_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):", line)
        if key_match:
            keys.add(key_match.group(1))
    return keys


def _extract_guidance_section(text: str) -> str:
    """The prose guidance between the Phase 3 fenced example and Quality
    Criteria -- this is where the doc_type/source authority-order guidance
    lives, and where AC8b's mechanical scan applies."""
    phase3_idx = text.index(_PHASE3_MARKER)
    quality_idx = text.index(_QUALITY_CRITERIA_MARKER, phase3_idx)
    return text[phase3_idx:quality_idx]


class Phase3FrontmatterFieldsTests(unittest.TestCase):
    """AC7: the Phase 3 example carries source and doc_type."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.template_text = _read_template()
        cls.yaml_block = _extract_phase3_yaml_block(cls.template_text)
        cls.keys = _extract_frontmatter_keys(cls.yaml_block)

    def test_source_key_present(self) -> None:
        self.assertIn("source", self.keys)

    def test_doc_type_key_present(self) -> None:
        self.assertIn("doc_type", self.keys)

    def test_doc_type_value_is_learning(self) -> None:
        self.assertIn('doc_type: "learning"', self.yaml_block)

    def test_source_uses_existing_docs_compound_variable(self) -> None:
        """AC8: no new template variable is introduced -- source reuses the
        already-registered {{DOCS_COMPOUND}} variable."""
        source_line = next(
            line for line in self.yaml_block.splitlines() if line.startswith("source:")
        )
        self.assertIn("{{DOCS_COMPOUND}}", source_line)

    def test_no_new_double_brace_variable_introduced(self) -> None:
        """Every {{VAR}} token in the Phase 3 example must already exist
        elsewhere in the template (pre-existing variable), proving the
        source/doc_type addition did not introduce a new one."""
        pre_existing_vars = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", self.template_text))
        example_vars = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", self.yaml_block))
        new_vars = example_vars - pre_existing_vars
        self.assertEqual(
            new_vars,
            set(),
            f"Phase 3 example introduced unexpected new template variable(s): {new_vars}",
        )
        # DOCS_COMPOUND itself must be among the variables used, confirming
        # the check is non-vacuous.
        self.assertIn("DOCS_COMPOUND", example_vars)

    def test_template_has_no_malformed_or_unresolved_braces(self) -> None:
        """AC8: the template still renders -- every {{ has a matching }}."""
        self.assertEqual(
            self.template_text.count("{{"),
            self.template_text.count("}}"),
            "Unbalanced {{ }} template variable braces",
        )
        self.assertNotRegex(
            self.template_text,
            r"\{\{[^}]*\{\{|\}\}[^{]*\}\}",
            "Nested or malformed {{...}} braces found",
        )


class CapabilityNeutralGuidanceTests(unittest.TestCase):
    """AC8b (amendment C3): the doc_type/source guidance names no specific
    backlog tool or CLI command -- a mechanical scan, not a review."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.template_text = _read_template()
        cls.guidance_section = _extract_guidance_section(cls.template_text)

    def test_guidance_section_contains_authority_order(self) -> None:
        self.assertIn("PATH-DERIVED", self.guidance_section)
        self.assertIn("directory convention", self.guidance_section)

    def test_no_forbidden_tool_tokens_in_guidance(self) -> None:
        lowered = self.guidance_section.lower()
        found = [tok for tok in _FORBIDDEN_TOOL_TOKENS if tok in lowered]
        self.assertEqual(
            found,
            [],
            f"Capability-neutral guidance must not name a specific backlog "
            f"tool/CLI command; found: {found}",
        )

    def test_no_forbidden_tool_tokens_anywhere_in_template(self) -> None:
        """Belt-and-suspenders: scan the entire template file, not just the
        extracted guidance section, in case a future edit relocates the
        doc_type/source guidance."""
        lowered = self.template_text.lower()
        found = [tok for tok in _FORBIDDEN_TOOL_TOKENS if tok in lowered]
        self.assertEqual(
            found,
            [],
            f"templates/skills/compound/SKILL.md.tmpl must remain capability-"
            f"neutral; found forbidden token(s): {found}",
        )

    def test_rung_three_always_resolves(self) -> None:
        self.assertIn(
            "Rung 3 always resolves",
            self.guidance_section,
        )


class QualityCriteriaTests(unittest.TestCase):
    """AC7 (Quality Criteria list): source and doc_type are called out."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.template_text = _read_template()

    def test_quality_criteria_mentions_source_and_doc_type(self) -> None:
        quality_idx = self.template_text.index(_QUALITY_CRITERIA_MARKER)
        quality_section = self.template_text[quality_idx:]
        self.assertIn("`source`", quality_section)
        self.assertIn("`doc_type`", quality_section)


class NoDogfoodCounterpartTests(unittest.TestCase):
    """AC9 / AC10: no installed .github/skills/compound/ counterpart exists,
    and no .autoharness/harness-manifest.yaml entry was touched -- proving
    this is a template-only change with no paired-edit obligation."""

    def test_no_installed_compound_skill_directory(self) -> None:
        compound_dir = _INSTALLED_SKILLS_DIR / "compound"
        self.assertFalse(
            compound_dir.exists(),
            "AC9: .github/skills/compound/ must not exist -- if it now does, "
            "a paired edit plus manifest checksum refresh is required and "
            "this task's scope no longer holds",
        )

    def test_harness_manifest_has_no_compound_entry(self) -> None:
        if not _HARNESS_MANIFEST.exists():
            self.skipTest("no .autoharness/harness-manifest.yaml in this workspace")
        manifest_text = _HARNESS_MANIFEST.read_text(encoding="utf-8")
        self.assertNotIn(
            "skills/compound/SKILL.md\n",
            manifest_text,
            "AC10: no installed compound/ dogfood counterpart entry should "
            "exist in harness-manifest.yaml",
        )


if __name__ == "__main__":
    unittest.main()
