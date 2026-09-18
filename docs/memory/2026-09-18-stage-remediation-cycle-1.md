---
title: "Stage remediation cycle 1 — seven-entry contract-defect portfolio"
description: "Session memory for Stage remediation cycle 1 against the local review of commit 1b6a312d. Records the disposition of all ten blocking P1 findings, the evidence behind the one partially-rejected finding, the corrected dependency graph, the backlog realignment, and the checkpoint supersession. Nothing was committed or pushed."
doc_type: memory
source: docs/memory/2026-09-18-stage-remediation-cycle-1.md
date: 2026-09-18
agent: stage
session_id: stage-2026-09-18-remediation-cycle-1
checkpoint: .backlogit/checkpoints/checkpoint-20260918-065902.json
supersedes_memory: docs/memory/2026-09-17-stage-seven-entry-contract-defect-portfolio.md
tags:
  - "stage"
  - "remediation"
  - "contract-defect-portfolio"
---

# Stage remediation cycle 1 — seven-entry contract-defect portfolio

Target: the local review of commit `1b6a312d` (not pushed; branch protection
requires a PR). Scope was strictly Stage: decisions, plans, reviews, backlog,
and checkpoint records. No source implementation, claim, build, PR, merge, or
Ship work. **Nothing committed, nothing pushed.**

## Finding disposition

| # | Finding | Disposition |
|---|---|---|
| 1 | P-006 evidence missing from four plans | **Fixed.** All six plans now carry a persisted `## Plan Hardening Record (P-006)` named by a `plan_hardening_section` key. Extended beyond the four named plans — see Scope extensions |
| 2 | `expected_red` had no deterministic ID→marker mapping | **Fixed.** Typed entry shape `{test_id, marker}`; observation specified against `unittest.TestResult` via a `P004Result` runner (new task `168.007-T`) |
| 3 | Post-claim plan promised a detector, shipped prose | **Fixed by withdrawal.** Detector removed from the release unit; typed policy-clause representation deferred to stash `E770139B`. Tasks `169.004-T` and `169.006-T` returned from `177-S` |
| 4 | Branch plan: no option-like rejection, wrong deps, empty rung, fake design-doc path | **Fixed, all four.** V1–V11 validator with leading-hyphen rejection (new task `170.010-T`); dependencies re-encoded; rung removed; provenance recorded as `unavailable-external` |
| 5 | Single-governing-plan feature too broad | **Fixed.** Reduced to three properties. Four surfaces deferred to stash entries `95575B96`, `4003E0B8`, `0F26AA6C`, `7C7A4C96`. High-complexity tasks split into `171.013-T`/`171.014-T` |
| 6 | Checkpoint plan ordering, validation boundary, stale count, malformed new checkpoint | **Fixed.** `validate_checkpoint_payload(payload, origin)` named and wired; ordering encoded; inventory test made invariant-based; corpus corrected 51→52; malformed checkpoint superseded via the official lifecycle |
| 7 | SAFE_CLOSE needed a durable tracker and version reconciliation | **Fixed.** Tracker is chore `002-C`, held outside `181-S` and outside `173-F`. CI-pinned v1.9.0 declared the authoritative baseline. New tasks `173.008-T`, `173.009-T`, `173.010-T` |
| 8 | DAG truth | **Fixed.** `168-S → 176-S` added; arbitrary serial chain among `177..181` removed and replaced by a fan-out on `176-S`. `169-S`/`175-S` untouched |
| 9 | Backlog Markdown integrity | **Partially fixed — see below.** Substance fixed; the H1/heading portion is not achievable through supported authoring |
| 10 | Operator-repaired historical checkpoint | **Fixed by telling the truth.** Recorded as an operator-authored, operator-authorized pre-existing repair. The operator's change was preserved untouched |

## Finding 9 — evidence for the partial rejection

The finding asked for repair "through supported backlogit section/template
authoring." Probing the installed binary showed the H1/heading surfaces
**cannot be produced that way**:

* `backlogit add --section description=… --section acceptance-criteria=…`
  wrote the description as plain body prose and **silently dropped** the second
  section. No template was applied.
* `backlogit update --section name=value` appends a
  `<!-- BEGIN:name -->…<!-- END:name -->` block. It emits **no `# H1`** and
  **no `##` headings**.
* Section names are **not validated** against the type's template: an invented
  `bogus-section-name` was accepted and written.
* There is **no removal operation** — an empty value leaves an empty marker
  block.
* Repo-wide, only `032-DL`, `080-F`, `081-F` carried marker blocks before this
  session, and **even those have no H1 or headings**. The templates under
  `.backlogit/templates/` are effectively advisory in this version.

