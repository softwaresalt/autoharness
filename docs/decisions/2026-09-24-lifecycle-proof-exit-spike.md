---
title: "Lifecycle proof-exit report (PE-1.5): proof entry exits, P1 rows unsatisfied, implementation matrix drafted but not ratified"
source: "docs/decisions/2026-09-24-lifecycle-proof-exit-spike.md"
doc_type: decision
description: "Stage-authored proof-exit report under charter PE-1.5 section 8 (charter commit d31d7b42), written read-only at HEAD c7d5f97e on chore/stage-176-s-workflow-defects in the one current worktree. It changes no earlier verdict. It lists the seven proof verdicts with their history: A run 5 PASS (synthetic fixture, with addendum), B run 3 PASS (disposable stub), C run 2 BLOCKED (circuit-breaker evidence and tool-wrapper spill, routed to the operator), D run 4 PASS (run 3 FAIL kept as history), E run 5 PASS (run 4 BLOCKED kept as history), F run 2 PASS, and G PENDING-LINUX (Windows PASS in runs 1 and 2, Linux PENDING). It audits all 40 PE-1.5 matrix rows. 18 rows are MET. 5 are MET only under Stage interpretations or findings that still need an operator decision. 2 are open for missing evidence. 5 are UNSATISFIED: PE-FLOW-02, PE-FLOW-04, PE-INTERFACE-03, PE-DATA-01 and PE-DATA-02. 7 are met on Windows with Linux PENDING, and 3 are deferred to the implementation matrix. Of the 37 rows that are not-deferrable or partly not-deferrable, 18 are cleanly MET. Stage rechecked PE-ACTIVATE-01 at HEAD: all three tracked blob IDs and raw-blob SHA-256 values equal the 4acba14a comparator, and the paths are clean. There was no activation. Section 8 is met in form, because Proof C is BLOCKED with a recorded route and Proof G is PENDING-LINUX with its gate carried. So proof entry EXITS. But the P1 and P0 rows above are unsatisfied and block the next Stage ratification. The lifecycle is NOT implementation-ready. The implementation acceptance matrix is drafted here and is not ratified. Actual Linux-native execution is carried as a non-waivable execution and release gate, and cross-platform acceptance is not met. Proof C's blocked path, and the choices for clearing it, are recorded. They are read-only evidence provenance first, then an explicit operator decision before any fresh Proof C. The tripped C script is not re-run, the breaker is not bypassed, and no PASS is taken from the final exit 0. The harness-architect real-surface render mismatch is recorded as follow-up work for a release unit after the proofs. It is not fixed here. C2, C3 and C4 stay open pending operator ratification. Publication and claim readiness are both false. 187-S stays queued and frozen. No backlog, plan, charter, source or Ship-surface change was made."
docline:
  type: spike
  date: 2026-09-24
  time_box: "n/a (proof-exit report; section 8, not a proof)"
  conclusion: "proof-entry-exits-p1-rows-unsatisfied"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "proof-exit"
    - "acceptance-matrix"
    - "ship-lifecycle"
    - "linux-execution-gate"
    - "governance-reset"
artifact_class: proof-exit-report
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.5"
charter_commit: d31d7b42
matrix_id: PE-1.5
charter_sections: ["3.1", "3.2", "3.3", "3.4", "6.1", "6.2", "7", "8", "10"]
head_at_authoring: c7d5f97e5f7820a584eaa475121277a8654da7b4
branch: chore/stage-176-s-workflow-defects
worktrees: 1
section_8_exit_condition_met: true
proof_entry_exits: true
implementation_ready: false
implementation_matrix_status: drafted-not-ratified
cross_platform_acceptance: unmet
linux_gate: "not-deferrable, non-waivable execution and release gate (section 6.9); Windows evidence never satisfies it"
proof_verdicts:
  - {proof: A, reported_run: 5, verdict: PASS, scope: synthetic-fixture-only, commits: [99e9ff5f, 4d132bf9], matrix: PE-1.4, history: "invocations 1-3 BLOCKED (PE-1.1, 231a2e5a); run 4 no verdict"}
  - {proof: B, reported_run: 3, verdict: PASS, scope: disposable-stub-and-predicate-only, commit: 6920cb7c, matrix: PE-1.4, history: "run 1 PASS historical (PE-1.3, 83525c62); run 2 BLOCKED (PE-1.4, 669ee9f6)"}
  - {proof: C, reported_run: 2, verdict: BLOCKED, route: operator, commit: 309ab0e2, matrix: PE-1.4, history: "run 1 FAIL (PE-1.3, 9d0ed834)"}
  - {proof: D, reported_run: 4, verdict: PASS, scope: synthetic-decided-contract-only, commit: 36f65975, matrix: PE-1.4, history: "run 1 FAIL (PE-1.1, b3fca43a); run 2 PASS historical (PE-1.2, a0079ac0); run 3 FAIL (PE-1.4, 8179feb1)"}
  - {proof: E, reported_run: 5, verdict: PASS, scope: synthetic-state-machine-model, commit: c7d5f97e, matrix: PE-1.5, history: "runs 1-4 BLOCKED (a04e1e5a, 6ee65c4a, 383ae6be, 945a224e)"}
  - {proof: F, reported_run: 2, verdict: PASS, commit: 8b39a08b, matrix: PE-1.4, history: "run 1 PASS historical (PE-1.1, 3df0509f)"}
  - {proof: G, reported_run: 2, verdict: PENDING-LINUX, host_verdicts: {windows: PASS, linux: PENDING}, commits: [6daf80bb, 06f8930b], matrix: PE-1.4}
prior_verdicts_changed: false
matrix_row_counts:
  total: 40
  met: 18
  met_conditional: 5
  open_evidence: 2
  unsatisfied: 5
  windows_met_linux_pending: 7
  deferred_to_implementation_matrix: 3
  not_deferrable_or_mixed: 37
  not_deferrable_met_clean: 18
