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

## Addendum: PR #513 review-fix cycle 1 (2026-10-12 UTC)

Append-only. The cycle 1 and cycle 2 records and the verdict above are unchanged. After the
staging PR (#513) received a Copilot review (review 5487147517, HEAD `cc06f41e`), Stage fixed
the findings that touch this plan and re-checked only the changed units as a single-agent
delta pass (same `TOOL_DEGRADED` declarations as above).

| Review thread | Change to this plan or its tasks | Commit |
|---|---|---|
| `PRRT_kwDORzpWpM6rWUWn` (missing B3b to B4 edge) | No plan change: the graph and the `208.005-T` note already declared `B3b -> B4`. The backlog edge `208.005-T` depends on `208.004-T` was added; an audit of every `207.*` and `208.*` task against both plan graphs and all task notes found no other missing edge | `d12a3979` |
| `PRRT_kwDORzpWpM6rWUXL` (empty `model_provider`) | B1 gains a no-`model_provider` vector; the error was in deliberation D4, now corrected (only `model_family` is mandatory) | `82c8308c` |
| `PRRT_kwDORzpWpM6rWUXr` (registry cannot see workspace-authored agents) | B2 is disk-first with a manifest left-join, adds manifest-orphan and conflict cases and three fixtures; B6, B6a, B7 text updated; B2 resized `S` to `M` | `78f88268` |
| `PRRT_kwDORzpWpM6rWUYJ` (purity not enforced) | B1 runs through the R1-A `forbid_io()` guard; B2's read-only claim is asserted by a tree-snapshot test | `b62cb4d1` |
| Operator answer to `040-DL` OQ1 to OQ9 | OQ9 (the B5 marker bump) confirmed 2026-10-12: the B5 checkpoint text now says Ship cites the recorded confirmation; no B5 scope change | `96a4503b` |

Delta persona pass over the changed units:

* **Architecture Strategist.** Disk-first enumeration then a left-join to the manifest is the
  same shape `frontmatter_conformity` already uses (`_fc_enumerate_targets` plus
  `_fc_classify`), so the unmanaged branch is now reachable. The registry return type
  became `SiteRegistry(sites, orphans, conflicts)`; B6 and B7 were updated in the same
  revision. The plan dependency graph is unchanged and acyclic, and the backlog now encodes
  every plan edge.
* **Python Reviewer.** The `verify_workspace` import cycle (it imports this module) is
  handled by function-local import or injection plus a standalone-import test.
  Containment and symlink checks precede every read.
* **Scope Boundary Auditor.** Still one concern and two files in B2; no new config key or
  routing value. The resize to `M` reflects volume only (complexity unchanged).
* **Learnings Researcher.** The managed versus workspace-authored provenance split from
  `037-DL` is reused, not reinvented.

New findings: **B-F9 [P3]** the registry return type changed shape; consumers were updated
together, acknowledged. **B-F10 [P3]** a workspace-authored agent has no default tier, so B7
compares it only when it is bound (an unbound one is skipped); this is now stated in B7 and
tested, acknowledged. No P0, P1, or P2 findings. The delta check supports the existing
verdict: the plan remains **PASS**. The statement above that OQ9 "blocks safe execution"
describes the plan as reviewed; OQ9 was confirmed afterwards (see the plan's "Unresolved
operator decisions" paragraph).
