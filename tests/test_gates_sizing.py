"""Tests for the pre-execution T-shirt sizing gate (task 055.003-T / U10).

Scope: a deterministic, hermetic T-shirt size estimator plus a safe write-back
that invokes the external ``backlogit update <id> --size <result>`` CLI. The
estimator is a pure function of task metadata and the pinned ruleset version. The
write-back never overwrites an existing size and never raises: a missing binary
or a backlogit rejection is a configuration failure, not a task failure.

No live models, no network, no real subprocess: ``fetch_fn`` and ``run_fn`` are
injected so every test is fully hermetic.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from autoharness.gates.sizing import (
    DEFAULT_BACKLOGIT,
    SIZES,
    SIZING_RULESET_VERSION,
    SizeEstimate,
    SizingResult,
    estimate_size,
    extract_signals,
    fetch_task,
    size_task,
)

_SIZE_INDEX = {s: i for i, s in enumerate(SIZES)}


def _task(*, title="", body="", description="", acceptance="", references=None, labels=None, size=None):
    """Build a backlogit-shaped task mapping for tests."""
    task: dict = {"id": "001.001-T", "artifact_type": "task"}
    if title:
        task["title"] = title
    if body:
        task["body"] = body
    if description and not body:
        task["description"] = description
    if references is not None:
        task["references"] = list(references)
    if labels is not None:
        task["labels"] = list(labels)
    if size is not None:
        task["size"] = size
    # embed markers when caller supplied section text
    sections = []
    if acceptance:
        sections.append(f"<!-- BEGIN:acceptance-criteria -->\n{acceptance}\n<!-- END:acceptance-criteria -->")
    if description and body == "":
        sections.append(f"<!-- BEGIN:description -->\n{description}\n<!-- END:description -->")
    if sections and "body" not in task:
        task["body"] = "\n\n".join(sections)
    return task


class _FakeProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class ExtractSignalsTests(unittest.TestCase):
    def test_pulls_description_and_acceptance_from_body_markers(self) -> None:
        body = (
            "<!-- BEGIN:acceptance-criteria -->\nWhen size is null, write it back.\n"
            "<!-- END:acceptance-criteria -->\n\n"
            "<!-- BEGIN:description -->\nEstimate task complexity.\n<!-- END:description -->"
        )
        sig = extract_signals({"body": body, "references": ["a.py"], "labels": ["cli", "telemetry"]})
        self.assertIn("Estimate task complexity", sig.description)
        self.assertIn("write it back", sig.acceptance)
        self.assertEqual(sig.references, ("a.py",))
        self.assertEqual(sig.labels, ("cli", "telemetry"))

    def test_falls_back_to_description_field(self) -> None:
        sig = extract_signals({"description": "Plain field description."})
        self.assertIn("Plain field description", sig.description)
        self.assertEqual(sig.references, ())
        self.assertEqual(sig.labels, ())

    def test_missing_fields_are_empty(self) -> None:
        sig = extract_signals({})
        self.assertEqual(sig.title, "")
        self.assertEqual(sig.description, "")
        self.assertEqual(sig.acceptance, "")
        self.assertEqual(sig.references, ())
        self.assertEqual(sig.labels, ())

    def test_pulls_title(self) -> None:
        sig = extract_signals({"title": "Cross-cutting schema migration"})
        self.assertEqual(sig.title, "Cross-cutting schema migration")


class EstimateSizeTests(unittest.TestCase):
    def test_returns_a_valid_size(self) -> None:
        est = estimate_size(_task(description="Do a thing."))
        self.assertIsInstance(est, SizeEstimate)
        self.assertIn(est.size, SIZES)
        self.assertEqual(est.ruleset_version, SIZING_RULESET_VERSION)

    def test_trivial_task_is_xs(self) -> None:
        est = estimate_size(_task(description="Fix a typo in a header comment.", labels=["docs"]))
        self.assertEqual(est.size, "XS")

    def test_huge_cross_cutting_task_is_xl(self) -> None:
        big = (
            "Rework the schema and run a data migration across the whole system. "
            "This is a cross-cutting architecture change touching security and "
            "concurrency and a breaking protocol change. " * 4
        )
        est = estimate_size(
            _task(
                description=big,
                acceptance="- one\n- two\n- three\n- four",
                references=["a.py", "b.py", "c.py", "d.py", "e.py"],
                labels=["schema", "migration", "security", "cross-cutting"],
            )
        )
        self.assertEqual(est.size, "XL")

    def test_deterministic(self) -> None:
        task = _task(
            description="Add a validation gate with tests.",
            acceptance="- gate fails on bad input\n- gate passes on good input",
            references=["src/x.py", "tests/test_x.py"],
            labels=["cli"],
        )
        self.assertEqual(estimate_size(task).size, estimate_size(task).size)
        self.assertEqual(estimate_size(task).score, estimate_size(task).score)

    def test_monotonic_more_complexity_never_shrinks(self) -> None:
        small = _task(description="Small change.", references=["a.py"], labels=["cli"])
        bigger = _task(
            description="Small change with a schema migration and refactor.",
            acceptance="- crit one\n- crit two\n- crit three",
            references=["a.py", "b.py", "c.py"],
            labels=["cli", "schema", "migration"],
        )
        self.assertGreaterEqual(
            _SIZE_INDEX[estimate_size(bigger).size],
            _SIZE_INDEX[estimate_size(small).size],
        )

    def test_title_complexity_raises_size(self) -> None:
        without = estimate_size(_task(description="Do the thing."))
        with_title = estimate_size(
            _task(
                title="Cross-cutting schema migration with concurrency and security",
                description="Do the thing.",
            )
        )
        self.assertGreaterEqual(
            _SIZE_INDEX[with_title.size], _SIZE_INDEX[without.size]
        )
        self.assertGreater(with_title.score, without.score)

    def test_keyword_matching_is_word_boundary_aware(self) -> None:
        # "typo" (simplicity) must not match inside "typography". Both tasks share
        # a complexity keyword so the score sits above the XS floor and the
        # simplicity deduction is observable.
        typo_word = estimate_size(_task(description="Fix a typo in the schema."))
        typography = estimate_size(_task(description="Improve the typography in the schema."))
        self.assertLess(typo_word.score, typography.score)

    def test_prose_acceptance_counts_once(self) -> None:
        prose = _task(
            description="Change.",
            acceptance="This is a single wrapped criterion that spans\nseveral physical lines but is one requirement.",
        )
        bulleted = _task(
            description="Change.",
            acceptance="- one\n- two\n- three\n- four\n- five",
        )
        self.assertLess(
            estimate_size(prose).score, estimate_size(bulleted).score
        )


class SizeTaskWriteBackTests(unittest.TestCase):
    def test_skips_when_size_already_set(self) -> None:
        calls = []

        def run_fn(argv, **kwargs):  # pragma: no cover - must not be called
            calls.append(argv)
            return _FakeProc()

        result = size_task(
            "001.001-T",
            fetch_fn=lambda tid, cwd: _task(description="x", size="M"),
            run_fn=run_fn,
        )
        self.assertEqual(result.action, "skipped-existing")
        self.assertEqual(result.existing_size, "M")
        self.assertIsNone(result.estimated_size)
        self.assertTrue(result.ok)
        self.assertEqual(calls, [])

    def test_skips_when_size_in_custom_fields(self) -> None:
        result = size_task(
            "001.001-T",
            fetch_fn=lambda tid, cwd: {"custom_fields": {"size": "L"}},
            run_fn=lambda argv, **kw: _FakeProc(),
        )
        self.assertEqual(result.action, "skipped-existing")
        self.assertEqual(result.existing_size, "L")

    def test_writes_back_with_safe_argv(self) -> None:
        captured: dict = {}

        def run_fn(argv, **kwargs):
            captured["argv"] = list(argv)
            captured["shell"] = kwargs.get("shell")
            return _FakeProc(returncode=0)

        result = size_task(
            "001.001-T",
            fetch_fn=lambda tid, cwd: _task(description="Add a feature with tests."),
            run_fn=run_fn,
        )
        self.assertEqual(result.action, "written")
        self.assertIn(result.estimated_size, SIZES)
        self.assertEqual(
            captured["argv"],
            ["backlogit", "update", "001.001-T", "--size", result.estimated_size],
        )
        self.assertFalse(captured["shell"])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.ok)

    def test_argv_arity_is_fixed_against_injection(self) -> None:
        captured: dict = {}

        def run_fn(argv, **kwargs):
            captured["argv"] = list(argv)
            return _FakeProc()

        malicious = "001.001-T; rm -rf / && echo pwned"
        result = size_task(
            malicious,
            fetch_fn=lambda tid, cwd: _task(description="x"),
            run_fn=run_fn,
        )
        self.assertEqual(len(captured["argv"]), 5)
        self.assertEqual(captured["argv"][2], malicious)

    def test_dry_run_does_not_invoke_subprocess(self) -> None:
        calls = []

        def run_fn(argv, **kwargs):  # pragma: no cover - must not be called
            calls.append(argv)
            return _FakeProc()

        result = size_task(
            "001.001-T",
            fetch_fn=lambda tid, cwd: _task(description="Add a feature."),
            run_fn=run_fn,
            dry_run=True,
        )
        self.assertEqual(result.action, "dry-run")
        self.assertIn(result.estimated_size, SIZES)
        self.assertEqual(result.argv[0], "backlogit")
        self.assertTrue(result.ok)
        self.assertEqual(calls, [])

    def test_missing_binary_is_config_failure_not_raise(self) -> None:
        def run_fn(argv, **kwargs):
            raise FileNotFoundError(2, "No such file or directory", "backlogit")

        result = size_task(
            "001.001-T",
            fetch_fn=lambda tid, cwd: _task(description="Add a feature."),
            run_fn=run_fn,
        )
        self.assertEqual(result.action, "error")
        self.assertTrue(result.missing_binary)
        self.assertFalse(result.ok)
        self.assertIn("backlogit", result.stderr)

    def test_backlogit_rejection_is_error_not_raise(self) -> None:
        def run_fn(argv, **kwargs):
            return _FakeProc(
                returncode=1,
                stderr='Error: artifact type "task" does not define a size field',
            )

        result = size_task(
            "001.001-T",
            fetch_fn=lambda tid, cwd: _task(description="Add a feature."),
            run_fn=run_fn,
        )
        self.assertEqual(result.action, "error")
        self.assertEqual(result.exit_code, 1)
        self.assertFalse(result.ok)
        self.assertIn("does not define a size field", result.stderr)

    def test_timeout_is_error_not_raise(self) -> None:
        import subprocess

        def run_fn(argv, **kwargs):
            raise subprocess.TimeoutExpired(cmd=argv, timeout=30)

        result = size_task(
            "001.001-T",
            fetch_fn=lambda tid, cwd: _task(description="Add a feature."),
            run_fn=run_fn,
        )
        self.assertEqual(result.action, "error")
        self.assertFalse(result.ok)
        self.assertIn("timed out", result.stderr)

    def test_fetch_failure_degrades_gracefully(self) -> None:
        def fetch_fn(tid, cwd):
            raise FileNotFoundError(2, "No such file or directory", "backlogit")

        result = size_task("001.001-T", fetch_fn=fetch_fn, run_fn=lambda a, **k: _FakeProc())
        self.assertEqual(result.action, "error")
        self.assertTrue(result.missing_binary)
        self.assertFalse(result.ok)

    def test_result_to_dict_is_serializable(self) -> None:
        result = size_task(
            "001.001-T",
            fetch_fn=lambda tid, cwd: _task(description="Add a feature."),
            run_fn=lambda argv, **kw: _FakeProc(),
        )
        payload = result.to_dict()
        self.assertEqual(payload["task_id"], "001.001-T")
        self.assertEqual(payload["action"], "written")
        self.assertIn("estimated_size", payload)


class FetchTaskDefaultFetcherTests(unittest.TestCase):
    """Directly exercise the default ``fetch_task`` subprocess fetcher.

    Every other test injects ``fetch_fn`` or patches ``sizing.fetch_task``, so
    the default fetcher's argv construction, non-zero-return ``RuntimeError``
    branch, and ``json.loads(stdout)`` success path are otherwise uncovered.
    These patch ``subprocess.run`` to keep the tests hermetic (no real backlogit).
    """

    def test_parses_json_on_success(self) -> None:
        proc = _FakeProc(returncode=0, stdout='{"id": "001.001-T", "artifact_type": "task"}')
        with mock.patch("autoharness.gates.sizing.subprocess.run", return_value=proc) as run_mock:
            result = fetch_task("001.001-T")
        self.assertEqual(result, {"id": "001.001-T", "artifact_type": "task"})
        argv = run_mock.call_args.args[0]
        self.assertEqual(argv, [DEFAULT_BACKLOGIT, "get", "001.001-T", "--format", "json"])
        self.assertFalse(run_mock.call_args.kwargs["shell"])

    def test_raises_runtimeerror_with_stderr_on_nonzero_return(self) -> None:
        proc = _FakeProc(returncode=1, stdout="", stderr="  task not found  ")
        with mock.patch("autoharness.gates.sizing.subprocess.run", return_value=proc):
            with self.assertRaises(RuntimeError) as ctx:
                fetch_task("404.404-T")
        self.assertEqual(str(ctx.exception), "task not found")

    def test_runtimeerror_fallback_message_when_stderr_empty(self) -> None:
        proc = _FakeProc(returncode=2, stdout="", stderr="")
        with mock.patch("autoharness.gates.sizing.subprocess.run", return_value=proc):
            with self.assertRaises(RuntimeError) as ctx:
                fetch_task("404.404-T")
        self.assertEqual(str(ctx.exception), "backlogit get 404.404-T failed")

    def test_passes_cwd_and_backlogit_bin_through(self) -> None:
        proc = _FakeProc(returncode=0, stdout="{}")
        with mock.patch("autoharness.gates.sizing.subprocess.run", return_value=proc) as run_mock:
            fetch_task("001.001-T", cwd=Path("workspace"), backlogit_bin="C:/Tools/backlogit.exe")
        argv = run_mock.call_args.args[0]
        self.assertEqual(argv[0], "C:/Tools/backlogit.exe")
        self.assertEqual(run_mock.call_args.kwargs["cwd"], str(Path("workspace")))


class SizingBoundaryTests(unittest.TestCase):
    def test_module_does_not_import_install_or_tune(self) -> None:
        import autoharness.gates.sizing as sizing

        source = __import__("inspect").getsource(sizing)
        for forbidden in ("verify_workspace", "schema_contracts", "install", "tune"):
            self.assertNotIn(f"import {forbidden}", source)
            self.assertNotIn(f"from autoharness.{forbidden}", source)

    def test_only_the_standard_library_and_typing_are_imported(self) -> None:
        import autoharness.gates.sizing as sizing

        # The estimator/write-back must not depend on other gates.* internals.
        source = __import__("inspect").getsource(sizing)
        self.assertNotIn("from autoharness.gates.", source)


if __name__ == "__main__":
    unittest.main()
