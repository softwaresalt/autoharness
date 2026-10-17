---
title: "Plan Hardening: cascade-close journaling, detach/poll, and provenance-marked recovery (P-006)"
date: 2026-10-16
policy: P-006
hardens: docs/plans/2026-10-16-cascade-close-recovery-and-journaling-plan.md
source_deliberation: 041-DL
source_stash: [369F8062, E337551C]
source: docs/plans/2026-10-16-cascade-close-recovery-and-journaling-hardening.md
doc_type: plan-hardening
agent: stage
---

# Plan Hardening (P-006)

## Why hardening is required

`requires_plan_hardening: yes`. Signals: (1) the change sits on the destructive close path and its audit record; (2) it adds a
new way to write a `post_close` record that the closure-evidence gate will accept, i.e. it deliberately *relaxes* a
fail-closed validator; (3) it adds lock-takeover semantics, process spawning/detachment, and a new on-disk journal holding raw
engine output; (4) it spans four families (runner/CLI, evidence validator, docs, template+mirror guidance), so a partial
landing leaves the contract self-contradictory.

## Adversarial findings and binding amendments

### H1 - A recovered record can launder an unattributed live state (BINDING, plan D-7 / T1 / T11)

Postconditions can be true because a human or another tool archived the items, and an engine `shipped` event alone does not prove that *this* cascade completed the archive
mutations (the 214-S RCA records `shipped` while archival was partial). Amendment (revised after Copilot review of PR 535): `postconditions_only` recovery requires operation-correlated
provenance for the **whole mutation footprint**: the engine-authored `shipment_status_changed -> shipped` event after `invocation.started_at`, plus, for every required archived id, an
engine-authored `archived` event inside the cascade's operation window with no foreign-actor event on those items in the window. `derived_live_state` is not a basis for the archived footprint.
If T1 shows the event log cannot supply that correlation, a passing recovered record is refused (exit 10) and only a journal-observed (`journal_complete`) recovery can pass. Tested in T16
(negative: identical live state with no engine event; engine stops partially and another actor completes the archival).

### H2 - Recovering while the engine is still running (BINDING, T10)

The wrapper kill leaves `backlogit` running unsupervised. Amendment: eligibility requires journaled child pid dead, no
`backlogit ... shipment ship <S>` process, and an unchanged fingerprint across two live reads separated by a settle window
(default 15 s, floor 5 s, configurable only upward). A legacy record without a journal (like 214-S) additionally requires an
operator `--confirm-engine-stopped`; absent confirmation => exit 10.

### H3 - "Provably dead" must be conservative (BINDING, T3/T4/D-5)

Rules: same host required; `pid` absent => dead; `pid` present with a recorded `pid_start` that differs => dead (reuse);
`pid` present and start time equal or unrecorded => NOT dead; unreadable/foreign-host/legacy lock (no host/pid_start) =>
operator `--confirm-owner-dead` required. "Cannot tell" is never "dead".

### H4 - Relaxation scope of the validator (BINDING, T9)

Every relaxed field is enumerated (`exit_code`, `timed_out`, `invocation.finished_at`, stdout/stderr capture, `commit_sha`,
`returned_ids`) and each is allowed only when the validated `recovery.facts` entry for that field is `unknown` or the
specific observed/derived basis. Non-recovered records retain today's exact rules; a mutation test strips the `recovery` block from
every recovered fixture and asserts the original failures return. `mutation_state: none` is rejected for recovered cascades.
The `facts` map must cover the full enumerated field set; a missing or extra key is a failure.

### H5 - Raw journal confidentiality and path trust (BINDING, T2)

Journal files hold unredacted engine output. Amendment: directory created with the existing trust-walk (no symlink/junction/reparse
components, contained in the workspace), files 0600 (Windows: best-effort ACL note in docs), directory is under the git-ignored
`.autoharness/gates/`, never read through links (`_read_no_follow`), size cap with an explicit truncated marker, evidence gets
redacted excerpts only (existing `redact`). Tested: link refusal, torn `meta.json`, oversize.

### H6 - Windows liveness primitive (BINDING, T3)

