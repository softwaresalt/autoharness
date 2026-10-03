"""Response parser, flat sets, and INV-10 evaluator tests (192.005-T, plan unit A3b).

Four table-driven scenarios (plan ``### A3b``):

1. the JSON-RPC envelope and ``mutation_state``;
2. the flat ``allowed_ids`` / ``required_ids`` table (re-plan R4; 038-DL D2);
3. the INV-10 table;
4. the parity test (M1, INV-P8; re-plan cycle-1 R9; cycle-2 C2-4).

Envelope characterization (the plan's first test step): the three files in
``tests/fixtures/backlogit_ship/`` are the exact stdout bytes of backlogit
1.11.0 (commit ``131577c``) captured on 2026-10-02 in a scratch fixture
workspace under the Git-ignored ``.proof-scratch/``:

* ``shipment-ship-help.jsonrpc``: ``backlogit --jsonrpc shipment ship --help``
  (the ``result`` is the help text, a string);
* ``shipment-ship-success.jsonrpc``: ``backlogit --jsonrpc shipment ship 001-S
  --sha <40 hex> --message ... --author ...`` (exit 0), over a manifest of one
  feature and its task;
* ``shipment-ship-gate-blocked.jsonrpc``: the same call while the task was
  still ``active`` (exit 6, a JSON-RPC ``error``).

This module is the only importer of ``shipment_closure._closure_scope_ids``
and ``shipment_closure._is_engine_inert`` (M1).
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import unittest
from pathlib import Path

from autoharness.gates import shipment_closure, topology
from autoharness.gates.cascade_evidence import (
    DECLARED_STATUS_MISSING,
    declared_status_from_record,
    declared_status_to_record,
)
from autoharness.gates.shipment_closure import (
    ClosePath,
    ClosePathDecision,
    DeliberationRecordSnapshot,
    LinkedDeliberationDisposition,
    LinkedDeliberationDispositionPlan,
    LinkedDeliberationOutcome,
    _closure_scope_ids,
    _is_engine_inert,
    assess_cascade_engine_semantics,
)
from autoharness.shipment_close import postclose
from autoharness.shipment_close.postclose import (
    ParsedResult,
    ParseError,
    PostCloseReread,
    RereadRecord,
    compute_flat_sets,
    derive_mutation_state,
    evaluate_postconditions,
    parse_ship_response,
)
from autoharness.shipment_close.preclose import PreCloseSnapshot

_REPO = Path(__file__).resolve().parents[1]
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "backlogit_ship"
_SHIPMENT = "900-S"
_SHA = {name: (name * 64)[:64] for name in "abcdef"}


def _disposition(deliberation_id: str, outcome: object, *, sha: str = "e" * 64) -> LinkedDeliberationDisposition:
    return LinkedDeliberationDisposition(
        deliberation_id=deliberation_id,
        outcome=outcome,
        reason_code=str(getattr(outcome, "value", outcome)),
        link_kinds=("source_deliberation_id",),
        linking_member_ids=("700.001-T",),
        records=(
            DeliberationRecordSnapshot(
                path=f".backlogit/queue/{deliberation_id}.md", declared_status="active", sha256=sha
            ),
        ),
        declared_status="active",
    )


_PLAN = LinkedDeliberationDispositionPlan(
    shipment_id=_SHIPMENT,
    engine=None,
    dispositions=(_disposition("701-DL", LinkedDeliberationOutcome.RETAINED_LIVE_STATUS),),
    unresolved_references=(),
)


def _member(member_id: str, artifact_type: str, status: object, parent_id: str | None, sha: str) -> dict:
    return {
        "id": member_id,
        "artifact_type": artifact_type,
        "location": "archive" if status == "archived" else "queue",
        "sha256": sha,
        "declared_status": declared_status_to_record(status),
        "parent_id": parent_id,
    }


def _snapshot(members: list[dict] | None = None, *, qualifying: tuple[str, ...] = ("700-F",)) -> PreCloseSnapshot:
    if members is None:
        members = [
            _member("700-F", "feature", "done", None, _SHA["a"]),
            _member("700.001-T", "task", "done", "700-F", _SHA["b"]),
            _member("700.002-T", "task", "archived", "700-F", _SHA["c"]),
            _member("700-DL", "deliberation", "accepted", None, _SHA["d"]),
        ]
    pre_close = {
        "classifier_verdict": "CASCADE",
        "qualifying_feature_ids": list(qualifying),
        "shipment_record": {"location": "queue", "sha256": _SHA["f"], "declared_status": "active"},
        "manifest_members": members,
        "out_of_manifest_descendants": [
            {"id": "700.003-T", "location": "archive", "sha256": _SHA["e"], "declared_status": "archived"}
        ],
        "linked_deliberation_disposition": {
            "dispositions": [
                {
                    "deliberation_id": "701-DL",
                    "outcome": "retained_live_status",
                    "reason_code": "retained_live_status",
                    "path": None,
                    "link_kinds": ["source_deliberation_id"],
                    "linking_member_ids": ["700.001-T"],
                    "referrer_ids": [],
                    "declared_status": "active",
                    "records": [
                        {"path": ".backlogit/queue/701-DL.md", "declared_status": "active", "sha256": "e" * 64}
                    ],
                }
            ],
            "unresolved_references": [],
            "read_failures": [],
            "planning_error": None,
        },
    }
    engine = assess_cascade_engine_semantics("1.11.0", probe_surface="cli", invocation_surface="cli")
    classifier = ClosePathDecision(ClosePath.CASCADE, "fixture", qualifying_feature_ids=qualifying)
    return PreCloseSnapshot(
        shipment_id=_SHIPMENT,
        feature_id="700-F",
        backlog_dir=Path(".backlogit"),
        manifest_ids=tuple(member["id"] for member in members),
        classifier=classifier,
        engine=engine,
        invocation_surface="cli",
        selection=(ClosePath.CASCADE, "fixture"),
        disposition=_PLAN,
        tool={},
        pre_close=pre_close,
    )


def _archived(sha: str, parent_id: str | None) -> RereadRecord:
    return RereadRecord(location="archive", sha256=sha, declared_status="archived", parent_id=parent_id)


def _reread(**overrides: object) -> PostCloseReread:
    records = {
        "700-F": _archived("1" * 64, None),
        "700.001-T": _archived("2" * 64, "700-F"),
        "700.002-T": RereadRecord(location="archive", sha256=_SHA["c"], declared_status="archived", parent_id="700-F"),
        "700-DL": _archived("3" * 64, None),
        "700.003-T": RereadRecord(location="archive", sha256=_SHA["e"], declared_status="archived", parent_id="700-F"),
    }
    records.update(overrides.pop("records", {}))
    shipment = overrides.pop(
        "shipment",
        RereadRecord(
            location="archive", sha256="4" * 64, declared_status="archived", parent_id=None, archived_status="shipped"
        ),
    )
    return PostCloseReread(shipment=shipment, records=records, disposition=overrides.pop("disposition", _PLAN))


def _parsed(archived: list[str], returned: list[str] | None = None) -> ParsedResult:
    return ParsedResult(
        shipment_id=_SHIPMENT,
        shipment_status="shipped",
        archived_ids=tuple(archived),
        returned_ids=tuple(returned or ()),
        commit_sha="0123456789abcdef0123456789abcdef01234567",
    )


_PASS_ARCHIVED = ["700.001-T", "700-F", "700-DL", _SHIPMENT]


def _evaluate(snapshot=None, parsed=None, reread=None, **kwargs):
    kwargs.setdefault("linked_deliberation_drift", ())
    kwargs.setdefault("disposition_byte_identical", True)
    return evaluate_postconditions(
        snapshot or _snapshot(), parsed if parsed is not None else _parsed(_PASS_ARCHIVED), reread or _reread(), **kwargs
    )


class EnvelopeTests(unittest.TestCase):
    """Scenario 1: the characterized envelope parses; malformed input is a ParseError; mutation_state."""

    def test_envelope_and_mutation_state(self) -> None:
        with self.subTest("characterized success envelope"):
            parsed = parse_ship_response((_FIXTURES / "shipment-ship-success.jsonrpc").read_bytes())
            self.assertEqual(
                parsed,
                ParsedResult(
                    shipment_id="001-S",
                    shipment_status="shipped",
                    archived_ids=("001.001-T", "001-F", "001-S"),
                    returned_ids=(),
                    commit_sha="0123456789abcdef0123456789abcdef01234567",
                ),
            )
        with self.subTest("characterized error envelope"):
            parsed = parse_ship_response((_FIXTURES / "shipment-ship-gate-blocked.jsonrpc").read_bytes())
            self.assertIsInstance(parsed, ParseError)
            self.assertIn("gate blocked", parsed.message)
        malformed = {
            "help text result": (_FIXTURES / "shipment-ship-help.jsonrpc").read_bytes(),
            "empty": b"",
            "not json": b"gate blocked\n",
            "not utf-8": b"\xff\xfe",
            "wrong version": b'{"jsonrpc":"1.0","id":"x","result":{}}',
            "two envelopes": b'{"jsonrpc":"2.0","result":{}}\n{"jsonrpc":"2.0","result":{}}',
            "result and error": b'{"jsonrpc":"2.0","result":{},"error":{"code":1,"message":"x"}}',
            "missing archived_ids": b'{"jsonrpc":"2.0","result":{"returned_ids":[],"shipment_id":"1-S","shipment_status":"shipped","commit_sha":null}}',
            "non-str id": b'{"jsonrpc":"2.0","result":{"archived_ids":[1],"returned_ids":[],"shipment_id":"1-S","shipment_status":"shipped","commit_sha":null}}',
            "array": b"[]",
        }
        for name, data in malformed.items():
            with self.subTest(f"malformed: {name}"):
                self.assertIsInstance(parse_ship_response(data), ParseError)
        with self.subTest("non-bytes input"):
            self.assertIsInstance(parse_ship_response("{}"), ParseError)

        snapshot = _snapshot()
        unchanged = PostCloseReread(
            shipment=RereadRecord(location="queue", sha256=_SHA["f"], declared_status="active", parent_id=None),
            records={
                member["id"]: RereadRecord(
                    location=member["location"],
                    sha256=member["sha256"],
                    declared_status=declared_status_from_record(member["declared_status"]),
                    parent_id=member["parent_id"],
                )
                for member in snapshot.pre_close["manifest_members"]
            }
            | {"700.003-T": RereadRecord(location="archive", sha256=_SHA["e"], declared_status="archived", parent_id="700-F")},
            disposition=_PLAN,
        )
        error = ParseError("gate blocked")
        changed = dataclasses.replace(
            unchanged, records=unchanged.records | {"700.001-T": _archived("9" * 64, "700-F")}
        )
        cases = [
            ("parsed success", _parsed(_PASS_ARCHIVED), _reread(), 0, False, "completed"),
            ("unparsed, unchanged", error, unchanged, 6, False, "none"),
            ("unparsed, changed", error, changed, 6, False, "indeterminate"),
            ("unparsed, archive twin", error, dataclasses.replace(unchanged, unreadable_ids=frozenset({"700-F"})), 1, False, "indeterminate"),
            ("unparsed, disposition not re-collected", error, dataclasses.replace(unchanged, disposition=None), 1, False, "indeterminate"),
            ("unparsed, deliberation modified", error, dataclasses.replace(unchanged, disposition=dataclasses.replace(_PLAN, dispositions=(_disposition("701-DL", LinkedDeliberationOutcome.RETAINED_LIVE_STATUS, sha="0" * 64),))), 1, False, "indeterminate"),
            ("timeout, unchanged", None, unchanged, None, True, "indeterminate"),
            ("parsed success but non-zero exit", _parsed(_PASS_ARCHIVED), unchanged, 1, False, "indeterminate"),
            ("no reread", error, None, 6, False, "indeterminate"),
        ]
        for name, parsed, reread, exit_code, timed_out, expected in cases:
            with self.subTest(f"mutation_state: {name}"):
                self.assertEqual(
                    derive_mutation_state(snapshot, parsed, reread, exit_code=exit_code, timed_out=timed_out), expected
                )


class FlatSetTests(unittest.TestCase):
    """Scenario 2: flat sets; the two set checks fail independently (INV-P3)."""

    def test_flat_set_table(self) -> None:
        allowed, required = compute_flat_sets(_snapshot().pre_close, _SHIPMENT)
        self.assertEqual(allowed, frozenset({"700-F", "700.001-T", "700.002-T", "700-DL", _SHIPMENT}))
        # The pre-close archived task is absent from required_ids; 701-DL (disposition set) is in neither.
        self.assertEqual(required, frozenset({_SHIPMENT, "700-F", "700.001-T", "700-DL"}))

        cases = [
            ("pass (explicit-member deliberation archived, H10)", _PASS_ARCHIVED, [], []),
            ("unexpected only (disposition-set deliberation archived)", [*_PASS_ARCHIVED, "701-DL"], ["701-DL"], []),
            ("missing only", ["700.001-T", "700-DL", _SHIPMENT], [], ["700-F"]),
            ("both", ["700.001-T", "700-DL", _SHIPMENT, "701-DL", "799-F"], ["701-DL", "799-F"], ["700-F"]),
        ]
        for name, archived, unexpected, missing in cases:
            with self.subTest(name):
                result = _evaluate(parsed=_parsed(archived))
                self.assertEqual(list(result.unexpected_archived), unexpected)
                self.assertEqual(list(result.missing_required), missing)
                self.assertEqual(result.postcondition_verdict, "pass" if not (unexpected or missing) else "fail")
                record = result.to_record()
                self.assertEqual(record["allowed_ids"], sorted(allowed))
                self.assertEqual(record["required_ids"], sorted(required))
                self.assertNotIn("701-DL", record["allowed_ids"] + record["required_ids"])
                failures = " ".join(record["failures"])
                self.assertEqual("unexpected_archived" in failures, bool(unexpected))
                self.assertEqual("missing_required" in failures, bool(missing))


class Inv10Tests(unittest.TestCase):
    """Scenario 3: INV-10 checks, each failing the verdict on its own."""

    def test_inv10_table(self) -> None:
        passing = _evaluate()
        self.assertEqual(passing.postcondition_verdict, "pass", passing.failures)
        self.assertEqual(passing.to_record()["shipment_record_archived_status"], "shipped")
        self.assertTrue(passing.parent_id_preserved and passing.baseline_invariant and passing.shipment_archived_shipped)

        cases = [
            ("non-empty returned_ids", {"parsed": _parsed(_PASS_ARCHIVED, ["700.001-T"])}, "returned_ids"),
            (
                "moved parent_id on an archived manifest task",
                {"reread": _reread(records={"700.002-T": _archived(_SHA["c"], "799-F")})},
                "parent_id_preserved",
            ),
            (
                "moved parent_id on an out-of-manifest artifact",
                {"reread": _reread(records={"700.003-T": _archived("8" * 64, "799-F")})},
                "baseline_invariant",
            ),
            (
                "modified descendant",
                {"reread": _reread(records={"700.003-T": _archived("7" * 64, "700-F")})},
                "baseline_invariant",
            ),
            (
                "shipment record lacks archived_status: shipped",
                {
                    "reread": _reread(
                        shipment=RereadRecord(location="archive", sha256="4" * 64, declared_status="archived", parent_id=None)
                    )
                },
                "shipment_archived_shipped",
            ),
            ("linked-deliberation drift (A3c)", {"linked_deliberation_drift": ({"deliberation_id": "701-DL"},)}, "linked_deliberation_drift"),
            ("disposition not evaluated (A3c)", {"disposition_byte_identical": None}, "disposition_byte_identical"),
            ("unparsed response", {"parsed": ParseError("gate blocked")}, "parse_error"),
        ]
        for name, kwargs, label in cases:
            with self.subTest(name):
                result = _evaluate(**kwargs)
                self.assertEqual(result.postcondition_verdict, "fail")
                self.assertIn(label, " ".join(result.failures))
        self.assertFalse(_evaluate(**cases[1][1]).parent_id_preserved)
        self.assertFalse(_evaluate(**cases[3][1]).baseline_invariant)
        self.assertFalse(_evaluate(**cases[4][1]).shipment_archived_shipped)


class ParityTests(unittest.TestCase):
    """Scenario 4: local sets and the archived check pinned to the merged private helpers."""

    def test_allowed_ids_parity(self) -> None:
        manifests = [
            [],
            [_member("710-F", "feature", "done", None, _SHA["a"])],
            [_member("711.001-T", "task", "done", "711-F", _SHA["a"]), _member("711-DL", "deliberation", "accepted", None, _SHA["b"])],
        ]
        for members in manifests:
            with self.subTest([member["id"] for member in members]):
                allowed, _ = compute_flat_sets(_snapshot(members, qualifying=()).pre_close, _SHIPMENT)
                self.assertEqual(allowed, _closure_scope_ids([member["id"] for member in members], _SHIPMENT))

    def test_truly_archived_parity(self) -> None:
        for raw in ("archived", "Archived", " archived ", True, None, DECLARED_STATUS_MISSING):
            with self.subTest(raw=raw):
                engine_value = None if raw is DECLARED_STATUS_MISSING else raw
                local = postclose._is_declared_archived(declared_status_to_record(raw))
                self.assertEqual(local, _is_engine_inert(engine_value))
                self.assertEqual(local, raw == "archived" and type(raw) is str)

    def test_private_names_pinned(self) -> None:
        self.assertIsInstance(shipment_closure._RELEASE_VERSION_PATTERN, str)
        signatures = {
            "_scan_backlog": ["backlog_dir"],
            "_enumerate_descendants": ["children_index", "root_id"],
            "_read_artifact_record": ["backlog_dir", "artifact_id"],
            "_check_path_containment": ["path", "backlog_dir"],
        }
        for name, parameters in signatures.items():
            with self.subTest(name):
                self.assertEqual(list(inspect.signature(getattr(shipment_closure, name)).parameters), parameters)
        # Gap-fill: A2b also lazily reuses the classifier's frontmatter parser.
        self.assertEqual(list(inspect.signature(topology._frontmatter).parameters), ["path"])

    def test_private_names_are_never_imported_at_module_top_level(self) -> None:
        lazy = {
            "_RELEASE_VERSION_PATTERN",
            "_scan_backlog",
            "_enumerate_descendants",
            "_read_artifact_record",
            "_check_path_containment",
            "_frontmatter",
        }
        never = {"_closure_scope_ids", "_is_engine_inert"}
        package = _REPO / "src" / "autoharness"
        modules = sorted((package / "shipment_close").glob("*.py")) + [package / "cli.py"]
        for module in modules:
            with self.subTest(module.name):
                tree = ast.parse(module.read_text(encoding="utf-8"))
                top_level = {
                    alias.name for node in tree.body if isinstance(node, ast.ImportFrom) for alias in node.names
                }
                self.assertFalse(top_level & (lazy | never), module)
        for module in sorted(package.rglob("*.py")):
            if module.name == "shipment_closure.py":
                continue
            with self.subTest(f"never imported: {module.relative_to(package)}"):
                text = module.read_text(encoding="utf-8")
                self.assertFalse(any(name in text for name in never), module)


if __name__ == "__main__":
    unittest.main()
