"""Pre-close snapshot and ``--classify-only`` tests (192.003-T, plan unit A2).

Four table-driven scenarios (plan ``### A2``):

1. the selection table: one CASCADE fixture under a fake ``1.11.0`` probe
   (VERIFIED, selected ``cascade``, exit 0) and a fake ``1.10.1`` probe
   (UNVERIFIED, selected ``safe_close``, the A2b observation set holds the
   linked deliberation's record paths, exit 3);
2. the disposition-snapshot table (re-plan R5, cycle-1 R2, H10);
3. the fail-closed input table (exit 2, no record);
4. lock precedence: an existing ``invoking`` record returns exit 7 before
   any classification (AN-F02).

The engine probe is faked through the A2a ``EngineProbe`` result, so no
backlogit binary is spawned. Fixtures use the record builder of
``tests/test_shipment_close_observation.py`` (the classification-test
builder) in a Git-ignored scratch workspace inside the repository
(constitution IV). No fixture builds a ``validated_linked_deliberations`` set
or asserts a linked deliberation in ``allowed_ids`` / ``required_ids``.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from test_shipment_close_observation import make_scratch_backlog, write_artifact

from autoharness.gates.cascade_evidence import build_evidence_path, validate_evidence_record
from autoharness.gates.shipment_closure import (
    EngineSemanticsVerdict,
    LinkedDeliberationDispositionPlan,
    assess_cascade_engine_semantics,
)
from autoharness.shipment_close import (
    EXIT_INPUT,
    EXIT_LOCKED,
    EXIT_OK,
    EXIT_SAFE_CLOSE_SELECTED,
    preclose,
)
from autoharness.shipment_close.engine_probe import EngineProbe
from autoharness.shipment_close.preclose import run_classify_only, run_preclose
from autoharness.shipment_close.runner import ResolvedBinary

_SHIPMENT = "900-S"
_SHA = "bd824b97999832aa38122f2f70d300ebbb5d2e09"
_RESOLVED = ResolvedBinary(binary_path="/opt/backlogit/backlogit", binary_sha256="0" * 64, argv_prefix=("backlogit",))


def _probe(version: str) -> EngineProbe:
    decision = assess_cascade_engine_semantics(
        version, probe_surface="cli", invocation_surface="cli", probed_commit="131577c"
    )
    return EngineProbe(decision=decision, invocation_surface="cli", version_excerpt=f'{{"version": "{version}"}}')


def _write_shipment(backlog: Path, items: list[str], *, status: str = "active", folder: str = "queue") -> None:
    lines = ["---", f"id: {_SHIPMENT}", "artifact_type: shipment", f"status: {status}", "custom_fields:", "    items:"]
    lines += [f"        - {item}" for item in items]
    lines += ["---", f"# {_SHIPMENT}"]
    target = backlog / folder / f"{_SHIPMENT}.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _cascade_fixture(test: unittest.TestCase) -> Path:
    """A root feature whose only out-of-manifest descendant is archived; one linked deliberation."""

    backlog = make_scratch_backlog(test)
    write_artifact(backlog, "queue", "600-F", "feature", status="done")
    write_artifact(
        backlog,
        "queue",
        "600.001-T",
        "task",
        parent_id="600-F",
        status="done",
        extra="custom_fields:\n    source_deliberation_id: 600-DL",
    )
    write_artifact(backlog, "archive", "600.002-T", "task", parent_id="600-F", status="archived")
    write_artifact(backlog, "queue", "600-DL", "deliberation", status="accepted")
    _write_shipment(backlog, ["600-F", "600.001-T"])
    return backlog


def _task_only_fixture(test: unittest.TestCase, *, deliberation_status: str = "active") -> Path:
    """A task-only manifest (classifier SAFE_CLOSE) linking a deliberation under the feature."""

    backlog = make_scratch_backlog(test)
    write_artifact(backlog, "queue", "610-F", "feature")
    write_artifact(
        backlog,
        "queue",
        "610.001-T",
        "task",
        parent_id="610-F",
        status="done",
        extra="custom_fields:\n    source_deliberation_id: 610-DL",
    )
    write_artifact(backlog, "queue", "610.002-T", "task", parent_id="610-F", status="queued")
    write_artifact(backlog, "queue", "610-DL", "deliberation", parent_id="610-F", status=deliberation_status)
    _write_shipment(backlog, ["610.001-T"])
    return backlog


def _classify(backlog: Path, feature_id: str, version: str = "1.11.0", **kwargs: object):
    probe = mock.Mock(return_value=_probe(version))
    with mock.patch.object(preclose, "probe_engine_semantics", probe):
        result = run_classify_only(backlog.parent, _SHIPMENT, feature_id, kwargs.pop("sha", _SHA), resolved=_RESOLVED)
    return result, probe


def _record(backlog: Path, feature_id: str) -> dict | None:
    path = build_evidence_path(backlog.parent, _SHIPMENT, feature_id)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _dispositions(record: dict) -> dict[str, dict]:
    plan = record["pre_close"]["linked_deliberation_disposition"]
    return {entry["deliberation_id"]: entry for entry in plan["dispositions"]}


class SelectionTests(unittest.TestCase):
    """Scenario 1: VERIFIED selects cascade (exit 0); UNVERIFIED fails closed to safe_close (exit 3)."""

    def test_selection_table(self) -> None:
        with self.subTest("1.11.0: VERIFIED, cascade, exit 0"):
            backlog = _cascade_fixture(self)
            result, probe = _classify(backlog, "600-F", "1.11.0")
            self.assertEqual(result.exit_code, EXIT_OK, result.message)
            probe.assert_called_once()
            record = _record(backlog, "600-F")
            pre_close = record["pre_close"]
            self.assertEqual(record["phase"], "pre_close")
            self.assertEqual(record["merge_commit_sha"], _SHA)
            self.assertEqual(record["tool"]["binary_path"], _RESOLVED.binary_path)
            self.assertEqual(record["tool"]["binary_sha256"], _RESOLVED.binary_sha256)
            self.assertEqual(pre_close["classifier_verdict"], "CASCADE")
            self.assertEqual(pre_close["qualifying_feature_ids"], ["600-F"])
            self.assertEqual(pre_close["engine_semantics"]["verdict"], "VERIFIED")
            self.assertEqual(pre_close["engine_semantics"]["invocation_surface"], "cli")
            self.assertEqual(pre_close["close_path_selection"]["selected_close_path"], "cascade")
            self.assertEqual(pre_close["shipment_record"]["location"], "queue")
            self.assertEqual(pre_close["shipment_record"]["declared_status"], "active")
            members = {member["id"]: member for member in pre_close["manifest_members"]}
            self.assertEqual(set(members), {"600-F", "600.001-T"})
            self.assertEqual(members["600.001-T"]["parent_id"], "600-F")
            self.assertEqual(members["600.001-T"]["artifact_type"], "task")
            self.assertEqual(len(members["600.001-T"]["sha256"]), 64)
            descendants = {entry["id"]: entry for entry in pre_close["out_of_manifest_descendants"]}
            self.assertEqual(set(descendants), {"600.002-T"})
            self.assertEqual(descendants["600.002-T"]["location"], "archive")
            self.assertEqual(_dispositions(record)["600-DL"]["outcome"], "archive")
            self.assertNotIn("observation_set", pre_close)
            self.assertNotIn("linked_deliberations", pre_close)
            problems = validate_evidence_record(record, shipment_id=_SHIPMENT, feature_id="600-F", close_path="cascade")
            self.assertEqual(
                sorted(problem.split(":")[0] for problem in problems),
                ["record.invocation", "record.phase", "record.post_close"],
            )

        with self.subTest("1.10.1: UNVERIFIED, safe_close, exit 3, deliberation observed"):
            backlog = _cascade_fixture(self)
            result, _ = _classify(backlog, "600-F", "1.10.1")
            self.assertEqual(result.exit_code, EXIT_SAFE_CLOSE_SELECTED, result.message)
            record = _record(backlog, "600-F")
            pre_close = record["pre_close"]
            self.assertEqual(pre_close["classifier_verdict"], "CASCADE")
            self.assertEqual(pre_close["engine_semantics"]["verdict"], "UNVERIFIED")
            self.assertEqual(pre_close["close_path_selection"]["selected_close_path"], "safe_close")
            self.assertEqual(_dispositions(record)["600-DL"]["outcome"], "retained_engine_unverified")
            observed = {(entry["id"], entry["path"]) for entry in pre_close["observation_set"]}
            self.assertEqual(
                observed,
                {("600.002-T", ".backlogit/archive/600.002-T.md"), ("600-DL", ".backlogit/queue/600-DL.md")},
            )
            self.assertEqual(
                validate_evidence_record(record, shipment_id=_SHIPMENT, feature_id="600-F", close_path="safe_close"),
                [],
            )


class DispositionSnapshotTests(unittest.TestCase):
    """Scenario 2: the planner snapshot is recorded; retained_* never halts; planning_error exits 2."""

    def test_disposition_snapshot_table(self) -> None:
        with self.subTest("live deliberation: planned outcome, absent from a VERIFIED observation set"):
            backlog = _task_only_fixture(self)
            result, _ = _classify(backlog, "610-F")
            self.assertEqual(result.exit_code, EXIT_SAFE_CLOSE_SELECTED, result.message)
            record = _record(backlog, "610-F")
            self.assertEqual(_dispositions(record)["610-DL"]["outcome"], "retained_live_status")
            observed = {entry["id"] for entry in record["pre_close"]["observation_set"]}
            self.assertEqual(observed, {"610-F", "610.002-T"})
            self.assertEqual(
                validate_evidence_record(record, shipment_id=_SHIPMENT, feature_id="610-F", close_path="safe_close"),
                [],
            )

        with self.subTest("explicit-member deliberation is absent from the snapshot (H10)"):
            backlog = _task_only_fixture(self)
            _write_shipment(backlog, ["610.001-T", "610-DL"])
            result, _ = _classify(backlog, "610-F")
            self.assertEqual(result.exit_code, EXIT_SAFE_CLOSE_SELECTED, result.message)
            record = _record(backlog, "610-F")
            self.assertNotIn("610-DL", _dispositions(record))
            self.assertIn("610-DL", {member["id"] for member in record["pre_close"]["manifest_members"]})

        with self.subTest("torn deliberation records retained_ambiguous and does not halt"):
            backlog = _task_only_fixture(self)
            write_artifact(backlog, "archive", "610-DL", "deliberation", parent_id="610-F", status="archived")
            result, _ = _classify(backlog, "610-F")
            self.assertEqual(result.exit_code, EXIT_SAFE_CLOSE_SELECTED, result.message)
            record = _record(backlog, "610-F")
            self.assertEqual(_dispositions(record)["610-DL"]["outcome"], "retained_ambiguous")

        with self.subTest("planner planning_error exits 2 with no record"):
            backlog = _task_only_fixture(self)
            failed = LinkedDeliberationDispositionPlan(
                shipment_id=_SHIPMENT,
                engine=None,
                dispositions=(),
                unresolved_references=(),
                planning_error="linked-deliberation planning failed: injected",
            )
            with mock.patch.object(preclose, "compute_linked_deliberation_disposition", return_value=failed):
                result, _ = _classify(backlog, "610-F")
            self.assertEqual(result.exit_code, EXIT_INPUT)
            self.assertIsNone(_record(backlog, "610-F"))


class FailClosedInputTests(unittest.TestCase):
    """Scenario 3: torn/duplicate members, a closed shipment, and a foreign feature exit 2."""

    def test_fail_closed_input_table(self) -> None:
        def torn(backlog: Path) -> None:
            write_artifact(backlog, "archive", "600.001-T", "task", parent_id="600-F", status="archived")

        def duplicate(backlog: Path) -> None:
            _write_shipment(backlog, ["600-F", "600.001-T", "600.001-T"])

        def shipped(backlog: Path) -> None:
            _write_shipment(backlog, ["600-F", "600.001-T"], status="shipped")

        def missing_member(backlog: Path) -> None:
            _write_shipment(backlog, ["600-F", "600.001-T", "600.009-T"])

        cases = [
            ("torn manifest member", torn, "600-F", _SHA),
            ("duplicate manifest member", duplicate, "600-F", _SHA),
            ("missing manifest member", missing_member, "600-F", _SHA),
            ("already-shipped shipment", shipped, "600-F", _SHA),
            ("feature outside the qualifying set", lambda backlog: None, "699-F", _SHA),
            ("short sha", lambda backlog: None, "600-F", _SHA[:12]),
            ("uppercase sha", lambda backlog: None, "600-F", _SHA.upper()),
            ("invalid feature id", lambda backlog: None, "600-X", _SHA),
        ]
        for name, mutate, feature_id, sha in cases:
            with self.subTest(name):
                backlog = _cascade_fixture(self)
                mutate(backlog)
                result, _ = _classify(backlog, feature_id, sha=sha)
                self.assertEqual(result.exit_code, EXIT_INPUT, result.message)
                if feature_id != "600-X":
                    self.assertIsNone(_record(backlog, feature_id))

    def test_run_preclose_rejects_closed_shipment(self) -> None:
        backlog = _cascade_fixture(self)
        _write_shipment(backlog, ["600-F", "600.001-T"], status="archived")
        with mock.patch.object(preclose, "probe_engine_semantics", return_value=_probe("1.11.0")):
            with self.assertRaises(preclose.PreCloseError) as caught:
                run_preclose(backlog.parent, _SHIPMENT, "600-F", resolved=_RESOLVED)
        self.assertEqual(caught.exception.exit_code, EXIT_INPUT)


class LockPrecedenceTests(unittest.TestCase):
    """Scenario 4: an invoking record wins with exit 7 before any classification (AN-F02)."""

    def test_invoking_record_wins(self) -> None:
        backlog = _task_only_fixture(self)  # now classifies SAFE_CLOSE
        path = build_evidence_path(backlog.parent, _SHIPMENT, "610-F")
        path.parent.mkdir(parents=True)
        invoking = {
            "phase": "invoking",
            "run_id": "0123456789abcdef0123456789abcdef",
            "shipment_id": _SHIPMENT,
            "feature_id": "610-F",
        }
        path.write_text(json.dumps(invoking) + "\n", encoding="utf-8")
        before = path.read_bytes()
        with mock.patch.object(preclose, "classify_shipment_close_path") as classify:
            result, probe = _classify(backlog, "610-F")
        self.assertEqual(result.exit_code, EXIT_LOCKED, result.message)
        classify.assert_not_called()
        probe.assert_not_called()
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