unsatisfied_rows: [PE-FLOW-02, PE-FLOW-04, PE-INTERFACE-03, PE-DATA-01, PE-DATA-02]
open_evidence_rows: [PE-AUTH-02, PE-EVIDENCE-01]
met_conditional_rows: [PE-AUTH-01, PE-SCOPE-07, PE-INTERFACE-02, PE-DATA-03, PE-EVIDENCE-03]
activate_01_recheck: {head: c7d5f97e, comparator: 4acba14a, blobs_equal: true, raw_sha256_equal: true, crlf: 0, tracked_diff_empty: true, porcelain_empty: true, activation_occurred: false}
open_operator_decisions: [C2, C3, C4, OD-1, OD-2, OD-3, OD-4, OD-5, OD-6, OD-7, OD-8]
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_authoring: "queued, 17 items, labels dag-root/shipment/ship-lifecycle/harness-architect (Stage read-only MCP get_shipment and tracked file); frozen"
shipment_claim_ready: false
publication_eligible: false
publication_ready: false
claim_ready: false
backlog_item_created: false
stash_entry_created: false
plan_changed: false
charter_changed: false
ship_surface_changed: false
render_mismatch_follow_up: "post-proof release unit (not fixed here)"
proof_c_rerun_performed: false
circuit_breaker_bypassed: false
stage_model_route: "claude-opus-5.5/anthropic/high requested and configured; unverified by Stage (ROUTING_DEGRADED: not self-verifiable)"
---

# Lifecycle proof-exit report (PE-1.5)

## Bottom Line

| Question | Answer |
|---|---|
| Is the section 8 exit condition met? | **Yes, in form.** Every proof is `PASS`, except Proof C, which is `BLOCKED` with a recorded route (to the operator, `309ab0e2`), and Proof G, which is `PENDING-LINUX` with its Linux gate carried forward (section Implementation Matrix Draft) |
| Does proof entry exit? | **Yes.** Proof entry exits under section 8 |
| Are the proof-exit rows satisfied? | **No.** Five rows are `UNSATISFIED` (`PE-FLOW-02` is `P0`; `PE-FLOW-04`, `PE-INTERFACE-03`, `PE-DATA-01` and `PE-DATA-02` are `P1`). Two `P1` rows have open evidence gaps, and five rows are met only under Stage interpretations or findings that need an operator decision. These block the **next Stage ratification** of the implementation matrix |
| Is the lifecycle implementation-ready? | **No.** Nothing here makes the lifecycle ready for implementation, harvest, planning, a review epoch, activation or claim |
| Implementation acceptance matrix | **Drafted, not ratified** (section Implementation Matrix Draft) |
| Cross-platform acceptance | **Not met.** Linux has not been executed. Actual Linux-native execution is a `not-deferrable`, non-waivable execution and release gate |
| Publication readiness | **Not ready** (see Publication and Claim Readiness) |
| Claim readiness | **Not ready.** `187-S` stays `queued` and frozen |

## Scope and Method

* **Actor and scope.** Stage worked read-only. It ran no fixture, script,
  build, test suite or linter, no index refresh and no backlog mutation. It
  made no push, pull request, branch, claim, stash entry or backlog change, and
  it edited no earlier findings artifact, charter, plan, review, source,
  template, manifest or Ship surface. The only tracked change is this file.
* **What Stage read.** Charter PE-1.5 sections 1 to 10 (as committed at
  `d31d7b42`). The reported-run findings for all seven proofs, the Proof A
  run 5 addendum, the Proof G run 2 correction addendum, and the Proof D run 3
  findings for its route.
* **What Stage checked.** Read-only `git` queries (`rev-parse`, `cat-file blob`
  hashed in a Python subprocess with binary capture, `diff`, `status`,
  `worktree list`, `log`, `show --name-only`). File existence and lock-file
  lengths. Text audits with `Select-String` over the proof findings artifacts.
  A read-only listing of `.proof-scratch/`. Three read-only backlogit MCP
  calls: `get_version`, `get_shipment 187-S` and the unfiltered Stage
  checkpoint list.
* **Precedence.** This report is subordinate to the charter and to every
  source that the charter is subordinate to. It interprets nothing in its own
  favour. Where a reading is uncertain, the row is not counted as met.

### Session and Tool State (`PE-EVIDENCE-05`)

| Item | State |
|---|---|
| Tool gate | `.autoharness/backlog-registry.yaml` is present. backlogit MCP is `TOOL_OK`: `get_version` (update check skipped) returned `1.10.1-0.20260823032255-b07729386a31+dirty` |
| Index sync (Stage Step 0.1) | **Not run, on purpose.** Section 6.1 says "Stage never runs the refresh or any backlog CLI mutation for a proof", and the operator limited this session to read-only analysis. The shipment read below is checked against the tracked file |
| Stage checkpoint recovery | The unfiltered `consumer_id: stage` list returned 67 records, all `stage`/`resolved`. There were 0 anomalies and 0 active records. This is a normal zero-candidate startup |
| Stage-side tool-wrapper spool (disclosed) | The checkpoint list response (81,536 B) was too large for the tool channel. The host tool wrapper spooled it automatically to OS Temp, outside the current working directory. Stage did not direct that write. Stage read the spooled file read-only, in process, and printed only counts. This is not a Ship proof invocation, and it is disclosed on the same terms as the Proof A, B and C spools |
| agent-engram, agent-intercom, graphtor-docs | No tools exposed in this runtime: `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`. Files were read directly. No broadcast was made |
| Stage route | Configured as `claude-opus-5.5` / `anthropic` / `high`, as requested. The runtime cannot confirm the model it actually uses (`ROUTING_DEGRADED`) |
| Git at authoring | HEAD `c7d5f97e`. `git status --porcelain` empty. One worktree. 29 local commits ahead of `origin`, none pushed by this session |

## Proof Verdicts (section 8 item 1)

Every verdict is listed exactly as recorded, under the version it was
recorded against. None is re-labelled. A historical `PASS` without section 6.1
refresh evidence is listed, but it never satisfies a proof-exit row by itself.

