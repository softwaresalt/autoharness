---
title: "Lifecycle proof-exit operator rulings 4 (2026-09-25): OD-11 list ratified; IM-17 closed with no revision; IM-03 finality now depends only on IM-16; 30 met, 0 conditional; OD-10 architecture decision still open"
source: "docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-4.md"
doc_type: decision
description: "Fourth Stage addendum to the PE-1.7 proof-exit refresh (a04dea18), recording the operator ruling given at 2026-09-25T17:55:28-07:00 on OD-11, the one decision left open by the third rulings record (347771bd) other than the OD-10 architecture decision. Ruling, verbatim: 'OD-11: List ratified'. The Orchestrator had shown the operator the full 47-code section 6.5 Stage candidate (classes 1, 1b and 2 to 8, with codes and meanings) and explained that OD-11 asks to ratify four items together: (a) the 39 codes outside the 8-code governing set, (b) the order within classes 2, 3 and 5 to 7, (c) the tie-break between declaration issues and (d) the declarations item shape {member_id, surface_id} with additionalProperties false. Because the four items were presented together as 'the list', the Orchestrator reads 'List ratified' as ratifying the section 6.5 candidate as proven by Proof C run 4 (4c6e2701), all four items, hash-pinned to charter commit 52c985cb (PE-1.4), which carries the candidate; the same block is byte-identical in the current charter e65887d8 (PE-1.7). This is the Orchestrator's reading and the operator may narrow it. Consequences: IM-17 becomes decided and closed; there is no revision, so no Proof C re-run is needed. IM-03's finality now depends only on IM-16 (the OD-10 architecture decision plus tests of both orders). No row status changes. Totals unchanged: 30 MET, 0 MET-COND, 0 OPEN-EVIDENCE, 0 UNSATISFIED, 7 Windows-met with Linux PENDING, 3 deferred (40). The only open operator decision on the proof-exit list is the OD-10 architecture decision. This record authorizes no plan, harvest, review epoch, activation, claim, retirement execution, push or pull request."
date: 2026-09-25
created: 2026-09-25
status: recorded
decision_status: partially-decided
deciders: operator
recorded_by: Stage
operator_rulings_at: "2026-09-25T17:55:28-07:00"
operator_rulings_relayed_by: Orchestrator
docline:
  type: decision
  date: 2026-09-25
  conclusion: "od-11-list-ratified-im-17-closed-im-03-finality-on-im-16-only-30-met-0-met-cond-od-10-architecture-decision-open"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "proof-exit"
    - "operator-rulings"
    - "acceptance-matrix"
    - "implementation-matrix-ratification"
    - "reason-taxonomy"
    - "ship-lifecycle"
    - "linux-execution-gate"
artifact_class: proof-exit-report-addendum
supersedes: none
relates:
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md, commit: a04dea18, relation: "records a ruling on its open decision OD-11 (IM-17)"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings.md, commit: 928bf3ff, relation: "first addendum"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-2.md, commit: 2634bac2, relation: "second addendum; matrix ratified with the IM-17 carve-out"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-3.md, commit: 347771bd, relation: "third addendum; continues its open-decision list"}
  - {path: docs/decisions/2026-09-24-surface-taxonomy-proof-c-run4-spike.md, commit: 4c6e2701, relation: "Proof C run 4 PASS; the proof behind the ratified candidate"}
  - {path: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md, commit: 52c985cb, relation: "charter PE-1.4; section 6.5 Stage candidate, hash pin for this ratification"}
  - {path: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md, commit: e65887d8, relation: "charter PE-1.7; same candidate block, byte-identical"}
