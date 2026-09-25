---
title: "Lifecycle proof-exit refresh (PE-1.7): no row unsatisfied, ten rows conditional on operator decisions, implementation matrix refreshed as a draft and not ratified"
source: "docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md"
doc_type: decision
description: "Read-only Stage audit under charter PE-1.7 (commit e65887d8), written at HEAD e65887d8 on chore/stage-176-s-workflow-defects in the one current worktree. It refreshes the proof-exit report of 9c83517d (PE-1.5, HEAD c7d5f97e) and does not edit it. New evidence since then: Proof D run 5 PASS (5976ff62), Proof C run 3 FAIL (f23b9549), charter PE-1.6 (cd2ef261), Proof C run 4 PASS under PE-1.6 (4c6e2701), the operator routing commit 08787a4b, and charter PE-1.7 (e65887d8), which rebaselines the PE-ACTIVATE-01 comparator to 08787a4b and records the operator's PE-FLOW-04 ruling (Option A). Effective verdicts: A PASS, B PASS, C run 4 PASS, D run 5 PASS, E PASS, F PASS, G PENDING-LINUX. PE-ACTIVATE-01 holds at HEAD against 08787a4b. Eight of the 40 rows change status. PE-FLOW-04 and PE-DATA-03 become MET. PE-FLOW-02, PE-INTERFACE-03, PE-DATA-01 and PE-DATA-02 move from UNSATISFIED to MET-COND. PE-TASK-01 and PE-EVIDENCE-05 move from MET to MET-COND, because two Stage readings those rows depend on are now visible. Totals: 18 MET, 10 MET-COND, 2 OPEN-EVIDENCE, 0 UNSATISFIED, 7 met on Windows with Linux PENDING, 3 deferred. No proof PASS confers claim authority, and the Proof C PASS ratifies none of the candidate proposals. The implementation matrix IM-01 to IM-17 (two rows added: R-C3b and candidate ratification) is a DRAFT and is NOT RATIFIED. Linux-native execution stays a non-waivable gate. 187-S stays queued and frozen. Publication and claim readiness are both false."
docline:
  type: spike
  date: 2026-09-25
  time_box: "n/a (proof-exit refresh; section 8, not a proof)"
  conclusion: "no-row-unsatisfied-ten-conditional-matrix-draft-not-ratified"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "proof-exit"
    - "acceptance-matrix"
    - "ship-lifecycle"
    - "linux-execution-gate"
    - "governance-reset"
artifact_class: proof-exit-report-refresh
refreshes: docs/decisions/2026-09-24-lifecycle-proof-exit-spike.md
refreshes_commit: 9c83517d
prior_report_edited: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.7"
charter_commit: e65887d8
matrix_id: PE-1.7
head_at_authoring: e65887d8267ea9a3f0612a2f6c69e4ba39706add
branch: chore/stage-176-s-workflow-defects
worktrees: 1
section_8_exit_condition_met: true
implementation_ready: false
implementation_matrix_status: drafted-not-ratified
cross_platform_acceptance: unmet
linux_gate: "not-deferrable, non-waivable execution and release gate (section 6.9); Windows evidence never satisfies it"
proof_verdicts:
  - {proof: A, reported_run: 5, verdict: PASS, scope: synthetic-fixture-only, commits: [99e9ff5f, 4d132bf9], matrix: PE-1.4, conditional_on: [OD-3]}
  - {proof: B, reported_run: 3, verdict: PASS, scope: disposable-stub-and-predicate-only, commit: 6920cb7c, matrix: PE-1.4, conditional_on: [OD-3]}
  - {proof: C, reported_run: 4, verdict: PASS, scope: synthetic-truth-table-and-candidate-schema-plus-real-surface-controls, commit: 4c6e2701, matrix: PE-1.6, conditional_on: [OD-9], history: "run 1 FAIL (PE-1.3, 9d0ed834); run 2 BLOCKED (PE-1.4, 309ab0e2); run 3 FAIL (PE-1.5, f23b9549)"}
  - {proof: D, reported_run: 5, verdict: PASS, scope: synthetic-decided-contract-only, commit: 5976ff62, matrix: PE-1.5, history: "run 1 FAIL (b3fca43a); run 2 historical PASS (a0079ac0); run 3 FAIL (8179feb1); run 4 PASS (36f65975), recorded PE-FLOW-04 historical exception (PE-1.7)"}
  - {proof: E, reported_run: 5, verdict: PASS, scope: synthetic-state-machine-model, commit: c7d5f97e, matrix: PE-1.5}
  - {proof: F, reported_run: 2, verdict: PASS, commit: 8b39a08b, matrix: PE-1.4}
  - {proof: G, reported_run: 2, verdict: PENDING-LINUX, host_verdicts: {windows: PASS, linux: PENDING}, commits: [6daf80bb, 06f8930b], matrix: PE-1.4}
prior_verdicts_changed: false
matrix_row_counts:
  total: 40
  met: 18
  met_conditional: 10
  open_evidence: 2
  unsatisfied: 0
  windows_met_linux_pending: 7
  deferred_to_implementation_matrix: 3
  not_deferrable_or_mixed: 37
  not_deferrable_met_clean: 18
rows_changed: [PE-FLOW-02, PE-FLOW-04, PE-INTERFACE-03, PE-DATA-01, PE-DATA-02, PE-DATA-03, PE-TASK-01, PE-EVIDENCE-05]
met_conditional_rows: [PE-AUTH-01, PE-SCOPE-07, PE-FLOW-02, PE-INTERFACE-02, PE-INTERFACE-03, PE-DATA-01, PE-DATA-02, PE-TASK-01, PE-EVIDENCE-03, PE-EVIDENCE-05]
open_evidence_rows: [PE-AUTH-02, PE-EVIDENCE-01]
unsatisfied_rows: []
activate_01_recheck: {head: e65887d8, comparator: 08787a4b, blobs_equal: true, raw_sha256_equal: true, crlf: 0, tracked_diff_empty: true, porcelain_empty: true, activation_occurred: false}
open_operator_decisions: [C2, C3, C4, OD-3, OD-4, OD-5, OD-6, OD-7, OD-8, OD-9, OD-10, OD-11]
resolved_operator_decisions: {OD-1: "superseded by Proof C run 4 PASS (4c6e2701)", OD-2: "resolved by operator ruling Option A (2026-09-25T13:27:40-07:00), recorded in PE-1.7 (e65887d8)"}
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_authoring: "queued, 17 items, labels dag-root/shipment/ship-lifecycle/harness-architect (tracked .backlogit/queue/187-S.md, unchanged since 082df7b2); frozen"
shipment_claim_ready: false
publication_eligible: false
publication_ready: false
claim_ready: false
backlog_item_created: false
stash_entry_created: false
plan_changed: false
ship_surface_changed: false
proof_run_performed: false
stage_model_route: "claude-opus-5.5/anthropic/high requested and configured; unverified by Stage (ROUTING_DEGRADED: not self-verifiable)"
---

