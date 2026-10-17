---
title: "Deliberation: durable journaling, detached supervision, and honest recovery for cascade-close"
description: "Options, trade-offs and decisions for making the mutating `autoharness shipment cascade-close` survive a killed wrapper: child-output journaling, a detach/poll mode with a caller-wait pre-flight, and an idempotent `--recover` that reconstructs a provenance-marked post_close record without fabricating unobserved facts. Stash 369F8062 (mechanism) and E337551C (re-scoped to propagation/enforcement)."
doc_type: deliberation
date: 2026-10-16
stash_entries: [369F8062, E337551C]
source_incident: "shipment 214-S / feature 207-F (PR 531 merged; closure PR 532 merged)"
rca: docs/compound/2026-10-16-cascade-close-killed-mid-run-leaves-invoking-record-and-stale-lock.md
deliberation_id: 041-DL
status: decided
requires_plan_hardening: "yes"
---

# Deliberation: cascade-close journaling, detach/poll, and `--recover`

All times UTC. Dark-mode (P-017) staging: the operator is AFK-capable, so every decision below is
Stage's recommendation with the trade-off recorded; the items the operator may want to overturn are
listed in Open Questions and flagged again in the plan.

## Problem frame

Evidence from the 214-S incident (RCA above) and from reading the code:

* `command._invoke_and_finalize` writes the `invoking` record, then `runner.run_bounded` spawns
  `backlogit shipment ship` with **stdout/stderr as pipes owned by the wrapper**. If the wrapper dies, the
  child keeps running in its own process group but its pipes break: stdout (the only source of
  `archived_ids`/`returned_ids`), stderr, and the exit code (only `wait()` in the wrapper sees it) are lost.
* `check_existing_record` maps an `invoking` record to exit 7 and `acquire_pair_lock` maps an existing lock to
  exit 7; nothing in the product can move an `invoking` record forward except the dead run itself.
* `_check_cascade` (validator) requires `exit_code == 0`, `timed_out == false`, `mutation_state == completed`,
  populated stdout/stderr captures, and a parsed result with empty `returned_ids`; so even a perfectly
  verified live state cannot yield a gate-passing record without the lost facts.
* `pre_claim` (pipeline-topology) blocks successors with `PREDECESSOR_CLOSURE_INCOMPLETE` when the
  predecessor's closure evidence never reaches `post_close`.
* The existing guidance (shipment-reconcile Cascade Close Sub-Procedure, gates-reference "Timeout sizing") already
  mandates attached async execution and polling for the full supervision budget. The incident was a
  propagation/enforcement miss at the caller (RCA), so guidance alone is demonstrably insufficient and a
  mechanical guard is warranted.

New evidence found during this deliberation: the backlogit engine writes its **own** durable per-item event
logs under `<backlog root>/logs/*.jsonl` (`shipment_status_changed`, `archived`, `status_changed`,
`shipment_item_returned_blocked`, each carrying a `_shipment_operation` correlation and an offset-bearing
timestamp). That is an engine-authored record of what the cascade did that survives the wrapper, and it is
what makes `returned_ids` recoverable without inventing it (see D-6). Its exact event predicates are not yet
characterised, so the plan front-loads a read-only characterisation task (T1).

## Options and trade-offs

### Axis A: how to stop losing child output and exit code

