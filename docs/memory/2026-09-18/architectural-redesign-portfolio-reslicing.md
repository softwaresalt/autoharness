---
title: "Stage session memory — architectural redesign and portfolio re-slicing"
description: "Session record for the 2026-09-18 Stage session that replaced symptom patching of six terminally blocked defect units with a shared execution architecture decision, four precursor foundations, two bounded spikes, eleven revision-1 plans and a rewired precursor-first shipment DAG."
doc_type: memory
source: docs/memory/2026-09-18/architectural-redesign-portfolio-reslicing.md
date: 2026-09-18
agent: stage
branch: chore/stage-176-s-workflow-defects
parent_head: db2afc9a
---

# Stage session — architectural redesign and portfolio re-slicing

## Mandate

Six defect units (`176-S`–`181-S`) were terminally blocked at plan-review
attempt 08 with an aggregate 4 P0, 34 P1 and 11 P2. The operator authorized a
strategic redesign rather than a ninth patching round: decide the shared
execution architecture first, adopt inert PREPARE → VERIFY → ACTIVATE rollout,
choose a compatibility strategy, create foundational precursors, re-slice the
defect units around them, and validate composed state machines before harvest.

## The frame error that was fixed

Every one of the six plans specified a **consumer** of a producer that no plan
in the portfolio built. Four separate units were each independently assuming
the same four missing producers — an operation boundary, safety primitives, a
manifest-compatible review recorder, and an installed harness-generation actor.
Two of the four P0s were therefore **unfixable locally**: patching a consumer
cannot create its producer.

## Research that changed the design (all reproducible)

* `cli.py` has a hand-rolled ten-command argv dispatch and no argparse
  subparsers; `gate` is the multi-level exemplar to follow.
* `.mcp.json` registers six servers; **`autoharness` is not one of them**, and
  `pyproject.toml` declares exactly two runtime dependencies with no MCP SDK →
  the transport is unresearched → bounded spike `182-S`.
* `templates/skills/harness-architect/SKILL.md.tmpl` exists but
  `.github/skills/harness-architect/` does **not**, while installed policy
  P-004 names `ship (via harness-architect skill)`.
* P-004's live precondition **already** requires `py_compile` exit 0 — so the
  attempt-08 P0 is a regression against policy, not a policy gap.
* Verdict manifests are **three shapes**, not one: Family A (6), Family B (1,
  governing the untouchable `175-S`), and the legitimate pre-review Family C.
  A closed eight-key format would reject all seven live records.
* 134 checkpoint records exist; **two are torn mid-write at exactly their file
  length** — observed partial writes, not hypothetical.
* The review-verdict consumer set is closed at **exactly four** tracked
  surfaces; `.autoharness/staging/` is gitignored generated output and must be
  excluded by rule.
* Harvest reads an inline `decision: PASS` from the **plan body** and never
  opens the manifest.
* The `176-S` "DAG root" was a false star: five edges all pointing at one node.

## What was decided

Eight decisions (D1–D8) in
`docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md`.
The load-bearing ones:

* **D1** — safe operations are Python functions with typed results, atomic
  writes, fixed argv under `shell=False`, path containment, registered once and
  exposed through two transports derived from one registry. Agents invoke by
  name. **The agent never holds the sensitive value** — `ensure-branch` takes a
  shipment ID, not a branch name.
* **D2** — PREPARE (inert) → VERIFY (evidence) → ACTIVATE (one task, one
  commit across every template, mirror, registry, permission and consumer).
  **Sequential task edges are not atomic.**
* **D3** — versioned total `normalize()` → canonical form open at the boundary
  and closed at the core → strict validation. Quarantine is a typed record.
  Immutable history is never rewritten.
* **D4** — P-004 bootstraps on a real installed actor; waiver, force flag and
  policy edit were all evaluated and rejected.
* **D5** — SAFE_CLOSE conformance moves to isolated Linux CI; the
  administrative-close transition is **removed**, not deferred.

## What was built

| Unit | Shipment | Feature | Tasks |
|---|---|---|---|
| S1 operation-transport spike | `182-S` | `176-F` | 3 |
| S2 conformance-isolation spike | `183-S` | `177-F` | 3 |
| P1 operation substrate + transports | `184-S` | `178-F` | 6 |
| P2 safe operation primitives | `185-S` | `179-F` | 9 |
| P3 review-authority foundation | `186-S` | `180-F` | 10 |
| P4 Ship harness lifecycle | `187-S` | `181-F` | 5 |

Plus eleven revision-1 plans, eleven pre-review (Family C) verdict manifests,
and hardening reviews on the nine high-risk plans.

## DAG

Roots: `182-S`, `183-S`, `177-S`. Verified acyclic over 871 edges / 717 nodes.
All eleven shipment manifests equal their covering feature's descendants
exactly. All 36 precursor tasks and all retained defect tasks carry both `size`
and `complexity`.

## Honest residuals

* **`abandoned` is unreachable to Stage.** `backlogit` rejects
  `queued → abandoned` and `blocked → abandoned`; the only path runs through
  `active`, requiring a Ship claim (P-010). `179-S` was **archived** instead.
* **`176-S` now sits behind `185-S` and `187-S`**, and the pre-existing
  `168-S → 176-S` edge places the older SHIP-10 chain behind the precursors.
  Real consequence, disclosed rather than hidden.
* **Task-level re-harvest of the five retained defect units is gated** on the
  foundations that define their calling conventions. Harvesting against an
  assumed signature is the exact defect this redesign removes.
* Engram circuit open and Intercom unavailable for the whole session; all
  research was direct reads plus backlogit SQL.

## Next session

Independent plan-review attempt 1 against the eleven revision-1 plans, starting
with the roots (`182-S`, `183-S`, `177-S`). No plan in this portfolio carries a
PASS, and none was self-reviewed.