| Proof | Reported run and verdict | History (unchanged) | Matrix rows | Recorded limits |
|---|---|---|---|---|
| A | Run 5 **`PASS`**, synthetic fixture only (PE-1.4, `99e9ff5f`; `PE-EVIDENCE-01` addendum `4d132bf9`) | Invocations 1-3 `BLOCKED` (PE-1.1, `231a2e5a`). Run 4 had no verdict (driver defect, superseded) | `PE-EVIDENCE-03`, `PE-FLOW-02` | The R2 reading, the file-bound count (1 authored script against 41 files on disk) and the spool classification are Stage interpretations. A veto turns the verdict into `BLOCKED` (R2, spool) or `FAIL` (file bound) |
| B | Run 3 **`PASS`**, disposable stub and predicate only (PE-1.4, `6920cb7c`) | Run 1 historical `PASS` (PE-1.3, `83525c62`). Run 2 `BLOCKED` (PE-1.4, `669ee9f6`) | `PE-INTERFACE-02`, `PE-SAFETY-05` | The spool classification and the direct CLI refresh transport are Stage interpretations. A veto gives `BLOCKED`. CR-B1 to CR-B5 carry forward |
| C | Run 2 **`BLOCKED`** (PE-1.4, `309ab0e2`), routed to the operator | Run 1 `FAIL` (PE-1.3, `9d0ed834`) | `PE-INTERFACE-03`, `PE-DATA-01`, `PE-DATA-02` | Two grounds, each enough alone: the same-error circuit breaker (admissibility of executions 5 and 6 not shown), and a tool-wrapper spill outside the current working directory. No section 6.5 fail condition was found. The render parity `false` is an observation (section Render Mismatch Follow-Up) |
| D | Run 4 **`PASS`**, synthetic decided contract only (PE-1.4, `36f65975`) | Run 1 `FAIL` (PE-1.1, `b3fca43a`). Run 2 historical `PASS` (PE-1.2, `a0079ac0`). Run 3 `FAIL` (PE-1.4, `8179feb1`) | `PE-DATA-03`, `PE-SAFETY-04` | Run 4 followed run 3's `FAIL` under the same version PE-1.4. See `PE-FLOW-04` in the audit. The refresh transport was not named, and the refresh stderr (489 B) is recorded by hash only |
| E | Run 5 **`PASS`**, synthetic state-machine model (PE-1.5, `c7d5f97e`) | Runs 1-4 `BLOCKED` (`a04e1e5a` PE-1.2, `6ee65c4a` and `383ae6be` PE-1.3, `945a224e` PE-1.4) | `PE-FLOW-03`, `PE-ACTIVATE-01` | L1-L7 narrow the claim. The handoff lacked Ship's elapsed time and the refresh stderr, and the refresh stdout hash was relayed only as a prefix |
| F | Run 2 **`PASS`** (PE-1.4, `8b39a08b`) | Run 1 historical `PASS` (PE-1.1, `3df0509f`) | `PE-DATA-04` | Three handoff items are still open: whether MCP was tried first, the `.backlogit` ignored-status before and after, and the itemized P-010 and P-002 results |
| G | **`PENDING-LINUX`** (PE-1.4, `6daf80bb`; run 2 correction addendum `06f8930b`). Windows `PASS` (runs 1 and 2, 49/49). Linux `PENDING` | None before run 1. Two earlier Ship halts happened before any write and left no verdict | `PE-SAFETY-01` to `07`, `PE-EVIDENCE-02`, `PE-INTERFACE-01` | Never `PASS`. The file-bound count is a Stage assumption. The run 2 refresh record lacks bounded output, and the "during" worktree listing is not stated separately |

`PE-FLOW-02` needs seven verdicts, each `PASS` or operator-deferred, except
that Proof G may be `PENDING-LINUX`. The table shows seven verdicts. Proof C is
`BLOCKED`, not `PASS` and not operator-deferred. So the Phase 2 gate stays
closed (see the audit).

## PE-ACTIVATE-01 Recheck at HEAD `c7d5f97e`

Stage hashed the raw blob bytes from `git cat-file blob`, captured in binary
by a Python subprocess.

| Path | Blob at HEAD | Equal to `4acba14a` | Raw-blob SHA-256 at HEAD | Equal to section 3.3 | CRLF |
|---|---|---|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | `4ccd7fdc2d134de485487acd75bfbc105d6f40ee` | Yes | `a2451b355d27203db51515c9f72289a59a2e11af06d2910fd934fef489f4cbeb` | Yes | 0 |
| `.github/agents/_ship.agent.md` | `e22916b62f36f1c25c421882a05f4049f1862c02` | Yes | `250fc87a4275a5b7c1a5a143b6c2d7d9b97c50db1b465a84157c3c891c4c8a38` | Yes | 0 |
| `.autoharness/harness-manifest.yaml` | `251f46e8c95703ed65e421210d3b08682d79d8bc` | Yes | `e3ddbac3e4648c06442de42e2f0ecc05c5dbee645cdb9e58760b5bdd010425d0` | Yes | 0 |

`git diff --name-only 4acba14a HEAD --` over the three paths is empty.
`git status --porcelain` over the three paths, and over the whole tree, is
empty. **No activation, full or partial, occurred.** This report adds one file
under `docs/decisions/`, so the three blobs at the commit of this report are
the same blobs.

## Row Audit (section 8 item 2)

**Status legend.** `MET`: the criterion is met on the record at `c7d5f97e`.
`MET-COND`: met only under a recorded Stage interpretation or subject to a
Stage finding that needs an operator decision (it is not counted as met).
`OPEN-EVIDENCE`: the record does not establish the criterion. It may be
closed by read-only transcription of evidence Ship already captured, or by an
explicit operator acceptance. `UNSATISFIED`: not met at proof exit.
`WIN-MET / LINUX-PENDING`: the Windows half is met and the Linux half is
carried as the `linux-execution-gate`. `DEFERRED`: `deferred-to-implementation-matrix`.

### AUTH