`os.kill(pid, 0)` on Windows is not a probe: signal value 0 is `CTRL_C_EVENT` and would signal a process group. Amendment: Windows
liveness and start time use `ctypes` `OpenProcess` / `GetExitCodeProcess` (`STILL_ACTIVE`) / `GetProcessTimes` only. The test seam asserts
`os.kill` is never called on `nt`.

### H7 - Detachment must fail closed, with an authorization barrier (BINDING, T7; revised after Copilot review of PR 535)

A one-way "supervisor started" notification cannot make exit 2 mutation-free: a delayed supervisor could start `shipment ship` after the foreground gave up, and a lost notification can hide an
already-started child. Amendment: a two-phase barrier. The supervisor writes `supervisor_ready` and then **waits**; it spawns the child only after the foreground writes `authorize.json`
(nonce + `valid_until`, re-checked by the supervisor itself). A foreground timeout before authorization writes `abort.json`; the supervisor never spawns after `abort.json` or past `valid_until`,
so that exit 2 is provably mutation-free. After `authorize.json` exists the foreground never reports a mutation-free refusal: an unacknowledged start is exit 9 "started (unconfirmed)",
`mutation_possible: yes`, resolved by `--poll`. It never degrades silently to attached, and never leaves a foreground finalizer and a supervisor finalizer both live (lock `run_id` plus a
`finalizer` token in `meta.json`). Tests: delayed supervisor start, lost notification, abort-before-authorize, late authorize.

**Addendum (Copilot round 3):** (a) the authorization wait is bounded independently of the foreground: the foreground persists `authorize_deadline` in `launch.json` *before* spawning the supervisor, and the
supervisor self-expires at that deadline without spawning, writes a terminal `never_authorized` outcome, rolls the evidence back and releases the lock itself; test: kill the foreground between lock handoff and
`authorize.json`. (b) Rollback disposition: `invoking` is written before the spawn, so a never-spawned run returns to `pre_close` through an owner-bound `invoking -> pre_close` rollback transition (T4) permitted only with
proof (`never_started` in `exit.json`/`outcome.json`, no `child_started`, same-run lock owner); afterwards an attached run takes the `pre_close` record over normally; test: abort followed by an attached invocation.

**Addendum (Copilot round 4):** (c) the foreground's snapshot revalidation precedes the supervisor startup and the authorization wait, so backlog state could drift in that window and `shipment ship` would act on scope
outside the validated baseline. The supervisor therefore **recomputes the snapshot and engine decision after the authorization wait, immediately before the child spawn** (the same steps 5-6 comparison against the durable `pre_close`
record: manifest, descendant fingerprints, engine re-probe, binary hash) and refuses to spawn on any drift: terminal `revalidation_drift` outcome (exit-4 class), `never_started` proof, rollback `invoking -> pre_close`, lock released; the post-close drift check is
a backstop, not the control. Test: change backlog state during the handshake and assert the child is never launched. (d) A crash after `never_started` is persisted but before the rollback leaves a stale lock and an `invoking` record with durable proof that no child
ran: `--recover` therefore also has a **recovery-owner rollback** (T4/T10): after validating the original run's `never_started` proof and quiescence (no `child_started`, no live descendants, lock owner provably dead) it moves `invoking -> pre_close` under its own
run id (the mutation-free branch; nothing is reconstructed or written to `post_close`), after which an attached retry proceeds. Test: crash between the sentinel write and the rollback, then recovery, then an attached retry.

### H8 - Idempotence and torn writes (BINDING, T4/T11)

Recovery writes only through the atomic temp+replace writer. A second `--recover` over a `post_close` record exits 2 (`evidence already
finalized`) and changes nothing. A crash between lock takeover and record write leaves the tombstone plus the original `invoking`
record: the next `--recover` re-verifies from scratch (tombstone is not a lock) and is safe. Takeover is serialized by the `.lock.takeover` guard with an
owner-identity recheck inside it (added by Copilot review of PR 535); a crash inside the guard leaves a guard that is never auto-cleared (operator review, exit 7).

### H9 - Timestamp handling (BINDING, T1/T11)

