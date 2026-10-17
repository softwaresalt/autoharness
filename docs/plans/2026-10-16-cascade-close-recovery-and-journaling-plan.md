---
title: "cascade-close durable journaling, detach/poll supervision, and provenance-marked --recover"
description: "Implementation plan making the mutating `autoharness shipment cascade-close` survive a killed wrapper: OS-level output journal with exit sentinel, detached supervisor with poll and a caller-wait pre-flight, an idempotent `--recover` that reconstructs a schema-valid post_close record marked recovered without fabricating unobserved facts, safe stale-lock takeover, validator extension, and propagated guidance. Stash 369F8062 (mechanism) and E337551C (re-scoped to propagation)."
date: 2026-10-16
status: reviewed
deliberation: "041-DL (docs/decisions/2026-10-16-cascade-close-recovery-and-journaling-deliberation.md)"
stash_entries: [369F8062, E337551C]
requires_plan_hardening: "yes"
plan_hardening_status: "hardened"
plan_hardening_record: docs/plans/2026-10-16-cascade-close-recovery-and-journaling-hardening.md
plan_review_verdict: "PASS"
plan_review_cycles: 2
tags: [plan, cascade-close, shipment-close, evidence-record, recovery, journaling, stale-lock, safety-critical, dogfood-parity]
---

## Problem Frame

During closure of 214-S the mutating `autoharness shipment cascade-close` was run synchronously and killed by the
runtime while `backlogit shipment ship` was mutating. The evidence record stayed `invoking`, the pair lock was
held by a dead pid, and stdout/stderr/exit code/`returned_ids` were lost; every sanctioned recovery was forbidden,
the closure-evidence gate requires a `post_close` record with observed facts, and `pre_claim` then blocks the
successor with `PREDECESSOR_CLOSURE_INCOMPLETE`.

Root cause (RCA): the command ran under a caller wait shorter than its own supervision budget. Contributing causes: no
durable capture independent of the wrapper process, no sanctioned recovery for an orphaned `invoking` record,
no caller-wait guard, and guidance that existed but was not propagated to the caller.

Full option analysis and decisions D-1..D-11: the deliberation. This plan implements the chosen direction.

### Code facts (read 2026-10-16)

| Concern | Current behaviour | File |
|---|---|---|
| Child capture | `run_bounded`: pipes + reader threads feeding `StreamCapture`; exit code and output only in wrapper memory | `shipment_close/runner.py` |
| Phases | `pre_close -> invoking -> post_close`, owner-bound atomic writes (`_OWNER_TRANSITIONS`), takeover only for `pre_close` | `shipment_close/persist.py` |
| Lock | `O_CREAT|O_EXCL` lock, payload `{run_id,pid,started_at}`; never auto-broken (exit 7) | `persist.py` |
| Existing record | `invoking` -> exit 7; `post_close` -> exit 2 | `persist.check_existing_record` |
| Postconditions | `evaluate_postconditions` (INV-10) over `ParsedResult` + `PostCloseReread`; pure, no I/O | `shipment_close/postclose.py` |
| Re-read | `command._reread`/`_recollect` rebuild the post-close state from the backlog dir | `shipment_close/command.py` |
| Validator | `_check_cascade` requires exit 0, not timed out, `completed`, populated captures, parsed result with empty `returned_ids`; recomputes derived fields | `gates/cascade_evidence.py` |
| Exit codes | 0,2..8 in use; 9 and 10 free | `shipment_close/__init__.py` |
| CLI | arg parsing and `--json` rendering | `src/autoharness/cli.py` (`_shipment_cascade_close_command`) |
| Engine event log | `<backlog root>/logs/*.jsonl`: `shipment_status_changed`, `archived`, `shipment_item_returned_blocked`, `_shipment_operation` correlation, offset-bearing timestamps | `.backlogit/logs/` (characterised in T1) |

## Requirements Trace

| # | Requirement (operator request) | Task(s) |
|---|---|---|
| R1 | Journal child stdout/stderr/exit incrementally to durable storage so a kill cannot lose them | T2, T5, T6 |
| R2 | Idempotent `--recover` for an `invoking` record with a dead lock owner: verify live postconditions vs pre_close baseline, write a schema-valid post_close marked recovered with provenance; never fabricate; fail closed when unverifiable | T1, T9, T10, T11, T12 |
| R3 | Safe automatic stale-lock handling only when owner provably dead and record recoverable; else operator review | T3, T4, T10 |
| R4 | Wrapper pre-flight / detachment so a short caller wait cannot kill it | T7, T8, T12 |
| R5 | Update Ship/shipment-reconcile guidance, template + installed mirrors + manifest checksums | T13, T14, T15 |
| R6 | Tests; canonical gate `PYTHONPATH=src python -m unittest discover -s tests` | every task, T16 |
| R7 | DAG placement of the new shipment defined and flagged | deliberation D-11, Shipment section |