| Row | Sev | Deferral | Status | Evidence |
|---|---|---|---|---|
| `PE-AUTH-01` | `P0` | not-deferrable | `MET-COND` | 33 commits in `082df7b2..c7d5f97e`. 23 are Stage findings commits, and each changes exactly one `docs/decisions/*-spike.md` file. 6 are charter or decision change-control commits under section 3 (`2e3c98a1`, `1ad7c03a`, `286aa4af`, `7f833cb8`, `52c985cb`, `d31d7b42`). 4 are setup commits. Three of those are recorded as operator-approved or operator-directed in sections 3.2 and 3.3 (`5bcb00e5`, `d20820ec`, `4acba14a`). **`89b0db6d` ("updated routing", `.autoharness/config.yaml` only, 3 lines) is not recorded in the charter**. It touches no `PE-ACTIVATE-01` path. All commits have one author identity, so Git cannot attribute actors. Ship-side: no Ship commit is evidenced, and the fixture writes stayed in scratch as reported. Proof F lacks the `.backlogit` ignored-status before and after. Needs OD-5 |
| `PE-AUTH-02` | `P1` | not-deferrable | `OPEN-EVIDENCE` | Met for A run 5 and B run 3. Gaps: D run 4 does not name the transport. E run 5 relays the refresh stdout hash as a prefix only, and no stderr. F run 2 does not say whether MCP was tried first, and does not itemize P-010 or P-002. G run 2 lacks the bounded refresh output and the separate "during" worktree listing. The direct CLI transport (no evidence that MCP was tried first) is a Stage interpretation in B, D, E, F and G. C run 2 is `BLOCKED` in any case. Needs OD-4 |
| `PE-AUTH-03` | `P0` | not-deferrable | `MET` | This report lists C2, C3 and C4 as pending. A text audit of the 19 proof findings artifacts found no authorization of attempt 12, revision 13, claim, retirement, re-charter, reviewer selection or `P2` policy. Every "claim-ready" occurrence is negative. Ship evidence reports were read only as relayed inside the findings |
| `PE-AUTH-04` | `P1` | not-deferrable | `MET` | Every normative source cited by a row exists at HEAD (23 paths checked). P-001 to P-021 are all present in the policy registry. The constitution sections cited (I, III, IV, V, Governance) exist. No row states an exception to a higher source. One charter-internal tension is routed as OD-8, not resolved here |

### SCOPE

| Row | Sev | Deferral | Status | Evidence |
|---|---|---|---|---|
| `PE-SCOPE-01` | `P0` | not-deferrable | `MET` | `git diff --stat 082df7b2 HEAD` is empty for the plan, the verdict manifest, `docs/reviews/review-history/` and governing decision revision 9 |
| `PE-SCOPE-02` | `P0` | not-deferrable | `MET` | `git diff --name-only 082df7b2 HEAD -- docs/reviews docs/plans` is empty |
| `PE-SCOPE-03` | `P1` | not-deferrable (lifts at proof exit) | `MET` | No change under `.backlogit/queue/` or `.backlogit/archive/` since `082df7b2`. The only `.backlogit/` change in the range is two checkpoint files in the operator setup commit `5bcb00e5`. `backlogit_get_shipment 187-S` returns `queued` with 17 items (`181-F` plus 16 tasks), and this equals the tracked `.backlogit/queue/187-S.md`. The freeze does not lift in practice: see Next Actions |
| `PE-SCOPE-04` | `P0` | not-deferrable | `MET` | `187-S` is `queued`. Labels are `dag-root`, `shipment`, `ship-lifecycle` and `harness-architect`, with no `harness-ready`. No tracked `181-F`/`181.*` file contains `harness-ready`. The tracked shipment file is unchanged since `082df7b2` |
| `PE-SCOPE-05` | `P2` | not-deferrable | `MET` | A case-sensitive search of the 19 proof artifacts for `176-S`, `184-S` to `186-S` and `188-S` to `191-S` finds none |
| `PE-SCOPE-06` | `P1` | not-deferrable | `MET` | `docs/plans/.2026-09-18-p004-observation-gate-plan.md.lock` and `docs/reviews/.2026-09-18-p004-observation-gate-plan-review.md.lock` both exist with length 0 |
| `PE-SCOPE-07` | `P1` | not-deferrable | `MET-COND` | Every counted run is within its time bound. File bounds are met literally for B (2), C (2), D (1), E (1 of 2) and F (1 script and 1 repository). A (1 authored script, 41 files on disk) and G (1 script per run, generated tree excluded) are met **only under Stage file-bound interpretations**. A literal count makes A `FAIL` and G `FAIL`. Needs OD-3 |

### FLOW

| Row | Sev | Deferral | Status | Evidence |
|---|---|---|---|---|
| `PE-FLOW-01` | `P0` | not-deferrable | `MET` | Every `FAIL` names its route: C run 1 (PE-1.4 re-charter of section 6.5), D run 1 (decision `286aa4af`), D run 3 (charter change control for "caught"). No plan revision followed (`PE-SCOPE-02`) |
| `PE-FLOW-02` | `P0` | not-deferrable | `UNSATISFIED` (gate closed, not violated) | Seven verdicts are listed above. Proof C is `BLOCKED`, not `PASS` and not operator-deferred. No Phase 2 artifact exists. The matrix draft below is section 8 item 3 content, is not ratified and opens no Phase 2 |
| `PE-FLOW-03` | `P1` | not-deferrable | `MET` | Proof E run 5 `PASS`, synthetic model, with L1-L7 recorded. Its evidence gaps are counted under `PE-AUTH-02` and `PE-EVIDENCE-01` |
| `PE-FLOW-04` | `P1` | not-deferrable | `UNSATISFIED` (Stage fail-closed finding) | Proof D run 3 was `FAIL` under PE-1.4 (`8179feb1`), with the route "charter change control". That change was not enacted. Run 4 (`36f65975`) asked the same section 6.6 question under the same version PE-1.4, on an operator instruction that kept the thresholds unchanged. The next version bump, PE-1.5 (`d31d7b42`), came after run 4 and was limited to section 6.7. Section 3.4 carries run 4's standing forward, but it does not rule on this row. As written, "no second attempt of a failed proof question exists without a charter version bump" is not met. The other re-runs do not engage the row: C run 2 and D run 2 each followed a version bump; A, B and E re-ran after `BLOCKED`; F run 2 and G run 2 corrected defects before evidence existed, or strengthened evidence, without a `FAIL`. Needs OD-2 |

