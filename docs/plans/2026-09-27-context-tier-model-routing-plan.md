---
title: "context_tier on model_routing routes and agent frontmatter; new generic Ship default; durable dogfood Ship pin"
description: "Add an optional, provider-agnostic context_tier (\"\", default, long_context) to every tier, role, and escalation route in harness-config and to the tier/role-routed agent frontmatter. Change the generic fresh-install Ship route to openai / gpt-6-luna / xhigh / long_context. Bind the pipeline agent templates to their P-013.5 role variables so this dogfood repository's binding claude-opus-5.5 / anthropic Ship route survives re-install and tune without being flagged as drift."
doc_type: plan
status: reviewed
created: 2026-09-27
source_stash: 6EC29DD6
source_deliberation: docs/decisions/2026-09-27-close-evidence-frontmatter-context-tier-staging-deliberation.md
depends_on_plan: docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md
binding_operator_ruling: "2026-09-27T13:18:02-07:00 - this repository's Ship route stays claude-opus-5.5 / anthropic"
post_review_operator_amendment: "2026-09-27T22:50-07:00 - dogfood Ship context_tier is long_context (template keeps {{SHIP_CONTEXT_TIER}}); Ship template max_subagent_tier changes from 2 to 3. Operator rulings, not new design; the PASS review is not reopened. See section Operator Rulings (2026-09-27T22:50-07:00)."
requires_plan_hardening: "yes"
---

# context_tier routing, new generic Ship default, durable dogfood Ship pin

## Problem Frame

Operators need to choose a context capacity per route. The generic install's Ship
route should default to `openai` / `gpt-6-luna` / `xhigh` / `long_context`. Three
things stand in the way today.

* Every route object in `schemas/harness-config.schema.json` has
  `additionalProperties: false`, so a `context_tier` key is rejected (F-C1).
* The installer derives routes in `src/autoharness/verify_workspace.py`
  (`_derive_tier_route_variables`, `_derive_orchestrator_route_variables`,
  `_derive_role_route_variables`, and the escalation derivations), and none of them
  knows the field.
* `templates/agents/_ship.agent.md.tmpl` and `_stage.agent.md.tmpl` render their
  frontmatter from `{{TIER_2_*}}` / `{{TIER_3_*}}`, not from the P-013.5 role
  variables. As a result, this repository's installed `_ship.agent.md`
  (`claude-opus-5.5`) is a hand-maintained divergence, and a re-install would
  silently revert it to tier2 `claude-sonnet-5` (F-B3, F-C5). That would violate the
  binding operator ruling.

## Requirements Trace

| # | Requirement (stash `6EC29DD6` / D-C*) | Unit(s) |
|---|---|---|
| R1 | Optional `context_tier` on tier1-3, orchestrator, stage, ship, escalation, and nested stage/ship escalation; allowed set `""`, `default`, `long_context` (D-C1) | C1 |
| R2 | Per-field fallback role → tier → `default`; nested escalation → tier3 → `default` (D-C2) | C2 |
| R3 | The same-route guard and both-present ambiguity ignore `context_tier` (D-C3) | C1, C2 |
| R4 | Resolve the field into agent frontmatter | C3a, C4a, C5a, C5b, C5c |
| R5 | Generic fresh-install Ship default openai / gpt-6-luna / xhigh / long_context, with no hardcoding in `.tmpl` (D-C4, Core Rule 3) | C3b |
| R6 | P-013.5 invocation override carries `context_tier`; `ROUTING_DEGRADED` when the runtime cannot honor it; the P-013.6 escalation handoff carries the resolved escalation `context_tier` | C6a, C6b |
| R7 | BINDING: this repository's Ship stays claude-opus-5.5 / anthropic; re-install, tune, and parity must not flag it; the override is durable (D-C6) | C4a, C4b, C7, C8 |
| R8 | No `schema_version` bump; configs without the field stay valid (D-C5) | C1 |
| R9 | Tune proposes the new Ship default only for workspaces with no explicit Ship `model_family` (D-C4) | C8 |

## Implementation Units

### C1 — Schema: optional `context_tier` on route objects

