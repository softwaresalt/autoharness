"""``cascade-close --poll``: a read-only, idempotent view of a supervised run (211-F, plan unit T8; hardening H14).

The answer comes from the journal and, when the journal's ``outcome.json`` is missing, from the terminal evidence
record of the journal's own run:

* ``outcome.json`` present: its exit code (``outcome_source: journal_outcome``);
* no ``outcome.json`` but a terminal ``post_close`` record for the journal's ``run_id`` (the finalizer died between the
  evidence write and the outcome write): derived read-only from that record, pass -> 0, postcondition failure -> 5,
  failed or unparsed invocation -> 6 (``outcome_source: evidence_record``);
* an ``invoking`` record whose lock owner is alive or cannot be proven dead: ``running`` (exit 9);
* an ``invoking`` record whose lock is gone or whose owner is provably dead: exit 7 with ``recovery_available``.

Nothing here writes, deletes, takes a lock, signals a process, or recovers anything.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from autoharness.gates.cascade_evidence import CascadeEvidenceError, build_evidence_path, validate_evidence_record
from autoharness.shipment_close import (
    EXIT_INPUT,
    EXIT_INVOCATION_INDETERMINATE,
    EXIT_LOCKED,
    EXIT_OK,
    EXIT_POSTCONDITION_FAILED,
    EXIT_STARTED,
)
from autoharness.shipment_close.journal import (
    MAX_JSON_BYTES,
    Journal,
    JournalError,
    _read_capped,
    journal_has,
    journal_path,
    read_json,
)
from autoharness.shipment_close.liveness import provably_dead
from autoharness.shipment_close.persist import PersistError, _read_no_follow, observe_lock

__all__ = ["PollOutcome", "poll_cascade_close"]

_RUN_ID: Final = "run_id"
_TRANSIENT_RETRIES: Final = 5
_TRANSIENT_BACKOFF_SECONDS: Final = 0.05


def _retrying(read: Callable[[], object]) -> object:
    """Retry a read that a concurrent atomic replace can transiently refuse (a Windows sharing violation)."""

    for _ in range(_TRANSIENT_RETRIES):
        try:
            return read()
        except PermissionError:
            pass
        except JournalError as exc:
            if exc.reason != "untrusted":
                raise
        time.sleep(_TRANSIENT_BACKOFF_SECONDS)
    return read()


@dataclass(frozen=True)
class PollOutcome:
    exit_code: int
    message: str
    evidence_path: Path | None = None
    journal_path: Path | None = None
    outcome_source: str | None = None
    recovery_available: bool | None = None
    failures: tuple[str, ...] = ()


def _open_journal(directory: Path) -> Journal:
    """Open a pair's journal by its ``meta.json`` (``launch.json`` is gone after a clean run's cleanup)."""

    raw, truncated = _read_capped(directory / "meta.json", MAX_JSON_BYTES)
    try:
        run_id = None if truncated else json.loads(raw.decode("utf-8")).get(_RUN_ID)
    except (ValueError, UnicodeDecodeError, AttributeError) as exc:
        raise JournalError("torn", "meta.json is not valid JSON (torn or corrupt)") from exc
    if type(run_id) is not str:
        raise JournalError("invalid", "meta.json carries no run_id")
    journal = Journal(path=directory, run_id=run_id)
    read_json(journal, "meta.json")
    return journal


def _derive_from_evidence(record: dict, shipment_id: str, feature_id: str) -> tuple[int, str]:
    post_close = record.get("post_close")
    invocation = record.get("invocation")
    verdict = post_close.get("postcondition_verdict") if isinstance(post_close, dict) else None
    if not isinstance(invocation, dict) or verdict not in ("pass", "fail"):
        return EXIT_LOCKED, "the terminal evidence record is malformed (operator review)"
    if (
        invocation.get("exit_code") != 0
        or invocation.get("timed_out") is not False
        or post_close.get("parse_error") is not None  # type: ignore[union-attr]
    ):
        return EXIT_INVOCATION_INDETERMINATE, "the invocation failed or its output did not parse"
    if verdict != "pass":
        return EXIT_POSTCONDITION_FAILED, "a postcondition failed"
    problems = validate_evidence_record(record, shipment_id=shipment_id, feature_id=feature_id, close_path="cascade")
    if problems:
        return EXIT_POSTCONDITION_FAILED, "the record claims a pass but does not validate"
    return EXIT_OK, "cascade close completed; every postcondition passed"


def _evaluate(workspace: Path | str, shipment_id: str, feature_id: str) -> PollOutcome:
    try:
        directory = journal_path(workspace, shipment_id, feature_id)
        evidence = build_evidence_path(workspace, shipment_id, feature_id)
    except (JournalError, CascadeEvidenceError) as exc:
        return PollOutcome(EXIT_INPUT, str(exc))
    if not os.path.lexists(directory):
        return PollOutcome(EXIT_INPUT, "no supervised run to poll: this pair has no journal", evidence_path=evidence)
    try:
        journal = _retrying(lambda: _open_journal(directory))
    except (JournalError, OSError) as exc:
        return PollOutcome(
            EXIT_LOCKED,
            f"the journal cannot be read (operator review): {exc}",
            evidence_path=evidence,
            journal_path=directory,
        )

    def result(code: int, message: str, **extra: object) -> PollOutcome:
        return PollOutcome(code, message, evidence_path=evidence, journal_path=directory, **extra)  # type: ignore[arg-type]

    if journal_has(journal, "outcome.json"):
        try:
            outcome = _retrying(lambda: read_json(journal, "outcome.json"))
        except JournalError:
            outcome = None
        if outcome is not None:
            return result(
                int(outcome["exit_code"]),  # type: ignore[arg-type]
                f"the supervised run ended: {outcome['outcome']}",
                outcome_source="journal_outcome",
            )

    if not os.path.lexists(evidence):
        return result(EXIT_INPUT, "the journal has no outcome and there is no evidence record")
    try:
        record = json.loads(_retrying(lambda: _read_no_follow(evidence)).decode("utf-8"))  # type: ignore[attr-defined]
    except (OSError, ValueError, PersistError) as exc:
        return result(EXIT_LOCKED, f"the evidence record cannot be read (operator review): {exc}")
    if not isinstance(record, dict):
        return result(EXIT_LOCKED, "the evidence record is not a JSON object (operator review)")
    phase = record.get("phase")
    same_run = record.get("run_id") == journal.run_id
    if phase == "post_close":
        if not same_run:
            return result(EXIT_INPUT, "the journal belongs to an earlier run; this pair was finalized by another run")
        code, message = _derive_from_evidence(record, shipment_id, feature_id)
        return result(
            code,
            f"{message} (derived from the evidence record; outcome.json is missing)",
            outcome_source="evidence_record",
        )
    if phase != "invoking":
        return result(EXIT_INPUT, f"no run in progress: the evidence record is {phase!r} and the journal has no outcome")
    if not same_run:
        return result(EXIT_LOCKED, "the invoking record belongs to another run (operator review)", recovery_available=False)

    try:
        observed = observe_lock(workspace, shipment_id, feature_id)
    except PersistError as exc:
        return result(EXIT_LOCKED, f"the lock cannot be read (operator review): {exc}", recovery_available=False)
    if observed is None:
        return result(
            EXIT_LOCKED,
            "the run left an invoking record and no lock: the supervisor is gone (recovery is available)",
            recovery_available=True,
        )
    if not observed.parsed or observed.run_id != journal.run_id:
        return result(
            EXIT_LOCKED, "the pair lock is unreadable or held by another run (operator review)", recovery_available=False
        )
    verdict = provably_dead(observed.host, observed.pid, observed.pid_start)
    if verdict.dead:
        return result(
            EXIT_LOCKED,
            f"the supervisor is gone ({verdict.basis}); the run is orphaned (recovery is available)",
            recovery_available=True,
        )
    return result(
        EXIT_STARTED,
        f"running: the supervisor is alive or cannot be proven dead ({verdict.basis})",
        recovery_available=False,
    )


def poll_cascade_close(
    workspace: Path | str,
    shipment_id: str,
    feature_id: str,
    *,
    wait_seconds: float = 0,
    poll_interval: float = 1.0,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> PollOutcome:
    """Poll once, or until the run stops being ``running`` (exit 9) or ``wait_seconds`` elapse; read-only."""

    deadline = clock() + max(0.0, float(wait_seconds))
    while True:
        outcome = _evaluate(workspace, shipment_id, feature_id)
        if outcome.exit_code != EXIT_STARTED or clock() >= deadline:
            return outcome
        sleep(max(0.0, min(poll_interval, deadline - clock())))
