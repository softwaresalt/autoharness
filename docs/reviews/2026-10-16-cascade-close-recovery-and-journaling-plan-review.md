---
title: "Plan review: cascade-close journaling, detach/poll supervision, and provenance-marked recovery"
description: "Multi-persona plan review of docs/plans/2026-10-16-cascade-close-recovery-and-journaling-plan.md, run as a single-agent declared-degradation pass. Cycle 1 produced one P1 (unauthenticated supervisor argv) and four P2 findings fixed in the plan; cycle 2 verified PASS."
doc_type: review
review_target: docs/plans/2026-10-16-cascade-close-recovery-and-journaling-plan.md
dispatch_mode: single-agent-declared-degradation
decision: PASS
review_cycles: 2
reviewed_utc: 2026-10-16
---

# Plan review: cascade-close journaling, detach/poll, and recovery

Review gate for the plan (stash `369F8062` + `E337551C`, deliberation `041-DL`). The authoritative machine-readable copy is
the `## Plan Review` section appended to the plan; this file is the standalone record. Dates UTC.

dispatch_mode: single-agent-declared-degradation

decision: PASS

## Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch` - this Stage session exposes no reviewer subagent dispatch surface. Declared fallback:
  single-agent persona pass, every persona applied inline against its rubric with its own finding list.
* `TOOL_DEGRADED: model-specific-review-routing` - cross-model review routing is not dispatchable here. Declared fallback: same-model rubric pass. No persona skipped.

## Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Constitution Reviewer | inline (always-on) | F2 P2 resolved |
| Python Reviewer | inline (always-on) | F4 P2 resolved, F8 P3 |
| Scope Boundary Auditor | inline (always-on) | F7 P3 |
| Learnings Researcher | inline (always-on) | F9 P3 (RCA re-scope of E337551C honoured) |
| Architecture Strategist | inline, same-model | F3 P2 resolved |
| Security Lens Reviewer | inline (triggered: spawning, journal, locks) | F1 P1 resolved, F10 P3 |
| Agent-Native Parity Reviewer | inline (triggered) | F6 P3 |
| Schema-CLI-Docs Coupling Reviewer | inline (extra, repo-specific) | F5 P2 resolved |

## Cycle history

* **Cycle 1: FAIL** - one P1 (F1): the detached supervisor would exec an argv read from `meta.json` that nothing authenticates, a new
  trust boundary on the destructive path. Plan revised (hardening H12: `argv_sha256` in both the `invoking` record and `meta.json`, binary re-hash before spawn,
  supervisor accepts only a journal path). Four P2 findings fixed in the same revision.
* **Cycle 2: PASS** - all revised sections re-verified against the code facts table; no open P0/P1.

* **Cycle 3 (post-publication, Copilot review of PR 535): three findings accepted and fixed** - (P1) takeover rename+`O_EXCL` was not an atomic owner-identity check: now
  serialized by an `O_EXCL` takeover guard with an owner-identity and liveness recheck inside it and a delayed-contender test (D-5, H8, T4); (P1) success cleanup deleted
  `outcome.json` that `--poll` needs: now only the raw streams are removed and the small terminal files are retained, with a poll-after-cleanup test (D-1, T6, T8);
  (P2) `validate_evidence_record` is pass-only, so recovery's exit-5 failure record could not be persisted: added `validate_evidence_structure` for recovery while the gate stays
  pass-only (T9, T11, T16). Verdict remains PASS; no open P0/P1.
* **Cycle 4 (Copilot re-review of the cycle-3 head): five further findings accepted and fixed** - (P1) a `shipped` event does not prove this cascade completed the archival: D-7/H1 now require
  operation-correlated provenance for the whole footprint, never `derived_live_state` for archived ids, with a partial-stop-then-other-actor test; (P1) one-way supervisor handshake could not make exit 2
  mutation-free: two-phase `authorize.json`/`abort.json` barrier (H7, T7); (P1) regular-file capture lost the inherited-pipe signal: descendant-group quiescence check and fail-closed
  `drain_incomplete` (H13, T5) with the grandchild test ported; (P2) the supervisor could only reconstruct a redacted argv: protected exact `launch.json` plus `argv_sha256` over the exact argv (H12, T5-T7);
  (P2) crash between the `post_close` and `outcome.json` writes: `--poll` evidence-record fallback (H14, T8). Verdict remains PASS; no open P0/P1.