* **Files:** `schemas/harness-config.schema.json`, and
  `tests/test_escalation_hierarchy_schema.py` (extended; or a sibling
  `tests/test_context_tier_schema.py` if the existing module's fixtures do not fit).
* **Changes:**
  * Add `definitions/contextTier = {type: string, enum: ["", "default", "long_context"]}`.
  * Reference it from the object form of tier1, tier2, and tier3, and from
    orchestrator, stage, ship, escalation, and `stage.escalation` / `ship.escalation`.
  * `nonEmptyRouteFields` is unchanged, so `context_tier` does not participate in the
    both-present ambiguity.
  * `schema_version` stays `1.1.0`.
  * anchor / alt review routes are unchanged (D-C7).
* **Tests:**
  * the existing dogfood and template configs (without the field) validate;
  * `context_tier: long_context` on ship validates;
  * `context_tier: huge` is rejected;
  * a flat escalation with only `context_tier` plus a nested `stage.escalation.model_family`
    is **not** ambiguous.
* **Posture:** test-first. **Size:** S. **Complexity:** low.

### C2 — Route derivation and verify checks resolve `context_tier`

* **Files:** `src/autoharness/verify_workspace.py`, `src/autoharness/frontmatter_contract.py`
  (the `CONTEXT_TIER_VALUES` constant only), and
  `tests/test_context_tier_resolution.py` (new).
* **Changes:**
  * `_resolve_role_route_field` accepts `context_tier`. A helper
    `_resolve_context_tier(route, fallback)` implements route → fallback tier →
    `"default"`, and a legacy string tier gives `"default"`.
  * The derivations emit two families, and they keep the existing resolved-vs-raw
    split (constraint C3 of `_derive_raw_escalation_variables`; H-C1):
    * **Resolved** (never empty; fallback ends at `"default"`):
      `TIER_1_CONTEXT_TIER`, `TIER_2_CONTEXT_TIER`, `TIER_3_CONTEXT_TIER`,
      `ORCHESTRATOR_CONTEXT_TIER` (route → tier2 → `default`, including the scalar
      orchestrator form, matching its provider/effort fallback), `STAGE_CONTEXT_TIER`,
      `SHIP_CONTEXT_TIER`, and the collapsed `ESCALATION_CONTEXT_TIER`;
    * **Raw pass-through** (empty string when unset; never read a fallback chain):
      `LEGACY_ESCALATION_CONTEXT_TIER`, `STAGE_ESCALATION_CONTEXT_TIER`, and
      `SHIP_ESCALATION_CONTEXT_TIER`. They exist only for the config write-back.
  * Escalation `context_tier` resolution (H-C2). The source-selection predicate is
    unchanged: `_escalation_route_has_any_field` keeps its three-field tuple, so a
    nested block that declares only `context_tier` never selects the nested source
    and never triggers the H2 both-present ambiguity (INV-C4).
    * A new `_effective_escalation_context_tier_for_role(model_routing, role)`
      resolves the value in this order: `<role>.escalation.context_tier`; then the
      flat `escalation.context_tier`, only when the flat route is the selected
      source; then `tier3.context_tier`; then `"default"`. When the nested route is
      the selected source, the flat route is never read (D-C2).
    * The base `ESCALATION_CONTEXT_TIER` resolves flat → tier3 → `"default"`.
      `_compose_artifact_variables` overlays the role-scoped value for
      `_stage.agent.md` / `_ship.agent.md`, just as it does the other three fields.
    * `_effective_escalation_route_for_role` keeps its 3-tuple return. Its two
      callers are unchanged.
  * The per_role escalation report gains `resolved_context_tier`, computed by the same
    `_effective_escalation_context_tier_for_role` helper that the derivation uses, so
    the check and the render cannot diverge. The `is_same_route` tuple is
    **unchanged** (an explicit comment and test pin D-C3).
  * One enum constant (H-C5): `CONTEXT_TIER_VALUES = ("default", "long_context")`
    lives in `src/autoharness/frontmatter_contract.py`, the module shipment B creates.
    It holds the resolved frontmatter values. The config schema enum is
    `["", *CONTEXT_TIER_VALUES]`, where `""` means unset/inherit and is legal only in
    config, never in rendered frontmatter.
  * `_add_frontmatter_model_routing_check` validates `context_tier`, when present, as
    a string in `CONTEXT_TIER_VALUES` with no unresolved placeholder. It stays
    optional, so older installs pass.
* **Tests:**
  * the fallback chain for ship (explicit, then tier2, then `default`);
  * the scalar orchestrator form gives the tier2 `context_tier`;
  * nested escalation never falls back to the flat route;
  * a nested `ship.escalation` that declares only `context_tier: long_context`
    (alongside a flat escalation family) keeps `source: legacy_flat`, is not
    ambiguous, gives the flat family, and gives `resolved_context_tier: long_context`;
  * the raw `*_ESCALATION_CONTEXT_TIER` variables are `""` when unset, and never take
    a resolved value;
  * the same family/provider/effort with a different `context_tier` is still
    `escalation_degraded: true`;
  * an invalid frontmatter `context_tier`, including `""`, fails;
  * schema parity: the schema `contextTier` enum equals `["", *CONTEXT_TIER_VALUES]`.
* **Posture:** test-first. **Size:** M. **Complexity:** medium.

### C3a — Installer variable table and config template placeholders

* **Files:** `.github/skills/install-harness/SKILL.md` (the variable table only, plus
  its `.autoharness/harness-manifest.yaml` checksum refreshed from the raw blob;
  review AS-F4 / AN-F4), `templates/harness-config.yaml.tmpl`, and
  `tests/test_template_variable_derivation_contract.py` (row references and new
  variables).
* **Changes:**
  * Add a `{{*_CONTEXT_TIER}}` row for every variable C2 emits. The source column is
    `config.model_routing.<route>.context_tier`, and the fallback follows D-C2 and
    H-C2.
    * The resolved rows default to `default`. The collapsed `{{ESCALATION_CONTEXT_TIER}}`
      is a resolved row, so it defaults to `default` too.
    * The three raw rows (`LEGACY_` / `STAGE_` / `SHIP_ESCALATION_CONTEXT_TIER`)
      default to `""` and are classified DERIVE-TO-EMPTY-STRING in the contract test.
  * The resolution fallback for existing configs is **unchanged** (Ship → tier2).
    The `{{SHIP_FAMILY}}` row keeps its `claude-sonnet-5` default, so the Python
    derivation and the contract test stay in parity and no existing workspace
    changes behavior.
  * `harness-config.yaml.tmpl` gains a `context_tier` line on each route block, with
    comments. Tier, orchestrator, stage, and ship blocks use the resolved variables,
    which matches how `{{SHIP_FAMILY}}` is written back today. The flat and nested
    escalation blocks use the raw variables.
  * **Write-back materialization (review AS-F8):** as with `model_family` today, the
    write-back stores the *resolved* tier and role `context_tier`. A route that
    inherited its tier at install time becomes explicit in the written config, so
    inheritance is one-time, at install.
    * This is the existing pattern for every tier and role route field, and this
      plan keeps it rather than giving one field a different lifecycle.
    * The tuning guide (C8) states it.
    * The escalation blocks keep raw pass-through, so escalation inheritance
      survives the write-back.
  * The row-number references in the contract test are re-derived.
* **Tests:**
  * the contract test covers every new variable (a missing row fails), and each raw
    row is classified DERIVE-TO-EMPTY-STRING;
  * a write-back round trip: rendering `harness-config.yaml.tmpl` from a config with
    an empty `ship.context_tier` and `tier2.context_tier: long_context` writes
    `ship.context_tier: long_context`, and leaves each escalation `context_tier` as
    `""`;
  * every `context_tier:` line in `templates/**/*.tmpl` carries a
    `{{*_CONTEXT_TIER}}` placeholder, never a literal value (INV-C3);
  * the `install-harness` manifest entry is `unchanged` after the edit.
* **Posture:** test-first. **Size:** S. **Complexity:** low.

### C3b — Fresh-install Ship seed

* **Files:** `.github/skills/install-harness/SKILL.md` (the install-flow text only,
  plus its manifest checksum refreshed again), and
  `tests/test_fresh_install_ship_seed_contract.py` (new; structural).
* **Changes:** add a **fresh-install seed** rule (H-C3, review AS-F2 / AS-F3 /
  AN-F2) to the install-harness flow. It is not added to the variable table's
  default column.
  * **First-install snapshot:** at install start, before Step 1.2 and therefore
    before Step 3.3 creates the manifest, the installer records
    `first_install = not exists(.autoharness/harness-manifest.yaml)`. Every later
    step reads this snapshot and never re-probes the manifest.
  * **Trigger:** `first_install` is true, **and** the operator-supplied input has
    no `model_routing.ship` key at all, **and** `config.overrides` sets none of
    `SHIP_FAMILY`, `SHIP_PROVIDER`, `SHIP_REASONING_EFFORT`, or `SHIP_CONTEXT_TIER`
    (review AS-F9). That covers both a missing `.autoharness/config.yaml` and a
    config without a `ship` key.
    * A `SHIP_*` template-variable override is an operator Ship choice. It
      suppresses the seed entirely and is applied by Step 1.0b item 7 as today.
    * An explicitly present `ship` block is an operator choice and is honored as
      written, even when all its fields are empty. It resolves through the normal
      Ship → tier2 fallback, and no seed value is mixed in.
  * **Action:** in Step 1.2, *before* the `{{SHIP_*}}` variables are derived, the
    installer sets the in-memory `model_routing.ship` to `model_provider: openai`,
    `model_family: gpt-6-luna`, `reasoning_effort: xhigh`, and
    `context_tier: long_context`, and reports the seed in the install summary.
  * Step 3.4 (the config write-back) then materializes those values, so every later
    install, verify, and tune reads an explicit Ship route and never re-applies the
    seed.
  * The seed values live in the installer skill only. No `.tmpl` gains a literal
    provider or family (Core Rule 3, INV-C3). The Python derivation gets no seed
    constant, because no Python install path exists.
* **Tests:**
  * the seed contract test asserts that install-harness states:
    * the first-install snapshot, taken before Step 1.2 and before Step 3.3;
    * the trigger (no `model_routing.ship` key, and no `SHIP_*` key in
      `config.overrides`);
    * the placement (Step 1.2, before `{{SHIP_*}}` derivation);
    * exactly the four seed values;
  * it also asserts that no `templates/**/*.tmpl` contains `gpt-6-luna` as a
    literal;
  * a config holding the seeded Ship block (what the write-back produces) derives
    `SHIP_FAMILY=gpt-6-luna`, `SHIP_PROVIDER=openai`, `SHIP_REASONING_EFFORT=xhigh`,
    and `SHIP_CONTEXT_TIER=long_context`;
  * a config with an explicitly present but empty ship block (the first-install
    operator path) resolves `SHIP_FAMILY` from tier2;
  * the `install-harness` manifest entry is `unchanged` after the edit.
* **Posture:** test-first. **Size:** S. **Complexity:** low.

### C4a — Pipeline agent templates bind to role variables (the durable pin), plus mirrors

* **Files:** `templates/agents/_ship.agent.md.tmpl`, `templates/agents/_stage.agent.md.tmpl`,
  `.github/agents/_ship.agent.md`, `.github/agents/_stage.agent.md`, the manifest
  checksums of those two installed entries, and `tests/test_role_bound_pipeline_render.py`
  (new). *Operator amendment 2026-09-27T22:50-07:00:* also the one-line
  `model_routing.ship.context_tier: "long_context"` in `.autoharness/config.yaml`,
  with its `artifacts[]` checksum and the top-level `config_hash` refreshed from the
  raw blob (moved here from C7; see below).
* **Changes:**
  * The Ship template frontmatter becomes `model_family: "{{SHIP_FAMILY}}"`,
    `model_provider: "{{SHIP_PROVIDER}}"`, `reasoning_effort: "{{SHIP_REASONING_EFFORT}}"`,
    `context_tier: "{{SHIP_CONTEXT_TIER}}"`. Stage becomes the same with `STAGE_*`.
  * Because the role variables fall back per field to tier2 / tier3, a workspace
    without role routes renders exactly as before.
  * ~~The installed mirrors gain `context_tier: "default"`.~~ *Operator ruling 5a
    (2026-09-27T22:50-07:00):* the installed Ship mirror gains
    `context_tier: "long_context"`, and the installed Stage mirror gains
    `context_tier: "default"`. Their `model_*` values are
    unchanged: Ship stays `claude-opus-5.5` / `anthropic` / `high`, and Stage stays
    `claude-opus-5.5`.
  * *Operator ruling 5a, sequencing consequence:* the dogfood config's explicit
    `model_routing.ship` gains `context_tier: "long_context"` in this unit, not in
    C7, so the installed Ship mirror equals the render under this repository's config
    from C4a onward. No other config key changes here.
  * ~~`max_subagent_tier` is **not** changed (stashed follow-up).~~ *Operator ruling
    5b (2026-09-27T22:50-07:00):* the Ship template's literal `max_subagent_tier: 2`
    (line 7) changes to `max_subagent_tier: 3`. That matches the installed mirror
    (already `3`), removes the F-B3 / D-B4 divergence, and retires stash `F9F40F94`.
    It is a generic change: every newly rendered Ship gets `3`, and the release notes
    say so. Any test or verifier expectation that pins the Ship template
    `max_subagent_tier` to `2` is updated to `3`. A read-only audit at `36146ba9`
    found none: the `max_subagent_tier: 2` literals in `tests/test_verify_workspace.py`
    write synthetic fixture agents and are not template pins. The Stage template's
    `max_subagent_tier` is unchanged.
* **Tests:**
  * rendering the Ship template under this repository's config gives
    `model_family: claude-opus-5.5`, `model_provider: anthropic`, and
    `context_tier: long_context` (the pin; operator ruling 5a replaced `default`);
  * rendering under a config with no ship route gives the tier2 family and
    `context_tier: default`;
  * rendering under a config holding the fresh-install seed gives `gpt-6-luna` /
    `openai` / `xhigh` / `long_context`;
  * under all three configs the rendered Ship declares `max_subagent_tier: 3`
    (operator ruling 5b);
  * **rendered-candidate validation (H-C6; plan-2 unit B2b):** for each of these
    three configs, the Ship and Stage templates are rendered with
    `verify_workspace._render_template` over `_compose_artifact_variables(
    _derive_template_variables(...), model_routing, role)`, and the rendered
    frontmatter passes B1 `check_agent(..., profile="tier-routed", mode="installed")`
    with zero non-informational findings.
    * B1 installed mode covers the frontmatter only. Body placeholders follow the
      repository's existing unresolved-placeholder rules, including the
      exempt output-schema exemplars (review AN-F8).
    * Template-mode validation alone does not satisfy this unit;
  * B3's conformity test passes on both templates and both installed files.
* **Posture:** test-first. **Size:** S. **Complexity:** medium.

### C4b — Route variables are config-authoritative in verify's staged render

* **Files:** `src/autoharness/verify_workspace.py` (`_derive_template_variables`, which
  gains a keyword-only `config_authoritative: bool` computed by the caller from the
  load result, and a warning helper), and `tests/test_route_variable_precedence.py`
  (new).
* **Changes (review AN-F3 / AS-F6):**
  * **The problem:** `_derive_template_variables` seeds from
    `manifest.variables_used` and then `setdefault`s the config-derived routing
    variables. A route variable recorded by an older install therefore wins over the
    current config in verify's staged render, and tune would act on a stale render.
  * **Route family:** every variable returned by `_derive_tier_route_variables`,
    `_derive_orchestrator_route_variables`, `_derive_role_route_variables`,
    `_derive_raw_escalation_variables`, and `_derive_escalation_prose_variables`,
    including the new `*_CONTEXT_TIER` variables.
  * For the route family only, precedence becomes (reviews AS-F9, AS-F10):
    1. `config.overrides[<VAR>]`, the operator's explicit template-variable override,
       which install-harness Step 1.0b item 7 applies. Verify does not honor it
       today; C4b makes it do so for route variables;
    2. the config-derived value, **assigned** over any `variables_used` value. This
       matches the P-013.5 rule that the live config is authoritative for routing,
       and the Orchestrator's session-start reload;
    3. the `variables_used` value. It is used only when no authoritative config is
       loaded.
  * **Authoritative config:** `.autoharness/config.yaml` exists, parses to a mapping,
    and raises no `invalid-config-yaml` strict-schema blocker.
    * In a manifest-only installation (no config) or with an invalid config, the
      existing manifest-first `setdefault` precedence is kept unchanged.
    * No `ROUTE_VARIABLE_STALE` warning is emitted then, because there is no
      authoritative value to compare against.
  * Every non-route variable keeps its existing manifest-first precedence.
  * When a recorded route variable differs from its config-derived value, verify
    also appends a non-fatal `warnings[]` entry,
    `ROUTE_VARIABLE_STALE: <VAR> recorded=<x> config=<y>`, so the operator sees that
    the manifest record is out of date.
  * The dogfood manifest's `variables_used` records no route variables, so this
    repository's render is unchanged.
* **Tests:**
  * a fixture whose manifest records `SHIP_FAMILY: claude-sonnet-5`, while its config
    declares `ship.model_family: claude-opus-5.5`, renders the Ship template with
    `model_family: claude-opus-5.5` (the rendered value, not only the warning). It
    gets exactly one `ROUTE_VARIABLE_STALE: SHIP_FAMILY` warning;
  * a non-route variable recorded in `variables_used` (for example
    `PRIMARY_LANGUAGE`) still wins over its derived default;
  * a fixture with no recorded route variables gets no warning and a byte-identical
    staged render;
  * a fixture whose `config.overrides` sets `SHIP_FAMILY: custom-x`, while its config
    `ship.model_family` is `claude-opus-5.5`, renders `custom-x`. The override wins
    (AS-F9);
  * a manifest-only fixture (no config file) whose manifest records
    `SHIP_FAMILY: claude-opus-5.5` renders `claude-opus-5.5`, not a generic default,
    and gets no `ROUTE_VARIABLE_STALE` warning (AS-F10);
  * an invalid-config fixture keeps manifest-first precedence and emits no stale
    warning.
* **Posture:** test-first. **Size:** S. **Complexity:** medium.

### C5a — Frontmatter contract extension for `context_tier`

* **Files:** `src/autoharness/frontmatter_contract.py`, and
  `tests/test_frontmatter_contract.py` (the B→C extension case, made concrete).
* **Changes:**
  * `context_tier` is added to `ROUTE_VALUE_KEYS`, and only there. `AGENT_OPTIONAL`
    is not a stored literal (plan-2 unit B1, AS-F6), so this single edit makes the
    key optional on `tier-routed` agents, `FM_FORBIDDEN_KEY` on `plugin-global`
    agents, and `FM_FORBIDDEN_KEY` on skills;
  * the enum validator (`CONTEXT_TIER_VALUES`, from C2) is registered through the
    `VALIDATORS` registry. There is no parallel check.
* **Tests:**
  * a `tier-routed` agent with or without `context_tier: default` passes;
  * `context_tier: huge` and `context_tier: ""` each give `FM_TYPE_INVALID`;
  * a `plugin-global` agent with `context_tier` gets `FM_FORBIDDEN_KEY`;
  * a skill with `context_tier` gets `FM_FORBIDDEN_KEY`;
  * in template mode, a placeholder-bearing `context_tier` passes presence checks
    and skips the enum check.
* **Posture:** test-first. **Size:** S. **Complexity:** low.

### C5b — Tier-routed agent templates gain `context_tier` (render gate)

* **Files:**
  * `templates/agents/_orchestrator.agent.md.tmpl`, the 17 non-pipeline
    `templates/agents/**/*.agent.md.tmpl`, and
    `templates/community/agents/adr-generator.agent.md.tmpl`. That file is tier-routed
    after plan-2 unit B3, and it gains `{{TIER_2_CONTEXT_TIER}}`;
  * `tests/test_template_frontmatter_conformity.py` (B3's test, extended).
* **Excluded (INV-B5, H-C7):** `.github/agents/auto-tune.agent.md` and
  `.github/agents/auto-mergeinstall.agent.md`. They are `plugin-global` in the root
  `plugin.json` `agents[]` and must not gain `context_tier` or any other
  route-value key.
* **Changes:** each template adds `context_tier: "{{TIER_n_CONTEXT_TIER}}"` (matching
  its existing `TIER_n_*` family), or `{{ORCHESTRATOR_CONTEXT_TIER}}`. The line is
  quoted the same way as the neighbouring route-value lines.
* **Tests:**
  * the conformity-test extension is scoped to the `tier-routed` profile, selected by
    `agent_profile_for`. Every tier-routed agent template declares `context_tier`
    with the same route prefix as its `model_family` placeholder. That is
    `TIER_n_CONTEXT_TIER` for `TIER_n_FAMILY`, and `ORCHESTRATOR_CONTEXT_TIER` for
    `ORCHESTRATOR_FAMILY` (review AN-F8);
  * every `plugin-global` agent carries no `context_tier`;
  * **rendered-candidate validation (H-C6; B2b):** every edited template, including
    `adr-generator`, is rendered under the dogfood config and under a role-less
    fixture config. Each rendered frontmatter has no unresolved `{{...}}` and passes
    B1 in installed mode. Body placeholders follow the repository's existing
    exempt-exemplar rules (AN-F8).
* **Posture:** test-first (the extended conformity test is RED before the template
  edits). **Size:** S (19 one-line edits, enumerated by the test). **Complexity:** low.

### C5c — Installed tier-routed agent mirrors gain `context_tier`

* **Files:** `.github/agents/_orchestrator.agent.md`, the 13
  `.github/agents/subagents/*.agent.md` files, and those 14 entries' checksums in
  `.autoharness/harness-manifest.yaml`.
* **Changes:**
  * each installed mirror gains `context_tier: "default"`, its resolved value under
    this repository's config (C7). The Ship mirror is not in this set; its
    `long_context` value is set in C4a (operator ruling 5a);
  * **only** that line is added. The mirrors' `model_*` values are not re-resolved
    in this unit;
  * checksums are taken from the raw staged blob (IM-12);
  * the plugin-global agents are excluded, as in C5b.
* **Tests:** B3's conformity test (installed mode) passes on every file, and B2a's
  verify check reports no frontmatter-conformity failure for them.
* **Posture:** mechanical, test-enumerated. **Size:** S. **Complexity:** low.

### C6a — P-013.5 policy text and the Orchestrator invocation directive

* **Files:** `templates/policies/workflow-policies.md.tmpl`,
  `.github/policies/workflow-policies.md`, the `_orchestrator.agent.md.tmpl`
  body (Steps 1 and 2 and the P-013.5 paragraph), the `.github/agents/_orchestrator.agent.md`
  body, `src/autoharness/verify_workspace.py`
  (`_add_orchestrator_invocation_routing_directive_check` only), and the manifest
  checksums of the two mirrors.
* **Changes:**
  * P-013.5: the invocation-time directive includes `context_tier`. When the runtime
    cannot honor a non-`default` tier, the agent records `ROUTING_DEGRADED:
    context_tier` and proceeds at the default context, without halting.
  * The Orchestrator body states the `context_tier` override and its
    `ROUTING_DEGRADED: context_tier` fallback at **both** invocation sites: the
    Stage step and the Ship step.
  * The P-013.5 `context_tier` sentence applies to installed, `tier-routed` agents
    only. Plugin-distributed (`plugin-global`) agents carry no `context_tier`, and
    they run on the operator-selected session model (plan-2 unit B7).
  * `context_tier` values are provider- and environment-agnostic capacity classes
    (`default`, `long_context`). The policy names no vendor, model, or token count
    (Core Rule 3, INV-C7).
  * The directive check (review AN-F6, AS-F7) also requires `context_tier` at each
    invocation site, inside a **bounded** window:
    * the Stage window is the existing one, from `config.model_routing.stage` up to
      `config.model_routing.ship`;
    * the Ship window runs from the first `config.model_routing.ship` up to the next
      Markdown heading line (`^#{2,4} `). In the current template, that heading is
      `### Step 3: Iteration Decision`. So the later `## Model Routing` P-013.5
      summary can never satisfy the Ship site;
    * `ROUTING_DEGRADED: context_tier` is required inside each bounded window;
    * the existing whole-tail `ROUTING_DEGRADED` scoping is unchanged.
  * A version-history row.
  * C5b/C5c edit the orchestrator frontmatter. C6a edits the body only, and the two
    are sequenced to avoid a same-file conflict.
  * Plan-2 unit B7 edits § P-013.1 and § P-013.4 of the same policy file. C6a and
    C6b edit § P-013.5 and § P-013.6 only. The sections are disjoint, so both rebase
    onto B7 and neither rewrites B7's text.
* **Tests:**
  * the directive check passes on the updated mirror;
  * missing-site regressions:
    * removing `context_tier` from the Stage window only fails the check with a
      scoping error;
    * removing it from the Ship invocation step only, while the `## Model Routing`
      summary still mentions it, also fails with a scoping error;
  * a structural test asserts the `context_tier`, `ROUTING_DEGRADED`, and plugin-agent
    exclusion wording in both the template and the mirror;
  * B7's assertion that the P-013.1 and P-013.4 MUST sentences are byte-unchanged
    still passes.
* **Posture:** characterization-first. **Size:** S. **Complexity:** low.

### C6b — P-013.6 escalation handoff carries the resolved `context_tier`

* **Files:**
  * `templates/instructions/escalation-protocol.instructions.md.tmpl` and its mirror
    `.github/instructions/escalation-protocol.instructions.md`;
  * the § P-013.6 text in `templates/policies/workflow-policies.md.tmpl` and its
    mirror;
  * the escalation-step bodies of `templates/agents/_stage.agent.md.tmpl` and
    `templates/agents/_ship.agent.md.tmpl`, and their mirrors;
  * the manifest checksums of the four mirrors.
* **Changes (review AN-F1):**
  * the escalation payload gains a separate field, `resolved_escalation_context_tier`.
    The `resolved_escalation_route` `(model_family, model_provider,
    reasoning_effort)` tuple is **unchanged**, so the same-route guard and every
    tuple consumer are untouched (D-C3, INV-C5);
  * the Stage and Ship "Resolve the escalation route" step adds
    `{{ESCALATION_CONTEXT_TIER}}`, which is role-scoped by `_compose_artifact_variables`
    (C2);
  * P-013.6 states that `context_tier` is excluded from the same-route guard, and
    that an unhonorable escalation `context_tier` records `ROUTING_DEGRADED:
    context_tier` without blocking the handoff.
* **Tests:**
  * a structural test asserts the new payload field in the template and the mirror;
  * the `resolved_escalation_route` row still names exactly three fields;
  * rendering the Stage and Ship templates under the dogfood config gives the
    escalation `context_tier` `default`, because the flat escalation is `""` and so
    falls back to tier3 and then `default`;
  * a fixture with `stage.escalation.context_tier: long_context` and
    `ship.escalation.context_tier: default`, both over a flat escalation family,
    renders Stage with `long_context` and Ship with `default` in their escalation
    steps. This proves the per-role overlay (review AN-F9);
  * the rendered Stage and Ship still pass B1 in installed mode.
* **Posture:** characterization-first. **Size:** S. **Complexity:** low.

### C7 — Dogfood config `context_tier` values and the durable Ship-pin regression test

* **Files:** `.autoharness/config.yaml`, its `artifacts[]` checksum and the
  top-level `config_hash` in `.autoharness/harness-manifest.yaml` (both refreshed
  from the raw blob), and `tests/test_dogfood_ship_route_pin.py` (new).
* **Changes:**
  * Add `context_tier: "default"` to tier1-3, orchestrator, and stage. The reviewed
    text also added it to ship, with the note "~~The Ship value `default` is the
    operator ruling's value for this repository~~".
    *Operator ruling 5a (2026-09-27T22:50-07:00):* the Ship value is
    `"long_context"`, and C4a has already added it. C7 checks it is present and does
    not re-add or change it. The
    flat escalation route gets `context_tier: ""`. The dogfood config declares no
    nested `stage.escalation` / `ship.escalation`, and this unit adds none.
  * The explicit `model_routing.ship` (`claude-opus-5.5` / `anthropic` / `high`) is
    **unchanged**. A config comment cites the operator ruling (2026-09-27T13:18:02-07:00),
    and the Ship `context_tier` ruling (2026-09-27T22:50-07:00), though the pin does
    not rely on the comment surviving.
  * The edit is additive only. No existing key or value changes.
* **Tests:** the new test asserts six things:
  1. the config Ship route is `claude-opus-5.5` / `anthropic` / `high`, with
     `context_tier: long_context` (operator ruling 5a; was `default`);
  2. the installed `_ship.agent.md` frontmatter matches it on all four keys, and
     declares `max_subagent_tier: 3`;
  3. the Ship template rendered under this config (through `_compose_artifact_variables`)
     matches the installed frontmatter's four routing keys and its
     `max_subagent_tier` (operator ruling 5b made both `3`);
  4. on this repository, `verify_workspace` reports `role_route_resolution` with
     `ok: true` (that check emits only `ok` and `errors`, per review AS-F5 / AN-F5),
     `_derive_template_variables` gives `SHIP_FAMILY=claude-opus-5.5` and
     `SHIP_PROVIDER=anthropic`, there is no `migration_proposals[]` entry whose
     `path` is `.github/agents/_ship.agent.md`, and there is no
     `ROUTE_VARIABLE_STALE` warning (C4b);
  5. the Ship escalation route is not `escalation_degraded`;
  6. the fresh-install seed trigger (C3b) does not fire for this repository, because
     the manifest exists and the Ship route is non-empty.
* **Posture:** test-first. **Size:** S. **Complexity:** low.

### C8 — Tune guidance: Ship-default proposal posture, and docs

* **Files:** `.github/skills/tune-harness/SKILL.md` (and its manifest checksum,
  refreshed from the raw blob; review AS-F4 / AN-F4), and `docs/tuning-guide.md`.
* **Changes:**
  * Tune may surface an informational, opt-in "new generic Ship default available"
    proposal **only** when `model_routing.ship` declares no non-empty
    `model_family`. An explicitly declared Ship route is an operator override, and
    tune never proposes replacing it (which covers this repository).
  * **Write-back materialization (H-C4):** the config write-back already stores the
    resolved `{{SHIP_FAMILY}}`, so after any install a Ship family inherited from
    tier2 is indistinguishable from an operator choice. Tune treats every non-empty
    value as an override. As a result, existing workspaces normally never see the
    proposal. That is the intended no-silent-change posture, and the tuning guide
    tells operators to edit `model_routing.ship` to adopt the new default.
  * Tune never auto-applies.
  * Document `context_tier`, its values, its fallback, the raw-vs-resolved escalation
    variables, the fresh-install seed trigger, the `ROUTING_DEGRADED` behavior, the
    plugin-agent exclusion, and the exclusion from the same-route guard.
* **Tests:** a structural assertion that the tune skill states the explicit-route
  exemption and the never-auto-apply rule, and that the `tune-harness` manifest
  entry is `unchanged` after the edit.
* **Posture:** docs/skill only. **Size:** S. **Complexity:** trivial.

## Dependency Graph

C1 → C2 → C3a → C3b → C4a → C4b → C5a → C5b → C5c → C6a → C6b → C7 → C8. The order is linear.

* The whole plan depends on shipment B (plan 2) being merged first, through the
  `blocks` edge.
* C2 needs B1's `frontmatter_contract.py` for `CONTEXT_TIER_VALUES`.
* C4a and C5b need B1's contract module, B2b's rendered-candidate path, and B3's
  conformity test. C5a extends B1 directly.
* C6a and C6b rebase onto B7.
* C6b follows C4a, because both edit the Ship and Stage templates: C4a the frontmatter,
  C6b the body.
* Requirement R4 is covered by C3a, C4a, C5a, C5b, and C5c.

## Decisions and Rationale

Deliberation D-C1 through D-C7. D-C6 implements the binding operator ruling, and the
rest are Stage-recommended, pending operator confirmation.
*Superseded by the operator rulings of 2026-09-27T22:50-07:00. D-C1 through D-C7 are
operator-confirmed in their reviewed-plan form: the deliberation makes the reviewed
plan authoritative, so the confirmation covers the H-C2, H-C3, H-C4, and H-C5
refinements of D-C2, D-C4, and D-C1. D-C6 carries the 5a and 5b overrides. The C4b
and C6b design choices were not named separately. They stand as reviewed plan design
unless the operator overrides them before Ship claims 200-S. See
[Operator Rulings](#operator-rulings-2026-09-27t2250-0700--post-review-amendment).*

* The durable pin is mechanical: role-variable binding plus the explicit config route
  plus a regression test. It never relies on a comment or on a second overrides map.
* The fresh-install seed changes only newly generated configs, so no existing
  workspace silently changes its Ship model.

## Risks and Caveats

* **C4a changes what every target workspace renders for Ship and Stage frontmatter
  whenever it declares role routes.** That is the P-013.5 intent: frontmatter now
  agrees with invocation-time routing. Mitigation: the per-field fallback keeps
  role-less workspaces byte-identical, and a render test covers both cases. Release
  notes state it.
* **C4b changes verify's staged render for any workspace whose manifest records route**
  **variables that differ from its config.** Verify then renders the config value.
  Mitigation: the change is surfaced as ROUTE_VARIABLE_STALE plus ordinary
  checksum drift, and never as a silent write. Tune still needs per-proposal
  approval. The dogfood manifest records no route variables.
* **Row-number pinning in the contract test** (F-C4) and a concurrent edit in 164-S.
  Mitigation: C3a re-derives the row references, and Ship rebases.
* **Manifest checksum churn across about 22 entries:**
  * 14 in C5c;
  * 2 in C4a;
  * 2 in C6a, of which the orchestrator entry is refreshed again;
  * 4 in C6b;
  * 2 in C3a and C3b (the same install-harness entry, refreshed twice);
  Templates are not manifest entries. Mitigation: each unit refreshes only its own
  entries, from the raw staged blob (IM-12), and C5c is a single mechanical commit.
* **A runtime that does not support context selection.** Mitigation:
  `ROUTING_DEGRADED`, which is non-fatal.
* **`gpt-6-luna` availability varies by environment.** Mitigation: it is an installer
  default, not a template constant, and operators override it in their config.

## Plan Hardening Signals

* Schema or contract change — **present** (`harness-config` schema; the frontmatter
  contract).
* Security — absent.
* Migration or config action — **present** (dogfood config edit; a new fresh-install
  default; tune proposals).
* Operator checkpoint — **present** (a binding ruling; tune proposal approval).
* Rollout risk — **present** (Ship/Stage frontmatter rendering in all workspaces;
  about 20 templates).

Requires plan hardening: yes

## Runtime Verification and Closure

* Runtime surfaces: `autoharness verify-workspace` (C2) and installer rendering
  (C3a-C6b).
* Runtime proof:
  1. `autoharness verify-workspace --json` on this repository passes, with
     `role_route_resolution.ok: true`, no `_ship.agent.md` migration proposal, and
     no `ROUTE_VARIABLE_STALE` warning. The derived `SHIP_FAMILY` is
     `claude-opus-5.5` (C7 test 4);
  2. a fresh scratch install with no config renders Ship
     `gpt-6-luna` / `openai` / `xhigh` / `long_context`, and writes that Ship route
     into the new config;
  3. a scratch first install whose operator config has an explicitly present but
     empty ship block renders Ship from tier2, with no seed and no behavior change.
* Precheck: `autoharness` is importable and install-harness can run in a scratch
  directory. Proof 2 is agent-executed, because install-harness is a skill.
* Blocked path: if proof 2 or 3 cannot run in this environment, closure records it as
  `BLOCKED` with the reason. It is never replaced by a unit test. The C3b derivation
  test and the C4a render test remain the automated evidence.
* Closure records all three.

## Plan Hardening

* **Hardening required:** yes.
* **Learnings and instructions consulted:**
  * `docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md` (no
    hardcoded provider IDs in `.tmpl` files; the role-route fallback);
  * `docs/compound/p013-orchestrator-model-routing.md`;
  * F02FD596 deliberation `docs/decisions/2026-08-07-model-routing-hierarchy-dynamic-reload-deliberation.md`
    (the nested escalation never falls back to the flat route; H2 ambiguity);
  * `escalation-protocol.instructions.md` (the ESCALATION_DEGRADED definition);
  * `constitution.instructions.md` (Core Rule 3).
* **Protected invariants:**
  * INV-C1 (BINDING): this repository's Ship route and installed Ship frontmatter stay
    `claude-opus-5.5` / `anthropic`, at every commit of this feature.
  * INV-C2: a workspace without role routes renders byte-identical routing keys
    before and after, apart from the added `context_tier` line.
  * INV-C3: no `.tmpl` hardcodes a provider or family.
  * INV-C4: the both-present escalation ambiguity semantics are unchanged.
  * INV-C5: ESCALATION_DEGRADED equality is unchanged.
  * INV-C6: existing configs without `context_tier` validate and resolve to
    `default`.
* **ProposedAction / ActionRisk:**

  | ProposedAction | ActionRisk | Approval |
  |---|---|---|
  | Edit `harness-config` schema route objects | medium | Plan-review PASS; additive only |
  | Rebind Ship/Stage template frontmatter to role variables | high | Binding operator ruling; the render tests in C4a are a merge prerequisite |
  | Edit the dogfood `.autoharness/config.yaml` | medium | Additive `context_tier` only; the Ship route is untouched (INV-C1) |
  | Change the generic fresh-install Ship default | medium | Operator request (verbatim); new installs only |

* **Rollback (corrected by review AS-F1):** the role-variable binding in C4a is the
  pin mechanism, so it is **never** reverted on its own.
  * Reverting it would restore `{{TIER_2_*}}` in the Ship template. The next
    re-install of this repository would then render tier2 `claude-sonnet-5` and break
    INV-C1.
  * A C4a defect is fixed forward, or rolled back only by removing the
    `context_tier` line and the `ROUTE_VARIABLE_STALE` warning while the `SHIP_*` /
    `STAGE_*` binding stays.
  * Any rollback commit must keep the C7 pin test green. A rollback that fails it is
    rejected.
  * Revert C3b to remove the fresh-install seed. That affects new installs only.
  * C4b is **not** reverted independently (review AN-F11). Reverting it would
    restore manifest-first route precedence, and existing installs whose manifest
    records a stale route variable would render the stale value again. A C4b defect
    is fixed forward, keeping the config-authoritative precedence. Any rollback
    commit must keep the C4b stale-manifest render test green.
  * C1 is additive.
  * Rollback trigger: any render test showing a role-less workspace changed, or the
    pin test failing.
* **Monitoring:** the next auto-tune on this repository must report no Ship-route
  proposal. The first fresh install in a target workspace records Ship
  `gpt-6-luna` / `long_context` in its manifest.
* **Operator checkpoint:** D-C6 is binding and needs no confirmation. D-C1 through
  D-C5 and D-C7 need confirmation, but none blocks safe execution. If the operator
  later picks a non-default dogfood Ship `context_tier`, that is a one-line config
  change covered by the C7 test.
  *Superseded by the operator rulings of 2026-09-27T22:50-07:00: D-C1 through D-C5
  and D-C7 are confirmed. The operator picked the dogfood Ship `context_tier`
  `long_context` (ruling 5a). That one-line config change now lands in C4a, and the
  C7 test pins it.*
* **Review-gate capability risk:** the same as Plan A.

### Hardening Pass 2 (2026-09-27)

* **Trigger:** the plan-2 review changed plan 2's contract and reported five required
  downstream adjustments to this plan. Hardening was re-run over the whole plan,
  grounded in `verify_workspace.py`, `schemas/harness-config.schema.json`,
  install-harness `SKILL.md`, `templates/harness-config.yaml.tmpl`,
  `.autoharness/config.yaml`, `.autoharness/harness-manifest.yaml`, and
  `plugin.json`.
* **Downstream adjustments from the plan-2 review.** Each one was verified against
  plan-2 units B1, B2b, B3, and B7, and the plan-2 `## Plan Review` downstream list,
  before it was applied:

  | # | Adjustment | Verified against | Applied in |
  |---|---|---|---|
  | DA-1 | `context_tier` joins `ROUTE_VALUE_KEYS`, not `AGENT_OPTIONAL` (not a stored list). It is optional on tier-routed agents and forbidden on plugin-global agents and on skills. Its validator registers through `VALIDATORS` | B1 key sets, AS-F6 cycle 2; `VALIDATORS` registry | C5a |
  | DA-2 | `adr-generator.agent.md.tmpl` joins the file list with `{{TIER_2_CONTEXT_TIER}}`. The test extension covers `tier-routed` agents only | B3 `adr-generator` gains `TIER_2_*` | C5b |
  | DA-3 | No `context_tier` on `auto-tune` / `auto-mergeinstall` | B3 plugin-global profile, INV-B5; `plugin.json` `agents[]` lists exactly these two | C5b, C5c |
  | DA-4 | C4/C5 template edits pass B2b's rendered-candidate check (installed mode), not only template mode | B2b action rule 1 | C4a, C5b (H-C6) |
  | DA-5 | C6 and B7 edit disjoint sections of `workflow-policies.md` (rebase only). C6's `context_tier` wording excludes plugin agents | B7 downstream note | C6a, C6b |

* **Hardening findings:**

  | ID | Gap found | Resolution |
  |---|---|---|
  | H-C1 | C2 named `STAGE_/SHIP_ESCALATION_CONTEXT_TIER` without saying whether they are raw or resolved. The existing `STAGE_/SHIP_/LEGACY_ESCALATION_*` families are raw pass-through (constraint C3), and `LEGACY_ESCALATION_CONTEXT_TIER` was missing. Resolving those would reintroduce the H2 flat+nested ambiguity | Two explicit families: resolved (tier, orchestrator, role, and the collapsed `ESCALATION_CONTEXT_TIER`) and raw (the three `*_ESCALATION_CONTEXT_TIER`). The config write-back uses the raw variables for escalation blocks (C2, C3a) |
  | H-C2 | `_escalation_route_has_any_field` selects the nested-vs-flat source. If it counted `context_tier`, a nested block with only `context_tier` would override the flat route in its entirety (H4), silently drop the escalation family to tier3, and could trigger both-present ambiguity | The predicate and `nonEmptyRouteFields` are unchanged. A separate `_effective_escalation_context_tier_for_role` defines the chain. `_effective_escalation_route_for_role` keeps its 3-tuple, and a test pins it (C2; INV-C4) |
  | H-C3 | The "fresh-install seed" had no location and no deterministic trigger. install-harness is agent-executed, and there is no Python install path, so "a no-config fixture resolves `gpt-6-luna`" could not be tested as written. Changing the `SHIP_FAMILY` row default would break parity with the Python derivation | The seed is applied in Step 1.2, before derivation. The first-install state is snapshotted before Step 3.3 writes the manifest. Trigger: first install and no `model_routing.ship` key; an explicitly present empty block is honored (review AS-F2, AS-F3, AN-F2). The row defaults are unchanged. A structural seed-contract test is added, plus a derivation test over the seeded config (C3b) |
  | H-C4 | The config write-back materializes the resolved Ship family, so tune's "absent or empty" condition never holds after any install. R9's proposal is effectively inert for existing workspaces | Documented as the intended no-silent-change posture. Every non-empty value is an override. The tuning guide gives the manual adoption path (C8). Stage-recommended, pending operator confirmation (confirmed with D-C4, 2026-09-27T22:50-07:00) |
  | H-C5 | The enum was defined in three places (schema, C2 check, C5 validator), and `""` would have been legal in rendered frontmatter | A single `CONTEXT_TIER_VALUES` holds the resolved values. The schema adds `""` for unset/inherit. A parity test is added, and `""` in frontmatter is rejected (C2) |
  | H-C6 | DA-4. Rendered-candidate validation was absent | Render tests with B1 in installed mode: C4a under the dogfood, role-less, and seeded configs; C5b under the dogfood and role-less configs |
  | H-C7 | C5 exceeded one concern (contract, 19 templates, 14 mirrors, 14 checksums). The plugin-global exclusion was implicit, and the mirror edit could have re-resolved stale `model_*` values | Split into C5a (contract), C5b (templates and render gate), and C5c (mirrors), after review AN-F7. The exclusion is explicit. C5c adds only the `context_tier` line |
  | H-C8 | C7's drift assertion ("no drift finding") had no observable check, and the Ship `context_tier` value was not pinned | Six concrete assertions: the config and installed values, the render parity, no `_ship.agent.md` migration proposal, the escalation not degraded, and the seed not firing (C7) |
  | H-C9 | The `context_tier` values could drift toward vendor or window-size names | INV-C7 and the C6a wording |

* **Protected invariants added:**
  * INV-C7: `context_tier` values are provider- and environment-agnostic capacity
    classes. No policy, schema, or template names a vendor, model, or token count
    for them.
  * INV-C8: no plugin-distributed agent (`plugin.json` `agents[]`) carries
    `context_tier` (extends INV-B5).
  * INV-C9: the raw `*_ESCALATION_CONTEXT_TIER` variables never take a resolved or
    fallback value.
* **INV-C1 re-verified (BINDING):**
  * the dogfood `model_routing.ship` is explicit (`claude-opus-5.5` / `anthropic` /
    `high`);
  * the manifest exists, so the seed cannot fire;
  * the write-back preserves the explicit route;
  * the C4a role binding renders it;
  * C8 exempts it from tune proposals;
  * the C7 test pins all of the above.
  The Ship `context_tier` for this repository is `default`.
  *Superseded by operator ruling 5a (2026-09-27T22:50-07:00): the Ship
  `context_tier` for this repository is `long_context`. C4a sets it, and the C7 test
  pins it along with the Ship `max_subagent_tier: 3` from ruling 5b.*
* **Observed, out of scope (no change here):** the installed tier-1 subagents record
  `model_family: gpt-5.6-luna`, but the dogfood `tier1.model_family` is now
  `gpt-6-luna`. That is pre-existing mirror staleness. C5c deliberately does not
  re-resolve `model_*`. It is a candidate stash entry for the operator.
* **ProposedAction / ActionRisk additions:**

  | ProposedAction | ActionRisk | Approval |
  |---|---|---|
  | Extend the plan-2 frontmatter contract (`ROUTE_VALUE_KEYS`, `VALIDATORS`) | medium | Plan-review PASS. Plan 2 designed this extension point |
  | Add the fresh-install seed to install-harness | medium | Operator request. First install only, whole-route-empty Ship only |

* **Rollback addition:** revert C5b and C5c together to remove the key from the
  templates and the mirrors. C5a can stay, because the key is optional. C6b can be
  reverted independently, because the escalation tuple is unchanged.
* **Review-gate capability risk (H-B12 precedent):** plan-review emits the literal
  `dispatch_mode:` and `decision:` markers. If the runtime has no reviewer-subagent
  tool, review runs under the declared degradation, with write-denied external
  anchor passes for the cross-model personas.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* Review record: `docs/reviews/2026-09-27-context-tier-model-routing-plan-review.md`.
  It is authoritative for findings, dispositions, and persona coverage.
* Gate: **PASS** under severity rule C4, with 0 open P0 and 0 open P1. It came after
  three review-fix cycles and a bounded fix-verification pass confined to the
  cycle-3 fixes.
  * Found (unique): 1 P0, 9 P1, 7 P2, and 2 P3.
  * Open: 1 P3 (SB-F1), an accepted out-of-scope residual.
* Plan hardening was required and is satisfied (the original record plus Hardening
  Pass 2).
* Persona coverage:
  * inline passes: Constitution, Python, Scope Boundary, and Learnings;
  * independent anchor-route passes (`gpt-6-sol`, external Copilot CLI with `write`
    and `shell` denied): Architecture Strategist and Agent-Native Parity;
  * Security Lens was not triggered;
  * declared degradation: `TOOL_DEGRADED: reviewer-subagent-dispatch — declared
    fallback: single-agent persona pass`.
* Review-driven structure changes:
  * C3 was split into C3a and C3b;
  * C4 was split into C4a and C4b, where C4b is the config-authoritative route
    precedence;
  * C5 was split into C5a, C5b, and C5c;
  * C6 was split into C6a and C6b, where C6b is the escalation handoff
    `context_tier`.
* Stage-recommended decisions pending operator confirmation are listed in the review
  record. *Superseded: they are operator-confirmed as of 2026-09-27T22:50-07:00,
  except C4b and C6b, which were not named separately (see Operator Rulings below).*
* Harvest is blocked by shipment B (plan 2).

## Operator Rulings (2026-09-27T22:50-07:00) — post-review amendment

The operator ruled on the staging deliberation's open items. Verbatim:

> "Confirm 1-4. 5. Set Ship's context_tier to long_context in the template. Set Ship's max_subagent_tier to 3 in its template."

Items 1 to 4 confirm D-C1 to D-C5, D-C7, D-C6, and D-P1 to D-P3, in their
reviewed-plan form. That form includes the H-C2, H-C3, H-C4, and H-C5 refinements.
The C4b and C6b design choices were not named separately. They stand as reviewed
plan design unless the operator overrides them before Ship claims 200-S. Item 5
overrides two values. This section records them. The deliberation holds the full
mapping, in its section "Operator rulings (2026-09-27T22:50-07:00)".

* **5a — Ship `context_tier` is `long_context`.** The following is a stated assumption
  (the Orchestrator's interpretation, recorded by Stage):
  * the Ship template keeps the variable binding `context_tier: "{{SHIP_CONTEXT_TIER}}"`
    (placeholder discipline, Core Rule 3). A fresh install renders `long_context`
    through the unchanged D-C4 / C3b seed;
  * this repository's `model_routing.ship.context_tier` becomes `"long_context"`, not
    `"default"`, and the installed `.github/agents/_ship.agent.md` gains
    `context_tier: "long_context"`;
  * Stage, tier1-3, and the orchestrator keep `"default"`, and the C7 regression test
    pins `long_context` for Ship.
  * Amended units: C4a (Ship mirror value, render expectation, and the one-line Ship
    config edit moved here from C7) and C7 (test pins; C7 no longer adds the Ship line).
    C5c now states that the Ship mirror is outside its set.
* **5b — the Ship template `max_subagent_tier` changes from `2` to `3`.** This is
  folded into C4a, which already rewrites the Ship template frontmatter. It replaces
  the reviewed line "`max_subagent_tier` is **not** changed (stashed follow-up)" and
  retires stash `F9F40F94`. The 193-F frontmatter contract already accepts an int
  from 1 to 3. The feature's release notes state the change.
* **Review state.** These edits come after the review record's `reviewed_blob` and
  after its PASS. They apply operator rulings. They are not new design, and they do
  not reopen any finding, so no re-review is required. This follows the repository's
  post-review amendment convention (the PR #460 "Post-review amendments" sections in
  the sibling plan reviews, and the 2026-09-15 terminal-shipment-closure plan's
  operator-authorized `dag-root` amendment). The only structural consequence is that
  the one-line Ship config edit moves from C7 to C4a. That change is sequencing, not
  scope. The review record carries a matching "Post-review amendments" note.
* **Backlog.** Tasks `194.005-T` (C4a) and `194.012-T` (C7) were amended in place, and
  the 200-S manifest is unchanged. The feature description of `194-F` and its DoD
  release-note line were updated to match.

## Pre-Claim Drift Amendments (2026-10-04)

Stage re-checked shipment 200-S against `main` at `300d0716`, after 192-F and 193-F
landed. The design holds (verdict **MINOR_NOTES_ONLY**). Four task bodies were amended
in place, under Stage authority, so that a literal execution keeps landed pins green:

1. **C1 (`194.001-T`):** also edit `schemas/harness-config/1.1.0.schema.json` in
   lockstep (byte-identical to the root minus `$id`), and add `context_tier` to the
   nested-escalation property set in `tests/test_escalation_hierarchy_schema.py`.
   `1.0.0.schema.json` stays untouched. D-C5 stands: the 1.1.0 mirror is edited in
   place, with no 1.2.0 mirror.
2. **C5a (`194.007-T`):** C5a owns the `docs/tuning-guide.md`
   `## Agent and Skill Frontmatter Contract` tables and the `context_tier` value rule.
   It flips `test_routing_key_constants` to `assertIn` and rewrites the B->C extension
   test to assert live behaviour.
3. **C6a (`194.010-T`):** update the `_write_minimal_verify_workspace_fixture` Step 1
   and Step 2 bodies in `tests/test_verify_workspace.py`. All
   `PluginGlobalPolicyClarificationTests` pass unmodified (§ P-013.5 is byte-identical
   between template and mirror, and case (d) stays verbatim). The Ship window ends at
   the next `^#{2,4} ` heading or EOF, and the version row is 1.30.0.
4. **C8 (`194.013-T`):** C8 must not edit the tuning-guide contract section, which
   C5a owns. It documents `context_tier` in a new `##` section, and tune-harness
   Step 1.5c and B5's Step 2.2 tokens stay intact.

C2 (`194.002-T`) is split into C2a and C2b for the 2-hour granularity rule. Full
record: `docs/reviews/2026-09-27-context-tier-model-routing-plan-review.md`,
§ Pre-claim drift check 2026-10-04.
