"""``cascade-close`` orchestration tests (192.006-T, plan unit A3).

Four table-driven scenarios (plan ``### A3``):

1. pass and argv log: exactly two A2a probe argvs (step 3 and the step 5
   re-probe) and one fixed ship argv (with ``--cwd``), no ``--version`` argv,
   no archive call (re-plan cycle-1 R7);
2. the pre-spawn fail-closed table (exit 3, 4, 7; the ship sentinel is
   never written);
3. the ``--classify-only`` record hand-off (re-plan cycle-1 R1; Copilot PR
   #481 T6);
4. the post-spawn failure table (exit 5, 6, 8).

A fake ``backlogit`` (the A3a ``argv_prefix`` seam: ``sys.executable`` plus a
script) logs every argv, answers the ``version`` probe from a per-call
script, simulates the cascade's archive moves, emits a canned JSON-RPC
envelope, and writes a sentinel file when ``shipment ship`` runs. Everything
lives in a Git-ignored scratch workspace inside the repository
(constitution IV); no real backlogit binary is spawned.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

from test_shipment_close_observation import make_scratch_backlog, write_artifact

from autoharness.gates.cascade_evidence import (
    build_evidence_path,
    validate_evidence_record,
)
from autoharness.shipment_close import (
    EXIT_INPUT,
    EXIT_INVOCATION_INDETERMINATE,
    EXIT_LOCKED,
    EXIT_OK,
    EXIT_POST_WRITE_FAILED,
    EXIT_POSTCONDITION_FAILED,
    EXIT_REVALIDATION_DRIFT,
    EXIT_SAFE_CLOSE_SELECTED,
    command,
    engine_probe,
)
from autoharness.shipment_close.persist import PersistError
from autoharness.shipment_close.preclose import run_classify_only
from autoharness.shipment_close.runner import ResolvedBinary, hash_binary

_SHIPMENT = "900-S"
_FEATURE = "600-F"
_TASK = "600.001-T"
_DL = "600-DL"
_SHA = "bd824b97999832aa38122f2f70d300ebbb5d2e09"
_VERIFIED = {"version": "1.11.0", "commit": "131577c"}
_UNVERIFIED = {"version": "1.10.1", "commit": "131577c"}

_FAKE_BACKLOGIT = r'''
import json, pathlib, sys, time

HERE = pathlib.Path(__file__).resolve().parent
control = json.loads((HERE / "control.json").read_text(encoding="utf-8"))
args = sys.argv[1:]
with open(HERE / "argv.log", "a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\n")

if args[:1] == ["version"]:
    counter = HERE / "probe-count"
    count = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(count + 1))
    probes = control["probes"]
    probe = probes[min(count, len(probes) - 1)]
    if probe.get("sleep"):
        time.sleep(probe["sleep"])
    sys.stdout.write(json.dumps({"version": probe["version"], "commit": probe.get("commit")}))
    sys.exit(probe.get("exit", 0))

if "shipment" in args and "ship" in args:
    (HERE / "ship.sentinel").write_text("ran", encoding="utf-8")
    root = pathlib.Path(args[args.index("--cwd") + 1])
    backlog = root / ".backlogit"
    ship = control["ship"]
    for artifact_id in ship.get("archive", []):
        source = backlog / "queue" / (artifact_id + ".md")
        lines = []
        for line in source.read_text(encoding="utf-8").splitlines():
            if line.startswith("status: "):
                old = line[len("status: "):]
                lines.append("status: archived")
                lines.append("archived_status: " + ("shipped" if artifact_id.endswith("-S") else old))
            else:
                lines.append(line)
        (backlog / "archive" / (artifact_id + ".md")).write_text("\n".join(lines) + "\n", encoding="utf-8")
        source.unlink()
    for relative in ship.get("modify", []):
        with open(root / relative, "a", encoding="utf-8") as handle:
            handle.write("modified during the ship call\n")
    sys.stderr.write(ship.get("stderr", ""))
    sys.stdout.write(json.dumps(ship["envelope"]))
    sys.exit(ship.get("exit", 0))

sys.exit(99)
'''


def _envelope(archived: list[str], *, returned: list[str] | None = None) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "archived_ids": archived,
            "returned_ids": returned or [],
            "shipment_id": _SHIPMENT,
            "shipment_status": "shipped",
            "commit_sha": _SHA,
        },
    }


_ARCHIVED = [_FEATURE, _TASK, _SHIPMENT]


def _default_ship() -> dict:
    return {"archive": list(_ARCHIVED), "envelope": _envelope(list(_ARCHIVED))}


def _write_shipment(backlog: Path, items: list[str]) -> None:
    lines = ["---", f"id: {_SHIPMENT}", "artifact_type: shipment", "status: active", "custom_fields:", "    items:"]
    lines += [f"        - {item}" for item in items]
    lines += ["---", f"# {_SHIPMENT}"]
    (backlog / "queue" / f"{_SHIPMENT}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _cascade_fixture(test: unittest.TestCase) -> Path:
    """A root feature whose only out-of-manifest descendant is archived; one linked deliberation."""

    backlog = make_scratch_backlog(test)
    write_artifact(backlog, "queue", _FEATURE, "feature", status="done")
    write_artifact(
        backlog,
        "queue",
        _TASK,
        "task",
        parent_id=_FEATURE,
        status="done",
        extra=f"custom_fields:\n    source_deliberation_id: {_DL}",
    )
    write_artifact(backlog, "archive", "600.002-T", "task", parent_id=_FEATURE, status="archived")
    write_artifact(backlog, "queue", _DL, "deliberation", status="accepted")
    _write_shipment(backlog, [_FEATURE, _TASK])
    return backlog


class _Harness:
    """One scratch workspace plus the fake backlogit and its control file."""

    def __init__(self, test: unittest.TestCase, *, probes: list[dict], ship: dict | None = None) -> None:
        self.backlog = _cascade_fixture(test)
        self.root = self.backlog.parent
        self.fakes = self.root / "fakes"
        self.fakes.mkdir()
        self.script = self.fakes / "backlogit_fake.py"
        self.script.write_text(_FAKE_BACKLOGIT, encoding="utf-8")
        self.set_control(probes=probes, ship=ship or _default_ship())
        self.resolved = ResolvedBinary(
            binary_path=str(self.script),
            binary_sha256=hash_binary(self.script),
            argv_prefix=(sys.executable, str(self.script)),
        )
        self.evidence = build_evidence_path(self.root, _SHIPMENT, _FEATURE)

    def set_control(self, *, probes: list[dict], ship: dict | None = None) -> None:
        current = {}
        control = self.fakes / "control.json"
        if control.exists():
            current = json.loads(control.read_text(encoding="utf-8"))
        current["probes"] = probes
        if ship is not None:
            current["ship"] = ship
        control.write_text(json.dumps(current), encoding="utf-8")
        counter = self.fakes / "probe-count"
        if counter.exists():
            counter.unlink()

    def argv_log(self) -> list[list[str]]:
        log = self.fakes / "argv.log"
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]

    def clear_log(self) -> None:
        log = self.fakes / "argv.log"
        if log.exists():
            log.unlink()

    @property
    def shipped(self) -> bool:
        return (self.fakes / "ship.sentinel").exists()

    def record(self) -> dict | None:
        return json.loads(self.evidence.read_text(encoding="utf-8")) if self.evidence.exists() else None

    def run(self, **kwargs: object) -> command.CascadeCloseOutcome:
        return command.run_cascade_close(
            self.root,
            _SHIPMENT,
            _FEATURE,
            kwargs.pop("sha", _SHA),
            message=kwargs.pop("message", "close 900-S"),
            author=kwargs.pop("author", "ship-agent"),
            resolved=self.resolved,
            timeout=60,
            **kwargs,
        )

    def classify_only(self):
        return run_classify_only(self.root, _SHIPMENT, _FEATURE, _SHA, resolved=self.resolved)


def _probe_argvs(log: list[list[str]]) -> list[list[str]]:
    return [argv for argv in log if argv[:1] == ["version"]]


def _ship_argvs(log: list[list[str]]) -> list[list[str]]:
    return [argv for argv in log if "ship" in argv]


class PassAndArgvLogTests(unittest.TestCase):
    """Scenario 1: a pass case with exactly two probe argvs and one fixed ship argv."""

    def test_pass_and_argv_log(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_OK, (outcome.message, outcome.failures))
        self.assertEqual(outcome.phase_written, "post_close")
        self.assertEqual(outcome.selected_close_path, "cascade")
        self.assertEqual(outcome.postcondition_verdict, "pass")
        self.assertEqual(outcome.evidence_path, harness.evidence)

        log = harness.argv_log()
        self.assertEqual(_probe_argvs(log), [["version", "--no-update-check", "--format", "json"]] * 2)
        self.assertEqual(
            _ship_argvs(log),
            [
                [
                    "--no-update-check",
                    "--jsonrpc",
                    "--cwd",
                    str(harness.root.resolve()),
                    "shipment",
                    "ship",
                    _SHIPMENT,
                    "--sha",
                    _SHA,
                    "--message",
                    "close 900-S",
                    "--author",
                    "ship-agent",
                ]
            ],
        )
        self.assertEqual(len(log), 3)
        self.assertFalse(any("--version" in argv for argv in log))
        self.assertFalse(any("archive" in argv for argv in log))

        record = harness.record()
        self.assertEqual(record["phase"], "post_close")
        self.assertEqual(record["invocation"]["mutation_state"], "completed")
        self.assertEqual(record["invocation"]["exit_code"], 0)
        self.assertEqual(record["invocation"]["argv_redacted"][-12:], _ship_argvs(log)[0][1:])
        self.assertEqual(record["post_close"]["linked_deliberation_drift"], [])
        self.assertTrue(record["post_close"]["disposition_byte_identical"])
        self.assertEqual(
            validate_evidence_record(record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path="cascade"), []
        )
        # The command never archives a deliberation (038-DL D3a).
        self.assertTrue((harness.backlog / "queue" / f"{_DL}.md").exists())

    def test_invalid_message_and_author_exit_2(self) -> None:
        for label, kwargs in (
            ("empty message", {"message": ""}),
            ("newline in author", {"author": "a\nb"}),
            ("NUL in message", {"message": "a\x00b"}),
            ("overlong author", {"author": "x" * 1025}),
        ):
            with self.subTest(label):
                harness = _Harness(self, probes=[_VERIFIED])
                outcome = harness.run(**kwargs)
                self.assertEqual(outcome.exit_code, 2, outcome.message)
                self.assertEqual(harness.argv_log(), [])
                self.assertIsNone(harness.record())


class PreSpawnFailClosedTests(unittest.TestCase):
    """Scenario 2: every pre-spawn refusal leaves the ship sentinel unwritten."""

    def test_unverified_engine_exits_3(self) -> None:
        harness = _Harness(self, probes=[_UNVERIFIED])
        outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_SAFE_CLOSE_SELECTED, outcome.message)
        self.assertFalse(harness.shipped)
        record = harness.record()
        self.assertEqual(record["phase"], "pre_close")
        self.assertEqual(record["pre_close"]["classifier_verdict"], "CASCADE")
        self.assertEqual(record["pre_close"]["close_path_selection"]["selected_close_path"], "safe_close")
        self.assertEqual(outcome.selected_close_path, "safe_close")
        self.assertEqual(outcome.phase_written, "pre_close")

    def test_revalidation_drift_table(self) -> None:
        def commit_changes(harness: _Harness) -> None:
            harness.set_control(probes=[_VERIFIED, {"version": "1.11.0", "commit": "2222222"}])

        def reprobe_times_out(harness: _Harness) -> None:
            harness.set_control(probes=[_VERIFIED, {"version": "1.11.0", "commit": "131577c", "sleep": 20}])

        rows = [("commit changes between step 3 and step 5", commit_changes, None, "pre_close.engine_semantics")]
        rows.append(("the step 5 re-probe times out", reprobe_times_out, None, "pre_close.engine_semantics"))

        def inject_drift(harness: _Harness):
            real_write = command.write_evidence_atomic

            def write(path, record, **kwargs):
                real_write(path, record, **kwargs)
                if record.get("phase") == "pre_close":
                    write_artifact(harness.backlog, "queue", _TASK, "task", parent_id=_FEATURE, status="active")

            return mock.patch.object(command, "write_evidence_atomic", side_effect=write)

        def binary_changes(harness: _Harness):
            real_preclose = command.run_preclose
            calls = []

            def preclose(*args, **kwargs):
                result = real_preclose(*args, **kwargs)
                calls.append(1)
                if len(calls) == 2:
                    with open(harness.script, "a", encoding="utf-8") as handle:
                        handle.write("# changed\n")
                return result

            return mock.patch.object(command, "run_preclose", side_effect=preclose)

        rows.append(("drift injected between steps 4 and 5", None, inject_drift, "pre_close.manifest_members"))
        rows.append(("binary hash changes before the spawn", None, binary_changes, "SHA-256 changed"))

        for label, setup, patcher, reason in rows:
            with self.subTest(label):
                harness = _Harness(self, probes=[_VERIFIED])
                if setup is not None:
                    setup(harness)
                with mock.patch.object(engine_probe, "PROBE_TIMEOUT_SECONDS", 2):
                    if patcher is not None:
                        with patcher(harness):
                            outcome = harness.run()
                    else:
                        outcome = harness.run()
                self.assertEqual(outcome.exit_code, EXIT_REVALIDATION_DRIFT, outcome.message)
                self.assertIn(reason, outcome.message)
                self.assertFalse(harness.shipped)
                self.assertEqual(_ship_argvs(harness.argv_log()), [])
                self.assertEqual(harness.record()["phase"], "pre_close")

    def test_existing_invoking_record_exits_7(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        harness.evidence.parent.mkdir(parents=True, exist_ok=True)
        invoking = {
            "phase": "invoking",
            "run_id": "0123456789abcdef0123456789abcdef",
            "shipment_id": _SHIPMENT,
            "feature_id": _FEATURE,
        }
        harness.evidence.write_text(json.dumps(invoking) + "\n", encoding="utf-8")
        before = harness.evidence.read_bytes()
        outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_LOCKED, outcome.message)
        self.assertEqual(harness.argv_log(), [])
        self.assertFalse(harness.shipped)
        self.assertEqual(harness.evidence.read_bytes(), before)


class ClassifyOnlyHandOffTests(unittest.TestCase):
    """Scenario 3: a cascade-selected --classify-only record is compared, never overwritten on a difference."""

    def _classified(self) -> _Harness:
        harness = _Harness(self, probes=[_VERIFIED])
        result = harness.classify_only()
        self.assertEqual(result.exit_code, EXIT_OK, result.message)
        self.assertEqual(harness.record()["pre_close"]["close_path_selection"]["selected_close_path"], "cascade")
        harness.clear_log()
        return harness

    def test_difference_exits_4_and_keeps_the_record(self) -> None:
        def unverified(harness: _Harness) -> None:
            harness.set_control(probes=[_UNVERIFIED])

        def disposition_changes(harness: _Harness) -> None:
            with open(harness.backlog / "queue" / f"{_DL}.md", "a", encoding="utf-8") as handle:
                handle.write("edited\n")

        def different_sha(harness: _Harness) -> dict:
            return {"sha": "a" * 40}

        for label, change, reason in (
            ("probe answers 1.10.1", unverified, "pre_close.close_path_selection"),
            ("disposition snapshot changes", disposition_changes, "pre_close.linked_deliberation_disposition"),
            ("a different --sha", different_sha, "merge_commit_sha"),
        ):
            with self.subTest(label):
                harness = self._classified()
                before = harness.evidence.read_bytes()
                kwargs = change(harness) or {}
                outcome = harness.run(**kwargs)
                self.assertEqual(outcome.exit_code, EXIT_REVALIDATION_DRIFT, outcome.message)
                self.assertIn(reason, outcome.message)
                self.assertEqual(harness.evidence.read_bytes(), before)
                self.assertFalse(harness.shipped)
                self.assertEqual(_ship_argvs(harness.argv_log()), [])

    def test_exact_match_restamps_through_the_takeover(self) -> None:
        harness = self._classified()
        classified = harness.record()
        captured = []
        real_write = command.write_evidence_atomic

        def write(path, record, **kwargs):
            if record.get("phase") == "pre_close":
                captured.append((json.loads(json.dumps(record)), kwargs))
            return real_write(path, record, **kwargs)

        with mock.patch.object(command, "write_evidence_atomic", side_effect=write):
            outcome = harness.run(run_id="f" * 32)
        self.assertEqual(outcome.exit_code, EXIT_OK, (outcome.message, outcome.failures))
        self.assertEqual(len(captured), 1)
        restamped, kwargs = captured[0]
        self.assertEqual(kwargs["takeover_from_run_id"], classified["run_id"])
        self.assertEqual(kwargs["owner_run_id"], "f" * 32)
        self.assertEqual(restamped["run_id"], "f" * 32)
        for record in (restamped, classified):
            record.pop("run_id")
            record["pre_close"].pop("captured_at")
        self.assertEqual(restamped, classified)
        self.assertEqual(harness.record()["run_id"], "f" * 32)
        self.assertEqual(harness.record()["phase"], "post_close")

    def test_stale_takeover_exits_4(self) -> None:
        harness = self._classified()
        before = harness.evidence.read_bytes()
        real_check = command.check_existing_record

        def stale(lock, *, mode):
            record = dict(real_check(lock, mode=mode))
            record["run_id"] = "e" * 32
            return record

        with mock.patch.object(command, "check_existing_record", side_effect=stale):
            outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_REVALIDATION_DRIFT, outcome.message)
        self.assertIn("takeover refused", outcome.message)
        self.assertEqual(harness.evidence.read_bytes(), before)
        self.assertFalse(harness.shipped)


class PostSpawnFailureTests(unittest.TestCase):
    """Scenario 4: post-spawn failures always leave a post_close record (except exit 8)."""

    def test_post_spawn_failure_table(self) -> None:
        rows = [
            (
                "non-empty returned_ids",
                {"archive": list(_ARCHIVED), "envelope": _envelope(list(_ARCHIVED), returned=["600.009-T"])},
                EXIT_POSTCONDITION_FAILED,
            ),
            (
                "the ship call modifies a disposition-set deliberation",
                {**_default_ship(), "modify": [f".backlogit/queue/{_DL}.md"]},
                EXIT_POSTCONDITION_FAILED,
            ),
            (
                "backlogit exits 1 with stderr",
                {
                    "archive": [],
                    "envelope": {"jsonrpc": "2.0", "id": 1, "error": {"code": 6, "message": "gate blocked"}},
                    "exit": 1,
                    "stderr": "failure detail token=supersecretvalue123\n",
                },
                EXIT_INVOCATION_INDETERMINATE,
            ),
        ]
        for label, ship, expected in rows:
            with self.subTest(label):
                harness = _Harness(self, probes=[_VERIFIED], ship=ship)
                outcome = harness.run()
                self.assertEqual(outcome.exit_code, expected, (outcome.message, outcome.failures))
                self.assertTrue(harness.shipped)
                record = harness.record()
                self.assertEqual(record["phase"], "post_close")
                self.assertEqual(record["post_close"]["postcondition_verdict"], "fail")
                self.assertEqual(outcome.phase_written, "post_close")
                if label.startswith("the ship call"):
                    kinds = {entry["kind"] for entry in record["post_close"]["linked_deliberation_drift"]}
                    self.assertIn("modified", kinds)
                    self.assertFalse(record["post_close"]["disposition_byte_identical"])
                if label.startswith("backlogit exits"):
                    stderr = record["invocation"]["stderr"]
                    self.assertIn("failure detail", stderr["excerpt"])
                    self.assertNotIn("supersecretvalue123", stderr["excerpt"])
                    self.assertTrue(stderr["redaction_applied"])
                    self.assertEqual(record["invocation"]["exit_code"], 1)

    def test_post_close_write_failure_exits_8(self) -> None:
        harness = _Harness(self, probes=[_VERIFIED])
        real_write = command.write_evidence_atomic

        def write(path, record, **kwargs):
            if record.get("phase") == "post_close":
                raise PersistError(2, "simulated post-close write failure")
            return real_write(path, record, **kwargs)

        with mock.patch.object(command, "write_evidence_atomic", side_effect=write):
            outcome = harness.run()
        self.assertEqual(outcome.exit_code, EXIT_POST_WRITE_FAILED, outcome.message)
        self.assertTrue(harness.shipped)
        self.assertEqual(harness.record()["phase"], "invoking")
        self.assertEqual(outcome.phase_written, "invoking")


class InvokingWriteFailureTests(unittest.TestCase):
    """198-S local review: no mutating call without a persisted ``invoking`` record."""

    def test_invoking_write_failure_exits_2_and_never_ships(self) -> None:
        for label, error in (
            ("a persistence refusal", PersistError(2, "simulated invoking write failure")),
            ("a raw OS error", OSError(28, "No space left on device")),
        ):
            with self.subTest(label):
                harness = _Harness(self, probes=[_VERIFIED])
                real_write = command.write_evidence_atomic
                phases: list[str] = []

                def write(path, record, *, _error=error, _phases=phases, _real=real_write, **kwargs):
                    _phases.append(record.get("phase"))
                    if record.get("phase") == "invoking":
                        raise _error
                    return _real(path, record, **kwargs)

                with mock.patch.object(command, "write_evidence_atomic", side_effect=write):
                    outcome = harness.run()
                self.assertEqual(outcome.exit_code, EXIT_INPUT, outcome.message)
                self.assertIn("invoking", phases)
                self.assertNotIn("post_close", phases)
                self.assertFalse(harness.shipped, "backlogit shipment ship ran without a persisted invoking record")
                self.assertEqual(_ship_argvs(harness.argv_log()), [])
                self.assertNotEqual(outcome.phase_written, "invoking")
                record = harness.record()
                self.assertIsNotNone(record)
                self.assertEqual(record["phase"], "pre_close")


if __name__ == "__main__":
    unittest.main()
