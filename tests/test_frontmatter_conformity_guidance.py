"""Structural tests for the frontmatter-conformity skill guidance (193-F B5).

The tune-harness skill gains Step 1.5c (frontmatter conformity migration) plus
its Step 2.2 mapping line; the verify-harness skill documents the
``frontmatter_conformity`` targeted check. Plan:
docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md (### B5).
"""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST = _ROOT / ".autoharness" / "harness-manifest.yaml"
_TUNE = ".github/skills/tune-harness/SKILL.md"
_VERIFY = ".github/skills/verify-harness/SKILL.md"

# The eight B2b action names (rules 1-8 of ``_fc_build_proposals``).
_ACTIONS = (
    "rerender",
    "reinstall-community",
    "source-repair",
    "manual-fix",
    "migrate-key",
    "remove-key",
    "add-key",
    "replace-value",
)

# Step 0b.2 preserved field set plus the B2b additions (AN-F1).
_STEP_0B2_FIELDS = (
    "contract",
    "from_version",
    "to_version",
    "status",
    "severity",
    "changed_fields",
    "action",
    "evidence",
)
_B2B_FIELDS = ("path", "code", "from_key", "to_keys", "value", "manual_review", "summary")


def _read(rel: str) -> str:
    return (_ROOT / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


def _section(text: str, heading: str) -> str:
    """Return the body under ``heading`` up to the next heading of the same or higher level."""
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


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _staged_blob_sha256(path: Path) -> str:
    """SHA-256 of the LF-normalized blob (IM-12 / CR-F1)."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class TuneHarnessStep15cTests(unittest.TestCase):
    """B5: tune-harness Step 1.5c and its Step 2.2 mapping."""

    def setUp(self) -> None:
        self.text = _read(_TUNE)
        self.section = _section(self.text, "#### Step 1.5c: Frontmatter Conformity Migration")
        self.flat = _normalized(self.section)

    def test_section_exists(self) -> None:
        self.assertTrue(self.section.strip(), "Step 1.5c section is missing or empty")

    def test_section_follows_step_15b_and_precedes_step_16(self) -> None:
        pos_b = self.text.index("#### Step 1.5b: Agent Identity Migration Detection")
        pos_c = self.text.index("#### Step 1.5c: Frontmatter Conformity Migration")
        pos_6 = self.text.index("#### Step 1.6:")
        self.assertLess(pos_b, pos_c)
        self.assertLess(pos_c, pos_6)

    def test_section_promotes_frontmatter_conformity_proposals(self) -> None:
        self.assertIn("contract: frontmatter-conformity", self.flat)

    def test_section_names_all_eight_actions(self) -> None:
        missing = [action for action in _ACTIONS if f"`{action}`" not in self.section]
        self.assertEqual(missing, [], f"Step 1.5c does not name actions: {missing}")

    def test_section_lists_complete_preserved_payload(self) -> None:
        missing = [
            field for field in (*_STEP_0B2_FIELDS, *_B2B_FIELDS) if f"`{field}`" not in self.section
        ]
        self.assertEqual(missing, [], f"Step 1.5c does not preserve payload fields: {missing}")

    def test_section_severity_mapping(self) -> None:
        self.assertIn("**Breaking**", self.section)
        self.assertIn("**Degrading**", self.section)
        self.assertIn("`nonconformant-managed`", self.section)

    def test_section_requires_operator_approval(self) -> None:
        self.assertIn("operator approval", self.flat)
        self.assertIn("INV-B1", self.flat)

    def test_section_never_invents_model_provider(self) -> None:
        self.assertIn("never invents `model_provider`", self.flat)

    def test_reinstall_community_refreshes_both_checksums(self) -> None:
        self.assertIn("`installed_checksum`", self.section)
        self.assertIn("`source_checksum`", self.section)
        self.assertRegex(self.flat, r"`reinstall-community`[^.]*refresh(es)? \*\*both\*\*")

    def test_skill_routing_keys_cite_p0135(self) -> None:
        self.assertIn("P-013.5", self.flat)
        self.assertIn("leaf-executor", self.flat)

    def test_null_value_requires_operator_supplied_value(self) -> None:
        self.assertRegex(self.flat, r"`null` `value`")

    def test_step_22_maps_frontmatter_conformity_proposals(self) -> None:
        step22 = _normalized(_section(self.text, "#### Step 2.2: Generate Change Proposals"))
        self.assertIn("contract: frontmatter-conformity", step22)
        self.assertIn("Step 1.5c", step22)
        self.assertIn("source: frontmatter-conformity", step22)


class VerifyHarnessCheckDocTests(unittest.TestCase):
    """B5: verify-harness documents the ``frontmatter_conformity`` targeted check."""

    def setUp(self) -> None:
        self.text = _read(_VERIFY)
        self.section = _section(self.text, "### Deterministic Check: `frontmatter_conformity`")
        self.flat = _normalized(self.section)

    def test_section_exists(self) -> None:
        self.assertTrue(self.section.strip(), "frontmatter_conformity check section is missing")

    def test_names_classes_and_profiles(self) -> None:
        for token in ("managed-rendered", "managed-source", "workspace-authored", "tier-routed", "plugin-global"):
            with self.subTest(token=token):
                self.assertIn(f"`{token}`", self.section)

    def test_fail_closed_regardless_of_checksum_and_unknown_key_informational(self) -> None:
        self.assertIn("regardless of checksum status", self.flat)
        self.assertIn("H-B3", self.flat)
        self.assertIn("`FM_UNKNOWN_KEY`", self.section)
        self.assertIn("informational", self.flat)


class GuidanceManifestChecksumTests(unittest.TestCase):
    """B5: both global skill definition checksums match their raw staged blobs."""

    def test_manifest_checksums_match_staged_blobs(self) -> None:
        manifest = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
        by_path = {item.get("path"): item for item in manifest.get("artifacts") or []}
        for rel in (_TUNE, _VERIFY):
            with self.subTest(path=rel):
                self.assertIn(rel, by_path)
                self.assertEqual(by_path[rel].get("template"), "global skill definition")
                self.assertEqual(by_path[rel].get("checksum"), _staged_blob_sha256(_ROOT / rel))


if __name__ == "__main__":
    unittest.main()
