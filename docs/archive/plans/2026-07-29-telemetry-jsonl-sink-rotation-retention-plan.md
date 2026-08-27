---
title: Telemetry JSONL sink rotation + retention policy
doc_type: plan
status: reviewed
created: 2026-07-29
source_stash_id: 7D1E2F1A
prior_work: 092-F / 097-S (PR #241, telemetry subsystem hardening)
covering_feature: 095-F
shipment: 100-S
hardened: 2026-07-29 (P-006, per PR #249 Copilot review — round 1: 6 findings; round 3: best-effort concurrent-writer mirror + no-replace rollover, findings A + B)
shipped: 2026-07-29 (PR #250, merge commit ac94a3f — dark mode; tasks 095.001-T..095.004-T)
---

# Plan: Rotation + retention for the telemetry JSONL sink

## Problem

`src/autoharness/telemetry/jsonl_sink.py` appends each `ExecutionEpoch` as one
JSON line to a single `execution_epochs.jsonl` mirror with **no** size- or
age-based rollover, **no** retention window, and **no** compaction. The mirror
therefore grows unbounded beside the authoritative SQLite store. This was
explicitly deferred as out-of-scope from shipment 097-S / feature 092-F to keep
that shipment width-isolated (see
`docs/archive/plans/2026-07-28-telemetry-followup-hardening-plan.md` §Out of scope).

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
* Rollover only **renames whole segment files** and never rewrites or compacts
  line content, so it keeps the existing atomic-append and replay contracts intact
  — compaction would rewrite history and fight the first-write-immutable invariant
  of the authoritative SQLite store. (Sealed segments are treated as append-only
  and are not rewritten; the sink does not, however, *guarantee* byte-immutability
  of a sealed segment against a late concurrent `O_APPEND` — see the Writer model.)

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
that the preflight token, rollover, and pruning all agree on. Sealing uses a
**no-replace atomic generation claim** (below): the active file is sealed to
`max(existing sealed generation) + 1` via an operation that **fails rather than
clobbers** if that generation name already exists, so a concurrent rollover can
never overwrite an already-sealed segment — without a global lock.

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
* Sealed segments are **not treated as strictly immutable**; they are scanned
  fully (no offset optimization is applied to them). A late `O_APPEND` into a
  just-sealed segment by a writer that opened the active fd before rollover is
  **acceptable under the sink's contract** (see Writer model) and is reconciled on
  read against SQLite, so no offset assumption about sealed segments can be
  violated.
* **Documented horizon bound:** replay/conflict guarantees hold only for epochs
  still inside the retention window. Once the segment carrying an `epoch_id` is
  pruned, a later replay of that `epoch_id` can no longer be detected and would be
  appended as new. This is acceptable for a best-effort mirror (SQLite remains
  authoritative and deduplicates on read) and MUST be stated explicitly in code
  docs and tests.

### Writer model — best-effort concurrent-writer mirror, no-replace rollover (findings A + B, round 3, DEFINITIVE)

A prior pass proposed a single-writer-per-path contract. That was **refuted by the
code** and is **withdrawn**: `autoharness telemetry record`
(`cli.py:934` → `record_epoch` at `cli.py:1003`) is a **second public writer entry
point** besides `eval/runner.py::run_matrix`, so overlapping CLI processes can
append the same JSONL path concurrently. The sink's own docstrings state its
**deliberate** contract:

* `jsonl_sink.py:96-104` (`_atomic_append_bytes`): a line is "a single atomic
  write, **safe for concurrent writers**" (POSIX `O_APPEND` atomic; Windows
  `FILE_APPEND_DATA` atomic).
* `jsonl_sink.py:161-171` (`append_epoch`): two processes writing the same
  `epoch_id` "can each pass the check and produce a duplicate line. That is
  **benign by design** — JSONL is a best-effort human-readable mirror, while
  SQLite is the authoritative first-write-immutable store. Readers deduplicate by
  `epoch_id` and apply SQLite-over-JSONL precedence … reconciled on read rather
  than by locking this secondary sink."

So the sink's **real, intentional contract** is: *best-effort concurrent-writer
JSONL mirror + SQLite authoritative + reconcile-on-read*, and it **deliberately
declines to lock**. Rotation MUST preserve this contract — not swap in a
single-writer model and not over-claim immutability. **Option A (minimal,
contract-aligned)** is adopted: make the genuinely dangerous rollover operations
race-safe *without* a global lock, and frame the residual best-effort behavior as
exactly the sink's existing documented contract.

* **No-replace atomic generation claim for sealing (finding A — rename-replace
  collision).** Sealing the active file to `gen-N` MUST use an operation that
  **fails rather than clobbers** if `gen-N` already exists — e.g. `os.link(active,
  sealed_gen_N)` then unlink the active name, or an `O_EXCL` / Win32 `CreateFileW
  CREATE_NEW` claim of the sealed name, or rename-to-unique-then-verify. On
  collision (another writer already claimed `gen-N`), the loser re-reads
  `max(existing sealed generation)` and **retries with the next generation**.
  Result: a concurrent rollover can **never** overwrite or lose an already-sealed
  segment, and it needs **no global lock**. This directly answers finding A: a
  plain `rename` that silently replaces the destination is forbidden.
* **No "sealed = immutable" claim; state the ACTUAL semantics (finding B — late
  `O_APPEND` into a sealed inode).** A writer that opened the active fd before
  rollover and appends after the rename lands a line in the just-sealed segment.
  Under this sink's contract that is **acceptable and not a correctness
  violation**, because: (a) JSONL is a best-effort mirror; (b) SQLite is
  authoritative and first-write-immutable; (c) readers dedupe by `epoch_id` and
  apply SQLite-over-JSONL precedence; and (d) the replay/preflight scan is an
  **optimization over the mirror, not the source of truth** — a scan that races a
  late line is reconciled on the next read against SQLite. Every "sealed segments
  are immutable / rollover is lossless" statement is **replaced** by this
  contract-aligned wording. We do **not** add a writer-drain lock the sink
  deliberately avoids.
* **Pruning is by-design lossy on the MIRROR, and that is the point.** Pruning
  removes only **sealed** segments beyond the retention window and **never** the
  active segment. Losing old *mirror* segments is the intended retention behavior;
  **SQLite retains authoritative history**, so pruning never deletes authoritative
  data. A prune racing a late append into a to-be-pruned sealed segment only drops
  best-effort mirror lines already superseded by SQLite — acceptable under
  contract. For extra safety, prune oldest-first and never prune a segment sealed
  within the current rollover critical section.
* **Preflight generation identity stays (finding 6), framed as a mirror-scan
  optimization.** The preflight token carries generation + size so a rotation
  between preflight and append forces a rescan for JSONL replay-check accuracy;
  correctness ultimately rests on SQLite.

**Tests for this model** (these replace the single-writer-only tests): (1)
**simultaneous destination-collision** — two writers pick the same next generation
→ the no-replace claim makes one retry the next generation; **both** sealed
segments are preserved, zero whole-segment loss; (2) **late-append-into-sealed
reconciled on read** — a line that lands in a sealed segment after rollover is
still correctly deduped with SQLite-over-JSONL precedence by the reader; (3)
**rollover between preflight and append** — replay/conflict still detected via the
preflight generation identity (finding 6).

### Segment size bound — restated to what the code can guarantee (finding 5)

`append_epoch` accepts an unconstrained encoded record and atomicity forbids
splitting a line, so an exact `_MAX_SEGMENT_BYTES` ceiling is not achievable. The
bound is stated as:

* **Oversized single record:** a record whose encoded line is larger than
  `_MAX_SEGMENT_BYTES` is still written **intact as one line to its own segment**
  (that segment is then sealed on the next append). Lines are never split.
* **Sealed segment size:** a sealed segment's size is ≤
  `_MAX_SEGMENT_BYTES + one max record` (the size check is evaluated before an
  append, so at most one over-threshold record is added before sealing; a
  benign concurrent duplicate is itself ≤ one max record and is superseded on
  read).
* **Total retained bytes:** ≤ `(_MAX_RETAINED_SEGMENTS + 1) × (_MAX_SEGMENT_BYTES
  + one max record)`.

Acceptance criteria assert this bound (segment ≤ threshold + one record after
sealing; total retained ≤ `(window+1) × (threshold + one record)`), and a test
covers the oversized-single-record case. This replaces the earlier, unachievable
"total bytes ≤ `(window+1) × threshold`" claim.

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

## Writer-model decision (PR #249 round 3, findings A + B) — code evidence

**Decision: Option A — best-effort concurrent-writer mirror with a no-replace
rollover claim.** A round-2 pass asserted a single-writer-per-path contract; it is
**withdrawn as refuted by the code**:

* **A second public writer entry point exists.** Besides
  `eval/runner.py::run_matrix`, the CLI subcommand `autoharness telemetry record`
  (`cli.py:934` `_telemetry_record_command` → `record_epoch` at `cli.py:1003`)
  records an epoch to the configured sink. **Overlapping CLI invocations can append
  the same JSONL path concurrently**, so "the only caller is a sequential single
  process" is false.
* **The sink documents concurrent writers as SUPPORTED BY DESIGN.**
  `_atomic_append_bytes` (`jsonl_sink.py:96-104`) is "a single atomic write,
  **safe for concurrent writers**" (POSIX `O_APPEND`; Windows `FILE_APPEND_DATA`).
  `append_epoch` (`jsonl_sink.py:161-171`) states two processes writing the same
  `epoch_id` "can each pass the check and produce a duplicate line … **benign by
  design** — JSONL is a best-effort human-readable mirror, while SQLite is the
  authoritative first-write-immutable store. Readers deduplicate by `epoch_id` and
  apply SQLite-over-JSONL precedence … reconciled on read rather than by locking
  this secondary sink."
* **The absence of a lock is intentional, not an oversight.** The sink
  *deliberately declines* to serialize concurrent writers and instead reconciles
  duplicates on read. That is the contract rotation must preserve — not replace
  with a single-writer model, and not over-claim as immutability.

**Why Option A (minimal) and not a full interprocess lock:** the only genuinely
dangerous rollover operation is **sealing** — a plain `rename` that silently
replaces an existing destination could destroy an already-sealed segment (finding
A). That is fixed precisely by a **no-replace atomic generation claim** (fail-and-
retry-next-generation), which needs no global lock. The late-append-into-sealed
race (finding B) is **not a correctness violation** under the sink's contract
because the JSONL mirror is best-effort and SQLite is authoritative with read-time
reconciliation — so adding a writer-drain lock the sink deliberately avoids would
be contract-violating over-engineering. Option A closes the dangerous case and
frames the residual behavior as exactly the sink's existing documented semantics.

**Contract statement (goes into code docs, `095-F`, and affected task specs):**
The JSONL sink is a **best-effort, concurrent-writer-safe human-readable mirror**;
SQLite is the authoritative first-write-immutable store, and duplicate/late mirror
lines are **reconciled on read** (`epoch_id` dedupe + SQLite-over-JSONL
precedence). Rotation preserves this: sealing uses a **no-replace generation
claim** so a concurrent rollover never clobbers a sealed segment; sealed segments
are **not claimed to be immutable** (a late `O_APPEND` into a sealed inode is
acceptable and reconciled on read); pruning removes only **sealed** segments beyond
the retention window (never the active segment, never authoritative SQLite data).
No global write lock is introduced, matching the sink's deliberate design.

## Plan hardening record (P-006 — formally applied; updated round 3)

This plan qualifies for P-006 hardening: review surfaced concurrency and
correctness findings and the reader read-path expands blast radius within the
telemetry subsystem. Hardening applied:

* **Finding 2 → constants, not config.** Avoids a four-schema + config + caller
  blast radius; keeps width isolation. Encoded in the design and acceptance
  criteria (no configurability claimed).
* **Finding 3 → reader task added (095.004-T).** History survives reads across
  rotation; manifest and dependency order updated.
* **Findings A + B (round 3, PIVOT) → best-effort concurrent-writer mirror with a
  no-replace rollover claim (Option A).** A round-2 single-writer-per-path claim
  (Option B) was **refuted by the code** (`cli.py:934/1003` is a second public
  `record_epoch` entry point; `jsonl_sink.py:96-104` / `:161-171` document
  concurrent writers as safe/benign-by-design with read-time reconciliation) and
  is **withdrawn**. Finding A (rename-replace collision) is answered by a
  **no-replace atomic generation claim** (`os.link`/`O_EXCL`/`CREATE_NEW`; loser
  retries next generation) — a concurrent rollover can never clobber a sealed
  segment, without a global lock, and a deterministic simultaneous-collision test
  proves it. Finding B (late `O_APPEND` into a sealed inode) is answered by
  **dropping the immutability over-claim** and stating the sink's actual contract:
  the mirror is best-effort, SQLite is authoritative, a late line is reconciled on
  read; a reader test proves dedup + SQLite-over-JSONL precedence still hold. No
  writer-drain lock is added (the sink deliberately avoids locking).
* **Finding 6 → preflight generation identity (kept), framed as a mirror-scan
  optimization.** A rollover between the preflight scan and the append invalidates
  a stale offset via the generation+size identity and forces a full rescan for
  JSONL replay-check accuracy; correctness ultimately rests on SQLite.
* **Finding 5 → restated, achievable byte bound** (threshold + one max record;
  oversized record → own intact segment; a benign concurrent duplicate is ≤ one
  max record and superseded on read).
* **Finding 1 → traceability fixed** (`095-F` covering feature; `095.001-T…
  095.004-T` tasks; `100-S` shipment) throughout this plan and all task specs.

Residual risk after hardening: none open. The bounded, contract-aligned
limitations are (a) the documented retention horizon (a pruned mirror epoch may
re-append; SQLite is authoritative) and (b) the sink's deliberate best-effort
concurrent-writer semantics (duplicate/late mirror lines reconciled on read, not by
locking). Both are the sink's **existing documented contract**, not new
over-claims. No open design decisions remain.

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
* **095.002-T — Size-based rollover on write with a no-replace generation claim.**
  When the active segment reaches `_MAX_SEGMENT_BYTES`, seal it to
  `max(existing sealed generation)+1` using a **no-replace atomic claim**
  (`os.link`+unlink / `O_EXCL` / Win32 `CREATE_NEW`, or rename-to-unique-then-
  verify) so an existing sealed name is **never** clobbered; on collision the loser
  re-reads `max(sealed generation)` and retries the next generation. Create a fresh
  active; an oversized single record is still written intact to its own segment.
  Preserves the sink's best-effort concurrent-writer contract — no global lock; a
  late `O_APPEND` into a just-sealed segment is acceptable (reconciled on read),
  not a violation. Depends on 095.001-T. Files: `jsonl_sink.py`, test. Scenarios
  (≤4): rollover triggers at a low (patched) threshold → sealed generation + fresh
  active; **simultaneous destination-collision** — two writers pick the same next
  generation → no-replace claim forces one to retry, both sealed segments preserved
  (zero whole-segment loss); default high threshold leaves current small writes
  single-segment (existing behavior preserved, incl. the existing multi-thread
  line-integrity test); oversized single record (> threshold) written intact to its
  own segment.
* **095.003-T — Bounded retention / pruning + restated byte bound.** Keep ≤
  `_MAX_RETAINED_SEGMENTS` sealed segments, pruning **oldest sealed** generations
  first; **never** prune the active segment and never a segment sealed within the
  current rollover critical section. Pruning is by-design lossy on the *mirror*
  only — SQLite retains authoritative history, so no authoritative data is deleted.
  Assert the restated bound. Depends on 095.002-T. Files: `jsonl_sink.py`, test.
  Scenarios (≤4): sealed count never exceeds the window and oldest pruned first;
  total retained bytes ≤ `(window+1) × (threshold + one record)` and a sealed
  segment is ≤ `threshold + one max record`; pruning never targets the active
  segment; pruned-epoch horizon — replay of a pruned mirror epoch re-appends (no
  false idempotency; SQLite authoritative).
* **095.004-T — Reader read-path across rotated segments + late-line reconciliation
  (finding 3, and finding B reconciliation).** Extend `reader.py::_read_jsonl`
  (and its source wiring) to enumerate + read active + retained sealed segments via
  the shared `jsonl_sink` enumeration, preserving existing
  dedupe/precedence/malformed-line skipping. Depends on 095.003-T (so real rotated
  + pruned segments exist to read). Files: `reader.py`, sibling reader test module
  (+ import from `jsonl_sink`). Scenarios (≤4): after rollover, `source="jsonl"`
  returns records from active + sealed segments (no history loss);
  **late-line-into-sealed reconciled on read** — a line that landed in a sealed
  segment after rollover is correctly deduped with SQLite-over-JSONL precedence;
  malformed line in a sealed segment skipped, others returned; records in a pruned
  segment are absent (consistent with the retention horizon).

## Plan-review verdict (re-run on hardened plan)

Multi-persona inline review (personas per Stage plan-review contract):

| Persona | Verdict |
|---|---|
| Python Reviewer | PASS — four focused tasks; constants (not config) match the code path; each task ≤3 files / ≤5 funcs / ≤4 scenarios. |
| Scope Boundary Auditor | PASS — width-isolated to `jsonl_sink.py` + `reader.py` + tests (telemetry subsystem); config/schema files explicitly out of scope per finding-2 decision; reader expansion justified and flagged. |
| Concurrency/Safety Reviewer | PASS — writer model is the sink's **code-documented best-effort concurrent-writer contract** (SQLite authoritative, reconcile-on-read); the genuinely dangerous seal operation uses a **no-replace generation claim** (finding A) proven by a simultaneous-collision test; the late-append-into-sealed race (finding B) is correctly framed as acceptable-and-reconciled rather than an over-claimed immutability, with a reader reconciliation test; pruning is bounded to old sealed segments and never the active segment or SQLite; byte bound restated to an achievable value. No single-writer or immutability over-claim remains. |
| Architecture Strategist | PASS — one shared generation identity unifies preflight token, rollover, and pruning (finding 6 + naming); replay-across-segments precedes rollover; reader task last so it reads real rotated history; every task leaves the suite green. |
| Learnings Researcher | PASS — applies 097-S task-only-manifest and canonical-unittest-gate learnings; retention/replay horizon documented and tested. |

**Findings: P0=0, P1=0.** All six round-1 PR #249 findings plus the two round-2/3
convergence findings (A: destination collision; B: sealed-segment immutability) are
resolved with one coherent, code-evidenced decision: **Option A — preserve the
sink's best-effort concurrent-writer mirror contract, make sealing race-safe via a
no-replace generation claim, and drop the single-writer/immutability over-claims.**
No guarantee is asserted that the design cannot deliver. P-006 hardening formally
applied (see Plan hardening record).