records_rulings_on: [docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md, docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-3.md]
records_rulings_on_commits: [a04dea18, 347771bd]
prior_reports_edited: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.7"
charter_commit: e65887d8
charter_edited: false
matrix_id: PE-1.7
head_at_authoring: 347771bd914f9967a5d2bc1f4c2cb8a9127fe204
branch: chore/stage-176-s-workflow-defects
worktrees: 1
rulings:
  OD-11: {ruling: "list ratified", operator_text: "OD-11: List ratified", reading: "ratifies the section 6.5 Stage candidate as proven by Proof C run 4, items (a) to (d)", reading_by: Orchestrator, operator_may_narrow: true, revision: none, proof_c_rerun_needed: false}
ratified_candidate:
  source_commit: 52c985cb25fac3026e900a5bc386e522f6f3517c
  source_charter_version: "1.4"
  source_lines: "717-749 at 52c985cb; 1222-1254 at e65887d8"
  candidate_block_sha256_lf_joined: 64c41cd150dde7273506e0a2b179a04187bb80139216b14b5fe898cb896b6847
  governing_block_sha256_lf_joined: cba91a303c24edf4b88a0a907d5caf8ca6c695a33c2b5cd256e1b7cba7f9f0cf
  identical_at_commits: [52c985cb, e65887d8]
  proven_by: {commit: 4c6e2701, verdict: PASS, charter_version: "1.6", fixture_sha256: {c3_verify.py: f7bb864376fd39d8a769fa0dc8f8b347762d847e3948715decfcba96e19392e3, c3_schema.json: a659c4ad7e3fc91517c5348449703c2667c3ad33aa8d75de41d427749831b1d3}}
  items: {a: "39 codes outside the 8-code governing set, with their class, state and exit", b: "order within classes 2, 3 and 5 to 7", c: "tie-break between declaration issues (class 3 listed order)", d: "declarations item shape {member_id, surface_id}, additionalProperties false"}
  codes_total: 47
  codes_governing: 8
  codes_ratified_here: 39
  state_split: {HARNESS_READY: 2, NO_HARNESS: 4, UNRESOLVED: 41}
pending_confirmation: []
stash_entry_created: false
backlog_item_created: false
proof_verdicts_changed: false
matrix_row_counts:
  total: 40
  met: 30
  met_conditional: 0
  open_evidence: 0
  unsatisfied: 0
  windows_met_linux_pending: 7
  deferred_to_implementation_matrix: 3
  not_deferrable_or_mixed: 37
  not_deferrable_met_clean: 30
rows_changed: []
rows_condition_changed_status_unchanged: []
met_conditional_rows: []
open_evidence_rows: []
unsatisfied_rows: []
implementation_matrix_status: ratified-by-operator-with-carve-outs
im_rows_ratified: [IM-01, IM-02, IM-04, IM-05, IM-06, IM-07, IM-08, IM-09, IM-10, IM-11, IM-12, IM-13, IM-14, IM-15]
im_rows_ratified_finality_open: [IM-03]
im_rows_decided_closed: [IM-17]
im_rows_not_ratified: [IM-16]
im_16_route: "architecture decision (OD-10); not yet made"
im_03_finality_blocked_by: [IM-16]
open_operator_decisions: [OD-10-architecture-decision]
resolved_operator_decisions: {OD-1: "superseded (4c6e2701)", OD-2: "resolved, Option A (e65887d8)", OD-3: "approved (928bf3ff)", OD-4: "gaps accepted, veto window closed (347771bd)", OD-5: "confirmed (928bf3ff)", OD-6: "withhold cleanup until the work ships (2634bac2)", OD-7: "yes; stash 9144435A (2634bac2)", OD-8: "confirmed (2634bac2)", OD-9: "accepted (928bf3ff)", OD-10: "routed to an architecture decision (347771bd); the decision itself is open", OD-11: "list ratified, items (a) to (d), Orchestrator reading (this record)", OD-12: "yes, answer 1 (347771bd)", C2: "approved (2634bac2)", C3: "retire 187-S, execution deferred to Phase 2 (2634bac2)", C4: "reviewer lead gpt-6-sol (2634bac2); only matrix-critical P2 blocks (347771bd)"}
cross_platform_acceptance: unmet
linux_gate: "not-deferrable, non-waivable execution and release gate (section 6.9); Windows evidence never satisfies it"
phase_2_ready: "gating decisions answered; starts only on Orchestrator routing"
phase_2_blocked_by: []
resolver_contract_freeze_blocked_by: [OD-10-architecture-decision, OD-10-tests-of-both-orders]
implementation_ready: false
feature_id: 181-F
shipment_id: 187-S
shipment_status: "queued and frozen; retirement approved (C3) but not executed; not read or touched by this record"
shipment_claim_ready: false
publication_eligible: false
publication_ready: false
claim_ready: false
plan_changed: false
ship_surface_changed: false
config_changed: false
proof_run_performed: false
authorizes: none
stage_model_route: "claude-opus-5.5/anthropic/high requested and configured; unverified by Stage (ROUTING_DEGRADED: not self-verifiable)"
---

