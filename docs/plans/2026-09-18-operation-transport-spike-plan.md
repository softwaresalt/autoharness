---
title: "Bounded spike: autoharness operation transport — MCP/sidecar feasibility and distribution impact"
description: "Time-boxed spike deciding how autoharness exposes Python-backed atomic operations to agents over MCP, and what that costs a PyPI-distributed CLI whose entire runtime dependency set is jsonschema and PyYAML. Produces a findings artifact with a measured comparison, a recommendation, a rejected alternative, the .mcp.json registration shape, and the CLI/MCP parity-test strategy. No production code ships. Gates the transport half of the operation substrate foundation."
doc_type: plan
source: docs/plans/2026-09-18-operation-transport-spike-plan.md
date: 2026-09-18
plan_id: operation-transport-spike
plan_path: docs/plans/2026-09-18-operation-transport-spike-plan.md
plan_role: active
revision: 1
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document authored under the strategic redesign, not a remediation of a prior revision. It carries REMEDIATED-PENDING-REVIEW because it awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-operation-transport-spike-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 71200CBB
  - 76EBDE6D
feature_id: 176-F
shipment_id: 182-S
unit_role: precursor-spike
gates: 184-S
requires_plan_hardening: false
hardening_rationale: "Time-boxed research producing a findings document. Ships no code, mutates no template, touches no policy, and changes no installed surface. Blast radius is one new file under docs/spikes/."
tags:
  - spike
  - mcp
  - transport
  - distribution
  - precursor
---

# Bounded spike: autoharness operation transport

## Problem frame

Two release units in this portfolio specify an MCP-reachable operation, and
neither can be planned honestly today.

* `180-S` specifies a "guarded MCP create" for checkpoints. Attempt-08 finding
  `B3` recorded that the plan "names no MCP server that exposes it, no owner
  that implements it, and no registration step that makes it callable."
* `176-S` requires an "MCP parity boundary" for the P-004 gate. Attempt-08
  finding `B6` recorded that the gate is CLI-only, so an agent operating
  through MCP crosses no gate at all.

Both findings have the same cause: **there is no `autoharness` MCP server, and
whether there can be one is unresearched.**

`.mcp.json` registers six servers — `backlogit`, `engram`, `graphtor-docs`,
`context7`, `tavily`, `github`. `autoharness` is not among them.
`pyproject.toml` declares exactly two runtime dependencies (`jsonschema`,
`PyYAML`) and ships a console script. There is no MCP SDK, and adding one to a
PyPI-distributed CLI has consequences this repository has already paid for once
(`docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md`).

Writing a plan over that unknown is what produced eight review cycles. This
spike exists so the foundation plan can be written over a measured answer.

## Questions

| # | Question | Decided by |
|---|---|---|
| Q1 | Hand-rolled JSON-RPC-over-stdio, or an MCP SDK runtime dependency? | T1 measurement + T2 prototype |
| Q2 | What is the wheel/install-size and dependency-tree cost of each? | T1 |
| Q3 | Does either option constrain `requires-python >=3.10`? | T1 |
| Q4 | What is the `.mcp.json` registration entry for an `autoharness` server? | T2 |
| Q5 | How does a test prove CLI and MCP expose the same operation set? | T2 |
| Q6 | Does the recommendation change the PyPI distribution contract? | T3 |

## Out of scope

* Any production code. The T2 prototype is **discarded**; only findings survive.
* Any change to `.mcp.json`, `pyproject.toml`, or any agent surface. Those are
  activation steps and belong to `184-S`.
* Choosing which operations to expose. That is the foundation's concern.

## Tasks

| ID | Task | Size | Complexity |
|---|---|---|---|
| `176.001-T` | Inventory both options; measure distribution impact | XS | low |
| `176.002-T` | Prototype registration + parity-test shape on a throwaway operation | S | medium |
| `176.003-T` | Author the findings artifact with recommendation and rejected alternatives | XS | low |

Sequence: `176.001-T` → `176.002-T` → `176.003-T`.

## Deliverable

`docs/spikes/2026-09-18-autoharness-operation-transport-findings.md`, containing:

1. the measured comparison table for Q1–Q3;
2. the recommended transport, with its rationale;
3. the rejected alternative, with the reason it was rejected;
4. the exact `.mcp.json` registration shape (Q4);
5. the parity-test strategy (Q5);
6. an explicit statement of whether the PyPI distribution contract changes (Q6).

This artifact is the **input contract** for
`docs/plans/2026-09-18-operation-substrate-transport-plan.md`. That plan must
not be harvested into executable tasks that assume a transport before this
artifact names one.

## Time box

The spike is bounded at the three tasks above. If Q1 cannot be resolved within
that bound, the findings artifact records the unresolved question and
recommends the **CLI-only** fallback (see R1), rather than expanding.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Both transport options prove unacceptable for a PyPI CLI | The CLI transport in `184-S` is unconditional and ships regardless. The sidecar degrades to a separately-installed optional surface, and the parity requirement is restated against that surface. Consuming units are told this explicitly rather than inheriting a silent gap. |
| R2 | The prototype is mistaken for shippable code | `176.002-T` states discard explicitly, and no task in `184-S` depends on prototype artifacts — only on the findings document. |
