---
session: stage
date: 2026-09-07
operator_request: "Compound-learn from Copilot review patterns; proactively detect before PR; bake methodology into the harness"
shipment_created: 170-S
feature_created: 162-F
tools: "backlogit MCP DEGRADED (transport closed) — CLI fallback used throughout"
source: docs/memory/2026-09-07-stage-review-pattern-learning-session.md
doc_type: memory
tags: [stage, review-pattern, compound-learning, pr-436, harvest, shipment]
---

# Stage session — hosted-review pattern learning (2026-09-07)

## What was asked

Inventory every Copilot finding on PR #436, derive the pattern taxonomy,
compound-learn it, run an adversarial re-review to find what Copilot missed,
and bake the whole loop into the harness workflow. Explicitly **not**: touch
PR #436, run a fifth fix cycle, implement anything, or invoke Ship.

## Tool status

* `TOOL_DEGRADED: backlogit MCP — MCP request failed: Transport closed.`
  CLI fallback (`backlogit` v1.10.1) used for every backlog operation.
  Declared, not silent.
* `INDEX_SYNC_OK (CLI fallback)` at session start (1144 artifacts) and again
  at session end.
* Model-specific review dispatch unavailable →
  `TOOL_DEGRADED: model-specific-review-routing — declared fallback:
  same-model inline rubric pass` (applies to both the adversarial review and
  plan-review).

## Key findings

**Inventory.** 34 reviews (15 Copilot), 39 inline comments (20 Copilot),
20 threads (19 resolved, 1 open), **36 suppressed findings** in review bodies,
5 operator issue comments, 13 documented rounds. **56 raw utterances → 24
distinct findings → 12 root-cause classes.** 100% escaped local review + CI.

**The three dominant classes** are all structural, not careless:

* **RC-9 current-HEAD readiness drift (8)** — self-generating: recording
  readiness creates a new commit.
* **RC-11 pre/post-mutation chronology falsification (8)** — a *correct*,
  byte-identical post-hoc reconstruction read as compliant pre-mutation
  evidence for five rounds.
* **RC-10 propagation incompleteness (7)** — rounds 6-9 were spent entirely
  on one fact that had seven homes.

**"Zero new threads" was a false convergence signal five times.**
`ad4cb74a` generated literally zero comments; four substantive rounds followed.

**Adversarial re-review** at `659c8e75` found **0 P0, 7 P1, 3 P2, 1 P3 →
`BLOCKED`**. Four P1s reproduce unfixed Copilot round-13 findings; three are
genuinely new — most importantly **AF-05**: both P-005 remediation conditions
exist only in prose, so `_closure_artifact_complete()` returns `True` and
`closure_complete('159-S')` unblocks successors today. That is the **third
recorded recurrence** of the `114-S` lesson *"a stated closure condition is
only real if the code actually enforces it."*

**AF-07's structural root cause** (the currently open thread): the `856B6770`
disposition *was* written — into the **working tree**, uncommitted, because
stash edits are Stage-owned and Ship correctly refused (P-021 capture-only).
No workflow step hands a Ship-observed Stage-owned currency gap back to Stage
before readiness is claimed. That gap is now task **162.011-T**.

## Decisions

Six, recorded in
`docs/decisions/2026-09-07-review-pattern-learning-methodology-deliberation.md`:
retrieval at `review` Step 1.5 (before routing, so it can influence routing);
a new conditional **Evidence Consistency Reviewer** persona; a bounded
mechanical **post-fix delta check** for the four mechanisable classes;
synthesis once at closure with a **5-signal promotion threshold**;
five workflow-evidence metrics (no telemetry engine); six surfaces + tests,
foundation files get a pointer only.

## Artifacts

| Artifact | Path |
|---|---|
| Finding inventory | `docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md` |
| Adversarial review | `docs/reviews/2026-09-07-pr-436-adversarial-review.md` |
| Compound learning | `docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md` |
| Deliberation | `docs/decisions/2026-09-07-review-pattern-learning-methodology-deliberation.md` |
| Plan (hardened, PASS) | `docs/plans/2026-09-07-review-pattern-learning-methodology-plan.md` |

All five: frontmatter valid, zero unresolved placeholders, all
cross-references resolve, `markdownlint` exit 0.

## Backlog

* Feature **162-F**, tasks **162.001-T … 162.013-T** (13), shipment **170-S**
  (14 items, 0 unsized, `M:4 S:7 XS:2`).
* Dependencies: 18 intra-shipment edges enforcing test-first ordering;
  shipment-level `170-S → 169-S` and `170-S → 162-S`.
* **Not routed to Ship** — deliberately. `#436`/`159-S` closure is still
  active and `169-S` is queued ahead.

## Self-caught error worth remembering

The plan and task 162.004-T initially specified
`templates/agents/subagents/` as the persona template mirror. **That directory
does not exist** — personas install to `.github/agents/subagents/` but their
templates live in `templates/agents/review/*.agent.md.tmpl`. The names do not
mirror. Caught by the cross-reference existence check, not by reading. This is
**RC-1 / producer-consumer naming**, i.e. exactly the class this session was
documenting, committed while documenting it. Both artifacts corrected and the
path contract is now stated as binding in the task.

## Next steps

1. **Operator** decides whether to authorise a further PR #436 round for
   `846D0282` (four unfixed evidence defects, incl. the false
   `Copilot review SATISFIED` claim and the impossible disposition date).
2. **Stage** triages `0BE73C89` (AF-05, needs deliberation), `9E22BFC6`
   (858B-remediation shipment has no identity), `27F9EC8A` (commit the
   already-written `856B6770` disposition), `AFEFC6AB` (frontmatter outcome
   contracts, needs deliberation).
3. **Ship** executes `170-S` only after `169-S` and `162-S` clear.
