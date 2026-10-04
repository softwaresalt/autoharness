"""194.004-T (C3b) -- fresh-install Ship seed contract (H-C3, AS-F2/AS-F3/AS-F9, AN-F2).

Structural pins on `.github/skills/install-harness/SKILL.md`:

* the first-install snapshot is recorded before Step 1.2 and Step 3.3 and is
  never re-probed;
* the seed trigger (first install, no `model_routing.ship` key, no `SHIP_*`
  key in `config.overrides`);
* the placement (inside Step 1.2, before any `{{SHIP_*}}` derivation row);
* exactly the four seed values.

The seed values live in the installer skill only (Core Rule 3, INV-C3): no
template and no Python derivation carries the seed family literal. Derivation
pins confirm what the Step 3.4 write-back produces resolves as seeded, and that
an explicitly present but empty `ship` block still falls back to tier2.
"""

from __future__ import annotations

import hashlib
import re
import unittest
import unittest.mock as _mock
from pathlib import Path
from typing import Any

import yaml

from autoharness.verify_workspace import (
    _derive_role_route_variables,
    _derive_template_variables,
    _render_template,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SKILL_RELATIVE = ".github/skills/install-harness/SKILL.md"
_SKILL = _REPO_ROOT / _SKILL_RELATIVE
_CONFIG_TEMPLATE = _REPO_ROOT / "templates/harness-config.yaml.tmpl"

_SEED_FAMILY = "gpt-6-luna"
_EXPECTED_SEED = {
    "model_provider": "openai",
    "model_family": _SEED_FAMILY,
    "reasoning_effort": "xhigh",
    "context_tier": "long_context",
}
_SHIP_OVERRIDE_KEYS = ("SHIP_FAMILY", "SHIP_PROVIDER", "SHIP_REASONING_EFFORT", "SHIP_CONTEXT_TIER")
_SNAPSHOT_EXPRESSION = "first_install = not exists(.autoharness/harness-manifest.yaml)"
_SEED_HEADING = "**Fresh-install Ship seed"


def _skill_text() -> str:
    return _SKILL.read_text(encoding="utf-8")


def _heading_index(text: str, heading: str) -> int:
    match = re.search(rf"^#### {re.escape(heading)}.*$", text, flags=re.MULTILINE)
    if match is None:
        raise AssertionError(f"install-harness SKILL.md has no `#### {heading}` heading")
    return match.start()


def _section(text: str, heading: str) -> str:
    start = _heading_index(text, heading)
    body_start = text.index("\n", start) + 1
    following = re.search(r"^#{2,4} ", text[body_start:], flags=re.MULTILINE)
    end = body_start + following.start() if following else len(text)
    return text[start:end]


def _seed_block(text: str) -> str:
    """The seed rule paragraph(s): from the seed heading to the variable table."""
    step_1_2 = _section(text, "Step 1.2:")
    start = step_1_2.find(_SEED_HEADING)
    if start < 0:
        raise AssertionError("Step 1.2 does not state the fresh-install Ship seed rule")
    end = step_1_2.find("| Template Variable |", start)
    if end < 0:
        raise AssertionError("the seed rule is not followed by the Step 1.2 variable table")
    return step_1_2[start:end]


def _load_live_fixtures() -> tuple[dict, dict, dict, dict]:
    autoharness_dir = _REPO_ROOT / ".autoharness"

    def load(name: str) -> Any:
        return yaml.safe_load((autoharness_dir / name).read_text(encoding="utf-8"))

    return (
        load("harness-manifest.yaml"),
        load("config.yaml"),
        load("workspace-profile.yaml"),
        load("backlog-registry.yaml"),
    )


def _variables_for(model_routing: dict[str, Any]) -> dict[str, str]:
    manifest, config, profile, registry = _load_live_fixtures()
    config = dict(config)
    config["model_routing"] = model_routing
    with _mock.patch("autoharness.verify_workspace._resolve_default_branch", return_value="main"):
        return _derive_template_variables(_REPO_ROOT, manifest, config, profile, registry)


_TIERS = {
    "tier1": {"model": "gpt-5.4-mini", "model_family": "gpt-5.4-mini"},
    "tier2": {"model": "claude-sonnet-5", "model_family": "claude-sonnet-5", "model_provider": "anthropic", "reasoning_effort": "medium"},
    "tier3": {"model": "claude-opus-5", "model_family": "claude-opus-5"},
}


class FirstInstallSnapshotTests(unittest.TestCase):
    def test_snapshot_expression_is_stated_once(self) -> None:
        self.assertEqual(_skill_text().count(_SNAPSHOT_EXPRESSION), 1)

    def test_snapshot_is_recorded_before_step_1_2_and_step_3_3(self) -> None:
        text = _skill_text()
        position = text.index(_SNAPSHOT_EXPRESSION)
        self.assertLess(position, _heading_index(text, "Step 1.2:"))
        self.assertLess(position, _heading_index(text, "Step 3.3:"))
        self.assertIn(_SNAPSHOT_EXPRESSION, _section(text, "Step 1.0:"))

    def test_snapshot_is_never_re_probed(self) -> None:
        snapshot_section = _section(_skill_text(), "Step 1.0:")
        self.assertIn("never re-probe", snapshot_section)
        self.assertIn("Step 3.3", snapshot_section)


class SeedTriggerAndPlacementTests(unittest.TestCase):
    def test_seed_lives_in_step_1_2_before_every_ship_row(self) -> None:
        text = _skill_text()
        step_1_2 = _section(text, "Step 1.2:")
        seed_position = step_1_2.index(_SEED_HEADING)
        for name in _SHIP_OVERRIDE_KEYS:
            with self.subTest(variable=name):
                self.assertLess(seed_position, step_1_2.index(f"| `{{{{{name}}}}}` |"))

    def test_seed_states_it_runs_before_ship_derivation(self) -> None:
        block = _seed_block(_skill_text())
        self.assertIn("before", block)
        self.assertIn("`{{SHIP_*}}`", block)

    def test_trigger_requires_first_install_and_no_ship_key_and_no_ship_override(self) -> None:
        block = _seed_block(_skill_text())
        self.assertIn("`first_install`", block)
        self.assertIn("no `model_routing.ship` key", block)
        self.assertIn("`config.overrides`", block)
        for name in _SHIP_OVERRIDE_KEYS:
            with self.subTest(override=name):
                self.assertIn(f"`{name}`", block)

    def test_override_suppresses_and_explicit_ship_block_is_honored(self) -> None:
        block = _seed_block(_skill_text())
        self.assertIn("Step 1.0b item 7", block)
        self.assertIn("suppresses the seed", block)
        self.assertIn("even when all its fields are empty", block)
        self.assertIn("no seed value is mixed in", block)

    def test_seed_declares_exactly_the_four_values(self) -> None:
        block = _seed_block(_skill_text())
        fences = re.findall(r"```yaml\n(.*?)```", block, flags=re.DOTALL)
        self.assertEqual(len(fences), 1, "the seed rule must carry exactly one yaml seed block")
        parsed = yaml.safe_load(fences[0])
        self.assertEqual(parsed, {"model_routing": {"ship": _EXPECTED_SEED}})

    def test_seed_family_literal_appears_only_in_the_seed_block(self) -> None:
        text = _skill_text()
        self.assertEqual(text.count(_SEED_FAMILY), _seed_block(text).count(_SEED_FAMILY))

    def test_write_back_materializes_and_summary_reports_the_seed(self) -> None:
        text = _skill_text()
        self.assertIn("never re-applied", _seed_block(text))
        self.assertIn("fresh-install Ship seed", _section(text, "Step 3.4:"))
        self.assertIn("Ship route seed:", _section(text, "Step 4.6:"))


class SeedLiteralDisciplineTests(unittest.TestCase):
    def test_no_template_contains_the_seed_family_literal(self) -> None:
        offenders = [
            str(path.relative_to(_REPO_ROOT))
            for path in sorted((_REPO_ROOT / "templates").rglob("*.tmpl"))
            if _SEED_FAMILY in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])

    def test_python_derivation_has_no_seed_constant(self) -> None:
        offenders = [
            str(path.relative_to(_REPO_ROOT))
            for path in sorted((_REPO_ROOT / "src").rglob("*.py"))
            if _SEED_FAMILY in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])


