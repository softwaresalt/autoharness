"""Tests for autoharness.supervise.bootstrap -- workspace bootstrap policy (120.001-T).

Covers: .env.local NO-CLOBBER parsing with single-matching-quote-pair
stripping, workspace-local COPILOT_HOME/ENGRAM_DATA_DIR defaulting on BOTH
platforms (unifying start.sh's previously-commented-out ENGRAM_DATA_DIR
default -- DELTA 2), and GITHUB_TOKEN/GITHUB_PERSONAL_ACCESS_TOKEN
resolution via ``gh auth token`` on BOTH platforms (DELTA 1/DELTA 3: gh
absent or failing is always non-fatal, never leaves an empty-string
placeholder, and never leaks the resolved secret value into warnings,
messages, or the frozen result envelope's own repr-visible surface other
than the ``env`` mapping explicitly designed to carry it to a child env).
"""

from __future__ import annotations

import dataclasses
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.supervise.bootstrap import BootstrapResult, bootstrap_workspace
from autoharness.supervise.redact import Redactor


class EnvLocalParsingTests(unittest.TestCase):
    def test_plain_and_quoted_values_are_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / ".env.local").write_text(
                "\n".join(
                    [
                        "PLAIN_VALUE=hello",
                        'DOUBLE_QUOTED="hello world"',
                        "SINGLE_QUOTED='hello world'",
                        "MISMATCHED_QUOTES=\"hello'",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            result = bootstrap_workspace(root, env={}, gh_executable="nonexistent-gh-binary")
            self.assertEqual(result.env["PLAIN_VALUE"], "hello")
            self.assertEqual(result.env["DOUBLE_QUOTED"], "hello world")
            self.assertEqual(result.env["SINGLE_QUOTED"], "hello world")
            self.assertEqual(result.env["MISMATCHED_QUOTES"], "\"hello'")

    def test_no_clobber_preset_var_wins(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / ".env.local").write_text("MY_CUSTOM_VAR=from_file\n", encoding="utf-8")
            result = bootstrap_workspace(
                root,
                env={"MY_CUSTOM_VAR": "from_process"},
                gh_executable="nonexistent-gh-binary",
            )
            # NO-CLOBBER: the pre-set value must not be overwritten, and must
            # not appear as a "resolved addition" in result.env either since
            # it was never actually changed by bootstrap.
            self.assertNotIn("MY_CUSTOM_VAR", result.env)

    def test_ignores_non_key_value_and_lowercase_is_still_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / ".env.local").write_text(
                "\n".join(
                    [
                        "# a comment",
                        "not a valid assignment",
                        "lowercase_var=works",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            result = bootstrap_workspace(root, env={}, gh_executable="nonexistent-gh-binary")
            self.assertEqual(result.env.get("lowercase_var"), "works")

    def test_absent_env_local_is_not_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            result = bootstrap_workspace(root, env={}, gh_executable="nonexistent-gh-binary")
            self.assertIsInstance(result, BootstrapResult)

    def test_trailing_whitespace_and_cr_are_stripped(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / ".env.local").write_bytes(b"WITH_CRLF=value_with_cr   \r\n")
            result = bootstrap_workspace(root, env={}, gh_executable="nonexistent-gh-binary")
            self.assertEqual(result.env["WITH_CRLF"], "value_with_cr")


class CopilotHomeAndEngramDataDirTests(unittest.TestCase):
    def test_defaults_to_workspace_subdirs_on_both_platforms(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            result = bootstrap_workspace(root, env={}, gh_executable="nonexistent-gh-binary")
            self.assertEqual(result.env["COPILOT_HOME"], str(root / ".copilot"))
            # DELTA 2: ENGRAM_DATA_DIR now defaults unconditionally -- no
            # platform branch, unlike today's start.sh where this line is
            # commented out.
            self.assertEqual(result.env["ENGRAM_DATA_DIR"], str(root / ".engram"))

    def test_honors_preset_values(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            result = bootstrap_workspace(
                root,
                env={"COPILOT_HOME": "/custom/copilot-home", "ENGRAM_DATA_DIR": "/custom/engram-data"},
                gh_executable="nonexistent-gh-binary",
            )
            self.assertNotIn("COPILOT_HOME", result.env)
            self.assertNotIn("ENGRAM_DATA_DIR", result.env)

    def test_empty_string_preset_is_treated_as_unset(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            result = bootstrap_workspace(
                root,
                env={"COPILOT_HOME": "", "ENGRAM_DATA_DIR": ""},
                gh_executable="nonexistent-gh-binary",
            )
            self.assertEqual(result.env["COPILOT_HOME"], str(root / ".copilot"))
            self.assertEqual(result.env["ENGRAM_DATA_DIR"], str(root / ".engram"))


class GitHubTokenResolutionTests(unittest.TestCase):
    def test_gh_absent_leaves_variables_unset_and_warns_non_fatally(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            result = bootstrap_workspace(
                root, env={}, gh_executable="definitely-not-a-real-executable-xyz"
            )
            self.assertNotIn("GITHUB_TOKEN", result.env)
            self.assertNotIn("GITHUB_PERSONAL_ACCESS_TOKEN", result.env)
            self.assertTrue(
                any("not found" in w.lower() and "GITHUB_TOKEN" in w for w in result.warnings)
            )
            # Never a bare empty-string placeholder.
            self.assertNotEqual(result.env.get("GITHUB_TOKEN"), "")

    def test_gh_failing_non_zero_exit_is_non_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            with mock.patch("shutil.which", return_value="/fake/path/gh"):
                with mock.patch("subprocess.run") as run_mock:
                    run_mock.return_value = subprocess.CompletedProcess(
                        args=["gh", "auth", "token"], returncode=1, stdout="", stderr="boom"
                    )
                    result = bootstrap_workspace(root, env={}, gh_executable="gh")
            self.assertNotIn("GITHUB_TOKEN", result.env)
            self.assertNotIn("GITHUB_PERSONAL_ACCESS_TOKEN", result.env)
            self.assertTrue(
                any("exited" in w.lower() and "GITHUB_TOKEN" in w for w in result.warnings)
            )

    def test_gh_success_resolves_both_vars_and_registers_secret(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            redactor = Redactor()
            with mock.patch("shutil.which", return_value="/fake/path/gh"):
                with mock.patch("subprocess.run") as run_mock:
                    run_mock.return_value = subprocess.CompletedProcess(
                        args=["gh", "auth", "token"], returncode=0, stdout="super-secret-token-value\n", stderr=""
                    )
                    result = bootstrap_workspace(root, env={}, gh_executable="gh", redactor=redactor)
            self.assertEqual(result.env["GITHUB_TOKEN"], "super-secret-token-value")
            self.assertEqual(result.env["GITHUB_PERSONAL_ACCESS_TOKEN"], "super-secret-token-value")
            # The secret must be registered with the redactor so it's caught
            # even if it matches no built-in regex pattern (H5).
            redacted = redactor.redact_text("token=super-secret-token-value end")
            self.assertNotIn("super-secret-token-value", redacted)

    def test_secret_never_leaks_into_warnings_or_messages(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            with mock.patch("shutil.which", return_value="/fake/path/gh"):
                with mock.patch("subprocess.run") as run_mock:
                    run_mock.return_value = subprocess.CompletedProcess(
                        args=["gh", "auth", "token"], returncode=0, stdout="topsecretvalue123\n", stderr=""
                    )
                    result = bootstrap_workspace(root, env={}, gh_executable="gh")
            for message in list(result.warnings) + list(result.messages):
                self.assertNotIn("topsecretvalue123", message)

    def test_preset_github_token_is_not_overwritten_and_gh_still_resolves_pat(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            with mock.patch("shutil.which", return_value="/fake/path/gh"):
                with mock.patch("subprocess.run") as run_mock:
                    run_mock.return_value = subprocess.CompletedProcess(
                        args=["gh", "auth", "token"], returncode=0, stdout="fresh-token\n", stderr=""
                    )
                    result = bootstrap_workspace(
                        root, env={"GITHUB_TOKEN": "already-set"}, gh_executable="gh"
                    )
            self.assertNotIn("GITHUB_TOKEN", result.env)
            self.assertEqual(result.env["GITHUB_PERSONAL_ACCESS_TOKEN"], "fresh-token")

    def test_both_preset_still_reresolves_unguarded_pat_only(self) -> None:
        """Preserves the pre-migration per-variable asymmetry exactly:
        GITHUB_TOKEN is guarded (NO-CLOBBER, gh never invoked once set) but
        GITHUB_PERSONAL_ACCESS_TOKEN is UNGUARDED and always re-resolved when
        gh is available -- matching start.ps1's unconditional
        `$env:GITHUB_PERSONAL_ACCESS_TOKEN = (gh auth token)` assignment.
        Unifying this guard behavior across the two variables would be an
        unnamed fourth delta outside the approved three-entry matrix."""

        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            with mock.patch("shutil.which", return_value="/fake/path/gh"):
                with mock.patch("subprocess.run") as run_mock:
                    run_mock.return_value = subprocess.CompletedProcess(
                        args=["gh", "auth", "token"], returncode=0, stdout="re-resolved\n", stderr=""
                    )
                    result = bootstrap_workspace(
                        root,
                        env={"GITHUB_TOKEN": "a", "GITHUB_PERSONAL_ACCESS_TOKEN": "b"},
                        gh_executable="gh",
                    )
            self.assertEqual(run_mock.call_count, 1)
            self.assertNotIn("GITHUB_TOKEN", result.env)  # guarded: untouched
            self.assertEqual(result.env["GITHUB_PERSONAL_ACCESS_TOKEN"], "re-resolved")  # unguarded: overwritten

    def test_both_preset_and_gh_absent_skips_entirely_non_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            result = bootstrap_workspace(
                root,
                env={"GITHUB_TOKEN": "a", "GITHUB_PERSONAL_ACCESS_TOKEN": "b"},
                gh_executable="definitely-not-a-real-executable-xyz",
            )
            self.assertNotIn("GITHUB_TOKEN", result.env)
            self.assertNotIn("GITHUB_PERSONAL_ACCESS_TOKEN", result.env)
            self.assertTrue(any("GITHUB_PERSONAL_ACCESS_TOKEN" in w for w in result.warnings))

    def test_never_uses_shell_true(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            with mock.patch("shutil.which", return_value="/fake/path/gh"):
                with mock.patch("subprocess.run") as run_mock:
                    run_mock.return_value = subprocess.CompletedProcess(
                        args=["gh", "auth", "token"], returncode=0, stdout="tok\n", stderr=""
                    )
                    bootstrap_workspace(root, env={}, gh_executable="gh")
            for call in run_mock.call_args_list:
                self.assertIsNot(call.kwargs.get("shell"), True)
                args_list = call.args[0] if call.args else call.kwargs.get("args")
                self.assertIsInstance(args_list, list)


class DoesNotMutateOsEnvironTests(unittest.TestCase):
    def test_default_env_is_a_copy_of_os_environ(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            snapshot_before = dict(os.environ)
            bootstrap_workspace(root, gh_executable="definitely-not-a-real-executable-xyz")
            self.assertEqual(dict(os.environ), snapshot_before)


class BootstrapResultShapeTests(unittest.TestCase):
    def test_result_is_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            result = bootstrap_workspace(root, env={}, gh_executable="definitely-not-a-real-executable-xyz")
            with self.assertRaises(dataclasses.FrozenInstanceError):
                result.env = {}  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
