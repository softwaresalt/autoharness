---
title: Role-based model routing enforcement (invocation-time, verifiable)
date: 2026-07-31
source_stash: EEAFA73C
deliberation: 010-DL
stage_invoked_on: claude-opus-4.8
review_mode: single-agent-declared-degradation
requires_plan_hardening: "yes"
---

# Role-based Model Routing Enforcement Plan

## Stage Mode and Tooling

* `ALL_TOOLS_OK` for backlogit: `TOOL_OK: backlogit (MCP)` and `TOOL_OK: backlogit (CLI 1.7.0)`.
* `INDEX_SYNC_OK` (607 items) before backlog reads.
* `INTERCOM_DEGRADED` (operator-declared), `ENGRAM_DEGRADED` (no MCP surface this
  session), `GRAPHTOR_UNAVAILABLE` (no MCP surface). Code/doc context came from
  direct `Select-String`, `view`, and schema/AST reads — never silent ad-hoc
  fallback: degradation declared per P-012.
* `TOOL_DEGRADED: reviewer-subagent-dispatch — inline single-agent persona pass`;
  plan review performed inline (no reviewer sub-agent dispatch surface reachable),
  matching the precedent set by `docs/plans/2026-07-27-multi-model-adversarial-review-routing-plan.md`.

## Problem Frame

Autoharness's core purpose includes deliberate model routing, but the Orchestrator
invokes the Stage and Ship subagents (Orchestrator template Steps 1 and 2) with
**no explicit model-override directive**. Sub-sessions therefore inherit the
default/session model. Two structural facts make this a silent failure rather than
a loud one:

1. The installed agent definitions already declare the correct model
   (`_stage.agent.md` → `model_family: claude-opus-4.8`; `_ship.agent.md` →
   `model_family: claude-sonnet-5`), and `config.model_routing` already binds
   `tier3: claude-opus-4.8` / `tier2: claude-sonnet-5`. The **desired mapping
   already exists** — but only as advisory frontmatter the Orchestrator Model
   Routing section itself concedes "may be ignored... the operator may need to
   manually select the model."
2. `verify_workspace._add_frontmatter_tier_check` validates **only**
   `max_subagent_tier`. Nothing fails when routing is omitted, unresolved, or
   silently defaulted.

The result: routing is an informal per-session promise. The operator requires it
encoded durably, executable, and verifiable, while preserving the shipped P-013
tier taxonomy (do not regress) and the retired `model_tier` frontmatter (do not
reintroduce — 053.004-T).

**Dogfood assignments (operator):** Stage → `claude-opus-4.8`; Ship →
`claude-sonnet-5`. Installed harnesses must be able to remap via configurable
role→model routes or capability-aware equivalents; provider IDs must not be
hardcoded across templates.

## Chosen Design (Option C — Hybrid role→route resolution + fail-closed verification)

Decided in `010-DL`. Three coordinated layers:

1. **Config role routes (source of truth, environment-agnostic).** Add optional
   first-class `stage` and `ship` routes under `config.model_routing`, reusing the
   existing `anchor_review` / `alt_review` named-route object pattern
   (`{ model_family, model_provider, reasoning_effort }`). When a role route is
   **unset**, resolution falls back to the agent's config-bound tier (Stage →
   `tier3`, Ship → `tier2`) so nothing regresses and P-013 is preserved. Concrete
   provider/model IDs live only in `.autoharness/config.yaml`; templates stay
   `{{VARIABLE}}`-parameterized.
2. **Invocation-time enforcement directive.** Amend Orchestrator Steps 1/2 (and the
   skill-delegation contract) with an explicit directive: resolve role→model,
   declare/pass the resolved `model_family`/`model_provider` as the invocation
   override, and — per Core Rule 3 — express it as an intent directive plus the
   resolved fields the runtime honors, **not** a baked environment-specific
   `--model` CLI flag. When the runtime cannot honor a per-invocation override,
   emit `ROUTING_DEGRADED` and surface to the operator — never silently default.
3. **Fail-closed verification.** Extend `verify_workspace` so the harness fails when
   (a) a pipeline agent's `model_family`/`model_provider` is empty or an unresolved
   `{{...}}` placeholder, (b) the Orchestrator invocation protocol lacks the routing
   directive, or (c) a declared role route does not resolve. Backed by red-green
   tests that fail against the pre-change state.

Policy is codified as **P-013.5 (Invocation-time model-routing enforcement)**
appended to the P-013 family (naming is an operator-visible open question — see
below), and the versioned `schemas/harness-config/1.0.0.schema.json` skew (tiers
still plain strings) is reconciled in the same pass.

## Planned Artifact Classes (exact)

