"""Route drift and catalog proposal guidance in the tune-harness skill (208-F B9).

The global, non-rendered tune-harness skill validates the loaded config by the
document's own ``schema_version`` (Step 0b.1), reads ``subagent_route_drift`` and
proposes ``refresh-route-frontmatter`` updates (proposal only), proposes catalog
extraction and the 1.1.0 to 1.2.0 bump (Step 1.5e), and keeps the explicit-Ship
route preservation rule. The end-of-shipment sweep asserts that none of the three
global skills that validate an operator config names the root schema file as the
sole validation target (invariant I11).
Plan: docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md (### B9).
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
_INSTALL = ".github/skills/install-harness/SKILL.md"
_DISCOVERY = ".github/skills/workspace-discovery/SKILL.md"

_STEP_01 = "#### Step 0b.1: Config Schema Validation"
_STEP_02 = "#### Step 0b.2: Schema-Contract Scan"
_STEP_15D = "#### Step 1.5d: Ship Route Default Proposal"
_STEP_15E = "#### Step 1.5e: Model Routing Route Drift and Catalog Proposals"
_STEP_16 = "#### Step 1.6:"
_STEP_22 = "#### Step 2.2: Generate Change Proposals"


def _read(rel: str) -> str:
    return (_ROOT / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


def _section(text: str, heading: str) -> str:
    lines = text.split("\n")
    level = len(heading) - len(heading.lstrip("#"))
    start = next((i + 1 for i, line in enumerate(lines) if line.strip() == heading), None)
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start:]:
        match = re.match(r"^(#{1,6}) ", line)
        if match and len(match.group(1)) <= level:
            break
        body.append(line)
    return "\n".join(body)


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class TuneConfigValidationStepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _read(_TUNE)
        self.section = _section(self.text, _STEP_01)
        self.intro = self.section.split("\n| Discrepancy")[0]
        self.flat = _flat(self.intro)

    def test_validation_selects_the_schema_by_the_documents_own_version(self) -> None:
        for token in (
            "schema_version",
            "schemas/harness-config/<schema_version>.schema.json",
            "resolve_contract_schema_path",
            "contract finding",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.flat)

    def test_root_schema_is_no_longer_the_sole_target(self) -> None:
        self.assertRegex(self.flat, r"(?i)root .*tracks only the current version")
        self.assertNotRegex(
            self.intro.strip(),
            r"^Validate the loaded config against `\{autoharness_home\}/schemas/harness-config\.schema\.json`\.",
        )

    def test_discrepancy_table_is_preserved(self) -> None:
        for token in ("| Unknown top-level key | Warning |", "| Missing required key | Error |", "Config-key migration"):
            self.assertIn(token, self.section)

    def test_step_adds_no_placeholder(self) -> None:
        self.assertNotIn("{{", self.intro)


class TuneRouteStepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _read(_TUNE)
        self.section = _section(self.text, _STEP_15E)
        self.flat = _flat(self.section)

    def test_step_marker_exists_between_step_15d_and_step_16(self) -> None:
        self.assertTrue(self.section.strip(), "Step 1.5e section is missing or empty")
        self.assertLess(self.text.index(_STEP_15D), self.text.index(_STEP_15E))
        self.assertLess(self.text.index(_STEP_15E), self.text.index(_STEP_16))

    def test_four_labeled_parts_exist(self) -> None:
        for label in (
            "**(a) Config validation.**",
            "**(b) Route-frontmatter drift.**",
            "**(c) Catalog extraction.**",
            "**(d) Schema version bump.**",
        ):
            with self.subTest(label=label):
                self.assertIn(label, self.section)

    def test_drift_is_read_from_subagent_route_drift_and_proposes_refresh(self) -> None:
        for token in (
            "`subagent_route_drift`",
            "`refresh-route-frontmatter`",
            "per drifted agent",
            "`drifted`",
            "`drift`",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.flat)

    def test_proposals_are_proposal_only_and_never_auto_applied(self) -> None:
        self.assertRegex(self.flat, r"proposal only")
        self.assertRegex(self.flat, r"never auto-appl")
        self.assertIn("`auto_apply`", self.flat)

    def test_workspace_authored_agents_are_advisory(self) -> None:
        self.assertRegex(self.flat, r"[Ww]orkspace-authored agents? (is|are) advisory")

    def test_unrenderable_site_gets_no_refresh_proposal(self) -> None:
        for token in ("ROUTING_BINDING_UNRESOLVED_SITE", "ROUTING_SITE_DEFAULT_UNRESOLVED"):
            with self.subTest(token=token):
                self.assertIn(token, self.flat)
        self.assertRegex(self.flat, r"gets no `refresh-route-frontmatter` proposal")
        self.assertIn("nothing can render it", self.flat)
        self.assertIn("repair the template's tier placeholder", self.flat)
        self.assertIn("remove the binding", self.flat)

    def test_catalog_extraction_needs_three_identical_blocks(self) -> None:
        self.assertRegex(self.flat, r"three or more [^.]*field-identical")
        self.assertIn("`model_routing.routes`", self.flat)
        self.assertIn("`model_routing.bindings`", self.flat)

    def test_schema_bump_proposal_names_both_versions(self) -> None:
        self.assertRegex(self.flat, r"`1\.1\.0` to `1\.2\.0`")
        self.assertIn("`schema_version`", self.flat)
        self.assertIn("upgrade-config-contract-1.1.0-to-1.2.0", self.flat)

    def test_ship_route_preservation_rule_is_preserved(self) -> None:
        self.assertIn("Step 1.5d", self.flat)
        self.assertRegex(self.flat, r"explicitly declared Ship route")
        self.assertRegex(self.flat, r"never (edits|proposes changes to) `model_routing\.ship`")

    def test_step_reads_config_at_runtime_without_placeholders(self) -> None:
        self.assertNotIn("{{", self.section)
        self.assertIn("at runtime", self.flat)

    def test_pinned_ship_default_step_is_untouched(self) -> None:
        step15d = _flat(_section(self.text, _STEP_15D))
        self.assertIn("new generic Ship default available", step15d)
        self.assertNotIn("subagent_route_drift", step15d)

    def test_step_22_maps_the_new_proposal_sources(self) -> None:
        step22 = _flat(_section(self.text, _STEP_22))
        self.assertIn("Step 1.5e", step22)
        self.assertIn("source: route-drift", step22)
        self.assertIn("source: route-catalog", step22)
        # Earlier source tokens stay intact.
        for token in ("source: ship-route-default", "source: frontmatter-conformity", "source: schema-contract"):
            self.assertIn(token, step22)

    def test_manifest_checksum_matches_committed_skill(self) -> None:
        manifest = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
        entry = next(a for a in manifest["artifacts"] if a["path"] == _TUNE)
        blob = (_ROOT / _TUNE).read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(entry["checksum"], hashlib.sha256(blob).hexdigest())


def _discovery_instruction() -> str:
    match = re.search(r"(?ms)^1\. (.*?)^2\. Extract operator preferences", _read(_DISCOVERY))
    if match is None:
        raise AssertionError("workspace-discovery Phase 0 item 1 not found")
    return match.group(1)


def _install_instruction() -> str:
    match = re.search(r"(?ms)^1\. (.*?)^2\. Extract operator preferences for:", _read(_INSTALL))
    if match is None:
        raise AssertionError("install-harness Step 1.0b item 1 not found")
    return match.group(1)


def _tune_instruction() -> str:
    return _section(_read(_TUNE), _STEP_01).split("\n| Discrepancy")[0]


class EndOfShipmentValidationSweepTests(unittest.TestCase):
    """Closes invariant I11: no global skill validates an operator config against the root schema alone."""

    _INSTRUCTIONS = {
        "workspace-discovery": _discovery_instruction,
        "install-harness": _install_instruction,
        "tune-harness": _tune_instruction,
    }

    def test_each_instruction_selects_the_schema_by_the_documents_own_version(self) -> None:
        for name, getter in self._INSTRUCTIONS.items():
            with self.subTest(skill=name):
                text = _flat(getter())
                self.assertIn("schema_version", text)
                self.assertIn("schemas/harness-config/<schema_version>.schema.json", text)
                self.assertIn("resolve_contract_schema_path", text)

    def test_none_names_the_root_schema_as_the_sole_validation_target(self) -> None:
        for name, getter in self._INSTRUCTIONS.items():
            instruction = getter()
            with self.subTest(skill=name):
                self.assertIn("tracks only the current version", _flat(instruction))
                for line in instruction.split("\n"):
                    if "schemas/harness-config.schema.json" in line:
                        self.assertIn("tracks only the current version", line)
                        self.assertRegex(line, r"not the validation target")

    def test_whole_skill_files_carry_no_root_only_validation_sentence(self) -> None:
        for rel in (_DISCOVERY, _INSTALL, _TUNE):
            with self.subTest(skill=rel):
                for line in _read(rel).split("\n"):
                    if "harness-config.schema.json" in line:
                        self.assertIn("tracks only the current version", line)


if __name__ == "__main__":
    unittest.main()
