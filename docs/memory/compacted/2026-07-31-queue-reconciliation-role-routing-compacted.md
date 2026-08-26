---
title: Compacted memory — Queue reconciliation (084-F/107-S) and role-based model routing (104-F/108-S)
doc_type: memory
memory_class: compacted
created: 2026-07-31
scope: stage-session-pair
shipment: [107-S, 108-S]
feature: [084-F, 104-F]
consolidates:
  - docs/archive/memory/2026-07-31-stage-group-and-stage-next.md
  - docs/archive/memory/2026-07-31-stage-role-model-routing.md
---

# Compacted: Stage sessions 2026-07-31 — queue reconciliation + role-based model routing

## Session 1 — Group-and-stage-next (084-F / 107-S)

**Queue reconciliation.** Archived 2 stale completed deliberations (`008-DL`, `009-DL`) and 9
stale completed features (`093-F`, `094-F`, `095-F`, `096-F`, `097-F`, `098-F`, `099-F`,
`101-F`, `102-F`) after verifying archived shipment history and terminal children. Cleared
`084-F`'s satisfied dependency on archived `079-F`; backlogit disallowed a direct
blocked→queued transition, so `084-F` was resumed via the allowed **blocked→active**
transition and became the sole active top-level release unit.

**Decision**: selected `084-F` as the next actual unimplemented release unit. Plan
`docs/archive/plans/2026-07-31-token-efficiency-telemetry-emission-plan.md` — P-006 hardening
required and completed; final review PASS under declared single-agent persona degradation
after one fix cycle.

**Harvest**: 8 S-sized, dependency-wired tasks `084.001-T`…`084.008-T` (roots
`084.001-T`/`084.002-T`; `084.003-T` deps on both; `084.004-T` deps on `001`; `084.005-T` deps
on `003`+`004`; `084.006-T` deps on `003`+`005`; `084.007-T` deps on `006`; `084.008-T` deps
on `004`+`006`). Shipment **107-S** created, status queued, **task-only** manifest.

**Correction (important, from PR #272 Copilot re-review)**: the covering feature `084-F` was
**not** a manifest member — coverage is derived from task `parent_id`, and `084-F` closes
separately. Earlier text that listed `084-F` as a shipment member was **inaccurate** and was
corrected; this is the same task-only convention documented elsewhere (097-S contract).

**Deferred**: `085-F` blocked by `084-F`; `077-F`/`080-F`/`081-F`/`082-F` remain
operator-decision/access-gated; stash `2970FA4E` (self-repair, decision-gated) low-priority
and unharvested.

## Session 2 — Role-based model routing (104-F / 108-S)

Staged the operator's role-based model routing enforcement requirement end-to-end: stash
`EEAFA73C` → deliberation `010-DL` (**Option C** chosen — hybrid role→route resolution +
fail-closed verification) → plan (P-006 hardened, PASS inline review, 0 blocking / 3
residual) → feature `104-F` + 9 dependency-ordered tasks `104.001-T`..`104.009-T` (all size S,
≤2h, width-isolated).

**Key architectural finding**: the desired role→model mapping already existed as *advisory*
frontmatter (`_stage`→claude-opus-4.8, `_ship`→claude-sonnet-5) and config tier bindings
(tier3=opus-4.8, tier2=sonnet-5) — but nothing enforced it. The real defect was
**invocation-time**: the Orchestrator template's Steps 1/2 invoke Stage/Ship with **no
explicit model-override directive**, and `verify_workspace` checked only
`max_subagent_tier` — so routing silently defaulted with nothing failing. Fix = config role
routes (reusing the `anchor_review` named-route precedent) + an explicit invocation directive
with `ROUTING_DEGRADED` fallback + fail-closed red-green verifier assertions. Constraint:
preserve P-013; do **not** reintroduce the retired `model_tier` field (053.004-T precedent).

**Shipment**: `108-S` created **`status: blocked`**, dependency-gated behind `107-S`
(`108-S depends_on 107-S`, blocks) — deliberately not queued/claimable yet; it transitions to
`queued` only after `107-S` ships. This is the handoff token to Ship, but Ship must **not**
claim it prematurely.

**Operator decisions left open** (unresolved at session end): (1) whether the auto-escalation
routing clause is a new P-013.5 sub-clause or amends P-013.4 (naming); (2) exact skill-
delegation contract file for the routing clause (later resolved as task `104.005-T`); (3)
whether role-route defaults belong in the versioned `1.0.0` schema examples.

## Cross-cutting notes

* Both sessions confirm the **task-only manifest convention** (097-S contract): a covering
  feature is never a shipment manifest member; it is derived via task `parent_id` and closed
  separately after all its tasks ship.
* **Dependency-gated shipment chains**: when multiple release units are staged in sequence
  (`107-S` → `108-S`), the successor is created `blocked` (not `queued`) with an explicit
  `depends_on` edge, and only transitions to `queued` once its predecessor ships — this is the
  scheduling mechanism used repeatedly in later, larger serial chains (109-F topology-gate
  saga, Plan 1 supervisor work).
* Backlogit's `blocked → queued` transition does **not** exist directly on features; use the
  allowed `blocked → active` transition instead when resuming a feature whose blocking
  dependency has been satisfied.

## Outcome / handoff

Both sessions left artifacts uncommitted for the Orchestrator to publish (per operator
instruction). Handoff order: `107-S` (queued, unclaimed) ships first; `108-S` (blocked until
`107-S` ships) follows. No implementation, build/test, branch, commit/push, PR, or shipment
claim was performed in either session; Ship was not invoked.
