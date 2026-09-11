---
title: "Stage session — review-fix cycle 1 remediation for the unpublished 163-F/171-S staging set"
date: 2026-09-10
agent: stage
session_id: stage-2026-09-10-8964a988-review-fix-cycle-1
doc_type: memory
feature_id: 163-F
shipment_id: 171-S
gate: 033-DL
status: complete
tags: [stage, review-fix, remediation, step-0c, pre-mutation-gate, durability, readiness]
---

# Stage session — review-fix cycle 1 (unpublished 163-F / 171-S staging set)

## Scope

Remediation of the local review findings against the **unpublished** commit range
`origin/main...2208bf47`. Direct push was rejected by branch protection after the
pre-push gate passed (2,087 tests, markdownlint). **No remote publication
occurred**, so every finding below was fixed before first publication rather than
after.

Stage-owned artifact work only. No implementation, source, test, template, config
or workflow file was written; no build was run; no shipment was claimed or shipped;
nothing was pushed; no PR was created.

## Degraded-mode declaration (P-012)

`TOOL_OK: backlogit` (MCP transport available), `INDEX_SYNC_OK`.
`INTERCOM_DEGRADED` — the `agent-intercom` callable surface is unavailable, so
operator visibility is reduced and no phase broadcasts were emitted. Only
non-destructive, non-approval-dependent work was performed; no destructive backlog
operation was attempted. `ENGRAM_DEGRADED`, `GRAPHTOR_UNAVAILABLE` — file-based
discovery used, with every factual claim verified by direct inspection.

Route: `claude-opus-5` / `anthropic` / `high`.

## Findings resolved

### P0-1 — duplicate YAML frontmatter key (blocking)

`docs/decisions/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation.md`
declared `shipment:` twice — once for the harvested shipment `169-S`, once for the
subject shipment `159-S` — so a YAML parser silently discarded the first. Renamed
the harvest relationship to `harvested_shipment` / `harvested_shipment_status` and
preserved the subject `shipment: 159-S`. Verified by parsing: 29 distinct keys, both
values now readable, `shipment_status` no longer present. A duplicate-key scan
across all `docs/**` and `.backlogit/**` frontmatter found **no other occurrence**.

### P1-1 — durability overstatement in the R1 evidence-gate contract (blocking)

The R1 mechanism anchors Step 0(c)'s evidence record with an engine-written
`PRECASCADE_EVIDENCE_ANCHOR` event in `.backlogit/logs/{shipment_id}.jsonl`. The
plan and decision described that anchor as "durable" and "auditable" without naming
an audience — but `.backlogit/logs/` is covered by a workspace `.gitignore` rule, so
the anchor is durable **locally** and invisible to a fresh-clone reviewer, who would
have been left with nothing but the agent-authored `collection_completed_at` the
design exists to demote.

Resolved **inside** the existing R1 evidence-gate contract as **R1-11** (plan) /
**D-7** (decision):

* **L1 — local runtime ordering proof (gate-bearing).** Unchanged. The engine log is
  the *sole* gate input; all four halt tokens read L1 and only L1.
* **L2 — repository audit evidence (never gate-bearing).** At the closure commit,
  commit the evidence record **and** that shipment's own engine log, force-added past
  the ignore rule, **verbatim and byte-unmodified** — the engine's own bytes, never
  an agent-written transcription. Bounded to one shipment at its own closure: no
  general un-ignoring of `.backlogit/logs/`, no historical backfill, no `.gitignore`
  change.

A fresh-clone reviewer can then verify the closure claim in three steps — digest
match, append-order position, state match — none of which consults an agent-authored
timestamp.

Fail-closed behaviour is **not** weakened. A fifth pre-cascade halt token for L2 was
considered and **rejected**: it would gate the close on an artifact that cannot exist
until after the close (the `15A02E21` unsatisfiable-gate mistake). L2 is enforced
where it can act — **operational closure is incomplete until L2 is committed**, a
reportable P-001 condition. Missing L2 never authorizes a close, never downgrades a
halt, and is never a fallback. Ignored logs are nowhere described as remotely
durable.

### Same-contract completion findings (fixed this cycle, not deferred)

| # | Finding | Resolution |
|---|---|---|
| 3 | `163.006-T` / plan U4 claimed diagram 05 and `docs/diagrams/` do not exist, said **create**, and named only two halt tokens | Both exist (operator-approved 2026-09-07 under gate `G-DIAG-REVIEW`, present as working-tree artifacts). Retargeted to **update** the existing diagram; extended to draw the R1 anchor node and **all four** halt tokens as separately labelled exits, plus the L1/L2 split drawn unwired from any gate decision. Title updated; re-sized `XS`→`S`, `trivial`→`low` |
| 4 | `163.005-T` / `163.006-T` carried stale `not yet committed` wording for the compound learning and archived stash IDs | Synchronized with `163.004-T`'s publication wording — published 2026-09-10, commit `5171ace1` on `main`; `15A02E21` and `1CD92B69` both reconciled and archived 2026-09-10 |
| 5 | Elided `Plan: ... U3/U4/U5` references | Expanded to the full plan path in `163.005-T`, `163.006-T`, `163.007-T` |
| 6 | `170-S` lacked a priority | `priority: high`, matching `162-F` and sibling shipment ordering |
| 7 | `163-F` metadata incoherent with its dependency mutation | Refreshed through the official `backlogit` update operation (no hand-edit of generated tool state). Its description also carried the superseded two-token contract; now states the current R1 + R1-11 contract |
| 8 | Documentation claimed `171-S` gained a `blocks` dependency on `033-DL` | Corrected in the decision (`D-6`), the `033-DL` record, `163-F`, and the plan frontmatter. backlogit shipment claim-eligibility evaluates **shipment predecessors only**, so the shipment→deliberation edge was correctly **rejected by the tool** and never recorded; inventing one would have created a permanently unsatisfiable edge. The real gate is feature/task level (`163-F` + `163.001-T`…`163.005-T` → `033-DL`) and is **satisfied** (`033-DL` is `done`). Also removed the duplicate `informs` link `033-DL → 163-F`, which duplicated the execution dependency — one relationship, one home, per the semantic-links protocol |
| 9 | `D-4` and `H-2` still carried pre-R1 two-token wording contradicting R1 | Marked **superseded** in place with the governing R1 semantics restated alongside. History retained, not erased |

