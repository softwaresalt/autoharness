"""Structural + parity tests for the capability-pack usage-enforcement coordinator.

The coordinator instruction (template + dogfood mirror) is a thin cross-pack
routing overlay. These tests lock the stable markers the verifier
(``_check_capability_pack_enforcement``) and tune drift check depend on:

* a route block delimited by ``<!-- BEGIN:capability-pack-routes -->`` /
  ``<!-- END:capability-pack-routes -->`` containing one ``<!-- route:{id} -->``
  row per enabled retrieval-enforced pack,
* a deferral block delimited by ``<!-- BEGIN:capability-pack-deferral -->`` /
  ``<!-- END:capability-pack-deferral -->`` containing one ``<!-- defer:{id} -->``
  bullet per enabled retrieval-enforced pack (kept in sync with the route rows so
  a single-pack install never points at an uninstalled pack instruction), and
* four safeguard-invariant markers.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = (
    _REPO_ROOT
    / "templates"
    / "instructions"
    / "capability-pack-enforcement.instructions.md.tmpl"
)
_DOGFOOD = (
    _REPO_ROOT
    / ".github"
    / "instructions"
    / "capability-pack-enforcement.instructions.md"
)

_ROUTE_BEGIN = "<!-- BEGIN:capability-pack-routes -->"
_ROUTE_END = "<!-- END:capability-pack-routes -->"
_DEFER_BEGIN = "<!-- BEGIN:capability-pack-deferral -->"
_DEFER_END = "<!-- END:capability-pack-deferral -->"
_SAFEGUARD_MARKERS = (
    "<!-- safeguard:pack-deferral -->",
    "<!-- safeguard:direct-search-exemptions -->",
    "<!-- safeguard:per-phase-health-reuse -->",
    "<!-- safeguard:internal-no-public-web -->",
)
# Retrieval-enforced packs: the template ships the full set; the dogfood enables
# both, so both files carry both route rows.
_RETRIEVAL_PACKS = ("agent-engram", "graphtor-docs")


def _route_pack_ids(text: str) -> set[str]:
    block = text.split(_ROUTE_BEGIN, 1)[1].split(_ROUTE_END, 1)[0]
    return set(re.findall(r"<!-- route:([a-z0-9-]+) -->", block))


def _defer_pack_ids(text: str) -> set[str]:
    block = text.split(_DEFER_BEGIN, 1)[1].split(_DEFER_END, 1)[0]
    return set(re.findall(r"<!-- defer:([a-z0-9-]+) -->", block))


class CapabilityPackEnforcementInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = _TEMPLATE.read_text(encoding="utf-8")
        cls.dogfood = _DOGFOOD.read_text(encoding="utf-8")

    def test_files_exist(self) -> None:
        self.assertTrue(_TEMPLATE.is_file(), f"missing template: {_TEMPLATE}")
        self.assertTrue(_DOGFOOD.is_file(), f"missing dogfood mirror: {_DOGFOOD}")

    def test_frontmatter_applyto_glob(self) -> None:
        for text in (self.template, self.dogfood):
            self.assertTrue(text.lstrip().startswith("---"), "missing frontmatter")
            front = text.split("---", 2)[1]
            self.assertRegex(front, r"applyTo:\s*'\*\*'")

    def test_route_block_present_with_full_set(self) -> None:
        for text in (self.template, self.dogfood):
            self.assertIn(_ROUTE_BEGIN, text)
            self.assertIn(_ROUTE_END, text)
            self.assertEqual(_route_pack_ids(text), set(_RETRIEVAL_PACKS))

    def test_deferral_block_present_with_full_set(self) -> None:
        for text in (self.template, self.dogfood):
            self.assertIn(_DEFER_BEGIN, text)
            self.assertIn(_DEFER_END, text)
            self.assertEqual(_defer_pack_ids(text), set(_RETRIEVAL_PACKS))

    def test_deferral_set_matches_route_set(self) -> None:
        # The installer renders both blocks to the same enabled set; the two
        # marker sets must stay in sync so a pruned single-pack install never
        # defers to an uninstalled pack instruction file.
        for text in (self.template, self.dogfood):
            self.assertEqual(_defer_pack_ids(text), _route_pack_ids(text))

    def test_all_safeguard_markers_present(self) -> None:
        for text in (self.template, self.dogfood):
            for marker in _SAFEGUARD_MARKERS:
                self.assertIn(marker, text, f"missing safeguard marker {marker}")

    def test_dogfood_has_no_unresolved_placeholders(self) -> None:
        leftover = re.findall(r"\{\{[^}]+\}\}", self.dogfood)
        self.assertFalse(leftover, f"unresolved placeholders: {leftover}")

    def test_template_and_dogfood_are_parity_drift_free(self) -> None:
        # No {{VARIABLE}} customization points and the dogfood enables the full
        # retrieval-enforced set, so the mirror is byte-identical to the template
        # (EOL-normalized).
        self.assertEqual(
            self.template.replace("\r\n", "\n"),
            self.dogfood.replace("\r\n", "\n"),
        )

    def test_defers_to_pack_instructions(self) -> None:
        for text in (self.template, self.dogfood):
            self.assertIn("agent-engram.instructions.md", text)
            self.assertIn("graphtor-docs.instructions.md", text)


if __name__ == "__main__":
    unittest.main()
