"""Structural tests for 194-F C6a (194.010-T): P-013.5 policy text and the
Orchestrator invocation directive carry ``context_tier`` with a
``ROUTING_DEGRADED: context_tier`` fallback.

Plan: docs/plans/2026-09-27-context-tier-model-routing-plan.md (### C6a and
"Pre-Claim Drift Amendments (2026-10-04)").
"""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST = _ROOT / ".autoharness" / "harness-manifest.yaml"
_POLICY_TEMPLATE = "templates/policies/workflow-policies.md.tmpl"
_POLICY_MIRROR = ".github/policies/workflow-policies.md"
_ORCH_TEMPLATE = "templates/agents/_orchestrator.agent.md.tmpl"
_ORCH_MIRROR = ".github/agents/_orchestrator.agent.md"
_P0135_HEADING = "### P-013.5 — Invocation-Time Model-Routing Enforcement"
_DEGRADED = "ROUTING_DEGRADED: context_tier"
# Core Rule 3 / INV-C7: the context_tier policy text names no vendor, model
# or token count.
_FORBIDDEN_VENDOR_TERMS = ("anthropic", "openai", "claude", "gpt", "gemini", "grok", "token")


def _read(rel: str) -> str:
    return (_ROOT / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


def _section(text: str, heading: str) -> str:
    """Body under ``heading`` up to the next heading of the same or higher level."""
    lines = text.split("\n")
    level = len(heading) - len(heading.lstrip("#"))
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start:]:
        match = re.match(r"^(#{1,6}) ", line)
        if match and len(match.group(1)) <= level:
            break
        body.append(line)
    return "\n".join(body)


def _heading_window(text: str, heading_prefix: str) -> str:
    """Body from the heading starting with ``heading_prefix`` to the next ^#{2,4} heading."""
    match = re.search(rf"^{re.escape(heading_prefix)}.*$", text, flags=re.MULTILINE)
    if match is None:
        return ""
    rest = text[match.end():]
    nxt = re.search(r"^#{2,4} ", rest, flags=re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def _context_tier_paragraph(section: str) -> str:
    for paragraph in section.split("\n\n"):
        if paragraph.strip().startswith("**Context tier**"):
            return paragraph.strip()
    return ""


def _staged_blob_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class P0135ContextTierPolicyTests(unittest.TestCase):
    """P-013.5 carries the context_tier directive in template and mirror."""

    def setUp(self) -> None:
        self.texts = {rel: _read(rel) for rel in (_POLICY_TEMPLATE, _POLICY_MIRROR)}

    def test_context_tier_paragraph_wording(self) -> None:
        for rel, text in self.texts.items():
            with self.subTest(path=rel):
                paragraph = _context_tier_paragraph(_section(text, _P0135_HEADING))
                self.assertTrue(paragraph, "P-013.5 **Context tier** paragraph is missing")
                flat = re.sub(r"\s+", " ", paragraph)
                for token in (
                    "`context_tier`",
                    _DEGRADED,
                    "default context",
                    "without halting",
                    "`tier-routed`",
                    "`plugin-global`",
                    "operator-selected session model",
                    "`default`",
                    "`long_context`",
                    "Core Rule 3",
                ):
                    self.assertIn(token, flat)
                lowered = flat.lower()
                for term in _FORBIDDEN_VENDOR_TERMS:
                    self.assertNotIn(term, lowered)

    def test_declare_sentence_includes_context_tier(self) -> None:
        for rel, text in self.texts.items():
            with self.subTest(path=rel):
                section = _section(text, _P0135_HEADING)
                declare = next(
                    (p for p in section.split("\n\n") if p.strip().startswith("**Declare**")), ""
                )
                self.assertIn("`context_tier`", declare)

    def test_section_has_no_placeholders(self) -> None:
        """Only the intentional `{{...}}` prose meta-token (EXEMPT_POLICY_PROSE_META_TOKEN) may appear."""
        for rel, text in self.texts.items():
            with self.subTest(path=rel):
                tokens = set(re.findall(r"\{\{[^}]*\}\}", _section(text, _P0135_HEADING)))
                self.assertLessEqual(tokens, {"{{...}}"})

    def test_version_history_row_1_30_0(self) -> None:
        template_row = re.search(r"^\| 1\.30\.0 +\| ([^|]+)\|", self.texts[_POLICY_TEMPLATE], re.M)
        mirror_row = re.search(r"^\| 1\.30\.0 +\| ([^|]+)\|", self.texts[_POLICY_MIRROR], re.M)
        self.assertIsNotNone(template_row)
        self.assertIsNotNone(mirror_row)
        self.assertEqual(template_row.group(1).strip(), "{{DATE}}")
        self.assertRegex(mirror_row.group(1).strip(), r"^\d{4}-\d{2}-\d{2}$")
        for rel in self.texts:
            with self.subTest(path=rel):
                row = re.search(r"^\| 1\.30\.0 .*$", self.texts[rel], re.M).group(0)
                self.assertIn("P-013.5", row)
                self.assertIn("context_tier", row)


class OrchestratorContextTierDirectiveTests(unittest.TestCase):
    """Both Orchestrator invocation sites carry context_tier and its fallback."""

    def setUp(self) -> None:
        self.texts = {rel: _read(rel) for rel in (_ORCH_TEMPLATE, _ORCH_MIRROR)}

    def test_stage_and_ship_steps_carry_context_tier_and_fallback(self) -> None:
        for rel, text in self.texts.items():
            for prefix in ("### Step 1: Route to Stage", "### Step 2: Route to Ship"):
                with self.subTest(path=rel, step=prefix):
                    window = _heading_window(text, prefix)
                    self.assertTrue(window.strip())
                    self.assertIn("`context_tier`", window)
                    self.assertIn(_DEGRADED, window)
                    self.assertIn("default context", window)

    def test_model_routing_summary_carries_context_tier_and_plugin_exclusion(self) -> None:
        for rel, text in self.texts.items():
            with self.subTest(path=rel):
                section = re.sub(r"\s+", " ", _section(text, "## Model Routing"))
                self.assertIn(_DEGRADED, section)
                self.assertIn("`plugin-global`", section)
                self.assertIn("operator-selected session model", section)

    def test_ship_resolve_delimiter_preserved(self) -> None:
        """tests/test_pipeline_topology_gate_agent_wiring.py extracts up to this marker."""
        for rel, text in self.texts.items():
            with self.subTest(path=rel):
                self.assertIn("3. **Resolve Ship's routed model", text)

    def test_mirror_manifest_checksums_match_staged_blob(self) -> None:
        manifest = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
        by_path = {item.get("path"): item for item in manifest.get("artifacts") or []}
        for rel in (_ORCH_MIRROR, _POLICY_MIRROR):
            with self.subTest(path=rel):
                self.assertIn(rel, by_path)
                self.assertEqual(by_path[rel].get("checksum"), _staged_blob_sha256(_ROOT / rel))


if __name__ == "__main__":
    unittest.main()