# Lifecycle proof-exit refresh (PE-1.7)

## Bottom Line

| Question | Answer |
|---|---|
| Is the section 8 exit condition met? | **Yes.** Six proofs are `PASS` and Proof G is `PENDING-LINUX` with its Linux gate carried forward (IM-01) |
| Are the proof-exit rows satisfied? | **Not yet.** No row is `UNSATISFIED` any more. But 10 rows are `MET-COND` (met only if the operator accepts a recorded Stage reading or an Orchestrator action) and 2 `P1` rows have open evidence gaps. Two `P0` rows, `PE-AUTH-01` and `PE-FLOW-02`, are among the conditional rows |
| What would close them? | Four operator decisions: OD-3 (ratify or veto the Stage readings), OD-4 (close or accept the evidence gaps), OD-5 (confirm `89b0db6d`) and OD-9 (accept or reject the Orchestrator's `git stash` set-aside during Proof C run 4). OD-8 fixes how the rows are read |
| Is the lifecycle implementation-ready? | **No.** Nothing here makes it ready for implementation, harvest, planning, a review epoch, activation or claim |
| Implementation acceptance matrix | **Refreshed as a draft. Not ratified.** IM-01 to IM-17. Two rows are new: IM-16 (R-C3b) and IM-17 (ratification of the Proof C candidate) |
| Cross-platform acceptance | **Not met.** Linux has not been executed. Linux-native execution is a non-waivable gate |
| Publication and claim readiness | **Both not ready.** `187-S` stays `queued` and frozen |

## Scope and Method

* **Actor and scope.** Stage worked read-only under PE-1.7. It ran no fixture,
  script, build, test suite or linter, no index refresh and no backlog
  mutation. It made no push, pull request, branch, claim or stash entry. It
  edited no findings artifact, proof-exit report, plan, review, source,
  template, manifest or Ship surface. This session's only other tracked
  change is the charter version 1.7 commit `e65887d8`, which the operator
  ordered. The only tracked change in this commit is this file.
* **The prior report stands.** The proof-exit report of `9c83517d` is kept
  unchanged, with its verdicts and audit as of `c7d5f97e`. This refresh cites
  it and restates a row only where the row's status changes.
* **What Stage read.** Charter PE-1.7 (as committed at `e65887d8`). The prior
  report. The Proof D run 5, Proof C run 3 and Proof C run 4 findings. The
  parent decision's architectural rule and stop conditions.
* **What Stage checked.** Read-only `git` queries (`rev-parse`, `cat-file
  blob` hashed in a Python subprocess with binary capture, `diff`, `log`,
  `show --name-only`, `status`, `worktree list`, `merge-base
  --is-ancestor`). Lock-file lengths. The tracked `187-S` file. A listing of
  `.proof-scratch/`. `Select-String` text audits over the three new findings
  artifacts. One read-only backlogit MCP call (`get_version`) and one
  read-only CLI checkpoint list.
* **Precedence.** This refresh is subordinate to the charter and to every
  source the charter is subordinate to. Where a reading is uncertain, the row
  is not counted as met.

### Session and Tool State (`PE-EVIDENCE-05`)

| Item | State |
|---|---|
| Tool gate | `.autoharness/backlog-registry.yaml` is present. backlogit MCP is `TOOL_OK`: `get_version` (update check skipped) returned `1.10.1-0.20260823032255-b07729386a31+dirty`. The backlogit CLI works |
| Index sync (Stage Step 0.1) | **Not run, on purpose** (`INDEX_SYNC_SKIPPED`). Row `PE-AUTH-01` (`P0`) says Stage performs no index refresh during the proof phase, and section 6.1 says "Stage never runs the refresh". The `187-S` read below uses the tracked file |
| Stage checkpoint recovery | An unfiltered CLI `checkpoint list`, captured in process (87,131 B, SHA-256 `1ab55a3ac37738b98c4913850b6f0d769ab345f99ea4e8939f4419dfca259560`), returned 71 records: 67 `stage`/`resolved`, 3 `ship`/`resolved` and 1 `ship`/`abandoned`. 0 need quarantine, 0 are quarantined, 0 are active. This is a normal zero-candidate startup |
| agent-engram, agent-intercom, graphtor-docs | The pack instruction files exist, but no tools are exposed in this runtime: `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`. Files were read directly. No broadcast was made. The Orchestrator relays to the operator |
| Stage-side tool-wrapper spool (disclosed) | One read-only `git diff 4acba14a 08787a4b` output (32.1 KB, mostly long manifest note lines) was too large for the tool channel. The host tool wrapper spooled it automatically to OS Temp, outside the current working directory. Stage did not direct that write, and read the spooled file read-only, with truncated lines. This is not a Ship proof invocation. It is disclosed on the same terms as the earlier Stage spool in the prior report |
| Stage pipeline steps | Stash triage, grouping, harvest, shipment assembly and stash archive do not apply. This is an Orchestrator-directed charter and audit turn, and the operator forbade any backlog, shipment or stash change. No docs-memory file or backlogit checkpoint was written, because each would be a tracked change outside the two ordered commits |
| Stage route | Configured as `claude-opus-5.5` / `anthropic` / `high`, from a fresh, schema-valid read of `.autoharness/config.yaml` relayed by the Orchestrator. The runtime cannot confirm the model it actually uses (`ROUTING_DEGRADED`) |
| Git at authoring | HEAD `e65887d8`. The only `git status --porcelain` entry is the untracked Orchestrator handoff `docs/scratch/2026-09-24-workflow-defects-session-pickup.md`, left alone. One worktree. 36 local commits ahead of `origin`, none pushed |

## What Changed Since the Prior Report

| Commit | What it is | Effect on this audit |
|---|---|---|
| `5976ff62` | Proof D run 5 `PASS`, synthetic decided contract (PE-1.5) | Now Proof D's admissible evidence (PE-1.7 ruling) |
| `f23b9549` | Proof C run 3 `FAIL`, time bound (PE-1.5) | History. Its route produced PE-1.6 |
| `cd2ef261` | Charter PE-1.6: Proof C clock rule and 120-minute bound, run 4 onward | Charter change control |
| `4c6e2701` | Proof C run 4 `PASS` (PE-1.6), T1 − T0 = 12 m 41 s | Proof C's effective evidence, with open items (below) |
| `08787a4b` | Operator routing commit: Orchestrator and Ship routes to claude-opus-5.5/anthropic/high in config and in mirror frontmatter lines 8-10; three manifest checksums and notes refreshed | Operator setup commit. It moves two `PE-ACTIVATE-01` blobs |
| `e65887d8` | Charter PE-1.7: comparator rebaselined to `08787a4b`; `PE-FLOW-04` ruling (Option A) recorded | Charter change control. It governs this audit |

## Proof Verdicts (section 8 item 1)

Every verdict is listed as recorded, under the version it was recorded
against. None is re-labelled. No proof `PASS` confers claim, closure, P-004
red or `harness-ready` authority (`PE-ACTIVATE-03`).

| Proof | Effective verdict | Commit and charter | Scope limits | History (unchanged) | Conditions |
|---|---|---|---|---|---|
| A | Run 5 **`PASS`** | `99e9ff5f`, addendum `4d132bf9`; PE-1.4 | Synthetic source-layout fixture only. Runner half from Ship's execution, policy half from Stage's static comparison | Invocations 1-3 `BLOCKED` (`231a2e5a`); run 4 no verdict | OD-3: the R2 reading, the file-bound count and the spool classification. A veto turns it into `BLOCKED` or `FAIL` as its artifact states |
| B | Run 3 **`PASS`** | `6920cb7c`; PE-1.4 | Disposable stub and predicate only. CR-B1 to CR-B5 carry forward | Run 1 historical `PASS` (`83525c62`); run 2 `BLOCKED` (`669ee9f6`) | OD-3: the spool classification and the direct CLI refresh transport. A veto gives `BLOCKED` |
| C | Run 4 **`PASS`** | `4c6e2701`; PE-1.6 | Synthetic truth table and candidate schema, plus real-surface controls read from Git blobs at `cd2ef261`. It ratifies **none** of the section 6.5 candidate proposals. R-C3b is `DISPUTED_NOT_ASSUMED`. Render parity is `false` (an operator follow-up, not a Proof C condition). The run 1 to 4 scratch directories are retained | Run 1 `FAIL` (PE-1.3, `9d0ed834`); run 2 `BLOCKED` (PE-1.4, `309ab0e2`); run 3 `FAIL` (PE-1.5, `f23b9549`) | OD-9: the Orchestrator's `git stash` set-aside of the operator's uncommitted mirror edit during run 4's Ship invocations (below). Evidence gaps go under OD-4 |
| D | Run 5 **`PASS`** | `5976ff62`; PE-1.5 | Synthetic decided contract only, not a production resolver. The run 4 limitations carry forward (precedence cases short-circuited, byte-code applicability at absent candidates not modelled, first-code selection not tested with competing errors) | Run 1 `FAIL` (`b3fca43a`); run 2 historical `PASS` (`a0079ac0`); run 3 `FAIL` (`8179feb1`); run 4 `PASS` (PE-1.4, `36f65975`), now the recorded `PE-FLOW-04` historical exception | None on the verdict. The operator's Option A ruling makes run 5 the admissible evidence |
| E | Run 5 **`PASS`** | `c7d5f97e`; PE-1.5 | Synthetic state-machine model. L1-L7 narrow the claim | Runs 1-4 `BLOCKED` | None on the verdict. Evidence gaps go under OD-4 |
| F | Run 2 **`PASS`** | `8b39a08b`; PE-1.4 | Checksum replay in a disposable repository | Run 1 historical `PASS` (`3df0509f`) | None on the verdict. Evidence gaps go under OD-4 |
| G | **`PENDING-LINUX`** | `6daf80bb`, addendum `06f8930b`; PE-1.4 | Windows `PASS` (runs 1 and 2, 49 of 49). Linux `PENDING`, never `PASS`. Execution on a Linux-native filesystem is non-waivable | Two earlier Ship halts, no verdict | OD-3: the file-bound count |

**The `git stash` set-aside (disclosed in `4c6e2701`).** The operator had an
uncommitted routing edit in `.github/agents/_ship.agent.md`, a
`PE-ACTIVATE-01` path. Section 6.1 makes Ship stop before its first write
when any of those paths has an uncommitted change. Before Ship's invocations,
the Orchestrator ran `git stash push -- .github/agents/_ship.agent.md`
(22:29:05). After them it restored the edit (`git stash pop`, 22:34:22). So
Ship's pre-write checks passed. Two facts limit the effect:

* The verifier read every real-surface input from Git blobs at `HEAD`
  (`git show HEAD:<path>`), never from the working tree. The edit could not
  change the fixture output.
* The edit was frontmatter routing only. The operator later committed it as
  `08787a4b`, and PE-1.7 records it as not an activation.

The Orchestrator is not a proof actor, and section 6.1 says there is "no
role workaround". Stage cannot accept a change to a proof-gated tracked
path on the operator's behalf. This is OD-9. If the operator rejects the
set-aside, Ship's gate should have halted run 4, which makes run 4
`BLOCKED`, and `PE-FLOW-02`, `PE-INTERFACE-03`, `PE-DATA-01` and
`PE-DATA-02` go back to `UNSATISFIED`.

## PE-ACTIVATE-01 Recheck at HEAD `e65887d8` (comparator `08787a4b`, PE-1.7)

Stage hashed the raw blob bytes from `git cat-file blob`, captured in binary
by a Python subprocess.

| Path | Blob at HEAD | Equal to `08787a4b` | Raw-blob SHA-256 at HEAD | Equal to section 3.6 | CRLF |
|---|---|---|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | `4ccd7fdc2d134de485487acd75bfbc105d6f40ee` | Yes | `a2451b355d27203db51515c9f72289a59a2e11af06d2910fd934fef489f4cbeb` | Yes | 0 |
| `.github/agents/_ship.agent.md` | `66933efaf085e7acff0db47f0bdc452a4fe58830` | Yes | `fd5a45a6c93e592eaf894228151416fdf35b527f79ee7bec6e11fa03f258b261` | Yes | 0 |
| `.autoharness/harness-manifest.yaml` | `e4274043e66a104ca8cf9f43e0d4e939847ac30e` | Yes | `1bef348082817e9dd2706484ffa3052bdef83059490e613d590d1e94d974255e` | Yes | 0 |

* `git diff --name-only 08787a4b HEAD --` over the three paths is empty. The
  only commit after `08787a4b` is `e65887d8`, which changes only the charter.
* `git status --porcelain` over the three paths is empty.
* **No activation, full or partial, occurred.** Section 3.6 records that the
  move from `4acba14a` to `08787a4b` is frontmatter-only routing plus checksum
  values. The template blob is unchanged, the mirror body is byte-identical
  and every section 6.7 anchor line is unchanged.
* This refresh adds one file under `docs/decisions/`, so the three blobs at
  its own commit are the same blobs.
* Earlier checks against `4acba14a` stand as recorded under the version they
  were made under (section 3.6).

## Row Audit (section 8 item 2)

**Status legend** (unchanged from the prior report):

* **`MET`**: met on the record at `e65887d8`.
* **`MET-COND`**: met only under a recorded Stage reading, or subject to a
  Stage finding or an Orchestrator action that needs an operator decision.
  It is **not** counted as met.
* **`OPEN-EVIDENCE`**: the record does not establish the criterion.
* **`UNSATISFIED`**: not met.
* **`WIN-MET / LINUX-PENDING`**: the Windows half is met and the Linux half
  is carried as the `linux-execution-gate`.
* **`DEFERRED`**: `deferred-to-implementation-matrix`.

Stage re-audited all 40 rows against the record at `e65887d8`. Eight rows
change status.

### Rows Whose Status Changes

| Row | Sev | Prior status (`9c83517d`) | Refreshed status | Reason and evidence |
|---|---|---|---|---|
| `PE-FLOW-02` | `P0` | `UNSATISFIED` (gate closed) | **`MET-COND`** (gate still closed) | Seven verdicts are now listed: A, B, C (run 4), D (run 5), E and F are `PASS`, and G is `PENDING-LINUX` with its Linux gate carried as IM-01, `not-deferrable`. No Phase 2 artifact exists: `git diff --name-only 082df7b2 HEAD -- docs/plans docs/reviews` is empty, and no `.backlogit/queue` or `.backlogit/archive` file changed. But three verdicts rest on pending decisions: A and B on OD-3, and C run 4 on OD-9. A veto of any of them removes a `PASS`. So Stage does not count the row as met. Phase 2 also stays closed because the matrix is not ratified (`PE-TASK-03`) |
| `PE-FLOW-04` | `P1` | `UNSATISFIED` (Stage fail-closed finding) | **`MET`** | The operator ruled Option A at 2026-09-25T13:27:40-07:00. PE-1.7 (`e65887d8`, section 3.6 and the note under the section 7.4 table) records it, with the row text unchanged. Stage applied that reading to the full record. The recorded `FAIL` verdicts are C run 1, C run 3, D run 1 and D run 3. A, B and E had only `BLOCKED` runs, and F and G had none. Every re-run after a `FAIL` came after a version bump: C run 2 after PE-1.4 (`52c985cb`); C run 4 after PE-1.6 (`cd2ef261`, 19:30:21, before the 22:24:25 authorization); D run 2 after PE-1.2 (`286aa4af`); D run 5 after PE-1.5 (`d31d7b42`, 17:29:37, before the 18:21:44 authorization). The one exception is D run 4 (`36f65975`), which is the single closed, recorded historical exception. Its breach stays on the record, and no verdict is relabelled. The row is not conditional, because the ruling is explicit. Disclosed and non-blocking: run 3's route ("caught" made concrete by charter change control) is still not enacted, and Option A accepts run 5 without it |
| `PE-INTERFACE-03` | `P1` | `UNSATISFIED` | **`MET-COND`** (OD-9) | C run 4, criterion 1. There are 8 label cases, including two unknown-but-well-formed surfaces (`harvest`, `impl-plan`). Each gives `SURFACE_UNSUPPORTED`, which is `UNRESOLVED` and never `NO_HARNESS`. `failure_count` is 0, and Stage reproduced the relayed stdout SHA-256 (`5d75c454...3d7324`, 1052 B). `SURFACE_UNSUPPORTED` is in the section 6.5 governing set, not a candidate proposal, so the row does not depend on the unratified candidate. The only condition is OD-9 |
| `PE-DATA-01` | `P1` | `UNSATISFIED` | **`MET-COND`** (OD-9) | C run 4, criteria 1 to 3. Governing codes 8 of 8, with correct state and exit. Read-limit cases: 21 single, 42 same-stage pairs and 294 cross-stage pairs, each giving `UNRESOLVED / 2` with the first-occurring code. Reachability 47 of 47. 2162 ordered precedence pairs. `reference_47_difference` is 0, and the state split is 2 / 4 / 41. **Candidate not ratified:** since PE-1.4, the row measures against the governing set and "the Stage candidate" as a proposal (section 3.3). Its pass criterion does not require ratification, so non-ratification does not condition this proof-entry row. It does condition the final contract, carried as IM-17 (OD-11). **R-C3b:** this is a read-limit error followed by a later recheck that completes with a disagreement. It is outside the section 6.5 pass list. The class 1 before class 1b precedence is fixed by the governing table. What is undecided is whether the recheck runs at all after a read-limit error (Decision 2 items 2 and 5). Both variants give `UNRESOLVED / 2`, and only the reason code differs. Under the section 3 change-request rule it is a change request, not a proof-phase blocker. It is carried as IM-16 (OD-10), and Stage assumes neither answer. The only condition on the row is OD-9 |
| `PE-DATA-02` | `P1` | `UNSATISFIED` | **`MET-COND`** (OD-9) | C run 4, criterion 4, plus criterion 2 for the governing codes. 47 schema branches and 47 surface branches are produced. 9 of 9 mutants are rejected by both the predicate and the schema, including the retired `READ_BUDGET_EXHAUSTED` code and a class 1b code replaced by `MEMBERS_TOO_MANY`. An output for every governing code validates against the candidate schema. Parity is proven for the candidate schema as proposed, and its ratification is IM-17. The only condition is OD-9 |
| `PE-DATA-03` | `P1` | `MET-COND` (OD-2) | **`MET`** | The operator ruling (Option A, PE-1.7) makes D run 5 (`5976ff62`, PE-1.5) Proof D's admissible evidence: `C_max` 202, margin 54, no byte-fit claim, `UNRESOLVED / 2` at every read and recheck stage, and 9 of 9 mutants caught. The row no longer depends on run 4. Run 5's residual evidence items are counted under `PE-AUTH-02` (P-010 self-check not itemized) and `PE-EVIDENCE-01` (interpreter version "probable", corroborated by Stage) |
| `PE-TASK-01` | `P1` | `MET` | **`MET-COND`** (OD-3, new reading (i)) | New fact: C run 3's recorded elapsed time went past its 75-minute bound (18:07:19 to after 19:22:19). It was recorded `FAIL`, as `PE-SCOPE-07` requires. Every section 6.2 bound is still at most 120 minutes (C is 120 from run 4, PE-1.6). The reported runs are within their bounds: C run 4 took 12 m 41 s of 120, and D run 5 about 15 of 45 minutes. Run 3 still stayed under 120 minutes, so it respected the 2-hour rule the requirement names. But the criterion, "recorded elapsed time is within its bound", is met only if the elapsed-time clause is read over reported runs, as the prior report did. Read over every run, run 3 makes the row permanently unmet. That reading needs OD-3 |
| `PE-EVIDENCE-05` | `P2` | `MET` | **`MET-COND`** (OD-3, new reading (ii); non-blocking) | The reported-run artifacts, C run 4 and D run 5, declare the engram, intercom, graphtor-docs and backlogit states (as not probed, or degraded). The non-reported C run 3 artifact does not, and neither does the historical D run 2 artifact. The row says "each artifact". The prior report's `MET` rested on a reported-run reading that it did not flag. Stage now flags it. `P2` does not block proof exit |

### Rows With Unchanged Status but Changed Evidence

| Row | Status (unchanged) | What changed |
|---|---|---|
| `PE-AUTH-01` (`P0`) | `MET-COND` | Seven commits since `c7d5f97e`. Four are Stage findings or report commits, each changing one `docs/decisions/*-spike.md` file (`9c83517d`, `5976ff62`, `f23b9549`, `4c6e2701`). Two are charter change control under section 3 (`cd2ef261`, `e65887d8`). One is the operator setup commit `08787a4b`, recorded as operator-approved in section 3.6: operator ruling 1 covers the Ship routing and manifest checksums, and the operator's 22:24:25 statement covers the config and Orchestrator edits. Its `Copilot-Session` trailer shows that an agent session made the commit under that approval. Git has one author identity and cannot attribute actors further. The conditions are now OD-5 (narrowed, below) and OD-9 (a non-proof actor changed a proof-gated tracked path in the working tree during a proof). The Proof F `.backlogit` gap stays under OD-4 |
| `PE-AUTH-02` (`P1`) | `OPEN-EVIDENCE` | **Proof D:** run 4's unnamed transport and 489 B stderr no longer count, because run 4 is not relied on. Run 5 records the transport (the CLI fallback, MCP absent), exit 0, stdout 23 B with its SHA-256, and empty stderr. Its remaining gap is that the P-010 self-check is not itemized. **Proof C:** run 2's gaps are superseded. Run 4 records the CLI refresh exit 0 and "indexed 1472 artifacts". It does not record the byte length and SHA-256 of the refresh stdout and stderr, whether MCP was tried first, the active-filtered task, feature and chore projections (only shipments are itemized), or an itemized P-010 self-check. **E, F and G:** unchanged. Needs OD-4 |
| `PE-AUTH-04` (`P1`) | `MET` | `e65887d8` adds a recorded historical exception to how `PE-FLOW-04` is evaluated. It went through the section 2 route: a question about the row was routed to the operator, and the operator ruled through a charter version. It authorizes no re-run and keeps run 4's breach on the record. It fits the parent decision, whose stop-condition outcomes include "explicit risk acceptance". No row states an exception to a higher source |
| `PE-SCOPE-01` to `04`, `06` | `MET` | Rechecked at `e65887d8`. The plan, reviews and governing decision are unchanged since `082df7b2`. The only `.backlogit/` change since `082df7b2` is still the two checkpoint files in `5bcb00e5`. The tracked `.backlogit/queue/187-S.md` is unchanged since `082df7b2`: `queued`, 17 items, labels `dag-root`, `shipment`, `ship-lifecycle` and `harness-architect`, and no `harness-ready`. Both lock files exist with length 0. No MCP shipment read was made, because the index is not refreshed |
| `PE-SCOPE-05` (`P2`) | `MET` | The three new findings artifacts name none of `176-S`, `184-S` to `186-S` or `188-S` to `191-S`. They mention `173-S` only as preflight context, not as a dependency |
| `PE-SCOPE-07` (`P1`) | `MET-COND` | C run 3's overrun is recorded `FAIL`, as the row requires. C run 4 used 2 files and 12 m 41 s. D run 5 used 1 file and about 15 minutes. The condition is still OD-3 (the A and G file-bound counts) |
| `PE-SAFETY-04` (`P1`) | `WIN-MET / LINUX-PENDING` | The Proof D half now rests on D run 5 and is no longer subject to a `PE-FLOW-04` finding. The row text names run 2. Section 3.3 required a new run, and section 3.4 lets a PE-1.5 run meet that |
| `PE-EVIDENCE-01` (`P1`) | `OPEN-EVIDENCE` | C run 2's gap is superseded. C run 4 records the question, host, filesystem, interpreter, command, raw output with its hashes, fixture listing with per-file SHA-256, per-criterion verdict, elapsed time, file count and scratch path. It does not record the refresh record's bounded output (byte length and SHA-256) or the `.backlogit` ignored status before and after. D run 5 is met, apart from the interpreter version being "probable" (Stage-corroborated). E, F and G are unchanged. Needs OD-4 |
| `PE-EVIDENCE-04` (`P2`) | `MET` | C run 3 and D run 5 shared one operator authorization (18:21:44). They have separate Ship invocations, verdicts, artifacts and time records |
| `PE-ACTIVATE-01` (`P0`) | `MET` | Now judged against `08787a4b` (PE-1.7; recheck above) |

Every other row keeps both its status and its evidence basis from the prior
report: `PE-AUTH-03`, `PE-FLOW-01`, `PE-FLOW-03`, `PE-INTERFACE-01`,
`PE-INTERFACE-02`, `PE-SAFETY-01` to `03`, `05` to `07`, `PE-DATA-04`,
`PE-TASK-02`, `PE-TASK-03`, `PE-EVIDENCE-02`, `PE-EVIDENCE-03`,
`PE-ACTIVATE-02` and `PE-ACTIVATE-03`. A text audit of the three new
artifacts found no authorization of attempt 12, revision 13, claim,
retirement, re-charter, reviewer selection or `P2` policy (`PE-AUTH-03`).
Every "authorization" found is an operator authorization of a proof run. It
also found no race, TOCTOU or hardlink-alias claim (`PE-SAFETY-06`). C run
3's `FAIL` names its reopened decision, the clock rule, which `cd2ef261`
settled (`PE-FLOW-01`).

### Counts

| Status | Rows | IDs |
|---|---|---|
| `MET` | 18 | AUTH-03, AUTH-04, SCOPE-01 to 06, FLOW-01, FLOW-03, FLOW-04, SAFETY-06, DATA-03, DATA-04, TASK-03, EVIDENCE-04, ACTIVATE-01, ACTIVATE-03 |
| `MET-COND` | 10 | AUTH-01 (`P0`), FLOW-02 (`P0`), SCOPE-07, INTERFACE-02, INTERFACE-03, DATA-01, DATA-02, TASK-01, EVIDENCE-03, EVIDENCE-05 (`P2`) |
| `OPEN-EVIDENCE` | 2 | AUTH-02, EVIDENCE-01 |
| `UNSATISFIED` | 0 | none |
| `WIN-MET / LINUX-PENDING` | 7 | SAFETY-01, 02, 03, 04, 05, 07, EVIDENCE-02 |
| `DEFERRED` | 3 | INTERFACE-01, TASK-02, ACTIVATE-02 |
| **Total** | **40** | 36 not-deferrable, 1 mixed (SAFETY-02) and 3 deferred |

Of the 37 not-deferrable or mixed rows, 18 are cleanly `MET`. The other 19
are 10 `MET-COND`, 2 `OPEN-EVIDENCE` and 7 with the Linux half `PENDING`.

**Decisions and the rows they close.**

| Decision | Rows it closes |
|---|---|
| OD-9 | `PE-INTERFACE-03`, `PE-DATA-01` and `PE-DATA-02` fully. It is part of `PE-FLOW-02` and `PE-AUTH-01` |
| OD-3 | `PE-SCOPE-07`, `PE-INTERFACE-02`, `PE-TASK-01`, `PE-EVIDENCE-03` and `PE-EVIDENCE-05`. It is part of `PE-FLOW-02` and `PE-AUTH-02` |
| OD-5 | Part of `PE-AUTH-01` |
| OD-4 | `PE-AUTH-02` and `PE-EVIDENCE-01` |

If the operator accepts OD-9, ratifies the OD-3 readings, confirms OD-5 and
closes OD-4, every proof-entry row is `MET`, carried as a Linux gate or
deferred. A veto instead changes the named verdicts and rows as stated
above.

## Implementation Matrix Draft, Refreshed (section 8 items 3 and 4)

> **DRAFT, NOT RATIFIED.** This matrix authorizes no implementation, plan,
> harvest, review epoch, activation or claim. Every row may change at
> ratification. Only the operator ratifies it, after proof exit and before
> any new review epoch (section 3). It should not be ratified while the
> conditional and open-evidence rows above remain open.

The IDs are kept from the prior draft. IM-16 and IM-17 are new, because the
Proof C run 4 evidence requires them. The render-parity follow-up stays in
IM-10.

| Draft ID | Requirement (draft) | Source | Proposed severity | Proposed deferral | Current status | In plain language |
|---|---|---|---|---|---|---|
| IM-01 | **Actual Linux-native execution** of the full Proof G case set (including G31 FIFO and the Linux symlink cases), in CI on a Linux runner with a Linux-native filesystem. It carries the Linux halves of `PE-SAFETY-01` to `05` and `07` and `PE-EVIDENCE-02`. Mocks, simulation, a Windows volume mounted into Linux and Windows evidence never satisfy it. No lifecycle release unit that depends on this containment ships without it | Section 6.9; `linux-execution-gate`; Proof G (`6daf80bb`, `06f8930b`) | `P1` | **`not-deferrable`, non-waivable** execution and release gate | **Open.** `PENDING-LINUX`. No Linux-native run is recorded | The file-safety checks have only run on Windows. They must pass on a real Linux machine before anything that relies on them ships, and no one can waive this |
| IM-02 | Cross-platform acceptance for every row that needs both hosts | Section 5 platform mandate; section 8 item 4 | `P1` | `not-deferrable`. Met only when IM-01 passes | **Unmet** | It cannot be called cross-platform until the Linux run in IM-01 passes |
| IM-03 | The SurfaceSpec reason taxonomy and result schema are closed and schema-parity-complete against the section 6.5 governing reason set. The implementation reproduces the proven truth table (47 codes, state split 2 / 4 / 41, all 9 mutant rejections), or a ratified revision is re-proven the same way | `PE-INTERFACE-03`, `PE-DATA-01`, `PE-DATA-02`; Proof C run 4 (`4c6e2701`) | `P1` | `not-deferrable` | **Proof-backed, conditional.** C run 4 `PASS` (PE-1.6) proves closure and parity for the Stage candidate as proposed, subject to OD-9. It is not final until IM-16 and IM-17 are decided | The list of reasons the resolver can give is proven complete, and it matches its schema in the test model. It needs the decisions in IM-16 and IM-17 before it is the final contract |
| IM-04 | The read budget is admitted `1..48`, `max_files=256`, with no byte-fit claim, and `UNRESOLVED / 2` at every read and recheck stage. Also test multi-error first-code selection, byte-code applicability at absent candidates, and precedence without short-circuit | `PE-DATA-03`; decision `286aa4af`; D run 5 (`5976ff62`); D runs 4 and 5 limitations | `P1` | `not-deferrable` | **Proof-backed.** D run 5 is admissible under the OD-2 ruling (`e65887d8`). The three limitation tests are open for implementation | The file-count budget is proven to fit up to 48 members, and every overflow fails safely. The implementation must add tests for three edge cases the model skipped |
| IM-05 | Bounded raw reads loop until EOF or cap+1, so a short read never becomes silent truncation. The byte bound is measured the same way on Windows and Linux | `PE-SAFETY-04`, `05`; G run 2 design note | `P1` | `not-deferrable` | **Open** (implementation). Windows design evidence only | A read must never silently cut a file short, and the size limit is measured the same way on both systems |
| IM-06 | No public or caller-supplied traversal adapter. Any test seam is private | `PE-INTERFACE-01` | `P1` | `not-deferrable` | **Binding part met** in Proof G. Carried into implementation | Don't expose a pluggable path-walking hook. Keep any test hook private |
| IM-07 | Ship consumes a validated document, not a process status. Resolve CR-B1 to CR-B5, including float-form `exit_code` being accepted (CR-B3) and the deep-nesting `RecursionError` (CR-B4) | `PE-INTERFACE-02`; Proof B run 3 | `P1` | `not-deferrable` | **Proof-backed, conditional** on OD-3. CR-B1 to CR-B5 are open | Ship must trust only a checked result document, never an exit code alone. Five known parser gaps must be fixed |
| IM-08 | The activation of template, mirror and manifest checksum is one task and one commit, measured against the `PE-ACTIVATE-01` comparator `08787a4b` (PE-1.7). The replacement wording for both PE-1.5 template spans meets the section 6.7 post-activation restore contract, keeps a session-start invocation of the recovery machine (E L6) and keeps the C1-C6 wiring (E O4) | `PE-ACTIVATE-02`; `PE-FLOW-03`; Proof E run 5; charter section 3.6 | `P1` | `not-deferrable` at implementation | **Open** (implementation). The baseline is now `08787a4b` | Switching Ship to the new per-task flow happens in one commit, starts from today's approved files, and keeps the safe crash-recovery order |
| IM-09 | The post-activation recovery fixture closes E L1 (rendered mirror form), L3 (an open event vocabulary that fails closed), L4 (unexercised branches) and L5 | Proof E run 5 | `P2` | Proposed `operator-deferrable` | **Open** | After the switch, extend the recovery test to cover the cases the model did not |
| IM-10 | Before any byte-exact render-parity resolver runs against `harness-architect` at HEAD, reconcile the render mismatch (first difference at byte 4994, a line reflow) in its own operator-approved release unit, without loosening the comparison | Proof C runs 2 to 4, real-surface control | `P1` | `not-deferrable` for that resolver | **Open.** Confirmed again by C runs 3 and 4 (`render_parity` `false` with every placeholder resolved). Capture is pending OD-7 | One installed skill file differs from its template by a line wrap. Fix it in its own small change before a byte-exact checker is switched on |
| IM-11 | Each future shipment holds at most 6 tasks and 8 hours, is independently valuable and carries two-axis sizing. An overrun escalates per P-013.6 | `PE-TASK-02` | `P1` | `not-deferrable` at harvest | **Open** (Phase 2) | Future work packages stay small: at most 6 tasks and 8 hours each |
| IM-12 | Manifest checksums come from raw staged-blob bytes: a Python subprocess with binary capture of `:<path>`, `git add --renormalize` when an `eol=lf` pin is added, and no redirect or PowerShell text capture | `PE-DATA-04`; Proof F run 2 | `P1` | `not-deferrable` | **Proof-backed.** F run 2. Each of the three values refreshed in `08787a4b` equals the raw-blob SHA-256 at that commit (charter section 3.6) | Checksums are computed from the exact committed bytes. Today's routing commit did this correctly |
| IM-13 | P-004 red evidence uses the exact canonical command with per-test marker attribution, read under R2 if the operator ratifies it (OD-3) | `PE-EVIDENCE-03`; Proof A run 5 | `P1` | `not-deferrable` | **Proof-backed, conditional** on OD-3 | Evidence that a test fails first must come from the exact standard test command and name the specific test |
| IM-14 | No artifact claims race, TOCTOU or hardlink-alias resistance | `PE-SAFETY-06` | `P2-critical` | `not-deferrable` | **Holding.** The text audit is clean | Never claim protection against race conditions or hard-link tricks. That is out of scope |
| IM-15 | Publication, execution and claim/closure gates stay distinct. A test or proof `PASS` confers no claim authority | `PE-ACTIVATE-03`; section 9 | `P1` | `not-deferrable` | **Holding.** Publication and claim are both not ready | Passing a proof or a test never, by itself, lets anyone claim, merge or publish |
| IM-16 (new) | **Decide R-C3b and test it.** A read-limit error occurs first, and a later recheck completes with a disagreement. Does the resolver report the read-limit code (early return) or `INPUT_CHANGED_DURING_RESOLUTION`? Both are `UNRESOLVED / 2`, and only the reason code differs. Decide in architecture (Decision 2 items 2 and 5), record the decision, and test both orders | Proof C run 4 (R-C3b `DISPUTED_NOT_ASSUMED`); `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md` Decision 2; charter section 3 change-request rule | `P1` (proposed; the operator may lower it) | `not-deferrable` before the resolver result contract is frozen | **Open.** Needs OD-10 | In one rare double-failure case, the design does not say which of two reason codes to report. Both correctly say "unresolved", but one must be chosen before the contract is final |
| IM-17 (new) | **Ratify, revise or reject the section 6.5 Stage candidate proposals** that the governing set does not settle: the codes outside the governing set, the order within classes 2, 3 and 5 to 7, the tie-break between declaration issues, and the shape of `declarations` items. Any revision is re-proven with the Proof C method (exhaustive enumeration, schema parity, mutants) before the resolver API is frozen | Proof C run 4 (its `PASS` ratifies none of them); section 6.5; section 3.3 (the candidate is a proposal, not ratified API) | `P1` | `not-deferrable` before API freeze | **Open.** Needs OD-11 | The proof shows the proposed reason list works. The operator has not yet agreed that it is the list to build |

## Open Operator Decisions (section 8 item 5)

| ID | Decision | Status | Rows or IM affected |
|---|---|---|---|
| C2 | Release-unit split | **Open.** Bounded proposal pending operator ratification (Phase 2) | Phase 2 |
| C3 | Migration and the fate of `187-S`: retire or re-charter, never patch | **Open.** Pending operator ratification (Phase 2). `187-S` stays `queued` and frozen | Phase 2, claim |
| C4 | `P2` publication policy, reviewer lead and routing | **Open.** Pending operator ratification (Phase 4). No `model_routing.anchor_review` route is selected | Review epoch |
| OD-1 | Proof C path (C-1 to C-4) | **Superseded.** Proof C run 4 `PASS` (PE-1.6, `4c6e2701`) replaces the need. Run 2 stays `BLOCKED` as history, and its breaker is not bypassed | none |
| OD-2 | Proof D run 4 under `PE-FLOW-04` | **Resolved** by the operator's Option A ruling (2026-09-25T13:27:40-07:00), recorded in PE-1.7 (`e65887d8`). The residual, run 3's unenacted "caught" clarification, is optional and not required | `PE-FLOW-04`, `PE-DATA-03`, `PE-SAFETY-04` (closed) |
| OD-3 | Ratify or veto the Stage readings: (a) Proof A's R2 reading; (b) the A and G file-bound counts; (c) the A, B and C spool classification; (d) the direct CLI refresh transport; **new** (i) `PE-TASK-01`'s elapsed-time clause is read over reported runs, and an overrun run is recorded `FAIL` (`PE-SCOPE-07`) without failing the row; **new** (ii) `PE-EVIDENCE-05` is read over reported-run artifacts | **Open** | `PE-FLOW-02`, `PE-SCOPE-07`, `PE-INTERFACE-02`, `PE-TASK-01`, `PE-EVIDENCE-03`, `PE-EVIDENCE-05`, `PE-AUTH-02`; IM-07, IM-13 |
| OD-4 | Close the evidence gaps, by Ship's read-only transcription of evidence it already captured or by explicit operator acceptance of each gap. The gaps now are: C run 4 (refresh stdout and stderr byte length and SHA-256, MCP-first, task, feature and chore projections, P-010 itemization, `.backlogit` ignored status before and after); D run 5 (P-010 itemization, captured interpreter version); E run 5, F run 2 and G run 2 as before | **Open** (gap list updated) | `PE-AUTH-02`, `PE-EVIDENCE-01` |
| OD-5 | Confirm `89b0db6d` (config routing) as an operator setup commit outside the proof actors | **Open, narrowed.** `08787a4b` settles the record half: the manifest's config checksum now equals the config raw-blob SHA-256, and its note and commit message name `89b0db6d`. It does **not** settle the attribution half. Operator ruling 1 approves the Ship routing and checksum change, and says nothing about who made `89b0db6d`. It needs a one-line confirmation | `PE-AUTH-01` |
| OD-6 | Approve or withhold cleanup of the scratch directories under `.proof-scratch/`. There are now **17**: A runs 4 and 5; B runs 1 to 3; C runs 1 to 4; D runs 3 to 5; E runs 4 and 5; F; G runs 1 and 2. Proof C run 4 asks that the C run 1 to 4 directories stay as hash-pinned evidence until cleanup is approved. Ship alone removes them, under section 6.1 | **Open** | Hygiene only |
| OD-7 | Authorize capture of the render-mismatch follow-up as a stash entry or release unit after proof exit | **Open** | IM-10 |
| OD-8 | Confirm the reading of section 8 against section 7.1: proof entry exits when section 8 is met, and `not-deferrable` rows that do not hold block ratification and Phase 2 but do not undo the exit | **Open** | Every conditional or open row |
| OD-9 (new) | Accept or reject the Orchestrator's `git stash` set-aside of the operator's uncommitted mirror routing edit during Proof C run 4's Ship invocations (22:29:05 to 22:34:22, disclosed in `4c6e2701`). Stage recommends acceptance, because the fixture read only `HEAD` blobs and the edit is now the approved, non-activating `08787a4b`. But only the operator can decide. Rejection makes run 4 `BLOCKED` | **Open** | `PE-FLOW-02`, `PE-INTERFACE-03`, `PE-DATA-01`, `PE-DATA-02`, `PE-AUTH-01`; IM-03 |
| OD-10 (new) | Rule on R-C3b (Decision 2 items 2 and 5), or route it to an architecture decision | **Open** | IM-16 (not a proof-entry row) |
| OD-11 (new) | Ratify, revise or reject the section 6.5 candidate proposals | **Open** | IM-17, IM-03 (not a proof-entry row) |

## Remaining Gates

| Gate | What still blocks it |
|---|---|
| **Ratification of the implementation matrix** | OD-9, OD-3, OD-5 and OD-4 must be closed, so that no `MET-COND` or `OPEN-EVIDENCE` row remains, and OD-8 fixes the reading. OD-10 and OD-11 must be decided before IM-03 can be ratified as a final contract. Then the operator ratifies the draft itself. Stage does not ratify it |
| **Phase 2** (re-slice, harvest, plan) | Ratification above (`PE-FLOW-02` is `P0`, and `PE-TASK-03` forbids harvest before ratification), then C2 and C3. No plan revision, harvest or backlog item is created before that |
| **New review epoch** | Phase 2 output, C4, and ratification of the section 9 governance defaults |
| **Activation** (`PE-ACTIVATE-02`, IM-08) | A ratified matrix, a planned and reviewed release unit, and one task and one commit measured against `08787a4b`. Nothing is activated now |
| **Any claim of `187-S` or its successor** | C3 decides its fate first. Then the ordinary P-002 and P-004 claim gates, CI and closure gates apply. No proof `PASS` confers claim authority (`PE-ACTIVATE-03`, IM-15). Any release unit that depends on containment also needs IM-01 (Linux-native execution) to pass, and no one can waive it |
| **Publication** | Not ready. The verdict manifest records `publication_eligible: false`. The 36 local commits (37 with this one) are unpushed, and pushing is an operator action. Publishing Stage artifacts confers no claim authority |

## Next Actions (plain language)

1. **Decide OD-9.** Say whether the Orchestrator's temporary set-aside of your
   uncommitted Ship routing edit during Proof C run 4 is acceptable. If it
   is, the three Proof C rows become met, pending only the items below.
2. **Decide OD-3.** Approve or veto the six listed Stage readings.
3. **Close OD-4.** Either ask Ship to transcribe the missing handoff fields
   it already has (nothing is re-run), or accept each gap explicitly.
4. **Confirm OD-5** in one line: `89b0db6d` was your own setup commit.
5. **Decide OD-10 and OD-11**, or send them to an architecture decision. They
   do not block proof exit. They do block treating the Proof C candidate as
   the final contract.
6. **Only then** can Stage bring this draft back for ratification, together
   with C2, C3 and C4. Even after ratification, the Linux run (IM-01) must
   pass before anything that depends on containment ships.
7. **Until then:** `187-S` stays queued and frozen. There is no plan,
   harvest, review attempt, activation, claim, push or pull request.

## References

* Prior proof-exit report (kept unchanged): `docs/decisions/2026-09-24-lifecycle-proof-exit-spike.md` (`9c83517d`, PE-1.5, HEAD `c7d5f97e`)
* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (PE-1.7, `e65887d8`; sections 2, 3, 3.3 to 3.6, 6.1, 6.2, 6.5, 6.7, 6.9, 7, 8, 9 and 10)
* Proof C: `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run4-spike.md` (`4c6e2701`); history `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run3-spike.md`, `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run2-spike.md`, `docs/decisions/2026-09-24-surface-taxonomy-proof-c-spike.md`
* Proof D: `docs/decisions/2026-09-24-read-budget-proof-d-run5-spike.md` (`5976ff62`); history `docs/decisions/2026-09-24-read-budget-proof-d-run4-spike.md`, `docs/decisions/2026-09-24-read-budget-proof-d-run3-spike.md`, `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md`, `docs/decisions/2026-09-23-read-budget-proof-d-spike.md`
* Proofs A, B, E, F and G: as listed in the prior report's References
* Decision: `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md` (Decision 2)
* Parent decision: `docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md` (architectural rule; stop conditions and permitted outcomes)
* Operator routing commit: `08787a4b`
* Related: `docs/decisions/2026-09-20-pr457-bounded-review-convergence-deliberation.md`; `docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md`
* Rules: `.github/policies/workflow-policies.md`; `.github/instructions/constitution.instructions.md`; `.github/instructions/circuit-breaker.instructions.md`
