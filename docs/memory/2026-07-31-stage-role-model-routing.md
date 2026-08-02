---
title: "Stage session — role-based model routing enforcement (104-F / 108-S)"
date: 2026-07-31
agent: Stage
invoked_on: claude-opus-4.8
mode: sequential / non-dark / planning-overlap / Stage-only
tools: backlogit MCP+CLI OK; INTERCOM_DEGRADED, ENGRAM_DEGRADED, GRAPHTOR_UNAVAILABLE
---

## Outcome

Staged the operator's role-based model routing enforcement requirement from stash
intake through a reviewed, decomposed, dependency-blocked shipment.

* Source stash: `EEAFA73C` (archived after harvest).
* Deliberation: `010-DL` (Option C chosen — hybrid role→route resolution + fail-closed verification).
* Plan: `docs/archive/plans/2026-07-31-role-based-model-routing-enforcement-plan.md` (P-006 hardened; inline plan-review PASS, 0 blocking / 3 residual; archived post-merge 2026-08-01, superseded by `docs/plans/2026-07-31-role-based-model-routing-enforcement-decided-plan.md`).
* Feature: `104-F`. Tasks: `104.001-T`..`104.009-T` (all size S, ≤2h, width-isolated).
* Shipment: `108-S`, `status: blocked`, dependency-gated **behind `107-S`** (`108-S` depends_on `107-S`, blocks). It is NOT queued/claimable yet: its reviewed published status stays `blocked` until `107-S` ships, at which point it transitions to `queued`.

## Key architectural finding

The desired mapping already exists as advisory frontmatter (`_stage`→claude-opus-4.8,
`_ship`→claude-sonnet-5) and config tier bindings (tier3=opus-4.8, tier2=sonnet-5).
The real defect is **invocation-time**: Orchestrator template Steps 1/2 invoke
Stage/Ship with no explicit model-override directive, and `verify_workspace` checks
only `max_subagent_tier` — so routing silently defaults with nothing failing.
Fix = config role routes (reusing anchor_review named-route precedent) + explicit
invocation directive with ROUTING_DEGRADED fallback + fail-closed red-green verifier
assertions. Preserve P-013; do NOT reintroduce `model_tier` (053.004-T).

## Operator decisions still pending

1. P-013.5 new sub-clause vs amend P-013.4 (naming).
2. Exact skill-delegation contract file for the routing clause (T5 / `104.005-T`).
3. Whether role-route defaults belong in the versioned `1.0.0` schema examples.

## Handoff

`108-S` is the handoff token to Ship. `108-S` is currently `blocked` (not queued,
not claimable): its dependency on `107-S` must clear first. Ship must NOT claim
`108-S` until `107-S` ships; only after `107-S` ships does `108-S` transition from
`blocked` to `queued` and become claimable (dependency-enforced). Stage performed
no implementation, no build/test, no
branches, no commits/push, no PR, and did not invoke Ship. Planning artifacts
(plan doc, this memory) left uncommitted per operator instruction.

## Next cycle inputs

`107-S` (queued, unclaimed) precedes `108-S` (blocked until `107-S` ships). Stash `2970FA4E` remains deferred
(low, decision-gated) — left intact.
