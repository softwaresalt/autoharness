"""Version-aware config validation guidance in the workspace-discovery skill (208-F B4a).

Phase 0 item 1 must select the harness-config schema by the document's own
``schema_version`` instead of validating against the root schema, which tracks
only the current contract version. The version and current mirror come only from
``tests/_config_schema_contract.py`` so the 1.2.0 cut-over never edits this test.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft7Validator

from _config_schema_contract import CURRENT_CONFIG_SCHEMA_VERSION, current_config_mirror_path
from autoharness.schema_contracts import SCHEMA_CONTRACTS, resolve_contract_schema_path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SKILL = _REPO_ROOT / ".github" / "skills" / "workspace-discovery" / "SKILL.md"
_ROOT_SCHEMA = _REPO_ROOT / "schemas" / "harness-config.schema.json"
_MIRROR_DIR = _REPO_ROOT / "schemas" / "harness-config"

_RUNTIME_VALIDATION_TOKENS = (
    "runtime_validation:",
    "validator_manifest",
    "validation_expectations",
    "releasability:",
)


def _skill_text() -> str:
    return _SKILL.read_text(encoding="utf-8")


def _phase0_item1() -> str:
    match = re.search(r"(?ms)^1\. (.*?)^2\. Extract operator preferences", _skill_text())
    if match is None:
        raise AssertionError("Phase 0 item 1 not found in the workspace-discovery skill")
    return match.group(1)


def _validator(path: Path) -> Draft7Validator:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def _mirror_versions() -> list[str]:
    """Known contract versions; each must have a published mirror file."""
    return [str(version) for version in SCHEMA_CONTRACTS["config"]["known_versions"]]


class Phase0ConfigValidationWordingTests(unittest.TestCase):
    def test_item_selects_the_schema_by_the_documents_own_version(self) -> None:
        item = _phase0_item1()
        for token in (
            "schema_version",
            "schemas/harness-config/<schema_version>.schema.json",
            "autoharness verify-workspace --workspace {workspace_path} --json",
            "contract finding",
        ):
            with self.subTest(token=token):
                self.assertIn(token, item)

    def test_item_states_the_root_tracks_only_the_current_version(self) -> None:
        item = _phase0_item1()
        self.assertIn("schemas/harness-config.schema.json", item)
        self.assertRegex(item, r"(?i)root[^\n]*tracks only the current version")

    def test_item_handles_absent_unknown_or_unmirrored_versions(self) -> None:
        item = _phase0_item1().lower()
        for token in ("absent", "unknown", "current mirror"):
            with self.subTest(token=token):
                self.assertIn(token, item)

    def test_item_no_longer_validates_against_the_root_file_alone(self) -> None:
        self.assertNotRegex(_phase0_item1().strip(), r"^Validate against `schemas/harness-config\.schema\.json`$")

    def test_item_adds_no_template_placeholder(self) -> None:
        self.assertNotIn("{{", _phase0_item1())

    def test_runtime_validation_contract_tokens_and_name_are_unchanged(self) -> None:
        text = _skill_text()
        for token in _RUNTIME_VALIDATION_TOKENS:
            with self.subTest(token=token):
                self.assertIn(token, text)
        self.assertRegex(text, r"(?m)\Aname: workspace-discovery$|\A---\nname: workspace-discovery\n")


class VersionSelectionBehaviorTests(unittest.TestCase):
    def test_every_known_version_has_a_mirror_selected_by_its_own_version(self) -> None:
        for version in _mirror_versions():
            with self.subTest(version=version):
                mirror = _MIRROR_DIR / f"{version}.schema.json"
                self.assertTrue(mirror.is_file(), f"missing mirror for known version {version}")
                fixture = {"schema_version": version}
                self.assertEqual(resolve_contract_schema_path("config", _REPO_ROOT, fixture), mirror)
                self.assertEqual(list(_validator(mirror).iter_errors(fixture)), [])

    def test_root_rejects_every_non_current_version_with_a_schema_version_const_error(self) -> None:
        root = _validator(_ROOT_SCHEMA)
        older = [version for version in _mirror_versions() if version != CURRENT_CONFIG_SCHEMA_VERSION]
        self.assertTrue(older, "expected at least one non-current known version")
        for version in older:
            with self.subTest(version=version):
                errors = list(root.iter_errors({"schema_version": version}))
                self.assertTrue(
                    any(list(error.absolute_path) == ["schema_version"] and error.validator == "const" for error in errors),
                    [error.message for error in errors],
                )

    def test_current_version_fixture_validates_against_root_and_current_mirror(self) -> None:
        fixture = {"schema_version": CURRENT_CONFIG_SCHEMA_VERSION}
        for label, schema_path in (("root", _ROOT_SCHEMA), ("current mirror", current_config_mirror_path())):
            with self.subTest(schema=label):
                self.assertEqual(list(_validator(schema_path).iter_errors(fixture)), [])


if __name__ == "__main__":
    unittest.main()