So producing the templated H1/heading structure would require hand-writing
Markdown bodies that the tool does not round-trip and would drift on the next
tool-driven update. **What was fixed instead:** the genuine gap —
`176-S`…`181-S` had *entirely empty bodies*. All six now carry `description`
and `items` sections (plus `blocked-returns` on `177-S`/`179-S`), and all six
features carry `goals` and `dod`.

Caveat: these probes ran against the local `1.10.1+dirty` build. CI pins
v1.9.0. Same divergence class as finding 7.

## Corrected dependency graph

```text
176-S  (dag root, no dependencies)
  ├── 177-S   ├── 178-S   ├── 179-S
  ├── 180-S   ├── 181-S   └── 168-S (also → 166-S, pre-existing)
169-S, 175-S — untouched, independent
```

`176-S` fixes the unsatisfiable P-004 red-phase precondition that every other
TDD shipment must pass, so it is a genuine technical prerequisite. The
revision-2 chain `177→178→179→180→181` encoded no technical prerequisite and
was removed.

**Queue positions were deliberately not used.** `backlogit queue move`
reorders within the entire active queue view (182+ items across all types),
which would have mutated unrelated `169-S`/`175-S` sequencing — prohibited by
finding 8. Execution preference is recorded in the shipment `description`
sections instead. `backlogit queue view --type shipment` already reflects the
DAG correctly.

## Backlog realignment

| Feature | Tasks | Change |
|---|---|---|
| 168-F | 7 | +`168.007-T` (P004Result runner) |
| 169-F | 6 | +`169.008-T` (structural test); −`169.004-T`, `169.006-T` returned |
| 170-F | 10 | +`170.010-T` (validator, plan T1); nine retitled to plan T2–T10 |
| 171-F | 10 | +`171.013-T`/`171.014-T` (T4b/T5b splits); −four returned |
| 172-F | 7 | unchanged; `172.007-T` respecified as invariant-based |
| 173-F | 10 | +`173.008-T`, `173.009-T`, `173.010-T`; plan T8 is chore `002-C`, outside the feature |

Sizing provenance moved to the canonical `ah-stage-sizing-v1`
(`docs/size-complexity-reference.md` line 77) for all 50 in-scope tasks, size
and complexity written in separate calls per the two-axis contract. Zero
unsized shipment members. The six returned tasks keep their original
`autoharness-2h-v1` provenance as historical record. Two `complexity: high`
tasks remain in the workspace — `169.004-T` and `171.010-T` — both descoped and
in no shipment.

## Checkpoint supersession

`checkpoint-20260918-052706.json` placed domain data in a **top-level
`progress`** object. Backlogit's own V1 schema permits that key, so
`checkpoint get` reports `valid: true` — this is a *harness-contract*
violation, not a tool validation failure.

It was **not hand-edited**. A compliant superseding record,
`checkpoint-20260918-065902.json`, was created through
`backlogit checkpoint create` with `progress` nested under `context`, the
blocker text corrected to `TO BE FIXED BY 176-S`, and `supersedes_checkpoint` /
`supersession_reason` recorded. Both are `resolved`; **zero active checkpoints
remain** (53 total).

## Scope extensions (flagged deliberately)

Finding 1 named four plans. I also flipped the **P-004** and **checkpoint**
plans from `requires_plan_hardening: "no"` to `"yes"` and authored records for
them, because both change `schemas/` or instruction files plus multiple
template-family mirror pairs — enumerated P-006 elevated-blast-radius signals —
and their four siblings declare `yes` for the same class. Flagging rather than
burying this: it is a judgement call beyond the literal finding.

## Review artifact restructuring

The six combined cycle-1+2 review files were `git mv`'d to
`docs/reviews/review-history/*-attempts-01-02-combined.md` and **preserved
verbatim**, with only classification frontmatter added. They were deliberately
*not* retroactively split into two attempt files — fabricating two
independently-authored records from a document never authored that way would be
provenance forgery, and it would violate the never-delete/classify-don't-rewrite
principle the single-governing-plan work establishes.

Six new immutable `-attempt-03.md` artifacts re-review plan revision 3. Six
small latest-verdict manifests sit at the original review paths. All six:
**PASS, 0 P0, 0 P1**.

## Validation

* `python -m unittest discover -s tests` → **2344 tests OK**, 54 skipped.
* Frontmatter + cross-reference integrity over all 26 portfolio artifacts →
  **0 problems, 0 dangling references**. (Repo-wide, many *pre-existing*
  unrelated docs lack `description`/`doc_type`; untouched.)
* `backlogit doctor` → only pre-existing archive-record findings, none from
  this portfolio.
* All six shipment manifests match their plan task counts.

## Not acted on

Python-reviewer findings against
`docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md` — declared a
false positive by the operator, outside commit `1b6a312d`. Confirmed untouched.

## Next

Next-eligible shipment: **`176-S`** (also unblocked: `169-S`, `175-S`).
Stage must not claim it — hand to Orchestrator for Ship evaluation.
