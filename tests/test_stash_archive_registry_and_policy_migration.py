"""Contract tests for 137.004-T: migrating the P-021 C5 policy clause and
the backlog registry template's stash-retirement mapping from the
deprecated `backlogit_stash_remove` MCP operation to the canonical
`backlogit_stash_archive` operation (MCP primary) / `backlogit stash
archive` (CLI fallback).

Scope boundary (per 137.004-T): this module asserts ONLY the policy clause
(templates/policies/workflow-policies.md.tmpl) and the registry mapping
(templates/backlog/registries/backlogit.registry.yaml). It does NOT assert
anything about the Ship agent contract itself (template or dogfood mirror),
the verifier, or the Ship contract tests -- those are 137.003-T's exclusive
acceptance surface, asserted in tests/test_scope_containment_policy_contract.py
and tests/test_verify_workspace.py.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW_POLICY_TEMPLATE = _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"
_BACKLOG_REGISTRY_TEMPLATE = (
    _REPO_ROOT / "templates" / "backlog" / "registries" / "backlogit.registry.yaml"
)


def _lf_text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


class WorkflowPolicyC5StashArchiveTests(unittest.TestCase):
    """Policy-clause half of 137.004-T."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = _lf_text(_WORKFLOW_POLICY_TEMPLATE)

    def test_c5_names_the_archive_operation_as_the_allowed_exception(self) -> None:
        self.assertIn("backlogit_stash_archive", self.text)

    def test_c5_no_longer_names_the_deprecated_remove_operation(self) -> None:
        self.assertNotIn("backlogit_stash_remove", self.text)

    def test_c5_manifest_derived_retirement_phrase_preserved(self) -> None:
        # Load-bearing for P-021 C5; must survive this migration verbatim.
        self.assertIn(
            "manifest-derived retirement of the source stash entry that fed the shipped scope",
            self.text,
        )

    def test_c5_discretionary_qualifier_still_governs_both_verbs(self) -> None:
        # H2: the rename must not collapse the removal/archival distinction.
        # DO NOT SIMPLIFY -- both verbs stay qualified as DISCRETIONARY.
        self.assertIn("DISCRETIONARILY remove, or DISCRETIONARILY archive them", self.text)

    def test_c5_post_merge_step7_scope_preserved(self) -> None:
        self.assertIn("post-merge Step 7", self.text)
        self.assertIn("custom_fields.source_stash_id", self.text)


class BacklogRegistryStashArchiveMappingTests(unittest.TestCase):
    """Registry half of 137.004-T."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = yaml.safe_load(_BACKLOG_REGISTRY_TEMPLATE.read_text(encoding="utf-8"))
        cls.operations = cls.registry["operations"]

    def test_stash_archive_mapping_exists(self) -> None:
        self.assertIn("stash_archive", self.operations)

    def test_stash_archive_mcp_tool_is_primary(self) -> None:
        mapping = self.operations["stash_archive"]
        self.assertEqual(mapping["mcp_tool"], "backlogit_stash_archive")

    def test_stash_archive_cli_fallback_is_exact_parameterized_string(self) -> None:
        """P1: a bare `backlogit stash archive` with no stash identifier is
        INVALID (the CLI declares exactly one required positional stash
        identifier). The placeholder must be spelled `{{stash_id}}` to bind
        against the mapping's own `params.stash_id` key."""
        mapping = self.operations["stash_archive"]
        self.assertIn("cli_command", mapping)
        self.assertEqual(mapping["cli_command"], "backlogit stash archive {{stash_id}}")
        self.assertIn("{{stash_id}}", mapping["cli_command"])
        self.assertEqual(mapping["params"]["stash_id"], "stash_id")

    def test_stash_archive_cli_fallback_is_never_bare(self) -> None:
        mapping = self.operations["stash_archive"]
        self.assertNotEqual(mapping["cli_command"], "backlogit stash archive")

    def test_stash_remove_mapping_still_present_deprecated_not_deleted(self) -> None:
        """H5: do NOT delete stash_remove -- the MCP tool is still exposed
        and the CLI retains `stash remove` as an alias. The registry's job
        is to describe the tool truthfully, including its deprecated
        surface."""
        self.assertIn("stash_remove", self.operations)
        mapping = self.operations["stash_remove"]
        self.assertEqual(mapping["mcp_tool"], "backlogit_stash_remove")

    def test_stash_remove_mapping_never_resolved_as_prescriptive_execution_path(self) -> None:
        """The registry MUST NOT resolve any Ship execution path to
        stash_remove: it is retained for description-of-reality only, not
        as an executable CLI fallback (no cli_command key)."""
        mapping = self.operations["stash_remove"]
        self.assertNotIn("cli_command", mapping)


if __name__ == "__main__":
    unittest.main()
