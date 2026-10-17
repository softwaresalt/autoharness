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

### H1 - A recovered record can launder an unattributed live state (BINDING, plan D-7 / T11)

Postconditions can be true because a human or another tool archived the items. Amendment: `postconditions_only` recovery
requires an engine-authored `shipment_status_changed -> shipped` event correlated to the shipment after `invocation.started_at`;
otherwise exit 10 with nothing written. Tested in T16 (negative: identical live state, no engine event).

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

### H7 - Detachment must fail closed (BINDING, T7)

If the supervisor cannot be proven started and detached (handshake via `meta.json` `supervisor_started_at` within a bounded wait), the
command exits 2 before invoking ship. It never degrades silently to attached, and never leaves a foreground finalizer and a supervisor
finalizer both live (the lock payload `run_id` plus a `finalizer` token in `meta.json` make the owner unique).

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

### H12 - Supervisor argv integrity (BINDING, added by plan review cycle 1, T5/T7)

The detached supervisor must not exec an argv it cannot authenticate. The foreground writes `argv_sha256` into both the `invoking` record and `meta.json`
(0600, trusted directory); the supervisor refuses to spawn when they disagree, when `argv[0]` is not the recorded binary path, or when the binary SHA-256
differs from `tool.binary_sha256` immediately before spawn. The supervisor accepts only a journal directory path as its own argument.

## Residual risks (accepted, recorded)

* Windows breakaway uncertainty (OQ-5): mitigated by H7; may make `--detach` unavailable in some runtimes, which leaves the attached path + pre-flight + recovery.
* Event-log schema belongs to backlogit: T1 pins fixtures and the reader fails closed on unknown shapes; a backlogit change that alters events degrades recovery to refusal, not to a wrong pass.
* `derived_live_state` for `returned_ids` is a logical consequence, not an observation; it is labelled as such and only allowed together with engine attribution (H1).