Engine log timestamps are offset-bearing. Recovery converts to UTC instants for all ordering checks (`parse_rfc3339_instant`), keeps the
original string in the facts map, and never rewrites the committed record's other timestamps. Stash 2C56E421 remains the owner of broader normalization.

### H10 - Parity and checksum ordering (BINDING, T14/T15)

Template and installed mirror change in the same task; manifest checksum computed over LF-normal bytes of the *final* mirror after the last edit in that
task; `autoharness verify` is the last step of T14 and T15 and again in T16.

### H11 - Process scan must not kill or signal (BINDING, T10)

The "is ship still running" scan is read-only (process listing only), never terminates anything, and a scan error is `unknown` => refusal, not a pass.

### H12 - Supervisor argv integrity (BINDING, added by plan review cycle 1, revised after Copilot review of PR 535, T5/T6/T7)

The detached supervisor must not exec an argv it cannot authenticate, and it must exec the *exact* argv, not the redacted audit copy (redaction can change `--message`/`--author`).
The foreground writes the exact argv to a protected `launch.json` (0600, git-ignored trusted journal directory, removed with the raw streams on success) and `argv_sha256` over that exact argv into
both the `invoking` record and `meta.json` (which carries only the redacted audit argv). The supervisor refuses to spawn when the `launch.json` hash and the `invoking` record hash disagree, when `argv[0]` is
not the recorded binary path, or when the binary SHA-256 differs from `tool.binary_sha256` immediately before spawn. The supervisor accepts only a journal directory path as its own argument.
Test: a `--message` containing a redaction-triggering value reaches the child byte-for-byte while the evidence record carries only the redacted copy.

### H13 - Regular-file capture must prove the descendant group is quiescent (BINDING, T5; added after Copilot review of PR 535)

Pipes gave the old runner an inherited-descriptor signal (`drain_incomplete`); regular files do not, so a grandchild can keep writing after the direct child exits. Amendment: after the direct child
exits the shim proves the descendant group is quiescent (POSIX: process-group liveness probe, then group kill; Windows: Job Object membership), kills survivors, and marks the stream
`drain_incomplete`/capture incomplete; successful finalization fails closed on an incomplete capture (exit 6 class, never `completed`). Where membership cannot be enumerated the result is
"unknown" and also fails closed. The existing `test_lingering_grandchild_does_not_hang_and_marks_drain_incomplete` scenario is ported to the journaled runner.

**Addendum (Copilot round 3):** (a) the quiescence verdict is persisted per stream in `exit.json` (`quiescence: {proven, method, survivors_killed}` and final byte counts) before any finalization, so a dead finalizer
cannot let recovery treat an incomplete/unproven capture as `journal_complete`; recovery enforces it (missing or unproven => `journal_partial` at best, never a passing journal capture); test the crash window.
(b) An empty process group/Job does not prove that no writer escaped it (a grandchild may leave the group with `start_new_session`/`setsid` and keep the descriptors), so completeness additionally requires an
open-writer probe on the journal files: Windows exclusive-open (`CreateFile` share mode 0) must succeed; Linux scan `/proc/*/fd` for links to the journal files; on a platform with neither primitive the result is
`unproven` and finalization fails closed (documented limitation). Test: an escaped-session grandchild holding stdout.

### H14 - Terminal-state polling survives a crash between evidence and outcome writes (BINDING, T8; added after Copilot review of PR 535)

The finalizer writes the `post_close` record before `outcome.json`. If it dies between the two, `--poll` falls back (read-only) to the validated terminal evidence record for the journal's `run_id`
(pass -> 0, postcondition fail -> 5, failed/unparsed invocation -> 6) and reports `outcome_source: evidence_record`; `--recover` still accepts only `invoking` records. Tested.

## Residual risks (accepted, recorded)

* Windows breakaway uncertainty (OQ-5): mitigated by H7; may make `--detach` unavailable in some runtimes, which leaves the attached path + pre-flight + recovery.
* Event-log schema belongs to backlogit: T1 pins fixtures and the reader fails closed on unknown shapes; a backlogit change that alters events degrades recovery to refusal, not to a wrong pass.
* `derived_live_state` for `returned_ids` is a logical consequence, not an observation; it is labelled as such and only allowed together with engine attribution (H1).