* **Cycle 5 (Copilot round 3): four further findings accepted and fixed** - (P1) capture-completeness verdict was in-memory only: persisted per stream in `exit.json` before finalization and enforced by recovery (H13, T5, T11);
  (P1) the authorization wait depended on the foreground: `authorize_deadline` persisted before spawn, supervisor self-expiry, terminal `never_authorized`, lock release (H7, T7); (P2) an empty process group does not prove no
  escaped writer: open-writer probe (Windows exclusive-open, Linux `/proc/*/fd`, else fail closed) and an escaped-session test (H13, T5/T16); (P2) a never-authorized detach left `invoking` with no retry path: owner-bound
  `invoking -> pre_close` rollback with never-spawned proof and an abort-then-attached test (H7, T4/T7). Verdict remains PASS; no open P0/P1.
* **Cycle 6 (Copilot round 4): two further findings accepted and fixed** - (P1) no snapshot revalidation after the authorization wait: the supervisor recomputes snapshot and engine decision immediately before spawn and refuses on
  drift, with a changed-during-handshake test (H7, T7); (P2) a crash between persisting `never_started` and the rollback left a stale lock: recovery-owner rollback for a provably dead owner (H7, T4/T10). Verdict remains PASS; no open P0/P1.

## Findings

| ID | Sev | Persona | Finding | Disposition |
|---|---|---|---|---|
| F1 | P1 | Security | Supervisor spawns an unauthenticated argv from `meta.json` | Resolved: H12, T5/T7 |
| F2 | P2 | Constitution | A single exit code 9 for "started/running" and "recovery refused" collides with `operator_action` rendering (`_CASCADE_CLOSE_NO_REVIEW` = {0,2,3}) | Resolved: 9 = started/running (`none`), 10 = RECOVERY_REFUSED (`review_required`) |
| F3 | P2 | Architecture | `check_existing_record` maps `invoking` to exit 7 in every mode, so recovery needs its own existing-record mode | Resolved: `MODE_RECOVER` in T10 |
| F4 | P2 | Python | `_check_in_record_ordering` treats a null `finished_at` as a shape error; a recovered record may legitimately have none | Resolved: tolerated only under a validated recovery block (T9) |
| F5 | P2 | Schema-CLI-Docs | Gate-output advisory was inside the validator task (validator + CLI in one task) | Resolved: moved to T12 |
| F6 | P3 | Agent-Native | `--poll`/`--recover --dry-run` must be machine-readable and idempotent | Covered: T8/T12 require `--json`, read-only |
| F7 | P3 | Scope | 16 tasks is large but each is one family/concern; two `high` tasks have named de-risking predecessors | Advisory |
| F8 | P3 | Python | Process tests must be deterministic (sentinel files, bounded sleeps, no wall-clock races) | Advisory; recorded for Ship |
| F9 | P3 | Learnings | E337551C re-scoped to propagation; T14/T15 must reuse the existing attached-async paragraph rather than add a second copy | Covered in T14 |
| F10 | P3 | Security | Windows file permissions for 0600 are best-effort | Accepted; documented in T13 |

## Checks performed

* Every cited code fact re-verified against `command.py`, `runner.py`, `persist.py`, `postclose.py`, `cascade_evidence.py` and `cli.py` (line-level read).
* 2-hour rule: largest task M; no XL/L. Width isolation: runner, persist, validator, CLI, docs, template families are separate tasks; only template+mirror pairs share a task (parity tests force atomicity).
* Hardening H1-H12 each mapped to at least one task and one negative test in T16.
* Fail-closed review: every refusal path writes nothing (`--recover`) or exits before the mutation (`--detach`, pre-flight).
