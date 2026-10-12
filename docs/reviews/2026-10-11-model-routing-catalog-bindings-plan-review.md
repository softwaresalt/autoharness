---
title: "Plan review: model routing catalog and bindings with schema 1.2.0 (R1-B)"
description: "Multi-persona plan review of docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md, run as a single-agent declared-degradation pass. Cycle 1 failed on a P1 (no render-time composition unit for bound subagents); the plan was revised with unit B6a and cycle 2 passes."
doc_type: review
review_target: docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md
dispatch_mode: single-agent-declared-degradation
decision: PASS
review_cycles: 2
reviewed_utc: 2026-10-12
---

# Plan review: model routing catalog and bindings with schema 1.2.0 (R1-B)

Review gate for `docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md`
(deliberation `040-DL`, stash `BF66F08B`). Dates are UTC.

dispatch_mode: single-agent-declared-degradation

decision: PASS

## Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch` — no reviewer subagent dispatch surface in
  this Stage session. Declared fallback: single-agent persona pass; every selected persona
  applied inline.
* `TOOL_DEGRADED: model-specific-review-routing` — `model_routing.anchor_review` is not
  dispatchable from this session. Declared fallback: same-model rubric pass for the
  cross-model personas.

## Persona coverage

| Persona | Mode | Triggered | Findings |
|---|---|---|---|
| Constitution Reviewer | inline pass | always-on | B-F5 (P3) |
| Python Reviewer | inline pass | always-on | B-F2 (P2, fixed) |
| Scope Boundary Auditor | inline pass | always-on | B-F4 (P2, fixed) |
| Learnings Researcher | inline pass | always-on | B-F3 (P2, fixed), B-F8 (P3) |
| Architecture Strategist | inline pass, same-model fallback | always | B-F1 (P1, fixed), B-F6 (P3) |
| Agent-Native Parity Reviewer | inline pass, same-model fallback | not triggered: no new agent-facing action in this release (the CLI is R1-A) | none |
| Security Lens Reviewer | inline pass, same-model fallback | judged not triggered: no auth, secrets, or new trust boundary; cross-provider exposure is operator data | B-F7 (P3, noted) |

## Findings

### Cycle 1 (decision before revision: FAIL)

* **B-F1 [P1] Architecture Strategist.** No unit made the render loop honor a binding.
  Subagent frontmatter renders from the global `TIER_<N>_*` variables, and the only
  per-artifact variable composition is the role overlay (`_resolve_artifact_role` and
  `_compose_artifact_variables`) for `_stage` and `_ship`. A bound agent would therefore
  render with its template tier values, so after a `tune` refresh its installed frontmatter
  would disagree with the render-parity check, and B7's fail-closed drift check and the
  render check could not both pass. This would also leave bindings declared in config but
  unable to be applied by install, the exact "accepted but inert" defect the release exists
  to remove. **Fixed:** new unit **B6a** adds a site overlay in the render loop (bound agent's
  four route variables come from the resolver; unbound and pipeline artifacts render
  byte-identically), new invariant **I9**, a ProposedAction row, a requirements-trace row
  (RB2a), a dependency-graph update (`B6 -> B6a -> B7`), and install-harness wording (B8).
* **B-F2 [P2] Python Reviewer.** B2 parsed template frontmatter with YAML, which can fail on
  unquoted `{{...}}` values (for example the `tools:` line in `_stage`). **Fixed:** B2 uses a
  targeted regex over the frontmatter block for the `{{TIER_<N>_FAMILY}}` variable.
* **B-F3 [P2] Learnings Researcher.** B8 and B9 edit global, non-rendered skills; per
  `docs/compound/096-S-template-vs-global-skill-placeholders.md` they must read values from
  the config at runtime and not rely on install-time placeholders. **Fixed:** both units
  state the rule.
* **B-F4 [P2] Scope Boundary Auditor.** `tests/test_context_tier_tune_guidance.py` pins
  prose in the install and tune skills that names `schema_version: "1.1.0"`; B8 could break
  those pins without budgeting for them. **Fixed:** B8 forbids editing pinned strings and
  budgets a meaning-preserving pin update only if the example config must change.
* **B-F5 [P3] Constitution Reviewer.** B4 is `harness-surface:none` (schemas and tests, no
  `src/` file), so the harness-architect imposes no RED roster; tests-first still applies.
  **Acknowledged:** the unit lists its tests and the implementer writes them first.
* **B-F6 [P3] Architecture Strategist.** Binding syntax is validated by the schema pattern
  and existence by the registry (two layers). **Acknowledged;** documented in B4 and B6.
* **B-F7 [P3] Security Lens Reviewer (noted, not triggered).** `routes` accepts any provider
  string by design (Core Rule 3). The release ships no routing data, so no data leaves the
  workspace because of it. Provider mix and egress remain `040-DL` OQ1, operator authority.
* **B-F8 [P3] Learnings Researcher.** Schema-mirror immutability
  (`docs/compound/2026-08-08-*`, `2026-08-30-*`) is respected: B4 forbids editing 1.1.0 and
  B5 pins it. **Acknowledged.**

### Cycle 2 (re-review after the fixes)

Re-checked B6a against the render-loop pattern it extends (file budget 2; depends on B6;
acceptance requires existing render-parity tests unchanged and byte-identical unbound
renders). Re-checked the graph: `B1 -> B2`; `B3a -> B3b -> B4 -> B5`;
`{B1, B2, B5} -> B6 -> B6a -> B7`; `B5 -> B8`; `{B7, B8} -> B9 -> B10 -> B11`. It is acyclic
and serial on the three shared files. No new findings.

## Hardening and verification gaps

Plan hardening was required (`Requires plan hardening: yes`) and is present: invariants I1
to I9, `ProposedAction`/`ActionRisk` table including the operator-owned config edit, added
verification, closure and rollback detail, operator checkpoints, and the review-gate
capability-risk declaration. Runtime verification and closure are specified for B4/B5,
B6/B7, B8, and B9. The one decision that blocks safe execution (`040-DL` OQ9, the dogfood
`schema_version` marker) is explicit, scoped to B5, and has a recommended default.

## Gate decision

Cycle 1 had one P1 and therefore failed. The plan was revised and re-reviewed; no P0 or P1
findings remain and the P2 findings were fixed. Decision: **PASS**. P3 items are
acknowledged for awareness.
