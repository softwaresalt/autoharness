"""Tests for autoharness.supervise.resolve -- Copilot CLI resolution + argv
composition (120.003-T). Pure module: no spawning, no subprocess calls.
"""

from __future__ import annotations

import dataclasses
import unittest
from unittest import mock

from autoharness.supervise.errors import ResolutionError
from autoharness.supervise.resolve import ResolveResult, resolve_copilot


class ResolutionOrderTests(unittest.TestCase):
    def test_env_copilot_exe_path_takes_precedence(self) -> None:
        result = resolve_copilot(
            [],
            env={"COPILOT_EXE_PATH": "/explicit/copilot", "COPILOT_EXE": "/legacy/copilot"},
        )
        self.assertEqual(result.exe_path, "/explicit/copilot")
        self.assertEqual(result.source, "env_path")

    def test_env_copilot_exe_used_when_exe_path_unset(self) -> None:
        result = resolve_copilot([], env={"COPILOT_EXE": "/legacy/copilot"})
        self.assertEqual(result.exe_path, "/legacy/copilot")
        self.assertEqual(result.source, "env_exe")

    def test_path_lookup_used_when_no_env_vars_set(self) -> None:
        with mock.patch("shutil.which", return_value="/usr/bin/copilot"):
            result = resolve_copilot([], env={})
        self.assertEqual(result.exe_path, "/usr/bin/copilot")
        self.assertEqual(result.source, "path_lookup")

    def test_unresolvable_raises_resolution_error_with_actionable_message(self) -> None:
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(ResolutionError) as ctx:
                resolve_copilot([], env={})
        message = str(ctx.exception)
        self.assertIn("Unable to locate Copilot CLI", message)
        self.assertIn("COPILOT_EXE_PATH", message)
        self.assertIn("COPILOT_EXE", message)
        self.assertIn("PATH", message)

    def test_never_fabricates_a_path(self) -> None:
        # H2: no guessed default path is ever returned.
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(ResolutionError):
                resolve_copilot([], env={})


class RemoteFlagCompositionTests(unittest.TestCase):
    def test_remote_appended_when_env_true(self) -> None:
        for value in ("true", "True", "TRUE", "1"):
            with self.subTest(value=value):
                result = resolve_copilot(
                    ["foo"], env={"COPILOT_EXE_PATH": "/x/copilot", "COPILOT_USE_REMOTE": value}
                )
                self.assertEqual(result.argv, ("/x/copilot", "--remote", "foo"))

    def test_remote_not_appended_when_env_falsy(self) -> None:
        for value in ("false", "0", "yes", ""):
            with self.subTest(value=value):
                result = resolve_copilot(
                    ["foo"], env={"COPILOT_EXE_PATH": "/x/copilot", "COPILOT_USE_REMOTE": value}
                )
                self.assertEqual(result.argv, ("/x/copilot", "foo"))

    def test_remote_not_duplicated_when_operator_already_passed_it(self) -> None:
        result = resolve_copilot(
            ["--remote", "foo"],
            env={"COPILOT_EXE_PATH": "/x/copilot", "COPILOT_USE_REMOTE": "true"},
        )
        self.assertEqual(result.argv, ("/x/copilot", "--remote", "foo"))
        # Exactly one --remote, not two.
        self.assertEqual(result.argv.count("--remote"), 1)

    def test_operator_args_forwarded_verbatim_including_leading_dashes_and_spaces(self) -> None:
        result = resolve_copilot(
            ["alpha", "--flag", "value with spaces", "-x"],
            env={"COPILOT_EXE_PATH": "/x/copilot"},
        )
        self.assertEqual(
            result.argv, ("/x/copilot", "alpha", "--flag", "value with spaces", "-x")
        )


class PurityTests(unittest.TestCase):
    def test_never_spawns_a_subprocess(self) -> None:
        with mock.patch("subprocess.run") as run_mock, mock.patch("subprocess.Popen") as popen_mock:
            resolve_copilot(["foo"], env={"COPILOT_EXE_PATH": "/x/copilot"})
            run_mock.assert_not_called()
            popen_mock.assert_not_called()

    def test_env_defaults_to_os_environ_read_only(self) -> None:
        # Should not raise even without an explicit env= (reads os.environ);
        # patch os.environ itself since a real dev environment may have
        # COPILOT_EXE_PATH/COPILOT_EXE already set.
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch("shutil.which", return_value="/usr/bin/copilot"):
                result = resolve_copilot([])
        self.assertEqual(result.source, "path_lookup")


class ResolveResultShapeTests(unittest.TestCase):
    def test_result_is_frozen(self) -> None:
        result = resolve_copilot([], env={"COPILOT_EXE_PATH": "/x/copilot"})
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.exe_path = "/y/copilot"  # type: ignore[misc]

    def test_argv0_is_exe_path(self) -> None:
        result = resolve_copilot(["a"], env={"COPILOT_EXE_PATH": "/x/copilot"})
        self.assertEqual(result.argv[0], result.exe_path)


if __name__ == "__main__":
    unittest.main()