### INTERFACE

| Row | Sev | Deferral | Status | Evidence |
|---|---|---|---|---|
| `PE-INTERFACE-01` | `P1` | deferred-to-implementation-matrix (binding now) | `DEFERRED` (binding part met) | The Proof G helper has no adapter parameter (runs 1 and 2). The row is carried as IM-06 in the draft |
| `PE-INTERFACE-02` | `P1` | not-deferrable | `MET-COND` | Proof B run 3: 5 of 5 genuine verdicts accepted, 20 of 20 impostors rejected. It depends on the spool and CLI-transport interpretations. Needs OD-3 |
| `PE-INTERFACE-03` | `P1` | not-deferrable | `UNSATISFIED` | The evidence is Proof C, and C run 2 is `BLOCKED`. The static observations do not satisfy the row |

### SAFETY

| Row | Sev | Deferral | Status | Evidence |
|---|---|---|---|---|
| `PE-SAFETY-01` | `P1` | not-deferrable; Linux half gate | `WIN-MET / LINUX-PENDING` | G run 2: 22 of 22 lexical cases, 0 candidate resolves |
| `PE-SAFETY-02` | `P1` | Windows symlink sub-case operator-deferrable; junction not-deferrable; Linux half gate | `WIN-MET / LINUX-PENDING` | All junction and symlink cases executed on Windows (the host had symlink privilege), so no deferral is needed |
| `PE-SAFETY-03` | `P1` | not-deferrable; Linux half gate | `WIN-MET / LINUX-PENDING` | Both roots, case-insensitive Windows root comparison, and `.autoharness/` reads |
| `PE-SAFETY-04` | `P1` | not-deferrable; Linux half gate | `WIN-MET / LINUX-PENDING` | Proof D half: D run 4 (PE-1.4; run 2 is the historical PE-1.2 `PASS` the row text names). It is subject to the `PE-FLOW-04` finding. G half: Windows met, with the raw request at most cap+1 |
| `PE-SAFETY-05` | `P1` | not-deferrable; Linux half gate | `WIN-MET / LINUX-PENDING` | B run 3: no case returns success with missing or truncated content (subject to OD-3). G Windows: no silent truncation |
| `PE-SAFETY-06` | `P2-critical` | not-deferrable | `MET` | A text audit finds only non-claims (the D run 1, B runs 1 and 2, and G artifacts). This report and its draft make no race, TOCTOU or hardlink-alias claim |
| `PE-SAFETY-07` | `P2-critical` | not-deferrable; Linux half gate | `WIN-MET / LINUX-PENDING` | Reserved device names and non-regular targets are rejected on Windows. G31 (FIFO) is Linux-only and unexecuted |

### DATA

| Row | Sev | Deferral | Status | Evidence |
|---|---|---|---|---|
| `PE-DATA-01` | `P1` | not-deferrable | `UNSATISFIED` | Proof C run 2 `BLOCKED` |
| `PE-DATA-02` | `P1` | not-deferrable | `UNSATISFIED` | Proof C run 2 `BLOCKED` |
| `PE-DATA-03` | `P1` | not-deferrable | `MET-COND` | D run 4: `C_max` 202, margin 54, byte non-guarantee, `UNRESOLVED / 2` at every stage, all nine controls caught. Its admissibility depends on OD-2 (`PE-FLOW-04`) |
| `PE-DATA-04` | `P1` | not-deferrable | `MET` | F run 2: the staged digest equals the HEAD digest, `54ad053a036e5c9f25164302db6c2498ce5d67609e16dc924e8d11ba03a71468`. Its handoff gaps are counted under `PE-AUTH-02` and `PE-EVIDENCE-01` |

### TASK

| Row | Sev | Deferral | Status | Evidence |
|---|---|---|---|---|
| `PE-TASK-01` | `P1` | not-deferrable | `MET` | Every section 6.2 bound is at most 90 minutes. Every counted run's recorded elapsed time is within its bound (C run 2 about 58 of 75 minutes on conservative accounting) |
| `PE-TASK-02` | `P1` | deferred-to-implementation-matrix | `DEFERRED` | Carried as IM-11 |
| `PE-TASK-03` | `P0` | not-deferrable | `MET` | No backlog item was created from the proofs. The only `.backlogit/` change since `082df7b2` is the two checkpoint files in `5bcb00e5` |

### EVIDENCE

| Row | Sev | Deferral | Status | Evidence |
|---|---|---|---|---|
| `PE-EVIDENCE-01` | `P1` | not-deferrable | `OPEN-EVIDENCE` | Met for A run 5 (after its addendum), B run 3 and D run 4 (transport unnamed, stderr by hash). Not established for C run 2 (no normalized failure messages or per-execution fixture hashes), E run 5 (no Ship elapsed time, refresh stdout hash prefix only, no refresh stderr), F run 2 (no `.backlogit` ignored before and after in the safety statement) or G run 2 (no bounded refresh output). Needs OD-4 |
| `PE-EVIDENCE-02` | `P1` | Windows not-deferrable; Linux half gate | `WIN-MET / LINUX-PENDING` | `Windows` on NTFS, native. Linux `PENDING`, never `PASS`. Carried as IM-01 |
| `PE-EVIDENCE-03` | `P1` | not-deferrable | `MET-COND` | A run 5: runner half from Ship's actual execution, policy half from Stage's static comparison, no actor or gate-evidence claim. It depends on the R2, file-bound and spool interpretations. Needs OD-3 |
| `PE-EVIDENCE-04` | `P2` | not-deferrable | `MET` | No combined Stage or Ship session was used. Each proof has its own verdict block and time record |
| `PE-EVIDENCE-05` | `P2` | not-deferrable | `MET` | Every reported-run artifact declares the engram, intercom, graphtor-docs and backlogit states, or declares them not probed |

