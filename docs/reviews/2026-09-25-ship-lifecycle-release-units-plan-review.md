---
title: "Review manifest: ship lifecycle release units A to D plan (governing epoch LIFECYCLE-E5)"
description: "Review manifest for the single governing plan docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md. The governing epoch is LIFECYCLE-E5-b7a77c76 (subject plan revision 9, commit 42fec73f, blob b7a77c76): its initial review and its final full consistency pass each passed 7 of 7 with no consolidated revision, closing NOROW-F20 and IM-14-F64 (verdict PASS; publication met). Operator rulings OP-5, OP-2 and OP-1 (2026-09-25T23:56:45-07:00) permit harvest of S(A), S(C), S(B-core) and S(B-entry); S(D) is withheld until the IM-10 shipment exists. Earlier epochs, all under the parameters frozen in 2ca9d9a5 and all EPOCH_STOPPED with publication not met and nothing harvested: LIFECYCLE-E2-R1-2d562820 (initial full review of revision 1, blob 2d562820, seven personas, all REVISE, 41 consolidated findings of which 7 block; two consolidated revisions and two delta reviews, blockers 7 -> 2 -> 3; stopped with 3 IM-14 blockers open); LIFECYCLE-E3-703d0de1 (IM-14 audit; revisions 4 and 5; stopped after delta review 1: 5 blockers closed, 7 new admitted); LIFECYCLE-E4-5cf1d52a (re-chartered IM-14 audit; revisions 6 to 8; used both consolidated revisions and stopped at the final full consistency pass with 2 blockers, one an authority mismatch). Findings, verdicts and dispositions live here and never in the plan."
doc_type: review-manifest
date: 2026-09-25
plan_id: ship-lifecycle-release-units
plan_path: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
review_epoch_family: LIFECYCLE-E5
review_epoch: LIFECYCLE-E5-b7a77c76
frozen_parameters: {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-5.md, commit: 2ca9d9a5, section: "Frozen Epoch Parameters"}
rubric: {version: R1, skill_path: .github/skills/plan-review/SKILL.md, skill_blob_sha1: c77f3685e81046195a55bcf4fc1e7d8973e40f97}
matrix_version: "IM-01 to IM-17 (a04dea18; ratified 2634bac2; IM-17 closed b8a7b100; IM-16 decided 8fa08913); PE-1.7 (e65887d8)"
reviews:
  - {epoch: LIFECYCLE-E2-R1-2d562820, step: initial-full-review, subject_revision: 1, subject_commit: c7363567, subject_blob: 2d5628206de3ab8083ec8ac173fa5283663f9b01, decision: REVISE, blocking_open: 7}
  - {epoch: LIFECYCLE-E2-R1-2d562820, step: consolidated-revision-1, subject_revision: 2, subject_commit: fcae22da, subject_blob: 1828ecb9462762945979fbbfc1a73320f5975653, decision: REVISE, blocking_claimed_fixed: 7}
  - {epoch: LIFECYCLE-E2-R1-2d562820, step: delta-review-1, subject_revision: 2, subject_blob: 1828ecb9462762945979fbbfc1a73320f5975653, decision: REVISE, blocking_open: 2}
  - {epoch: LIFECYCLE-E2-R1-2d562820, step: consolidated-revision-2, subject_revision: 3, subject_commit: bd7002d5, subject_blob: ffa663de030a0a07baa5b62ea1078b750a0a4009, decision: REVISE, blocking_claimed_fixed: 2}
  - {epoch: LIFECYCLE-E2-R1-2d562820, step: delta-review-2, subject_revision: 3, subject_blob: ffa663de030a0a07baa5b62ea1078b750a0a4009, decision: REVISE, blocking_open: 3}
  - {epoch: LIFECYCLE-E3-703d0de1, step: initial-review, subject_revision: 4, subject_commit: 48cafb4a, subject_blob: 703d0de11fa5515a4abba0146d2f792bbe9991a6, decision: REVISE, blocking_open: 5}
  - {epoch: LIFECYCLE-E3-703d0de1, step: consolidated-revision-1, subject_revision: 5, subject_commit: 01cb89b9, subject_blob: 057a7615a5a53e53698bb53604ad7fba5382e744, decision: REVISE, blocking_claimed_fixed: 5, blocking_open: 7}
  - {epoch: LIFECYCLE-E3-703d0de1, step: delta-review-1, subject_revision: 5, subject_blob: 057a7615a5a53e53698bb53604ad7fba5382e744, decision: REVISE, blocking_closed: 5, blocking_open: 7}
  - {epoch: LIFECYCLE-E4-5cf1d52a, step: initial-review, subject_revision: 6, subject_commit: 33ad886b, subject_blob: 5cf1d52a48840d43aacfe8795b9b6ceba8d7f809, decision: REVISE, blocking_open: 3}
  - {epoch: LIFECYCLE-E4-5cf1d52a, step: consolidated-revision-1, subject_revision: 7, subject_commit: 79c18cc0, subject_blob: 0aa8b652bee6f4a0ca67316d450ca781f8953c1c, decision: REVISE, blocking_claimed_fixed: 3, blocking_open: 1}
  - {epoch: LIFECYCLE-E4-5cf1d52a, step: delta-review-1, subject_revision: 7, subject_blob: 0aa8b652bee6f4a0ca67316d450ca781f8953c1c, decision: REVISE, blocking_closed: 3, blocking_open: 1}
  - {epoch: LIFECYCLE-E4-5cf1d52a, step: consolidated-revision-2, subject_revision: 8, subject_commit: d47f64b1, subject_blob: 8d397c0559ae96da709620fc3db044124c068423, decision: PASS, blocking_claimed_fixed: 1}
  - {epoch: LIFECYCLE-E4-5cf1d52a, step: delta-review-2, subject_revision: 8, subject_blob: 8d397c0559ae96da709620fc3db044124c068423, decision: PASS, blocking_closed: 1, blocking_open: 0}
  - {epoch: LIFECYCLE-E4-5cf1d52a, step: final-full-consistency-pass, subject_revision: 8, subject_blob: 8d397c0559ae96da709620fc3db044124c068423, decision: REVISE, blocking_open: 2, residue_audit: no-claim}
  - {epoch: LIFECYCLE-E5-b7a77c76, step: initial-review, subject_revision: 9, subject_commit: 42fec73f, subject_blob: b7a77c7644fa97dff01c724480abfcbcea8f346d, decision: PASS, blocking_closed: 2, blocking_open: 0, residue_audit: no-claim}
  - {epoch: LIFECYCLE-E5-b7a77c76, step: final-full-consistency-pass, subject_revision: 9, subject_blob: b7a77c7644fa97dff01c724480abfcbcea8f346d, decision: PASS, blocking_open: 0, residue_audit: no-claim}
  - {epoch: LIFECYCLE-E5-b7a77c76, step: verdict, subject_revision: 9, subject_commit: 42fec73f, subject_blob: b7a77c7644fa97dff01c724480abfcbcea8f346d, dispatch_mode: explicit-model subagent, decision: PASS, publication: met}
consolidated_revisions_used: 0
consolidated_revisions_limit: 2
status: passed
verdict: PASS
decision: PASS
publication: met
publication_eligible: true
harvest_permitted: true
harvest_permitted_scope: [S(A), S(C), S(B-core), S(B-entry)]
harvest_withheld: {shipment: S(D), reason: "gated on the IM-10 shipment existing (OP-1 approved; IM-10 not yet scheduled as a shipment)"}
harvest_prerequisites: {OP-5: "authorized 2026-09-25T23:56:45-07:00: harvest reads dispatch_mode and decision from the E5 verdict entry bound to blob b7a77c76", OP-2: "keep 2026-09-25T23:56:45-07:00: IM-09 D4 stays in Unit D", OP-1: "approved 2026-09-25T23:56:45-07:00: IM-10 release unit (stash 9144435A) to be scheduled to ship before S(D); S(D) harvest waits for the IM-10 shipment"}
operator_rulings_harvest: {at: "2026-09-25T23:56:45-07:00", OP-5: authorized, OP-2: keep, OP-1: approved}
e2_stop: {epoch: LIFECYCLE-E2-R1-2d562820, last_subject_revision: 3, last_subject_commit: bd7002d5, last_subject_blob: ffa663de030a0a07baa5b62ea1078b750a0a4009, status: epoch-stopped, verdict: EPOCH_STOPPED, decision: EPOCH_STOPPED, publication: not-met, publication_eligible: false, harvest_permitted: false, consolidated_revisions_used: 2, consolidated_revisions_limit: 2, stop_conditions_triggered: [blockers-do-not-decline-across-revisions, second-remediation-fails], operator_decision: {at: "2026-09-25T20:47:56-07:00", outcome: spike, next: "E3 scoped to the IM-14 audit section after spike ratification"}, operator_ratification: {at: "2026-09-25T21:10:37-07:00", spike_commit: 27bcc254, design: ratified, e3_scope_widened: true, residue_text_audit: "agent-performed, recorded, release-scoped; operator not required"}}
e3_epoch: {id: LIFECYCLE-E3-703d0de1, subject_revision: 4, subject_commit: 48cafb4a, subject_blob: 703d0de11fa5515a4abba0146d2f792bbe9991a6, scope: "IM-14 section, C5 Change cell, contradicting IM-14/PE-SAFETY-06 trace text, CONST-G2-F01", baseline_blob: ffa663de030a0a07baa5b62ea1078b750a0a4009, verdict: EPOCH_STOPPED}
e3_stop: {epoch: LIFECYCLE-E3-703d0de1, last_subject_revision: 5, last_subject_commit: 01cb89b9, last_subject_blob: 057a7615a5a53e53698bb53604ad7fba5382e744, status: epoch-stopped, verdict: EPOCH_STOPPED, decision: EPOCH_STOPPED, publication: not-met, publication_eligible: false, harvest_permitted: false, consolidated_revisions_used: 1, consolidated_revisions_limit: 2, stop_conditions_triggered: [blockers-do-not-decline-across-revisions, newly-admitted-findings-at-least-as-many-as-closed], operator_decision: {at: "2026-09-25T22:29:53-07:00", outcome: re-charter, next: "LIFECYCLE-E4 (IM-14 audit re-chartered)"}}
e4_epoch: {id: LIFECYCLE-E4-5cf1d52a, subject_revision: 6, subject_commit: 33ad886b, subject_blob: 5cf1d52a48840d43aacfe8795b9b6ceba8d7f809, derived_from: {revision: 5, commit: 01cb89b9, blob: 057a7615a5a53e53698bb53604ad7fba5382e744}, scope: "IM-14 section, C5 Change cell, IM-14 row, D3 preflight item 6 and noclaim-audit Files cells only if contradicting, frontmatter", verdict: EPOCH_STOPPED}
e4_stop: {epoch: LIFECYCLE-E4-5cf1d52a, last_subject_revision: 8, last_subject_commit: d47f64b1, last_subject_blob: 8d397c0559ae96da709620fc3db044124c068423, status: epoch-stopped, verdict: EPOCH_STOPPED, decision: EPOCH_STOPPED, publication: not-met, publication_eligible: false, harvest_permitted: false, consolidated_revisions_used: 2, consolidated_revisions_limit: 2, blocking_open: [NOROW-F20, IM-14-F64], residue_audit: {blob: 8d397c0559ae96da709620fc3db044124c068423, personas: 7, result: no-claim}, stop_conditions_triggered: [authority-mismatch-between-artifacts, remediation-budget-exhausted-with-open-blockers, blockers-do-not-decline-across-revisions], operator_decision: {at: "2026-09-25T23:16:08-07:00", outcome: new-epoch, next: "LIFECYCLE-E5 (harvest_gate, Bottom Line Status, residue harvest clause)"}}
e5_epoch: {id: LIFECYCLE-E5-b7a77c76, subject_revision: 9, subject_commit: 42fec73f, subject_blob: b7a77c7644fa97dff01c724480abfcbcea8f346d, derived_from: {revision: 8, commit: d47f64b1, blob: 8d397c0559ae96da709620fc3db044124c068423}, scope: "frontmatter (harvest_gate, revision and epoch metadata, hardening_pass only if needed), Bottom Line Status line, residue-rule harvest clause", blockers_targeted: [NOROW-F20, IM-14-F64], blockers_closed: [NOROW-F20, IM-14-F64], consolidated_revisions_used: 0, residue_audit: {blob: b7a77c7644fa97dff01c724480abfcbcea8f346d, personas: 7, result: no-claim}, verdict: PASS, decision: PASS, publication: met, harvest_permitted_at_verdict: false, harvest_permitted: true, harvest_authorized_by: "OP-5 (2026-09-25T23:56:45-07:00); scope S(A), S(C), S(B-core), S(B-entry); S(D) withheld"}
recorded_by: Stage
consolidated_by: "Orchestrator (raw collection and blocking classification); Stage (classification check, identity resolution, dispositions)"
---

# Review Manifest: Ship Lifecycle Release Units Plan

## Epoch

