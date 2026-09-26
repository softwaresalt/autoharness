---
title: "Review manifest: ship lifecycle release units A to D plan (LIFECYCLE-E2)"
description: "Review manifest for the single governing plan docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md. It records epoch LIFECYCLE-E2-R1-2d562820 under the parameters frozen in 2ca9d9a5: the initial full review of plan revision 1 (blob 2d562820), seven personas, all REVISE, 41 consolidated findings of which 7 block; two consolidated revisions and two delta reviews followed (blockers 7 -> 2 -> 3), and the epoch stopped with 3 IM-14 blockers open (verdict EPOCH_STOPPED; publication not met; nothing harvested). Epoch LIFECYCLE-E3-703d0de1 (IM-14 audit; subjects revisions 4 and 5) then stopped after delta review 1: 5 blockers closed, 7 new admitted (verdict EPOCH_STOPPED; publication not met; nothing harvested). Findings, verdicts and dispositions live here and never in the plan."
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
  - {step: consolidated-revision-1, subject_revision: 2, subject_commit: fcae22da, subject_blob: 1828ecb9462762945979fbbfc1a73320f5975653, decision: REVISE, blocking_claimed_fixed: 7}
  - {step: delta-review-1, subject_revision: 2, subject_blob: 1828ecb9462762945979fbbfc1a73320f5975653, decision: REVISE, blocking_open: 2}
  - {step: consolidated-revision-2, subject_revision: 3, subject_commit: bd7002d5, subject_blob: ffa663de030a0a07baa5b62ea1078b750a0a4009, decision: REVISE, blocking_claimed_fixed: 2}
  - {step: delta-review-2, subject_revision: 3, subject_blob: ffa663de030a0a07baa5b62ea1078b750a0a4009, decision: REVISE, blocking_open: 3}
  - {epoch: LIFECYCLE-E3-703d0de1, step: initial-review, subject_revision: 4, subject_commit: 48cafb4a, subject_blob: 703d0de11fa5515a4abba0146d2f792bbe9991a6, decision: REVISE, blocking_open: 5}
  - {epoch: LIFECYCLE-E3-703d0de1, step: consolidated-revision-1, subject_revision: 5, subject_commit: 01cb89b9, subject_blob: 057a7615a5a53e53698bb53604ad7fba5382e744, decision: REVISE, blocking_claimed_fixed: 5, blocking_open: 7}
  - {epoch: LIFECYCLE-E3-703d0de1, step: delta-review-1, subject_revision: 5, subject_blob: 057a7615a5a53e53698bb53604ad7fba5382e744, decision: REVISE, blocking_closed: 5, blocking_open: 7}
consolidated_revisions_used: 2
consolidated_revisions_limit: 2
status: epoch-stopped
verdict: EPOCH_STOPPED
decision: EPOCH_STOPPED
publication: not-met
publication_eligible: false
harvest_permitted: false
stop_conditions_triggered: [blockers-do-not-decline-across-revisions, second-remediation-fails]
operator_decision: {at: "2026-09-25T20:47:56-07:00", outcome: spike, next: "E3 scoped to the IM-14 audit section after spike ratification"}
operator_ratification: {at: "2026-09-25T21:10:37-07:00", spike_commit: 27bcc254, design: ratified, e3_scope_widened: true, residue_text_audit: "agent-performed, recorded, release-scoped; operator not required"}
e3_epoch: {id: LIFECYCLE-E3-703d0de1, subject_revision: 4, subject_commit: 48cafb4a, subject_blob: 703d0de11fa5515a4abba0146d2f792bbe9991a6, scope: "IM-14 section, C5 Change cell, contradicting IM-14/PE-SAFETY-06 trace text, CONST-G2-F01", baseline_blob: ffa663de030a0a07baa5b62ea1078b750a0a4009, verdict: EPOCH_STOPPED}
e3_stop: {epoch: LIFECYCLE-E3-703d0de1, last_subject_revision: 5, last_subject_commit: 01cb89b9, last_subject_blob: 057a7615a5a53e53698bb53604ad7fba5382e744, status: epoch-stopped, verdict: EPOCH_STOPPED, decision: EPOCH_STOPPED, publication: not-met, publication_eligible: false, harvest_permitted: false, consolidated_revisions_used: 1, consolidated_revisions_limit: 2, stop_conditions_triggered: [blockers-do-not-decline-across-revisions, newly-admitted-findings-at-least-as-many-as-closed], operator_decision: {at: "2026-09-25T22:29:53-07:00", outcome: re-charter, next: "LIFECYCLE-E4 (IM-14 audit re-chartered)"}}
next_epoch: {id: pending (LIFECYCLE-E4-<first 8 hex of the revision 6 blob>), subject_revision: 6, derived_from: {revision: 5, commit: 01cb89b9, blob: 057a7615a5a53e53698bb53604ad7fba5382e744}, scope: "IM-14 section, C5 Change cell, IM-14 row, D3 preflight item 6 and noclaim-audit Files cells only if contradicting, frontmatter", verdict: pending}
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
epoch: LIFECYCLE-E4-<first 8 hex of the revision 6 blob> (fixed when revision 6 is committed)
opened_by: operator re-charter 2026-09-25T22:29:53-07:00
subject: plan revision 6, derived from revision 5 (commit 01cb89b9, blob 057a7615a5a53e53698bb53604ad7fba5382e744)
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
| E4 verdict | Pending |
