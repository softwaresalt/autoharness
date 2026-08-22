"""Property tests for tests/_git_env.py's consistent_git_env normalizer
(144.005-T, shipment 152-S).

Plan: docs/plans/2026-08-22-git-config-env-containment-plan.md Task 5.
Amendments A1, A7, A7R (BINDING).
"""

from __future__ import annotations

import copy
import os
import unittest

from _git_env import consistent_git_env


class ConsistentGitEnvPropertyTests(unittest.TestCase):
    """The six binding properties, each individually tested."""

    def test_preservation_well_formed_pairs_survive_unchanged_in_order(self) -> None:
        base = {
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "safe.bareRepository",
            "GIT_CONFIG_VALUE_0": "explicit",
            "GIT_CONFIG_KEY_1": "credential.interactive",
            "GIT_CONFIG_VALUE_1": "never",
        }
        result = consistent_git_env(base)
        self.assertEqual(result["GIT_CONFIG_COUNT"], "2")
        self.assertEqual(result["GIT_CONFIG_KEY_0"], "safe.bareRepository")
        self.assertEqual(result["GIT_CONFIG_VALUE_0"], "explicit")
        self.assertEqual(result["GIT_CONFIG_KEY_1"], "credential.interactive")
        self.assertEqual(result["GIT_CONFIG_VALUE_1"], "never")

    def test_narrowness_key_absent_value_present_pair_dropped_and_renumbered(
        self,
    ) -> None:
        base = {
            "GIT_CONFIG_COUNT": "2",
            # GIT_CONFIG_KEY_0 is ABSENT -- only VALUE_0 present.
            "GIT_CONFIG_VALUE_0": "orphan_value",
            "GIT_CONFIG_KEY_1": "safe.bareRepository",
            "GIT_CONFIG_VALUE_1": "explicit",
        }
        result = consistent_git_env(base)
        self.assertEqual(result["GIT_CONFIG_COUNT"], "1")
        self.assertEqual(result["GIT_CONFIG_KEY_0"], "safe.bareRepository")
        self.assertEqual(result["GIT_CONFIG_VALUE_0"], "explicit")
        self.assertNotIn("GIT_CONFIG_KEY_1", result)
        self.assertNotIn("GIT_CONFIG_VALUE_1", result)

    def test_narrowness_value_absent_key_present_pair_dropped_and_renumbered(
        self,
    ) -> None:
        base = {
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "orphan_key",
            # GIT_CONFIG_VALUE_0 is ABSENT.
            "GIT_CONFIG_KEY_1": "safe.bareRepository",
            "GIT_CONFIG_VALUE_1": "explicit",
        }
        result = consistent_git_env(base)
        self.assertEqual(result["GIT_CONFIG_COUNT"], "1")
        self.assertEqual(result["GIT_CONFIG_KEY_0"], "safe.bareRepository")
        self.assertEqual(result["GIT_CONFIG_VALUE_0"], "explicit")
        self.assertNotIn("GIT_CONFIG_KEY_1", result)
        self.assertNotIn("GIT_CONFIG_VALUE_1", result)

    def test_narrowness_both_absent_pair_dropped(self) -> None:
        base = {
            "GIT_CONFIG_COUNT": "2",
            # Both GIT_CONFIG_KEY_0 and GIT_CONFIG_VALUE_0 absent entirely.
            "GIT_CONFIG_KEY_1": "safe.bareRepository",
            "GIT_CONFIG_VALUE_1": "explicit",
        }
        result = consistent_git_env(base)
        self.assertEqual(result["GIT_CONFIG_COUNT"], "1")
        self.assertEqual(result["GIT_CONFIG_KEY_0"], "safe.bareRepository")
        self.assertEqual(result["GIT_CONFIG_VALUE_0"], "explicit")

    def test_narrowness_both_present_with_empty_value_kept_verbatim(self) -> None:
        """Empty is NOT absent -- a pair whose value is the empty string
        (exactly GIT_CONFIG_VALUE_2's real-world shape, the operator
        constraint this whole plan exists to satisfy) is KEPT, not
        dropped."""
        base = {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "some.key",
            "GIT_CONFIG_VALUE_0": "",
        }
        result = consistent_git_env(base)
        self.assertEqual(result["GIT_CONFIG_COUNT"], "1")
        self.assertEqual(result["GIT_CONFIG_KEY_0"], "some.key")
        self.assertEqual(result["GIT_CONFIG_VALUE_0"], "")

    def test_provable_no_op_on_already_self_consistent_input(self) -> None:
        base = {
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "safe.bareRepository",
            "GIT_CONFIG_VALUE_0": "explicit",
            "GIT_CONFIG_KEY_1": "credential.interactive",
            "GIT_CONFIG_VALUE_1": "never",
            "PATH": "/usr/bin",
            "GIT_CONFIG_GLOBAL": "/some/path",
        }
        result = consistent_git_env(base)
        self.assertEqual(result, base)
        self.assertEqual(list(result.keys()), list(base.keys()))

    def test_no_triple_at_all_returned_unchanged(self) -> None:
        base = {"PATH": "/usr/bin", "HOME": "/home/user"}
        result = consistent_git_env(base)
        self.assertEqual(result, base)

    def test_malformed_count_non_integer_returned_unchanged(self) -> None:
        base = {
            "GIT_CONFIG_COUNT": "not_a_number",
            "GIT_CONFIG_KEY_0": "some.key",
            "GIT_CONFIG_VALUE_0": "some_value",
        }
        result = consistent_git_env(base)
        self.assertEqual(result, base)

    def test_malformed_count_negative_returned_unchanged(self) -> None:
        base = {
            "GIT_CONFIG_COUNT": "-1",
            "GIT_CONFIG_KEY_0": "some.key",
            "GIT_CONFIG_VALUE_0": "some_value",
        }
        result = consistent_git_env(base)
        self.assertEqual(result, base)

    def test_purity_never_mutates_os_environ(self) -> None:
        sentinel_key = "AUTOHARNESS_GITENV_PURITY_" + os.urandom(4).hex().upper()
        os.environ[sentinel_key] = ""  # deliberately blank, on the real os.environ
        try:
            before = copy.deepcopy(os.environ.copy())
            consistent_git_env()  # base=None -- reads from real os.environ
            after = os.environ.copy()
            self.assertEqual(before, after)
            # Also exercise the mutating-input-illusion case: passing a plain
            # dict explicitly and confirming that dict itself is untouched.
            base = {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "orphan_key",
            }
            base_copy = dict(base)
            consistent_git_env(base)
            self.assertEqual(base, base_copy)
        finally:
            os.environ.pop(sentinel_key, None)