| Field | Value |
|---|---|
| Governing epoch | `LIFECYCLE-E5-b7a77c76`, verdict `PASS` (see [E5 Verdict](#e5-verdict)). The rows below record the first epoch, E2 (`EPOCH_STOPPED`) |
| Epoch token | `LIFECYCLE-E2-R1-2d562820` (first 8 hex of the reviewed blob) |
| Subject | `docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md`, revision 1, commit `c7363567`, blob `2d5628206de3ab8083ec8ac173fa5283663f9b01` |
| Frozen parameters | Rulings 5 (`2ca9d9a5`), "Frozen Epoch Parameters": rubric R1, persona set, reviewer route, severity mapping, finding lineage, cadence, budgets and gates. Nothing is restated or changed here |
| Rubric integrity | `.github/skills/plan-review/SKILL.md` blob `c77f3685e81046195a55bcf4fc1e7d8973e40f97` at `c7363567`, equal to R1 |
| Record location | This manifest. The R1 rubric's "append to the plan" step is replaced by this manifest under the plan's single-governing-plan contract; harvest reads it only under OP-5 |

## Initial Full Review (subject revision 1)

```text
dispatch_mode: multi-agent
dispatch_route: explicit-model gpt-6-sol, dispatcher Orchestrator
decision: REVISE
```

`decision: REVISE` is not `PASS` or `ADVISORY`, so harvest halts on it.
`dispatch_mode:` uses the rubric's enum value. The route detail is on
its own line.

### Dispatch and Personas

Stage's runtime has no subagent dispatch. The Orchestrator dispatched all
seven personas. The `anchor_review` personas ran with `gpt-6-sol` named
explicitly. That is the frozen route, so it is not a route change and does
not pause the epoch. Every selected persona was covered.

| Persona | Role | Frozen route | Model actually used | Agent ID | Decision |
|---|---|---|---|---|---|
| Architecture Strategist | Lead | `anchor_review` | `gpt-6-sol` / `openai` / `high` | `03aa57a7` | REVISE |
| Security Lens Reviewer | Supporting | `anchor_review` | `gpt-6-sol` / `openai` / `high` | `c5d5b001` | REVISE |
| Agent-Native Parity Reviewer | Supporting | `anchor_review` | `gpt-6-sol` / `openai` / `high` | `208ca575` | REVISE |
| Constitution Reviewer | Supporting | caller | `claude-opus-5.5` / `anthropic` / `high` | `a9ac98f8` | REVISE (read the working-tree copy, identical to `c7363567`) |
| Python Reviewer | Supporting | caller | `claude-opus-5.5` / `anthropic` / `high` | `3b96fe75` | REVISE |
| Scope Boundary Auditor | Supporting | caller | `claude-opus-5.5` / `anthropic` / `high` | `515ac98b` | REVISE |
| Learnings Researcher | Supporting | caller | `claude-opus-5.5` / `anthropic` / `high` | `f3dca2ab` | REVISE |

### Blocking Classification Check

Stage re-applied the frozen rule. A finding blocks only if its class is
`CRITERION` or `EVIDENCE` **and** it is `P0` or `P1`, or it is `P2` on
IM-14, `PE-SAFETY-06` or `PE-SAFETY-07`. The Orchestrator's seven blocking
findings all meet that rule. No other finding does:

* `PE-SAFETY-03-F01` (`CRITERION`) and IM-09-F01 and IM-16-F01 (`EVIDENCE`)
  are `P2` on rows that are not `P2-critical`.
* IM-14-F04 is `P2` on a critical row, but its class is `CONSISTENCY`.
  IM-14-F03 and `PE-SAFETY-07-F01` are `P3`.
* Findings with no matrix row are `CHANGE` or `PROCESS` and cannot block.

### Identity Resolution

The personas numbered their findings independently, so some IDs collided.
Stage keeps the Orchestrator's IDs for the seven blocking findings. Every
other distinct concern gets the next free `F<NN>` on its row. Child IDs
(`<parent>.<n>`) are kept for residue after a partial close, as the
lineage rule says, so they are not used for new findings. Row-less
findings are numbered once across all personas as `NOROW-F<NN>`.

| Raw ID (persona) | Stable ID | Relation |
|---|---|---|
| IM-10 (Parity, P1 CRITERION) | IM-10-F01 | Primary |
| IM-10 (Constitution, P2 RISK) | IM-10-F01 | Duplicate |
| IM-07 (Lead, P1 EVIDENCE) | IM-07-F01 | Primary |
| IM-07 (Parity, P1 EVIDENCE); IM-07 (Scope, P2 EVIDENCE); IM-07-F01 (Python, P2 RISK) | IM-07-F01 | Duplicates |
| IM-07-F02 (Python: duplicate keys, NaN) | IM-07-F03 | Distinct |
| IM-07-F01 (Constitution: B rollback and D1) | IM-07-F02 | Distinct |
| IM-05-F01 (Security) | IM-05-F01 | Primary |
| IM-05-F01 (Python: `O_BINARY`) | IM-05-F02 | Distinct |
| IM-01-F01 (Security: `TMPDIR` export) | IM-01-F01 | Primary |
| IM-01-F01 (Learnings: `pipefail`) | IM-01-F02 | Distinct |
| IM-01-F01 (Python: upper-case root) | IM-01-F03 | Distinct |
| IM-14 (Security, Scope, Constitution, Python, Learnings: audit scope) | IM-14-F01 | Security primary; four duplicates |
| IM-14-F02 (Learnings: wrapping, controls) | IM-14-F02 | Primary |
| IM-14-F02 (Scope: historical wording) | IM-14-F03 | Distinct |
| IM-14-F02 (Constitution: docstring owner) | IM-14-F04 | Distinct |
| IM-13-F01 (Constitution: per-test marker) | IM-13-F01 | Primary |
| IM-13-F01 (Learnings: CRLF render equality) | IM-13-F02 | Distinct |
| IM-04-F01 (Learnings: tie-break fixtures) | IM-04-F01 | Primary |
| IM-04-F01 (Python: backlog root) | IM-04-F02 | Distinct |
| IM-08-F01 (Constitution: P-009) | IM-08-F01 | Primary |
| IM-08-F01, IM-08-F02 (Learnings) | IM-08-F02, IM-08-F03 | Distinct |
| IM-06-F01 (Scope); IM-06-F01 (Python) | IM-06-F01 | Scope primary; Python duplicate |
| IM-11-F01 (Python, P2); IM-11-F01 (Scope, P3) | IM-11-F01 | Python primary (higher severity); Scope duplicate |
| NOROW-F01 (Lead) | NOROW-F01 | Primary |
| NOROW-F01 (Parity) | NOROW-F02 | Primary |
| NOROW-F01, NOROW-F02 (Scope) | NOROW-F03, NOROW-F04 | Primary |
| NOROW-F01 to NOROW-F05 (Constitution) | NOROW-F05 to NOROW-F09 | Primary |
| NOROW-F01 (Python) | NOROW-F10 | Primary |
| NOROW-F01, NOROW-F02 (Learnings) | NOROW-F11, NOROW-F12 | Primary |

That leaves 41 findings: 7 block and 34 do not. There are 10 duplicate
raw findings: 1 on IM-10, 3 on IM-07-F01, 4 on IM-14-F01, 1 on IM-06-F01
and 1 on IM-11-F01.

### Findings

Disposition in this table is the state at the end of the initial review.
The disposition after consolidated revision 1 is recorded in its own
section below.

| ID | Raised by | Class | Sev | Blocking | Summary | Disposition |
|---|---|---|---|---|---|---|
| IM-10-F01 | Parity | CRITERION | P1 | **Yes** | S(D) can start before the separate IM-10 unit ships. D2 stays red until D3, so P-001 deadlocks S(D) against IM-10 | Open |
| IM-07-F01 | Lead | EVIDENCE | P1 | **Yes** | D1's validator and `python -m` entry have no capture, input or output contract. No test covers the live Ship T1 handoff or refuses T2, T3 and Claim after `resolver-not-observed` | Open |
| IM-05-F01 | Security | CRITERION | P1 | **Yes** | C3 says binary but not unbuffered. A buffered object can fetch more than cap+1 bytes | Open |
| IM-01-F01 | Security | CRITERION | P1 | **Yes** | `TMPDIR` may not reach Python, so the fixtures may land off the recorded filesystem | Open |
| IM-14-F01 | Security | CRITERION | P2 (critical row) | **Yes** | The audit scope covers C and the D3 diff only. IM-14 says all units | Open |
| IM-14-F02 | Learnings | EVIDENCE | P2 (critical row) | **Yes** | The regex misses wrapped claims, the presence check fails on a wrapped sentence, and there are no controls | Open |
| IM-13-F01 | Constitution | CRITERION | P1 | **Yes** | One marker per task cannot give each roster test its own marker under R2 | Open |
| IM-01-F02 | Learnings | EVIDENCE | P2 | No | A pipe can mask the unittest exit code without `pipefail` | Open |
| IM-01-F03 | Python | RISK | P2 | No | The upper-case root case has no Linux branch, so it would skip | Open |
| IM-05-F02 | Python | CRITERION | P2 | No | `os.open` without `O_BINARY` is text mode on Windows | Open |
| IM-07-F02 | Constitution | CONSISTENCY | P3 | No | B's rollback must also revert D1 | Open |
| IM-07-F03 | Python | RISK | P2 | No | D1 must reject duplicate JSON keys and `NaN` or `Infinity` | Open |
| IM-14-F03 | Scope | RISK | P3 | No | The plan's historical "race-resistant" wording would trip a wider audit | Open |
| IM-14-F04 | Constitution | CONSISTENCY | P2 (critical row) | No | No task writes the required non-claim docstring sentence | Open |
| IM-02-F01 | Python | RISK | P2 | No | Templates are not `eol=lf` pinned, so a CRLF checkout causes a render mismatch on Windows | Open |
| IM-03-F01 | Learnings | CONSISTENCY | P2 | No | Schema mirrors differ in `$id`, so "byte-identical" is wrong. Pin the `1.0.0` mirror | Open |
| IM-04-F01 | Learnings | EVIDENCE | P2 | No | Tie-break fixtures must make listed order disagree with task-ID and first-seen order | Open |
| IM-04-F02 | Python | CONSISTENCY | P2 | No | Backlog-root detection versus claims, and whether `backlog_root.py` or its override is reused | Open |
| IM-06-F01 | Scope | CONSISTENCY | P3 | No | Name the private patch points | Open |
| IM-08-F01 | Constitution | RISK | P3 | No | Cite P-009 and check the merge commit's two parents | Open |
| IM-08-F02 | Learnings | RISK | P3 | No | backlogit 1.10's claim cascades tasks to `active`, so T1 to T3 must not depend on `queued` | Open |
| IM-08-F03 | Learnings | RISK | P3 | No | D2 should assert that no ordering claim contradicts the Ship procedure | Open |
| IM-09-F01 | Scope | EVIDENCE | P2 | No | D4's "listed mis-orderings" and L5 are not listed | Open |
| IM-11-F01 | Python | RISK | P2 | No | B4b is overloaded and B sits at 480 of 480. Split B | Open |
| IM-12-F01 | Learnings | RISK | P2 | No | Check that the recorded checksum equals the HEAD blob before refresh, and halt on drift | Open |
| IM-13-F02 | Learnings | RISK | P3 | No | A1's render-equality check breaks on a CRLF template on Windows | Open |
| IM-16-F01 | Python | EVIDENCE | P2 | No | `FILE_COUNT_LIMIT` cannot be reached through `resolve_shipment` with the defaults. A private limits hook is needed | Open |
| `PE-SAFETY-03-F01` | Python | CRITERION | P2 | No | `commonpath` raises `ValueError` across drives or with `\\?\` | Open |
| `PE-SAFETY-07-F01` | Constitution | CONSISTENCY | P3 | No | List the `/dev` targets in Risky Actions. Cleanup unlinks and never follows | Open |
| NOROW-F01 | Lead | PROCESS | P3 | No | B3 depends on the private `_render_template` | Open |
| NOROW-F02 | Parity | CHANGE | P3 | No | Record the CLI-only boundary; a future MCP transport uses the same resolver | Open |
| NOROW-F03 | Scope | CHANGE | P3 | No | Reader code `IO` is never verified | Open |
| NOROW-F04 | Scope | PROCESS | P3 | No | `181.001-T` is missing from the trace | Open |
| NOROW-F05 | Constitution | PROCESS | P3 | No | Rollback landing: `chore/` branch pull request, merge commit, recheck of approved SHAs | Open |
| NOROW-F06 | Constitution | PROCESS | P3 | No | Record A1 and A2's pre-edit failing run as gap characterization | Open |
| NOROW-F07 | Constitution | PROCESS | P3 | No | Declare `freeze-scope` and `careful` modes for D3 and its rollback | Open |
| NOROW-F08 | Constitution | PROCESS | P3 | No | Windows test temp lies outside the workspace | Open |
| NOROW-F09 | Constitution | PROCESS | P3 | No | The post-D3 monitoring window sits outside P-001 closure. Name where it is recorded | Open |
| NOROW-F10 | Python | CHANGE | P3 | No | Add a golden `inputs_sha256` fixture | Open |
| NOROW-F11 | Learnings | PROCESS | P3 | No | P-015 close path: successors stay queued behind `blocks` edges | Open |
| NOROW-F12 | Learnings | PROCESS | P3 | No | A1 and A2 are code-affecting for closure anchors | Open |

### Gate State After the Initial Review

Publication is **not met**: 7 blocking findings are open. The next step is
consolidated revision 1 of 2, then delta reviews against changes only, then
one final full consistency pass.

## Consolidated Revision 1 (subject revision 2)

| Field | Value |
|---|---|
| Subject | Plan revision 2, commit `fcae22da`, blob `1828ecb9462762945979fbbfc1a73320f5975653` (842 lines) |
| Revisions used | 1 of 2 |
| Author | Stage (`claude-opus-5.5` / `anthropic` / `high`) |
| Review state | Pending delta reviews against changes only. No finding is closed until a delta review checks its named evidence |

### Contract Growth (limit: over 20% ends the epoch)

Measured against revision 1 (blob `2d562820`):

| Measure | Revision 1 | Revision 2 | Growth |
|---|---:|---:|---:|
| File bytes | 69163 | 82011 | +18.6% |
| Body bytes (after frontmatter) | 63778 | 76224 | +19.5% |
| Words | 10198 | 12061 | +18.3% |
| Lines | 769 | 842 | +9.5% |
| Tasks | 17 | 17 | 0% |
| Reason codes / `ReadErrorCode` values | 47 / 8 | 47 / 8 | 0% |
| New public names | none | `verify_workspace.render_template` (alias) | +1 |
| Summed estimate (minutes) | 1390 | 1555 | +11.9% |
| Shipments | 4 | 5 | +25% (B split, required by section 9 budgets; see note) |

Every text-size measure is within 20%. The shipment count is higher only
because the section 9 budget rule required B to split. No task,
reason code or public contract was added for that. Whether a
budget-required split counts as contract growth is for the Orchestrator to
rule on.

Orchestrator ruling: the B split into S(B-core)/S(B-entry) is required by
the ratified section 9 per-shipment budget and adds no task, reason code or
public contract; it is not contract growth. Contract growth is measured on
the text/contract measures, all within 20% (max +19.5% body bytes). The
operator may overrule.

### Dispositions

Line references are to revision 2 (blob `1828ecb9`).

| ID | Blocking | Disposition | Evidence in revision 2 |
|---|---|---|---|
| IM-10-F01 | **Yes** | Fixed | L186 (IM-10 row); L482 and L494-498 (`S(IM-10) -> S(D)`; S(D) harvested only once the IM-10 shipment exists); PD-02; OP-1 |
| IM-07-F01 | **Yes** | Fixed | L183 (IM-07 row); L417 (B5 one document plus one LF); L433 (D1 capture contract and entry); L434 (real-CLI handoff test, exits 0/1/2 plus an impostor); L444 (D2: no T2, T3 or Claim after `resolver-not-observed`); invariant 6 |
| IM-05-F01 | **Yes** | Fixed | L181; L301 (`os.open` unbuffered, reads only through `_read_chunk`, request bound); L302 (recorded request sizes, at most 65 bytes requested for 4096 B, short reads) |
| IM-01-F01 | **Yes** | Fixed | L177; L323 (`export TMPDIR`, effective fixture root asserted under `$RUNNER_TEMP`, filesystem type of that root); L324 (evidence fields) |
| IM-14-F01 | **Yes** | Fixed | L190 and the `PE-SAFETY-06` row; L721-755 (one inventory across A to D, carriers and closures; a missing file fails); extended by B1, B5, D1, D2 and D4, and run by D3's preflight |
| IM-14-F02 | **Yes** | Fixed | L737-752 (whitespace collapse including newlines, `[-\s]*` patterns, broader affirmative forms, positive and negative controls) |
| IM-13-F01 | **Yes** | Fixed | L135 (FI-9); L159-168 (Marker Convention: prefix plus per-test suffix, pairwise distinct, test-to-marker map); L189; A1 and A2 (L224, L231); every `Marker` row marked `(prefix)` |
| IM-01-F02 | No | Fixed | L323 (`set -euo pipefail`, log file, exit code gated before the summary) |
| IM-01-F03 | No | Fixed | L291 (Linux case-sensitivity branch under the same ID) |
| IM-05-F02 | No | Fixed | L301 (`O_BINARY`); L302 (`\r\n\x1a` returned byte-exact) |
| IM-07-F02 | No | Fixed | L762 (B rollback includes D1) |
| IM-07-F03 | No | Fixed | L433-434 (`object_pairs_hook`, `parse_constant`, controls) |
| IM-14-F03 | No | Fixed | L119 (history reworded); L754-755 |
| IM-14-F04 | No | Fixed | L279-281 (C1 writes the docstring sentence and tests it); the inventory's required-sentence rule |
| IM-02-F01 | No | Partly fixed; the pin is deferred | L578 (risk row: B uses LF fixtures, and D3 preflight (4) fails closed). The template `eol=lf` pin and renormalize are deferred to the IM-10 unit, which owns that template's bytes |
| IM-03-F01 | No | Fixed | L362-364 (equal except `$id`; `1.0.0` mirror SHA-256 pinned) |
| IM-04-F01 | No | Fixed | L374 (listed order disagrees with task-ID and first-seen order) |
| IM-04-F02 | No | Fixed | L373-374 (two fixed names probed by `isdir`, not a claim; no override, no `backlog_root.py`; override-set test) |
| IM-06-F01 | No | Fixed | L182; L263-265 (`_is_contained`, `_read_chunk`); L406 (`_resolve` limits) |
| IM-08-F01 | No | Fixed | L457 (P-009 merge commit, two-parent check) |
| IM-08-F02 | No | Fixed | L444 (T1 to T3 do not depend on `queued`) |
| IM-08-F03 | No | Fixed | L444 (no contradicting order statement) |
| IM-09-F01 | No | Fixed | L467-468 (L1, L3, L4, L5 enumerated from the Proof E run 5 limitations table) |
| IM-11-F01 | No | Fixed | L141-157 (re-estimate 550 minutes; B split into S(B-core) and S(B-entry)); L424; frontmatter `release_units`; PD-15 |
| IM-12-F01 | No | Fixed | L188; L224; L235; D3 preflight (1) |
| IM-13-F02 | No | Fixed | L224 and L235 (LF-normalized comparison) |
| IM-16-F01 | No | Fixed | L406-407 (private `_resolve` limits hook; read-limit codes reached with small limits) |
| `PE-SAFETY-03-F01` | No | Fixed | L201; L290-291 (`ValueError` -> `OUTSIDE_TRUST_ROOT`; cross-drive case) |
| `PE-SAFETY-07-F01` | No | Fixed | L681 (`/dev` targets listed; cleanup unlinks and never follows) |
| NOROW-F01 | No | Fixed | L384 (public alias `render_template`); PD-09; Risky Actions row |
| NOROW-F02 | No | Fixed | PD-16; Out of Scope |
| NOROW-F03 | No | Deferred | `IO` stays a closed code with a defined mapping (Unit B table). A portable `IO` fixture needs a per-OS mechanism: POSIX permission bits, or a Windows byte-range lock. Proof G does not cover that. C3 may add it if cheap. It is a `CHANGE`, so non-blocking |
| NOROW-F04 | No | Fixed | L511 (`181.001-T` trace row) |
| NOROW-F05 | No | Fixed | L458 (rollback through a `chore/` pull request, merge commit, SHA recheck) |
| NOROW-F06 | No | Fixed | L225 and L236 (pre-edit run recorded as gap characterization) |
| NOROW-F07 | No | Fixed | L456 (`careful` and `freeze-scope`; boundary is the three paths) |
| NOROW-F08 | No | Fixed | L704 (`TMP`/`TEMP` point at the in-workspace `.proof-scratch/tmp`) |
| NOROW-F09 | No | Fixed | L604 (monitoring recorded in Ship `docs/memory/`; does not hold S(D) open) |
| NOROW-F10 | No | Fixed | L396 (golden `inputs_sha256` fixture) |
| NOROW-F11 | No | Fixed | L498 (P-015 single closure; successors stay `queued`) |
| NOROW-F12 | No | Fixed | L601 (A is code-affecting for closure) |

Totals: 39 fixed, 1 partly fixed with the rest deferred (IM-02-F01), 1
deferred (NOROW-F03), 0 declined. All 7 blocking findings are marked fixed
and wait for delta-review confirmation.

**Stage-found correction (not a review finding).** B5's `--help` now prints
to stdout with exit 0 (L417), matching argparse. Revision 1 said usage on
stderr with exit 2.

## Delta Review 1 (subject revision 2)

```text
dispatch_mode: multi-agent
dispatch_route: explicit-model gpt-6-sol, dispatcher Orchestrator
decision: REVISE
```

The same seven reviewer agents checked revision 2 against changes only.
Lead (`gpt-6-sol`), Security (`gpt-6-sol`) and Python returned REVISE.
Parity (`gpt-6-sol`), Constitution, Scope and Learnings returned PASS.

**Closed on named evidence.** IM-10-F01, IM-07-F01, IM-05-F01, IM-01-F01,
IM-13-F01, IM-14-F02, IM-14-F03, IM-14-F04, IM-01-F02, IM-01-F03,
IM-05-F02, IM-07-F02, IM-07-F03, IM-02-F01 (deferral accepted), IM-03-F01,
IM-04-F02, IM-08-F01 to F03, IM-09-F01, IM-11-F01, IM-12-F01, IM-13-F02,
IM-16-F01, `PE-SAFETY-03-F01`, `PE-SAFETY-07-F01`, NOROW-F01, NOROW-F02
and NOROW-F04 to F10.

**Reopened.** IM-14-F01 was closed by four reviewers but held open by
Security and re-raised by Lead. It is treated as open and blocking, with
the residue recorded as IM-14-F01.1.

**Identity resolution.** Reviewer-local IDs collided. Stable IDs below;
merged local IDs are named in the Raised-by column.

| ID | Raised by (local ID) | Row class | Blocking | Summary |
|---|---|---|---|---|
| IM-14-F01.1 | Lead (IM-14-F05), Security (IM-14-F01, IM-14-F01.1) | IM-14, `P2-critical` | **Yes** | The inventory omits changed artifacts (C5's CI workflow, `schema_contracts.py`, `verify_workspace.py`, the manifest); extending tasks omit the audit test from Files; no per-shipment scope statement |
| IM-14-F05 | Python (IM-14-F05) | IM-14, `P2-critical` | **Yes** | Patterns miss inflected claims ("resistant to race", "protects against TOCTOU"); no inflected positive control |
| IM-14-F06 | Learnings (IM-14-F05) | IM-14 | No | Negative controls `trace` and `brace` test nothing; anchor with `\b` |
| IM-14-F07 | Constitution (IM-14-F05, P3), Scope (IM-14-F05) | IM-14 | No | S(A) closes before the audit exists; B2 and B3 modules join late |
| IM-03-F02 | Lead, Parity (IM-03-F02) | IM-03 | No | `FILE_COUNT_LIMIT` is reachable only through `_resolve`, not the public resolver or CLI |
| IM-03-F03 | Python (IM-03-F02) | IM-03 | No | Pinned schema hash breaks on a CRLF checkout |
| IM-11-F02 | Learnings (IM-11-F02) | IM-11 | No | S(B-core) is a partial-feature shipment; `shipment ship` hazard (097-S) |
| IM-11-F03 | Scope (IM-11-F03) | IM-11 | No | S(B-core) could publish schema `1.0.0` before B-entry's 47-code check |
| IM-07-F04 | Constitution (IM-07-F04) | IM-07 | No | D1's capture files have no named in-workspace, Git-ignored path or cleanup |
| IM-16-F02 | Python (IM-16-F02) | IM-16 | No | `usage.files_claimed` is unobservable from outside `_resolve` |
| IM-13-F03 | Python (IM-13-F03) | IM-13 | No | Structural tests reach no stub, so FI-9 refuses their RED |
| IM-10-F01.1 | Constitution (IM-10-F01.1), Scope (IM-10-F02) | IM-10 | No | Stale "D3 halts; D1, D2 remain valuable" text |
| IM-06-F01.1 | Python (IM-06-F01.1, P3) | IM-06 | No | "Tests patch nothing else" versus C1's and C3's counters |
| IM-04-F01.1 | Learnings (IM-04-F01.1) | IM-04 | No | Class-precedence fixtures must put the lower-class fact first |
| NOROW-F11.1 | Learnings (NOROW-F11.1, P3) | none | No | Close path is the classifier verdict |
| NOROW-F12.1 | Learnings (NOROW-F12.1, P3) | none | No | A's code-affecting rationale is procedure text; anchor refresh in its own commit |
| NOROW-F13 | Constitution, Python (NOROW-F13), Scope (IM-11-F02), Learnings (IM-11-F03) | none | No | Duplicated table header and separator |
| NOROW-F14 | Constitution (NOROW-F14) | none | No | B3 Files omit `verify_workspace.py` and the alias test |
| NOROW-F15 | Scope (NOROW-F13) | none | No | Runtime Verification has one B row for two shipments |
| NOROW-F16 | Scope (NOROW-F15, P3 advisory) | none | No | Public alias versus private import |
| NOROW-F17 | Scope (NOROW-F14) | none | No | Growth headroom |
| NOROW-F03 | Scope (NOROW-F03, P3) | none | No | `IO` unfixtured (re-raised) |

## Consolidated Revision 2 (subject revision 3)

| Field | Value |
|---|---|
| Subject | Plan revision 3, commit `bd7002d5`, blob `ffa663de030a0a07baa5b62ea1078b750a0a4009` (823 lines) |
| Revisions used | 2 of 2. A failed second remediation ends the epoch |
| Author | Stage (`claude-opus-5.5` / `anthropic` / `high`) |
| Review state | Pending delta reviews against changes only, then the final full consistency pass |

### Orchestrator Growth Ruling

Contract growth stays measured cumulatively against the epoch baseline,
revision 1 blob `2d562820`, on text measures (file bytes, body bytes,
words) and contract measures (tasks, reason codes, public names). The limit
is at most +20.0% each. Shipment count is exempt under the prior B-split
ruling. Changing the baseline mid-epoch would be a rubric change, so it is
not changed. Revision 3 therefore had to be size-neutral: body bytes at
most 76533, file bytes at most 82995, words at most 12237. Additions were
offset by condensing history and rationale prose, never contract text.

### Contract Growth (revision 1 versus revision 3)

| Measure | Revision 1 | Revision 3 | Limit | Growth |
|---|---:|---:|---:|---:|
| File bytes | 69163 | 81929 | 82995 | +18.5% |
| Body bytes (after frontmatter) | 63778 | 76103 | 76533 | +19.3% |
| Words | 10198 | 12001 | 12237 | +17.7% |
| Tasks | 17 | 17 | 20 | 0% |
| Reason codes / `ReadErrorCode` values | 47 / 8 | 47 / 8 | unchanged | 0% |
| New public names | none | `verify_workspace.render_template` (alias, unchanged since revision 2) | unchanged | +1 |
| Lines (not a limit) | 769 | 823 | none | +7.0% |
| Shipments (exempt) | 4 | 5 | exempt | +25% |

**Correction to the revision 2 table.** Re-measured from blob `1828ecb9`,
revision 2 is 82037 file bytes (+18.6%), 76250 body bytes (+19.6%) and
12064 words (+18.3%). The earlier table (82011, 76224, 12061) was measured
before a final edit. Every value stayed within 20%.

Revision 3 adds no task, reason code, public name, subsystem or threat
class.

### Dispositions

Line references are to revision 3 (blob `ffa663de`).

| ID | Blocking | Disposition | Evidence in revision 3 |
|---|---|---|---|
| IM-14-F01.1 | **Yes** | Fixed | L732-739 (scope rule: listed artifacts of each shipped unit plus every added or modified path in the shipment's diff against its base; a missing listed path or an unscanned listed or diffed path fails); L724-729 (table adds `.github/workflows/ci.yml`, `schema_contracts.py`, `verify_workspace.py`, the manifest, the Ship template and mirror); L190 (IM-14 row, B3 added); audit test in Files of C5, B1, B3, B5, D1, D2, D4 (L322, L361, L383, L416, L432, L443, L466) |
| IM-14-F05 | **Yes** | Fixed | L742-746 (`\b`-anchored patterns, `\w*` after every stem and after race, TOCTOU and hardlink); L750-753 (positive controls include `resistant to race` and `protects against TOCTOU`) |
| IM-14-F06 | No | Fixed | L750-753 (negative controls `trace-free`, `embrace-safe`, the required sentence) |
| IM-14-F07 | No | Fixed | L737-739 (C5's first run audits A retroactively; B3 puts B-core's modules in scope before S(B-core) closes); L385 |
| IM-03-F02 | No | Fixed | L179 (IM-03 row); L418 (B5: all 47 codes through `_resolve`, defaults-reachable codes through `resolve_shipment` and the CLI) |
| IM-03-F03 | No | Fixed | L363 (pinned SHA-256 over LF-normalized bytes; no `.gitattributes` change) |
| IM-11-F02 | No | Fixed | L498-501 (each shipment its own feature; closes on the classifier verdict, never `shipment ship` over part of a feature); L507 |
| IM-11-F03 | No | Fixed | L761 (no release tag includes S(B-core) before S(B-entry) closes; a B-entry-found defect reverts B-core, never `1.1.0`) |
| IM-07-F04 | No | Fixed | L433 (capture files under Git-ignored `.proof-scratch/harness-resolve/`, deleted after the entry returns); L444 (D2 asserts path and cleanup) |
| IM-16-F02 | No | Fixed | L406 (`_resolve` returns the result and `ReadUsage` privately); L374 (B2 reads usage from the reader it passes in) |
| IM-13-F03 | No | Fixed | L166-168 (structural tests recorded outside the roster) |
| IM-10-F01.1 | No | Fixed | L562 (PD-12 gates S(D)); L576 (S(D) not harvested or claimable; A, C and B inert); L691 (S(D) not claimable; D3 preflight (4) re-checks) |
| IM-06-F01.1 | No | Fixed | L265 (no other module function patched; counters only spy on `os.path.realpath` and `os.open`) |
| IM-04-F01.1 | No | Fixed | L407 (lower-class fact first in encounter and task-ID order) |
| NOROW-F11.1 | No | Fixed | L498-501 |
| NOROW-F12.1 | No | Fixed | L598 (procedure-text rationale; anchor refresh in a separate evidence-only commit) |
| NOROW-F13 | No | Fixed | L143 (one header) |
| NOROW-F14 | No | Fixed | L383 (`verify_workspace.py` in Files); L385 (alias identity test) |
| NOROW-F15 | No | Fixed | L600-601 (B-core and B-entry rows) |
| NOROW-F16 | No | Accepted as-is | Advisory. The alias stays (PD-09) |
| NOROW-F17 | No | Resolved by ruling | Orchestrator growth ruling above |
| NOROW-F03 | No | Deferred (reaffirmed) | Unchanged from consolidated revision 1; deferral accepted by Scope |

Totals: 19 fixed (both blocking), 1 accepted as-is, 1 resolved by
ruling, 1 deferred. No finding declined.

## Delta Review 2 (subject revision 3)

```text
dispatch_mode: multi-agent
dispatch_route: explicit-model gpt-6-sol, dispatcher Orchestrator
decision: REVISE
```

The same seven reviewer agents checked revision 3 (blob `ffa663de`)
against changes only.

| Persona | Route | Decision |
|---|---|---|
| Architecture Strategist (lead) | `gpt-6-sol` | PASS |
| Agent-Native Parity Reviewer | `gpt-6-sol` | PASS |
| Python reviewer | `claude-opus-5.5` | PASS |
| Security Lens Reviewer | `gpt-6-sol` | REVISE |
| Scope reviewer | `claude-opus-5.5` | REVISE |
| Constitution Reviewer | `claude-opus-5.5` | REVISE (corroborating Security only) |
| Learnings reviewer | `claude-opus-5.5` | REVISE |

**Closed on named revision 3 evidence.** IM-14-F01, IM-14-F01.1,
IM-14-F05, IM-14-F06, IM-03-F02, IM-03-F03, IM-06-F01.1, IM-16-F02,
IM-13-F03, IM-11-F02, IM-11-F03, IM-04-F01.1, IM-10-F01.1, IM-07-F04,
NOROW-F11.1, NOROW-F12.1, NOROW-F13, NOROW-F14, NOROW-F15, NOROW-F16
(accepted as-is) and NOROW-F17 (resolved by ruling). IM-14-F07 is closed
in part; its residue is IM-14-F07.1. NOROW-F03 stays open and deferred,
with the deferral accepted.

### Open Blocking Findings (IM-14 / `PE-SAFETY-06`, `P2-critical`)

| ID | Raised by (confidence) | Revision 3 lines | Summary |
|---|---|---|---|
| IM-14-F07.1 | Scope (8); Learnings concurs (8) | L190, L726, L730, L732-739; A1/A2 Files (L222, L233) | A1 and A2 modify `tests/test_harness_architect_p004_contract.py`, which inventory row A omits. C5's retroactive run scans A's listed artifacts, not S(A)'s diff. Row "All" says carriers are checked at harvest by the same scan, but harvest precedes C5, so that scan does not exist yet |
| IM-14-F08 | Security (8.4); Constitution corroborates (7) | L730-738 | The exemption covers whole files that quote the patterns (audit test, plan, review manifest), so their remaining prose is never scanned. The wording reads as a property-based class, not a closed list. Revision 3 also dropped the earlier IM-14-F03 guard (plan history avoids claim forms). Remedy: a closed three-path list asserted by the test that exempts only literal pattern declarations and fixtures, with the rest scanned |
| IM-14-F11 | Learnings (7) | L742-752 | The patterns miss claims with an intervening word or compound: `race-condition-free`, `race condition safe`, `guards against a TOCTOU race`, `protects against the race`, `prevents a race`, `free of race conditions`, `safe from TOCTOU`, `provides TOCTOU resistance`. Same class as IM-14-F05, which was ruled blocking. IM-14-F10 covers the reversed-order subset |

### Non-Blocking New Findings

Carried to the next epoch or to harvest. Two findings are below the
confidence threshold and are informational only.

| ID | Raised by (confidence) | Sev | Status | Summary |
|---|---|---|---|---|
| IM-14-F09 | Python (8) | P2 | Open | How the audit base reaches the test under `unittest discover` is unnamed (for example an `AHLC_AUDIT_BASE` variable). Closure and D3 must show the base is set, and fail closed otherwise |
| IM-14-F10 | Python (7) | P3 | Open | Reversed-order claims ("free of race conditions", "safe from TOCTOU") |
| IM-14-F12 | Learnings (7) | P3 | Open | The Ship template and mirror are added to the inventory "at D3 preflight", but D3 is frozen-scope and D4 is deferrable. D2 should add them |
| IM-14-F13 | Learnings (6) | — | **Informational** (below threshold) | Renames and copies (`R`, `C`) escape an added-or-modified diff filter |
| IM-14-F14 | Python (IM-14-F08, 7); Scope (IM-14-F09, 7) | P2/P3 | Open | Whole pre-existing files are now listed with no baseline scan; negations give false positives; no rule for pre-existing hits outside freeze scope |
| IM-14-F15 | Scope (IM-14-F08, 7) | — | Open | Exemption wording as a class versus a closed list (overlaps IM-14-F08) |
| IM-16-F02.1 | Python (7) | P3 | Open | B2's usage observation implies an unnamed private helper that accepts a reader |
| CONST-II-F01 | Constitution (7) | P2 | Open | Structural tests "may pass": record the pre-implementation failing run as gap characterization (Principle II evidence) |
| CONST-VII-F01 | Constitution (6) | — | **Informational** (below threshold) | Deletion scope and overwrite behavior of the capture cleanup |
| CONST-G2-F01 | Constitution (8) | P3 | Open | The plan lost its final newline (MD047); one byte |
| NOROW-F18 | Parity (8) | P3 | Open | `.proof-scratch/` is ignored here but not guaranteed in installed workspaces; verify the ignore rule before writing |
| NOROW-F19 | Scope (7) | P3 | Open | The C3 record said four features; the plan now has five. Add a trace note |

## Epoch Stop

```text
decision: EPOCH_STOPPED
publication: not met
harvest: not permitted
```

| Field | Value |
|---|---|
| Epoch | `LIFECYCLE-E2-R1-2d562820` |
| Last subject | Plan revision 3, commit `bd7002d5`, blob `ffa663de030a0a07baa5b62ea1078b750a0a4009` |
| Consolidated revisions used | 2 of 2 |
| Blocking trend | 7 (initial review) -> 2 (after revision 2) -> 3 (after revision 3) |
| Stop conditions triggered | "Blockers do not decline across revisions" (2 -> 3) and "a second remediation fails" |
| Publication gate | **Not met** |
| Harvest | Nothing harvested. Harvest reads its verdict from this manifest under OP-5, and `EPOCH_STOPPED` is not `PASS`, so it fails closed |
| Plan revisions after the stop | None. No revision 4 and no local fix |

**Where the blockers are.** All three open blockers are confined to the
IM-14 non-claim audit surface: the C5 audit test, the inventory, the
pattern set and the exemptions. Every other part of units A, C, B-core,
B-entry and D converged, with no open P0 or P1 and no other open
matrix-critical P2.

**Permitted outcomes (operator decision pending).** Split, spike,
re-charter or new epoch, explicit risk acceptance, defer, or cancel. No
outcome is chosen here.

**Orchestrator recommendation.** A time-boxed spike on the IM-14 audit
mechanism, designing a bounded, closed detector instead of an open-ended
regex net:

1. Scope from diff hunks.
2. Closed path and line exemptions.
3. A fixed claim vocabulary with a mandatory recorded non-claim
   attestation.

Then a new epoch E3 scoped to the IM-14 audit section only, with revision 3
as its baseline and every other section frozen.

### Operator Decision

```text
decided_at: 2026-09-25T20:47:56-07:00
outcome: spike
verdict: EPOCH_STOPPED (unchanged)
harvest_permitted: false (unchanged)
```

The operator chose **spike** from the permitted outcomes: a spike to
redesign the IM-14 non-claim audit. Rationale, quoted: "A misaligned audit
will only become a long-term continuous nuisance to the development
workflows."

**Next.** After the operator ratifies the spike, a new epoch E3 opens,
scoped to the IM-14 audit section only. Its baseline is plan revision 3
(blob `ffa663de030a0a07baa5b62ea1078b750a0a4009`), and every other section
stays frozen. Until then the verdict stays `EPOCH_STOPPED` and harvest
stays blocked.

### Operator Ratification of the IM-14 Spike

```text
decided_at: 2026-09-25T21:10:37-07:00
subject: docs/decisions/2026-09-26-im14-non-claim-audit-redesign-spike.md (commit 27bcc254)
verdict: EPOCH_STOPPED (unchanged for E2)
harvest_permitted: false (unchanged)
```

The operator's three rulings, as relayed verbatim by the Orchestrator:

1. "Design RATIFIED (O2/O3 hybrid as specified in the spike's drop-in
   section)."
2. "E3 scope widened as recommended: E3 may also align C5's Change cell
   (plan rev 3 L323, incl. its CI module list) with the new section."
3. "Manual coverage of the plan and its review manifest ACCEPTED", with
   this operator clarification, quoted: "it is not my intention that all
   plan and review records should be manually reviewed, which would be
   onerous for the operator."

**Binding interpretation of ruling 3.** The "text audit" for the residue
is performed by an agent: a review persona in E3, and Ship at harvest and
at each closure. It is recorded as a disposition with the `LEDGER` count.
The operator is not a required participant. It covers only this release's
IM-14 residue: this plan, this review manifest and the final closure pull
request, as the spike lists. It creates no standing obligation to review
plan or review records generally.

## Epoch LIFECYCLE-E3 (IM-14 audit)

```text
epoch: LIFECYCLE-E3-703d0de1
opened_by: operator ratification 2026-09-25T21:10:37-07:00
subject: plan revision 4, commit 48cafb4a, blob 703d0de11fa5515a4abba0146d2f792bbe9991a6
baseline: plan revision 3, commit bd7002d5, blob ffa663de030a0a07baa5b62ea1078b750a0a4009
verdict: pending
harvest_permitted: false
```

| Field | Value |
|---|---|
| Scope (open) | The plan's "Non-Claim Audit Inventory" section; C5's Change cell, including its CI module list; any IM-14 or `PE-SAFETY-06` trace-row text (for example the IM-14 row at revision 3 line 190) that would otherwise contradict the new section; and the final-newline fix CONST-G2-F01 |
| Frozen | Everything else, at revision 3 |
| Design source | The ratified spike's drop-in specification, with ruling 3's binding interpretation folded in |
| Rubric, personas and routes | Unchanged from E2 (rulings 5, `2ca9d9a5`). Lead Architecture Strategist, Security Lens and Parity on `gpt-6-sol` / `openai` / `high`. Constitution, Python, Scope and Learnings on the caller route |
| Cadence | One initial review of the scoped changes, then delta reviews, then one final full consistency pass |
| Budget | At most 2 consolidated revisions |
| Blocking rule | C4 unchanged: only matrix-critical `P2` blocks, besides `P0` and `P1` |
| Growth | Still cumulative against revision 1 blob `2d562820`: body bytes, file bytes and words each at most 20% over revision 1 |
| E2 | Verdict stays `EPOCH_STOPPED`, and `harvest_permitted` stays `false` |
| E3 verdict | `EPOCH_STOPPED` after delta review 1 (see [E3 Epoch Stop](#e3-epoch-stop)); publication not met; `harvest_permitted` stays `false` |

### Revision 4 (E3 subject)

| Field | Value |
|---|---|
| Epoch token | `LIFECYCLE-E3-703d0de1` (first 8 hex of the revision 4 blob) |
| Subject | Plan revision 4, commit `48cafb4a`, blob `703d0de11fa5515a4abba0146d2f792bbe9991a6`, 832 lines |
| Changed body lines (revision 4 numbering) | 190 (IM-14 trace row); 323 (C5 Change cell and CI module list); 454 (D3 preflight item 6); 719-761 (Non-Claim Audit Inventory section); 832 (final LF, CONST-G2-F01) |
| Changed frontmatter lines | 2-3 (title, description), 10 (`revision: 4`), 12-13 (`prior_revision`, `review_epoch`), 15-16 (epoch family and token rule), 21 (`hardening_pass`) |
| Not changed | Every other line, frozen at revision 3. No task, reason code, public name, subsystem or threat class added |
| Growth against revision 1 (`2d562820`) | File bytes 82261 (+18.94%, limit 82995); body bytes 76372 (+19.75%, limit 76533); words 12076 (+18.42%, limit 12237) |

## E3 Initial Review

```text
epoch: LIFECYCLE-E3-703d0de1
subject: plan revision 4, commit 48cafb4a, blob 703d0de11fa5515a4abba0146d2f792bbe9991a6
scope: changes only (E3-open regions)
decision: REVISE
```

| Persona | Route | Decision |
|---|---|---|
| Architecture Strategist (lead) | `gpt-6-sol` | REVISE |
| Security Lens Reviewer | `gpt-6-sol` | REVISE |
| Agent-Native Parity Reviewer | `gpt-6-sol` | REVISE |
| Constitution Reviewer | caller route (`claude-opus-5.5`) | REVISE |
| Python reviewer | caller route (`claude-opus-5.5`) | REVISE |
| Scope reviewer | caller route (`claude-opus-5.5`) | REVISE |
| Learnings reviewer | caller route (`claude-opus-5.5`) | REVISE |

**Closed by construction (all seven agree).** The E2 blockers
IM-14-F07.1, IM-14-F08 and IM-14-F11; also IM-14-F09, IM-14-F10,
IM-14-F12, IM-14-F13, IM-14-F14, IM-14-F15 and CONST-G2-F01 (final LF).
`AUDITED` and `LEDGER` are test-local constants, not public names. No
new task, reason code, public name, subsystem or threat class. Anchors
and Markdown intact. The Python reviewer recorded its share of the
agent residue text audit: the scoped revision 4 sections contain no
resistance claim; `LEDGER` count n/a.

### Findings (stable IDs)

Reviewer IDs collided, so Stage assigned stable IDs. Line references are
to revision 4.

| Stable ID | Raised by (confidence) | Blocking | Revision 4 lines | Summary |
|---|---|---|---|---|
| IM-14-F16 (E3-B1) | Lead F16 (9); Learnings F16 (8); Scope F16 (8); Constitution CONST-E3-F01 (8); Python E3PY-03 (8) | **Yes** | L190, L323, L454, L725-729, L739-744 | `LEDGER` timing deadlock: tasks add entries for their own lines, but non-floor lines are scanned only once a later closure lists the merge, so the unused-entry rule turns every shipment's own CI red from C5 on |
| IM-14-F17 (E3-B2) | Parity F17 (8); Learnings F17 (7); Scope F20 (P3); Constitution CONST-E3-F04 (P3) | **Yes** | L750-757 | Residue text audit not executable: who audits what, where it is recorded, "Ship at harvest" when harvest is Stage-owned (P-010), and the meaning of the `LEDGER` count before C5 |
| IM-14-F18 (E3-B3) | Parity F16 (9) | **Yes** | L454, L724-749 | D3's activation edit is unexamined before merge: it is listed only at a later closure and the Ship surfaces are not floor files |
| IM-14-F19 (E3-B4) | Security F16 (9); Python E3PY-01 (8); Learnings F22 (P3) | **Yes** | L733-740, L757-761 | Detector token-boundary escapes: `TOC-`/`TOU` across lines, snake_case (`test_toctou_safe`, `race_free`, `RACE_SAFE`), `hard-linked` and `hard linking`, `TOCTOUs` and `TOCTTOU` |
| IM-14-F20 (E3-B5) | Python E3PY-02 (8); Scope F17 (7); Learnings F20 (P3); Constitution CONST-E3-F02 (P3) | **Yes** | L735-751 | Pair-hit clearing undefined: clearing checks "its line", a pair's hash is undefined, the required sentence may wrap, and the pair control asserts a hit rather than a failure |
| IM-14-F21 (E3-N1) | Lead F17 (P2, 9); Constitution CONST-E3-F05 (P3) | No | L725-729, L745-748, L323 | No post-S(D) switch to the floor-only check, so git scan, unshallow and historical fail-on-skip persist forever |
| IM-14-F22 (E3-N2) | Learnings F18b; Scope F21; Python E3PY-06a; Constitution CONST-E3-F05 | No | L323 | `git fetch --unshallow` fails on a full clone under `set -e`; guard with `git rev-parse --is-shallow-repository` |
| IM-14-F23 (E3-N3) | Learnings F19; Scope F18; Constitution CONST-E3-F02; Python E3PY-04/05 | No | L730-731 | Diff and hash determinism: `--no-color --no-ext-diff --no-textconv`, bytes, strict UTF-8, CR strip, hash without diff marker, hunk-state header parsing, fail a listed commit with no added line |
| IM-14-F24 (E3-N4) | Learnings F21; Scope F19; Constitution CONST-E3-F03 | No | L725-729 | `AUDITED` composition: S(C)'s closure re-appends S(A)'s closure merge; multi-commit harvests and multi-merge shipments |
| IM-14-F25 (E3-N5) | Learnings F18a, F18c | No | L741-748 | Unused-entry check only after a full scan; assert each listed SHA is an ancestor of the default branch |
| IM-14-F26 (E3-N6) | Python E3PY-06b (6) | — | L323 | **Informational** (below threshold): the coverage module is not in the CI module list |
| NOROW-F19 (E3-N7) | Scope NOROW-F19 (P3) | No | frozen (C3 note) | Four versus five features trace note; outside E3 scope |

## E3 Consolidated Revision 1 (subject revision 5)

| Field | Value |
|---|---|
| Subject | Plan revision 5, commit `01cb89b9`, blob `057a7615a5a53e53698bb53604ad7fba5382e744`, 836 lines, LF, final newline |
| Revisions used | 1 of 2 |
| Author | Stage (`claude-opus-5.5` / `anthropic` / `high`) |
| Changed body lines (revision 5 numbering) | 190 (IM-14 trace row); 323 (C5 Change cell); 721-765 (Non-Claim Audit Inventory, from revision 4 lines 721-761) |
| Changed frontmatter lines | 3 (description: revision 5 sentence), 10 (`revision: 5`), 12 (`prior_revision` revision 4, `48cafb4a`, `703d0de1`) |
| Not changed | Every other line, including D3 preflight item 6 (line 454), which claims no scan of a future commit. No task, reason code, public name, subsystem or threat class added |
| Review state | Pending delta review of the changes, then the final full consistency pass |

### Contract Growth (revision 1 versus revision 5)

Offsets came only from compressing the E3-open regions; the new detector
pattern is shorter than the one it replaces.

| Measure | Revision 1 | Revision 4 | Revision 5 | Limit | Growth |
|---|---:|---:|---:|---:|---:|
| File bytes | 69163 | 82261 | 82440 | 82995 | +19.20% |
| Body bytes (after frontmatter) | 63778 | 76372 | 76533 | 76533 | +19.999% (at the limit) |
| Words | 10198 | 12076 | 12091 | 12237 | +18.56% |
| Tasks | 17 | 17 | 17 | 20 | 0% |
| Reason codes / `ReadErrorCode` values | 47 / 8 | 47 / 8 | 47 / 8 | unchanged | 0% |
| New public names | none | alias only | alias only | unchanged | unchanged |
| Lines (not a limit) | 769 | 832 | 836 | none | +8.7% |

### Dispositions

Line references are to revision 5 (blob `057a7615`).

| ID | Blocking | Disposition | Evidence in revision 5 |
|---|---|---|---|
| IM-14-F16 | **Yes** | Fixed | L728-732 (C5 seeds `AUDITED` through S(A)'s closure; each closure appends what landed since; both add `LEDGER` entries for hits in the lines they newly audit, confirmed by local review; tasks ledger only floor hits); L745-746 (unused entry fails only after a full scan); L190 (closures extend `AUDITED` and `LEDGER`) |
| IM-14-F17 | **Yes** | Fixed | L753-760 (agent-performed, release-scoped, no operator duty; E3 persona audits plan and manifest, recorded here; Ship audits read-only the harvest commits before claiming S(A) in its session note with `LEDGER` n/a, each shipment's merge diff at its closure, the last also its pull request, in the closure note with the `LEDGER` count; Ship writes no planning or review artifact) |
| IM-14-F18 | **Yes** | Fixed | L758-760 (before D3 is presented ready, Ship audits D3's added template and mirror lines, recorded in the readiness record); L454 unchanged and claims no future-commit scan |
| IM-14-F19 | **Yes** | Fixed | L739-742 (`_` and `-` as spaces, whitespace collapsed; pair joined by a space or else with a trailing hyphen dropped; compact pattern with `rac` inflections, `toctt?ous?`, `time of check`, `hard ?link\w*` and `symlink ?swap\w*`, shorter than revision 4's); L761-765 (controls `race_free`, `test_toctou_safe`, `TOCTTOU`, `hard-linked`, `TOC-`/`TOU`; negatives `trace-free`, `embrace-safe`, `grace period`). Stage re-checked the stated rule against all listed controls, `TOCTOUs`, `hard linking`, `RACE_SAFE`, `racetrack` and `trace_id`, and the required sentence |
| IM-14-F20 | **Yes** | Fixed | L740-746 (pairs only where neither line hits; "line or pair" in the clearing clause; the hash is of that normalized unit, the line or the join that hit; the floor uses the same rule, L736-738); L750-752 (required sentence on one physical line); L761-763 (split-pair controls listed under "Must fail") |
| IM-14-F21 | No | Fixed | L731-733 (S(D)'s closure, after its full scan, marks the list final; then only the floor runs); L733 and L749 (git scan and fail-on-skip only until final); L323 (unshallow only until `AUDITED` is final) |
| IM-14-F22 | No | Fixed | L323 (`git fetch --unshallow` only if `git rev-parse --is-shallow-repository` prints `true`) |
| IM-14-F23 | No | Fixed in part; rest deferred to C5 implementation | L734-736 (`--no-ext-diff --no-textconv`; a listed commit with no added line fails). Deferred for the body-byte budget (0 bytes of headroom): `--no-color`, byte capture with strict UTF-8, CR strip, hashing without the diff marker stated explicitly, and hunk-state header parsing. These are implementation mechanics of C5's test and do not change the contract |
| IM-14-F24 | No | Fixed | L726-729 (each commit or merge landing the harvest, a shipment or a closure, listed once; each closure appends what landed since). The closure-time assertion that none is missing is left to C5 implementation |
| IM-14-F25 | No | Fixed | L745-746 (unused-entry check only after a full scan); L727-728 (each listed commit asserted an ancestor of the base branch) |
| IM-14-F26 | — | Informational; carried to harvest | No change (below threshold). Harvest records the coverage module's absence from the C5 CI module list |
| NOROW-F19 | No | Carried to harvest | Outside E3 scope (frozen C3 note) |

Totals: 5 blocking fixed; 4 non-blocking fixed and 1 fixed in part with
the rest deferred; 1 informational and 1 out-of-scope finding carried to
harvest. No finding declined.

## E3 Delta Review 1 (subject revision 5)

```text
epoch: LIFECYCLE-E3-703d0de1
subject: plan revision 5, commit 01cb89b9, blob 057a7615a5a53e53698bb53604ad7fba5382e744
dispatch_mode: multi-agent, dispatcher Orchestrator
scope: changes only
decision: REVISE
```

| Persona | Reviewer session | Route | Decision |
|---|---|---|---|
| Architecture Strategist (lead) | E3 lead session | `gpt-6-sol` | REVISE |
| Agent-Native Parity Reviewer | E3 parity session | `gpt-6-sol` | REVISE |
| Constitution Reviewer | E3 constitution session | `claude-opus-5.5` | REVISE |
| Security Lens Reviewer | `1f0fd656` (replaces `c5d5b001`) | `gpt-6-sol` | REVISE |
| Python reviewer | E3 python session | `claude-opus-5.5` | PASS |
| Learnings reviewer | E3 learnings session | `claude-opus-5.5` | PASS |
| Scope reviewer | `8ab6cc56` (replaces `515ac98b`) | `claude-opus-5.5` | PASS |

**Reviewer replacement (not a route change).** The original Security
session `c5d5b001` ran out of context and returned nothing, and the
original Scope session `515ac98b` ran out of context with an unverified
REVISE. Neither result is counted. Each was replaced by a fresh session
of the same persona on the same model (`1f0fd656`, `gpt-6-sol`;
`8ab6cc56`, `claude-opus-5.5`). Persona, rubric and route are unchanged,
so the "reviewer route changes mid-epoch" stop condition does not apply.
Scope's frozen-region check was clean: revision 5 changes only the
E3-open regions.

**Closed on revision 5 evidence.** All five initial E3 blockers:
IM-14-F16, IM-14-F17, IM-14-F18, IM-14-F19 and IM-14-F20. The Lead
closed F16 and F21 but reads F17 as still open, and Security reads F20
as closed only in part. Those residues are admitted below as the new
IM-14-F27 and IM-14-F30, not counted as reopened findings. Also closed:
IM-14-F21, IM-14-F22 and IM-14-F25. The IM-14-F23 and IM-14-F24
deferrals were accepted by Lead, Parity (advisory), Constitution,
Python, Learnings and Scope, but rejected by Security, whose rejections
are admitted as IM-14-F32 and IM-14-F33.

### New Blocking Findings (IM-14 / `PE-SAFETY-06`, `P2-critical`)

| Stable ID | Raised by (confidence) | Sev | Revision 5 lines | Summary | Proposed remedy |
|---|---|---|---|---|---|
| IM-14-F27 | Lead (residue of F17, 8) | P2 | L753-760 | The E3 reviewer audits the plan and manifest as they were during E3, but both change later. Ship's harvest and closure audits cover harvest commits and shipment diffs, not the plan and manifest as they stand then | At harvest and at each closure, Ship audits the plan and manifest as they stand then, recording the disposition and the `LEDGER` count |
| IM-14-F28 | Parity IM-14-F21.1 (9); Constitution CONST-E3-F07 (P3, duplicate) | P2 | L732-746 | After the list is final only the floor runs, but the unused-entry rule would then fail every non-floor `LEDGER` entry (for example S(C)'s fixture entries), so the canonical test goes permanently red | In final mode, apply the unused-entry check to floor entries only, or have S(D)'s closure keep only floor entries |
| IM-14-F29 | Constitution CONST-E3-F06 (7) | P2 | L725-728 | "Each commit or merge landing the harvest" includes the merge of the harvest PR, whose first-parent diff is the whole branch (charter, proofs, spike, plan, manifest). That means hundreds of hits for C5 to ledger, contradicting the ratified "0 pre-existing surfaced" | List the harvest commit itself (`sha^1 sha` = the harvest's own lines) and each merge that lands a shipment or closure |
| IM-14-F30 | Security SEC-1 (0.96); Python F28py (P3, duplicate) | P2 | L739-746 | Pairs are scanned only when neither line hits. A line holding the required sentence plus `TOC-` clears on its own, and a next line `TOU resistance` has no hit, so that pair is never scanned: an escape | Scan every adjacent pair, or pairs where neither line has an uncleared hit, with a control for this case |
| IM-14-F31 | Security SEC-2 (0.93) | P2 | L743-746 | A `LEDGER` entry is keyed only by the normalized unit's hash and a label, so a `fixture` entry also clears an identical claim on a production path | Bind each entry to its path (or occurrence) as well as its hash |
| IM-14-F32 | Security SEC-3 (0.88) | P2 | L734-746 (IM-14-F23 deferral) | Deferring determinism is not acceptable: the hash is a contract that must match across hosts | The plan must state the contract: raw bytes with `--no-color`; strict UTF-8, else fail; hunk-aware CR and marker strip; raw pair join with the trailing hyphen dropped, then `_`/`-` to space and whitespace collapsed; SHA-256 of the UTF-8 bytes |
| IM-14-F33 | Security SEC-4 (0.81) | P2 | L725-732 (IM-14-F24 deferral) | Deferring the completeness check is not acceptable | Before the final marker, the closure independently lists the landing commits, compares that list exactly with `AUDITED`, and refuses the final marker on any omission |

Constitution also rated IM-14-F20 and IM-14-F23 partial but acceptable.

### Non-Blocking Findings (carried to the next epoch or to harvest)

| Stable ID | Raised by | Sev | Revision 5 lines | Summary |
|---|---|---|---|---|
| IM-14-F34 | Python F27py | P3 | L739-742 | Normalization order: map `_` and `-` to space after the hyphen-dropped pair join (a 0-byte swap) |
| IM-14-F35 | Python F29py | P3 | L739-742 | camelCase claims (for example `raceFree`) remain residue |
| IM-14-F36 | Learnings F27l | P3 | L323, L733, L747-749 | After the list is final the git scan is absent, not skipped; drop "Until `AUDITED` is final" from L323 to pay for it |
| IM-14-F37 | Learnings F28l | P3 | L753-755 | Bind the E3 reviewer's audit to the blob that passes the final full consistency pass (harvest carry) |
| IM-14-F38 | Scope | P3 | L731-732 | S(D)'s final full scan is never CI-verified; record the pre-final result, or mark final in a separate commit |
| IM-14-F39 | Scope | P3 | L756-760 | "Readiness record" and "session note" must name existing Ship record types |
| IM-14-F40 | Scope | P3 | L734-736 | CR-strip residual: `.gitattributes` does not pin `src/*.py` to LF |
| IM-14-F41 | Parity IM-14-F24.1 (partial) | P3 | L726 | The final closure's own landing cannot be listed in `AUDITED` (it would be self-referential); say that its recorded text audit covers it |
| IM-14-F26 | Python E3PY-06b (re-raised) | P3 | L323 | The coverage module is not in the CI module list (carried to harvest) |

Advisory notes, no ID: Learnings would accept the IM-14-F24 deferral
only as a harvest carry into each closure carrier (list the first-parent
merges since the last listed commit and record exclusions), and the
IM-14-F23 deferral only with a C5 control that `++ race-free` must fail.
Python suggests C5 check ancestry red-first. NOROW-F19 stays carried to
harvest.

## E3 Epoch Stop

```text
epoch: LIFECYCLE-E3-703d0de1
decision: EPOCH_STOPPED
publication: not met
harvest: not permitted
operator_decision: pending
```

| Field | Value |
|---|---|
| Last subject | Plan revision 5, commit `01cb89b9`, blob `057a7615a5a53e53698bb53604ad7fba5382e744` |
| Consolidated revisions used | 1 of 2 |
| Blocking trend | 5 (initial review of revision 4) -> 7 (delta review 1 of revision 5) |
| Findings closed versus admitted | 5 blocking closed; 7 new blocking admitted |
| Stop conditions triggered | "Blockers do not decline across revisions" (5 -> 7) and "newly admitted findings are at least as many as findings closed" (7 >= 5), per the convergence-reset deliberation (`docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md`, stop conditions) |
| Growth headroom | Body bytes 76533 of 76533 (0 bytes left); file bytes 82440 of 82995; words 12091 of 12237 |
| Publication gate | **Not met** |
| Harvest | Nothing harvested. Harvest reads its verdict from this manifest under OP-5, and `EPOCH_STOPPED` is not `PASS`, so it fails closed |
| Plan revisions after the stop | None. "Another attempt is not a permitted outcome", so there is no revision 6, and the second consolidated revision goes unused |
| E2 | Unchanged: `EPOCH_STOPPED` |

**Where the blockers are.** All seven open blockers are again confined
to the IM-14 non-claim audit: which commits are listed and whether that
list is complete (IM-14-F29, IM-14-F33); the final mode and the ledger
(IM-14-F28, IM-14-F31); pair coverage (IM-14-F30); the hash contract
(IM-14-F32); and residue coverage of the current plan and manifest
(IM-14-F27). No P0, P1 or other matrix-critical P2 is open elsewhere.
Body bytes have no headroom left, so any in-plan remedy would need
cuts elsewhere or a growth ruling.

**Permitted outcomes (operator decision pending).** Split, spike,
re-charter or new epoch, explicit risk acceptance, defer, or cancel. No
outcome is chosen here.

## Operator Re-charter of the IM-14 Audit (E3 outcome)

```text
at: 2026-09-25T22:29:53-07:00
outcome: re-charter / new epoch (LIFECYCLE-E4)
```

**Ruling (verbatim).** "Re-charter the IM-14 audit. F29 is concerning
in that it seems like it would significantly grow the transcript on
each new audit. Once something has already passed an audit, it should
be checked off the audit list UNLESS a DAG dependency of a new commit
would be impacted or implicated by the changes in the commit."

| From spike `27bcc254` | Status |
|---|---|
| History scan: the closed `AUDITED` commit list, the `git diff` scan, the CI unshallow, the final-marker transition | **Superseded** |
| Closed trigger vocabulary and detector | Retained |
| Digest `LEDGER` in the test | Retained, now keyed to `(path, SHA-256)` |
| Required sentence | Retained |
| Agent text audit for residue; no operator duty | Retained, now incremental |

**Orchestrator interpretation of "checked off" (an interpretation; the
operator may correct it).** The audit is incremental and never re-reads
what has already passed.

* Each unit is audited once: the harvest commit or commits themselves
  (their own `<sha>^1 <sha>` diff, never the whole-branch merge of the
  harvest pull request), the added lines of each shipment's own merge
  diff, D3's prepared template and mirror added lines (before D3 is
  presented ready), and the final closure pull request's added lines.
  Once dispositioned, a unit is checked off (recorded once: commit SHA,
  disposition and, where it applies, the `LEDGER` count) and later
  closures do not re-audit it.
* Exception (re-open): a checked-off unit is audited again only when a
  later commit modifies its lines, or changes a DAG dependency that the
  unit describes or relies on (for example a surface, module or
  contract whose behavior the audited text states), so that the prior
  text could now become or imply a resistance claim. The auditing agent
  names the implicated units and audits only their affected lines.
* The automated floor check is a deterministic unit test over three
  small files. It runs in CI on every run but produces no agent
  transcript and no growing record, so it is not an "audit list" in the
  operator's sense.

## Epoch LIFECYCLE-E4 (IM-14 audit, re-chartered)

```text
epoch: LIFECYCLE-E4-5cf1d52a
opened_by: operator re-charter 2026-09-25T22:29:53-07:00
subject: plan revision 6, commit 33ad886b, blob 5cf1d52a48840d43aacfe8795b9b6ceba8d7f809, derived from revision 5 (commit 01cb89b9, blob 057a7615a5a53e53698bb53604ad7fba5382e744)
verdict: pending
harvest_permitted: false
```

| Field | Value |
|---|---|
| Scope (open) | The Non-Claim Audit Inventory section; C5's Change cell (the unshallow clause is removed); the IM-14 row; D3 preflight item 6 and any Files cell listing `tests/test_harness_noclaim_audit.py`, each only if it now contradicts; frontmatter |
| Frozen | Everything else, at revision 5 |
| Design source | The re-chartered design (floor-only automated check; fixed reading, normalization and hash contract; pair matches that span the join; path-bound `LEDGER`; incremental agent text audit for residue), under the operator ruling above |
| Rubric, severity mapping, personas, routes | Frozen, unchanged from E2 and E3 (rulings 5, `2ca9d9a5`): only P0, P1 and matrix-critical P2 (IM-14, `PE-SAFETY-06`, `PE-SAFETY-07`) block. The same seven personas. Lead, Security and Parity on `gpt-6-sol`; Constitution, Python, Scope and Learnings on `claude-opus-5.5` |
| Reviewer sessions | Fresh sessions of the same persona and model; not a route change |
| Contract limits | No new task, reason code, public name, subsystem or threat class |
| Growth | Unchanged, cumulative against revision 1 blob `2d562820`: body bytes at most 76533, file bytes at most 82995, words at most 12237 |
| Budget | At most 2 consolidated revisions |
| Cadence | One initial review of the scoped changes, then delta reviews, then one final full consistency pass |
| Stop conditions | As in the convergence-reset deliberation (`docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md`, stop conditions); another attempt is not a permitted outcome on stop |
| Carried findings | E3's F26, F34 to F41 and NOROW-F19: disposed of in E4 where the re-charter makes them moot, otherwise carried to harvest |
| E2 and E3 | Verdicts stay `EPOCH_STOPPED`; `harvest_permitted` stays `false` |
| E4 verdict | `EPOCH_STOPPED` at the final full consistency pass (see [E4 Epoch Stop](#e4-epoch-stop)); publication not met; `harvest_permitted` stays `false` |

### Revision 6 (E4 subject)

| Field | Value |
|---|---|
| Epoch token | `LIFECYCLE-E4-5cf1d52a` (first 8 hex of the revision 6 blob) |
| Subject | Plan revision 6, commit `33ad886b`, blob `5cf1d52a48840d43aacfe8795b9b6ceba8d7f809`, 837 lines, LF, final newline |
| Changed body lines (revision 6 numbering) | 190 (IM-14 row); 323 (C5 Change cell: unshallow sentence removed, the rest verbatim); 721-766 (Non-Claim Audit Inventory) |
| Changed frontmatter lines | 2-3 (title, description), 10 (`revision: 6`), 12-13 (`prior_revision`, `review_epoch`), 15-16 (epoch family and token rule) |
| Not changed | D3 preflight item 6 (line 454; "passes with no skip" still holds, since the floor test has no skip path). Every Files cell, frozen: B1 and D1 still own the floor files; the cells of B2/B3, B5, D2 and D4 that list the audit test are now vestigial (their lines are residue units) but do not contradict. B1's and B3's Verification cells ("paths are added to the audit inventory") are outside E4 scope and read as the inventory section, not `FLOOR` |
| Contract limits | No task, reason code, public name, subsystem or threat class added. `FLOOR` and `LEDGER` are test-local constants |

#### Contract Growth (revision 1 versus revision 6)

| Measure | Revision 1 | Revision 5 | Revision 6 | Limit | Growth |
|---|---:|---:|---:|---:|---:|
| File bytes | 69163 | 82440 | 82363 | 82995 | +19.09% |
| Body bytes (after frontmatter) | 63778 | 76533 | 76498 | 76533 | +19.94% |
| Words | 10198 | 12091 | 12098 | 12237 | +18.63% |
| Tasks | 17 | 17 | 17 | 20 | 0% |
| Lines (not a limit) | 769 | 836 | 837 | none | +8.8% |

#### Rule Check (Stage, throwaway)

Stage ran a throwaway Python check of the rules as written at L729-742
against every control at L760-766. It covered the IM-14-F05, F10 and
F11 forms and `time-of-`/`check`, with the second line of each split
pair indented. All 29 cases matched: every must-fail case failed, and
the path-bound entry passed on its own path and failed on another. The
check also confirmed that invalid UTF-8 fails, that a CRLF copy yields
the same units as LF, that no negative hits, that the required sentence
hits and clears, and that an unused entry fails. Two wording choices
came from this check. The space join is tried first, so `time-of-` /
`check` is still caught. Whitespace at the hyphen join is dropped, so
an indented `TOU` still joins with `TOC-`.

#### E3 Findings Under the Re-charter

| ID | Disposition in revision 6 | Evidence |
|---|---|---|
| IM-14-F27 | Addressed | L751-758: the E4 persona audits the plan and manifest at the PASS blob; later edits land in harvest or closure commits, which are residue units |
| IM-14-F28 | Moot by construction | No final mode: `FLOOR` is fully scanned on every run and every entry must be used (L725-728, L738-742) |
| IM-14-F29 | Moot by construction | No `AUDITED` list or history scan; the harvest commits' own diffs are residue units, never the whole-branch merge (L753) |
| IM-14-F30 | Addressed | Every adjacent pair is checked, including after a cleared line; spanning matches only (L731-735); control at L763 |
| IM-14-F31 | Addressed | `LEDGER` is keyed to `(path, SHA-256)` (L739-740); control at L763-764 |
| IM-14-F32 | Addressed | Reading, normalization and hash contract fixed in the plan (L729-735); invalid UTF-8 and CRLF controls (L764-765) |
| IM-14-F33 | Moot by construction | No commit list and no final marker to complete |
| IM-14-F34 | Addressed | Raw join, then normalization (L731-734) |
| IM-14-F35 | Covered by the residue audit | camelCase in floor lines is reviewed in the shipment merge diffs (L746-757); carried to harvest as a C5 note |
| IM-14-F36 | Moot by construction | No git scan and no unshallow; the L323 clause is removed |
| IM-14-F37 | Addressed | E4 persona audit bound to the blob that passes the final full consistency pass (L751-753) |
| IM-14-F38 | Moot by construction | No final full scan |
| IM-14-F39 | Carried to harvest | Map "session note", "closure note" and "readiness record" to existing Ship record types |
| IM-14-F40 | Addressed | CR removed before normalization (L729-730); CRLF control |
| IM-14-F41 | Moot by construction | No `AUDITED`; the final closure pull request is a residue unit (L757) |
| IM-14-F26 | Carried to harvest | The coverage module is not in the C5 CI module list (cell frozen apart from the unshallow removal) |
| NOROW-F19 | Carried to harvest | Outside E4 scope |

## E4 Initial Review

```text
epoch: LIFECYCLE-E4-5cf1d52a
subject: plan revision 6, commit 33ad886b, blob 5cf1d52a48840d43aacfe8795b9b6ceba8d7f809
scope: changes only (E4-open regions); fresh reviewer sessions
decision: REVISE
```

| Persona | Fresh session | Route | Decision |
|---|---|---|---|
| Security Lens Reviewer | `f0eaa4a1` | `gpt-6-sol` | PASS |
| Architecture Strategist (lead) | `687d2cb2` | `gpt-6-sol` | PASS |
| Python reviewer | `fca7a513` | `claude-opus-5.5` | PASS |
| Agent-Native Parity Reviewer | `b466cc0a` | `gpt-6-sol` | REVISE |
| Scope reviewer | `5bb49836` | `claude-opus-5.5` | REVISE |
| Learnings reviewer | `296b2a2d` | `claude-opus-5.5` | REVISE |
| Constitution Reviewer | `a8c11c68` | `claude-opus-5.5` | REVISE |

**Closed or moot (unanimous).** The seven E3 blockers IM-14-F27 to
IM-14-F33. Learnings reads F27 as closed only in part; that residue is
IM-14-F43. Constitution's reading of F27 is IM-14-F46.

**Stop-condition check.** Blockers declined (7 -> 3), and the new
blockers (3) are fewer than those closed (7). Not triggered.

### Findings (stable IDs)

Line references are to revision 6.

| Stable ID | Raised by (confidence) | Sev | Blocking | Revision 6 lines | Summary and remedy |
|---|---|---|---|---|---|
| IM-14-F42 (E4-B1) | Parity E4-ANP-F01 (10) | P2 | **Yes** | L725-728 | `FLOOR` reads as requiring all three files at C5, but B1's and D1's files do not exist yet, so C5's CI goes red. Remedy: C5 lists `harness_read.py`, B1 adds `harness_surfaces.py`, D1 adds `harness_verdict.py`; a listed file missing fails |
| IM-14-F43 (E4-B2) | Scope E4-SBA-F01 (7); Learnings E4-LR-F01 (7) | P2 | **Yes** | L757 | Only the final closure pull request is a unit, so the closure pull requests of S(A), S(C), S(B-core) and S(B-entry) go unaudited. Remedy: each closure pull request is a unit, recorded where it is not circular (its body, which is not in its own diff) |
| IM-14-F44 (E4-B3) | Constitution E4-CR-F01 (8) | P2 | **Yes** | L746 | "Everything outside `FLOOR`" drops claims inside floor files that the detector cannot see (`raceFree`, `isTOCTOUSafe`, "cannot be swapped between check and use"), contradicting the E3 F35 disposition. Remedy: residue also covers claims the test misses inside `FLOOR` |
| IM-14-F45 | Constitution CR-F04 | P3 | No | L753 | "Harvest commits' own diffs" could be read as the merge's first-parent diff; say "each non-merge harvest commit's diff" |
| IM-14-F46 | Constitution CR-F03 | P3 | No | L757-758 | Stage, not Ship, audits later plan or manifest edits as units |
| IM-14-F47 | Python PY-F01 | P3 | No | L731-734 | Hyphen-dropped join only when line 1 ends with `-`; removing the required sentence replaces it with nothing |
| IM-14-F48 | Scope SBA-F03 | P3 | No | L759 | "It may run the detector as an aid" is optional (36 B) |
| IM-14-F49 | Constitution CR-F02 | P3 | No | L760-766 | Controls for a missing `FLOOR` file and an unused entry |
| IM-14-F50 | Constitution CR-F05 | P3 | No | L747-757 | A checked-off record binds commit SHA and disposition; location of the final closure pull request record |
| IM-14-F51 | Constitution CR-F06; Python PY-F03; Learnings LR-F03; Scope SBA-F02 | P3 | No | frozen B1 L362, B3 L385, B5, D2 L441 | Frozen "added to the audit inventory" cells: `FLOOR` grows only by B1 and D1; the rest is residue |
| IM-14-F52 | Python PY-F02; Learnings LR-F02 | P3 | No | frozen B2, B4a, B4b Files | These tasks edit `harness_surfaces.py` without the audit test in Files; add it when touching a trigger or ledgered line |
| IM-14-F53 | Python PY-F04 | P3 | No | L739-740 | The `LEDGER` path key is the repo-relative POSIX string used in `FLOOR` |
| IM-14-F54 | Learnings LR-F04 | P3 | No | L753-754 | The manifest commit recording PASS lands through the harvest commits |
| IM-14-F55 | Learnings LR-F05 | P3 | No | L755-757 | S(D)'s merge diff repeats D3's checked-off lines; skip them unless changed |

## E4 Consolidated Revision 1 (subject revision 7)

| Field | Value |
|---|---|
| Subject | Plan revision 7, commit `79c18cc0`, blob `0aa8b652bee6f4a0ca67316d450ca781f8953c1c`, 838 lines, LF, final newline |
| Revisions used | 1 of 2 |
| Author | Stage (`claude-opus-5.5` / `anthropic` / `high`) |
| Changed body lines (revision 7 numbering) | 727-729 (Floor: staged `FLOOR`); 733-734 (Reading: hyphen join condition); 747-760 (Residue) |
| Changed frontmatter lines | 3 (description: revision 7 sentence), 10 (`revision: 7`), 12 (`prior_revision` revision 6, `33ad886b`, `5cf1d52a`) |
| Not changed | Every other line, including L190, the C5 cell, D3 preflight item 6 and every Files and Verification cell. No task, reason code, public name, subsystem or threat class added |
| Review state | Pending delta review of the changes, then the final full consistency pass |

### Contract Growth (revision 1 versus revision 7)

| Measure | Revision 1 | Revision 6 | Revision 7 | Limit | Growth |
|---|---:|---:|---:|---:|---:|
| File bytes | 69163 | 82363 | 82414 | 82995 | +19.16% |
| Body bytes (after frontmatter) | 63778 | 76498 | 76531 | 76533 | +19.997% (2 bytes left) |
| Words | 10198 | 12098 | 12107 | 12237 | +18.72% |
| Tasks | 17 | 17 | 17 | 20 | 0% |
| Lines (not a limit) | 769 | 837 | 838 | none | +9.0% |

The IM-14-F48 cut (36 bytes) paid for part of the blocker fixes.

**Rule check (Stage, throwaway).** The rules at revision 7 L725-743
were re-run against every control at L761-767, the F05, F10 and F11
forms, `time-of-`/`check` and indented second lines. Three cases were
added: C5's stage with only `harness_read.py` listed passes, a listed
file missing fails, and `TOC`/`TOU` with no hyphen is not joined.
All 32 cases matched.

### Dispositions

Line references are to revision 7 (blob `0aa8b652`).

| ID | Blocking | Disposition | Evidence in revision 7 |
|---|---|---|---|
| IM-14-F42 | **Yes** | Fixed | L727-729 (C5 lists `harness_read.py`, B1 adds `harness_surfaces.py` and D1 `harness_verdict.py`; a listed file missing fails) |
| IM-14-F43 | **Yes** | Fixed | L758-759 (each closure pull request is a unit, recorded in its body, which is outside its diff) |
| IM-14-F44 | **Yes** | Fixed | L747-748 (residue covers everything outside `FLOOR` and any claim the test misses inside it) |
| IM-14-F45 | No | Fixed | L755 (each non-merge harvest commit's diff) |
| IM-14-F46 | No | Fixed | L759-760 (Stage audits later plan or manifest edits as units) |
| IM-14-F47 | No | Fixed in part | L733-734 (hyphen join only when the first line ends in `-`). The "replace with nothing" reading of sentence removal is carried to C5 |
| IM-14-F48 | No | Fixed | L760 (the optional detector-aid clause is cut) |
| IM-14-F49 | No | Carried to harvest | C5 adds controls for a missing listed file and an unused entry (both rules are already stated at L729 and L743) |
| IM-14-F50 | No | Carried to harvest | Each checked-off record names the commit SHA and the disposition. The closure pull request location is fixed by IM-14-F43 |
| IM-14-F51 | No | Carried to harvest | Note on B1, B3, B5 and D2: `FLOOR` grows only by B1 and D1; other paths are residue units |
| IM-14-F52 | No | Carried to harvest | B2, B4a and B4b add the audit test to Files when they touch a trigger or ledgered line of `harness_surfaces.py` |
| IM-14-F53 | No | Carried to harvest | C5 note: the `LEDGER` path key is the repo-relative POSIX string used in `FLOOR` |
| IM-14-F54 | No | Carried to harvest | The manifest commit recording PASS lands through the harvest commits and is audited as a unit |
| IM-14-F55 | No | Carried to harvest | At S(D)'s closure, D3's checked-off lines are skipped unless changed (the incremental rule at L749-752) |

**Harvest carries** (0 plan bytes): IM-14-F47 (in part) and IM-14-F49 to
F55, plus the E3 carries IM-14-F26, IM-14-F35 (C5 note), IM-14-F39 and
NOROW-F19.

Totals: 3 blocking fixed; 4 non-blocking fixed, 1 fixed in part; 7
carried to harvest. No finding declined.

## E4 Delta Review 1 (subject revision 7)

```text
epoch: LIFECYCLE-E4-5cf1d52a
subject: plan revision 7, commit 79c18cc0, blob 0aa8b652bee6f4a0ca67316d450ca781f8953c1c
scope: changes only
decision: REVISE
```

| Persona | Session | Route | Decision |
|---|---|---|---|
| Agent-Native Parity Reviewer | `b466cc0a` | `gpt-6-sol` | PASS |
| Python reviewer | `fca7a513` | `claude-opus-5.5` | PASS |
| Scope reviewer | `5bb49836` | `claude-opus-5.5` | PASS |
| Learnings reviewer | `296b2a2d` | `claude-opus-5.5` | PASS |
| Constitution Reviewer | `a8c11c68` | `claude-opus-5.5` | PASS |
| Security Lens Reviewer | `f0eaa4a1` | `gpt-6-sol` | PASS |
| Architecture Strategist (lead) | `687d2cb2` | `gpt-6-sol` | REVISE |

**Withdrawals.** Security raised E4-SLR-F01 (the PR body is mutable),
and the Lead raised E4-AS-F02 (the same point). The Orchestrator
clarified that "(its body)" names the record carrier and that the unit
is the closure pull request's commit diff, and both reviewers withdrew
their findings. Neither is counted. Both suggested an unambiguous
wording, recorded as IM-14-F61.

**Closed.** All E4 initial blockers, IM-14-F42, IM-14-F43 and IM-14-F44.
IM-14-F45, F46 and F48 hold. IM-14-F47 is accepted in part, and
Constitution accepts IM-14-F50 as partial.

**Stop-condition check.** Blockers declined (3 -> 1), and the new
blocker (1) is fewer than those closed (3). Not triggered.

| Stable ID | Raised by (confidence) | Sev | Blocking | Revision 7 lines | Summary and remedy |
|---|---|---|---|---|---|
| IM-14-F56 | Lead E4-AS-F01 (8) | P2 | **Yes** | L747-760 | Stage's audit of later plan or manifest edits has no deadline, so it could be relied on before it is dispositioned. Remedy: Stage dispositions each later edit, bound to its content, before the next Ship claim or closure; pay by cutting "read-only" |
| IM-14-F57 | Python E4-PY-F05; Scope SBA-F04; Learnings LR-F06; Constitution CR-F07 | P3 | No | L733-734 | `TOC- ` (trailing whitespace) then `TOU` escapes the hyphen join; strip trailing whitespace before the ends-in-`-` test, and add a `TOC- `/`TOU` control |
| IM-14-F58 | Constitution CR-F08 | P3 | No | L758-759 | Copy the closure pull request disposition into the merge commit message |
| IM-14-F59 | Parity E4-ANP-F02 | P3 | No | L754-758 | Name the existing Ship record carriers (advisory) |
| IM-14-F60 | Learnings LR-F07 | P3 | No | L759-760 | Record Stage's audit in the edit's commit message, which is outside its own diff; the first agent to audit a line checks it off |
| IM-14-F61 | Security (suggestion); Lead (after withdrawing E4-AS-F02) | P3 | No | L758-759 | Disambiguate "each closure pull request (its body)" as "the closure PR diff, with the body as the record" |

## E4 Consolidated Revision 2 (subject revision 8)

| Field | Value |
|---|---|
| Subject | Plan revision 8, commit `d47f64b1`, blob `8d397c0559ae96da709620fc3db044124c068423`, 838 lines, LF, final newline |
| Revisions used | 2 of 2 (the last) |
| Author | Stage (`claude-opus-5.5` / `anthropic` / `high`) |
| Changed body lines (revision 8 numbering) | 749-760 (Residue bullet only) |
| Changed frontmatter lines | 3 (description: revision 8 sentence), 10 (`revision: 8`), 12 (`prior_revision` revision 7, `79c18cc0`, `0aa8b652`) |
| Not changed | Every other line, including the Floor, Reading, Detector, Clearing, Required sentence and Controls bullets. No task, reason code, public name, subsystem or threat class added |
| Review state | Pending delta review of the changes, then the final full consistency pass |

### Contract Growth (revision 1 versus revision 8)

| Measure | Revision 1 | Revision 7 | Revision 8 | Limit | Growth |
|---|---:|---:|---:|---:|---:|
| File bytes | 69163 | 82414 | 82415 | 82995 | +19.16% |
| Body bytes (after frontmatter) | 63778 | 76531 | 76532 | 76533 | +19.997% (1 byte left) |
| Words | 10198 | 12107 | 12108 | 12237 | +18.73% |
| Tasks | 17 | 17 | 17 | 20 | 0% |
| Lines (not a limit) | 769 | 838 | 838 | none | +9.0% |

These edits were paid for inside the Residue bullet. "Read-only" was cut
(the final sentence already bars Ship writes). "It is incremental:" was
cut, since the rule itself states it. "The unit" became "it", and "the
`LEDGER` count" became "`LEDGER` count".

**Rule check (Stage, throwaway).** The rule bullets (L725-746) are
unchanged from revision 7. Re-run against every control, the rules
gave the same 32 of 32 results. A literal `TOC- `/`TOU` case (the
IM-14-F57 carry) escapes as written.

### Dispositions

Line references are to revision 8 (blob `8d397c05`).

| ID | Blocking | Disposition | Evidence in revision 8 |
|---|---|---|---|
| IM-14-F56 | **Yes** | Fixed | L758-760 (by Stage, each later plan or manifest commit, before the next Ship claim or closure, recorded in its message; the commit binds the audit to its content, and the message is outside its own diff) |
| IM-14-F61 | No | Fixed | L758 ("each closure pull request diff (body record)": the diff is the unit, the body the record) |
| IM-14-F57 | No | Carried to harvest | C5: strip trailing whitespace before the ends-in-`-` test; add a `TOC- `/`TOU` control |
| IM-14-F58 | No | Carried to harvest | The closure merge commit message copies the closure pull request disposition |
| IM-14-F59 | No | Carried to harvest | Map session note, closure note, readiness record and body record to existing Ship carriers (with IM-14-F39) |
| IM-14-F60 | No | Fixed in part; rest carried | The commit-message location is in the plan (L759-760). Carried: the first agent to audit a line checks it off |

**Harvest carries** (0 plan bytes): IM-14-F57, F58, F59 and the rest of
F60, together with the earlier carries: IM-14-F47 (in part), F49 to
F55, F26, F35, F39 and NOROW-F19.

Totals: 1 blocking fixed; 1 non-blocking fixed, 1 fixed in part; 3
carried to harvest. No finding declined.

## E4 Delta Review 2 (subject revision 8)

```text
epoch: LIFECYCLE-E4-5cf1d52a
subject: plan revision 8, commit d47f64b1, blob 8d397c0559ae96da709620fc3db044124c068423
scope: changes only
decision: PASS (7 of 7)
```

All seven personas passed, in the same sessions as delta review 1.
IM-14-F56 and IM-14-F61 are closed.

| Stable ID | Raised by | Sev | Summary (harvest carry) |
|---|---|---|---|
| IM-14-F62 | Constitution CR-F09; Scope (timing note) | P3 | A record in a commit message can be lost by an amend; audit the staged diff at commit time |
| IM-14-F63 | Learnings | P3 | A line can be audited twice once (at the Stage commit and again in a shipment diff); the first audit checks it off (with IM-14-F60) |
| NOROW-F21 | Constitution CR-F10 | P3 | The plan description says "Revision 8 revises the subject (revision 6)" while `prior_revision` is 7. It is accurate (revision 6 is the E4 subject) but easy to misread. Plan text; not corrected under E4 |

## E4 Final Full Consistency Pass (subject revision 8)

```text
subject: plan revision 8, blob 8d397c0559ae96da709620fc3db044124c068423
decision: REVISE (4 PASS, 3 REVISE; 2 blocking)
```

| Persona | Session / route | Decision | Blocking IDs | `residue_audit` |
|---|---|---|---|---|
| Architecture Strategist (lead) | `687d2cb2` / `gpt-6-sol` | REVISE | NOROW-F20 (P1, 9) | no-claim |
| Agent-Native Parity Reviewer | `b466cc0a` / `gpt-6-sol` | REVISE | NOROW-F20 (P1, 10) | no-claim |
| Security Lens Reviewer | `f0eaa4a1` / `gpt-6-sol` | REVISE | IM-14-F64 (P2-critical, 8) | no-claim |
| Constitution Reviewer | `a8c11c68` / `claude-opus-5.5` | PASS | none | no-claim |
| Python reviewer | `fca7a513` / `claude-opus-5.5` | PASS | none | no-claim |
| Scope reviewer | `5bb49836` / `claude-opus-5.5` | PASS | none | no-claim |
| Learnings reviewer | `296b2a2d` / `claude-opus-5.5` | PASS | none | no-claim |

**IM-14 persona residue audit (the plan and manifest unit).** All seven
personas returned no-claim at blob
`8d397c0559ae96da709620fc3db044124c068423`. This record stands, bound to
that blob, whatever the epoch outcome. Any later edit to the plan or
manifest is a new unit under the revision 8 Residue rule.

### Blocking

| Stable ID | Raised by (confidence) | Sev | Plan lines (rev 8) | Summary |
|---|---|---|---|---|
| NOROW-F20 | Lead (9); Parity (10); corroborated as non-blocking by Constitution CR-F11/CR-F12, Python (7), Scope SBA-F05, Learnings LR-F08 (P2)/LR-F09 | P1 | L49 (`harvest_gate`); Bottom Line Status (L70) | **Authority mismatch.** `harvest_gate` requires a "LIFECYCLE-E2 review PASS", but E2 is permanently `EPOCH_STOPPED` and E4 governs, so no PASS can satisfy the gate. The Status still says revision 3 / E2. It is a prerequisite for harvest, not a harvest carry, and needs an operator-authorized correction and review. The gate fails closed |
| IM-14-F64 | Security E4-SLR-F02 (8) | P2 (IM-14-critical) | L755-760; OP-1 (L506-515, L613) | Non-merge harvest commits are audited only "before claiming S(A)". OP-1 lets S(D) be harvested later (after the IM-10 shipment exists), so a late harvest commit has no audit checkpoint, and Stage's later-edit rule covers only plan and manifest commits. Required: audit each harvest commit's own diff before the first Ship claim or closure after it lands. No historical rescan |

### Non-Blocking (harvest carries unless the next epoch absorbs them)

| Stable ID | Raised by | Sev | Summary |
|---|---|---|---|
| IM-14-F65 | Scope SBA-F06; Learnings LR-F10 | P3 | Add D4 (~L470, "test files added to the audit inventory") to the IM-14-F51 note |
| NOROW-F22 | Constitution CR-F13; Scope SBA-F07; Learnings LR-F11; Python | P3 | The Plan-Harden record stops at revisions 3 and 4; add a no-new-signal note for revisions 5 to 8 |
| NOROW-F23 | Constitution CR-F14 | P3 | L646 labels "Constitution V (explicit contracts)", but Principle V is Structured Observability |

The stale `harvest_gate` and Status text (CR-F11, CR-F12, SBA-F05,
LR-F08, LR-F09) is merged into NOROW-F20 and not counted separately.

## E4 Epoch Stop

```text
epoch: LIFECYCLE-E4-5cf1d52a
decision: EPOCH_STOPPED
publication: not met
harvest: not permitted
operator_decision: pending
```

| Field | Value |
|---|---|
| Last subject | Plan revision 8, commit `d47f64b1`, blob `8d397c0559ae96da709620fc3db044124c068423` |
| Consolidated revisions used | 2 of 2 (budget exhausted) |
| Blocking trend | 3 (initial) -> 1 (delta 1) -> 0 (delta 2) -> 2 (final full consistency pass) |
| Open blockers | NOROW-F20 (P1, authority mismatch), IM-14-F64 (P2, IM-14-critical) |
| Stop conditions triggered | "An authority mismatch is found between artifacts" (NOROW-F20: the plan's gate names E2, but E4 governs); the remediation budget is exhausted with 2 blockers open; blockers rose (0 -> 2) |
| Publication gate | **Not met** |
| Harvest | Nothing harvested. Harvest reads its verdict from this manifest under OP-5, and `EPOCH_STOPPED` is not `PASS`, so it fails closed. The plan's `harvest_gate` also fails closed |
| Plan revisions after the stop | None in E4. No revision 9 |
| Record that stands | The IM-14 persona residue audit: no-claim at blob `8d397c05` |
| E2 and E3 | Unchanged: `EPOCH_STOPPED` |

**Where the blockers are.** One is procedural: the stale E2 gate and
Status text (NOROW-F20). The other is a single IM-14 checkpoint for late
harvest commits (IM-14-F64). Both remedies are small, but the plan has 1
body byte of growth headroom.

**Permitted outcomes (operator decision pending).** Split, spike,
re-charter or new epoch, explicit risk acceptance, defer, or cancel. No
outcome is chosen here.

## Operator Ruling: New Epoch LIFECYCLE-E5 (E4 outcome)

```text
at: 2026-09-25T23:16:08-07:00
outcome: new epoch (LIFECYCLE-E5)
```

**Ruling (verbatim).** "Pursue the recommended new E5 epoch."

**Accepted recommendation.** A narrow new epoch, LIFECYCLE-E5, that
changes only three spots:

1. The frontmatter `harvest_gate` points at the publication PASS of
   whichever epoch governs the plan, as recorded in the review manifest,
   instead of naming a stopped epoch.
2. The Bottom Line Status line is brought up to date (it still reads
   "Revision 3 ... `LIFECYCLE-E2`...").
3. The residue rule in the Non-Claim Audit Inventory requires each
   non-merge harvest commit's own diff to be audited before the first
   Ship claim or closure after that commit lands, replacing "before
   claiming S(A)". This closes IM-14-F64 without any historical rescan.

The body must be net-neutral: shortening the Status line pays for the
new wording. Same seven personas and routes; one initial review of the
changes, then delta reviews if needed, then one final full consistency
pass.

## Epoch LIFECYCLE-E5

```text
epoch: LIFECYCLE-E5-b7a77c76
opened_by: operator ruling 2026-09-25T23:16:08-07:00
subject: plan revision 9, commit 42fec73f, blob b7a77c7644fa97dff01c724480abfcbcea8f346d, derived from revision 8 (commit d47f64b1, blob 8d397c0559ae96da709620fc3db044124c068423)
verdict: pending
harvest_permitted: false
```

| Field | Value |
|---|---|
| Scope (open) | Frontmatter (`harvest_gate`; revision and epoch metadata; `hardening_pass` only if needed for consistency); the Bottom Line Status line; the harvest clause of the residue rule in the Non-Claim Audit Inventory |
| Frozen | Everything else, at revision 8 |
| Blockers targeted | NOROW-F20 (P1, `harvest_gate` authority mismatch and stale Status); IM-14-F64 (P2, IM-14-critical: audit checkpoint for late harvest commits) |
| Rubric, severity mapping, personas, routes | Frozen as in E4. Only P0, P1 and matrix-critical P2 block. The same seven personas. Lead, Security and Parity on `gpt-6-sol`; Constitution, Python, Scope and Learnings on `claude-opus-5.5` |
| Contract limits | Unchanged: no new task, reason code, public name, subsystem or threat class |
| Growth | Unchanged, cumulative against revision 1 blob `2d562820`: body bytes at most 76533, file bytes at most 82995, words at most 12237 |
| Budget | At most 2 consolidated revisions |
| Cadence | One initial review of the changes, then delta reviews if needed, then one final full consistency pass |
| Stop conditions | As in the convergence-reset deliberation (`docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md`, stop conditions) |
| Carried findings | IM-14-F62, IM-14-F63, IM-14-F65, NOROW-F21 to NOROW-F23 and every earlier harvest carry stay carried; none is in scope |
| E2, E3 and E4 | Verdicts stay `EPOCH_STOPPED` |
| E4 residue audit | The no-claim record bound to blob `8d397c05` stands for unchanged lines; changed lines are new units |
| E5 verdict | `PASS` at the final full consistency pass (see [E5 Verdict](#e5-verdict)); publication met; `harvest_permitted` stays `false` until OP-5 |

### Revision 9 (E5 subject)

| Field | Value |
|---|---|
| Epoch token | `LIFECYCLE-E5-b7a77c76` (first 8 hex of the revision 9 blob) |
| Subject | Plan revision 9, commit `42fec73f`, blob `b7a77c7644fa97dff01c724480abfcbcea8f346d`, 839 lines, LF, final newline |
| Author | Stage |
| Changed body lines (revision 9 numbering) | 70 (Bottom Line Status); 754-756 (harvest clause of the Residue bullet; one line added by the wrap) |
| Changed frontmatter lines | 2 (title: `LIFECYCLE-E5 subject`), 3 (description: revision 9 sentence), 10 (`revision: 9`), 12 (`prior_revision` revision 8, `d47f64b1`, `8d397c05`), 13, 15 and 16 (`review_epoch`, epoch family and token rule: `LIFECYCLE-E5`), 49 (`harvest_gate`) |
| Not changed | Every other line, including the rest of the Residue bullet (its plan-and-manifest unit still reads "by an E4 persona", L753, frozen), `hardening_pass` (not needed for consistency) and every task, reason code, public name, subsystem and threat class |
| Side effect | The rewritten description sentence no longer contains the NOROW-F21 wording ("revises the subject (revision 6)"); its disposition is left to the E5 review |

| Change | Before (revision 8) | After (revision 9) | Target |
|---|---|---|---|
| 1. `harvest_gate` (L49) | "Harvest only after a LIFECYCLE-E2 review PASS recorded in the review manifest. Not before." | "Harvest only after a publication PASS of the governing review epoch, recorded in the review manifest and bound to the plan blob it reviewed. Not before." Generic: it cannot go stale when an epoch stops, and matches OP-5 (harvest reads its verdict from the manifest) | NOROW-F20 |
| 2. Bottom Line Status (L70) | "Revision 3, consolidated revision 2 of 2 of `LIFECYCLE-E2-R1-2d562820` (findings in the review manifest). Not publication-eligible. Not implementation-ready. No backlog item exists yet" | "Revision 9, `LIFECYCLE-E5` subject (verdict in the review manifest). Not publication-eligible. Not implementation-ready. No backlog item yet" (current, and 44 bytes shorter) | NOROW-F20 |
| 3. Residue, Ship clause (L754-756) | "by Ship, each non-merge harvest commit's diff before claiming S(A) (session note)" | "by Ship, each non-merge harvest commit's own diff before the first Ship claim or closure after it lands (session note)". A late S(D) harvest commit (OP-1) is audited before the next Ship claim or closure; no historical rescan | IM-14-F64 |

#### Contract Growth (revision 1 versus revision 9)

| Measure | Revision 1 | Revision 8 | Revision 9 | Limit | Growth |
|---|---:|---:|---:|---:|---:|
| File bytes | 69163 | 82415 | 82455 | 82995 | +19.22% (540 left) |
| Body bytes (after frontmatter) | 63778 | 76532 | 76527 | 76533 | +19.99% (6 left) |
| Words | 10198 | 12108 | 12121 | 12237 | +18.86% (116 left) |
| Tasks | 17 | 17 | 17 | 20 | 0% |
| Lines (not a limit) | 769 | 838 | 839 | none | +9.1% |

Measured as in earlier revisions: file bytes are the blob size; body
bytes are the bytes after the closing frontmatter `---` line; words are
whitespace-separated tokens of the whole file. The body is net-negative
(-5 bytes): the shorter Status line (-44) pays for the Residue clause
(+37, and +2 for the indent of the added wrapped line). The frontmatter
grows by 45 bytes, inside the file limit.

**Residue audit (Stage, revision 8 rule).** The changed lines make no
race, TOCTOU or hardlink-alias resistance claim (no-claim), recorded in
the revision 9 commit message.

## E5 Initial Review (subject revision 9)

```text
epoch: LIFECYCLE-E5-b7a77c76
subject: plan revision 9, commit 42fec73f, blob b7a77c7644fa97dff01c724480abfcbcea8f346d
dispatch_mode: explicit-model subagent
scope: changes only
decision: PASS (7 of 7)
```

The seven E4 reviewer sessions were reused: same persona and model, so
not a route change.

| Persona | Session / route | dispatch_mode | Decision | Blocker status | P3 raised | `residue_audit` |
|---|---|---|---|---|---|---|
| Architecture Strategist (lead) | `687d2cb2` / `gpt-6-sol` | explicit-model subagent | PASS | None open | None | no-claim |
| Security Lens Reviewer | `f0eaa4a1` / `gpt-6-sol` | explicit-model subagent | PASS | None open | None | no-claim |
| Agent-Native Parity Reviewer | `b466cc0a` / `gpt-6-sol` | explicit-model subagent | PASS | None open | None | no-claim |
| Constitution Reviewer | `a8c11c68` / `claude-opus-5.5` | explicit-model subagent | PASS | None open | E5-CR-F01, F02, F03 | no-claim |
| Python reviewer | `fca7a513` / `claude-opus-5.5` | explicit-model subagent | PASS | None open | E5-PY-F01, F02 | no-claim |
| Scope reviewer | `5bb49836` / `claude-opus-5.5` | explicit-model subagent | PASS | None open | E5-SBA-F01, F02 | no-claim |
| Learnings reviewer | `296b2a2d` / `claude-opus-5.5` | explicit-model subagent | PASS | None open | E5-LR-F01, F02 | no-claim |

`residue_audit` covers the revision 9 changed lines and the E5 manifest
sections.

### Blockers Closed

Line references are to revision 9 (blob `b7a77c76`).

| ID | Status | Evidence in revision 9 |
|---|---|---|
| NOROW-F20 | **Closed** | L49: `harvest_gate` requires "a publication PASS of the governing review epoch, recorded in the review manifest and bound to the plan blob it reviewed", so it no longer names a stopped epoch and matches OP-5. L70: the Status reads "Revision 9, `LIFECYCLE-E5` subject (verdict in the review manifest)" |
| IM-14-F64 | **Closed** | L754-756: Ship audits "each non-merge harvest commit's own diff before the first Ship claim or closure after it lands (session note)", so a late S(D) harvest commit (OP-1) has a checkpoint. No historical rescan |
| NOROW-F21 | **Moot** (closed by the rewritten description) | Frontmatter L3: the revision 9 sentence no longer says "revises the subject (revision 6)" |

### New Findings (P3, harvest carries)

Stage assigned stable IDs. None blocks.

| Stable ID | Raised by | Sev | Revision 9 lines | Summary and carry |
|---|---|---|---|---|
| IM-14-F66 | Constitution E5-CR-F01; Python E5-PY-F01; Scope E5-SBA-F01; Learnings E5-LR-F01 | P3 | L753 (frozen) | The plan-and-manifest unit still reads "by an E4 persona at the blob passing the final full consistency pass". Historical wording; E5 reused the seven E4 sessions, so the E5 record satisfies it as written. Optional fix at the next plan revision: "an E4" -> "a review" |
| NOROW-F24 | Constitution E5-CR-F02 | P3 | L49 (frontmatter only) | "Bound to the plan blob it reviewed" should also say that blob is the one being harvested, for example "bound to the plan blob being harvested" |
| IM-14-F67 | Constitution E5-CR-F03 | P3 | L754-758 | Lines created by resolving a conflict in a harvest merge commit fall outside every non-merge harvest commit's diff. Require conflict-free harvest merges, or audit the combined diff of a conflicted merge (C5 and harvest note) |
| IM-14-F68 | Scope E5-SBA-F02 | P3 | L754-756 | How Ship recognizes the harvest commits that landed since the last check-off is unnamed. Carry with IM-14-F59 and IM-14-F39 (Ship record carriers) |
| NOROW-F25 | Learnings E5-LR-F02 | P3 | L70 | The Status row must be refreshed with each plan revision. Stage note: after this PASS, the plan's `publication_eligible: false`, `status: pending-review` and the Status row's "Not publication-eligible" lag this manifest. Under OP-5 the manifest governs |
| NOROW-F26 | Python E5-PY-F02 | P3 | L756 | Short line from the minimal-diff wrap ("each shipment's merge diff at its"); cosmetic |

## E5 Final Full Consistency Pass (subject revision 9)

```text
epoch: LIFECYCLE-E5-b7a77c76
subject: plan revision 9, blob b7a77c7644fa97dff01c724480abfcbcea8f346d
dispatch_mode: explicit-model subagent
scope: full plan and manifest
decision: PASS (7 of 7; 0 blocking)
```

| Persona | Session / route | dispatch_mode | Decision | Blocking IDs | New finding | `residue_audit` |
|---|---|---|---|---|---|---|
| Architecture Strategist (lead) | `687d2cb2` / `gpt-6-sol` | explicit-model subagent | PASS | None | None | no-claim |
| Security Lens Reviewer | `f0eaa4a1` / `gpt-6-sol` | explicit-model subagent | PASS | None | None | no-claim |
| Agent-Native Parity Reviewer | `b466cc0a` / `gpt-6-sol` | explicit-model subagent | PASS | None | None | no-claim |
| Constitution Reviewer | `a8c11c68` / `claude-opus-5.5` | explicit-model subagent | PASS | None | Advisory (NOROW-F27) | no-claim |
| Python reviewer | `fca7a513` / `claude-opus-5.5` | explicit-model subagent | PASS | None | E5-PY-F03 (NOROW-F27) | no-claim |
| Scope reviewer | `5bb49836` / `claude-opus-5.5` | explicit-model subagent | PASS | None | E5-SBA-F03 (NOROW-F27) | no-claim |
| Learnings reviewer | `296b2a2d` / `claude-opus-5.5` | explicit-model subagent | PASS | None | E5-LR-F03 (NOROW-F27) | no-claim |

**IM-14 persona residue audit (the plan and manifest unit).** All seven
E5 personas returned no-claim for this plan and its manifest at blob
`b7a77c7644fa97dff01c724480abfcbcea8f346d`. That is the unit "this plan
and its manifest ... at the blob passing the final full consistency
pass", recorded here. Any later plan or manifest commit is a new unit
under the Residue rule, audited by Stage before the next Ship claim or
closure and recorded in its commit message.

| Stable ID | Raised by | Sev | Summary | Status |
|---|---|---|---|---|
| NOROW-F27 | Python E5-PY-F03; Scope E5-SBA-F03; Learnings E5-LR-F03; Constitution (advisory) | P3 | The manifest's top-level `review_epoch`, `verdict`, `decision` and `title` still describe E2. Add a reviews entry bound to blob `b7a77c76` with `decision: PASS`, and update or scope the top-level fields | **Closed in manifest** (this commit): E5 `reviews` entries including the verdict entry bound to `b7a77c76`; top-level `title`, `description`, `review_epoch_family`, `review_epoch`, `status`, `verdict`, `decision`, `publication`, `publication_eligible` and `consolidated_revisions_used` describe E5; the E2-scoped top-level keys moved into `e2_stop`; the E2 `reviews` entries are labeled with their epoch; `next_epoch` became `e5_epoch`; the body's Epoch table names the governing epoch |

All earlier carries stay carried.

## E5 Verdict

```text
epoch: LIFECYCLE-E5-b7a77c76
subject: plan revision 9, commit 42fec73f, blob b7a77c7644fa97dff01c724480abfcbcea8f346d
dispatch_mode: explicit-model subagent
decision: PASS
publication: met
harvest: not yet permitted (awaiting OP-5)
```

| Field | Value |
|---|---|
| Epoch | `LIFECYCLE-E5-b7a77c76` |
| Subject | Plan revision 9, commit `42fec73f`, blob `b7a77c7644fa97dff01c724480abfcbcea8f346d` |
| Reviews | Initial review: 7 of 7 PASS. Final full consistency pass: 7 of 7 PASS, 0 blocking |
| Consolidated revisions used | 0 of 2 |
| Blockers | NOROW-F20 and IM-14-F64 closed. Open P0, P1 or matrix-critical P2: none |
| Publication gate | **Met** |
| IM-14 residue audit | No-claim by all seven E5 personas at blob `b7a77c76` (plan and manifest unit) |
| E2, E3 and E4 | Unchanged: `EPOCH_STOPPED` |

**Harvest is not yet permitted.** The verdict is bound to blob
`b7a77c76`; harvesting any other blob does not satisfy it. Harvest
needs:

1. **OP-5 (operator):** authorize harvest to read `dispatch_mode` and
   `decision` from this manifest entry, bound to the reviewed blob.
2. **OP-2 (operator):** keep or defer IM-09 D4. Without an answer, D4 is
   harvested as planned.
3. **OP-1 (operator):** approve and schedule the IM-10 release unit
   (stash `9144435A`) so it ships before S(D). It blocks the harvest of
   S(D) only.

**Harvest-carry set** (0 plan bytes; each lands as a note on its carrier
at harvest):

| Origin | Carries |
|---|---|
| E2 (delta review 2, non-IM-14, never dispositioned since) | IM-16-F02.1, CONST-II-F01, NOROW-F18 |
| E2 deferrals (standing) | NOROW-F03 (portable `IO` fixture; C3 may add it if cheap); IM-02-F01 (template `eol=lf` pin, deferred to the IM-10 unit) |
| E3 | IM-14-F26, IM-14-F35 (C5 note), IM-14-F39, NOROW-F19 |
| E4 | IM-14-F47 (in part), IM-14-F49 to F55, IM-14-F57 to F59, IM-14-F60 (rest), IM-14-F62, IM-14-F63, IM-14-F65, NOROW-F22, NOROW-F23 |
| E5 | IM-14-F66, IM-14-F67, IM-14-F68, NOROW-F24, NOROW-F25, NOROW-F26 |
| Closed, not carried | NOROW-F20, IM-14-F64 (closed in E5); NOROW-F21 (moot); NOROW-F27 (closed in manifest) |

## Operator Rulings: OP-5, OP-2, OP-1 (harvest authorization)

Recorded at `2026-09-25T23:56:45-07:00`. Operator text, verbatim:

```text
OP-5: Authorized / OP-2: Keep / OP-1: Approved
```

| Item | Ruling | Meaning |
|---|---|---|
| OP-5 | Authorized | Harvest reads `dispatch_mode` and `decision` from the E5 verdict entry of this manifest, bound to plan blob `b7a77c7644fa97dff01c724480abfcbcea8f346d`. No `## Plan Review` section is appended to the plan; the plan blob stays unchanged. Harvesting any other blob does not satisfy the verdict |
| OP-2 | Keep | IM-09 is kept: D4 (post-activation recovery fixture) stays in Unit D and is harvested with S(D) |
| OP-1 | Approved | The IM-10 release unit (stash `9144435A`) is approved and is to be scheduled to ship before S(D). It gates the harvest of S(D) only |

**Harvest scope now:** S(A), S(C), S(B-core) and S(B-entry), in the
plan's dependency order (S(A) is the DAG root; each successor is blocked
by its predecessor and stays queued).

**Withheld:** S(D). It is harvested only after the IM-10 shipment exists.

This section supersedes the "Harvest is not yet permitted" statement in
the E5 Verdict above; the verdict, its binding to blob `b7a77c76` and the
harvest-carry set are unchanged. The harvest-carry set lands as notes on
each carrier at harvest.