| Option | Description | Pros | Cons |
|---|---|---|---|
| A1 Wrapper-side incremental copy | Keep pipes; reader threads append every chunk to journal files | Small change to `run_bounded`; keeps pipe semantics | Dies with the wrapper: bytes in flight and the exit code are still lost; the child gets EPIPE/SIGPIPE when the wrapper dies (can change the engine's behaviour mid-cascade) |
| **A2 OS-level redirection + exit sentinel (chosen)** | Child stdout/stderr are redirected by the OS straight to journal files; a small supervisor shim waits for the child and atomically writes `exit.json` | Nothing is in the wrapper's memory, so a wrapper kill loses nothing already written; no broken pipe; removes the `drain_incomplete` grandchild-pipe class; exit code durable when the shim survives | New process layer; unbounded disk growth needs a cap; raw (unredacted) output on disk needs 0600 + ignored dir; Windows job-object survival of the shim is unproven (probe + fail-closed fallback) |
| A3 Engine-side only | Rely entirely on the engine's own event logs | Zero wrapper change | Event logs do not carry stdout/stderr/exit code; no parse of the `ship` response |

### Axis B: how a caller wait shorter than the supervision budget stops being fatal

| Option | Description | Pros | Cons |
|---|---|---|---|
| B1 Docs only (status quo) | Guidance already says attached async + poll | No code | Demonstrably failed (214-S) |
| B2 Pre-flight only | Caller declares its maximum wait (`--caller-wait` or env); refuse when it is below `--timeout + 600` | Cheap, fail-closed, before any mutation | Needs the caller to declare; undeclared stays unprotected |
| **B3 Detach + poll with pre-flight (chosen)** | `--detach` does steps 1-7 in the foreground, hands the run (child, finalization, lock) to a detached supervisor process, and returns immediately; `--poll` reports status or the final exit code; B2 pre-flight refuses a declared insufficient wait in attached mode | A short caller wait can no longer kill the mutation; poll is idempotent and re-attachable across agent sessions | More moving parts (lock handoff, finalizer ownership); Windows breakaway uncertainty |
| B4 Refuse unless explicitly `--attached`/`--detach` | Make the choice mandatory | Closes the "undeclared" hole entirely | Breaking CLI contract for the one consumer (Ship); existing tests change. Recorded as open question OQ-1; default stays compatible |

### Axis C: what to do about an already-orphaned `invoking` record

| Option | Description | Pros | Cons |
|---|---|---|---|
| C1 Retry (re-run ship) | Idempotent retry of the engine call | Looks simple | Rejected: `backlogit shipment ship` is destructive and not idempotent over a half-applied state; re-running after exits 5-8 is forbidden for good reason |
| C2 Operator hand-edit | Operator writes the record | None | Rejected: fabrication; the record is "never hand-edited" |
| C3 New terminal phase `abandoned`/`recovered_unverified` | Close the record without post_close | Honest about unknowns | Cannot pass the closure-evidence gate, so successors stay blocked; kept only as the refusal path (nothing written) |
| **C4 `--recover` reconstruct with provenance (chosen)** | Verify live postconditions against the pre_close baseline, correlate with the engine event log and the journal, and write a schema-valid `post_close` marked recovered, with a per-field provenance map | Unblocks the pipeline without inventing facts; idempotent; reuses `evaluate_postconditions` | Schema/validator extension on a safety path; needs strict anti-laundering rules (D-4, D-7) |

### Axis D: schema evolution

| Option | Pros | Cons |
|---|---|---|
| **D1 Additive optional `recovery` block, `schema_version` stays 1 (chosen)** | Old records validate unchanged; an old validator reading a recovered record fails closed (null `exit_code`) rather than passing it | A reader that ignores unknown keys could miss the marker; mitigated: the gate emits an advisory and the validator is the only reader of record |
| D2 Bump `schema_version` to 2 | Explicit break | Breaks every existing committed record's validation unless dual-version; larger blast radius for no added safety |

## Decisions

* **D-1 (journal, A2).** Journal directory `.autoharness/gates/cascade-close/{S}-{F}.journal/` (git-ignored lock
  directory, trust-walked like the lock dir, files 0600): `meta.json` (run_id, redacted argv, effective timeout,
  declared caller wait, host, supervisor/child pid and start times), `stdout.raw`, `stderr.raw` (OS-redirected,
  append-only, capped), `exit.json` (exit code, finished_at, timed_out, written atomically by the shim), and
  `outcome.json` (final command exit code and message, written by the finalizer). Raw files may hold unredacted
  engine output: they are never committed; only redacted excerpts enter the evidence record (existing
  `redact`). Journals are retained on any non-success and removed on a clean exit-0 run by the owning run only.
* **D-2 (detach + poll, B3).** `--detach` (mutating mode only) and `--poll [--wait N]`. The detached supervisor owns
  the child, finalization (steps 9-10) and lock release; the lock payload is handed to the supervisor pid by
  an owner-bound atomic rewrite. If detached survival cannot be established (Windows breakaway refused),
  `--detach` exits 2 before the mutation and never silently degrades to attached.
* **D-3 (pre-flight).** `--caller-wait <seconds>` (or `AUTOHARNESS_CALLER_WAIT_SECONDS`): in attached mode, a declared wait below
  `timeout + SUPERVISION_MARGIN_SECONDS` exits 2 before any mutation. An undeclared wait is recorded in the journal as
  `undeclared` and produces a warning, not a refusal (compatibility; OQ-1).
* **D-4 (recovery contract).** `autoharness shipment cascade-close --recover` (plus `--dry-run`) is
  evidence-only: it never invokes backlogit, never moves/archives/edits a backlog artifact, and never re-runs
  ship. Eligibility is fail-closed and exact: evidence phase `invoking` for this pair; no `post_close`; run_id
  consistent; pre_close baseline present and valid; owner **provably dead** (D-5); engine quiescent (no
  journaled child alive, no `backlogit ... shipment ship <S>` process, live state stable across two reads
  separated by a settle window; a legacy record with no journal additionally needs an operator
  `--confirm-engine-stopped`). Anything else exits 10 (`RECOVERY_REFUSED`; exit 9 means started/still running for `--detach`/`--poll`) and writes nothing.
* **D-5 (stale-lock policy).** Automatic takeover happens **only inside `--recover`** and only when the lock owner is
  provably dead: same host and the pid is absent, or the pid exists but its recorded start time differs (pid
  reuse). Legacy locks without `host`/`pid_start` are never auto-cleared; they need operator
  `--confirm-owner-dead`. Takeover is an atomic rename of the stale lock to a tombstone
  (`{S}-{F}.lock.stale-{old_run_id}`) followed by an `O_EXCL` create, so concurrent recoverers race safely and the
  evidence of the takeover is preserved. A mutating run that meets a stale lock still exits 7, but reports
  `recovery_available: true`; it never auto-recovers and never re-invokes ship.
* **D-6 (returned_ids semantics).** Facts are classified per field: `observed_journal` (parsed from journaled
  stdout), `engine_event_log` (engine-authored events correlated by `_shipment_operation` and the invocation
  window; empty `shipment_item_returned_blocked` set means observed-empty), `derived_live_state` (a logical
  consequence of verified live postconditions, e.g. every required id archived and every non-allowed
  fingerprint unchanged implies nothing was returned that matters), or `unknown`. `unknown` is a legal value
  only inside a recovery block and only for fields the validator lists; nothing is ever defaulted to a success
  value.
* **D-7 (anti-laundering).** A `postconditions_only` recovery additionally requires engine attribution: at least one
  engine-authored `shipment_status_changed -> shipped` event for the shipment, with the shipment-operation correlation,
  after `invocation.started_at`. Without it the live state could have been produced by a human or another tool, so
  recovery refuses (exit 10). The recovered record carries `recovery.mode` (`journal_complete`, `journal_partial`,
  `postconditions_only`), `recovered_at`, `recovery_run_id`, `supersedes_run_id`, `lock_disposition`, and the
  per-field `facts` map; `exit_code`, `timed_out`, `finished_at` and the stdout/stderr captures may be null/unavailable
  only when the facts map marks them `unknown`, and `mutation_state` may be `completed` only from verified
  postconditions, never `none` for a recovered cascade.
* **D-8 (schema, D1).** Additive `recovery` block, `schema_version` unchanged. The validator's existing
  recomputation of allowed/required sets, set differences, drift and `shipment_archived_shipped` is unchanged and
  still applies to recovered records; recovery only relaxes the enumerated observed-fact fields.
* **D-9 (gate visibility).** The closure-evidence gate accepts a valid recovered record and surfaces
  `evidence_recovered: true` plus the recovery mode in its output. Requiring a closure-frontmatter acknowledgement is
  deferred as OQ-2 (default: advisory only; smaller contract surface).
* **D-10 (E337551C re-scope).** Re-scope to propagation and enforcement of guidance that already exists: the mutating
  run MUST use `--detach` + `--poll` (or attached with a sufficient declared `--caller-wait`); closure subagent
  delegation and Ship/operational-closure/circuit-breaker text carry the rule and the new exit-7-on-invoking routing
  (`--recover --dry-run`, operator approval for the write). Template + installed mirror + manifest checksums change
  together (dogfood parity).
* **D-11 (DAG placement).** The shipment is a **declared root** (`dag-root` label), not a `blocks` successor of 214-S.
  A `blocks` edge to 214-S would deadlock the very shipment that repairs 214-S's evidence
  (`PREDECESSOR_CLOSURE_INCOMPLETE`), and Genesis does not apply (many shipment records exist). `217-S` already
  uses the same root-label pattern. Stage may apply `dag-root`; Ship must not. Flagged: 215-S depends on 214-S and
  will stay blocked until 214-S's evidence is repaired by running the **new** `--recover` after this shipment
  merges; that repair is a separate Ship/closure action and an operator decision, not part of this shipment.

## Out of scope (P-021 deferrals, not captured here)

* Continuing or compensating a *partially applied* cascade (postconditions fail on live state): `--recover` records
  an honest `fail` verdict (exit 5) and stops. A forward-repair command is a separate deliberation.
* The broader stall-detection class (stash 9869AA32) and recording the effective timeout in evidence (A5FA81C4):
  the journal `meta.json` records the effective timeout and caller wait, but the evidence-schema field remains A5FA81C4.
* Normalising offset-bearing engine log timestamps for the committed evidence record (2C56E421): recovery converts to
  UTC instants for ordering and preserves the original string in the facts map.

## Open questions

* **OQ-1** Flip the default so mutating mode refuses unless `--detach` or `--attached` is chosen (B4)? Default here: no.
* **OQ-2** Require an explicit closure-artifact acknowledgement for recovered evidence in the closure-evidence gate? Default: advisory.
* **OQ-3** Approval class for `--recover` (write): default is the same destructive-command approval as
  `--classify-only --replace-pre-close` (it dispositions an audit record); `--dry-run` needs none.
* **OQ-4** Should 214-S itself be repaired by `--recover` after this ships, or kept as the disclosed `BLOCKED`
  precedent? Operator decision; not scoped here.
* **OQ-5** Windows: does the runtime's process tree/job object permit breakaway for the detached supervisor? T5/T7 probe it; the fail-closed fallback applies if not.

## Source references (P-021 C5/C6 reconciliation)

* 369F8062 and E337551C: originating PR 531 (merged) and, recovered late from the 214-S closure record, closure PR 532 (merged).
  Task N/A (closure-phase work), review-thread N/A (truthful terminal `N/A`), feature 207-F, shipment 214-S.
* Duplicate scan over all 289 active stash entries: clean (no second entry for this expansion). Related but distinct, not
  merged: 9869AA32, A5FA81C4, 2C56E421, E01BA307, 320499CC.
