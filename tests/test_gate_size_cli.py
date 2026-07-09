"""End-to-end smoke tests for the `autoharness gate size` CLI subcommand.

Hermetic: the backlogit fetch and write-back are patched so no external binary
or network is touched. Covers the estimate/dry-run/skip/error exit-code contract.
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

from autoharness.cli import main

_TRIVIAL_TASK = {
    "id": "001.001-T",
    "title": "Fix typo in README",
    "description": "Correct a spelling error in the intro paragraph.",
    "labels": ["docs"],
}

_HEAVY_TASK = {
    "id": "002.002-T",
    "title": "Cross-cutting schema migration with concurrency and security review",
    "description": " ".join(["word"] * 400)
    + " schema migration architecture protocol distributed concurrency security",
    "acceptance_criteria": "- one\n- two\n- three\n- four\n- five",
    "labels": ["a", "b", "c", "d"],
}


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:  # noqa: PERF203 - test harness
        code = exc.code
    return out.getvalue(), err.getvalue(), code


class GateSizeHelpTests(unittest.TestCase):
    def test_gate_help_lists_size(self) -> None:
        out, _, _ = _run("gate", "--help")
        self.assertIn("size", out)
        self.assertIn("check", out)

    def test_size_help(self) -> None:
        out, _, _ = _run("gate", "size", "--help")
        self.assertIn("T-shirt size", out)
        self.assertIn("--dry-run", out)


class GateSizeArgErrorTests(unittest.TestCase):
    def test_missing_task_id_exits_2(self) -> None:
        _, _, code = _run("gate", "size")
        self.assertEqual(code, 2)

    def test_unknown_flag_exits_2(self) -> None:
        _, _, code = _run("gate", "size", "001.001-T", "--bogus")
        self.assertEqual(code, 2)

    def test_unknown_subcommand_exits_2(self) -> None:
        _, _, code = _run("gate", "frobnicate")
        self.assertEqual(code, 2)


class GateSizeDryRunTests(unittest.TestCase):
    def test_dry_run_estimates_without_writing(self) -> None:
        with mock.patch(
            "autoharness.gates.sizing.fetch_task", return_value=dict(_TRIVIAL_TASK)
        ):
            out, _, code = _run("gate", "size", "001.001-T", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("dry-run", out)
        self.assertIn("would write size: XS", out)

    def test_dry_run_json_is_serializable(self) -> None:
        with mock.patch(
            "autoharness.gates.sizing.fetch_task", return_value=dict(_HEAVY_TASK)
        ):
            out, _, code = _run("gate", "size", "002.002-T", "--dry-run", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["action"], "dry-run")
        self.assertEqual(payload["estimated_size"], "XL")
        self.assertTrue(payload["ok"])


class GateSizeWriteTests(unittest.TestCase):
    def test_written_invokes_backlogit_and_exits_0(self) -> None:
        completed = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch(
            "autoharness.gates.sizing.fetch_task", return_value=dict(_TRIVIAL_TASK)
        ), mock.patch(
            "autoharness.gates.sizing.subprocess.run", return_value=completed
        ) as run:
            out, _, code = _run("gate", "size", "001.001-T")
        self.assertEqual(code, 0)
        self.assertIn("wrote size: XS", out)
        argv = run.call_args.args[0]
        self.assertEqual(argv[:4], ["backlogit", "update", "001.001-T", "--size"])

    def test_skip_when_size_exists_exits_0(self) -> None:
        task = dict(_TRIVIAL_TASK, size="M")
        with mock.patch("autoharness.gates.sizing.fetch_task", return_value=task):
            out, _, code = _run("gate", "size", "001.001-T")
        self.assertEqual(code, 0)
        self.assertIn("skipped-existing", out)
        self.assertIn("M", out)


class GateSizeErrorTests(unittest.TestCase):
    def test_backlogit_rejection_failopen_exits_0(self) -> None:
        rejected = mock.Mock(
            returncode=1, stdout="", stderr="artifact type task does not define a size field"
        )
        with mock.patch(
            "autoharness.gates.sizing.fetch_task", return_value=dict(_TRIVIAL_TASK)
        ), mock.patch("autoharness.gates.sizing.subprocess.run", return_value=rejected):
            out, _, code = _run("gate", "size", "001.001-T")
        self.assertEqual(code, 0)
        self.assertIn("NOT blocked", out)

    def test_backlogit_rejection_strict_exits_3(self) -> None:
        rejected = mock.Mock(
            returncode=1, stdout="", stderr="artifact type task does not define a size field"
        )
        with mock.patch(
            "autoharness.gates.sizing.fetch_task", return_value=dict(_TRIVIAL_TASK)
        ), mock.patch("autoharness.gates.sizing.subprocess.run", return_value=rejected):
            out, _, code = _run("gate", "size", "001.001-T", "--strict")
        self.assertEqual(code, 3)
        self.assertIn("NOT blocked", out)

    def test_missing_binary_failopen_exits_0_strict_exits_3(self) -> None:
        with mock.patch(
            "autoharness.gates.sizing.fetch_task", return_value=dict(_TRIVIAL_TASK)
        ), mock.patch(
            "autoharness.gates.sizing.subprocess.run", side_effect=FileNotFoundError()
        ):
            _, _, code = _run("gate", "size", "001.001-T")
        self.assertEqual(code, 0)
        with mock.patch(
            "autoharness.gates.sizing.fetch_task", return_value=dict(_TRIVIAL_TASK)
        ), mock.patch(
            "autoharness.gates.sizing.subprocess.run", side_effect=FileNotFoundError()
        ):
            _, _, code = _run("gate", "size", "001.001-T", "--strict")
        self.assertEqual(code, 3)

    def test_fetch_failure_failopen_exits_0_strict_exits_3(self) -> None:
        with mock.patch(
            "autoharness.gates.sizing.fetch_task", side_effect=RuntimeError("no such task")
        ):
            _, _, code = _run("gate", "size", "999.999-T")
        self.assertEqual(code, 0)
        with mock.patch(
            "autoharness.gates.sizing.fetch_task", side_effect=RuntimeError("no such task")
        ):
            _, _, code = _run("gate", "size", "999.999-T", "--strict")
        self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
