---
title: "Review manifest: ship lifecycle release units A to D plan (LIFECYCLE-E2)"
description: "Review manifest for the single governing plan docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md. It records epoch LIFECYCLE-E2-R1-2d562820 under the parameters frozen in 2ca9d9a5: the initial full review of plan revision 1 (blob 2d562820), seven personas, all REVISE, 41 consolidated findings of which 7 block. Findings, verdicts and dispositions live here and never in the plan."
doc_type: review-manifest
date: 2026-09-25
plan_id: ship-lifecycle-release-units
plan_path: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
review_epoch_family: LIFECYCLE-E2
review_epoch: LIFECYCLE-E2-R1-2d562820
frozen_parameters: {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-5.md, commit: 2ca9d9a5, section: "Frozen Epoch Parameters"}
rubric: {version: R1, skill_path: .github/skills/plan-review/SKILL.md, skill_blob_sha1: c77f3685e81046195a55bcf4fc1e7d8973e40f97}
matrix_version: "IM-01 to IM-17 (a04dea18; ratified 2634bac2; IM-17 closed b8a7b100; IM-16 decided 8fa08913); PE-1.7 (e65887d8)"
reviews:
  - {step: initial-full-review, subject_revision: 1, subject_commit: c7363567, subject_blob: 2d5628206de3ab8083ec8ac173fa5283663f9b01, decision: REVISE, blocking_open: 7}
consolidated_revisions_used: 0
consolidated_revisions_limit: 2
status: open
publication_eligible: false
recorded_by: Stage
consolidated_by: "Orchestrator (raw collection and blocking classification); Stage (classification check, identity resolution, dispositions)"
---

# Review Manifest: Ship Lifecycle Release Units Plan

## Epoch

| Field | Value |
|---|---|
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
