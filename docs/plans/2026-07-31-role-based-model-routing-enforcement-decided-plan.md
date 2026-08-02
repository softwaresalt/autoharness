---
title: "Role-based Model Routing Enforcement (invocation-time, verifiable) — DECIDED"
type: decided-plan
date: 2026-07-31
decided_at: 2026-08-01
supersedes: docs/archive/plans/2026-07-31-role-based-model-routing-enforcement-plan.md
source_stash: EEAFA73C
deliberation: 010-DL
shipment: 108-S
feature: 104-F
decision: PASS
tags:
  - "model-routing"
  - "invocation-time"
  - "verify-workspace"
  - "104-F"
---

# Decided Plan — 104-F Role-based Model Routing Enforcement

Consolidated from the reviewed plan (inline single-agent declared-degradation
review, `requires_plan_hardening: yes`, **PASS** with 0 blocking findings and 3
residual operator-visible items carried into execution). This decided-plan
keeps only the actionable decisions, surviving implementation units, and
rationale; the verbose original — including the full Stage tooling narrative
and inline review rubric table — is archived at
`docs/archive/plans/2026-07-31-role-based-model-routing-enforcement-plan.md`.
Execution on PR #276 surfaced and resolved 10 additional Copilot review
findings across 3 hosted-review rounds (2 review-fix cycles beyond the
in-session local-review fix) — see
`docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md` for
full findings and generalized lessons.

## Problem

The Orchestrator invokes Stage/Ship sub-agents with no explicit model-override
directive, so sub-sessions silently inherit the default/session model even
though the desired role→model mapping already exists as advisory frontmatter.
`verify_workspace._add_frontmatter_tier_check` validated only
`max_subagent_tier` — nothing failed when routing was omitted, unresolved, or
silently defaulted. Dogfood assignments: Stage → `claude-opus-4.8`; Ship →
`claude-sonnet-5`. Installed harnesses must remain environment/provider
agnostic via configurable role→route mappings with tier fallback — no
provider IDs hardcoded in templates.

## Chosen Design (Option C — Hybrid role→route resolution + fail-closed verification)

Three coordinated layers, decided in `010-DL`:

1. **Config role routes (source of truth, environment-agnostic).** Optional
   first-class `stage`/`ship` routes under `config.model_routing`, reusing the
   existing `anchor_review`/`alt_review` named-route object pattern
   (`{ model_family, model_provider, reasoning_effort }`). Unset role route
   falls back to the agent's config-bound tier (Stage → `tier3`, Ship →
   `tier2`) — P-013 taxonomy preserved, no regression. Concrete provider/model
   IDs live only in `.autoharness/config.yaml`; templates stay
   `{{VARIABLE}}`-parameterized.
2. **Invocation-time enforcement directive.** Orchestrator Steps 1/2 (and the
   skill-delegation contract) resolve role→model and declare/pass the
   resolved `model_family`/`model_provider` as an intent directive — never a
   baked environment-specific `--model` CLI flag. When the runtime cannot
   honor a per-invocation override, emit `ROUTING_DEGRADED` and surface to the
   operator — never silently default.
3. **Fail-closed verification.** `verify_workspace` fails when (a) a pipeline
   agent's `model_family`/`model_provider` is empty, non-string, or an
   unresolved `{{...}}` placeholder, (b) the Orchestrator invocation protocol
   lacks the routing directive (scoped presence check between the resolved
   `config.model_routing.stage`/`.ship` anchor mentions, not a whole-file
   `must_contain`), or (c) a declared role route does not resolve. Backed by
   red-green tests.

Codified as **P-013.5 (Invocation-time model-routing enforcement)** appended
to the P-013 family in the template-only policy registry
(`templates/policies/workflow-policies.md.tmpl`) — no installed
`workflow-policies.md` mirror exists in this repo, so no live-doc counterpart
was touched.

## Surviving Implementation Units (executed, all done)

**Task/plan ID mapping note (intentional inversion, preserved verbatim from
the reviewed plan):** T3 (Installer) = `104.004-T`; T4 (Orchestrator) =
`104.003-T` — IDs are reversed relative to the unit ordinal, but the
dependency edge `104.003-T` depends-on `104.004-T` still sequences Installer
before Orchestrator correctly.

| Unit | Scope | Backlog ID | Depends on |
| --- | --- | --- | --- |
| T1 | Schema role routes + 1.0.0 skew reconciliation | `104.001-T` | — |
| T2 | Config template + dogfood config routes | `104.002-T` | T1 |
| T3 | Installer variable resolution + tier fallback | `104.004-T` | T1, T2 |
| T4 | Orchestrator invocation directive | `104.003-T` | T3 |
| T5 | Skill-delegation contract routing clause | `104.005-T` | T4 |
| T6 | Policy P-013.5 (template-only registry) | `104.006-T` | T4 |
| T7 | Verifier: resolved model fields (red-green) | `104.007-T` | T2, T3 |
| T8 | Verifier: invocation directive + role-route resolution (red-green) | `104.008-T` | T4, T1 |
| T9 | Docs + variable tables + compound learning | `104.009-T` | T3, T4, T6 |

All 9 units completed via TDD on `feat/role-based-model-routing`, merged via
PR #276 (merge commit `f37e251e6bda94dd1233c11907054f71bc8f529e`).

## Plan Hardening Decisions (P-006, carried into execution)

* **Schema-version skew**: both `schemas/harness-config.schema.json` and
  `schemas/harness-config/1.0.0.schema.json` reconciled in T1; existing
  configs re-validated against both.
* **P-013 regression guard**: role routes are optional with tier fallback;
  `max_subagent_tier` check untouched; `model_tier` frontmatter never
  reintroduced.
* **Environment agnosticism (Core Rule 3)**: no baked `--model` CLI flag, no
  provider IDs in `.tmpl` files; directive is intent + resolved frontmatter
  fields; `ROUTING_DEGRADED` never silently defaults.
* **YAML null trap**: empty placeholders must be quoted (`"{{...}}"`) in T2 to
  avoid becoming YAML null and failing `type: string`.
* **Fail-closed proof**: T7/T8 verifier assertions are red-green — each
  demonstrably failed against the pre-change tree before implementation.
* **Scope containment**: reviewer-route concerns (anchor/alt reviewers,
  2026-07-27 plan) kept out of scope — related_to link only.

## Residual Items Resolved During Execution

1. **P-013.5 naming** — resolved: appended as P-013.5 (not merged into
   P-013.4).
2. **Delegation-contract file for T5** — resolved: the skill-delegation
   inheritance contract clause was added to the appropriate instruction file
   during T5 execution (see PR #276 diff for `104.005-T`).
3. **Role-route defaults in versioned schema examples** — resolved during T1;
   no example defaults were added to the versioned schema (routes remain
   optional, tier-fallback documented in the installer variable table
   instead).

## Post-Harvest Hardening (PR #276, beyond the ratified plan)

Local adversarial review found and fixed 1 P1 (`role_route_resolution`
over-broad gating). Three hosted Copilot review rounds then found 10 findings
total across 2 review-fix cycles (manifest checksum drift, non-dict
frontmatter crash, `model_provider`-optional handling, precondition wording,
superseded docs, hardcoded template example, a whole-file `must_contain`
check defeated by a summary-only edit, and non-string `model_family`/
`model_provider` acceptance) — all resolved before merge. Full findings,
fixes, and 2 generalized lessons: see
`docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md`.

**Verdict: PASS** (plan review 0 blocking findings; execution review 0
unresolved P0/P1 at merge).
