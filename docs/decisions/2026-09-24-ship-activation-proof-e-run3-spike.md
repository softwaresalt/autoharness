---
title: "Proof E run 3 - Ship per-task actor and checkpoint-first state machine: findings (BLOCKED, transcript bound exceeded)"
source: "docs/decisions/2026-09-24-ship-activation-proof-e-run3-spike.md"
doc_type: decision
description: "Stage-authored findings for Proof E run 3 under charter PE-1.3 section 6.7. The fixture's own transcript guard stopped at 4600 bytes before any trace verdict was printed (exit 2, empty stdout). Verdict BLOCKED, not PASS and not FAIL. Run 1 (PE-1.2) and run 2 (PE-1.3) artifacts stay unchanged. PE-ACTIVATE-01 raw blobs still equal 5bcb00e5 at 43f870eb, but only as a provisional observation that must be rechecked at proof exit. Proof E attempts are voluntarily stopped for this session."
docline:
  type: spike
  date: 2026-09-24
  time_box: "1h"
  conclusion: "defer"
  confidence: "medium"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags: ["ship-lifecycle", "checkpoint-recovery", "state-machine", "proof-entry"]
proof: E
proof_run: 3
proof_verdict: BLOCKED
proof_verdict_basis: fixture-transcript-guard-stopped-before-any-trace-verdict
prior_run_artifacts:
  run_1: {matrix: PE-1.2, verdict: BLOCKED, artifact: docs/decisions/2026-09-24-ship-activation-proof-e-spike.md, changed: false}
  run_2: {matrix: PE-1.3, verdict: BLOCKED, artifact: docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md, changed: false}
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
matrix_id: PE-1.3
charter_section: "6.7 (PE-1.3)"
matrix_rows: [PE-FLOW-03, PE-ACTIVATE-01]
activation_check: {row: PE-ACTIVATE-01, status: provisional-observed-head-only, observed_head: 43f870eb, baseline: 5bcb00e5, recheck_required_at_proof_exit: true}
scratch_path: ".proof-scratch/E3-20260924-013122/"
branch: chore/stage-176-s-workflow-defects
head_at_authoring: 43f870eb
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
charter_changed: false
universal_circuit_tripped: false
session_attempts_stopped: voluntary
scratch_cleanup_status: removed-by-parent-2026-09-24T01:34:04-07:00
---

# Proof E run 3 findings - Ship per-task actor and checkpoint-first state machine

## Verdict

**BLOCKED** - not PASS and not FAIL. The fixture's transcript guard stopped
execution before any trace verdict was emitted. No evidence was produced about
the product or charter state, in either direction. Run 1 (PE-1.2, BLOCKED) and
run 2 (PE-1.3, BLOCKED) remain immutable.

## Ship execution (as reported to Stage)

**Pre-write gates:** P-001 active shipments/tasks/features/chores empty; P-002
no claim; P-010 verification only; P-011 `git status` clean; P-016 one
worktree; HEAD `43f870eb` as expected.

### Scratch file

| Field | Value |
|---|---|
| Path | `.proof-scratch\E3-20260924-013122\proof_e_state_machine.py` (under cwd, charter-compliant) |
| Host | Windows 11, Python 3.14.3 |
| Size | 12,536 bytes (requested below about 10 KiB; target missed, recorded honestly) |
| SHA-256 | `91cb0d603088b32744995e3b393dc01d5090b2f062a50999c5a242043520eab3` |
| Disposable files | 1 of 2 allowed (file bound met) |

### Command and result

`python -B .proof-scratch\E3-20260924-013122\proof_e_state_machine.py` (one invocation)

Native exit `2`; stdout empty (0 bytes); stderr exactly
`OUTPUT_BOUND_EXCEEDED: fixture transcript reached 4600 bytes` (62 bytes).

No per-trace outcome exists. The canonical traces, the five required negatives
and the extra cases (quarantine, ambiguous selection) were **not** reported as
accepted or rejected. The in-memory transcript was discarded by the guard, so
no partial trace evidence can be recovered.

**Timing (-07:00):** host start not emitted; pre-write 01:31:22; post-run
01:33:23 (2m01s window); parent scratch cleanup 01:34:04, no scratch remains.
Without a host start, the full elapsed bound is not independently evidenced.

## PE-ACTIVATE-01 (provisional, observed HEAD only)

The script emitted no compare result. Stage re-checked the raw Git blobs
read-only (`git rev-parse`, `git cat-file blob`, SHA-256) at `43f870eb`:

| Path | Blob (5bcb00e5 = 43f870eb) | Raw-blob SHA-256 |
|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | `a3407080665c` | `7f2ddef1ada977fbb0d06a3f83587b1151acde297148a0847e1b0145d5595db2` |
| `.github/agents/_ship.agent.md` | `5f397d0f1f2c` | `83f9e73520f5d88708738f6bdbfc849377e9d1705366120cb49c1dc6b72ff81c` |
| `.autoharness/harness-manifest.yaml` | `17ae787d492f` | `10c0fa89e08c325c099d0332e35b01008e85a26d3ffc76cc765e8cff052addb8` |

`git diff 5bcb00e5 43f870eb` for the three paths is empty. These values match
the approved `5bcb00e5` digests. This is **not** a new pass from run 3. The row
names the proof-exit commit as its comparator, so it must be rechecked at
proof exit, and it does not make up for `PE-FLOW-03`.

## Matrix rows

| Row | Status after run 3 |
|---|---|
| `PE-FLOW-03` | Not satisfied. `BLOCKED`: no trace verdict was emitted |
| `PE-ACTIVATE-01` | Provisional: equal at `43f870eb` only; recheck at proof exit |
| `PE-EVIDENCE-01` | Partial: exit code, stdout, stderr and script digest are recorded; no trace transcript exists |

## Attempt accounting and voluntary stop

Run 3 is the third counted Proof E attempt. The observed fixture errors
differ (run 2: parsing, then a missing or duplicated anchor; run 3: the output
bound), so the universal three-same-error circuit breaker has **not** tripped.
Stage is **voluntarily** stopping further Proof E attempts this session to
avoid another synthetic fixture repair loop. This stop does not authorize a
PASS, a charter edit, a task claim or a shipment claim.

## Honest bounds

* Evidence is Ship-reported plus Stage read-only git checks; Stage did not run
  the fixture.
* No product or charter conclusion is drawn from the guard stop.
* Script size exceeded the requested target; the charter file bound (at most
  two disposable files) was still met.
* Engram circuit is open; agent-intercom and graphtor-docs are unavailable.
  No remote broadcast was made.

## Next Steps

1. **First**, compress the fixture evidence contract into a small table-driven
   trace list: one concise outcome line per case plus a bounded digest of the
   canonical event order. Use the exact checkpoint heading already clarified.
2. Before any new Ship run, complete a read-only review confirming that the
   projected transcript stays under 4600 bytes and that all five required
   negatives and the extra cases (quarantine, ambiguous selection) are present.
3. Only after step 2 passes may a fresh Ship run be scheduled. Recheck
   `PE-ACTIVATE-01` at proof exit.

## Cross-references

* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (section 6.7, PE-1.3)
* Run 1: `docs/decisions/2026-09-24-ship-activation-proof-e-spike.md`
* Run 2: `docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md`