## Scope Boundaries

* `--recover` never invokes backlogit, never moves/archives/edits a backlog artifact, never re-runs ship, never edits
  a deliberation. It writes the evidence record and (when taking over) moves the stale lock to a tombstone.
* No continuation/compensation of a partially applied cascade; an honest exit-5 `fail` record is the ceiling.
* No change to the classifier, engine-semantics gate, or SAFE_CLOSE path.
* `schema_version` stays 1 (additive `recovery` block).
* 214-S itself is not repaired by this shipment (OQ-4).
* Out of scope: stash 9869AA32, A5FA81C4, 2C56E421, E01BA307, 320499CC.

## Architecture

```text
cascade-close --detach (foreground: steps 1-7, writes invoking, spawns supervisor, returns exit 9 "started")
   `-> detached supervisor process  (owns lock, hands pid into lock payload)
         |- child: backlogit shipment ship   (stdout/stderr redirected by the OS to journal/*.raw)
         |- shim writes journal/exit.json atomically at child exit
         `- finalizer: steps 9-10 (re-read, INV-10, post_close write), journal/outcome.json, lock release
cascade-close --poll [--wait N]   idempotent: running(9) | outcome.json's exit code | supervisor dead -> 7 + recovery_available
cascade-close --recover [--dry-run]  evidence-only, fail closed, writes recovered post_close (or exit 9, nothing written)
```

Journal directory: `.autoharness/gates/cascade-close/{S}-{F}.journal/` (git-ignored via `.autoharness/gates/`):
`meta.json`, `stdout.raw`, `stderr.raw` (append-only, 0600, size-capped), `exit.json`, `outcome.json`.

New exit codes (9 and 10 are both free today; `operator_action` is `none` for 9 and `review_required` for 10): **9** = "started / still running, not complete"
for `--detach` and `--poll` (mutation possible: yes); **10** = `RECOVERY_REFUSED` for `--recover` (nothing written). The JSON `mode` field names the mode.

### Recovered record shape (additive, schema_version 1)

```json
"recovery": {
  "recovered": true,
  "mode": "journal_complete | journal_partial | postconditions_only",
  "recovered_at": "<UTC>", "recovery_run_id": "<hex32>", "supersedes_run_id": "<hex32 = record.run_id>",
  "lock_disposition": {"action": "tombstoned|absent|operator_confirmed", "owner_pid": 0, "owner_host": "...", "basis": "pid_absent|pid_start_mismatch|operator_confirmed"},
  "engine_attribution": {"basis": "engine_event_log", "shipped_event_at": "<instant>", "operation": "<id>"},
  "facts": {"exit_code": "observed_journal|unknown", "timed_out": "...", "finished_at": "observed_journal|engine_event_log|unknown",
            "stdout": "observed_journal|unknown", "stderr": "...", "archived_ids": "observed_journal|engine_event_log|derived_live_state",
            "returned_ids": "observed_journal|engine_event_log|derived_live_state|unknown", "commit_sha": "...", "mutation_state": "derived_live_state|observed_journal"}
}
```

Unobserved facts are written as `null`; a lost stream capture is `{"availability": "unavailable", "reason": "..."}`. Validator rules
(T9): the block is structurally validated first; each relaxation is keyed on the matching `facts` entry being `unknown`; an `observed_*`
fact requires the journal-derived capture fields to be present; `mutation_state` is `completed` or `indeterminate`, never `none`;
all existing recomputations (allowed/required sets, set differences, drift, `shipment_archived_shipped`) still apply.

## Implementation Units

Every task: test-first, one concern, <= 2 h human-equivalent, `size` + `complexity` assigned. Gate per task:
`PYTHONPATH=src python -m unittest discover -s tests` (and the touched test module first).

* **T1 (S/medium): engine event-log provenance spike + reader.** Read-only characterisation of `.backlogit/logs/*.jsonl`
  for a shipment cascade: exact predicates for "archived by cascade S" (`_shipment_operation`, window), "returned blocked", "shipped".
  Deliverables: `docs/spikes/2026-10-16-cascade-close-engine-event-log-provenance.md`, sanitized fixtures under
  `tests/fixtures/cascade_close_event_logs/` (including a real 214-S-shaped log), new `shipment_close/event_log.py`
  (`read_cascade_events(backlog_dir, shipment_id, since)`; malformed/unreadable => explicit error, never empty-by-default) + tests.
  De-risks T11. If the event log cannot attribute the cascade, T11 downgrades `returned_ids` to `derived_live_state` only and
  `postconditions_only` recovery refuses; record the finding.
* **T2 (M/medium): `shipment_close/journal.py`.** Journal dir creation via `ensure_trusted_directory`, 0600 files,
  `meta.json`/`exit.json`/`outcome.json` atomic writers and readers, schema-checked reads (fail closed), size cap, retention/cleanup of
  own files, tests incl. symlink/junction refusal and torn-file handling.
* **T3 (S/medium): `shipment_close/liveness.py`.** `is_process_alive`/`provably_dead(host, pid, pid_start)`. Windows via
  `ctypes` (`OpenProcess`/`GetExitCodeProcess`/`GetProcessTimes`), POSIX via `os.kill(pid, 0)` plus `/proc/<pid>/stat` start time. Conservative:
  "unknown" never counts as dead. Injectable seam for tests.
* **T4 (M/medium): `persist.py` lock + transitions.** Lock payload gains `host`, `pid_start`, `supervisor` flag; owner-bound lock rewrite
  (pid handoff); `takeover_stale_lock` serialized by an `O_EXCL` takeover guard (`.lock.takeover`): inside the guard re-read the lock, re-verify the owner identity (`run_id`, `pid`, `pid_start`, `host`) equals the identity proven dead and re-check liveness, rename to a never-overwritten tombstone `.lock.stale-{old_run_id}-{recovery_run_id}`, `O_EXCL` create the new lock, release the guard; an identity mismatch (delayed contender) or a stale guard exits 7; tests include the delayed-contender interleaving (A takes over, B still holding the old stale verdict must not rename A's live lock); recovery
  transition `invoking -> post_close` for a recovery run holding the lock (new run id, `recovery.supersedes_run_id == record.run_id`), all
  other transitions unchanged; tests incl. concurrent takeover race.
* **T5 (M/medium): journaled child runner.** `shipment_close/supervisor.py` shim (`python -m autoharness.shipment_close.supervisor`): spawns the
  child with stdout/stderr redirected to journal files, kills the group on timeout, writes `exit.json` atomically; `run_journaled` returns a
  `BoundedRunResult` by streaming the journal files through `StreamCapture` (parse buffer/cap semantics preserved). Includes a detached-survival
  probe test (child outlives a killed launcher; skipped with reason where the platform forbids).
* **T6 (M/medium): command integration (attached).** `_invoke_and_finalize` uses the journaled runner and writes `meta.json` (run id, redacted argv,
  effective timeout, declared caller wait, host, pids); journal retained on non-success; on a clean exit-0 run only `stdout.raw`/`stderr.raw` are removed and `meta.json`/`exit.json`/`outcome.json` are retained so `--poll` after cleanup still returns the final code (test: poll after successful cleanup); mutating run that meets a
  stale lock/`invoking` record reports `recovery_available` (exit 7 unchanged, nothing recovered, nothing invoked); existing exit-code behaviour and tests unchanged.
* **T7 (M/high; de-risked by T5): `--detach`.** Foreground steps 1-7, spawn detached supervisor (Windows `DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP` with
  breakaway attempt; POSIX `start_new_session`), lock pid handoff, the supervisor cross-checks `meta.json` `argv_sha256` against the `argv_sha256` the foreground wrote into the `invoking` record and re-hashes the binary immediately before spawn (hardening H12), finalizer runs steps 9-10 and writes `outcome.json`, releases lock; if detachment
  cannot be established the command exits 2 before the mutation. Never both a foreground and a supervisor finalizer (single owner).
* **T8 (S/low): pre-flight + `--poll`.** `--caller-wait`/`AUTOHARNESS_CALLER_WAIT_SECONDS` refusal (exit 2, pre-mutation) when `< timeout + SUPERVISION_MARGIN_SECONDS`
  in attached mode; `--poll [--wait N]` maps journal state to exit codes (running 9, `outcome.json` code, dead supervisor with `invoking` -> 7 with
  `recovery_available`), idempotent and side-effect free.
* **T9 (M/medium): validator + record builder extension (`gates/cascade_evidence.py`).** `recovery` block validation, per-field relaxations keyed to
  `facts` (including tolerance of a null `invocation.finished_at` in `_check_in_record_ordering`, only under a validated recovery block), anti-fabrication rules,
  negative tests (strip the block => the old failures return; every `unknown` fact exercised; forged `observed_journal` without
    capture data rejected; `none` mutation_state rejected for recovered records). Adds `validate_evidence_structure(record, ...)`: the same structural and
    recomputation-consistency checks as `validate_evidence_record` but accepting a consistent `fail` verdict and non-empty `failures`, used only by recovery to persist a
    determinate partial-recovery record; `validate_evidence_record` (used by the closure-evidence gate) stays pass-only; test that a failure record validates structurally
    yet is refused by the gate. The gate-output advisory is wired in T12 (CLI width isolation).
* **T10 (M/medium): recovery eligibility.** `shipment_close/recover.py` part 1: a new `MODE_RECOVER` existing-record check in `persist.py` (an `invoking` record is the expected input there, not exit 7), record/phase/pair checks, pre_close validity, owner liveness via T3,
  child liveness (journal pids; process scan for `backlogit ... shipment ship <S>`), settle-window stability (two live reads), legacy-record operator
  confirmations (`--confirm-owner-dead`, `--confirm-engine-stopped`), stale lock takeover via T4, `--dry-run` report. Refusal => exit 10, nothing written.
* **T11 (M/high; de-risked by T1, T9): recovery reconstruction.** `recover.py` part 2: rebuild `ParsedResult` from journal stdout (`observed_journal`) else engine
  event log (`engine_event_log`) else `derived_live_state`; engine attribution check (D-7); reuse `_reread`/`_recollect`/`evaluate_postconditions`; build
  and validate the recovered record before writing with the new **structural/consistency** validator `validate_evidence_structure` (T9) so a determinate partial-recovery `fail` record can be persisted (exit 5) while the closure-evidence gate keeps using the pass-only `validate_evidence_record` and therefore never unblocks successors on a failure record; write via T4 transition; idempotent (a second run exits 2 `evidence already finalized`).
* **T12 (S/low): CLI wiring.** `--recover`, `--dry-run`, `--detach`, `--poll`, `--wait`, `--caller-wait`, `--confirm-owner-dead`, `--confirm-engine-stopped`
  parsing/exclusions, `--json` fields (`recovered`, `recovery_mode`, `recovery_available`, `journal_path`), the closure-evidence gate output advisory (`evidence_recovered`, `recovery_mode`),
  `operator_action` for exits 9 and 10, usage text, exit-code mapping.
* **T13 (S/low): docs.** `docs/gates-reference.md` (modes table, journal, detach/poll, pre-flight, recovery, exit 9, lock section, evidence fields, gate
  advisory) and `CHANGELOG.md`; docs tests (`tests/test_flat_manifest_closure_docs.py` style) updated.
* **T14 (S/low): shipment-reconcile guidance.** `templates/skills/shipment-reconcile/SKILL.md.tmpl` and `.github/skills/shipment-reconcile/SKILL.md` (byte-parity),
  manifest checksum: mandatory `--detach` + `--poll` (or attached with sufficient declared wait), exit 7 + `invoking` routing to `--recover --dry-run`
  then operator-approved `--recover`, recovered-evidence handling in the closure artifact; avoid duplicating existing paragraphs (E337551C re-scope).
* **T15 (M/low): Ship/closure propagation.** `_ship.agent.md.tmpl` + mirror, `operational-closure` skill tmpl + mirror, `circuit-breaker` instruction tmpl +
  mirror (stall bound for `--poll`), closure-subagent delegation wording; manifest checksums; parity tests.
* **T16 (M/medium): incident replay + final gate.** End-to-end test with a fake backlogit: kill the wrapper mid-ship, assert journal survival, `--recover --dry-run`
  and `--recover` produce a record that passes `validate_evidence_record`, the closure-evidence gate and the pipeline-topology predecessor check fixture; lock
  tombstone asserted; idempotence; refusal matrix (live owner, no attribution, partial mutation => exit 5 record that the gate still refuses, legacy record without confirmations), delayed-contender takeover, poll after cleanup.
  Full `unittest discover` run and dogfood `verify` run.

Dependency order: T1 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7 -> T8 -> T9 -> T10 -> T11 -> T12 -> T13 -> T14 -> T15 -> T16 (linear chain; one active task).

### Backlog ID map (feature 211-F, shipment 218-S, deliberation 041-DL)

Task IDs were assigned out of plan order by a parallel create; the `T<n>:` title prefix is the plan unit and the dependency chain follows the plan order.

| Plan unit | Task ID | Plan unit | Task ID |
|---|---|---|---|
| T1 | 211.002-T | T9 | 211.009-T |
| T2 | 211.001-T | T10 | 211.010-T |
| T3 | 211.004-T | T11 | 211.011-T |
| T4 | 211.003-T | T12 | 211.015-T |
| T5 | 211.006-T | T13 | 211.013-T |
| T6 | 211.005-T | T14 | 211.014-T |
| T7 | 211.008-T | T15 | 211.012-T |
| T8 | 211.007-T | T16 | 211.016-T |

Shipment `218-S` is a declared root (`labels: [dag-root]`, no `blocks` edges); see deliberation D-11.

## Hardening amendments (binding)

H1-H11 of the hardening record are binding on the named tasks: H1 -> T11/T16; H2, H11 -> T10; H3 -> T3/T4; H4 -> T9; H5 -> T2; H6 -> T3; H7 -> T7;
H8 -> T4/T11; H9 -> T1/T11; H10 -> T14/T15. Added by plan review cycle 1: H12 (supervisor argv integrity, T5/T7), the 9/10 exit-code split, the recover
existing-record mode, null `finished_at` handling, and gate-advisory width isolation.

## Sizing summary

S: T1, T3, T8, T12, T13, T14 (6). M: T2, T4, T5, T6, T7, T9, T10, T11, T15, T16 (10). Complexity: low 5, medium 9, high 2 (each with a named de-risking predecessor).
Largest estimate 2 h; no task exceeds the 2-hour rule.

## Decisions and Rationale

See the deliberation, D-1..D-11. Plan-level additions: D-12 journals are never committed (git-ignored) and raw output is 0600; D-13 recovery never trusts an
unattributed live state; D-14 the poll and dry-run paths are read-only; D-15 lock takeover preserves the stale lock as a tombstone rather than deleting it.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Recovered record launders a human/partial mutation as a clean close | D-7 engine attribution + full INV-10 recomputation; refusal otherwise |
| Windows job object kills the detached supervisor | probe in T5; `--detach` fails closed (exit 2) before mutating; recovery covers the remainder |
| Raw output holds secrets | 0600, git-ignored, evidence gets redacted excerpts only |
| Validator relaxation weakens normal records | relaxations keyed to a validated `recovery` block; negative tests for every field |
| Wrong liveness verdict (pid reuse) | `pid_start` comparison; "unknown" never dead; legacy locks need operator confirmation |
| Engine still running during recovery | child liveness + process scan + settle-window stability + legacy `--confirm-engine-stopped` |
| Lock handoff race | single owner token (`run_id`) rewrite, atomic replace; takeover CAS via rename |

## Verification Plan

Per-task module tests, then the canonical gate `PYTHONPATH=src python -m unittest discover -s tests`; `autoharness verify` on the dogfood workspace after
T14/T15 (template-vs-installed parity and manifest checksums); T16 replay. Telemetry/doc claims verified against the code, not memory.

## Requires plan hardening

yes - safety-critical close path (destructive-command evidence, lock semantics, validator contract). Hardening record linked in the frontmatter.

## Plan Review

* decision: PASS (2 cycles, `dispatch_mode: single-agent-declared-degradation`; `TOOL_DEGRADED: reviewer-subagent-dispatch`, `TOOL_DEGRADED: model-specific-review-routing`)
* standalone record: `docs/reviews/2026-10-16-cascade-close-recovery-and-journaling-plan-review.md`
* cycle 1 FAIL: P1 F1 (unauthenticated supervisor argv) plus P2 F2-F5; all resolved in this plan and the hardening record (H12); cycle 2 PASS, no open P0/P1.
* open P3 advisories: F6-F10 (see the standalone record).
* post-publication Copilot review (PR 535): two P1 + one P2 fixed in the plan, deliberation, hardening record and tasks 211.003-T, 211.005-T, 211.007-T, 211.009-T, 211.011-T; verdict unchanged.

