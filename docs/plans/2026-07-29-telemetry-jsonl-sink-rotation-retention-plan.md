---
title: Telemetry JSONL sink rotation + retention policy
doc_type: plan
status: reviewed
created: 2026-07-29
source_stash_id: 7D1E2F1A
prior_work: 092-F / 097-S (PR #241, telemetry subsystem hardening)
covering_feature: 100-F
---

# Plan: Rotation + retention for the telemetry JSONL sink

## Problem

`src/autoharness/telemetry/jsonl_sink.py` appends each `ExecutionEpoch` as one
JSON line to a single `execution_epochs.jsonl` mirror with **no** size- or
age-based rollover, **no** retention window, and **no** compaction. The mirror
therefore grows unbounded beside the authoritative SQLite store. This was
explicitly deferred as out-of-scope from shipment 097-S / feature 092-F to keep
that shipment width-isolated (see
`docs/plans/2026-07-28-telemetry-followup-hardening-plan.md` §Out of scope).

The sink is a **best-effort human-readable mirror**; SQLite is the authoritative
first-write-immutable store. Even so, the sink enforces two replay invariants on
every append via `scan_epoch_digest` / `find_epoch_digest`:

* **Idempotent replay** — re-appending the same `epoch_id` + identical payload
  digest returns `idempotent_replay` and does not duplicate the line.
* **Conflict detection** — the same `epoch_id` with a *different* digest raises
  `TelemetryConflictError`.

Today those checks scan one file. Any rotation mechanism MUST keep both invariants
holding **across rotated segments**, or telemetry replay integrity regresses.

## Ground-truth verification (done before planning)

* Read `jsonl_sink.py` in full (161 lines) and `tests/test_telemetry_jsonl_sink.py`
  in full.
* The preflight/replay entry points are `scan_epoch_digest(path, epoch_id, *,
  start_offset=0)` and `find_epoch_digest(path, epoch_id)`; `append_epoch` calls
  the scan, compares digests, and either returns `idempotent_replay`, raises
  `TelemetryConflictError`, or atomically appends via `_atomic_append_bytes`
  (POSIX `O_APPEND` / Win32 `FILE_APPEND_DATA`, both atomic per line).
* The existing tests write small records only (max ~1440 tiny lines in the
  concurrency test), so a rollover threshold in the multi-MiB range is never hit
  by the current suite → existing single-file behavior is preserved unchanged.
* Rotation/retention was recorded as an out-of-scope follow-up in the 2026-07-28
  hardening plan; it is genuinely unimplemented, not already done.

## Design decision

**Size-based segment rollover with a bounded retained-segment window, and
replay/preflight checks extended to scan the active segment plus all retained
sealed segments** so idempotency and conflict detection hold across rotated
segments (within the retention horizon).

Rationale for choosing size-based rollover + retention window over age-based
rollover or in-place compaction:

* It is the **simplest mechanism that provably bounds disk usage**: total bytes ≤
  `(max_retained_segments + 1) * max_segment_bytes`.
* It is **deterministic and testable** with a low threshold in tests (no clock
  dependence, unlike age-based rollover; no line rewriting, unlike compaction).
* Sealed segments are **immutable append-only files**, which keeps the existing
  atomic-append and immutable-replay contracts intact — compaction would rewrite
  history and fight the first-write-immutable invariant.

### Configuration (additive, sane defaults; rotation on by default)

* `max_segment_bytes` — active segment rolls over when it would exceed this size.
  Default large enough (multi-MiB, e.g. 8 MiB) that the current test suite never
  triggers rollover, preserving existing behavior.
* `max_retained_segments` — number of sealed segments kept; oldest pruned first.

Sealed segment naming: monotonic, sortable, colocated with the active file
(e.g. `execution_epochs.jsonl.1`, `.2`, … or a zero-padded/timestamped suffix)
so enumeration yields a stable oldest→newest order.

### Replay integrity across segments (the hard invariant)

* The replay lookup enumerates the active segment **and** all retained sealed
  segments. Idempotent-replay and conflict detection consider a match in **any**
  retained segment.
* Active-file `start_offset` tail-scan optimization is preserved for the active
  segment; sealed segments are immutable and scanned fully (they never change).
* **Documented horizon bound:** replay/conflict guarantees hold only for epochs
  still inside the retention window. Once the segment carrying an `epoch_id` is
  pruned, a later replay of that `epoch_id` can no longer be detected and would be
  appended as new. This is acceptable for a best-effort mirror (SQLite remains
  authoritative and deduplicates on read) and MUST be stated explicitly in code
  docs and tests.

### Rollover concurrency (top risk)

The sink supports concurrent writers. Rollover (seal active → start fresh) must be
**race-tolerant**: a rename race (target already sealed by another writer, or
source already rotated) MUST NOT corrupt data or raise — the writer re-resolves
the current active segment and appends there. JSONL is best-effort, so rollover is
best-effort: never raise on rollover contention; always land the append intact in
the current active segment.

## Width isolation

Strictly the telemetry JSONL sink: `src/autoharness/telemetry/jsonl_sink.py` and
`tests/test_telemetry_jsonl_sink.py` (a sibling test module is acceptable). No
changes to `epoch.py`, `record.py`, aggregation, schemas, CLI, or templates. No
refactor of unrelated telemetry code.

## Plan hardening assessment (P-006)

P-006 elevated-blast-radius triggers are schemas, CLI distribution, or multiple
template families. **None apply** — this is a single Python module plus its test
file, additive and config-gated with defaults that leave existing behavior
unchanged. **P-006 hardening not required.** The one genuine risk (rollover
concurrency) is contained by (a) keeping sealed segments immutable, (b) making
rollover race-tolerant/non-raising, and (c) the mandatory acceptance criterion
that all existing single-file tests still pass unchanged.

## Test-first (P-002 / P-004)

Every task is TDD: write failing tests first (red), implement, green. Canonical
full-suite gate for this repo is `PYTHONPATH=src python -m unittest discover -s
tests` (see compound `097-S-canonical-unittest-gate`); the targeted module is
`tests/test_telemetry_jsonl_sink.py` (runnable via
`python -m unittest tests.test_telemetry_jsonl_sink`).

## Harvest model (dependency-ordered, ≤2h / ≤3 files / ≤5 funcs / ≤4 scenarios each)

* **100.001-T — Replay/preflight scan across segments.** Extend the replay lookup
  to enumerate active + sealed retained segments, preserving idempotent-replay and
  conflict semantics across segments. Foundation first so later rollover never
  breaks replay. Scenarios: idempotent replay when the epoch lives in a sealed
  segment; conflict detected across segments; single-segment behavior unchanged.
* **100.002-T — Size-based rollover on write.** Seal the active segment to a
  monotonically-named segment when it reaches `max_segment_bytes`; start a fresh
  active file; race-tolerant, non-raising. Depends on 100.001. Scenarios: rollover
  triggers at a low test threshold and produces sealed + fresh active; high default
  threshold leaves current small writes single-file (existing behavior preserved);
  concurrent writers don't corrupt/raise on rollover race; appended line lands
  intact after rollover.
* **100.003-T — Bounded retention / pruning.** Keep ≤ `max_retained_segments`
  sealed segments, pruning oldest first so total bytes are bounded. Depends on
  100.002. Scenarios: sealed count never exceeds the window; oldest pruned first;
  total on-disk bytes bounded by `(window+1) * threshold`; replay across still-
  retained segments holds and the pruned-epoch horizon bound is documented/tested.

## Plan-review verdict

Multi-persona inline review (personas per Stage plan-review contract):

| Persona | Verdict |
|---|---|
| Python Reviewer | PASS — three focused tasks on one module + its test; additive config with defaults; each task ≤5 funcs / ≤4 scenarios. |
| Scope Boundary Auditor | PASS — width-isolated to `jsonl_sink.py` + test; no schema/CLI/template/aggregation edits; matches deferred follow-up from 097-S. |
| Concurrency/Safety Reviewer | PASS with focus — rollover race is the top risk; mitigated by immutable sealed segments, non-raising race-tolerant rollover, and the "existing tests unchanged" gate. |
| Architecture Strategist | PASS — replay-across-segments precedes rollover so every task leaves the suite green; sealed segments preserve the first-write-immutable contract; size-based choice avoids clock/compaction complexity. |
| Learnings Researcher | PASS — applies 097-S task-only-manifest and canonical-unittest-gate learnings; retention horizon bound documented. |

**Findings: P0=0, P1=0.** Advisory (P2, folded into acceptance criteria): document
the retention-horizon replay bound; keep default threshold high enough that the
existing suite never rolls. No P-006 hardening required.
