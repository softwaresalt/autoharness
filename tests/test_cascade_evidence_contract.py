"""Evidence record contract tests for CASCADE close evidence (192.001-T, plan unit A1).

Three table-driven scenarios (plan ``### A1``):

1. shape and pair (including the record path rules and byte-stable
   serialization);
2. cascade internal consistency (AS-F11);
3. selection consistency against the merged engine gate and
   ``select_close_path`` (re-plan R1/R2, cycle-1 R6).

Every fixture builds ``engine_semantics`` by calling
``assess_cascade_engine_semantics`` and the selection by calling
``select_close_path``; no fixture hard-codes a validated linked-deliberation set.
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from autoharness.gates import cascade_evidence
from autoharness.gates.cascade_evidence import (
    EVIDENCE_SCHEMA_VERSION,
    CascadeEvidenceError,
    build_evidence_path,
    redact,
    validate_evidence_record,
)
from autoharness.gates.shipment_closure import (
    ClosePath,
    ClosePathDecision,
    assess_cascade_engine_semantics,
    select_close_path,
)

_SHIPMENT = "198-S"
_FEATURE = "192-F"
_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64


def _engine_record(
    version: object = "1.11.0",
    *,
    probe_surface: object = "cli",
    invocation_surface: str = "cli",
    probed_commit: object = "0123abc",
) -> dict:
    decision = assess_cascade_engine_semantics(
        version,
        probe_surface=probe_surface,
        invocation_surface=invocation_surface,
        probed_commit=probed_commit,
    )
    return {
        "verdict": decision.verdict.value,
        "reason": decision.reason,
        "probed_version": decision.probed_version,
        "minor_line": list(decision.minor_line) if decision.minor_line is not None else None,
        "probed_commit": decision.probed_commit,
        "probe_surface": decision.probe_surface,
        "invocation_surface": invocation_surface,
    }


def _pre_close(classifier: str, engine: dict, *, observation: bool) -> dict:
    classifier_reason = (
        "every qualifying feature descendant is engine-inert"
        if classifier == "CASCADE"
        else "no qualifying root feature member"
    )
    decision = ClosePathDecision(
        close_path=ClosePath[classifier],
        reason=classifier_reason,
        qualifying_feature_ids=(_FEATURE,) if classifier == "CASCADE" else (),
    )
    engine_decision = assess_cascade_engine_semantics(
        engine["probed_version"],
        probe_surface=engine["probe_surface"],
        invocation_surface=engine["invocation_surface"],
        probed_commit=engine["probed_commit"],
    )
    selected, selection_reason = select_close_path(decision, engine_decision)
    pre_close = {
        "classifier_verdict": classifier,
        "classifier_reason": classifier_reason,
        "qualifying_feature_ids": list(decision.qualifying_feature_ids),
        "engine_semantics": engine,
        "close_path_selection": {
            "selected_close_path": selected.value,
            "reason": selection_reason,
        },
        "shipment_record": {"location": "queue", "sha256": _SHA_A, "declared_status": "active"},
        "manifest_members": [
            {
                "id": "192.001-T",
                "artifact_type": "task",
                "location": "queue",
                "sha256": _SHA_B,
                "declared_status": "done",
                "parent_id": _FEATURE,
            }
        ],
        "out_of_manifest_descendants": [],
        "linked_deliberation_disposition": {
            "dispositions": [],
            "unresolved_references": [],
            "read_failures": [],
            "planning_error": None,
        },
        "captured_at": "2026-10-02T00:00:00Z",
    }
    if observation:
        pre_close["observation_set"] = [
            {
                "id": "192.001-T",
                "path": ".backlogit/queue/192.001-T.md",
                "location": "queue",
                "sha256": _SHA_B,
                "declared_status": "done",
            },
            {
                "id": "192.099-T",
                "path": None,
                "location": "missing",
                "sha256": None,
                "declared_status": None,
            },
        ]
    return pre_close


def _base(phase: str, pre_close: dict) -> dict:
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "shipment_id": _SHIPMENT,
        "feature_id": _FEATURE,
        "merge_commit_sha": "bd824b97999832aa38122f2f70d300ebbb5d2e09",
        "run_id": "0123456789abcdef0123456789abcdef",
        "phase": phase,
        "tool": {
            "binary_path": "backlogit",
            "binary_sha256": _SHA_C,
            "version_excerpt": "backlogit version 1.11.0",
        },
        "pre_close": pre_close,
    }


def _capture() -> dict:
    return {
        "total_bytes": 12,
        "total_lines": 1,
        "sha256": _SHA_A,
        "capture_truncated": False,
        "excerpt": '{"ok": true}',
        "redaction_applied": False,
    }


def safe_close_record(
    *, classifier: str = "SAFE_CLOSE", engine: dict | None = None
) -> dict:
    engine = engine if engine is not None else _engine_record()
    return _base("pre_close", _pre_close(classifier, engine, observation=True))


def cascade_record(*, engine: dict | None = None) -> dict:
    engine = engine if engine is not None else _engine_record()
    record = _base("post_close", _pre_close("CASCADE", engine, observation=False))
    record["invocation"] = {
        "argv_redacted": ["backlogit", "shipment", "ship", _SHIPMENT, "--json"],
        "started_at": "2026-10-02T00:00:01Z",
        "finished_at": "2026-10-02T00:00:02Z",
        "exit_code": 0,
        "timed_out": False,
        "mutation_state": "completed",
        "stdout": _capture(),
        "stderr": _capture(),
    }
    record["post_close"] = {
        "parsed_result": {
            "shipment_status": "shipped",
            "archived_ids": ["192.001-T", "192-F"],
            "returned_ids": [],
            "commit_sha": None,
        },
        "shipment_record_status": "archived",
        "shipment_record_archived_status": "shipped",
        "allowed_ids": ["192.001-T", "192-F", _SHIPMENT],
        "required_ids": ["192.001-T", "192-F", _SHIPMENT],
        "unexpected_archived": [],
        "missing_required": [],
        "linked_deliberation_drift": [],
        "disposition_byte_identical": True,
        "parent_id_preserved": True,
        "baseline_invariant": True,
        "shipment_archived_shipped": True,
        "postcondition_verdict": "pass",
        "failures": [],
    }
    return record


def _validate(record: dict, close_path: str) -> list[str]:
    return validate_evidence_record(
        record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path=close_path
    )


def _disposition(outcome: str, *, path: object = None, reason_code: str | None = None) -> dict:
    return {
        "deliberation_id": "035-DL",
        "outcome": outcome,
        "reason_code": reason_code or outcome,
        "path": path,
        "link_kinds": ["source_deliberation_id"],
        "linking_member_ids": [_FEATURE],
        "referrer_ids": [],
        "declared_status": "accepted",
        "records": [
            {"path": ".backlogit/queue/035-DL.md", "declared_status": "accepted", "sha256": _SHA_C}
        ],
    }


class EvidenceShapeAndPairTests(unittest.TestCase):
    """Scenario 1: shape, pair, path rules, and byte-stable serialization."""

    def test_shape_and_pair_table(self) -> None:
        def drop_post_close(record: dict) -> None:
            del record["post_close"]

        def set_path(index: int, value: object):
            def mutate(record: dict) -> None:
                record["pre_close"]["observation_set"][index]["path"] = value

            return mutate

        def with_disposition(outcome: str, path: object, reason_code: str | None = None):
            def mutate(record: dict) -> None:
                record["pre_close"]["linked_deliberation_disposition"]["dispositions"] = [
                    _disposition(outcome, path=path, reason_code=reason_code)
                ]

            return mutate

        def with_read_failure(path: object):
            def mutate(record: dict) -> None:
                record["pre_close"]["linked_deliberation_disposition"]["read_failures"] = [
                    {"path": path, "reason_code": "path_escape"}
                ]

            return mutate

        def with_record_path(value: str):
            def mutate(record: dict) -> None:
                disposition = _disposition("retained_read_error", reason_code="unreadable_file")
                disposition["records"][0]["path"] = value
                record["pre_close"]["linked_deliberation_disposition"]["dispositions"] = [
                    disposition
                ]

            return mutate

        def missing_with_sha(record: dict) -> None:
            record["pre_close"]["observation_set"][1]["sha256"] = _SHA_A

        # (label, builder, close_path, mutation, accepted)
        rows = [
            ("well-formed safe_close", safe_close_record, "safe_close", None, True),
            ("well-formed cascade", cascade_record, "cascade", None, True),
            ("cascade missing post_close", cascade_record, "cascade", drop_post_close, False),
            (
                "mismatched shipment id",
                safe_close_record,
                "safe_close",
                lambda r: r.__setitem__("shipment_id", "199-S"),
                False,
            ),
            (
                "mismatched feature id",
                cascade_record,
                "cascade",
                lambda r: r.__setitem__("feature_id", "193-F"),
                False,
            ),
            (
                "unknown schema_version",
                safe_close_record,
                "safe_close",
                lambda r: r.__setitem__("schema_version", 2),
                False,
            ),
            ("SAFE_CLOSE record offered for cascade", safe_close_record, "cascade", None, False),
            ("cascade record offered for safe_close", cascade_record, "safe_close", None, False),
            ("absolute path", safe_close_record, "safe_close", set_path(0, "/.backlogit/queue/x.md"), False),
            ("dot-dot segment", safe_close_record, "safe_close", set_path(0, ".backlogit/../x.md"), False),
            ("drive prefix", safe_close_record, "safe_close", set_path(0, "C:/.backlogit/queue/x.md"), False),
            ("bare drive prefix", safe_close_record, "safe_close", set_path(0, "C:.backlogit/x.md"), False),
            ("UNC prefix", safe_close_record, "safe_close", set_path(0, "//server/.backlogit/x.md"), False),
            ("backslash UNC prefix", safe_close_record, "safe_close", set_path(0, "\\\\server\\x.md"), False),
            ("backslash separator", safe_close_record, "safe_close", set_path(0, ".backlogit\\queue\\x.md"), False),
            ("outside backlog root", safe_close_record, "safe_close", set_path(0, "docs/x.md"), False),
            (
                "mixed backlog roots",
                safe_close_record,
                "safe_close",
                with_record_path(".backlog/queue/035-DL.md"),
                False,
            ),
            ("null path on a queue entry", safe_close_record, "safe_close", set_path(0, None), False),
            ("missing entry with a sha256", safe_close_record, "safe_close", missing_with_sha, False),
            (
                "null path on retained_read_error",
                safe_close_record,
                "safe_close",
                with_disposition("retained_read_error", None, "path_escape"),
                True,
            ),
            (
                "relative path on retained_read_error",
                safe_close_record,
                "safe_close",
                with_disposition("retained_read_error", ".backlogit/queue/035-DL.md", "unreadable_file"),
                True,
            ),
            (
                "absolute path on retained_read_error",
                safe_close_record,
                "safe_close",
                with_disposition("retained_read_error", "/etc/035-DL.md", "path_escape"),
                False,
            ),
            ("null path on read_failures entry", safe_close_record, "safe_close", with_read_failure(None), True),
            (
                "outside-root read_failures path",
                safe_close_record,
                "safe_close",
                with_read_failure("../outside.md"),
                False,
            ),
            (
                "records[] path outside root",
                safe_close_record,
                "safe_close",
                with_record_path("docs/decisions/035-DL.md"),
                False,
            ),
        ]
        for label, builder, close_path, mutation, accepted in rows:
            with self.subTest(label):
                record = builder()
                if mutation is not None:
                    mutation(record)
                errors = _validate(record, close_path)
                if accepted:
                    self.assertEqual(errors, [])
                else:
                    self.assertNotEqual(errors, [], f"{label} was accepted")

        # The pair builds exactly one workspace-contained path per (S, F).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.assertEqual(
                build_evidence_path(root, _SHIPMENT, _FEATURE),
                root / "docs" / "closure" / "evidence" / "198-S-192-F-close-evidence.json",
            )
            for shipment_id, feature_id in (("../198-S", _FEATURE), (_SHIPMENT, "192-F/x"), ("", _FEATURE)):
                with self.subTest(pair=(shipment_id, feature_id)):
                    with self.assertRaises(CascadeEvidenceError):
                        build_evidence_path(root, shipment_id, feature_id)

        # Two serializations of the same record are byte-stable.
        record = cascade_record()
        shuffled = copy.deepcopy(record)
        shuffled["post_close"]["parsed_result"]["archived_ids"].reverse()
        shuffled["post_close"]["allowed_ids"].reverse()
        first = cascade_evidence._serialize_evidence_record(record)
        second = cascade_evidence._serialize_evidence_record(shuffled)
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))
        self.assertTrue(first.endswith("}\n"))
        self.assertFalse(first.endswith("\n\n"))
        self.assertNotIn("\r", first)
        reloaded = json.loads(first)
        self.assertEqual(reloaded["post_close"]["allowed_ids"], sorted(record["post_close"]["allowed_ids"]))
        self.assertEqual(_validate(reloaded, "cascade"), [])


class CascadeInternalConsistencyTests(unittest.TestCase):
    """Scenario 2: a ``pass`` verdict contradicting its own evidence is rejected (AS-F11)."""

    def test_cascade_internal_consistency_table(self) -> None:
        def post(key: str, value: object):
            return lambda r: r["post_close"].__setitem__(key, value)

        def invocation(key: str, value: object):
            return lambda r: r["invocation"].__setitem__(key, value)

        rows = [
            ("postcondition_verdict fail", post("postcondition_verdict", "fail")),
            ("non-zero exit_code", invocation("exit_code", 1)),
            ("timed out", invocation("timed_out", True)),
            ("indeterminate mutation_state", invocation("mutation_state", "indeterminate")),
            ("non-empty linked_deliberation_drift", post("linked_deliberation_drift", [{"deliberation_id": "035-DL"}])),
            ("disposition_byte_identical false", post("disposition_byte_identical", False)),
            ("parent_id_preserved false", post("parent_id_preserved", False)),
            ("baseline_invariant false", post("baseline_invariant", False)),
            ("shipment_archived_shipped false", post("shipment_archived_shipped", False)),
            ("non-empty returned_ids", lambda r: r["post_close"]["parsed_result"].__setitem__("returned_ids", ["192-F"])),
            ("non-empty unexpected_archived", post("unexpected_archived", ["193-F"])),
            ("non-empty missing_required", post("missing_required", ["192.001-T"])),
            ("non-empty failures", post("failures", ["baseline drift"])),
            ("parse_error present", post("parse_error", "stdout exceeded capture cap")),
            ("phase invoking", lambda r: r.__setitem__("phase", "invoking")),
        ]
        self.assertEqual(_validate(cascade_record(), "cascade"), [])
        for label, mutation in rows:
            with self.subTest(label):
                record = cascade_record()
                mutation(record)
                self.assertNotEqual(_validate(record, "cascade"), [], f"{label} was accepted")


class SelectionConsistencyTests(unittest.TestCase):
    """Scenario 3: the record's selection must equal a fresh re-assessment (re-plan R1/R2)."""

    def test_selection_consistency_table(self) -> None:
        def hand_edit_verified(record: dict) -> None:
            engine = record["pre_close"]["engine_semantics"]
            engine["verdict"] = "VERIFIED"

        def flip_selection(record: dict) -> None:
            record["pre_close"]["close_path_selection"]["selected_close_path"] = "cascade"

        def edit_reason(record: dict) -> None:
            record["pre_close"]["close_path_selection"]["reason"] = "operator said so"

        def surface(record: dict) -> None:
            record["pre_close"]["engine_semantics"]["invocation_surface"] = "mcp"

        rows = [
            (
                "safe_close, CASCADE classifier, UNVERIFIED 1.10.1",
                lambda: safe_close_record(classifier="CASCADE", engine=_engine_record("1.10.1")),
                "safe_close",
                True,
            ),
            (
                "safe_close, CASCADE classifier, UNVERIFIED 1.11.1-rc1",
                lambda: safe_close_record(classifier="CASCADE", engine=_engine_record("1.11.1-rc1")),
                "safe_close",
                True,
            ),
            (
                "safe_close, CASCADE classifier, VERIFIED 1.11.0",
                lambda: _forced_safe_close_over_verified(),
                "safe_close",
                False,
            ),
            (
                "cascade with UNVERIFIED engine",
                lambda: _forced_cascade_over_unverified(),
                "cascade",
                False,
            ),
            (
                "hand-edited VERIFIED over 1.10.0",
                lambda: _mutated(
                    safe_close_record(classifier="CASCADE", engine=_engine_record("1.10.0")),
                    hand_edit_verified,
                ),
                "safe_close",
                False,
            ),
            (
                "selected path disagrees with select_close_path",
                lambda: _mutated(safe_close_record(), flip_selection),
                "safe_close",
                False,
            ),
            (
                "selection reason disagrees with select_close_path",
                lambda: _mutated(safe_close_record(), edit_reason),
                "safe_close",
                False,
            ),
            (
                "invocation_surface mcp",
                lambda: _mutated(safe_close_record(), surface),
                "safe_close",
                False,
            ),
            (
                "probed_commit carries token=...",
                lambda: safe_close_record(engine=_engine_record(probed_commit="abc token=s3cr3t")),
                "safe_close",
                False,
            ),
            (
                "selection reason carries token=...",
                lambda: _safe_close_with_reason("no qualifying root feature member token=s3cr3t"),
                "safe_close",
                False,
            ),
        ]
        for label, build, close_path, accepted in rows:
            with self.subTest(label):
                errors = _validate(build(), close_path)
                if accepted:
                    self.assertEqual(errors, [])
                else:
                    self.assertNotEqual(errors, [], f"{label} was accepted")
        # The redaction-neutrality check compares the text element, never the tuple.
        self.assertEqual(redact("abc token=s3cr3t")[1], True)
        self.assertNotEqual(redact("abc token=s3cr3t")[0], "abc token=s3cr3t")
        self.assertEqual(redact("plain"), ("plain", False))