class ConsistentGitEnvPassThroughTests(unittest.TestCase):
    """A7 (BINDING): the second, unrelated GIT_CONFIG* injection channel is
    matched by EXACT name shape only -- a prefix match on GIT_CONFIG* would
    silently disable these. Dedicated pass-through test for EACH."""

    def test_git_config_parameters_passes_through_unchanged(self) -> None:
        base = {"GIT_CONFIG_PARAMETERS": "'safe.bareRepository=explicit'"}
        result = consistent_git_env(base)
        self.assertEqual(
            result["GIT_CONFIG_PARAMETERS"], "'safe.bareRepository=explicit'"
        )

    def test_git_config_global_passes_through_unchanged(self) -> None:
        base = {"GIT_CONFIG_GLOBAL": "/some/global/gitconfig"}
        result = consistent_git_env(base)
        self.assertEqual(result["GIT_CONFIG_GLOBAL"], "/some/global/gitconfig")

    def test_git_config_system_passes_through_unchanged(self) -> None:
        base = {"GIT_CONFIG_SYSTEM": "/some/system/gitconfig"}
        result = consistent_git_env(base)
        self.assertEqual(result["GIT_CONFIG_SYSTEM"], "/some/system/gitconfig")

    def test_git_config_nosystem_passes_through_unchanged(self) -> None:
        base = {"GIT_CONFIG_NOSYSTEM": "1"}
        result = consistent_git_env(base)
        self.assertEqual(result["GIT_CONFIG_NOSYSTEM"], "1")

    def test_any_other_git_config_prefixed_name_passes_through_unchanged(
        self,
    ) -> None:
        base = {"GIT_CONFIG_SOME_FUTURE_VARIABLE": "untouched"}
        result = consistent_git_env(base)
        self.assertEqual(
            result["GIT_CONFIG_SOME_FUTURE_VARIABLE"], "untouched"
        )


if __name__ == "__main__":
    unittest.main()