| Class | Concrete artifact(s) | Nature |
|---|---|---|
| JSON schema | `schemas/harness-config.schema.json`, `schemas/harness-config/1.0.0.schema.json` | add `stage`/`ship` role routes; reconcile 1.0.0 tier skew |
| Config template | `templates/harness-config.yaml.tmpl` | add `stage:`/`ship:` route blocks (quoted `{{...}}`) |
| Live dogfood config | `.autoharness/config.yaml` | add `stage`/`ship` routes (opus-4.8 / sonnet-5) |
| Installer skill | `.github/skills/install-harness/SKILL.md` | add `{{STAGE_*}}`/`{{SHIP_*}}` var rows + tier-fallback semantics |
| Orchestrator agent | `templates/agents/_orchestrator.agent.md.tmpl` + regen `.github/agents/_orchestrator.agent.md` | invocation directive in Steps 1/2 + Model Routing section |
| Delegation instruction | skill-delegation / subagent contract instruction (exact file to be located by Ship) | skills inherit routed agent session model; confirm routing before skill invocation |
| Policy doc | `templates/policies/workflow-policies.md.tmpl` (+ installed `workflow-policies.md`) | P-013.5 + amendment log |
| Verifier (CLI) | `src/autoharness/verify_workspace.py` | fail-closed assertions (resolved model fields; directive presence; role-route resolution) |
| Tests | `tests/test_verify_workspace.py` | red-green cases that fail when routing omitted/defaulted |
| Docs | `docs/getting-started.md`, `docs/product-specs/orchestrator-model-routing-spec.md`, new `docs/compound/*` learning | variable tables + spec amendment + learning |

No provider-specific string is hardcoded in any `.tmpl`; all resolve from config.

## Task Breakdown (each ≤ 2h, width-isolated)

Ordering encodes dependencies: schema → config → installer → consumers → verify → docs.

1. **T1 — Schema role routes + 1.0.0 skew reconciliation** (schema family). Add
   `stage`/`ship` object routes to both schema files; make `1.0.0` tiers
   `oneOf:[string,object]` to match the unversioned schema; keep sub-object
   `additionalProperties:false`. **AC:** a config with `stage`/`ship` object routes
   validates; misspelled sub-fields are rejected; every pre-existing
   `.autoharness/config.yaml` still validates against both schemas.
2. **T2 — Config template + dogfood config routes** (config family). Add
   `stage:`/`ship:` blocks to `harness-config.yaml.tmpl` with quoted `{{STAGE_*}}`/
   `{{SHIP_*}}` placeholders; add resolved routes to `.autoharness/config.yaml`
   (`stage` → opus-4.8/anthropic/high; `ship` → sonnet-5/anthropic/high). **AC:**
   template emits schema-valid YAML with no YAML-null from empty placeholders;
   resolved live config validates (T1). Depends on T1.
3. **T3 — Installer variable resolution + tier fallback** (installer skill family).
   Add `{{STAGE_FAMILY}}`/`{{STAGE_PROVIDER}}`/`{{STAGE_REASONING_EFFORT}}` and
   `SHIP_` rows to the install-harness variable table; each falls back to
   `tier3`/`tier2` respectively when the role route is unset. **AC:** every new
   variable has a source+default+fallback row; a post-install agent frontmatter
   carries no unresolved `{{...}}`. Depends on T1, T2.
4. **T4 — Orchestrator invocation directive** (orchestrator agent family). Amend
   Steps 1 and 2 to resolve role→model and declare/pass the override; update the
   Model Routing section to describe enforcement + `ROUTING_DEGRADED` fallback;
   regenerate `.github/agents/_orchestrator.agent.md`. **AC:** Steps 1/2 each
   contain the explicit routing directive referencing the resolved `model_family`
   and the degraded-mode declaration; no `{{...}}` left in the regenerated def.
   Depends on T3.
5. **T5 — Skill-delegation contract routing clause** (instruction family). State in
   the delegation/subagent contract that skills inherit the invoking agent's routed
   session model and that an agent must confirm its own routing before invoking a
   skill (covers "apply when invoking agents AND their skill workflows"). **AC:**
   contract text present; cross-references P-013.5; no per-skill model field
   introduced (skills remain leaf executors). Depends on T4 (shared directive
   wording).
6. **T6 — Policy P-013.5** (policy family). Append P-013.5 (invocation-time
   model-routing enforcement: resolve-declare-or-degrade; fail-closed) to
   `workflow-policies.md.tmpl` + amendment log; update installed copy. **AC:**
   P-013.5 present in template and installed file with fail-closed + ROUTING_DEGRADED
   semantics; canonical `| Field | Value |` policy table format. Depends on T4.
