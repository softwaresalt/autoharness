"""Tests for the atomic gate-check pipeline and module-boundary isolation (T6).

Covers discovery -> match -> run aggregation, atomic all-or-nothing blocking,
no-match / all-pass exit semantics, and the Plan Review P2-2 requirement that
``gates/*`` never imports install/tune modules.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.gates import gate as gate_mod
from autoharness.gates.config import GatePolicy, GatesConfig, LifecycleHooks, ValidationGate
from autoharness.gates.discovery import InvalidGitRefError
from autoharness.gates.runner import GateResult

GATES_DIR = Path(__file__).resolve().parents[1] / "src" / "autoharness" / "gates"
FORBIDDEN_IMPORTS = ("verify_workspace", "schema_contracts", "install", "tune")
_BASE_SHA = "a" * 40
_HEAD_SHA = "b" * 40
_TEMP_ROOT = Path(__file__).resolve().parents[1] / ".test-output"


def _config(*gates: ValidationGate) -> GatesConfig:
    policy = GatePolicy(validation_gates=tuple(gates))
    return GatesConfig(
        enabled=True,
        lifecycle_hooks=LifecycleHooks(pre_task_completion=policy),
    )


def _gate(pattern: str = "docs/**/*.md", command: str = "check {file_path}") -> ValidationGate:
    return ValidationGate(pattern=pattern, command=command, timeout_seconds=10)


def _make_run_fn(fail_paths: set[str]):
    """Return a fake subprocess.run: nonzero for argv whose last token is in fail_paths."""

    class _Proc:
        def __init__(self, returncode: int, stderr: str) -> None:
            self.returncode = returncode
            self.stdout = ""
            self.stderr = stderr

    def run_fn(argv, **_kwargs):
        target = argv[-1]
        if target in fail_paths:
            return _Proc(1, f"gate failed for {target}")
        return _Proc(0, "")

    return run_fn


class GatePipelineTests(unittest.TestCase):
    def test_all_pass_not_blocked(self) -> None:
        report = gate_mod.run_gates(
            _config(_gate()),
            ["docs/a.md", "docs/sub/b.md"],
            run_fn=_make_run_fn(set()),
            case_sensitive=True,
        )
        self.assertEqual(len(report.results), 2)
        self.assertFalse(report.blocked)
        self.assertEqual(report.failures, ())

    def test_single_failure_blocks_atomically(self) -> None:
        report = gate_mod.run_gates(
            _config(_gate()),
            ["docs/a.md", "docs/sub/b.md"],
            run_fn=_make_run_fn({"docs/sub/b.md"}),
            case_sensitive=True,
        )
        self.assertTrue(report.blocked)
        self.assertEqual(len(report.failures), 1)
        self.assertEqual(report.failures[0].file, "docs/sub/b.md")

    def test_no_match_passes(self) -> None:
        report = gate_mod.run_gates(
            _config(_gate(pattern="src/**/*.py")),
            ["docs/a.md", "README.md"],
            run_fn=_make_run_fn({"docs/a.md"}),
            case_sensitive=True,
        )
        self.assertEqual(report.matched_files, ())
        self.assertFalse(report.blocked)

    def test_check_no_gates_returns_empty_report(self) -> None:
        report = gate_mod.check(GatesConfig(enabled=False), base="main")
        self.assertEqual(report.results, ())
        self.assertFalse(report.blocked)

    def test_check_uses_injected_discover(self) -> None:
        captured = {}

        def fake_discover(base, head, *, cwd=None):
            captured["base"] = base
            captured["head"] = head
            return ["docs/x.md"]

        def fake_resolve(ref: str, *, cwd=None, runner=None):
            return {"main": _BASE_SHA, "HEAD": _HEAD_SHA}[ref]

        with mock.patch.object(gate_mod, "resolve_commit_ref", side_effect=fake_resolve):
            report = gate_mod.check(
                _config(_gate()),
                base="main",
                head="HEAD",
                discover=fake_discover,
                run_fn=_make_run_fn(set()),
                case_sensitive=True,
            )
        self.assertEqual(captured["base"], _BASE_SHA)
        self.assertEqual(captured["head"], _HEAD_SHA)
        self.assertEqual(report.matched_files, ("docs/x.md",))
        self.assertFalse(report.blocked)

    def test_check_rejects_invalid_base_without_discovery(self) -> None:
        called = False
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            output_path = Path(tmp) / "would-not-exist.txt"

            def fake_discover(base, head, *, cwd=None):
                nonlocal called
                called = True
                return []

            with self.assertRaises(InvalidGitRefError) as ctx:
                gate_mod.check(
                    _config(_gate()),
                    base=f"--output={output_path}",
                    discover=fake_discover,
                )
        self.assertEqual(ctx.exception.exit_code, 2)
        self.assertFalse(called)
        self.assertFalse(output_path.exists())

    def test_results_are_gate_result_instances(self) -> None:
        report = gate_mod.run_gates(
            _config(_gate()),
            ["docs/a.md"],
            run_fn=_make_run_fn(set()),
            case_sensitive=True,
        )
        self.assertIsInstance(report.results[0], GateResult)


class ModuleBoundaryTests(unittest.TestCase):
    def test_gates_package_has_no_install_tune_coupling(self) -> None:
        offenders: list[str] = []
        for py_file in GATES_DIR.glob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for module in FORBIDDEN_IMPORTS:
                # Only inspect actual import statements, not prose in docstrings.
                pattern = re.compile(
                    rf"^\s*(?:from|import)\s+[\w\.]*\b{re.escape(module)}\b",
                    re.MULTILINE,
                )
                if pattern.search(text):
                    offenders.append(f"{py_file.name} imports {module}")
        self.assertEqual(offenders, [], f"gates/ must not import install/tune modules: {offenders}")


if __name__ == "__main__":
    unittest.main()
