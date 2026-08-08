---
title: "Migrating model_routing.escalation from legacy flat to nested per-role (F02FD596)"
status: active
related_feature: 113-F
related_shipment: 121-S
---

# Migrating `model_routing.escalation` from legacy flat to nested per-role (F02FD596)

## Summary

Prior to F02FD596, `.autoharness/config.yaml` declared exactly one
telemetry-driven auto-escalation route for P-013.6:

```yaml
model_routing:
  escalation:
    model_family: "..."
    model_provider: "..."
    reasoning_effort: "..."
```

This route was **role-agnostic** — the same escalation target applied
regardless of whether Stage or Ship was the halting agent. F02FD596
introduces an optional **nested per-role escalation override**, allowing
Stage and Ship to declare distinct escalation routes:

```yaml
model_routing:
  stage:
    model_family: "..."
    model_provider: "..."
    reasoning_effort: "..."
    escalation:            # NEW: nested per-role override for Stage
      model_family: "..."
      model_provider: "..."
      reasoning_effort: "..."
  ship:
    model_family: "..."
    model_provider: "..."
    reasoning_effort: "..."
    escalation:            # NEW: nested per-role override for Ship
      model_family: "..."
      model_provider: "..."
      reasoning_effort: "..."
  escalation:               # DEPRECATED-LEGACY: retained for compatibility
    model_family: "..."
    model_provider: "..."
    reasoning_effort: "..."
```

## Resolution precedence (per role)

1. **Nested per-role override**: `model_routing.<role>.escalation` for the
   acting role (`stage.escalation` or `ship.escalation`). A nested override
   that declares only some fields falls back **per field** to
   `model_routing.tier3` for the missing fields — **never** to the legacy
   flat route.
2. **Legacy flat fallback (DEPRECATED)**: when the acting role has no nested
   `escalation` override, `model_routing.escalation` (the pre-F02FD596 flat,
   role-agnostic route) resolves instead.
3. **Tier3 fallback**: any field still unresolved after (1)/(2) falls back
   per-field to `model_routing.tier3`.

## H1 — No-regression guarantee (backward compatibility)

A workspace that declares **only** the legacy flat `model_routing.escalation`
route (no nested `<role>.escalation` anywhere) resolves **identically** to
pre-F02FD596 behavior: both roles resolve from the flat route, falling back
per-field to `tier3`. No existing `.autoharness/config.yaml` needs to change
to remain valid, and `verify_workspace`'s
`_add_escalation_route_resolution_check` preserves the exact
`resolved_escalation_family` / `resolved_escalation_provider` /
`resolved_escalation_reasoning_effort` / `same_route_roles` top-level
output shape computed from the legacy/flat route for this reason — 21
pre-existing tests validate this with zero test modification required by
the schema/resolver rewrite.

## H2 — Both-present fail-closed (AMBIGUOUS)

The legacy flat `model_routing.escalation` and any nested
`<role>.escalation` (for either role) **MUST NOT** both declare a non-empty
field simultaneously. If both are present:

* **Schema level**: `harness-config.schema.json` /
  `harness-config/1.0.0.schema.json` reject the config document (a `not`
  constraint at the `model_routing` object level, referencing the shared
  `definitions.nonEmptyRouteFields` fragment).
* **Loader/verification level**: `verify_workspace`'s
  `_add_escalation_route_resolution_check` returns `ambiguous: true`,
  `ok: false` with an `AMBIGUOUS_ESCALATION_CONFIG` message, as a backstop
  for any config that reaches the loader without schema validation (or a
  schema version lag).

**Never auto-pick a winner.** To migrate, either:

* fully adopt nested per-role escalation and delete/empty the legacy flat
  `model_routing.escalation` block, or
* remove the nested `<role>.escalation` override(s) and keep using the
  legacy flat route.

## H3 — Role-scoped `ESCALATION_DEGRADED` (same-route no-op)

The `ESCALATION_DEGRADED` same-route guard compares the **acting role's own**
fully-resolved escalation tuple against that **same role's own** resolved
role route (P-013.5) — never a different role's route. Stage and Ship are
evaluated independently: it is possible for Stage's resolution to be
`ESCALATION_DEGRADED` (e.g., Stage's role route already equals `tier3`, and
no distinct escalation override is declared for Stage) while Ship's
resolution is a genuine escalation, or vice versa. `verify_workspace` reports
this per-role in the `per_role` dict and preserves the `same_route_roles`
top-level list (roles for which the guard fired) for backward compatibility.

## H4 — Per-field fallback never crosses to the legacy route

A nested `<role>.escalation` override that declares only some fields (e.g.,
only `model_family`) falls back **per missing field** directly to
`model_routing.tier3` — it never falls back to the legacy flat
`model_routing.escalation`, even in the hypothetical case where the legacy
route is also present in a way that would otherwise be non-ambiguous. (In
practice this scenario cannot arise without also triggering H2's
both-present fail-closed rule, since a partially-declared nested override is
itself "present.") This rule exists to keep the fallback chain unambiguous
and to guard against implementation drift.

## H5 — Schema `additionalProperties: false` parity

The nested `escalation` property added under `stage` and `ship` in both
schema files uses the identical 3-field shape (`model_family`,
`model_provider`, `reasoning_effort`) and `additionalProperties: false` as
the legacy flat `escalation` property, so an unknown key in a nested
override is rejected identically to an unknown key in the legacy flat block.

## H8 — No dogfood escalation data values written by this migration

This migration is a **structural** change only. No nested
`stage.escalation` / `ship.escalation` values were written to this
repository's own `.autoharness/config.yaml` as part of 113-F/121-S — the
nested override remains commented-out example scaffolding in
`templates/harness-config.yaml.tmpl`, and this workspace continues to
resolve its escalation route from the legacy flat block exactly as before.
Operators may opt into nested per-role escalation independently, at their
own discretion, once this migration lands.

## Files affected

* `schemas/harness-config.schema.json`, `schemas/harness-config/1.0.0.schema.json`
  — nested `escalation` property under `stage`/`ship`; `not` constraint (H2)
  at the `model_routing` level; deprecated flat `escalation` description.
* `src/autoharness/verify_workspace.py` —
  `_add_escalation_route_resolution_check` rewritten for nested-per-role
  resolution, additive `per_role`/`ambiguous`/`deprecated_flat_in_use`
  fields, backward-compatible top-level legacy fields preserved.
* `templates/instructions/escalation-protocol.instructions.md.tmpl` (and
  installed mirror `.github/instructions/escalation-protocol.instructions.md`)
  — 3-step precedence, H2 both-present paragraph, role-scoped H3 wording.
* `templates/policies/workflow-policies.md.tmpl` — P-013.6 section rewrite,
  `1.18.0` changelog entry.
* `templates/agents/_stage.agent.md.tmpl` / `_ship.agent.md.tmpl` (and
  installed mirrors) — Escalation Protocol step 2/3 updated to reference the
  nested-per-role precedence and role-scoped same-route guard.
* `templates/harness-config.yaml.tmpl` — commented-out nested
  `stage.escalation` / `ship.escalation` example scaffolding; deprecation
  notice on the legacy flat block.
* `.github/skills/install-harness/SKILL.md` — variable-resolution table
  updated for the nested precedence description.