def _mutated(record: dict, mutation) -> dict:
    mutation(record)
    return record


def _forced_safe_close_over_verified() -> dict:
    """A CASCADE-classified record under a VERIFIED engine that claims safe_close."""
    record = safe_close_record(classifier="CASCADE", engine=_engine_record("1.11.0"))
    selection = record["pre_close"]["close_path_selection"]
    selection["selected_close_path"] = "safe_close"
    selection["reason"] = record["pre_close"]["classifier_reason"]
    return record


def _forced_cascade_over_unverified() -> dict:
    """A cascade record whose engine is UNVERIFIED but claims the cascade selection."""
    record = cascade_record(engine=_engine_record("1.10.1"))
    selection = record["pre_close"]["close_path_selection"]
    selection["selected_close_path"] = "cascade"
    selection["reason"] = (
        f"{record['pre_close']['classifier_reason']}; "
        f"{record['pre_close']['engine_semantics']['reason']}"
    )
    return record


def _safe_close_with_reason(reason: str) -> dict:
    record = safe_close_record()
    record["pre_close"]["classifier_reason"] = reason
    record["pre_close"]["close_path_selection"]["reason"] = reason
    return record


class RedactionCoverageTests(unittest.TestCase):
    """198-S local review: broadened redaction coverage without false positives."""

    _SECRET = "QZX9secretVALUE9QZX"

    def test_sensitive_formats_are_redacted(self) -> None:
        s = self._SECRET
        rows = [
            ("prefixed env key", f"GITHUB_TOKEN={s}"),
            ("npm token env", f"export NPM_TOKEN={s}"),
            ("db password env", f"DB_PASSWORD={s} other"),
            ("aws secret access key", f"AWS_SECRET_ACCESS_KEY={s}"),
            ("azure client secret", f"AZURE_CLIENT_SECRET = {s}"),
            ("dotted config key", f"spring.datasource.password={s}"),
            ("colon password", f"password: {s}"),
            ("colon header api key", f"X-Api-Key: {s}"),
            ("colon quoted value", f"secret: \"{s} with spaces\""),
            ("json prefixed key", f'{{"github_token": "{s}"}}'),
            ("json camelCase key", f'{{"accessToken":"{s}"}}'),
            ("json header key", f'{{"x-api-key" : "{s}"}}'),
            ("json single-quoted key", f"{{'client_secret': \"{s}\"}}"),
            ("url userinfo", f"fetching https://user:{s}@example.com/repo.git"),
            ("url userinfo token user", f"git clone https://x-access-token:{s}@github.com/o/r"),
            ("aws access key id", "key AKIAIOSFODNN7QZX9ABC found"),
            (
                "pem private key block",
                "before\n-----BEGIN RSA PRIVATE KEY-----\nMIIQZX9secretVALUE9QZX\nabc\n"
                "-----END RSA PRIVATE KEY-----\nafter",
            ),
            ("pem openssh key", f"-----BEGIN OPENSSH PRIVATE KEY-----\n{s}\n-----END OPENSSH PRIVATE KEY-----"),
            ("pem unterminated (truncated) block", f"-----BEGIN PRIVATE KEY-----\n{s}\n"),
            ("legacy key=value", f"abc token={s}"),
            ("legacy json key", f'{{"token": "{s}"}}'),
        ]
        for label, text in rows:
            with self.subTest(label):
                redacted, applied = redact(text)
                self.assertTrue(applied, label)
                self.assertIn(cascade_evidence.REDACTION_MARKER, redacted)
                self.assertNotIn("QZX9secretVALUE9QZX", redacted)
                self.assertNotIn("AKIAIOSFODNN7QZX9ABC", redacted)
                self.assertNotIn("MIIQZX9", redacted)
                # Redaction is idempotent, so a persisted excerpt stays neutral.
                self.assertEqual(redact(redacted), (redacted, False))
        with self.subTest("PEM surroundings and URL host are kept"):
            redacted, _ = redact(rows[16][1])
            self.assertTrue(redacted.startswith("before\n"))
            self.assertTrue(redacted.endswith("\nafter"))
            self.assertIn("@example.com/repo.git", redact(rows[13][1])[0])
            self.assertIn("GITHUB_TOKEN=", redact(rows[0][1])[0])
            self.assertIn('"accessToken":', redact(rows[10][1])[0])

    def test_ordinary_output_is_redaction_neutral(self) -> None:
        fixtures = Path(__file__).parent / "fixtures" / "backlogit_ship"
        texts = [path.read_text(encoding="utf-8") for path in sorted(fixtures.glob("*.jsonrpc"))]
        self.assertTrue(texts)
        texts += [
            json.dumps(cascade_record(), indent=2, sort_keys=True),
            json.dumps(safe_close_record(), indent=2, sort_keys=True),
            "198-S 192-F 192.001-T 001.001-T 1263B218 PRRT_kwDORzpWpM6oh0SP",
            "0123456789abcdef0123456789abcdef01234567 cce56634 deadbeef",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "backlogit 1.11.0 (commit 0b4056f) built 2026-10-02T20:52:49Z",
            "gate blocked: 001.001-T remains active",
            "git@github.com:softwaresalt/autoharness.git https://github.com/softwaresalt/autoharness/pull/481",
            "time 12:30:45 at C:\\Source\\GitHub\\autoharness\\docs\\closure\\evidence",
            "--message string   merge commit message to record on released artifacts",
        ]
        for text in texts:
            with self.subTest(text=text[:60]):
                self.assertEqual(redact(text), (text, False))


if __name__ == "__main__":
    unittest.main()
