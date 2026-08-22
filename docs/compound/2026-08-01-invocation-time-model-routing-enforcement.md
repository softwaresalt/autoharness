---
title: "P-013.5: Invocation-Time Model-Routing Enforcement"
problem_type: harness_architecture
category: agent_design
root_cause: informal_session_model_promise
tags: [orchestrator, model-routing, invocation-directive, verify-workspace, p013.5, stage, ship]
shipment: 108-S
feature: 104-F
pr: TBD
merge_commit: TBD
merged_at: TBD
date: "2026-08-01"
source: docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md
doc_type: learning
---

## Problem

P-013 (`docs/compound/p013-orchestrator-model-routing.md`) made an agent's
**installed** base tier config-resolved via `model_routing`, binding
`model_family`/`model_provider`/`reasoning_effort` into that agent's own
frontmatter at install time. But nothing made routing *verifiable at
invocation time*: the Orchestrator's Steps 1/2 invoked the Stage/Ship
subagents with no explicit model-override directive. In practice this meant
role routing was an informal session promise — a sub-agent invocation could
silently inherit whatever model the *current* session happened to be running
under, rather than the role's intended route (e.g., Stage should reason at a
frontier tier; Ship should execute at a standard tier). There was no
mechanism to detect this drift, and no explicit signal when a runtime could
not honor a per-invocation override.

## Root Cause

Model routing was expressed entirely as installed-agent frontmatter plus
policy prose ("Stage requires Tier 3 reasoning capacity..."). Frontmatter is
read once, at agent-file-parse time, by whatever harness/runtime is hosting
that agent's *own* session — it says nothing about what model a **different**
session (the one about to be spawned for a subagent invocation) will run
under. Enforcement therefore needed to live in the *invoking* agent's
directive text (declare the resolved override at the call site), not solely
in the invoked agent's own frontmatter.

## Fix (Option C hybrid, chosen in deliberation 010-DL)

1. **First-class role routes in config**, reusing the existing `alt_review`
   optional-object schema pattern (not `anchor_review`'s required-fields
   pattern, since role routes must support partial/absent tier fallback):
   `model_routing.stage` / `model_routing.ship` — `model_provider`,
   `model_family`, `reasoning_effort`, `additionalProperties: false`, no
   `required` array. Added identically to both
   `schemas/harness-config.schema.json` and
   `schemas/harness-config/1.0.0.schema.json` (these two files were already
   byte-identical except `$id` at the time of this work — a previously
   claimed "1.0.0 tier skew" no longer existed and needed no reconciliation).
2. **Per-field tier fallback**: when a role route or one of its sub-fields is
   absent/empty, resolution falls back *per field* to `model_routing.tier3`
   (Stage) / `model_routing.tier2` (Ship) — chosen so P-013's existing tier
   taxonomy keeps working unchanged for any workspace that never declares an
   explicit stage/ship route. Tier values may be a legacy plain string or an
   object; the fallback resolver normalizes both forms and treats a
   tier object's `model` field as a `model_family` fallback when
   `model_family` itself is absent.
3. **Installer variables**: `STAGE_FAMILY`/`STAGE_PROVIDER`/`STAGE_REASONING_EFFORT`
   and `SHIP_*` equivalents added to the `install-harness/SKILL.md` variable
   table, each documented with its per-sub-field fallback.
