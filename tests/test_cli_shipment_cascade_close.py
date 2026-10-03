"""CLI wiring tests for ``autoharness shipment cascade-close`` (192.015-T, plan unit A3d).

Three table-driven scenarios (plan ``### A3d``), with ``run_cascade_close``
and ``run_classify_only`` stubbed and the binary resolution faked, so no
backlogit binary is resolved or spawned (constitution IV):

1. the ``--json`` object for every exit code in the A3 table, including
   ``mutation_possible`` per code and per mode;
2. the USAGE text carries the destructive and no-clobber labels;
3. the argument-parsing table: an out-of-range ``--timeout``, a lone
   ``--replace-pre-close``, a missing ``--sha``, and the other invalid
   combinations each exit 2 without resolving a binary or running a mode;
   valid argv routes ``--classify-only`` (and ``--classify-only
   --replace-pre-close``) to ``run_classify_only`` and the mutating mode to
   ``run_cascade_close``.
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from autoharness import cli
from autoharness.cli import main
from autoharness.shipment_close import command, preclose, runner
from autoharness.shipment_close.command import CascadeCloseOutcome
from autoharness.shipment_close.preclose import ClassifyOnlyResult
from autoharness.shipment_close.runner import ResolvedBinary

_SHA = "bd824b97999832aa38122f2f70d300ebbb5d2e09"
_RESOLVED = ResolvedBinary(binary_path="/opt/backlogit/backlogit", binary_sha256="0" * 64, argv_prefix=("backlogit",))
_EVIDENCE = Path("docs/closure/evidence/900-S-600-F-cascade-close.json")
_JSON_KEYS = {
    "mode",
    "exit_code",
    "evidence_path",
    "phase_written",
    "classifier_verdict",
    "engine_verdict",
    "selected_close_path",
    "mutation_possible",
    "postcondition_verdict",
    "failures",
    "operator_action",
}
_BASE = ("shipment", "cascade-close", "--shipment", "900-S", "--feature", "600-F", "--sha", _SHA)
_MUTATING = (*_BASE, "--message", "close 900-S", "--author", "ship")


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:
        code = exc.code
    return out.getvalue(), err.getvalue(), code


class _Stubs:
    """Patch the binary resolution and both mode entry points."""

    def __init__(self, *, mutating: CascadeCloseOutcome | None = None, classify: ClassifyOnlyResult | None = None):
        self.resolve = mock.Mock(return_value=_RESOLVED)
        self.mutating = mock.Mock(return_value=mutating)
        self.classify = mock.Mock(return_value=classify)
        self._patches = [
            mock.patch.object(runner, "resolve_backlogit_binary", self.resolve),
            mock.patch.object(command, "run_cascade_close", self.mutating),
            mock.patch.object(preclose, "run_classify_only", self.classify),
        ]

    def __enter__(self) -> _Stubs:  # noqa: PYI034 - Python 3.10 has no typing.Self
        for patch in self._patches:
            patch.start()
        return self

    def __exit__(self, *exc: object) -> None:
        for patch in reversed(self._patches):
            patch.stop()


def _json(*argv: str, **stubs: object) -> tuple[dict, int | None, _Stubs]:
    with _Stubs(**stubs) as active:
        out, _err, code = _run(*argv, "--json")
    return json.loads(out), code, active


class JsonOutputTests(unittest.TestCase):
    """Scenario 1: one ``--json`` object per exit code, with ``mutation_possible`` per code."""

    def test_mutating_json_per_exit_code(self) -> None:
        table = [
            (0, "post_close", "yes", "none", "pass", ()),
            (2, None, "no", "none", None, ()),
            (3, "pre_close", "no", "none", None, ()),
            (4, "pre_close", "no", "review_required", None, ()),
            (5, "post_close", "yes", "review_required", "fail", ("returned_ids non-empty",)),
            (6, "post_close", "indeterminate", "review_required", None, ()),
            (7, None, "unknown", "review_required", None, ()),
            (8, "invoking", "yes", "review_required", None, ()),
        ]
        for exit_code, phase, mutation, action, verdict, failures in table:
            with self.subTest(exit_code=exit_code):
                outcome = CascadeCloseOutcome(
                    exit_code=exit_code,
                    message=f"outcome {exit_code}",
                    evidence_path=_EVIDENCE,
                    phase_written=phase,
                    classifier_verdict="CASCADE",
                    engine_verdict="VERIFIED",
                    selected_close_path="cascade",
                    mutation_state="mutated",
                    postcondition_verdict=verdict,
                    failures=failures,
                )
                payload, code, stubs = _json(*_MUTATING, mutating=outcome)
                self.assertEqual(set(payload), _JSON_KEYS)
                self.assertEqual(code, exit_code)
                self.assertEqual(payload["mode"], "mutating")
                self.assertEqual(payload["exit_code"], exit_code)
                self.assertEqual(payload["evidence_path"], str(_EVIDENCE))
                self.assertEqual(payload["phase_written"], phase)
                self.assertEqual(payload["classifier_verdict"], "CASCADE")
                self.assertEqual(payload["engine_verdict"], "VERIFIED")
                self.assertEqual(payload["selected_close_path"], "cascade")
                self.assertEqual(payload["mutation_possible"], mutation)
                self.assertEqual(payload["postcondition_verdict"], verdict)
                self.assertEqual(payload["operator_action"], action)
                self.assertIsInstance(payload["failures"], list)
                for failure in failures:
                    self.assertIn(failure, payload["failures"])
                if exit_code not in (0, 3):
                    self.assertIn(f"outcome {exit_code}", payload["failures"])
                stubs.classify.assert_not_called()
                stubs.mutating.assert_called_once()

    def test_classify_only_json_per_exit_code(self) -> None:
        table = [
            (0, "cascade", "pre_close"),
            (3, "safe_close", "pre_close"),
            (2, None, None),
            (7, None, None),
        ]
        for exit_code, selected, phase in table:
            with self.subTest(exit_code=exit_code):
                result = ClassifyOnlyResult(
                    exit_code,
                    f"classify {exit_code}",
                    evidence_path=_EVIDENCE if phase else None,
                    selected_close_path=selected,
                    classifier_verdict="CASCADE" if selected else None,
                    engine_verdict="UNVERIFIED" if selected == "safe_close" else None,
                )
                payload, code, stubs = _json(*_BASE, "--classify-only", classify=result)
                self.assertEqual(set(payload), _JSON_KEYS)
                self.assertEqual(payload["mode"], "classify_only")
                self.assertEqual(payload["exit_code"], exit_code)
                self.assertEqual(code, exit_code)
                self.assertEqual(payload["selected_close_path"], selected)
                self.assertEqual(payload["phase_written"], phase)
                self.assertIsNone(payload["postcondition_verdict"])
                # --classify-only never invokes the cascade: exit 0 is "no", unlike the mutating mode.
                expected = "unknown" if exit_code == 7 else "no"
                self.assertEqual(payload["mutation_possible"], expected)
                self.assertEqual(payload["operator_action"], "review_required" if exit_code == 7 else "none")
                stubs.mutating.assert_not_called()

    def test_input_failures_report_mutation_not_possible(self) -> None:
        with mock.patch.object(runner, "resolve_backlogit_binary", side_effect=runner.PersistError(2, "no binary")):
            out, _err, code = _run(*_MUTATING, "--json")
        payload = json.loads(out)
        self.assertEqual(code, 2)
        self.assertEqual(payload["exit_code"], 2)
        self.assertEqual(payload["mutation_possible"], "no")
        self.assertIn("no binary", payload["failures"][0])

    def test_human_output_names_the_exit_code(self) -> None:
        outcome = CascadeCloseOutcome(exit_code=3, message="selected safe_close (engine UNVERIFIED)")
        with _Stubs(mutating=outcome):
            out, err, code = _run(*_MUTATING)
        self.assertEqual(code, 3)
        self.assertIn("selected safe_close", out + err)


class UsageTests(unittest.TestCase):
    """Scenario 2: USAGE labels the destructive modes and the no-clobber ``--classify-only``."""

    def test_usage_labels(self) -> None:
        usage = cli.SHIPMENT_USAGE
        self.assertIn("cascade-close", usage)
        lowered = usage.lower()
        self.assertIn("destructive", lowered)
        self.assertIn("no-clobber", lowered)
        self.assertRegex(usage, r"--classify-only --replace-pre-close[^\n]*\n?[^\n]*DESTRUCTIVE")
        self.assertRegex(usage, r"(?s)mutating mode[^\n]*DESTRUCTIVE")
        self.assertRegex(lowered, r"(?s)plain --classify-only.{0,200}no-clobber.{0,200}read-only")
        self.assertIn("shipment cascade-close", cli.USAGE)
        for token in ("--shipment", "--feature", "--sha", "--message", "--author", "--timeout", "--json"):
            self.assertIn(token, usage)
        self.assertIn(f"{runner.MIN_TIMEOUT_SECONDS}-{runner.MAX_TIMEOUT_SECONDS} seconds", usage)
        self.assertIn(f"Default: {runner.DEFAULT_TIMEOUT_SECONDS}.", usage)
        self.assertNotIn("30-900", usage)

    def test_help_prints_usage(self) -> None:
        for argv in (("shipment",), ("shipment", "--help"), ("shipment", "cascade-close", "--help")):
            with self.subTest(argv=argv):
                out, _err, code = _run(*argv)
                self.assertIn(code, (0, None))
                self.assertIn("cascade-close", out)


class ArgumentParsingTests(unittest.TestCase):
    """Scenario 3: invalid argv exits 2 before any resolution; valid argv routes to one mode."""

    def test_invalid_argument_table(self) -> None:
        no_sha = ("shipment", "cascade-close", "--shipment", "900-S", "--feature", "600-F")
        cases = [
            ("timeout below range", (*_MUTATING, "--timeout", str(runner.MIN_TIMEOUT_SECONDS - 1))),
            ("timeout above range", (*_MUTATING, "--timeout", str(runner.MAX_TIMEOUT_SECONDS + 1))),
            ("non-integer timeout", (*_MUTATING, "--timeout", "1e2")),
            ("lone --replace-pre-close", (*_MUTATING, "--replace-pre-close")),
            ("lone --replace-pre-close without message", (*_BASE, "--replace-pre-close")),
            ("missing --sha (mutating)", (*no_sha, "--message", "m", "--author", "a")),
            ("missing --sha (classify-only)", (*no_sha, "--classify-only")),
            ("missing --shipment", ("shipment", "cascade-close", "--feature", "600-F", "--sha", _SHA, "--classify-only")),
            ("missing --feature", ("shipment", "cascade-close", "--shipment", "900-S", "--sha", _SHA, "--classify-only")),
            ("mutating without --message", (*_BASE, "--author", "ship")),
            ("mutating without --author", (*_BASE, "--message", "m")),
            ("classify-only with --message", (*_BASE, "--classify-only", "--message", "m")),
            ("classify-only with --timeout", (*_BASE, "--classify-only", "--timeout", "120")),
            ("duplicate flag", (*_MUTATING, "--sha", _SHA)),
            ("missing flag value", (*_BASE, "--classify-only", "--workspace")),
            ("unknown argument", (*_BASE, "--classify-only", "--force")),
            ("unknown shipment subcommand", ("shipment", "ship", "900-S")),
        ]
        for name, argv in cases:
            for emit_json in (False, True):
                with self.subTest(name, emit_json=emit_json):
                    with _Stubs() as stubs:
                        out, err, code = _run(*argv, *(("--json",) if emit_json else ()))
                    self.assertEqual(code, 2, out + err)
                    stubs.resolve.assert_not_called()
                    stubs.mutating.assert_not_called()
                    stubs.classify.assert_not_called()
                    if emit_json and name != "unknown shipment subcommand":
                        payload = json.loads(out)
                        self.assertEqual(payload["exit_code"], 2)
                        self.assertEqual(payload["mutation_possible"], "no")
                        self.assertEqual(payload["operator_action"], "none")
                        self.assertTrue(payload["failures"])

    def test_routing_table(self) -> None:
        classify = ClassifyOnlyResult(0, "selected cascade", evidence_path=_EVIDENCE, selected_close_path="cascade")
        mutating = CascadeCloseOutcome(exit_code=0, message="closed", evidence_path=_EVIDENCE)
        workspace = ("--workspace", "scratch-ws")

        with self.subTest("plain --classify-only is no-clobber"):
            payload, _code, stubs = _json(*_BASE, "--classify-only", *workspace, classify=classify)
            self.assertEqual(payload["mode"], "classify_only")
            stubs.resolve.assert_called_once_with(Path("scratch-ws"))
            stubs.classify.assert_called_once_with(
                Path("scratch-ws"), "900-S", "600-F", _SHA, resolved=_RESOLVED, replace_pre_close=False
            )

        with self.subTest("--classify-only --replace-pre-close replaces (destructive)"):
            payload, _code, stubs = _json(*_BASE, "--replace-pre-close", "--classify-only", classify=classify)
            self.assertEqual(payload["mode"], "replace_pre_close")
            stubs.classify.assert_called_once_with(
                Path("."), "900-S", "600-F", _SHA, resolved=_RESOLVED, replace_pre_close=True
            )
            stubs.mutating.assert_not_called()

        with self.subTest("mutating mode with the default and an explicit --timeout"):
            for extra, timeout in (
                ((), runner.DEFAULT_TIMEOUT_SECONDS),
                (("--timeout", str(runner.MAX_TIMEOUT_SECONDS)), runner.MAX_TIMEOUT_SECONDS),
            ):
                payload, _code, stubs = _json(*_MUTATING, *extra, mutating=mutating)
                self.assertEqual(payload["mode"], "mutating")
                stubs.mutating.assert_called_once_with(
                    Path("."),
                    "900-S",
                    "600-F",
                    _SHA,
                    message="close 900-S",
                    author="ship",
                    resolved=_RESOLVED,
                    timeout=timeout,
                )
                stubs.classify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