## Gates re-run

* **Plan hardening — R1-11** (third pass, `R1-11-H1`…`H7`): unsatisfiable-gate check
  drove the design; passing/failing states named for L2; protected invariants
  re-verified including a pinned token count of exactly four; lock invariants
  unaffected (L2 runs outside and after the lock window).
* **Plan review — cycle 3** (7 personas): **PASS**, zero unresolved P0, zero
  unresolved P1. Cycle 3 of a 3-cycle budget. Every finding raised passed the P-021
  C1 same-contract-surface test and was **fixed**, so no `DEFERRED SCOPE EXPANSION`
  capture was required by this cycle.

## Residual risk — checkpoint payload contract conflict (stash `904C47BC`)

`checkpoint-20260909-232909.json` carries a top-level `progress` object. Harness
`backlogit.instructions.md` rule 4 forbids hoisting domain data to the top level;
backlogit's own CheckpointV1 schema explicitly declares `progress` a **legal
top-level key**, whose only legal children are exactly the fields rule 4 says must
live under `context`. The two contracts are in direct tension: an agent cannot
satisfy rule 4 while also using the engine's modelled `progress` object.

**Disposition — carried as residual risk / follow-up, not claimed as compliant:**

* the tool-owned checkpoint was **not** hand-edited, quarantined, repaired, or
  resolved;
* no self-authorized disposition was made, and `requires deliberation: yes` on
  `904C47BC` remains **unmet**;
* `904C47BC` remains **active** and is the single live tracker (it supersedes the
  archived, narrower `7AD60E4F`); it records the full 26-file scope, the finding that
  the **writer path** is still emitting non-conforming payloads, and the guidance
  that the **contract conflict must be resolved first** — quarantining files against
  a premise that may itself be wrong would destroy accurate history for no integrity
  gain;
* this session therefore does **not** claim full checkpoint-contract compliance.

Consequently the readiness outcome below is `READY_WITH_FOLLOWUPS`, citing
`904C47BC`.

## Local Review Readiness

- Reviewed HEAD: the commit introducing this record (parent `2208bf478a3c356920aace8adbf5651af969588e`); the reviewed content is that commit's complete tree
- Outcome: `READY_WITH_FOLLOWUPS`
- Blocking findings: `P0=0, P1=0` (P0-1 and P1-1 both resolved in this cycle)
- Full local build: `not applicable — Stage-owned planning/backlog artifact work only; no source, test, template, config or workflow file changed`
- Follow-ups: `904C47BC` (checkpoint payload contract conflict — active, undispositioned, `requires deliberation: yes` unmet); plan review cycle 3 `P3-4` (the motivating `.gitignore` rule is itself uncommitted working-tree state; R1-11 is written to be correct either way) and `P3-5` (same as `904C47BC`)
- Shadow review: `not requested` — no PR exists; nothing was pushed and no publication occurred

## Shipment state at session end

* `169-S` — `queued`, unshipped. Eligible in the queue view.
* `171-S` — `queued`, `priority: high`, dependencies: `blocks 169-S` (unchanged, and
  the only shipment-level edge). **Not claimable**: absent from the eligible
  `queue --type shipment --status queued` result, which returns only `161-S` and
  `169-S`. It becomes eligible only after `169-S` reaches `shipped`.
* `170-S` — `queued`, now `priority: high`, dependencies: `blocks 169-S`,
  `blocks 162-S`. Also not eligible.
* `033-DL` — `done`; feature/task-level gate on `163-F` and `163.001-T`…`163.005-T`
  satisfied. Edges retained as a permanent audit record.

## Preserved unrelated dirty files (deliberately NOT committed)

* `.gitignore` (modified — adds `.backlogit/logs/`)
* `.backlogit/checkpoints/checkpoint-20260908-195611.json` (untracked, `agent: ship`)
* `docs/design-docs/cost-per-unit-of-work-reduction.md` (untracked)
* `docs/diagrams/` (untracked — 13 files including diagram 05 and the `eraser/` set)
* `scripts/check_eraser_diagrams.py` (untracked)

## Next steps

1. Operator decision on `904C47BC` — resolve the checkpoint contract conflict
   (amend harness rule 4, or reaffirm it) **before** any file disposition.
2. Publication of this commit remains blocked by branch protection on direct push;
   a PR is required and is **Ship-owned**, not Stage's to create.
3. `171-S` stays queued until `169-S` ships. Do not claim it earlier.