# Lifecycle proof-exit operator rulings 4 (2026-09-25)

## Bottom Line

| Question | Answer |
|---|---|
| What did the operator decide? | OD-11: **"List ratified"** |
| How is that read? | As ratifying the **section 6.5 Stage candidate as proven by Proof C run 4** (`4c6e2701`): all four items (a) to (d) below, hash-pinned to charter commit `52c985cb` (PE-1.4). This is **the Orchestrator's reading**, because the operator was shown all four items together as "the list". **The operator may narrow it** |
| What changes? | **IM-17 is decided and closed.** There is no revision, so **no Proof C re-run** is needed. **IM-03's finality now depends only on IM-16** |
| What changes in the rows? | **No row status changes.** OD-11 conditioned IM-17 and IM-03, not a proof-entry row |
| Counts | Unchanged: **30 `MET`**, 0 `MET-COND`, 0 `OPEN-EVIDENCE`, 0 `UNSATISFIED`, 7 Windows-met with Linux `PENDING`, 3 deferred (40) |
| What is still open? | Among operator decisions, only **the OD-10 architecture decision** (routed in `347771bd`, not yet made) |
| What does this authorize? | **Nothing.** See [What This Record Does Not Do](#what-this-record-does-not-do) |

## Scope and Method

* **Actor.** Stage, directed by the Orchestrator. Stage wrote this one file.
  It ran no proof, fixture, build, test suite or linter other than a Markdown
  lint of this file, and no index refresh. It did not read or touch `187-S`.
  It made no push, branch, worktree or pull request, and did not touch any
  `git stash` entry. The Proof C run 4 scratch pair was read read-only, to
  confirm hashes and the precedence and `declarations` shape it encodes.
* **Nothing earlier is edited.** The charter (`52c985cb` to `e65887d8`), the
  refresh report (`a04dea18`), the three earlier rulings records
  (`928bf3ff`, `2634bac2`, `347771bd`), the Proof C findings and the scratch
  evidence stay as committed or as kept under OD-6.
* **Fail-closed rule** (as in the earlier addenda). A row changes status only
  if a ruling recorded here closes its sole remaining condition. A reading
  that the operator may narrow is disclosed as a reading.
* **Session state.** backlogit MCP `get_version` (update check skipped)
  returned `1.10.1-0.20260823032255-b07729386a31+dirty` (`TOOL_OK`). Index
  sync was not run, on purpose, as in the earlier addenda
  (`INDEX_SYNC_SKIPPED`). Checkpoint recovery: `list_checkpoints` with
  `consumer_id: stage` and no status or agent filter returned 67 records, all
  `stage`/`resolved`, with `needs_quarantine` 0 and `quarantined` 0. That is
  a normal zero-candidate startup. The host tool wrapper again spooled that
  read-only output (74.4 KB) to OS Temp outside the working directory; Stage
  read the spool read-only. Engram, intercom and graphtor-docs expose no
  tools here (`ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`,
  `GRAPHTOR_UNAVAILABLE`). The Orchestrator relays to the operator.

## Operator Ruling (verbatim)

Given at **2026-09-25T17:55:28-07:00** and relayed by the Orchestrator.

> OD-11: List ratified

OD-11 is defined in the refresh report's "Open Operator Decisions" section
(`a04dea18`): "Ratify, revise or reject the section 6.5 candidate
proposals". Its implementation-matrix row is IM-17.

### What the Operator Was Shown

After `347771bd`, the Orchestrator presented the full 47-code section 6.5
Stage candidate to the operator: classes 1, 1b and 2 to 8, with each code and
its meaning. It explained that OD-11 asks the operator to ratify four items
that no earlier source settles (charter section 6.5, "Not ratified by any
source, and so proposals only"):

| Item | What is ratified | Where it is fixed |
|---|---|---|
| (a) | **The 39 codes outside the 8-code governing set**, each with the class, state and exit listed for it | Candidate table, classes 2, 3 and 5 to 7 |
| (b) | **The order within classes 2, 3 and 5 to 7** (the listed order is the precedence) | Same table |
| (c) | **The tie-break between declaration issues**: when more than one class 3 issue is present, the code listed first in class 3 is reported (`FEATURE_DECLARES_SURFACE`, `DECLARATION_MISSING`, `DECLARATION_MALFORMED`, `DECLARATION_DUPLICATE`, `DECLARATION_MIXED`, `SURFACE_UNSUPPORTED`) | Class 3 order; run 4's oracle ranks by class, then by listed position |
| (d) | **The `declarations` item shape** `{member_id, surface_id}`, with `additionalProperties: false` (both keys required, both strings). The list stays sorted by task ID, as plan revision 12 already fixes | Section 6.5 (run 1's Ship assumption, carried as a labelled candidate); `c3_schema.json` in run 4 |

The 8 governing codes (the three class 1b read-limit codes,
`INPUT_CHANGED_DURING_RESOLUTION`, `SURFACE_UNSUPPORTED`,
`MEMBERS_TOO_MANY`, `NO_SURFACES_REQUIRED` and `ALL_SURFACES_PRESENT`) and
the class order 1, 1b, 2 to 8 were already fixed by the charter. Class 1b
keeps its first-occurrence rule, with no fixed order among its three codes.
Nothing here changes those.

### How the Ruling Is Read

**Reading recorded here (the Orchestrator's).** "List ratified" ratifies the
section 6.5 candidate as proven by Proof C run 4, that is, **all four items
(a) to (d) together**. The basis is that the operator was shown the four
items together as "the list" and gave one answer. The operator did not
separately name any item, and **may narrow the reading**. If the operator
narrows it, IM-17 reopens for the items left out, and IM-03's finality again
depends on IM-17 for those items.

**Why "as proven" matters.** The ratified list is the one run 4 proved, not
a new one. So the ratification is a decision with **no revision**, and
IM-17's re-proof clause ("Any revision is re-proven with the Proof C
method") is not triggered.

## Hash Pin

The charter says "The commit of this charter version is the durable,
hash-pinned candidate". The candidate was introduced in PE-1.4.

| Pin | Value |
|---|---|
| Charter commit that carries the candidate | **`52c985cb25fac3026e900a5bc386e522f6f3517c`** (PE-1.4), section 6.5 "Stage candidate" block, lines 717 to 749 |
| Same block in the current charter | `e65887d8267ea9a3f0612a2f6c69e4ba39706add` (PE-1.7), lines 1222 to 1254. PE-1.5, 1.6 and 1.7 did not change it |
| Candidate block, SHA-256 of its lines joined with LF | `64c41cd150dde7273506e0a2b179a04187bb80139216b14b5fe898cb896b6847`, the same at both commits |
| Governing reason set block, same method | `cba91a303c24edf4b88a0a907d5caf8ca6c695a33c2b5cd256e1b7cba7f9f0cf`, the same at both commits |
| Proof | Proof C run 4 `PASS` under PE-1.6 (`4c6e2701`). It ran the frozen pair `c3_verify.py` (SHA-256 `f7bb8643...19392e3`) and `c3_schema.json` (SHA-256 `a659c4ad...31b1d3`), re-hashed read-only for this record and unchanged. Its report records `"charter_version":"PE-1.5; Proof C candidate remains PE-1.4"` |
| What run 4 proved for the list | 47 of 47 codes reachable, 2162 ordered precedence pairs (47 × 46) in a strict total order apart from class 1b, 47 schema and 47 surface branches, 9 of 9 mutants rejected, state split 2 / 4 / 41, `reference_47_difference` 0 |

Run 4's schema carries the note "declarations item shape is provisional, not
ratified". That note describes the file as it was frozen. The scratch file is
kept as evidence under OD-6 and is not edited. From this record on, item (d)
is ratified.

## Consequences

| Item | Before (`347771bd`) | Now |
|---|---|---|
| IM-17 | Not ratified. Open on OD-11 | **Decided and closed.** The candidate proposals are ratified with no revision, so no Proof C re-run is needed |
| IM-03 | Ratified as proof-backed. Finality open on IM-16 and IM-17 | Ratified as proof-backed. **Finality open on IM-16 only** |
| IM-16 | Not ratified. Open, routed to an architecture decision (OD-10) | **Unchanged** |
| Resolver contract or API freeze | Blocked on OD-10's architecture decision, tests of both orders, and OD-11 | **Blocked on OD-10's architecture decision and tests of both orders only** |

**IM-16 and the ratified list.** R-C3b chooses between
`INPUT_CHANGED_DURING_RESOLUTION` and a class 1b read-limit code. Both are
already in the ratified list, so the OD-10 decision cannot add or remove a
code. Whether it needs any Proof C re-run beyond the tests of both orders is
part of that decision, and Stage assumes no answer. R-C3b stays
`DISPUTED_NOT_ASSUMED`.

## Row-Status Consequences

**No row status changes.** `a04dea18` records OD-11 as affecting "IM-17,
IM-03 (not a proof-entry row)". `PE-DATA-01` and `PE-DATA-02` were already
`MET`. Their pass criteria measure against the governing set and the
candidate as a proposal, so they never depended on ratification.

Rows checked against this commit:

* `PE-AUTH-01` (`MET`, unchanged). This record is a proof-exit report
  addendum (`artifact_class: proof-exit-report-addendum`), as OD-12 answer 1
  classifies the addenda. The same commit also carries one
  `.backlogit/stash.jsonl` line: an operator-requested stash intake that is
  unrelated to the proof exit and is not recorded here. Stage reads it as a
  post-exit capture under OD-8, made through backlogit, and not a
  proof-phase backlog mutation. OD-12 answer 1 named only `9144435A`, so
  this classification is a Stage reading. If the operator disagrees,
  `PE-AUTH-01` becomes `MET-COND` on that point.
* `PE-AUTH-03` (`MET`, unchanged). OD-11 is recorded as an operator ruling,
  quoted with its timestamp, and the reading is disclosed as the
  Orchestrator's. This record authorizes nothing itself.
* `PE-SCOPE-01` to `07` and `PE-TASK-03` (`MET`, unchanged). No plan,
  review, shipment or lock file changes, and no harvest.
* `PE-ACTIVATE-01` (`MET`, unchanged). Since `08787a4b`, only
  `docs/decisions/` files and `.backlogit/stash.jsonl` have changed, and this
  commit adds one of each kind. The template, mirror, manifest and config
  blobs are the blobs at `08787a4b`.
* `PE-FLOW-02` (`MET`, unchanged). No Phase 2 artifact exists. This record is
  not one.

## Updated Counts

Checked against the `347771bd` table. No row moves.

| Status | Rows | IDs |
|---|---|---|
| `MET` | 30 | AUTH-01, AUTH-02, AUTH-03, AUTH-04, SCOPE-01 to 07, FLOW-01 to 04, INTERFACE-02, INTERFACE-03, SAFETY-06, DATA-01 to 04, TASK-01, TASK-03, EVIDENCE-01, EVIDENCE-03, EVIDENCE-04, EVIDENCE-05, ACTIVATE-01, ACTIVATE-03 |
| `MET-COND` | 0 | none |
| `OPEN-EVIDENCE` | 0 | none |
| `UNSATISFIED` | 0 | none |
| `WIN-MET / LINUX-PENDING` | 7 | SAFETY-01, 02, 03, 04, 05, 07, EVIDENCE-02 |
| `DEFERRED` | 3 | INTERFACE-01, TASK-02, ACTIVATE-02 |
| **Total** | **40** | 36 not-deferrable, 1 mixed (SAFETY-02) and 3 deferred |

The 7 Linux-`PENDING` rows stay pending until IM-01 runs on Linux. No one can
waive that gate.

## Open Decisions and Remaining Gates

| Item | Status | Affects |
|---|---|---|
| **OD-10 architecture decision** | **Open, the only open operator decision.** Routed in `347771bd`; decide R-C3b (amend or extend Decision 2 items 2 and 5 of `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`, or a new record), then test both orders | IM-16, IM-03 finality, resolver contract freeze |
| Section 9 governance defaults | Need ratification before the next review epoch opens, except the `P2` publication rule (decided in `347771bd`) | Review epoch |
| Linux-native run (IM-01) | Not executed. Non-waivable | 7 Linux-`PENDING` rows, IM-02, any containment-dependent unit |
| `187-S` retirement mechanics | C3 approved retirement. The mechanics must still be checked against the installed backlogit version, and retirement must not be performed as a Ship claim | Phase 2 re-slice |
| Scratch cleanup | Withheld under OD-6 until the last lifecycle release unit closes | Hygiene |
| IM-10 reconciliation | Stash `9144435A` needs triage and its own release unit | IM-10 |
| Publication | Not ready. There are 40 local commits ahead of upstream, 41 with this one, and none is pushed. Pushing is an operator action | Publication |

Resolved: OD-1 (`4c6e2701`), OD-2 (`e65887d8`), OD-3, OD-5 and OD-9
(`928bf3ff`), OD-6, OD-7, OD-8, C2, C3 and the C4 reviewer lead
(`2634bac2`), OD-4, OD-10 routing, OD-12 and the C4 `P2` rule (`347771bd`),
and OD-11 (this record).

## What This Record Does Not Do

This record only records the OD-11 ruling of 2026-09-25T17:55:28-07:00, the
reading it is given and its effect on IM-17, IM-03 and the open-decision
list. It **does not make** the OD-10 architecture decision or choose between
R-C3b's two codes. It **does not ratify** IM-16 or the section 9 defaults. It
**does not edit** the charter, the Proof C evidence or any earlier record. It
**authorizes no** plan, plan revision, harvest, backlog item, shipment
change, `187-S` retirement step, review epoch, activation, claim,
configuration change, proof run, scratch cleanup, push or pull request.
`187-S` stays `queued` and frozen until Phase 2 is routed.

## References

* Refresh report: `docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md` (`a04dea18`), IM-03, IM-16, IM-17 and OD-11
* Third rulings record: `docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-3.md` (`347771bd`), "Implementation Matrix Ratification" and "Open Decisions"
* Second rulings record: `docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-2.md` (`2634bac2`), matrix ratification with carve-outs
* Proof C run 4: `docs/decisions/2026-09-24-surface-taxonomy-proof-c-run4-spike.md` (`4c6e2701`), "Candidate and freeze" and the criteria table
* Charter: `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md`, section 6.5 (candidate at `52c985cb`, PE-1.4; current `e65887d8`, PE-1.7)
* Architecture decision: `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`, Decision 2 items 2 and 5 (not edited)
* Policies: `.github/policies/workflow-policies.md` (P-010)