4. **Orchestrator invocation directive**: Steps 1 and 2 of both the full
   template (`templates/agents/_orchestrator.agent.md.tmpl`) and the
   condensed installed dogfood copy (`.github/agents/_orchestrator.agent.md`)
   now include an explicit "Resolve routed model (P-013.5)" step before each
   subagent invocation — resolve the config route, declare the resolved
   `model_family`/`model_provider` as the invocation override, and emit
   `ROUTING_DEGRADED` explicitly (never a silent fallback to the current
   session's model) when the hosting runtime cannot honor a per-invocation
   override. This is a **portable invocation contract**, not a claim that
   every environment exposes a literal `--model` CLI flag — some runtimes
   support per-invocation overrides natively, others require declaring the
   override in the routed prompt/config and degrading explicitly when that is
   not honored.
5. **Skill-delegation inheritance**: a new "Skill-Delegation Model
   Inheritance (P-013.5)" section in `role-enforcement.instructions.md`
   (template + installed) makes explicit that skills are leaf executors
   which inherit the invoking agent's already-routed session model. Skills
   must not re-resolve routing per invocation, and must carry forward any
   `ROUTING_DEGRADED` state from their invoking agent rather than silently
   resolving their own route.
6. **Policy**: `### P-013.5 — Invocation-Time Model-Routing Enforcement`
   appended to the P-013 family in
   `templates/policies/workflow-policies.md.tmpl` (Resolve / Declare /
   Degrade-explicitly / Skill-inheritance / Fail-closed-verification /
   Violation-Action structure). The policy registry in this repository is
   template-only (no installed `.github/policies/workflow-policies.md`
   mirror exists here), so no installed-file counterpart was required.
7. **Fail-closed verification** (`src/autoharness/verify_workspace.py`):
   - `orchestrator_model_routing_fields` / `stage_model_routing_fields` /
     `ship_model_routing_fields` — each installed pipeline agent must declare
     a non-empty, fully-resolved `model_family`/`model_provider` (no
     unresolved `{{...}}`). Gated on `file_path.exists()` per agent (unlike
     the pre-existing, unconditional `orchestrator_tier_fields` check) so
     partial workspaces/fixtures that omit one of the three pipeline agent
     files never register a false failure — the CLI's `_report_has_failures`
     treats *any* `ok: False` targeted check as a whole-command failure, so
     over-eager unconditional checks are a real regression risk against
     existing fixtures.
   - `orchestrator_invocation_routing_directive` — the installed Orchestrator
     must actually contain the P-013.5 directive text (not just the template
     source), confirming the directive was installed, not merely documented.
   - `role_route_resolution` — verifies the stage/ship role routes each
     resolve to a non-empty `model_family` via explicit route or tier
     fallback; evaluated only when the workspace has **explicitly opted in**
     to P-013.5 role routing — either `model_routing.stage`/`.ship` is
     declared (even an empty object counts, since declaring the key signals
     intent), or both `model_routing.tier2` and `.tier3` are present (the
     fallback targets the check depends on). A `model_routing` block that
     declares neither (e.g. `tier1`-only, or an empty `{}`) has not opted in
     and is out of scope for this check — see "Review-Fix Hardening" below;
     an earlier version of this check gated on any non-empty `model_routing`
     block at all, which regressed schema-valid partial/legacy configs.

## Verification Pattern

Each new check has a paired red/green test in `tests/test_verify_workspace.py`:
a passing fixture, an unresolved-placeholder fixture, an empty-field fixture,
a directive-present/missing fixture pair, direct unit tests against the
role-route-resolution helper (fallback success and unresolvable failure),
and one end-to-end `verify_workspace()` failure case. All were run RED
against the pre-change verifier and GREEN after implementation, then
verified against the actual dogfood workspace (`.autoharness/config.yaml`
declares explicit `stage`/`ship` routes; all five new targeted checks pass).

## Dogfood Assignment

Stage → `claude-opus-4.8` (anthropic, high reasoning effort) — frontier-tier
role, mirrors the `tier3` fallback. Ship → `claude-sonnet-5` (anthropic, high
reasoning effort) — standard-tier role, mirrors the `tier2` fallback. Recorded
in `.autoharness/config.yaml` under `model_routing.stage` / `model_routing.ship`.

## Guardrail: No Hardcoded Provider IDs in Templates

Per Core Rule 3 (Environment Agnosticism), no `.tmpl` file hardcodes a
provider or model-family string for the stage/ship routes — they remain
`{{STAGE_FAMILY}}`/`{{STAGE_PROVIDER}}`/`{{STAGE_REASONING_EFFORT}}` and
`{{SHIP_*}}` placeholders resolved strictly from `.autoharness/config.yaml`
at install time. Only the installed dogfood copies (`.autoharness/config.yaml`,
`.github/agents/_orchestrator.agent.md`) carry resolved, environment-specific
values.

## Review-Fix Hardening (PR #276)

Two rounds of adversarial review each found a real defect before merge —
recorded here so future maintainers don't reintroduce them:

**Local review (cycle 1/3, pre-PR)**: `role_route_resolution` initially fired
whenever `model_routing` was any non-empty dict, including configs that only
set `tier1` or were `{}`. Fixed by requiring explicit opt-in (see corrected
gating description above).

**Copilot review (PR #276, hosted)**: six further findings, all fixed:
1. `.github/skills/install-harness/SKILL.md` is checksum-tracked but its
   manifest entry wasn't refreshed after the T3/104.004-T edit — would have
   caused `verify_workspace` to classify it as `user-modified` drift.
   Refreshed.
2. `_add_frontmatter_model_routing_check` crashed with `AttributeError` when
   `yaml.safe_load()` returned a non-mapping (list/scalar/bool) for
   syntactically-valid-but-structurally-wrong frontmatter. Added an
   `isinstance(frontmatter, dict)` guard that fails closed with a clean
   targeted-check result instead.
3. Requiring `model_provider` unconditionally non-empty broke schema-valid
   legacy/default installs: the installer table's `TIER_2_PROVIDER`/
   `TIER_3_PROVIDER` (and their stage/ship fallbacks) default to **empty**.
   `model_provider` is now optional — only an unresolved `{{...}}` placeholder
   in it is an error; `model_family` remains required non-empty (every tier/
   role route has a non-empty family default).
4. Both `role-enforcement.instructions.md` (template + installed) stated
   skills require the invoking agent's session to be "resolved and
   non-degraded" before invocation — directly contradicting the very next
   clause describing how a `ROUTING_DEGRADED` session must still propagate to
   its skills. Reworded to "confirm and propagate" the current routing state
   rather than requiring non-degraded as a precondition.
5. `templates/agents/_orchestrator.agent.md.tmpl`'s configuration example
   hardcoded concrete Anthropic model IDs and the `anthropic` provider string
   — contradicting this PR's own "no provider-specific string is hardcoded in
   any `.tmpl`" claim and Core Rule 3. Rewritten to use the actual
   `{{STAGE_FAMILY}}`/`{{SHIP_FAMILY}}`/etc. template variables.
6. This doc and `docs/product-specs/orchestrator-model-routing-spec.md` both
   described the pre-fix (any-`model_routing`) gating behavior rather than
   the corrected explicit-opt-in condition — both updated to match the
   shipped implementation.

**Copilot re-review (PR #276, second hosted round, after the six-finding push
above)**: two further findings, both fixed:
7. `orchestrator_invocation_routing_directive` was a whole-file
   `must_contain` check, satisfiable by the "Model Routing" summary paragraph
   alone even after both Step 1/Step 2 per-invocation directives were
   deleted (the summary legitimately restates the same four tokens for human
   readers). Replaced with a dedicated, scoped check that requires
   `ROUTING_DEGRADED` to appear in the narrow window between the file's
   first `config.model_routing.stage` mention and its first
   `config.model_routing.ship` mention — i.e. inside Stage's own invocation
   paragraph, before Ship's route is even introduced. A summary sentence
   that mentions both routes back-to-back in the same clause has no room
   for a distinct `ROUTING_DEGRADED` between them, so this scoping is not
   satisfiable by summary text alone. **Lesson**: a `must_contain`-style
   whole-file token check only proves presence, never placement — any check
   whose safety property depends on tokens appearing at a *specific site*
   (not just anywhere) needs a scoped/windowed check, not a flat substring
   match.
8. `_add_frontmatter_model_routing_check` accepted any non-string value
   (`false`, `42`, `[]`, `{}`) as a valid `model_family`, since the original
   check only tested for `None` or an empty string. Now requires an actual
   string type for `model_family`, and requires `model_provider` to be a
   string when present (still optional). The parallel config-side path
   (`_resolve_role_route_field`/`_add_role_route_resolution_check`) was
   independently confirmed safe: its final gate already requires
   `isinstance(resolved_family, str) and .strip()`, and
   `model_routing.stage`/`.ship`'s `model_family`/`model_provider` are
   already typed `string` in `harness-config.schema.json`, so a non-string
   config-side value is caught by schema validation before this check runs.
   **Lesson**: a "falsy or empty-string" check is not the same as a "wrong
   type" check — `False`/`0`/`[]`/`{}` are all falsy-adjacent but pass an
   `is None or == ""` test unnoticed; prefer `not isinstance(x, str) or not
   x.strip()` whenever the field's only valid representation is a string.

This second round confirms a pattern worth generalizing: **every fail-closed
FOUNDATION_ASSERTIONS-style check added for this feature was reviewed twice**
(local adversarial review, then two rounds of hosted Copilot review) before
converging on a version safe against deletion-while-leaving-decoys and
type-confusion attacks. Future P-013.x-style verifier checks should budget for
at least one hosted-review pass focused specifically on "can this check be
satisfied without the invariant actually holding?"

## Related

- `docs/compound/p013-orchestrator-model-routing.md` — original P-013 design
  (persona isolation + tier taxonomy + frontmatter schema).
- `docs/product-specs/orchestrator-model-routing-spec.md` — amended with a
  2026-08-01 P-013.5 note and new Phase 3 assertion-coverage entries.
- `docs/plans/2026-07-31-role-based-model-routing-enforcement-decided-plan.md`
  (post-merge decided-plan, supersedes the archived original at
  `docs/archive/plans/2026-07-31-role-based-model-routing-enforcement-plan.md`)
  — defines the exact T1–T9 task breakdown and the intentional T3/T4
  backlog-ID inversion (T3 Installer = `104.004-T`, T4 Orchestrator =
  `104.003-T`).