### ACTIVATE

| Row | Sev | Deferral | Status | Evidence |
|---|---|---|---|---|
| `PE-ACTIVATE-01` | `P0` | not-deferrable | `MET` | Section PE-ACTIVATE-01 Recheck above |
| `PE-ACTIVATE-02` | `P1` | deferred-to-implementation-matrix | `DEFERRED` | Carried as IM-08 |
| `PE-ACTIVATE-03` | `P1` | not-deferrable | `MET` | No proof artifact asserts publication or claim readiness. This report states both as not ready |

### Counts

| Status | Rows | IDs |
|---|---|---|
| `MET` | 18 | AUTH-03, AUTH-04, SCOPE-01 to 06, FLOW-01, FLOW-03, SAFETY-06, DATA-04, TASK-01, TASK-03, EVIDENCE-04, EVIDENCE-05, ACTIVATE-01, ACTIVATE-03 |
| `MET-COND` | 5 | AUTH-01, SCOPE-07, INTERFACE-02, DATA-03, EVIDENCE-03 |
| `OPEN-EVIDENCE` | 2 | AUTH-02, EVIDENCE-01 |
| `UNSATISFIED` | 5 | FLOW-02 (`P0`), FLOW-04, INTERFACE-03, DATA-01, DATA-02 |
| `WIN-MET / LINUX-PENDING` | 7 | SAFETY-01, 02, 03, 04, 05, 07, EVIDENCE-02 |
| `DEFERRED` | 3 | INTERFACE-01, TASK-02, ACTIVATE-02 |
| **Total** | **40** | 36 not-deferrable, 1 mixed (SAFETY-02) and 3 deferred |

Of the 37 not-deferrable or mixed rows, 18 are cleanly `MET`. The 19 others
are 5 `MET-COND`, 2 `OPEN-EVIDENCE`, 5 `UNSATISFIED` and 7 with the Linux half
`PENDING`. Stage does not count a `MET-COND` row as met, and does not treat
any static observation from blocked Proof C as meeting a row.

## Proof C Blocked Path and Options

**What is recorded.** Run 2 (`309ab0e2`) ran the same command six times, with
native exits `1, 1, 1, 1, 1, 0`. The same-error circuit breaker
(`.github/instructions/circuit-breaker.instructions.md`) cannot be shown
to have allowed executions 5 and 6. Only execution 1 has different stable
evidence. Executions 2 to 5 have no normalized failure messages and no
per-execution fixture hashes. A tool-wrapper spool of an early snapshot to host
Temp also cannot be shown to fall outside the section 6.1 bounded-output
sentence. The final exit 0 cannot be used on its own. **This report takes no
`PASS` from the final exit 0, does not bypass the breaker, and does not re-run
the tripped script.**

**Options, in the order Stage recommends. The operator chooses.**

| Option | What happens | Execution? | What it can change |
|---|---|---|---|
| C-1. Read-only evidence provenance (recommended first) | Ship gives, from evidence it **already captured**: the normalized failure message for each of executions 1 to 5 (the `fixture_failures` entries, or the first stderr line for execution 1); the fixture SHA-256 in effect at each execution; the command that spooled, its output byte length, and whether it was a section 6.1 projection or checkpoint read (never the spool content). Stage then writes an addendum or a new findings artifact. The run 2 artifact stays unchanged | None. Inspecting captured evidence is not another attempt | If each step shows a genuinely different error, ground 1 clears. If the spool is shown to be outside the rule, ground 2 clears. Only then could Stage reconsider admissibility of the existing execution 6 evidence against section 6.5 |
| C-2. Operator ruling on the spill | The operator rules whether section 6.1's bounded-output sentence covers automatic host-wrapper spools, and the ruling is recorded. A standing ruling also settles the A and B spool interpretations (OD-3) | None | Ground 2 only. Ground 1 still needs C-1 or C-3 |
| C-3. Fresh Proof C run 3, only on explicit operator authorization | Needed because the breaker tripped. A new scratch directory, fresh 75-minute and 2-file bounds, the final fixture frozen and hashed before the first execution, one counted execution, all output captured in process with a console excerpt of at most 2 KiB, and normalized failure messages captured for any non-zero exit. It is a new operation, not a continuation of the tripped run 2 chain | Yes, by Ship, verification-only, after operator authorization | It can produce an admissible run 3 verdict. It is not a `PE-FLOW-04` re-run, because run 2 is `BLOCKED`, not `FAIL` |
| C-4. Operator deferral of Proof C (not recommended) | Section 8 and `PE-FLOW-02` allow an operator-deferred verdict | None | It would meet `PE-FLOW-02`'s wording. It would **not** meet `PE-INTERFACE-03`, `PE-DATA-01` or `PE-DATA-02`, which are `not-deferrable`. Only a charter version bump could change that, and Stage does not recommend one |

## Render Mismatch Follow-Up (post-proof release unit; not fixed here)

* **Observation (Proof C run 2, reproduced read-only by Stage).** The
  installed `.github/skills/harness-architect/SKILL.md` (7501 B, raw SHA-256
  `39089629cd115f80f801c61b37040e2cf5a937940b2ae16f929f184647ba9f36`) matches
  its manifest checksum. But the template rendered from the top-level
  `variables_used` mapping (5 of 5 placeholders resolved) differs first at
  byte 4994. The only difference is a line reflow of the Step 5.2 paragraph,
  and the two texts are equal after whitespace normalization.
* **Why it matters.** A byte-exact render-parity resolver would classify this
  one supported surface as `RENDER_MISMATCH`, then `STALE`, then
  `NO_HARNESS / 1` at HEAD, even though its checksum matches.
