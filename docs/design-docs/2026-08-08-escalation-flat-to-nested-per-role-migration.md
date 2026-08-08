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
  `harness-config/1.1.0.schema.json` reject the config document (a `not`
  constraint at the `model_routing` object level, referencing the shared
  `definitions.nonEmptyRouteFields` fragment). See the "Schema-version bump"
  section below for why this constraint lives in the `1.1.0` mirror and not
  the `1.0.0` mirror.
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
`stage.escalation` / `ship.escalation` **values** were written to this
repository's own `.autoharness/config.yaml` as part of 113-F/121-S — the
nested override blocks are always-rendered in
`templates/harness-config.yaml.tmpl` with empty-string defaults (Copilot
review round 2, PR #316), and this workspace continues to resolve its
escalation route from the legacy flat block exactly as before (all-empty
nested sub-fields are treated as absent and never trigger H2). Operators may
opt into nested per-role escalation independently, at their own discretion,
once this migration lands.

## Schema-version bump: 1.0.0 -> 1.1.0 (PR #316 Copilot review)

The initial implementation added the nested `stage.escalation`/
`ship.escalation` properties and the H2 `not` ambiguity constraint **in
place** to both `schemas/harness-config.schema.json` (root/current) and the
published `schemas/harness-config/1.0.0.schema.json` mirror, while leaving
`schema_version`'s `const` and `schema_contracts.py`'s
`current_version`/`known_versions` for the `config` contract unchanged at
`1.0.0`. Copilot review correctly identified this as a schema-versioning
ambiguity forbidden by `src/autoharness/schema_contracts.py`'s
versioned-contract discipline: an old 1.0.0 validator rejects a document
using the new nested override (both `stage`/`ship` sub-schemas declare
`additionalProperties: false`), while the patched-in-place 1.0.0 validator
accepts it — the same version identifier no longer names one contract.

Fixed by mirroring the tool-telemetry-event v1.0->v1.1 precedent
(`schema_contracts.py`'s `tool-telemetry-event` entry, PR #294 review-fix
cycle 2):

* `schemas/harness-config/1.0.0.schema.json` restored to its exact
  pre-F02FD596 bytes (byte-identical to `main`) — never mutated in place.
* `schemas/harness-config/1.1.0.schema.json` added as a new versioned
  mirror carrying the nested per-role escalation additions (identical to
  the root schema except `$id`).
* `schemas/harness-config.schema.json` (root/current) keeps the additions
  and its `schema_version.const` bumped to `"1.1.0"`.
* `src/autoharness/schema_contracts.py`'s `config` contract entry:
  `current_version: "1.1.0"`, `known_versions: ("0.9.0", "1.0.0", "1.1.0")`.
* `templates/harness-config.yaml.tmpl`'s default `schema_version` bumped to
  `"1.1.0"` so freshly installed configs track the current contract.
* This repository's own dogfood `.autoharness/config.yaml` bumped its
  `schema_version` to `"1.1.0"` (structural version bump only — no
  escalation data values changed, preserving H8 above) with a refreshed
  manifest checksum in `.autoharness/harness-manifest.yaml`.

No `CONTRACT_MIGRATIONS["config"]` entry was added for this bump: it is
purely additive (no field rename/removal), so an existing config declaring
`schema_version: "1.0.0"` remains fully valid forever against the restored,
untouched 1.0.0 mirror via `resolve_contract_schema_path`'s
version-matched-schema lookup — exactly the same non-forced-migration
treatment given to the tool-telemetry-event 1.0->1.1 bump. `verify_workspace`
now classifies an installed 1.0.0 config as `known-legacy` (no action
required) rather than `current`; adopting nested per-role escalation
requires declaring `schema_version: "1.1.0"`.

## Files affected

* `schemas/harness-config.schema.json`, `schemas/harness-config/1.1.0.schema.json`
  (new mirror) — nested `escalation` property under `stage`/`ship`; `not`
  constraint (H2) at the `model_routing` level; deprecated flat `escalation`
  description; `schema_version.const` bumped to `1.1.0`.
  `schemas/harness-config/1.0.0.schema.json` restored to its exact
  pre-F02FD596 bytes (never mutated in place, see "Schema-version bump"
  above).
* `src/autoharness/schema_contracts.py` — `config` contract entry
  `current_version`/`known_versions` bumped to track `1.1.0`.
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
* `templates/harness-config.yaml.tmpl` — always-rendered nested
  `stage.escalation` / `ship.escalation` blocks (empty-string defaults);
  deprecation notice on the legacy flat block; default `schema_version`
  bumped to `1.1.0`.
* `.autoharness/config.yaml` (this repository's own dogfood config) —
  `schema_version` bumped to `1.1.0` (structural only, no escalation data
  changed); `.autoharness/harness-manifest.yaml` checksum refreshed.
* `.github/skills/install-harness/SKILL.md` — variable-resolution table
  updated for the nested precedence description, including the six raw
  `STAGE_ESCALATION_*`/`SHIP_ESCALATION_*` variables and Step 3.4
  preservation language.
