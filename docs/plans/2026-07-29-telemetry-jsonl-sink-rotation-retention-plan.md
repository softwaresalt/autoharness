---
title: Telemetry JSONL sink rotation + retention policy
doc_type: plan
status: reviewed
created: 2026-07-29
source_stash_id: 7D1E2F1A
prior_work: 092-F / 097-S (PR #241, telemetry subsystem hardening)
covering_feature: 095-F
shipment: 100-S
hardened: 2026-07-29 (P-006, per PR #249 Copilot review — round 1: 6 findings; round 2: single-writer concurrency convergence, findings A + B)
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

* It is the **simplest mechanism that bounds disk usage** to a small multiple of
  the segment threshold — see the restated bound under "Segment size bound"
  below (finding 5): total retained ≤ `(_MAX_RETAINED_SEGMENTS + 1) ×
  (_MAX_SEGMENT_BYTES + one max record)`.
* It is **deterministic and testable** with a low threshold in tests (no clock
  dependence, unlike age-based rollover; no line rewriting, unlike compaction).
* Sealed segments are **immutable append-only files**, which keeps the existing
  atomic-append and immutable-replay contracts intact — compaction would rewrite
  history and fight the first-write-immutable invariant.

### Rotation parameters (non-configurable module constants — finding 2)

Rotation thresholds are **module-level constants in `jsonl_sink.py`**, NOT
runtime configuration:

* `_MAX_SEGMENT_BYTES` — active segment rolls over when it reaches or exceeds this
  size. Default large enough (multi-MiB, e.g. 8 MiB) that the current test suite
  never triggers rollover, preserving existing behavior.
* `_MAX_RETAINED_SEGMENTS` — number of sealed segments kept; oldest pruned first
  (≥ 1).

**Why constants, not config (finding 2 decision):** `TelemetryConfig`
(`config.py`) exposes only `enabled`/`mode`/`database_path`/`emit_jsonl`/
`jsonl_path`; the production caller passes only path + preflight
(`record.py:167-170`); and BOTH validation-gates schemas plus BOTH harness-config
schemas declare the `telemetry` block with `additionalProperties: false`
(`schemas/validation-gates.schema.json`, `schemas/validation-gates/1.0.0.schema.json`,
`schemas/harness-config.schema.json`, `schemas/harness-config/1.0.0.schema.json`).
Exposing `max_segment_bytes`/`max_retained_segments` as configuration would
require editing all four schemas (a versioned schema bump), `config.py` parsing,
and the `record.py` caller — a large cross-cutting blast radius across the schema
family and CLI config path with no demonstrated need for per-workspace tuning.
Module constants keep the change width-isolated to the telemetry subsystem and
deliver exactly the behavior the plan/tasks claim. Tests override the constants
locally (e.g. `mock.patch`/monkeypatch) to exercise rollover at a low threshold;
the acceptance criteria therefore do NOT claim runtime configurability the code
path cannot deliver. Runtime configurability, if ever needed, is an explicit
future feature with its own schema-versioned shipment.

Sealed segment naming carries a **monotonic zero-padded generation** colocated
with the active file: `execution_epochs.jsonl.00001`, `.00002`, …. The active
segment is always the base name `execution_epochs.jsonl`. Enumeration yields a
stable oldest→newest order by generation. The generation is the single identity
that the preflight token, rollover, and pruning all agree on. Rollover always
seals to `max(existing sealed generation) + 1`, a name that by construction does
not already exist, so under the single-writer contract (below) a rename can never
clobber an existing sealed segment.

### Replay integrity across segments + preflight generation identity (findings 1, 6)

* The replay lookup enumerates the active segment **and** all retained sealed
  segments. Idempotent-replay and conflict detection consider a match in **any**
  retained segment.
* **Preflight generation identity (finding 6):** `JsonlPreflightScan` gains a
  segment-identity field (the active segment's generation plus its size at scan
  time). `append_epoch` compares the recorded identity to the current active
  segment before trusting `scanned_offset`. If the active segment was replaced by
  a rollover between preflight and append (identity mismatch) — including an
  equal-sized replacement or a larger replacement whose bytes belong to a
  different file — the offset optimization is **invalidated** and the append
  performs a full cross-segment rescan. An offset is only ever reused when it
  belongs to the *same* active-segment generation. This closes the "equal-sized
  replacement skips rescanning / larger replacement resumes at a stale offset"
  gap.
* Sealed segments are immutable and scanned fully (they never change), so no
  offset optimization is needed for them.
* **Documented horizon bound:** replay/conflict guarantees hold only for epochs
  still inside the retention window. Once the segment carrying an `epoch_id` is
  pruned, a later replay of that `epoch_id` can no longer be detected and would be
  appended as new. This is acceptable for a best-effort mirror (SQLite remains
  authoritative and deduplicates on read) and MUST be stated explicitly in code
  docs and tests.

### Writer model — single-writer-per-path contract (findings A + B, round 2, DEFINITIVE)

The prior "best-effort generation + retention slack" wording implied cross-process
immutability without either a lock or a stated writer contract. That was correctly
rejected. This pass makes **one definitive decision, grounded in the code**:
**Option B — the sink's contract is single-writer-per-path.** See the
"Writer-model decision" section below for the code evidence. Concurrent
multi-**process** writers to the same JSONL path are **explicitly OUT OF
CONTRACT**.

Under this contract the rollover protocol needs **no interprocess lock**, and both
findings dissolve on the merits rather than by hand-waving:

* **Immutability is by sequential construction (finding B).** The single writer
  executes each epoch as a strict, non-overlapping sequence:
  `preflight → [if active ≥ _MAX_SEGMENT_BYTES: rename active → gen N, create fresh
  active, prune] → append to the current active segment`. Each append is a
  synchronous `open(O_APPEND) → write one line → close`; **no `O_APPEND` handle is
  ever held across a rename.** Therefore the writer never appends to a segment
  after sealing it — a sealed segment is byte-for-byte stable for the rest of its
  life. There is no open-before-rollover / append-after-rename inode race, because
  there is no second writer and no outstanding handle. "Retention slack closes the
  race" is **removed**; immutability holds by construction, not by slack.
* **No destination-collision (finding A).** With a single writer, two writers can
  never choose the same next generation. Additionally, rollover seals to
  `max(existing sealed generation) + 1`, a name that does not already exist, so the
  rename never overwrites an existing sealed segment even in the presence of a
  stale/leftover file at a lower generation.
* **Atomic line integrity is retained as defense-in-depth, not a rollover
  guarantee.** The existing atomic append (`O_APPEND` / Win32 `FILE_APPEND_DATA`)
  and the existing preflight/replay + `TelemetryConflictError` machinery stay. Per
  the current `append_epoch` docstring, if an *accidental* second writer ever
  appends concurrently, the worst case is a duplicate intact line that readers
  **reconcile on read** (epoch-id dedupe, SQLite-over-JSONL precedence) — this is
  the codebase's existing, deliberate stance and is preserved. We do **not**
  upgrade that into a rollover/immutability guarantee, and multi-process rollover
  remains out of contract.
* **The only loss is retention pruning (documented horizon).** A line is dropped
  only when its segment is later pruned — the intended retention behavior. SQLite
  remains the authoritative, lossless store.

**Tests for this model:** (1) rollover between preflight and append *within one
writer* — replay/conflict still detected (preflight generation identity, finding
6); (2) sealed-segment immutability — after a rollover, subsequent appends target
only the new active segment and the sealed segment's bytes are unchanged; (3)
next-generation naming never targets an existing sealed name (no-clobber by
construction). We do **not** write a concurrent-multi-writer rollover test, because
that scenario is out of contract; we test the single-writer sequence that the
production caller actually exercises.

### Segment size bound — restated to what the code can guarantee (finding 5)

`append_epoch` accepts an unconstrained encoded record and atomicity forbids
splitting a line, so an exact `_MAX_SEGMENT_BYTES` ceiling is not achievable. Under
the single-writer contract the bound is fully deterministic:

* **Oversized single record:** a record whose encoded line is larger than
  `_MAX_SEGMENT_BYTES` is still written **intact as one line to its own segment**
  (that segment is then sealed on the next append). Lines are never split.
* **Sealed segment size:** a sealed segment's size is ≤
  `_MAX_SEGMENT_BYTES + one max record` (the size check is evaluated before each
  sequential append, so at most one over-threshold record is added before sealing).
* **Total retained bytes:** ≤ `(_MAX_RETAINED_SEGMENTS + 1) × (_MAX_SEGMENT_BYTES
  + one max record)`.

Acceptance criteria assert this sequential bound (segment ≤ threshold +
one record after sealing; total retained ≤ `(window+1) × (threshold + one
record)`), and a test covers the oversized-single-record case. This replaces the
earlier, unachievable "total bytes ≤ `(window+1) × threshold`" claim.

## Width isolation

Telemetry subsystem only. Files touched:

* `src/autoharness/telemetry/jsonl_sink.py` — segment model/generation, rollover,
  retention, cross-segment replay + preflight identity (constants, no config).
* `src/autoharness/telemetry/reader.py` — read-path across rotated segments
  (finding 3; see Scope change below).
* `tests/test_telemetry_jsonl_sink.py` and a sibling reader test module.

No changes to `epoch.py`, `record.py`, aggregation, `config.py`, schemas, CLI, or
templates. No refactor of unrelated telemetry code. **Scope expansion vs. the
original plan:** `reader.py` is now in scope (finding 3) — still inside
`src/autoharness/telemetry/`. Config/schema files remain OUT of scope by the
finding-2 decision.

## Scope change from review (PR #249, finding 3): reader read-path

`reader.py::_read_jsonl` opens only `config.jsonl_path` (the active segment,
`reader.py:204-221`). Without reader support, after any rollover the
`source="jsonl"` (and the jsonl half of `source="combined"`) read path silently
returns only the fresh active segment and **loses rotated history** — a
correctness defect for a rotation feature whose whole purpose is to retain
bounded history. Decision: **include reader support** (new task 095.004-T). The
reader enumerates active + retained sealed segments via the shared segment
enumeration in `jsonl_sink.py`, preserving the existing `_dedupe` / `_combine`
precedence and malformed-line skipping. The public read contract is unchanged
except that it now correctly spans retained segments. The 100-S manifest gains
095.004-T (see Harvest model).

## Writer-model decision (PR #249 round 2, findings A + B) — code evidence

**Decision: Option B — single-writer-per-path contract.** Determined from the
code, not assumed:

* **Production caller is a sequential single process.** The only caller of
  `record_epoch` is `autoharness.eval.runner.run_matrix` (`eval/runner.py:189`),
  which iterates `for config in matrix.configs:` and calls
  `record_epoch(epoch, telemetry_config)` **sequentially** — no `ProcessPool`,
  `ThreadPool`, `concurrent.futures`, or `multiprocessing` anywhere in the call
  path.
* **The module contract is explicitly "no execution loop."** `record.py`'s module
  docstring states autoharness is an install/tune tool with *"no in-process
  execution loop to wrap"* and that the runtime *"supplies a fully-formed epoch
  payload at task close"*, fanned out to sinks, fail-open and off the critical
  path.
* **No locking primitive exists to reuse.** A repo-wide search of `src/` for
  `flock` / `msvcrt` / `O_EXCL` / `fcntl` / `portalocker` / `filelock` /
  `threading.Lock` / `multiprocessing` returns nothing — the codebase has never
  needed interprocess write serialization for telemetry.
* **Idempotency ≠ multi-writer serialization.** The existing preflight/replay +
  `TelemetryConflictError` machinery defends **re-emission/retry** of the same
  `epoch_id` (idempotent replay) and **payload immutability** (a conflicting digest
  for the same id). `append_epoch`'s own docstring says two processes writing the
  same epoch concurrently *"can each pass the check and produce a duplicate line …
  benign by design … reconciled on read rather than by locking this secondary
  sink."* The codebase therefore **already declines** to serialize concurrent
  writers and handles the rare accidental case by read-time reconciliation. This
  is direct evidence that the intended model is single-writer, with concurrency
  treated as benign-and-reconciled, not lock-protected.

Because no production path creates concurrent multi-process writers to one JSONL
path, **Option A (interprocess rollover lock + `O_EXCL` no-replace claim) would add
a lock for a scenario the code never produces** — more complexity, no correctness
gain. Option B is the simplest *correct* model.

**Contract statement (goes into code docs, `095-F`, and affected task specs):**
The JSONL sink is **single-writer-per-path**: at most one sink instance / one
process appends a given `jsonl_path` at a time, as the production caller
(`run_matrix`, sequential, single process) guarantees. Under this contract sealed
segments are **immutable by construction** (the writer never appends to a segment
after sealing it) and rollover needs no lock. **Concurrent multi-process writers to
the same path — during rollover or otherwise — are OUT OF CONTRACT.** The
pre-existing atomic-append line-integrity property is retained as defense-in-depth
(and the pre-existing multi-thread line-integrity test stays green because the
default threshold keeps it in the single-active-segment regime), but it is not
elevated into a rollover or immutability guarantee.

## Plan hardening record (P-006 — formally applied; updated round 2)

This plan qualifies for P-006 hardening: review surfaced concurrency and
correctness findings and the reader read-path expands blast radius within the
telemetry subsystem. Hardening applied:

* **Finding 2 → constants, not config.** Avoids a four-schema + config + caller
  blast radius; keeps width isolation. Encoded in the design and acceptance
  criteria (no configurability claimed).
* **Finding 3 → reader task added (095.004-T).** History survives reads across
  rotation; manifest and dependency order updated.
* **Findings A + B (round 2) → single-writer-per-path contract (Option B).** The
  definitive writer-model decision above, driven by code evidence. Immutability is
  by sequential construction (no open-before-rollover race under one writer); the
  destination-collision case cannot arise (one writer, `max+1` no-clobber naming);
  no interprocess lock is introduced. The earlier "generation + retention slack"
  survival claim is **removed and replaced** by the contract-based invariant. Out-
  of-contract multi-process concurrency is stated explicitly.
* **Finding 6 → preflight generation identity (kept, still relevant).** Within one
  writer a rollover can occur between the preflight scan and the append; the
  generation+size identity in the preflight token invalidates a stale offset and
  forces a full rescan, preserving replay/conflict detection.
* **Finding 5 → restated, achievable byte bound** (threshold + one max record;
  oversized record → own intact segment) — now fully deterministic under the
  single-writer sequence.
* **Finding 1 → traceability fixed** (`095-F` covering feature; `095.001-T…
  095.004-T` tasks; `100-S` shipment) throughout this plan and all task specs.

Residual risk after hardening: none open. The one bounded limitation is the
documented retention horizon (a pruned epoch may re-append; SQLite is
authoritative) and the explicit out-of-contract status of concurrent multi-process
writers. No open design decisions remain.

## Test-first (P-002 / P-004)

Every task is TDD: write failing tests first (red), implement, green. Canonical
full-suite gate for this repo is `PYTHONPATH=src python -m unittest discover -s
tests` (see compound `097-S-canonical-unittest-gate`); the targeted module is
`tests/test_telemetry_jsonl_sink.py` (runnable via
`python -m unittest tests.test_telemetry_jsonl_sink`).

## Harvest model (dependency-ordered, ≤2h / ≤3 files / ≤5 funcs / ≤4 scenarios each)

Linear dependency chain: 095.001-T → 095.002-T → 095.003-T → 095.004-T. Each task
leaves the full suite green.

* **095.001-T — Segment model + cross-segment replay with preflight generation
  identity.** Introduce segment enumeration + monotonic generation naming
  (module constants) and extend the replay lookup (`scan_epoch_digest` /
  `find_epoch_digest`) to scan the active + sealed segments. Add the
  generation+size identity to `JsonlPreflightScan` and invalidate the
  `scanned_offset` optimization on identity mismatch (full rescan). No rollover
  code yet; the identity-mismatch path is tested by simulating an active-segment
  replacement. Files: `jsonl_sink.py`, test. Scenarios (≤4): idempotent replay
  when epoch lives in a sealed segment; conflict detected across segments; active
  segment replaced between preflight and append → replay/conflict still detected
  (stale-offset invalidated); single-segment behavior unchanged.
* **095.002-T — Size-based rollover on write (single-writer contract).** Seal the
  active segment to `max(sealed generation)+1` when it reaches `_MAX_SEGMENT_BYTES`
  (a name that does not already exist → no clobber); create a fresh active;
  oversized single record still written intact to its own segment. Under the
  single-writer-per-path contract the writer's sequence is strictly
  size-check → rename → create-fresh → append, with no `O_APPEND` handle held
  across the rename, so sealed segments are immutable **by construction** (no lock,
  no in-flight-append race). Depends on 095.001-T. Files: `jsonl_sink.py`, test.
  Scenarios (≤4): rollover triggers at a low (patched) threshold → sealed
  generation + fresh active; default high threshold leaves current small writes
  single-segment (existing behavior preserved, incl. the existing multi-thread
  line-integrity test); sealed-segment immutability — after rollover, subsequent
  appends target only the new active segment and the sealed segment's bytes are
  unchanged; oversized single record (> threshold) written intact to its own
  segment.
* **095.003-T — Bounded retention / pruning + restated byte bound.** Keep ≤
  `_MAX_RETAINED_SEGMENTS` sealed segments, pruning oldest generations first.
  Assert the deterministic single-writer bound. Depends on 095.002-T. Files:
  `jsonl_sink.py`, test. Scenarios (≤4): sealed count never exceeds the window and
  oldest pruned first; total retained bytes ≤ `(window+1) × (threshold + one
  record)`; a sealed segment is ≤ `threshold + one max record`; pruned-epoch
  horizon — replay of a pruned epoch re-appends (no false idempotency).
* **095.004-T — Reader read-path across rotated segments (finding 3).** Extend
  `reader.py::_read_jsonl` (and its source wiring) to enumerate + read active +
  retained sealed segments via the shared `jsonl_sink` enumeration, preserving
  existing dedupe/precedence/malformed-line skipping. Depends on 095.003-T (so
  real rotated + pruned segments exist to read). Files: `reader.py`, sibling
  reader test module (+ import from `jsonl_sink`). Scenarios (≤4): after rollover,
  `source="jsonl"` returns records from active + sealed segments (no history
  loss); dedupe/precedence preserved across segments; malformed line in a sealed
  segment skipped, others returned; records in a pruned segment are absent
  (consistent with the retention horizon).

## Plan-review verdict (re-run on hardened plan)

Multi-persona inline review (personas per Stage plan-review contract):

| Persona | Verdict |
|---|---|
| Python Reviewer | PASS — four focused tasks; constants (not config) match the code path; each task ≤3 files / ≤5 funcs / ≤4 scenarios. |
| Scope Boundary Auditor | PASS — width-isolated to `jsonl_sink.py` + `reader.py` + tests (telemetry subsystem); config/schema files explicitly out of scope per finding-2 decision; reader expansion justified and flagged. |
| Concurrency/Safety Reviewer | PASS — writer model is a code-evidenced single-writer-per-path contract; sealed-segment immutability holds by sequential construction (no lock, no open-before-rollover race); the same-generation destination collision cannot arise (one writer, `max+1` no-clobber naming); concurrent multi-process writers are explicitly out of contract; byte bound restated to an achievable, deterministic value. |
| Architecture Strategist | PASS — one shared generation identity unifies preflight token, rollover, and pruning (findings 6 + naming); replay-across-segments precedes rollover; reader task last so it reads real rotated history; every task leaves the suite green. |
| Learnings Researcher | PASS — applies 097-S task-only-manifest and canonical-unittest-gate learnings; retention/replay horizon documented and tested. |

**Findings: P0=0, P1=0.** All six round-1 PR #249 findings plus the two round-2
convergence findings (A: destination collision; B: sealed-segment immutability)
are resolved with one coherent, code-evidenced decision: the
single-writer-per-path contract (Option B). No over-claim of cross-process
losslessness remains; no open design decisions. P-006 hardening formally applied
(see Plan hardening record).
