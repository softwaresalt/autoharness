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

## Addendum: PR #513 review-fix cycle 2 (2026-10-12 UTC)

Append-only. The cycle 1 and cycle 2 records, the cycle 1 addendum, and the verdict above are
unchanged. The staging PR (#513) received a second Copilot review (review 5494415746, HEAD
`e0051e68`) with three findings, all touching this plan. Stage verified each against the
repository, fixed it, and re-checked only the changed units as a single-agent delta pass
(same `TOOL_DEGRADED` declarations as above). The graph statement in the cycle 1 addendum
("the backlog encodes the `B3b -> B4` edge") described that state; the edge now reads
`B3b -> B5`, as below.

| Review thread | Verification and change | Commit |
|---|---|---|
| `PRRT_kwDORzpWpM6rkjC9` (`model_routing` still open to arbitrary keys) | Confirmed: `model_routing` has no `additionalProperties` in the root schema or the 1.1.0 mirror (the dogfood config carries no unknown key). Decision: B4 closes `model_routing` with an allowlist in the **1.2.0 schema only** (1.1.0 untouched, so I1 and I2 hold); B1 exports `MODEL_ROUTING_KNOWN_KEYS`; B6 adds `routing_unknown_keys` (fails at 1.2.0 with `ROUTING_UNKNOWN_KEY`, one advisory per key below 1.2.0, the same gate as the anchor check); regression cases for `routez` and an inert `subagents` block at the schema and verify layers, and a 1.1.0 stays-valid case | `e21a9502` |
| `PRRT_kwDORzpWpM6rkjDk` (a deliberately red boundary between B4 and B5) | Confirmed: the four B3 modules validate current-version fixtures and the dogfood config against both the root and the current mirror, which read the contract version (1.1.0 until B5), so the root const at 1.2.0 in B4 made them red. B4 now only publishes the unreferenced 1.2.0 mirror (2 files); B5 is the single atomic cut-over (root schema content, `current_version`, `known_versions`, migration entry, byte pin, lockstep test, dogfood marker, manifest hash), resized `S` / `low` to `M` / `medium`; edges: `208.005-T` no longer depends on `208.004-T`, `208.006-T` now does; invariant I10 | `789f5748` |
| `PRRT_kwDORzpWpM6rkjEC` (alias check only in `verify-workspace`) | Confirmed (see the R1-A review addendum). B6's alias check now delegates to the shared R1-A function `model_routing_yaml.check_model_routing_yaml` (`207.006-T`); B6 defines no scanner and tests delegation | `7ba1193a` |

Audit for the same "intermediate red" pattern across all of R1-B: B1, B2, B3a, B3b, B4 (now),
B6, B6a, B7, B8, B9, B10, and B11 each leave the suite green by their acceptance criteria;
B5 is the only unit that changes the root const, the contract version, the current-mirror
pairing, and the marker, and it does so together. The shipment manifest order of `215-S`
already honored every edge and is unchanged.

Delta persona pass over the changed units:

* **Architecture Strategist.** Closing `model_routing` only in 1.2.0 keeps every published
  mirror immutable; the unknown-key severity follows the same fail-at-1.2.0 / advisory-below
  gate as anchors (040-DL D2), so one rule covers every accepted-but-inert routing key.
  Publishing the mirror unreferenced and adopting it atomically in B5 keeps the
  contract-version-coupled tests green at every boundary. The graph is
  `B3a -> B3b -> B5`, `B4 -> B5`, `{B1, B2, B5} -> B6`; acyclic; `autoharness gate
  dag-readiness` reports `cycle_detected: false` and `ready_set: [209-S]`.
* **Python Reviewer.** `MODEL_ROUTING_KNOWN_KEYS` is a plain frozenset in the pure module (no
  I/O, so the A2 import allowlist still passes) and a B6 sync test ties it to the 1.2.0
  mirror's `model_routing.properties`, so the schema and the check cannot drift.
* **Scope Boundary Auditor.** B4 shrinks to two new files; B5 grows to three files plus the
  marker pair (within budget, resized for volume and integration risk); B6's net size is
  unchanged (the event scan left, a set-difference check arrived). No routing value, config
  key beyond the documented twelve, or policy text changes.
* **Learnings Researcher.** The seven-step mirror-immutability fix and the existence-gated
  verify-check pattern from the two compound learnings still govern; no conflict.

New findings: **B-F11 [P3]** B5 resized `S` / `low` to `M` / `medium`; both axes re-estimated
under `ah-stage-sizing-v1`, `215-S` histogram now `M:8`, `S:5`, acknowledged. **B-F12 [P3]**
between B5 and B8 the config template still renders `schema_version: "1.1.0"` while a global
skill still says to validate against the root schema file; no test gate observes it and B8,
B9, and R1-A A5 close the install, tune, and Orchestrator wording within the same shipment.
The one consumer none of them covers, `workspace-discovery` Phase 0, is out of scope here
(P-021 C1) and captured as `DEFERRED SCOPE EXPANSION` stash `44CB5AE1`, which must route
through `deliberate` (C6) before `215-S` is claimed, acknowledged. **B-F13 [P3]** B6 now
carries four checks, but the raw-YAML scan moved to R1-A, so its size and complexity are
unchanged, acknowledged. No P0, P1, or P2 findings. The delta check supports the existing
verdict: the plan remains **PASS**.