7. **T7 — Verifier assertion: resolved model fields (red-green)** (verifier/tests).
   Extend the frontmatter check so pipeline agents (`_stage`, `_ship`,
   `_orchestrator`) must declare non-empty `model_family`/`model_provider` with no
   `{{...}}` placeholder. Test-first: add a failing fixture, then implement. **AC:**
   test fails against pre-change verifier; passes after; unresolved/empty model
   fields fail verification. Depends on T2, T3.
8. **T8 — Verifier assertion: invocation directive + role-route resolution
   (red-green)** (verifier/tests). Add a FOUNDATION_ASSERTION that the installed
   Orchestrator contains the routing directive, and a check that declared
   `config.model_routing.stage`/`ship` routes resolve. Test-first. **AC:** removing
   the directive or breaking a role route fails verification; present/resolved
   passes. Depends on T4, T1.
9. **T9 — Docs + variable tables + compound learning** (docs family). Update
   `getting-started.md` variable table; amend `orchestrator-model-routing-spec.md`
   with P-013.5; add a `docs/compound/*` learning capturing the invocation-time
   enforcement pattern. **AC:** variable tables list `STAGE_*`/`SHIP_*`; spec
   amended; zero unresolved `{{...}}` in docs. Depends on T3, T4, T6.

## Plan Hardening (P-006)

`requires_plan_hardening: yes` — blast radius is elevated (two JSON schemas + CLI
distribution surface + multiple template families). Hardening applied:

* **Schema-version skew (highest mechanical risk).** The versioned
  `1.0.0.schema.json` still models tiers as plain strings; adding role routes to
  only one schema would create validation divergence. **Mitigation:** T1 reconciles
  both schemas in one task; T1 AC re-validates existing configs against **both**.
* **P-013 regression risk.** Do not reintroduce `model_tier`; do not couple role
  strictly to tier. **Mitigation:** role routes are optional with tier fallback;
  `max_subagent_tier` check is untouched; T8 asserts fallback resolution.
* **Environment agnosticism (Core Rule 3).** No baked `--model` CLI flag; no
  provider IDs in `.tmpl`. **Mitigation:** directive is intent + resolved
  frontmatter fields; `ROUTING_DEGRADED` declared, never silent default; T7 fails on
  any `{{...}}` left unresolved in a `.tmpl`-derived agent def.
* **YAML null trap.** Empty placeholders unquoted become YAML null and fail
  `type:string`. **Mitigation:** T2 mandates quoted `"{{...}}"` (compound-documented
  in p013 learning).
* **Fail-closed proof.** The whole point is that verification fails when routing is
  omitted. **Mitigation:** T7/T8 are red-green — each must demonstrably fail against
  the pre-change tree before implementation.
* **Scope containment.** Review-routing (anchor/alt reviewers) is a **distinct**
  concern (2026-07-27 plan). **Mitigation:** related_to link, not merged scope; no
  reviewer-route files in this plan's artifact classes.
* **Blast-radius measurement, not estimate.** Ship must re-scan `model_routing`
  references before edits (removal deliberation warns the estimate over-counted).

## Plan Review (inline, single-agent declared degradation)

`review_mode: single-agent-declared-degradation` — no reviewer sub-agent dispatch
surface reachable; reviewed inline against the plan-review rubric.

| Lens | Finding | Verdict |
|---|---|---|
| Problem/solution fit | Design targets the exact defect (invocation-time enforcement + verification); does not merely restate desired mapping that already exists in config. | PASS |
| P-013 / prior-art integrity | Preserves tier taxonomy; no `model_tier` return; reuses anchor_review named-route precedent; reconciles known 1.0.0 skew. | PASS |
| Environment agnosticism | No hardcoded provider IDs in templates; no baked CLI flag; explicit `ROUTING_DEGRADED` fallback. | PASS |
| Verifiability / fail-closed | T7/T8 red-green assertions fail when routing omitted, unresolved, or defaulted — satisfies "not an informal promise". | PASS |
| Granularity / 2h rule | 9 tasks, each single-family, width-isolated (schema ≠ config ≠ installer ≠ agent ≠ instruction ≠ policy ≠ verifier ≠ docs). | PASS |
| Acceptance objectivity | Each task has objective, checkable AC; schema tasks re-validate; verifier tasks are red-green. | PASS |
| Dependency soundness | Linear schema→config→installer→consumers→verify→docs order; no cycles. | PASS |
| Role/scope boundary | Stage-only staging; no implementation performed; review-routing kept out of scope. | PASS |

**Residual / operator-visible open items** (do not block PASS; must be resolved
during execution): (1) P-013.5 naming vs amending P-013.4; (2) exact
delegation-contract file for T5; (3) whether role-route defaults belong in the
versioned schema examples.

**Verdict: PASS** (0 blocking findings; 3 residual operator-visible items carried
into the backlog).