class SeedDerivationTests(unittest.TestCase):
    def test_seeded_ship_block_derives_the_seed_route(self) -> None:
        variables = _variables_for({**_TIERS, "ship": dict(_EXPECTED_SEED)})
        self.assertEqual(variables["SHIP_FAMILY"], "gpt-6-luna")
        self.assertEqual(variables["SHIP_PROVIDER"], "openai")
        self.assertEqual(variables["SHIP_REASONING_EFFORT"], "xhigh")
        self.assertEqual(variables["SHIP_CONTEXT_TIER"], "long_context")

    def test_seeded_route_survives_the_step_3_4_write_back(self) -> None:
        """Write-back renders the seeded block explicitly, so a later install,
        verify, or tune reads the same Ship route without re-seeding."""
        variables = _variables_for({**_TIERS, "ship": dict(_EXPECTED_SEED)})
        rendered = yaml.safe_load(_render_template(_CONFIG_TEMPLATE.read_text(encoding="utf-8"), variables))
        ship = rendered["model_routing"]["ship"]
        for key, value in _EXPECTED_SEED.items():
            with self.subTest(key=key):
                self.assertEqual(ship[key], value)
        rederived = _derive_role_route_variables(rendered["model_routing"])
        self.assertEqual(rederived["SHIP_FAMILY"], "gpt-6-luna")
        self.assertEqual(rederived["SHIP_CONTEXT_TIER"], "long_context")

    def test_explicit_empty_ship_block_falls_back_to_tier2(self) -> None:
        empty_ship = {"model_family": "", "model_provider": "", "reasoning_effort": "", "context_tier": ""}
        variables = _derive_role_route_variables({**_TIERS, "ship": empty_ship})
        self.assertEqual(variables["SHIP_FAMILY"], "claude-sonnet-5")
        self.assertEqual(variables["SHIP_PROVIDER"], "anthropic")
        self.assertEqual(variables["SHIP_REASONING_EFFORT"], "medium")
        self.assertEqual(variables["SHIP_CONTEXT_TIER"], "default")
        self.assertNotIn(_SEED_FAMILY, variables.values())


class ManifestEntryTests(unittest.TestCase):
    def test_install_harness_manifest_entry_is_unchanged(self) -> None:
        manifest = yaml.safe_load((_REPO_ROOT / ".autoharness/harness-manifest.yaml").read_text(encoding="utf-8"))
        entries = [
            artifact for artifact in manifest["artifacts"]
            if isinstance(artifact, dict) and artifact.get("path") == _SKILL_RELATIVE
        ]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["checksum"], hashlib.sha256(_SKILL.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