* **Follow-up (not done here).** Reconcile the bytes in its own
  operator-approved release unit **after** proof exit. Either reflow the
  template, or re-render the installed file and refresh its manifest checksum
  with the Proof F raw staged-blob procedure. Do not loosen the comparison
  (`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`).
  It must land before any resolver that compares renders byte for byte runs
  against this surface (draft row IM-10). Section 4.3 forbids the change
  during proofs. The operator's scope for this session forbids backlog
  changes, so Stage created no stash entry. Capturing one is OD-7.

## Implementation Matrix Draft (section 8 items 3 and 4; NOT RATIFIED)

This is a **draft**. It is not ratified, it authorizes no implementation, plan,
harvest or review epoch, and every row may change at ratification. It is
ratified only by the operator, after this report and before any new review
epoch (section 3). It cannot be ratified while the blocking rows in the audit
stay open.

| Draft ID | Requirement (draft) | Source | Proposed severity | Proposed deferral |
|---|---|---|---|---|
| IM-01 | **Actual Linux-native execution** of the full Proof G case set (including G31 FIFO and the Linux symlink cases), in CI on a Linux runner with a Linux-native filesystem. It carries the Linux halves of `PE-SAFETY-01` to `05` and `07` and `PE-EVIDENCE-02`. Mocks, simulation, a Windows volume mounted into Linux, and Windows evidence never satisfy it. No lifecycle release unit that depends on this containment ships without it | Section 6.9; `linux-execution-gate`; Proof G | `P1` | **`not-deferrable`, non-waivable execution and release gate.** No one may waive it |
| IM-02 | Cross-platform acceptance for every row that needs both hosts. **Status now: UNMET** | Section 5 platform mandate; section 8 item 4 | `P1` | `not-deferrable`; met only when IM-01 passes |
| IM-03 | The SurfaceSpec reason taxonomy and result schema are closed and schema-parity-complete against the section 6.5 governing reason set. **Not proven.** The Stage candidate is still a proposal | `PE-INTERFACE-03`, `PE-DATA-01`, `PE-DATA-02`; Proof C | `P1` | `not-deferrable`; cannot be ratified until Proof C has an admissible verdict |
| IM-04 | The read budget is admitted `1..48`, `max_files=256`, with no byte-fit claim, and `UNRESOLVED / 2` at every read and recheck stage. Also test multi-error first-code selection, byte-code applicability at absent candidates, and precedence without short-circuit | `PE-DATA-03`; decision `286aa4af`; D run 4 carried limitations | `P1` | `not-deferrable`; subject to OD-2 |
| IM-05 | Bounded raw reads loop until EOF or cap+1, so a short read never becomes silent truncation. The byte bound is measured the same way on Windows and Linux | `PE-SAFETY-04`, `05`; G run 2 design note | `P1` | `not-deferrable` |
| IM-06 | No public or caller-supplied traversal adapter. Any test seam is private | `PE-INTERFACE-01` | `P1` | `not-deferrable` |
| IM-07 | Ship consumes a validated document, not a process status. Resolve CR-B1 to CR-B5, including float-form `exit_code` being accepted (CR-B3) and the deep-nesting `RecursionError` (CR-B4) | `PE-INTERFACE-02`; Proof B | `P1` | `not-deferrable` |
| IM-08 | The activation of template, mirror and manifest checksum is one task and one commit. The replacement wording for both PE-1.5 template spans meets the section 6.7 post-activation restore contract, keeps a session-start invocation of the recovery machine (E L6) and keeps the C1-C6 wiring (E O4) | `PE-ACTIVATE-02`; `PE-FLOW-03`; Proof E | `P1` | `not-deferrable` at implementation |
| IM-09 | The post-activation recovery fixture closes E L1 (rendered mirror form), L3 (open event vocabulary that fails closed), L4 (unexercised branches) and L5 | Proof E run 5 | `P2` | Proposed `operator-deferrable` |
| IM-10 | Before any byte-exact render-parity resolver runs against `harness-architect` at HEAD, the render mismatch is reconciled in its own release unit (section Render Mismatch Follow-Up) | Proof C run 2 item 5 | `P1` | `not-deferrable` for that resolver |
| IM-11 | Each future shipment holds at most 6 tasks and 8 hours, is independently valuable and carries two-axis sizing. An overrun escalates per P-013.6 | `PE-TASK-02` | `P1` | `not-deferrable` at harvest |
| IM-12 | Manifest checksums come from raw staged-blob bytes: a Python subprocess with binary capture of `:<path>`, `git add --renormalize` when an `eol=lf` pin is added, and no redirect or PowerShell text capture | `PE-DATA-04`; Proof F | `P1` | `not-deferrable` |
| IM-13 | P-004 red evidence uses the exact canonical command with per-test marker attribution, read under R2 if the operator ratifies it (OD-3) | `PE-EVIDENCE-03`; Proof A | `P1` | `not-deferrable` |
| IM-14 | No artifact claims race, TOCTOU or hardlink-alias resistance | `PE-SAFETY-06` | `P2-critical` | `not-deferrable` |
| IM-15 | Publication, execution and claim/closure gates stay distinct. A test or proof `PASS` confers no claim authority | `PE-ACTIVATE-03`; section 9 | `P1` | `not-deferrable` |

## Open Operator Decisions (section 8 item 5)

The charter decisions stay open. Nothing here selects or approves them.

| ID | Decision | Status |
|---|---|---|
| C2 | Release-unit split | Bounded proposal, **pending operator ratification** (Phase 2) |
| C3 | Migration and the fate of `187-S`: retire or re-charter, never patch | **Pending operator ratification** (Phase 2). `187-S` stays `queued` and frozen until then |
| C4 | `P2` publication policy, reviewer lead and routing | **Pending operator ratification** (Phase 4). No `model_routing.anchor_review` route is selected here |

New decisions this report routes to the operator:

