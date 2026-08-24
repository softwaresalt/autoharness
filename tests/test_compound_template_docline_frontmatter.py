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
        """AC8: this task's diff added exactly two new lines to the
        pre-existing Phase 3 yaml block (`source:` and `doc_type:`); every
        `{{VAR}}` token appearing in THOSE TWO LINES must already be used
        somewhere else in the template.

        Scoping "new" to the two lines this task actually added (rather
        than the whole yaml_block) is essential: the other ~16 fields in
        the Phase 3 example (`{{TITLE}}`, `{{TYPE}}`, `{{CATEGORY}}`, ...)
        are PRE-EXISTING placeholders that are legitimately used ONLY
        inside this one example block -- excluding the whole block from
        `pre_existing_vars` (as a naive fix would) makes every one of them
        falsely register as "new". Confirmed against the template's
        pre-140.002-T content (`git show 4fff68a2^:templates/skills/compound/SKILL.md.tmpl`),
        which has neither a `source:` nor a `doc_type:` line in this block.
        """
        added_lines = [
            line
            for line in self.yaml_block.splitlines()
            if line.startswith("source:") or line.startswith("doc_type:")
        ]
        self.assertEqual(len(added_lines), 2, "expected exactly source: and doc_type: lines")
        added_text = "\n".join(added_lines)
        added_vars = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", added_text))

        rest_of_template = self.template_text
        for line in added_lines:
            rest_of_template = rest_of_template.replace(line, "", 1)
        pre_existing_vars = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", rest_of_template))

        new_vars = added_vars - pre_existing_vars
        self.assertEqual(
            new_vars,
            set(),
            f"source:/doc_type: lines introduced unexpected new template variable(s): {new_vars}",
        )
        # Non-vacuity: DOCS_COMPOUND is the only variable these two lines
        # use, and it must genuinely be used elsewhere in the template too
        # (not only by virtue of these two lines themselves).
        self.assertEqual(added_vars, {"DOCS_COMPOUND"})
        self.assertIn("DOCS_COMPOUND", pre_existing_vars)

    def test_new_placeholder_in_added_lines_is_detected(self) -> None:
        """Non-vacuity guard for the check above: a placeholder that
        appears ONLY in a probe line standing in for source:/doc_type:
        (nowhere else in the template) must be flagged as new, proving the
        exclusion actually changes the outcome rather than being a no-op."""
        rest_of_template = self.template_text
        for line in self.yaml_block.splitlines():
            if line.startswith("source:") or line.startswith("doc_type:"):
                rest_of_template = rest_of_template.replace(line, "", 1)
        pre_existing_vars = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", rest_of_template))

        probe_line = 'new_probe_field: "{{TOTALLY_NEW_PROBE_VAR}}"'
        probe_vars = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", probe_line))
        probe_new_vars = probe_vars - pre_existing_vars
        self.assertEqual(probe_new_vars, {"TOTALLY_NEW_PROBE_VAR"})

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

    def test_quality_criteria_source_bullet_states_value_shape_rule(self) -> None:
        """146.003-T (026-DL): directly-affected regression coverage for the
        Quality Criteria ratchet (Copilot review, PR #404).
        `test_quality_criteria_mentions_source_and_doc_type` above only
        checks that both field-name tokens occur somewhere in the section --
        the old, weaker non-emptiness-only bullet also satisfied that check,
        so it cannot detect a regression back to the old wording. This test
        asserts the `source` bullet itself states the VALUE-SHAPE rule
        (the document's own repo-relative path), not mere non-emptiness,
        while `doc_type` remains described as presence/non-emptiness
        (026-DL R3).
        """
        quality_idx = self.template_text.index(_QUALITY_CRITERIA_MARKER)
        quality_section = self.template_text[quality_idx:]
        bullet_lines = [
            line
            for line in quality_section.splitlines()
            if line.strip().startswith("*") and "`source`" in line
        ]
        self.assertEqual(
            len(bullet_lines),
            1,
            "expected exactly one Quality Criteria bullet mentioning `source`",
        )
        bullet = bullet_lines[0]

        self.assertNotIn(
            "`source` and `doc_type` are present and non-empty",
            bullet,
            "Quality Criteria bullet regressed to the old, weaker "
            "non-emptiness-only wording",
        )
        self.assertIn(
            "repo-relative path",
            bullet,
            "Quality Criteria bullet must state the source value-shape rule",
        )
        self.assertIn("`doc_type`", bullet)
        self.assertIn("present and non-empty", bullet)


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
