"""Dark Factory Visibility Protocol lives in the workflow policy (209-F U5).

The protocol (the eight ``DARK_MODE_*``/handoff events and their required
content) is a P-017 contract of ``workflow-policies``: operator-visible
session-output summaries with no dependency on any optional capability pack.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from autoharness.verify_workspace import DARK_FACTORY_ASSERTIONS, verify_workspace

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"
_MIRROR = _REPO_ROOT / ".github" / "policies" / "workflow-policies.md"

_EXPECTED_TABLE = """\
| Event | Required broadcast content |
|---|---|
| `DARK_MODE_START` | resolved scope, merge-approval authority, admin-fallback authority, stop conditions, visibility mode |
| `DARK_MODE_SCOPE` | concrete stash IDs, feature/task IDs, shipment IDs, and any explicitly excluded items |
| `BRAINSTORM_HANDOFF_READY` | brainstorm/requirements artifact path, unresolved questions, and handoff target |
| `LOCAL_REVIEW_READY` | reviewed HEAD, readiness outcome, P0/P1 counts, follow-ups or residual-risk notes, shadow-review posture |
| `DARK_MODE_MERGE_AUTHORIZED` | PR number, reviewed HEAD, checks state, merge strategy, approval source, and scope match |
| `ADMIN_FALLBACK_ATTEMPTED` | after the fallback command/API returns: PR number, block classification, fallback authority, command/API used, and actual result |
| `DARK_MODE_HALTED` | halt reason, violated policy or stop condition, affected scope item, and required operator action |
| `DARK_MODE_COMPLETE` | shipped/closed shipments, decisions, gate outcomes, reviewed HEADs, merge/fallback outcome, closure status, and follow-up items |"""

_VISIBILITY_TOKENS = [
    "Dark Factory Visibility Protocol",
    "BRAINSTORM_HANDOFF_READY",
    "DARK_MODE_COMPLETE",
    "degraded-visibility",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _verify_policy_only_workspace(policy_text: str) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        home = root / "home"
        workspace = root / "workspace"
        (home / "schemas").mkdir(parents=True)
        (workspace / ".autoharness").mkdir(parents=True)
        (workspace / ".github" / "policies").mkdir(parents=True)
        schema = {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object"}
        for name in ("harness-manifest", "harness-config", "workspace-profile"):
            (home / "schemas" / f"{name}.schema.json").write_text(json.dumps(schema), encoding="utf-8")
        _write_yaml(
            workspace / ".autoharness" / "harness-manifest.yaml",
            {
                "schema_version": "1.0.0",
                "installed_at": "2026-04-24T00:00:00Z",
                "autoharness_version": "1.3.2",
                "profile_hash": "abc",
                "primitives_installed": [4, 8],
                "capability_packs": [],
                "artifacts": [
                    {
                        "path": ".github/prompts/feature-flow-dark.prompt.md",
                        "primitive": 4,
                        "template": "templates/prompts/feature-flow-dark.prompt.md.tmpl",
                        "checksum": "stale-checksum",
                    }
                ],
                "variables_used": {"PROJECT_NAME": "demo-workspace"},
            },
        )
        _write_yaml(workspace / ".autoharness" / "config.yaml", {"schema_version": "1.0.0"})
        _write_yaml(workspace / ".autoharness" / "workspace-profile.yaml", {"schema_version": "1.0.0"})
        (workspace / ".github" / "policies" / "workflow-policies.md").write_text(policy_text, encoding="utf-8")
        return verify_workspace(workspace, home, workspace / ".autoharness" / "staging")


class DarkFactoryVisibilityAssertionTests(unittest.TestCase):
    def test_assertion_targets_the_policy_mirror(self) -> None:
        entries = {entry["key"]: entry for entry in DARK_FACTORY_ASSERTIONS}
        entry = entries["dark_factory_visibility_contract"]
        self.assertEqual(entry["path"], ".github/policies/workflow-policies.md")
        self.assertEqual(entry["must_contain"], _VISIBILITY_TOKENS)
        self.assertTrue(entry.get("required"))
        self.assertNotIn("requires_pack", entry)

    def test_check_fails_on_policy_lacking_the_protocol(self) -> None:
        report = _verify_policy_only_workspace("P-017\nRun pipeline in dark mode\nDARK_MODE_ACTIVE\n")
        check = report["targeted_checks"]["dark_factory_visibility_contract"]
        self.assertFalse(check["ok"])
        self.assertEqual(check["missing"], _VISIBILITY_TOKENS)

    def test_check_passes_on_policy_carrying_the_protocol(self) -> None:
        report = _verify_policy_only_workspace("\n".join(_VISIBILITY_TOKENS) + "\n")
        self.assertTrue(report["targeted_checks"]["dark_factory_visibility_contract"]["ok"])

    def test_check_passes_on_the_dogfood_tree(self) -> None:
        with tempfile.TemporaryDirectory() as staging:
            report = verify_workspace(_REPO_ROOT, _REPO_ROOT, Path(staging))
        self.assertTrue(report["targeted_checks"]["dark_factory_visibility_contract"]["ok"])
        self.assertEqual(len(report["blockers"]), 0)


class PolicyVisibilityProtocolContentTests(unittest.TestCase):
    def test_template_and_mirror_carry_the_event_table_verbatim(self) -> None:
        for path in (_TEMPLATE, _MIRROR):
            with self.subTest(path=path.name):
                text = _read(path)
                self.assertIn(_EXPECTED_TABLE, text)
                p017 = text.split("## P-017:", 1)[1].split("\n## P-018:", 1)[0]
                self.assertIn("Dark Factory Visibility Protocol", p017)
                self.assertIn(_EXPECTED_TABLE, p017)

    def test_degraded_visibility_halt_rules_are_retained(self) -> None:
        for path in (_TEMPLATE, _MIRROR):
            with self.subTest(path=path.name):
                p017 = _read(path).split("## P-017:", 1)[1].split("\n## P-018:", 1)[0]
                self.assertIn("degraded-visibility", p017)
                for stop in (
                    "destructive actions",
                    "admin fallback",
                    "scope expansion",
                    "secrets-exposure risk",
                    "ambiguous branch-protection state",
                ):
                    self.assertIn(stop, p017)

    def test_policy_has_no_pack_transport_dependency(self) -> None:
        for path in (_TEMPLATE, _MIRROR):
            with self.subTest(path=path.name):
                self.assertNotIn("inter" + "com", _read(path).lower())


if __name__ == "__main__":
    unittest.main()