| ID | Decision needed | Rows affected |
|---|---|---|
| OD-1 | Choose the Proof C path: C-1 first (recommended), C-2, C-3 (explicit authorization of a fresh run), or C-4 | `PE-FLOW-02`, `PE-INTERFACE-03`, `PE-DATA-01`, `PE-DATA-02` |
| OD-2 | Rule on Proof D run 4 under `PE-FLOW-04`. Either record, by an operator-approved charter version, that run 4 is admissible despite following run 3's PE-1.4 `FAIL`, or keep run 4 as history and order a fresh Proof D run under PE-1.5 or later | `PE-FLOW-04`, `PE-DATA-03`, `PE-SAFETY-04` |
| OD-3 | Ratify or veto the Stage interpretations: the A R2 reading; the A and G file-bound counts; the A, B and C spool classification; the direct CLI refresh transport. A veto changes the named verdicts as each artifact states | `PE-SCOPE-07`, `PE-INTERFACE-02`, `PE-EVIDENCE-03`, `PE-AUTH-02` |
| OD-4 | Close the evidence gaps, either by Ship's read-only transcription of evidence it already captured (as the Proof A addendum did), or by explicit operator acceptance of each gap | `PE-AUTH-02`, `PE-EVIDENCE-01` |
| OD-5 | Confirm `89b0db6d` (config routing, not recorded in the charter) as an operator setup commit outside the proof actors | `PE-AUTH-01` |
| OD-6 | Approve or withhold cleanup of the 14 scratch directories under `.proof-scratch/` (A run 4 and 5; B runs 1 to 3; C runs 1 and 2; D runs 3 and 4; E runs 4 and 5; F; G runs 1 and 2). Ship alone removes them, under the section 6.1 rule | Hygiene only |
| OD-7 | Authorize capture of the render-mismatch follow-up as a stash entry or release unit after proof exit | IM-10 |
| OD-8 | Confirm the reading of section 8 against section 7.1. Stage reads it as: proof entry exits when section 8 is met, and `not-deferrable` rows that do not hold block ratification and Phase 2. They do not un-exit proof entry | Every blocking row |

## Publication and Claim Readiness

* **Publication readiness: not ready.** The verdict manifest records
  `publication_eligible: false`, `verdict: FAIL` and
  `attempt_12_authorized: false`. The 29 local proof-phase commits are
  unpushed. Pushing or publishing them is an operator action, and publishing
  Stage artifacts confers no claim authority
  (`docs/decisions/2026-09-20-pr457-bounded-review-convergence-deliberation.md`).
  Stage did not check the live PR #457 state, because this report did not need
  it.
* **Claim readiness: not ready.** `187-S` is `queued`, has no `harness-ready`
  label, and is frozen under C3. No proof `PASS` and no part of this report
  confers claim, closure, P-004 red or `harness-ready` authority
  (`PE-ACTIVATE-03`).
* **Implementation readiness: not ready.** See Bottom Line.

## Next Actions (plain language)

1. **Proof C first.** Ask Ship for the evidence it already has on Proof C run
   2: the error message behind each of the five failed executions, the fixture
   hash each one used, and which command spilled output to Temp and how large
   it was. Nothing is re-run. If that evidence does not clear both grounds,
   the operator decides whether to authorize a fresh, single-execution Proof C
   run 3.
2. **Proof D.** The operator rules on whether run 4 counts, since it
   followed a `FAIL` without a charter version bump. The alternative is a fresh
   Proof D run under the current charter.
3. **Stage interpretations.** The operator approves or vetoes the recorded
   Stage readings (R2, the file-bound counts, the spool classification and the
   CLI refresh transport).
4. **Evidence gaps.** Ship transcribes the missing D, E, F and G handoff fields
   from what it already captured, or the operator accepts each gap
   explicitly.
5. **Only then** can Stage bring the implementation matrix draft to the
   operator for ratification, together with C2, C3 and C4. Even after
   ratification, Linux-native execution (IM-01) must pass before any release
   unit that depends on containment ships.
6. **Until then:** `187-S` stays queued and frozen. There is no plan, harvest,
   review attempt, activation, claim, push or pull request. The
   harness-architect render fix waits for its own release unit after proof
   exit.

## References

* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (PE-1.5, `d31d7b42`; sections 3.1 to 3.4, 4, 5, 6.1, 6.2, 6.5, 6.7, 6.9, 7, 8, 9 and 10)
* Proof A: `docs/decisions/2026-09-24-p004-red-runner-proof-a-run5-spike.md`; history `docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md`
* Proof B: `docs/decisions/2026-09-24-cli-authenticity-proof-b-run3-spike.md`; history `docs/decisions/2026-09-24-cli-authenticity-proof-b-spike.md`, `docs/decisions/2026-09-24-cli-authenticity-proof-b-run2-spike.md`
* Proof C: `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run2-spike.md`; history `docs/decisions/2026-09-24-surface-taxonomy-proof-c-spike.md`
* Proof D: `docs/decisions/2026-09-24-read-budget-proof-d-run4-spike.md`; history `docs/decisions/2026-09-23-read-budget-proof-d-spike.md`, `docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md`, `docs/decisions/2026-09-24-read-budget-proof-d-run3-spike.md`
* Proof E: `docs/decisions/2026-09-24-ship-activation-proof-e-run5-spike.md`; history `docs/decisions/2026-09-24-ship-activation-proof-e-spike.md`, `docs/decisions/2026-09-24-ship-activation-proof-e-run2-spike.md`, `docs/decisions/2026-09-24-ship-activation-proof-e-run3-spike.md`, `docs/decisions/2026-09-24-ship-activation-proof-e-run4-spike.md`
* Proof F: `docs/decisions/2026-09-24-staged-blob-checksum-proof-f-run2-spike.md`; history `docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md`
* Proof G: `docs/decisions/2026-09-24-ordinary-path-containment-proof-g-spike.md` (run 2 correction addendum included)
* Decision: `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`
* Parent decision: `docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md`
* Related: `docs/decisions/2026-09-20-pr457-bounded-review-convergence-deliberation.md`; `docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md`
* Rules: `.github/instructions/circuit-breaker.instructions.md`; `.github/policies/workflow-policies.md`; `.github/instructions/constitution.instructions.md`
* Learning: `docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`
