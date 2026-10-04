"""Structural tests for the C8 tune guidance (200-S / 194.013-T).

The tune-harness skill states the explicit-Ship-route exemption and the
never-auto-apply rule for the opt-in "new generic Ship default available"
proposal, outside Step 1.5c; the tuning guide documents ``context_tier`` in a
new ``##`` section that leaves the C5a-owned frontmatter contract section alone.
Plan: docs/plans/2026-09-27-context-tier-model-routing-plan.md (### C8 and
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
_TUNE = ".github/skills/tune-harness/SKILL.md"
_GUIDE = "docs/tuning-guide.md"

_STEP_15C = "#### Step 1.5c: Frontmatter Conformity Migration"
_STEP_15D = "#### Step 1.5d: Ship Route Default Proposal"
_STEP_16 = "#### Step 1.6:"
_STEP_22 = "#### Step 2.2: Generate Change Proposals"
_CONTRACT = "## Agent and Skill Frontmatter Contract"
_ROUTING = "## Model Routing and Context Tier"
_MANUAL = "## Manual Tuning"
_PROPOSAL = "new generic Ship default available"


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


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class TuneSkillShipDefaultProposalTests(unittest.TestCase):
    """C8: explicit-Ship-route exemption and never-auto-apply, outside Step 1.5c."""

    def setUp(self) -> None:
        self.text = _read(_TUNE)
        self.section = _section(self.text, _STEP_15D)
        self.flat = _flat(self.section)

    def test_section_exists(self) -> None:
        self.assertTrue(self.section.strip(), "Step 1.5d section is missing or empty")

    def test_section_sits_between_step_15c_and_step_16(self) -> None:
        pos_c = self.text.index(_STEP_15C)
        pos_d = self.text.index(_STEP_15D)
        pos_6 = self.text.index(_STEP_16)
        self.assertLess(pos_c, pos_d)
        self.assertLess(pos_d, pos_6)

    def test_step_15c_does_not_carry_the_ship_default_rule(self) -> None:
        step15c = _flat(_section(self.text, _STEP_15C))
        self.assertNotIn(_PROPOSAL, step15c)
        self.assertNotIn("model_routing.ship", step15c)

    def test_proposal_is_informational_and_opt_in(self) -> None:
        self.assertIn(_PROPOSAL, self.flat)
        self.assertIn("informational", self.flat)
        self.assertIn("opt-in", self.flat)

    def test_proposal_only_when_no_non_empty_ship_model_family(self) -> None:
        self.assertRegex(
            self.flat,
            r"only\*?\*? when `model_routing\.ship` declares no non-empty `model_family`",
        )

    def test_explicit_ship_route_is_an_operator_override_never_replaced(self) -> None:
        self.assertIn("operator override", self.flat)
        self.assertRegex(self.flat, r"never proposes replacing it")

    def test_every_non_empty_value_is_an_override_after_write_back(self) -> None:
        self.assertIn("{{SHIP_FAMILY}}", self.flat)
        self.assertIn("write-back", self.flat)
        self.assertRegex(self.flat, r"every non-empty (`model_family` )?value as an operator override")

    def test_never_auto_applies(self) -> None:
        self.assertRegex(self.flat, r"[Nn]ever auto-appl")
        self.assertIn("`auto_apply`", self.flat)

    def test_exemption_is_generic_not_dogfood_specific(self) -> None:
        # Review-fix batch B5: the installed skill ships to every workspace, so
        # the exemption is stated generically (any non-empty Ship family) and
        # never names the autoharness repository's own pinned route.
        self.assertNotIn("this repository", self.flat)
        self.assertIn("`model_routing.ship.model_family` is a non-empty string", self.flat)

    def test_step_0b2_classifies_route_variable_stale(self) -> None:
        # Review-fix batch B5: Step 0b.2 classifies the verify ROUTE_VARIABLE_STALE warning.
        flat = _flat(_section(self.text, "#### Step 0b.2: Schema-Contract Scan"))
        self.assertIn("`kind: route-variable-stale`", flat)
        self.assertIn("ROUTE_VARIABLE_STALE:<VAR>", flat)
        self.assertIn("non-fatal", flat)
        self.assertIn("variables_used", flat)
        self.assertRegex(flat, r"re-install")

    def test_step_22_maps_the_proposal_source(self) -> None:
        step22 = _flat(_section(self.text, _STEP_22))
        self.assertIn("source: ship-route-default", step22)
        self.assertIn("Step 1.5d", step22)
        # B5 tokens stay intact.
        self.assertIn("contract: frontmatter-conformity", step22)
        self.assertIn("Step 1.5c", step22)
        self.assertIn("source: frontmatter-conformity", step22)

    def test_manifest_checksum_matches_staged_blob(self) -> None:
        manifest = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
        entry = next(a for a in manifest["artifacts"] if a["path"] == _TUNE)
        blob = (_ROOT / _TUNE).read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(entry["checksum"], hashlib.sha256(blob).hexdigest())


class TuningGuideContextTierTests(unittest.TestCase):
    """C8: the tuning guide documents ``context_tier`` in its own ``##`` section."""

    def setUp(self) -> None:
        self.text = _read(_GUIDE)
        self.section = _section(self.text, _ROUTING)
        self.flat = _flat(self.section)

    def test_section_exists_between_contract_and_manual_tuning(self) -> None:
        self.assertTrue(self.section.strip(), "Model Routing and Context Tier section is missing")
        pos_contract = self.text.index(_CONTRACT)
        pos_routing = self.text.index(_ROUTING)
        pos_manual = self.text.index(_MANUAL)
        self.assertLess(pos_contract, pos_routing)
        self.assertLess(pos_routing, pos_manual)

    def test_contract_section_does_not_absorb_the_routing_docs(self) -> None:
        contract = _section(self.text, _CONTRACT)
        self.assertNotIn(_PROPOSAL, contract)
        self.assertNotIn("ROUTING_DEGRADED", contract)

    def test_cross_references_the_contract_tables(self) -> None:
        self.assertIn("Agent and Skill Frontmatter Contract", self.flat)

    def test_documents_values_and_fallback(self) -> None:
        for token in ("`context_tier`", "`default`", "`long_context`", '`""`'):
            self.assertIn(token, self.flat)
        self.assertIn("falls back", self.flat)
        self.assertIn("`tier2`", self.flat)
        self.assertIn("`tier3`", self.flat)

    def test_documents_raw_vs_resolved_escalation_variables(self) -> None:
        for token in (
            "`{{ESCALATION_CONTEXT_TIER}}`",
            "`{{LEGACY_ESCALATION_CONTEXT_TIER}}`",
            "`{{STAGE_ESCALATION_CONTEXT_TIER}}`",
            "`{{SHIP_ESCALATION_CONTEXT_TIER}}`",
        ):
            self.assertIn(token, self.flat)
        self.assertIn("raw", self.flat)
        self.assertIn("resolved", self.flat)

    def test_documents_fresh_install_seed_trigger(self) -> None:
        self.assertIn("fresh-install Ship seed", self.flat)
        self.assertIn("first install", self.flat)
        self.assertIn("no `model_routing.ship` key", self.flat)

    def test_documents_routing_degraded(self) -> None:
        self.assertIn("ROUTING_DEGRADED: context_tier", self.flat)
        self.assertIn("without halting", self.flat)

    def test_documents_plugin_agent_exclusion(self) -> None:
        self.assertIn("plugin-global", self.flat)

    def test_documents_same_route_guard_exclusion(self) -> None:
        self.assertIn("same-route guard", self.flat)

    def test_documents_ship_default_posture(self) -> None:
        self.assertIn(_PROPOSAL, self.flat)
        self.assertIn("operator override", self.flat)
        self.assertRegex(self.flat, r"[Nn]ever auto-appl")
        self.assertIn("edit `model_routing.ship`", self.flat)

    def test_documents_verification_and_migration(self) -> None:
        # Review-fix batch B2/B5.
        self.assertIn("`ROUTE_VARIABLE_STALE:<VAR>`", self.flat)
        self.assertIn("non-fatal", self.flat)
        self.assertIn("`variables_used`", self.flat)
        self.assertIn("`config.overrides`, then config, then the manifest", self.flat)
        self.assertIn('requires `schema_version: "1.1.0"`', self.flat)
        self.assertIn("plain-string `orchestrator` form", self.flat)
        self.assertIn("rendered before this release fails that check", self.flat)


class GettingStartedRoleRouteTests(unittest.TestCase):
    """Review-fix batch B3: the getting-started role-route row covers the seed and context tiers."""

    def test_role_route_row(self) -> None:
        text = _read("docs/getting-started.md")
        row = next(line for line in text.split("\n") if line.startswith("| `model_routing.stage` / `.ship` |"))
        for token in ("fresh-install Ship seed", "no `model_routing.ship` key", "install-harness Step 1.2",
                      "`STAGE_CONTEXT_TIER`", "`SHIP_CONTEXT_TIER`", '`schema_version: "1.1.0"`'):
            self.assertIn(token, row)
        self.assertIn('schema_version: "1.1.0"\npreset: standard', text)


if __name__ == "__main__":
    unittest.main()
