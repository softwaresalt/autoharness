---
title: "Model routing catalog and bindings: tier-delta route catalog and subagent site bindings with schema 1.2.0 (R1-B)"
description: "Plan for the second release unit of the 040-DL model-routing design. Adds a YAML-anchor-free tier-delta route catalog (`model_routing.routes`) and installed-agent subagent site bindings (`model_routing.bindings`) as an additive schema 1.2.0 with a new mirror, extends the R1-A resolver, and lands the verification, drift, tune, install, policy, and documentation surfaces in the same release so no accepted key is ever inert."
doc_type: plan
status: reviewed
created: 2026-10-11
source_stash: BF66F08B
source_deliberation: docs/decisions/2026-10-11-model-routing-v2-deliberation.md
deliberation_id: 040-DL
baseline_document: docs/design-docs/model-routing-v2.md
release: "R1-B"
harvested_feature: "208-F"
harvested_shipment: "215-S"
predecessor_plan: docs/plans/2026-10-11-model-routing-resolver-single-source-plan.md
review_record: docs/reviews/2026-10-11-model-routing-catalog-bindings-plan-review.md
requires_plan_hardening: "yes"
---

# Model routing catalog and bindings (R1-B)

## Outcome

After this plan ships (and `R1-A` has shipped):

* `model_routing.routes` accepts named **tier deltas** (`tier` plus optional field
  overrides). `model_routing.bindings` assigns a route to a registered subagent site
  (`agent:<id>`). Both are optional; an absent or empty block changes nothing.
* The config contract is **schema 1.2.0**, published as a new
  `schemas/harness-config/1.2.0.schema.json` mirror. The 1.1.0 mirror is preserved
  byte-for-byte and pinned by test. Configs at 1.1.0 stay valid and resolve identically.
* The R1-A resolver resolves `agent:<id>` sites under **two explicit, never-mixed branches**
  (an **unbound** site from its template default tier; a **bound** site from the binding's
  route, never consulting the site default tier) and reports an ordered `resolution_chain`.
  Both paths that render an agent from a template (the staged render loop for manifest
  artifacts and the in-memory render of an installed community agent) apply a binding to the
  bound agent's route variables through **one** shared composition function (the resolver's
  route, then explicit `config.overrides`), so install, tune, the render-parity check, and the
  drift check agree; unbound artifacts render byte-identically to before.
* `verify-workspace` fails closed on: an unresolved catalog or binding reference, an
  unknown site, a binding on a pipeline site, a binding on a managed site whose template
  default tier cannot be established (`ROUTING_BINDING_UNRESOLVED_SITE`), `routes`/`bindings`
  declared in a 1.1.0 config (they would be inert), an unknown key directly under
  `model_routing` in a 1.2.0
  config (for example a misspelled `routez` or the inert `subagents` block), and YAML
  anchors, aliases, or merge keys under `model_routing` in a 1.2.0 config. For a config
  declaring an older `schema_version` the last two are advisory warnings only, so no
  existing workspace turns red. The anchor/alias/merge-key rule is the single R1-A function
  that the `routing resolve` CLI also calls before loading the config, so the runtime
  resolver exits non-zero for the same 1.2.0 config that `verify-workspace` fails.
* The 1.2.0 schema closes `model_routing` itself with `additionalProperties: false` and an
  allowlist (the ten existing keys plus `routes` and `bindings`), so a 1.2.0 config with an
  unknown `model_routing` key fails schema validation with a named path. The published
  1.1.0 mirror is not touched: a 1.1.0 config with extra keys keeps validating exactly as
  today.
* For workspaces that declare bindings, `verify-workspace` fails closed when an installed,
  manifest-managed subagent (rendered from a manifest template, or installed from a
  community template) has a frontmatter route that differs from the route the renderer writes
  for it, or is **unbound** with a template default tier that cannot be established. That
  expected route is derived from the same composed variables the renderer uses (the resolved
  route plus explicit `config.overrides`, by one shared function), never from raw resolver
  output, so a correctly rendered agent using an explicit `TIER_<N>_*` override is not drift.
  For workspace-authored agents it is advisory with a migration proposal. For workspaces that
  declare no bindings it reports the drift as non-blocking `info` only. An unbound community
  agent resolves its template default tier exactly as an unbound rendered agent does; it is
  never skipped.
* `tune-harness` detects the drift and repeated route blocks and proposes a refresh or a
  catalog extraction (proposal only). Fresh installs render empty `routes`/`bindings`
  blocks at schema 1.2.0.
* P-013.5 is amended to state the catalog, sites, precedence, the anchor prohibition, and
  the resolver as the normative executable definition.
* The dogfood config's `schema_version` marker moves to `1.2.0` (marker only; no routing
  value changes) after operator confirmation.
* Every global skill that validates an operator config selects the schema by the document's
  own `schema_version` (the `resolve_contract_schema_path` rule) instead of the root schema
  file alone, which tracks only the current version: `workspace-discovery` via B4a (before
  the cut-over), `install-harness` via B8, `tune-harness` via B9, and the Orchestrator via
  R1-A A5. A valid legacy 1.1.0 config is therefore never reported invalid by an agent after
  the root const reads `1.2.0`.

## Problem Frame

See `docs/decisions/2026-10-11-model-routing-v2-deliberation.md` (decisions D1 to D5, D10,
D11). In short: the baseline's anchors, phases, and subagent names cannot be loaded, are
rejected by the schema, or name sites that do not exist; the real gaps are that subagent
routing is stale install-time frontmatter that `verify-workspace` never checks (13 installed
subagents carry routes matching neither current `tier1` nor `tier2`), that every route is a
full four-field copy, and that unknown `model_routing` keys pass the schema and are silently
inert. `model_routing` sets no `additionalProperties`, in the root schema and in the 1.1.0
mirror alike, so a misspelled `routez` or a baseline-style top-level `subagents` block
validates and is ignored. This repository's dogfood config carries no such key and no
template or test fixture renders one; it is the shape the baseline proposes and any
hand-edited workspace config can reproduce.

This release closes those gaps in one shipment on purpose. Landing the schema keys without
their verification (or the reverse) would create a window in which keys are accepted and
ignored, which is the exact defect class being removed.

Scope boundaries (P-021 C1):

* In scope: catalog, bindings, schema 1.2.0, resolver extension, verification and drift,
  install/tune surfaces, P-013.5 amendment, docs, the dogfood `schema_version` marker, and the
  version-aware config-validation wording in the global skills that read an operator config
  (B4a, B8, B9): the root schema's current-version-only const is changed by this release's
  own cut-over, so completing the consumers of that contract surface is not an expansion
  (P-021 C1; Copilot thread `PRRT_kwDORzpWpM6rlcW8`).
* Out of scope: escalation `chain` (R2), review diversity and invocation-time subagent
  directives (R3), phase sites (R4), any routing value in `.autoharness/config.yaml`,
  refreshing the 13 stale subagent frontmatters (a `tune` chore once this ships), CLI
  `--site agent:<id>` support (R3 consumes it), whether R3's invocation-time route and
  `routing resolve` should include the render-time `config.overrides` layer that this release
  keeps outside the resolver (`DEFERRED SCOPE EXPANSION` stash `EB56281C`), the stale prose in
  `escalation-protocol.instructions.md` (R2).

## Requirements Trace

| # | Requirement (040-DL decision) | Unit |
|---|---|---|
| RB1 | Tier-delta catalog resolves; names and tiers validated; no anchors; unknown `model_routing` keys rejected at 1.2.0 (D2, D10) | B1, B4, B6 |
| RB2 | Bindings resolve for registered `agent:<id>` sites; unknown site fails (D3) | B1, B2, B6 |
| RB2a | A bound subagent renders consistently with install, tune, and the render-parity check, through one shared composition function (the resolver's route, then explicit `config.overrides`); a binding on a managed site whose default tier is unresolved is rejected (D3, D4, D10; PR #513 threads `PRRT_kwDORzpWpM6rmyoO`, `PRRT_kwDORzpWpM6rmyoz`) | B6, B6a |
| RB3 | Per-field precedence as two explicit branches, unbound (template default tier) and bound (the binding's route, never the site default tier), with a reserved ordered `resolution_chain` (D4; PR #513 thread `PRRT_kwDORzpWpM6rmypP`) | B1 |
| RB4 | Schema 1.2.0 as a new mirror, with a closed `model_routing` key allowlist; 1.1.0 preserved; contract, migration, and tests (D1, D10, D11) | B3a, B3b, B4, B5 |
| RB4a | No agent-executed consumer validates an operator config against the root schema alone once the root tracks only the current version: the validation wording selects the mirror matching the document's own `schema_version` (D11; PR #513 thread `PRRT_kwDORzpWpM6rlcW8`, stash `44CB5AE1` materialized) | B4a (before B5), B8, B9 sweep (R1-A A5 for the Orchestrator) |
| RB5 | Verification: integrity, unknown site, a binding on a managed site with an unresolved default tier, inert keys at 1.1.0, unknown `model_routing` keys, alias-free through the shared R1-A guard (A2a), subagent drift whose expected frontmatter comes from the same composed variables as the renderer (D10) | B6, B7 |
| RB6 | Install and tune surfaces (D10, D11) | B8, B9 |
| RB7 | P-013.5 amendment and documentation (D10, D12) | B10, B11 |
| RB8 | Dogfood marker bump, operator-confirmed, no routing value touched (D11) | B5 |

## Planned Contract Extensions (to the R1-A resolver)

* `resolve_site(config, site, *, kind="route", installed_roles=frozenset(), sites=None)`
  where `sites: Mapping[str, SiteSpec] | None` and
  `SiteSpec(site: str, default_tier: str | None, managed: bool)`. `default_tier` is the
  `tier<N>` key whose `TIER_<N>_*` variables the agent's template renders (the mapping
  `_derive_tier_route_variables` already uses). It is derived by **one** parse of that
  template for both `managed-rendered` and `managed-community` sites (B2); it is `None` for a
  workspace-authored site, and for a managed site whose tier cannot be established (the
  reason is carried by `SiteRegistry.unresolved`, B2, so `SiteSpec` keeps exactly these
  three fields).
* Site grammar: `orchestrator`, `stage`, `ship`, or `agent:<id>` with
  `<id>` matching `^[a-z0-9][a-z0-9_-]*$`.
* New resolver errors: `ROUTING_REF_UNRESOLVED: <name>`, `ROUTING_UNKNOWN_SITE: <site>`,
  `ROUTING_CATALOG_INVALID: <name>: <reason>`,
  `ROUTING_BINDING_ON_PIPELINE_SITE: <site>`. Verify-level codes (defined by the verify units,
  not resolver codes): `ROUTING_BINDING_UNRESOLVED_SITE: <id>: <reason>` (B6 and B7) and
  `ROUTING_SITE_DEFAULT_UNRESOLVED: <id>: <reason>` (B7).
* `MODEL_ROUTING_KNOWN_KEYS: frozenset[str]`: the closed set of keys the resolver
  understands directly under `model_routing` (`tier1`, `tier2`, `tier3`, `orchestrator`,
  `stage`, `ship`, `escalation`, `anchor_review`, `alt_review`, `alt_doc_review`, `routes`,
  `bindings`). It is a constant in the pure module (no I/O). The 1.2.0 schema allowlist (B4)
  and the verify-workspace unknown-key check (B6) must agree with it, and a sync test (B6)
  fails if the constant and the schema's `model_routing.properties` diverge.
* **Precedence for `agent:<id>`: two explicit branches, chosen once by whether
  `model_routing.bindings` has an entry for the site, never mixed** (040-DL D4; PR #513
  thread `PRRT_kwDORzpWpM6rmypP`). Per field, first non-empty wins within the branch:
  * **Unbound** (no binding): `site.default_tier` is the base: that tier's field, then the
    terminal `default` for `context_tier` only. A site with no `default_tier` (a
    workspace-authored site, or a managed site whose tier is unresolved) has nothing to resolve:
    `ROUTING_UNRESOLVED: model_family`.
  * **Bound**: the binding's selected route is the base: (1) the binding's per-field
    override; (2) the binding route's catalog-delta field, then the field of the tier the
    route names (its `tier`, or for a bare-tier binding that tier); then the terminal
    `default` for `context_tier` only. **`site.default_tier` is not consulted**, not even as a
    field-level fallback, so a field the bound route leaves empty is never inherited from the
    agent's old template tier: an empty `model_provider` or `reasoning_effort` stays empty
    (the runtime default) and an unset `context_tier` is `default`. A bound site whose route
    yields no `model_family` is `ROUTING_UNRESOLVED`, not a fall-through.
  `model_family` unresolved is `ROUTING_UNRESOLVED` in both branches. The `resolution_chain`
  lists only the contributing layers of the chosen branch, in order (a bound site's chain
  never names the site default tier), so a later derived-route layer (`9B582824`) can be
  inserted without changing consumers.
* **The resolver has no `config.overrides` layer.** `config.overrides[<VAR>]` (194.006-T,
  AS-F9) is a render-time layer applied over the config-derived route-family variables,
  `TIER_<N>_*` included; it never enters `resolve_site` (R1-A states this). Anything that
  compares an installed frontmatter to a route must therefore compose that layer, which the
  next bullet centralizes.
* **One shared render/verify composition function, outside the pure module (B6a defines it,
  B7 consumes it).** `verify_workspace._compose_site_route_variables(base_variables,
  model_routing, site_id, site_registry, *, config_authoritative, overrides)` sits
  next to `_compose_artifact_variables` in `verify_workspace.py`, the module that already
  owns `_render_template`, the override layer (`_authoritative_route_variables`,
  `_context_tier_override_error`), and both render seams. `config_authoritative` has **no
  default**: every caller passes the C4b-computed authority, so the new function does not
  repeat the `config_authoritative=True` default of the older compose helpers (the residual
  stash `09DFC9F9` item 3 records; this release leaves those helpers as they are). It returns `base_variables`
  unchanged for the **unbound** branch (the base map already carries the site default tier's
  `TIER_<N>_*` with any explicit overrides), for a site that is not a registered managed site
  with a resolved default tier, for a pipeline artifact, and when the config is not
  authoritative (manifest-first, as for the role overlay). For a **bound** site it returns a
  new map in which the four `TIER_<N>_*` variables (`N` the site's default tier) carry the
  pure resolver's bound route, and each of those four names that `config.overrides` sets to
  a valid value (an invalid `*_CONTEXT_TIER` is skipped, as the existing compose paths do)
  then takes the override. Overrides are keyed to the variable names the agent's template
  renders, so only the `TIER_<N>_*` of the site's own default tier `N` apply; an override on
  another tier's variables (`TIER_<T>_*`, with `T` the bound route's tier and `T` different from
  `N`) does not reach the bound agent, exactly as it reaches no agent whose template does not
  reference those variables (rejected: re-deriving the bound route from the effective
  tier-`T` variables, which would duplicate tier derivation inside the composer). A companion
  `_expected_site_route` reads the four expected
  frontmatter values from that same composed map for a managed site (and from the resolver
  output alone for a bound workspace-authored site, which has no template and so no
  `TIER_<N>_*` variable an override could name). Both render seams (the staged loop and
  `_fc_rendered_candidate`) render the template with the composed map, and B7 reads its
  expectation through the same two functions, so the renderer and the drift check cannot
  diverge. The function cannot live in `model_routing.py` (its import allowlist excludes
  `verify_workspace`; it stays pure) or in `model_routing_sites.py` (it must not import
  `verify_workspace` at module level, B2). The registry is built once per verify run and
  passed in.
* The pure module stays pure. Building `sites` is I/O (it enumerates installed agent files,
  then joins them to the workspace manifest and templates) and lives in a separate
  `src/autoharness/model_routing_sites.py`.
* Consumed from R1-A (not defined here): `model_routing_yaml.check_model_routing_yaml(raw_text,
  schema_version) -> YamlGuardResult(errors, warnings, parse_error)` (R1-A unit A2a). B6's
  alias check delegates to it; B6 defines no scanner. Because `215-S` blocks on `214-S`, the
  function has shipped before B6 is claimed.

## Implementation Units

Execution posture: test-first for every code unit (the harness-architect generates the
expected-RED roster at Ship time); migration-first discipline for the schema bump (B3a and
B3b make the existing tests version-agnostic **before** the root schema changes, B4a makes the
one agent-executed consumer that no other unit owns, the `workspace-discovery` Phase 0
validation wording, version-aware **before** the root schema changes, and B5
then flips the root schema, the contract version, the current-mirror pairing, and the
dogfood marker in one commit). **No task boundary is deliberately red:** every unit leaves
the full suite green. Canonical test gate: `$env:PYTHONPATH='src'; python -m unittest discover -s tests`.

### B1: Resolver: tier-delta catalog and bindings

**Files (3, one is a data fixture):** `src/autoharness/model_routing.py`,
`tests/test_model_routing_catalog_bindings.py` (new),
`tests/fixtures/model_routing/catalog-bindings.json` (new).

**Change:** Extend `resolve_site` per the planned extensions: catalog name and `tier`
validation, bare-tier references, binding overrides, the two explicit precedence branches
(unbound: the site default tier; bound: the binding's route, never the site default tier),
error taxonomy, `resolution_chain`, and the `MODEL_ROUTING_KNOWN_KEYS` constant (a plain
frozenset; no logic, so the module stays pure). The resolver reads no `config.overrides`.
Vectors cover: a binding to a catalog route; a binding to a bare tier;
a binding with a field override; a route or binding that declares no `model_provider` (valid:
the runtime default; only an unresolved `model_family` is `ROUTING_UNRESOLVED`); a catalog
route named like a tier; a route with no `tier`;
an unknown reference; a binding on `agent:_stage`; `context_tier` precedence; the
baseline's six profiles expressed as deltas; and the **bound/unbound branch vectors** (PR #513
thread `PRRT_kwDORzpWpM6rmypP`), all on one config where the site's default tier (`tier2`)
supplies `model_provider`, `reasoning_effort: high`, and `context_tier: long_context` and the
bound tier (`tier1`) declares only a `model_family`:

* **unbound** `agent:x`: resolves every field from the site default tier (provider, effort,
  and `long_context` all present), the contrast case;
* **bound** `agent:x` to bare `tier1`: `model_provider` and `reasoning_effort` stay empty and
  `context_tier` is `default`, none inherited from `tier2`;
* **bound** `agent:x` to a catalog route (`tier: tier1`, only `reasoning_effort: low`):
  provider stays empty, effort is `low`, `context_tier` is `default`;
* **bound** with only a `context_tier` override: that field comes from the override and the
  others still do not fall to `tier2`;
* a generic assertion over every bound vector: no `resolution_chain` entry is sourced from the
  site default tier, and an unbound vector's chain names no binding layer;
* an `overrides` mapping present in the config passed to `resolve_site` changes no field (the
  resolver has no override layer).

**Tests (scenarios):** vectors parametrized and run through `guarded_resolve` (the R1-A A2
`forbid_io()` guard in `tests/_resolver_purity_guard.py`, so purity is enforced during every
call rather than assumed); the A1 existing-semantics vectors still pass unchanged
(regression guard); `assert_module_import_pure(model_routing)` still passes after the B1
additions (the site-grammar regex needs only the allowlisted `re`); a catalog or binding
vector cannot make the resolver touch the filesystem or environment, because `sites` is
passed in rather than discovered; `MODEL_ROUTING_KNOWN_KEYS` is a frozenset of exactly the
twelve documented keys.

**Acceptance criteria:** all catalog/bindings vectors and all A1 vectors pass under the
guard; the module still passes the static import allowlist; the `resolution_chain` for a
bound site names each contributing layer of the bound branch in order and never the site
default tier; a bound tier that leaves a field empty while the site default tier would
supply it keeps that field empty (or `default` for `context_tier`);
`MODEL_ROUTING_KNOWN_KEYS` has exactly the twelve documented members.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium` (unchanged by PR #513 cycle 5: the branch vectors are five rows in the same parametrized
fixture, no new file or module). **Depends on:** none within this plan (shipment-level: R1-A
shipped).

### B2: Site registry builder and template sync test

**Files (2):** `src/autoharness/model_routing_sites.py` (new),
`tests/test_model_routing_sites.py` (new).

**Change:** `build_site_registry(workspace_path, autoharness_home, manifest, profile=None)`
returns a frozen `SiteRegistry(sites: Mapping[str, SiteSpec], orphans: tuple[str, ...],
conflicts: tuple[str, ...], unresolved: Mapping[str, str])`. The builder is **disk-first**: it
enumerates the installed agent files first and only then joins them to the manifest. A
workspace-authored agent has no manifest provenance by definition, so a candidate set drawn
only from `manifest.artifacts[]` could never contain one and the unmanaged branch would be
unreachable.

1. **Enumerate.** Collect every `*.agent.md` under the harness's agent scan directories, in
   sorted order: `.github/agents/` (recursive, which covers `.github/agents/subagents/`)
   plus the configured local agents directory when the profile declares a global-tool
   self-install (the directories `_resolve_agent_scan_dirs` returns). Path containment is
   checked before any read: a scan root or file that resolves outside the workspace is not
   traversed or read, and symlink or reparse-point files are skipped (the rules
   `frontmatter_conformity` already applies through `_fc_enumerate_targets` and
   `_fc_resolve_contained`). Drop the pipeline agents (`_orchestrator`, `_stage`, `_ship`).
2. **Left-join to the manifest.** Look each file's normalized workspace-relative path up in
   the manifest provenance index (`_fc_build_provenance_index`, `_fc_classify`; an untracked
   path classifies as workspace-authored). A file whose class is managed (`FC_MANAGED_CLASSES`,
   three members) registers with `managed=True` and is handled by class:
   * **`managed-rendered`** (a manifest `artifacts[]` entry whose template source exists
     inside `templates/`): `default_tier` is parsed from that template, for example
     `agents/review/correctness-reviewer.agent.md.tmpl`.
   * **`managed-community`** (a manifest `community_templates[]` entry; the classifier assigns
     the class from the entry alone and does not test its template): `default_tier` is parsed
     from the entry's `template_path`, for example
     `templates/community/agents/adr-generator.agent.md.tmpl`, resolved by the rule
     `frontmatter_conformity` already applies to community candidates
     (`_fc_contained_community_source`: a relative path to an existing file inside
     `autoharness_home/templates/`; an absolute, escaping, missing, or non-file path is never
     read). A community agent is a real managed agent site: its template declares the same
     `{{TIER_<N>_*}}` placeholders as a rendered agent (the shipped `adr-generator` template
     declares `max_subagent_tier: 2` and `model_family: "{{TIER_2_FAMILY}}"`), and it is
     rendered by `_render_template` like any other.
   * **`managed-source`** (`auto-tune`, `auto-mergeinstall`; manifest label "global agent
     definition"): dropped. It has no template and no tier default, and the frontmatter
     contract forbids route-value keys on it.

   Both template-backed classes derive the tier through **one parse**, not two schemes: a
   targeted regex over the template's frontmatter block (not a full YAML parse, because
   template frontmatter can carry unquoted `{{...}}` values that are not valid YAML) for the
   `{{TIER_<N>_FAMILY}}` variable; exactly one distinct `N` gives `default_tier = "tier<N>"`.

   **Unresolved default.** When the template cannot yield exactly one tier, the site still
   registers with `managed=True, default_tier=None` and `SiteRegistry.unresolved` maps its id
   to a reason: `template-path-unusable` (a community `template_path` that fails the
   containment rule, is missing, or is not a file), `template-unreadable` (a read or decode
   error), `no-tier-placeholder` (no `{{TIER_<N>_FAMILY}}` in the frontmatter), or
   `ambiguous-tier` (more than one distinct `N`). The builder never raises, never guesses a
   tier, and never demotes the site to workspace-authored: the class comes from the manifest
   (as in `frontmatter_conformity`, where an unusable community template is `unproducible`,
   not unmanaged), and demoting would turn a fail-closed managed check into an advisory one.
   A `managed-rendered` file whose template source is missing never reaches this branch: the
   classifier already treats it as unknown-provenance, so it registers workspace-authored. An
   unresolved site is still a **known** site (it exists, so an unbound one gets the B7
   verdict), but it is **not bindable**: a binding on it is rejected up front by B6 as
   `ROUTING_BINDING_UNRESOLVED_SITE: <id>: <reason>` and again by B7, because a binding is
   applied only by overlaying the four `TIER_<N>_*` variables of a single resolved tier
   (B6a), and this site offers no such target (or no readable template at all). B2 only
   records the reason; it does not enforce the rule.

   Every other file registers as **workspace-authored**: `default_tier=None, managed=False`
   (no manifest entry, a workspace-source label, or unestablished provenance, as in
   `frontmatter_conformity`).
3. **Manifest orphans.** A manifest entry (`artifacts[]` `path`, or `community_templates[]`
   `installed_path`) that is an agent path under a scan directory but has no file on disk is
   a distinct case. It is returned in `orphans` (sorted paths), is not a site (nothing is
   installed to bind), and is not re-reported here: the artifact checksum scan already
   reports a missing managed file, and the community-template check reports it as
   `missing file`.
4. **Conflicts.** Two on-disk files that yield the same site id register neither; the id is
   listed in `conflicts`.

The site id is the file name without `.agent.md`, so the `technology-reviewer` template
installed as `python-reviewer` registers as `python-reviewer`. The builder is read-only.
`verify_workspace` imports this module, so the shared helpers are imported function-locally
or injected, never at module top level (no import cycle).

**Tests (scenarios):** every shipped subagent template and every shipped community agent
template (`templates/community/agents/*.agent.md.tmpl`, currently `adr-generator`) maps to
exactly one tier (sync test: a new template without a recognizable tier variable fails the
test, forcing an explicit decision). Fixture workspaces (temporary directories) cover each
branch of the join:

* a **managed agent**: file on disk plus a manifest entry with its template registers
  `managed=True` with the template's default tier;
* a **managed-community agent** (PR #513 thread `PRRT_kwDORzpWpM6rmKbh`): file on disk plus a
  `community_templates[]` entry (`installed_path`, `template_path` naming a fixture template
  whose frontmatter has `model_family: "{{TIER_2_FAMILY}}"`) registers `managed=True,
  default_tier="tier2"` with an empty `unresolved`; the same template bytes registered
  through an `artifacts[]` entry yield the identical `default_tier` (one parse, two sources);
* **unresolved defaults** (each registers `managed=True, default_tier=None`, stays in
  `sites`, and names its reason in `unresolved`): a community `template_path` that names a
  missing file, and one that is absolute or escapes `templates/` (both
  `template-path-unusable`; the outside file is never read, asserted at the read seam like the
  escape fixture); and, run for **both** template-backed classes, a template with no
  `{{TIER_<N>_FAMILY}}` (`no-tier-placeholder`), one referencing two distinct tiers
  (`ambiguous-tier`), and one whose read raises (`template-unreadable`);
* a **workspace-authored agent**: file on disk with **no manifest entry** registers
  `managed=False, default_tier=None` (this is the branch a manifest-derived candidate set
  could never reach);
* a **manifest orphan**: an `artifacts[]` entry, and separately a `community_templates[]`
  entry, whose file is missing is absent from `sites` and present in `orphans`;
* pipeline agents and `managed-source` agents are excluded; two files with the same site id
  land in `conflicts` and are registered as neither;
* a scan root or file that escapes the workspace (or is a symlink) is not read;
* the builder is read-only, asserted rather than claimed: a before/after snapshot of the
  fixture workspace tree (relative paths plus SHA-256 of each file's bytes) is identical
  after every call above;
* `autoharness.model_routing_sites` imports standalone (no cycle with `verify_workspace`).

**Acceptance criteria:** the registry for this workspace has `sites` containing the 13
installed subagents (managed, with their template default tiers), excludes `_orchestrator`,
`_stage`, `_ship`, `auto-tune`, and `auto-mergeinstall`, and has empty `orphans`,
`conflicts`, and `unresolved` (this workspace installs no community agent, so community
coverage is by fixture); the managed, managed-community, unresolved-default,
workspace-authored, and manifest-orphan fixtures pass.

**Size note (PR #513 cycle 4):** `M` / `medium` is unchanged. The increment is one more
template source for the same parse (a call to the existing `_fc_contained_community_source`)
plus fixtures that share one parametrized helper; still two files and one concern. PR #513
cycle 5 changes no B2 code or test: it only states who enforces the unresolved verdict (B6 and B7).

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** B1.

### B3a: Make escalation and anchor-review schema tests version-agnostic

**Files (3):** `tests/_config_schema_contract.py` (new helper),
`tests/test_escalation_hierarchy_schema.py`, `tests/test_anchor_review_routing.py`.

**Change:** The helper exposes `CURRENT_CONFIG_SCHEMA_VERSION` (read from
`SCHEMA_CONTRACTS["config"]["current_version"]`) and `current_config_mirror_path()`. Replace
hardcoded `"1.1.0"` fixture `schema_version` values and the hardcoded
`schemas/harness-config/1.1.0.schema.json` constant with the helper. Behavior and assertions
are otherwise identical. These modules (and the two in B3b) validate current-version fixtures
and the dogfood config against **both** the root schema and the current mirror, so the
contract version, the root `schema_version` const, the current-mirror file, and the dogfood
marker are read together; routing the version and mirror path through one helper is what lets
B5 flip all four in a single commit without editing these tests again.

**Tests (scenarios):** both modules pass at the current version (1.1.0) with no assertion
changes; a grep-style assertion in the helper's own test that no hardcoded config
`1.1.0` pin remains in these two modules.

**Acceptance criteria:** the two modules pass unmodified in meaning before and after; no
remaining hardcoded harness-config `1.1.0` references in them.

**Harness surface:** `harness-surface:none` (tests only). **Size/complexity:** `S` / `low`.
**Depends on:** none.

### B3b: Make context-tier schema and resolution tests version-agnostic

**Files (2):** `tests/test_context_tier_schema.py`, `tests/test_context_tier_resolution.py`.

**Change:** Same substitution as B3a using the helper. Keep the root-versus-current-mirror
lockstep assertion, now against `current_config_mirror_path()`.

**Tests (scenarios):** both modules pass at 1.1.0 unchanged in meaning; the lockstep
assertion reads the current mirror via the helper.

**Acceptance criteria:** as B3a.

**Harness surface:** `harness-surface:none`. **Size/complexity:** `S` / `low`. **Depends
on:** B3a.

### B4: Author the schema 1.2.0 mirror (unreferenced until B5)

**Files (2):** `schemas/harness-config/1.2.0.schema.json` (new),
`tests/test_harness_config_schema_1_2_0.py` (new).

**Change:** Publish the new mirror as a copy of the current root schema with `$id` set to the
1.2.0 mirror URL, `schema_version` const `1.2.0`, and these additions under `model_routing`:
`routes` (object; each value a `routeDelta`: `tier` required enum `tier1|tier2|tier3`,
optional `model_family`, `model_provider`, `reasoning_effort`, and `context_tier` via the
existing `contextTier` definition; `additionalProperties: false`; property names match
`^[a-z][a-z0-9_-]{0,47}$` and are not `tier1`, `tier2`, `tier3`, or `default`) and `bindings` (object;
`patternProperties` `^agent:[a-z0-9][a-z0-9_-]*$` to a `bindingDelta`: `route` required
string, the four optional overrides; `additionalProperties: false` at both levels).

**Closing `model_routing` itself (the one other change).** `model_routing` becomes a closed
object: it gains `additionalProperties: false` over exactly the twelve properties it declares
(the ten existing keys plus `routes` and `bindings`), so an unknown key such as `routez` or a
top-level `subagents` block fails validation with a named path instead of being silently
inert. The `not` ambiguity constraint on `model_routing` is unchanged. This tightening exists
**only** in the 1.2.0 schema (this mirror, and the root once B5 adopts it): a 1.2.0 config is
a deliberate opt-in (`schema_version` is bumped by the operator), whereas the published 1.1.0
mirror stays byte-identical, so every 1.1.0 config that validates today (extra keys included)
still validates (invariants I1, I2). Nothing else changes: the mirror is the current root
plus the additions above. **Do not edit `schemas/harness-config/1.1.0.schema.json`.**

**Why the root is not touched here.** The root `schema_version` const, the contract's
`current_version`, the current-mirror file, and the dogfood marker are read together by the
B3a/B3b modules (they validate current-version fixtures and the dogfood config against both
the root and the current mirror) and by `resolve_contract_schema_path`. Flipping the root
const in this unit while the contract and marker stay at 1.1.0 would leave those tests
deliberately red until B5. So this unit publishes the mirror without referencing it
(`known_versions` does not list 1.2.0, so nothing selects the file) and changes no existing
test's behavior; B5 adopts it atomically.

**Tests (scenarios):** empty and valid catalog/bindings validate; `routes.stage` style names
that equal a tier, a route without `tier`, an unknown binding key shape (for example
`phases.architect`), and the baseline-shaped block all fail with a named path; **an
otherwise-valid 1.2.0 config whose only defect is an unknown `model_routing` key** (`routez:
{}`) **fails with an `additionalProperties` error naming `routez`**, and so does the same
config carrying only the inert baseline-style `subagents` block; every
key the dogfood config and the rendered config template carry under `model_routing` is a member
of the allowlist (a key-set subset check, independent of the marker); the
`model_routing.properties` key set equals the twelve documented keys; a 1.1.0 document
**including one with an unknown `model_routing` key and one with a `subagents` block** still
validates against the untouched 1.1.0 mirror. All of these validate against the mirror file
directly, not the root.

**Acceptance criteria:** the schema tests pass; the full suite is green with **no existing
test changed** and `git diff` shows no change to the 1.1.0 mirror, the root
`harness-config.schema.json`, `src/autoharness/schema_contracts.py`, or
`.autoharness/config.yaml` (the mirror is unreferenced until B5).

**Harness surface:** `harness-surface:none` (JSON schema and tests; no `src/` file).
**Size/complexity:** `M` / `medium`. **Depends on:** none within this plan (B3a/B3b gate
B5, not this unit).

### B4a: Version-aware config validation wording in the workspace-discovery skill (before the cut-over)

Added in PR #513 review-fix cycle 3 for Copilot thread `PRRT_kwDORzpWpM6rlcW8`. It
materializes the work first captured as `DEFERRED SCOPE EXPANSION` stash `44CB5AE1`
(archived with a forward reference to this unit).

**Files (3):** `.github/skills/workspace-discovery/SKILL.md`,
`.autoharness/harness-manifest.yaml` (checksum),
`tests/test_workspace_discovery_config_validation_guidance.py` (new).

**Why it is in scope.** `workspace-discovery` Phase 0 item 1 validates
`.autoharness/config.yaml` against `schemas/harness-config.schema.json`, the root schema,
which pins `schema_version` to the current contract version only. After B5 the root const is
`1.2.0` and `model_routing` is a closed allowlist, so a valid legacy 1.1.0 config (every
workspace installed today) would be reported invalid by an agent following the skill. A
read-only probe confirmed the mechanism: a `{schema_version: 1.0.0}` document validates
against its own mirror and fails the root with `'1.1.0' was expected`; B5 makes the same true
of 1.1.0. `verify-workspace` is unaffected because it selects the mirror through
`resolve_contract_schema_path`; install-harness, tune-harness, and the Orchestrator wording
are rewritten by B8, B9, and R1-A A5. The regression is caused by this release's own
authorized cut-over on the same contract surface, so completing it is not a scope expansion
(P-021 C1) and it is not deferred a second time.

**Change (mechanical, no new design).** Rewrite Phase 0 item 1 only: read `schema_version`
from the document and validate against
`{autoharness_home}/schemas/harness-config/<schema_version>.schema.json` when that mirror
exists (the selection `resolve_contract_schema_path` makes); when the version is absent,
unknown to the contract, or has no mirror, validate against the current mirror and report
the version as a contract finding rather than declaring the file invalid on the root alone;
state that the root file tracks only the current version; name
`autoharness verify-workspace --workspace {workspace_path} --json` as the CLI that applies
the same selection. The skill is global and non-rendered (no template; installed-only engine
artifact), so the wording reads the version from the document at runtime and adds no
`{{...}}` placeholder. Nothing else in the skill changes: the `runtime_validation`,
`validator_manifest`, `validation_expectations`, and `releasability` tokens pinned by the
`workspace_discovery_runtime_validation_contract` check, and the frontmatter `name`, stay.

**Tests (scenarios), version-agnostic:** the version and the current mirror come only from the
B3a helper (`tests/_config_schema_contract.py`); no current-version literal, so B5 never
edits this test. (1) Phase 0 item 1 names selection by the document's own `schema_version`,
the mirror path pattern, and the verify-workspace CLI, states the root tracks only the
current version, and no longer instructs validation against the root file alone; (2) for every
mirror file in `schemas/harness-config/`, a minimal `{schema_version: <v>}` fixture resolves
through `resolve_contract_schema_path` to that mirror and validates against it; (3) every
non-current mirror version is rejected by the root schema with a `schema_version` const error
(the hazard the wording guards; true before and after B5); (4) the current-version fixture
validates against the root and the current mirror (lockstep; true before and after B5);
(5) the four runtime-validation contract tokens and the frontmatter `name` are unchanged.
Run unmodified in B5's full-suite gate, the same test covers the post-cut-over cases: a 1.1.0
config validates through the mirror selection (not the root) and a 1.2.0 config validates
against the root and the 1.2.0 mirror.

**Acceptance criteria:** the new test passes at this unit's commit and unmodified at B5's and
every later commit; Phase 0 item 1 selects the schema by the document's own `schema_version`
and the root file is no longer the sole validation target; the manifest checksum equals the
LF-normalized committed skill; `git diff` shows changes only in the three listed files.

**Harness surface:** `harness-surface:none`. **Size/complexity:** `S` / `low`
(`ah-stage-sizing-v1`: one prose edit, one checksum, one test over existing mirrors; same
shape as B9). **Depends on:** B3a (the helper). **Ordering:** B5 depends on B4a, and the
`215-S` manifest lists B4a before B5. It does not depend on B4 or B5: the wording is correct
before and after the cut-over, which is why it can land first.

### B5: Atomic 1.2.0 cut-over: root schema, contract bump, migration entry, 1.1.0 byte pin, dogfood marker

**Files (3 plus a marker pair):** `schemas/harness-config.schema.json`,
`src/autoharness/schema_contracts.py`, `tests/test_harness_config_schema_versioning.py`
(new); marker pair: `.autoharness/config.yaml` (the single `schema_version` line) and
`.autoharness/harness-manifest.yaml` (`config_hash` and affected checksums).

**Why one unit.** The root `schema_version` const, `SCHEMA_CONTRACTS["config"]["current_version"]`
(which drives the B3 helper's fixture version and `current_config_mirror_path()`), the
current-mirror file, and the dogfood marker are read together by the four B3a/B3b modules
(each validates current-version fixtures and the dogfood config against both the root and the
current mirror) and by `resolve_contract_schema_path`. Any subset flipping alone is red, so
they flip in one commit and no task boundary is deliberately red.

**Change:** Replace the root schema's content with the B4 mirror's content (identical except
`$id`), so the root const reads `1.2.0` and carries `routes`, `bindings`, and the
`model_routing` allowlist. Set `SCHEMA_CONTRACTS["config"]["current_version"]` to `1.2.0`,
add `1.2.0` to `known_versions`, extend the version-decision comment block in the established
style, and add a `known-legacy` `upgrade-config-contract-1.1.0-to-1.2.0` entry to
`CONTRACT_MIGRATIONS` (additive; action: bump `schema_version`, optionally adopt
`routes`/`bindings`, rerun verify-workspace). Add `test_legacy_1_1_0_mirror_preserved_unchanged`,
pinning the SHA-256 of the LF-normalized bytes of the 1.1.0 mirror (value computed from the
committed file at implementation time). Bump the dogfood `schema_version` to `1.2.0` and
refresh the manifest `config_hash`. If the full-suite gate shows any other test that pins the
config version or validates a current-version document against the root, make it
version-agnostic through the B3 helper in this unit as a meaning-preserving edit and record it
in the task comment; if that would exceed the file budget, stop and re-split rather than
commit a red boundary.

**Operator confirmation:** `.autoharness/config.yaml` is operator-owned. The operator
confirmed the bump on 2026-10-12 (`040-DL`, "Operator Confirmation (2026-10-12)", OQ9 yes), so
Ship cites that record at intake rather than re-asking. The edit is limited to the
`schema_version` marker (no `model_routing` value may change). Ship halts and asks the
operator only if the recorded confirmation is missing or the change would exceed the marker.

**Tests (scenarios):** the contract reports `1.2.0` current and `1.1.0` known-legacy;
`resolve_contract_schema_path` selects the 1.2.0 mirror for a 1.2.0 document and the
untouched 1.1.0 mirror for a 1.1.0 document; the 1.1.0 byte pin; the root and the 1.2.0
mirror are identical except `$id` (the lockstep check); the dogfood config (marker 1.2.0)
validates against the root and the 1.2.0 mirror; `summarize_schema_contract` marks a 1.1.0
config `known-legacy` with the new proposal; the four B3 modules pass unmodified; the B4a test
passes unmodified and now also covers the post-cut-over cases (the 1.1.0 mirror is a
non-current mirror that the root rejects and the mirror selection accepts; the 1.2.0 current
fixture validates against the root and the 1.2.0 mirror).

**Acceptance criteria:** the full suite is green in this unit's commit with no test changing
meaning; verify-workspace on this workspace reports the config contract as current with no
schema warning; the config diff is exactly one line; B4a is complete before this unit starts,
so no skill instructs validating a legacy-version operator config against the root schema
alone at the cut-over.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium` (resized from `S` / `low`: the root schema file joins the unit and atomicity raises
the integration risk; size and complexity are both re-estimated under `ah-stage-sizing-v1`).
**Depends on:** B3b, B4, B4a.

### B6: verify-workspace: catalog, binding, site, inert-key, unknown-key, and alias checks

**Files (2):** `src/autoharness/verify_workspace.py`,
`tests/test_verify_workspace_routing_catalog.py` (new).

**Change:** Add targeted checks (existence-gated: they pass silently when `routes`/`bindings`
are absent, `model_routing` has no unknown key, and the config has no anchors):

* `routing_catalog_integrity`: every catalog route is valid and every binding `route`
  resolves (uses the resolver); unknown site, pipeline-site binding, and tier-named catalog
  entries fail; and a binding on a **managed site whose template default tier is
  unresolved** (`SiteRegistry.unresolved`) fails closed as
  `ROUTING_BINDING_UNRESOLVED_SITE: <id>: <reason>` (PR #513 thread
  `PRRT_kwDORzpWpM6rmyoO`), up front at config validation, because B6a can apply a binding
  only by overlaying the four `TIER_<N>_*` variables of one resolved tier.
* `routing_inert_keys`: `routes`/`bindings` present while `schema_version` is `1.1.0` or
  older fails (`ROUTING_KEYS_REQUIRE_1_2_0`), because they would be accepted and ignored.
* `routing_unknown_keys`: any key directly under `model_routing` that is not in
  `model_routing.MODEL_ROUTING_KNOWN_KEYS` is accepted-but-inert. The severity follows the
  config's declared `schema_version`, the same gate the alias check uses (040-DL D2, D11):
  **a 1.2.0 config fails** (`ROUTING_UNKNOWN_KEY: <key>`, naming the key and the allowed
  set; the 1.2.0 schema's `additionalProperties: false` rejects the same config earlier, so
  this check is the named, schema-independent second layer); **an older config produces one
  advisory warning per key** (the same code, severity `warning`) and never changes `ok`,
  because the published 1.1.0 schema cannot be tightened (I1) and an existing workspace that
  validates today (including one carrying a baseline-style `subagents` block) must not turn
  red (I2, I4). `routes`/`bindings` are in the known set, so in an older config they are
  reported once, by `routing_inert_keys`, not twice.
* `routing_anchor_alias_free`: reads the raw text of `.autoharness/config.yaml` and calls the
  **shared R1-A function** `model_routing_yaml.check_model_routing_yaml(raw_text,
  schema_version)` (R1-A unit A2a, the same function the `routing resolve` CLI calls before
  it loads the config). An anchor, alias, or merge key anywhere under `model_routing` is an
  `error` there, reported here as a failure (`ROUTING_ANCHOR_UNSUPPORTED`), in a 1.2.0
  config, and a `warning`, reported here as an advisory, in older configs; a `parse_error` is
  reported, not raised. This unit adds **no scanner of its own**: one implementation serves
  the CLI and `verify-workspace`, so a configuration `verify-workspace` rejects cannot
  resolve successfully at runtime.

Use `model_routing_sites.build_site_registry(...).sites` as the site set. A managed agent is
a known site whatever its class, a managed-community agent and a managed site whose default
tier is unresolved included (B2), so an **unbound** site with an unresolved default is still a
known site (B7 owns that verdict). Being known is not being bindable: a **binding** on a
managed site whose default tier is unresolved fails as `ROUTING_BINDING_UNRESOLVED_SITE`
(above), and a binding on a workspace-authored agent (no template, no default tier, nothing
to overlay) is a known site and valid. A binding
whose id is in the registry's `orphans` (manifest entry, file missing) or `conflicts`
(duplicate site id) fails as `ROUTING_UNKNOWN_SITE` and the message names that cause.

**Tests (scenarios):** valid catalog and binding pass; unresolved reference, unknown site,
pipeline-site binding, tier-named route each fail with their code; a binding to a
workspace-authored agent (on disk, no manifest entry) is a known site and passes; a binding
to a managed-community agent with a **resolvable** default tier is a known site and passes;
**a binding to a managed site whose default tier is unresolved fails
`ROUTING_BINDING_UNRESOLVED_SITE: <id>: <reason>`, parametrized over the four reasons
(`template-path-unusable`, `template-unreadable`, `no-tier-placeholder`, `ambiguous-tier`)
and over both template-backed classes, including a bound site whose installed frontmatter
equals the binding's route (it must still fail), while an unbound unresolved site remains a
known site and adds no failure here;** a binding to a manifest-orphan id (manifest entry, file
missing) fails as
`ROUTING_UNKNOWN_SITE` naming the missing file; `routes` in a 1.1.0 config fails; the
baseline block (with anchors
defined) fails the alias check at 1.2.0 and warns at 1.1.0; **the alias check delegates to
the shared A2a function (patched and asserted called; a source assertion shows
`verify_workspace.py` has no `yaml.parse` or event scan of its own), a 1.2.0 config with an
alias under `model_routing` fails with `ROUTING_ANCHOR_UNSUPPORTED`, and the same config at
1.1.0 is only a warning; an otherwise-valid 1.2.0
config whose only defect is an unknown `model_routing` key (`routez`) fails
`routing_unknown_keys` with `ROUTING_UNKNOWN_KEY: routez` (run with a permissive schema so
the named check, not the schema, is what fails); the same at 1.2.0 with only an inert
`subagents` block; a 1.1.0 config carrying `subagents` or `routez` passes `ok` with one
advisory warning per key and no failure; `routes` in a 1.1.0 config is reported once (by
`routing_inert_keys`), not also by `routing_unknown_keys`; a sync test asserts
`MODEL_ROUTING_KNOWN_KEYS` equals the `model_routing.properties` key set of the current
(1.2.0) mirror;** a config with none of these keys adds only passing checks.

**Acceptance criteria:** the new checks appear in `targeted_checks` with the documented
keys; every pre-existing verify test passes unmodified; verify-workspace on this workspace
is unchanged except the new passing keys (this workspace carries no unknown key).

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** B1, B2, B5; and, across the shipment edge (`215-S` blocks on
`214-S`), the R1-A function `model_routing_yaml.check_model_routing_yaml` from A2a, which has
shipped by then (the same convention as B1's dependency on the R1-A resolver). With the event
scan moved into A2a, B6 is a thin delegating wrapper for the alias check, and its size and
complexity (`M` / `medium`) are unchanged by the addition of the unknown-key check and by the
PR #513 cycle 5 bound-unresolved rejection (one more failing branch in
`routing_catalog_integrity`, tested by one parametrized scenario over the four reasons).

### B6a: Render-time site composition for bound subagents (the shared composition function)

**Files (2):** `src/autoharness/verify_workspace.py`,
`tests/test_verify_workspace_site_composition.py` (new).

**Change:** The render loop already composes per-artifact variables for the role artifacts
(`_resolve_artifact_role` plus `_compose_artifact_variables`). Add the equivalent **site
overlay** as the single shared function `_compose_site_route_variables`, plus its companion
`_expected_site_route` (both defined under Planned Contract Extensions; this unit owns them,
and B7 consumes them). The two precedence branches are explicit:

* **Bound** (`model_routing.bindings` has an entry for `agent:<id>`; the artifact is at
  `.github/agents/**/<id>.agent.md`, site id the file stem, and its registered site is a
  managed site with a resolved default tier): overlay that artifact's four route variables
  (`TIER_<N>_FAMILY`, `TIER_<N>_PROVIDER`, `TIER_<N>_REASONING_EFFORT`,
  `TIER_<N>_CONTEXT_TIER`, with `N` the registry's `default_tier`) with the pure resolver's
  **bound** route for the site, then let each of those four names that `config.overrides`
  sets to a valid value take the override (`config.overrides` precedence mirrors the role
  overlay and `_authoritative_route_variables`). **The overlay assigns all four variables
  unconditionally, an empty string included**: skipping empty values would leave the base
  map's value, the agent's old template tier, in place and re-create at render time the
  cross-tier inheritance the bound branch forbids (D4). So a bound tier that leaves
  `model_provider` empty renders `model_provider: ""`.
* **Unbound**: the base map back unchanged. It already carries the site default tier's
  `TIER_<N>_*` with any explicit `config.overrides`, so an unbound artifact, and every
  pipeline artifact (the same "no resolved role means base map" constraint as the role
  overlay), renders byte-identically to before.

Base map back unchanged also for: an artifact with no registered site; a workspace-authored
agent (not a manifest artifact, no template render, `default_tier=None`); a managed site whose
default tier is unresolved (`SiteRegistry.unresolved`, B2: its template names no single tier
to overlay, so B6 and B7 reject a binding on it rather than let it pass unapplied); a bound
site whose binding does not resolve (resolver error: B6 reports it and B7 fails it); and a
config that is not authoritative (manifest-first, as for the role overlay).

The overlay applies at **both** seams that render an agent from a template: the staged render
loop (manifest `artifacts[]`, `managed-rendered`) and the in-memory community render in
`_fc_rendered_candidate` (`managed-community`). A community agent is not in `artifacts[]`, so
the staged loop never renders it, and without the second seam the candidate behind a
`reinstall-community` proposal would carry the tier default instead of the bound route (PR
#513 thread `PRRT_kwDORzpWpM6rmKbh`). The site registry is built once per verify run and
passed to both seams (not rebuilt per artifact). Without this unit, a bound agent could never
satisfy both the render-parity check and the B7 drift check.

**Tests (scenarios):** table-driven over one fixture helper:

1. a bound managed-rendered agent renders with the binding's four values (staged seam);
2. a bound managed-community agent's in-memory candidate render carries the binding's values
   (second seam);
3. every unbound agent, community agents included, renders byte-identically to the pre-change
   render (guards invariant I9), and pipeline agents are unchanged;
4. **`config.overrides`**: an explicit `TIER_<N>_<FIELD>` override on a bound agent wins for
   that variable while the other three come from the binding, and an override keyed to the
   bound route's own tier variables (`TIER_<T>_*`, `T` different from the agent's `N`) does not
   reach the agent; on an unbound agent the render is
   byte-identical to pre-change; an invalid `TIER_<N>_CONTEXT_TIER` override is skipped, as in
   the existing compose paths;
5. **bound/unbound branch at render**: a bound tier that leaves provider, effort, or
   `context_tier` empty while the agent's template default tier supplies them renders
   `model_provider: ""`, `reasoning_effort: ""`, `context_tier: "default"` (the overlay
   overwrites with empty), and the same agent unbound renders the default tier's values;
6. **no overlay** (base map, no exception): a managed site with an unresolved default tier, a
   non-authoritative config, and a bound site whose binding does not resolve;
7. **single-function contract**: in every fixture above, `_expected_site_route(...)` equals
   the four frontmatter values parsed back from the rendered bytes, and a source assertion
   shows both render seams and B7 call `_compose_site_route_variables` and
   `verify_workspace.py` has no other composition of a site's `TIER_<N>_*` variables;
8. **reinstall regression**: a bound resolvable community agent and a bound resolvable
   rendered agent reproduce the bound route (with and without an override) in the
   `reinstall-community` candidate and the staged render respectively; for a bound site with
   an unresolved default tier the candidate carries no binding and B6 rejects the config
   (cross-checked in B6's tests).

**Acceptance criteria:** all existing render-parity and checksum-scan tests pass unchanged;
the render of every agent in this workspace (no bindings) is byte-identical before and
after; a bound agent's render carries its binding's route values at both seams, with an
explicit override winning per variable, and a bound tier's empty field renders empty rather
than inherited; `_expected_site_route` equals the parsed rendered frontmatter in every
fixture.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`, unchanged by PR #513 cycle 5. The function is the overlay this unit already owned
(the role overlay's twin) plus a small accessor and the empty-overwrite rule; the scenario list
grows from five to eight, table-driven over one fixture helper, in the same two files and one
concern (render composition). **Depends on:** B6.

### B7: verify-workspace: installed subagent route drift

**Files (2):** `src/autoharness/verify_workspace.py`,
`tests/test_verify_workspace_subagent_route_drift.py` (new).

**Change:** Add `subagent_route_drift`. For each registry site (`build_site_registry(...).sites`,
which includes managed (rendered and community) and workspace-authored agents enumerated from
disk), compare the installed frontmatter `model_family`, `model_provider`,
`reasoning_effort`, `context_tier` to the **route the renderer writes for that site**. That
expected route is read through B6a's `_expected_site_route(...)` from
`_compose_site_route_variables(...)`, with the same inputs the two render seams pass (base
variables, `model_routing`, `config_authoritative`, `overrides`, the registry), and **never
from raw resolver output**: the resolver has no `config.overrides` layer, so a correctly
rendered agent using an explicit `TIER_<N>_*` override, bound or unbound, would otherwise be
reported as drift and fail closed (PR #513 thread `PRRT_kwDORzpWpM6rmyoz`). B7 contains no
derivation of its own, so the renderer and the drift check cannot diverge. The branches are
the same two explicit ones as D4:

* **Unbound managed agent** (rendered or community): the expectation is the site default
  tier's `TIER_<N>_*` from the composed map (the base map, overrides included). An unbound
  **managed-community** agent resolves its template default tier exactly as an unbound
  managed-rendered agent does and is compared, never skipped (PR #513 thread
  `PRRT_kwDORzpWpM6rmKbh`).
* **Bound managed agent with a resolved default tier**: the expectation is the binding's route
  with explicit overrides on top (B6a). The site default tier is not consulted.
* **Workspace-authored agent**: it has no default tier and no template, so it resolves a route
  only when it is bound, and the expectation is then the resolver's bound route (no override
  can name it, because overrides are keyed by `TIER_<N>_*` variables); drift is one advisory
  warning (provenance split reused from `frontmatter_conformity`). An unbound
  workspace-authored agent has nothing to compare and is skipped.
* **Unbound managed agent whose default tier is unresolved** (`SiteRegistry.unresolved`, B2):
  not silently skipped; it cannot resolve a route, so the verdict follows the drift opt-in
  (below) as `ROUTING_SITE_DEFAULT_UNRESOLVED: <id>: <reason>` (a verify-level code, not a
  resolver code).
* **Bound managed agent whose default tier is unresolved** (PR #513 thread
  `PRRT_kwDORzpWpM6rmyoO`): **rejected**, `ROUTING_BINDING_UNRESOLVED_SITE: <id>: <reason>`,
  whatever its installed frontmatter says. B6a cannot apply its binding (no `TIER_<N>_*`
  overlay target, or no readable template), so reinstall or community rendering could restore
  a different route; the site is therefore never compared and never passes, and it yields no
  `refresh-route-frontmatter` proposal (nothing can render it). A bound site whose binding does
  not resolve (resolver error) is likewise never compared: B7 reports the resolver's code for
  it. B6 already rejects both configs; B7 repeats the rejection so that it cannot pass a site
  the renderer cannot compose even when run on its own.

Behavior depends on whether the workspace **declares bindings** (the opt-in): with bindings, a
managed agent (manifest-rendered or community) that drifts fails closed, an unbound managed
agent whose default tier is unresolved fails closed, and a bound-and-unrenderable site fails
as above; without bindings (so no site can be bound), drift and unresolved defaults are
reported only as non-blocking `info` lines (count plus at most 20 ids). Every drift also
yields a `refresh-route-frontmatter` migration proposal. The opt-in is `bindings` non-empty,
**not** `schema_version`, so this workspace (which will be at 1.2.0 with no bindings) does not
turn red over its 13 stale subagents.

**Tests (scenarios):** one parametrized fixture builder (the B2 and B6a style). **Matrix:** class
{managed-rendered, managed-community} x {unbound, bound} x {frontmatter matches the expected
route, drifted} x {bindings declared, none declared}: a match passes and appears in the
compared set (a community agent is never skipped); drift fails closed when bindings are
declared and is `info` only otherwise (`ok` stays true). **Targeted:**

1. a bound workspace-authored agent (on disk, no manifest entry) with drift warns and does not
   change `ok`; an unbound workspace-authored agent is skipped;
2. **explicit override**: a bound agent whose frontmatter carries an explicit
   `TIER_<N>_*` override value passes; the same agent carrying the raw binding value (override
   ignored) fails closed; an **unbound** agent rendered with an override passes (no false
   drift); and a frontmatter that differs from the composed expectation while an override is
   present still fails closed;
3. **bound branch**: a bound tier that leaves provider, effort, or `context_tier` empty while
   the agent's template default tier supplies them: frontmatter with the empty values passes,
   frontmatter carrying the default tier's values fails closed;
4. **unresolved default** (community `template_path` missing, and a template with no tier
   placeholder): unbound plus bindings declared fails with `ROUTING_SITE_DEFAULT_UNRESOLVED`
   naming the reason; no bindings declared is one `info` line and `ok` stays true; **bound, it
   fails with `ROUTING_BINDING_UNRESOLVED_SITE` even when the installed frontmatter equals the
   binding's route values, and emits no refresh proposal**; a bound site whose binding does
   not resolve fails with the resolver's code and is never compared;
5. **reinstall round trip**: write the B6a render output (the staged render for a bound
   managed-rendered agent, the `reinstall-community` candidate for a bound managed-community
   agent, each with and without an override) as the installed file: B7 passes; change one
   frontmatter route field: it fails closed;
6. proposals are emitted for each drift; the opt-in predicate (`bindings` non-empty) is tested
   in both directions; `info` output is bounded (count plus at most 20 ids);
7. a non-authoritative config: the expectation is the same manifest-first base map the render
   uses (no false drift).

**Acceptance criteria:** verify-workspace on this workspace stays `ok` and reports the 13
drifted subagents as `info`; the expected frontmatter is read from the same composed variables
the renderer uses (no site-route derivation of its own); an explicit `TIER_<N>_*` override is
never reported as drift; an unbound managed-community agent is compared against its template
default tier and never skipped; an unresolved managed default is reported with its reason and
never skipped silently; a bound site can never pass while the renderer cannot apply its
binding.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`, unchanged by PR #513 cycle 5. B7 gets thinner and class-agnostic (it reads the
expectation from B6a's function instead of deriving one), and its scenarios are restated as
one parametrized matrix plus seven targeted scenarios in the same two files and one concern
(the drift verdict). **Depends on:** B6a.

### B8: Config template and install-harness surfaces

**Files (3):** `templates/harness-config.yaml.tmpl`,
`.github/skills/install-harness/SKILL.md`, `tests/test_config_template_routes_bindings.py`
(new).

**Change:** The template renders `schema_version: "1.2.0"` and, under `model_routing`, empty
`routes: {}` and `bindings: {}` blocks with a short comment (tier-delta catalog; no YAML
anchors; sites are `agent:<id>`). The install-harness validation step validates against the
schema version matching the document's own `schema_version`, and states that for an agent
with a binding the four route variables of that artifact come from the shared site
composition (B6a: the binding's route, then explicit `config.overrides`; the template default
tier is never consulted for a bound agent), that an unbound agent renders its template
default tier as before, and that a binding on a managed agent whose template default tier
cannot be established is rejected by verification (`ROUTING_BINDING_UNRESOLVED_SITE`). No new
template variables.
The install-harness skill is a global, non-rendered skill: any new route guidance must read
values from the workspace config at runtime and must not rely on install-time `{{...}}`
substitution (`docs/compound/096-S-template-vs-global-skill-placeholders.md`).
`tests/test_context_tier_tune_guidance.py` pins prose in the install and tune skills that
names `schema_version: "1.1.0"` (the context-tier requirement and the example config). Do
not edit those pinned strings; add new text beside them. If the install-harness example
config must show `1.2.0`, change the example and its pin together in this unit as a
meaning-preserving edit and record it in the task comment.

**Tests (scenarios):** the rendered default config validates against the 1.2.0 mirror;
rendering leaves no unresolved `{{...}}`; the template contains no `&`, `*alias`, or `<<:`;
`tests/test_context_tier_tune_guidance.py` passes (or its pin is updated per the change note).

**Acceptance criteria:** template render parity and variable-derivation tests pass unchanged.

**Harness surface:** `harness-surface:none`. **Size/complexity:** `S` / `low`. **Depends
on:** B5. **File budget note:** 3 files plus the pin test only if the example must change.
The `workspace-discovery` counterpart of the validation-wording change is B4a (before B5);
the end-of-shipment sweep over all three global skills is asserted in B9.

### B9: tune-harness: route drift and catalog proposals

**Files (triple + test):** `.github/skills/tune-harness/SKILL.md`,
`.autoharness/harness-manifest.yaml` (checksum), `tests/test_tune_harness_route_guidance.py`
(new).

**Change:** Add a tune step that (a) validates the loaded config against the schema version
matching its own `schema_version`; (b) reads `subagent_route_drift` and proposes a
`refresh-route-frontmatter` update per drifted agent (proposal only, never auto-applied;
workspace-authored agents advisory); a site that verify reports as
`ROUTING_BINDING_UNRESOLVED_SITE` or `ROUTING_SITE_DEFAULT_UNRESOLVED` gets no refresh
proposal, because nothing can render it: tune reports the reason and the operator's options
(repair the template's tier placeholder, or remove the binding); (c) proposes extracting a
catalog entry when three or
more route blocks are field-identical; (d) proposes the 1.1.0 to 1.2.0 `schema_version`
bump. Preserve the existing Ship-route preservation rule (this repository's
`dogfood_ship_route_pin` posture). The tune-harness skill is global and non-rendered: read
route values from the workspace config at runtime; add no install-time placeholders (the
same rule as B8).

**Tests (scenarios):** the new step markers exist; proposals are described as proposal-only;
the guidance says an unrenderable site (`ROUTING_BINDING_UNRESOLVED_SITE`,
`ROUTING_SITE_DEFAULT_UNRESOLVED`) gets no refresh proposal;
the existing tune contract tests (`test_context_tier_tune_guidance`,
`test_frontmatter_conformity_guidance`) pass unchanged; **end-of-shipment sweep (closes
invariant I11):** the config-validation instruction in each of `workspace-discovery` (B4a),
`install-harness` (B8), and `tune-harness` (this unit) selects the schema by the document's
own `schema_version`, and none names `schemas/harness-config.schema.json` as the sole
validation target (read-only file assertions; B9 is the last of the three to land).

**Acceptance criteria:** manifest checksum equals the committed skill; the sweep passes.

**Harness surface:** `harness-surface:none`. **Size/complexity:** `S` / `low`. **Depends
on:** B7, B8.

### B10: P-013.5 amendment

**Files (triple + test):** `templates/policies/workflow-policies.md.tmpl`,
`.github/policies/workflow-policies.md`, `.autoharness/harness-manifest.yaml` (checksum),
`tests/test_route_catalog_policy_contract.py` (new).

**Change:** Amend P-013.5 with a "Route catalog and site bindings" clause covering: catalog
entries are tier deltas (not a parallel taxonomy); sites and bindings; per-field precedence
stated as the two explicit subagent branches (unbound: the template default tier; bound: the
binding's route, never the site default tier as a field-level fallback), with explicit
`config.overrides` a render-time layer outside the resolver; a binding on a managed agent
whose template default tier cannot be established is rejected (`ROUTING_BINDING_UNRESOLVED_SITE`);
frontmatter is a rendered default and is drift-checked against the route the renderer writes
(the resolved route composed with explicit overrides); YAML anchors, aliases, and merge
keys are unsupported under `model_routing` (one shared raw-YAML check rejects them in a 1.2.0
config for both `verify-workspace` and the `routing resolve` CLI); unknown sites fail verification; the resolver
module and CLI are the normative executable definition; skills still inherit and are not
sites. Add the fail-closed verification items (B6/B7) to the P-013.5 verification list. Add
an Amendment Log row using the **next minor version after the latest row at claim time**
(do not hardcode a number; the queued `209-S` to `213-S` chain also appends rows). Do not
claim P-013.7 (reserved for `9B582824`).

**Tests (scenarios):** the clause markers exist in template and mirror (including the bound
and unbound branch statement and the unresolved-default rejection); the amendment row is
present; the existing P-013 policy contract tests pass unchanged.

**Acceptance criteria:** template/mirror/manifest triple consistent; Amendment Log row
version is the next in sequence.

**Harness surface:** `harness-surface:none`. **Size/complexity:** `M` / `low`. **Depends
on:** B9.

### B11: Documentation and changelog

**Files (3):** `docs/tuning-guide.md`, `CHANGELOG.md`,
`docs/design-docs/model-routing-v2.md` (status banner only).

**Change:** Document the catalog, bindings, sites, precedence (the two explicit subagent
branches: unbound from the template default tier, bound from the binding's route with no
fall-through to the template tier; explicit `TIER_<N>_*` `config.overrides` win over a bound
route, and a binding on a managed agent whose template tier cannot be established is
rejected), the opt-in drift behavior, and
the migration path in the tuning guide; add the CHANGELOG entry; add a banner to the baseline
design doc stating it is superseded as a proposal by `040-DL` and retained as the baseline.

**Tests (scenarios):** documentation conformity gates (markdown structure, cross-references)
pass.

**Acceptance criteria:** the quality gates in the constitution pass for the changed files.

**Harness surface:** `harness-surface:none`. **Size/complexity:** `S` / `trivial`. **Depends
on:** B10.

## Dependency Graph

```text
B1 -> B2
B3a -> B3b -> B5
B3a -> B4a -> B5
B4 -> B5
{B1, B2, B5} -> B6 -> B6a -> B7
B5 -> B8
{B7, B8} -> B9 -> B10 -> B11
```

No cycles. Serial by file: `model_routing.py` (B1), `verify_workspace.py` (B6, B6a, B7),
`harness-manifest.yaml` (B4a, B5, B9, B10). B4 only adds new files and is independent of B3a/B3b;
B5 is the single unit that changes the root schema, the contract version, and the dogfood
marker, so it waits for the B3 migration, the B4 mirror, and the B4a validation wording. B4a
needs only the B3a helper and is correct before and after the cut-over, so it lands before
B5. The manifest lists B4 before B5, B4a before B5, and B3b before B5.

## Decisions and Rationale

* **One release for schema, resolver, verification, and surfaces.** Accepted-but-inert keys
  are the defect class being removed, so no key lands without its enforcement.
* **Migration-first, then one atomic cut-over.** B3a/B3b remove the test coupling to the
  literal `1.1.0` before anything else changes, and B4a does the same for the one
  agent-executed consumer that no other unit owns (the `workspace-discovery` Phase 0
  validation wording). B4 then publishes the 1.2.0 mirror
  *unreferenced* (a new file nothing selects), and B5 flips the root const, the contract
  version, the current-mirror pairing, and the dogfood marker in one commit. The two
  alternatives were rejected: changing the root const in B4 and the contract in B5 leaves the
  four B3 modules (which validate current-version fixtures and the dogfood config against both
  the root and the current mirror) deliberately red between the two units; folding all of
  B4 and B5 into one unit would exceed the 2-hour rule. The recurrence history of
  schema-mirror mutation (`docs/compound/2026-08-08-*`, `2026-08-30-*`) is why the 1.1.0
  byte pin exists.
* **Version-aware validation wording is completed by this release, not deferred (B4a).** The
  root schema tracks only the current version, so a skill that validates against it alone
  reports a valid legacy config as invalid once B5 moves the const. B8, B9, and R1-A A5
  already rewrite three consumers; the fourth, `workspace-discovery`, gets its own small unit
  because B8 depends on B5 (folding it there would land the correction after the cut-over)
  and B5 is at its file budget. A prose-only hold ("deliberate before `215-S` is claimed") was
  rejected: a hold that lives only in free text is invisible to claim eligibility, the same
  failure as stash `FCC31BAB`. The fix is a backlog task with a dependency edge from B5 and
  an acceptance test, so the shipment cannot reach the cut-over without it.
* **Drift opt-in is "bindings declared".** Keying it to `schema_version` would turn this
  workspace red the moment its marker moves to 1.2.0, over drift that predates this work.
* **Catalog entries are tier deltas.** Preserves the P-013.5 invariant (a targeted override,
  never a parallel taxonomy) and P-013.2 tier-class semantics, and avoids reintroducing
  four-field copies.
* **Registry is derived from disk and classified by the manifest, in a separate I/O module.**
  Keeps the resolver pure and portable, and makes workspace-authored agents (which have no
  manifest entry) reachable.
* **One tier parse for every template-backed managed class (PR #513 thread
  `PRRT_kwDORzpWpM6rmKbh`).** `FC_MANAGED_CLASSES` has three members. `managed-rendered`
  (manifest `artifacts[]`) and `managed-community` (manifest `community_templates[]`, whose
  entry exposes `template_path`) are both agents rendered from a template with
  `{{TIER_<N>_*}}` placeholders (the shipped `adr-generator` community template declares
  `{{TIER_2_FAMILY}}`), so both derive `default_tier` from that template by the one
  regex; `managed-source` has no template and no route keys and is dropped. Deriving it only
  for `managed-rendered` registered a community agent as `managed=True, default_tier=None`, so
  an unbound one resolved no route: B7 would skip it or fail it as `ROUTING_UNRESOLVED`, and
  B6a gave it no overlay. A tier that cannot be established is surfaced with a reason
  (`SiteRegistry.unresolved`); for an unbound site it follows B7's bindings opt-in, and a
  binding on such a site is rejected (below). Rejected: guessing a tier
  (would verify the agent against the wrong route), demoting the site to workspace-authored
  (would turn a fail-closed managed check into an advisory one, and the class comes from the
  manifest, as in `frontmatter_conformity`), and skipping silently (the defect).
* **A subagent site resolves under two explicit, never-mixed branches (PR #513 thread
  `PRRT_kwDORzpWpM6rmypP`).** The earlier text listed the site default tier after the
  binding as one more per-field fallback, which contradicted 040-DL D4 (the template default
  tier applies when a subagent has no binding) and could mix tiers: a bound tier whose
  provider or `context_tier` is intentionally empty would inherit those fields from the
  agent's old template tier instead of staying the runtime default. Bound resolves from the
  binding's route only; unbound resolves from the template default tier. Rejected: keeping the
  fall-through (a bound agent would silently keep part of its previous route, and the
  resolver, the renderer, and the drift check would each need to agree on which fields leak).
* **One composition function serves the renderer and the drift check, and it lives in
  `verify_workspace.py` (PR #513 thread `PRRT_kwDORzpWpM6rmyoz`).** Comparing installed
  frontmatter with raw resolver output reports a correctly rendered agent as drift whenever
  `config.overrides` sets a `TIER_<N>_*` variable, because the renderer applies that layer and
  the resolver, by contract, has none (this also affects unbound agents). Deriving the
  expectation from the same composed variables the render seams use removes the divergence by
  construction. Placement: `model_routing.py` must stay pure (its import allowlist excludes
  `verify_workspace`), `model_routing_sites.py` must not import `verify_workspace` at module
  level, and `verify_workspace.py` already owns `_render_template`, the override layer, the
  role overlay (`_compose_artifact_variables`), and both render seams. Rejected: adding an
  override layer to the pure resolver (it would change the R1-A contract and the CLI output
  that the Orchestrator reads, and overrides are keyed by template variable names, a render
  concern); a second expectation derivation inside B7 (the divergence the finding names).
* **A binding on a managed site with an unresolved default tier is rejected, not rendered
  around (PR #513 thread `PRRT_kwDORzpWpM6rmyoO`).** A binding reaches an installed agent only
  by overlaying the four `TIER_<N>_*` variables through the plain `{{KEY}}` renderer
  (`_render_template`). The four unresolved reasons all leave no overlay target: a missing,
  escaping, or unreadable template has nothing to render, and a template with no or several
  tier placeholders has no single `N`. Letting such a bound site resolve and be compared would
  pass verification on coincidentally matching frontmatter while reinstall and community
  rendering cannot apply the binding. Rejected: a render path that needs no `TIER_<N>_*`
  (a per-site placeholder family in every agent template, or a post-render frontmatter
  rewrite), which adds a second rendering mechanism for the prose install and tune skills and a
  future port to reproduce, to serve templates that are already defective. The rule is stated
  once in D3 and enforced in B6 (config validation) and B7 (installed verdict), with B6a
  applying no overlay, so the three cannot disagree.
* **Unknown `model_routing` keys: schema allowlist at 1.2.0, advisory below.** The only place
  an allowlist can live without mutating the published 1.1.0 mirror (I1) is the new 1.2.0
  schema, and a 1.2.0 config is an operator opt-in, so failing there is safe. For older
  configs the schema cannot be tightened and an existing workspace that validates today must
  not turn red (I2, I4), so `routing_unknown_keys` warns. This is the same
  fail-at-1.2.0 / advisory-below gate 040-DL D2 sets for anchors, one rule for every
  accepted-but-inert routing key. The alternative of failing older configs was rejected: it
  would silently reclassify previously valid configs as invalid.
* **No CLI `agent:` sites yet.** Nothing consumes them until R3's invocation directives.

## Risks and Caveats

| Risk | Mitigation |
|---|---|
| A schema version bump cascades into tests and tooling | B3a/B3b first; B4 publishes an unreferenced mirror and changes no existing test; B5 flips the root const, contract version, current mirror, and dogfood marker in one commit and requires the full suite green there. |
| A task boundary left red between the root const change and the contract bump | There is none by construction: no unit changes the root const without the contract version and marker (B5 only), and B4/B6/B6a/B7 leave the suite green; B5 stops and re-splits rather than commit red. |
| A global skill still tells agents to validate an operator config against the root schema file, which carries const 1.2.0 after B5 (`workspace-discovery` Phase 0; B8, B9, and R1-A A5 already rewrite the install, tune, and Orchestrator wording) | Materialized, not deferred (PR #513 thread `PRRT_kwDORzpWpM6rlcW8`): new unit B4a (`208.014-T`, `S` / `low`) rewrites the `workspace-discovery` wording to select the mirror matching the document's own `schema_version`, B5 depends on it (backlog edge `208.006-T` -> `208.014-T`) and the `215-S` manifest lists it first, and B9 asserts an end-of-shipment sweep over all three skills (invariant I11). Stash `44CB5AE1` is archived with a forward reference. `verify-workspace` is unaffected (it selects the matching mirror). |
| In-place mutation of the 1.1.0 mirror (third-occurrence bug class) | B4 forbids editing it; B5 pins its bytes. |
| Verify turns red on this workspace | Drift opt-in is bindings-only; inert-key, unknown-key, and alias checks are existence-gated; B6/B7 acceptance includes "this workspace unchanged except new passing keys and info". |
| A 1.2.0 allowlist rejects a hand-edited config with a key it does not know (for example a `subagents` block carried over from the baseline) | Intended: the key was inert. The failure names the key and the allowed set. Configs below 1.2.0 are untouched (schema) and get a non-blocking advisory (B6); the operator chooses when to bump `schema_version`. |
| Dogfood marker bump exceeds the marker or its confirmation record is missing | Operator confirmed 2026-10-12 (`040-DL` OQ9); Ship cites the record and checks the diff is one marker line; if either fails Ship halts with the reason; no half-state. |
| Amendment Log version collision with the `209-S` to `213-S` chain | Version chosen at claim time as the next minor; shipment sequenced after `213-S`; rebase at claim. |
| Site registry diverges from templates | B2 sync test over the shipped subagent templates and the shipped community agent templates. |
| A managed-community agent is registered without a default tier, so an unbound one is skipped or fails as unresolved (PR #513 thread `PRRT_kwDORzpWpM6rmKbh`) | B2 derives the tier from the community `template_path` by the same parse as a rendered agent, with managed-community, missing and escaping `template_path`, no-placeholder, ambiguous, and unreadable fixtures; B7 compares an unbound community agent against its template default and surfaces an unresolved unbound default (fail closed with bindings, `info` without); B6a overlays both render seams (invariant I12). |
| A bound subagent mixes tiers: a field its route leaves empty is silently filled from the agent's old template tier (PR #513 thread `PRRT_kwDORzpWpM6rmypP`) | Two explicit branches (D4, Planned Contract Extensions): bound never consults `site.default_tier`; B1 vectors where the bound tier leaves provider, effort, or `context_tier` empty while the default tier would supply it, plus an unbound contrast and a no-site-default-layer assertion over every bound chain; B6a overwrites all four variables, empty included; B7 fails frontmatter that carries the default tier's values (invariant I13). |
| The renderer and the drift check disagree: an explicit `TIER_<N>_*` override reported as drift, or a bound agent on an unresolved default tier passing verify while reinstall cannot apply its binding (PR #513 threads `PRRT_kwDORzpWpM6rmyoz`, `PRRT_kwDORzpWpM6rmyoO`) | One shared composition function in `verify_workspace.py` (`_compose_site_route_variables` plus `_expected_site_route`, B6a) is called by both render seams and by B7; `ROUTING_BINDING_UNRESOLVED_SITE` rejects the binding in B6 and B7 and B6a applies no overlay; override, bound-branch, round-trip, and unresolved-bound fixtures in B6a and B7 (invariant I14). |
| `build_site_registry` misclassifies a workspace-authored agent as managed, or never sees one | Disk-first: installed agent files are enumerated, then left-joined to the manifest provenance index (the classification `frontmatter_conformity` uses); fixtures for managed, managed-community, workspace-authored (no manifest entry), and manifest-orphan agents. |
| Registry enumeration reads outside the workspace or follows a link | Containment and symlink/reparse checks before any read (same rules as `frontmatter_conformity`); an escape fixture in B2. |
| New Python surface vs the Go direction | Pure resolver with JSON vectors; registry builder is thin I/O; flagged for `039-DL`. |
| Distribution payload lists (168-S, on hold) omit the new mirror and modules | Recorded as a cross-read note for the `207-S` disposition; packaging includes `schemas/` and `src/` today. |

## Plan Hardening Signals (REQUIRED)

* Public API, schema, or contract change: **present**. New schema version, new config keys,
  new verify check keys, a P-013.5 amendment.
* Security, auth, permission, or compliance-sensitive behavior: **absent as shipped**. The
  release enables per-subagent routing but ships no routing data and changes no route; any
  cross-provider route is a later operator data decision (`040-DL` OQ1).
* Migration, backfill, destructive data/config action, or irreversible step: **present**.
  Schema version bump and an edit to the operator-owned dogfood config marker.
* External integration, operator checkpoint, or external dependency: **present**. Operator
  confirmation for the config marker (given 2026-10-12); `R1-A` must have shipped; manifest checksums.
* High runtime, rollout, or rollback risk: **present**. A fail-closed verification gate and
  a version bump touching tests, tooling, and installed workspaces.

Requires plan hardening: yes

## Runtime Verification and Closure

| Unit | Runtime surface | Verification before absorption |
|---|---|---|
| B4/B5 | schema validation, `verify-workspace` | Validate this workspace config at 1.2.0 against the new mirror and a copy at 1.1.0 against the untouched mirror; confirm the 1.1.0 mirror hash equals `origin/main`. |
| B4a | `workspace-discovery` Phase 0 | After B5, follow Phase 0 against a scratch config declaring 1.1.0 and one declaring 1.2.0: the first validates against the 1.1.0 mirror (not the root), the second against the root and the 1.2.0 mirror; neither is reported invalid. |
| B6/B7 | `verify-workspace` | Run on this workspace: all prior keys unchanged, new keys passing, 13 subagents reported as `info` drift. Run on a scratch copy with a deliberately broken binding, an anchor, an unknown `model_routing` key (`routez`), and a drifted managed subagent: each fails at 1.2.0 with its documented code; the unknown key and the anchor warn only on a scratch copy declared at 1.1.0. This workspace installs no community agent, so also run on a scratch workspace with the `adr-generator` community agent installed (manifest `community_templates[]` entry) and bindings declared for another agent: unbound with matching tier-2 frontmatter it passes and is listed as compared; with drifted frontmatter it fails closed; with its `template_path` pointing at a missing file it fails with `ROUTING_SITE_DEFAULT_UNRESOLVED` naming `template-path-unusable`; with no bindings declared the last two are `info` only. Then, on the same scratch workspace: bind `adr-generator` to `tier1`, install its `reinstall-community` candidate as the file, and confirm it passes and carries the bound route, with an explicit `config.overrides` `TIER_2_FAMILY` winning for that one variable and not reported as drift; bind a tier that leaves `model_provider` empty while the agent's tier-2 default supplies one and confirm the installed provider is empty and frontmatter carrying the tier-2 provider fails closed; point the bound agent's `template_path` at a missing file and confirm both `routing_catalog_integrity` and `subagent_route_drift` fail with `ROUTING_BINDING_UNRESOLVED_SITE` naming `template-path-unusable`, even when the installed frontmatter equals the binding's route. |
| B8 | fresh install render | Render the template for a scratch workspace; validate against 1.2.0; confirm no unresolved placeholders. |
| B9 | `tune-harness` guidance | Walk the new step against a scratch config with three identical route blocks; confirm proposals are proposal-only. |

Closure artifact: shipment closure record under `docs/closure/` with the before/after
verify-workspace comparison and the 1.1.0 hash evidence. Rollback trigger: any pre-existing
test needing a meaning change, a changed 1.1.0 mirror hash, or this workspace failing verify
for a reason other than a documented new check. Rollback: revert the shipment PR; the config
marker revert is one line plus the manifest checksum. Owner: Ship, validated by the operator
at merge. Follow-ups (not scope): `tune` refresh of the 13 subagent frontmatters; R2, R3, R4.

## Plan Hardening

**Required:** yes. Four signals are present: contract/schema, migration (version bump plus
an operator-owned file), operator checkpoint, and rollout risk across tests and installed
workspaces. Hardening recorded 2026-10-12 (UTC).

**Learnings and instructions consulted:**

* `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md` and
  `docs/compound/2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md`
  (published mirrors are immutable; seven-step repeatable fix; pin the legacy mirror).
* `docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md` (existence-gated
  verify checks so partial or legacy workspaces never see false failures).
* `docs/decisions/2026-08-07-model-routing-hierarchy-dynamic-reload-deliberation.md`
  (both-present fail-closed; migration table style; no last-known-good).
* `docs/decisions/2026-09-27-close-evidence-frontmatter-context-tier-staging-deliberation.md`
  and `037-DL` (managed versus workspace-authored provenance split; tune proposes, never
  auto-applies).
* `docs/design-docs/2026-08-20-template-dogfood-paired-edit-maintenance-contract.md`
  (manifest checksum triple).
* `.github/policies/workflow-policies.md` P-013.2, P-013.4, P-013.5, P-013.6, P-004;
  `src/autoharness/schema_contracts.py` version-decision comments.

**Protected invariants:**

* I1 the published `schemas/harness-config/1.1.0.schema.json` bytes never change.
* I2 every 1.1.0 config that validates today still validates and resolves identically.
* I3 no key is accepted by the schema without a verification path: at 1.2.0 the schema
  allowlist plus `routing_unknown_keys` close `model_routing`; for older configs
  `routing_inert_keys` (`routes`/`bindings`) and the advisory `routing_unknown_keys` cover
  what the immutable 1.1.0 schema cannot reject; B6 covers catalog, bindings, and anchors.
* I4 this workspace's `verify-workspace` stays `ok`; new checks report passing or `info`
  only.
* I5 the dogfood config diff is exactly the `schema_version` line (and the manifest
  `config_hash`); no `model_routing` value changes.
* I6 catalog entries remain tier deltas (no parallel taxonomy); P-013.2 tier class is
  preserved.
* I7 skills remain leaf executors; bindings address agents only.
* I8 no provider or model name is hardcoded in any template (Core Rule 3).
* I9 every unbound artifact, and every pipeline artifact, renders byte-identically to its
  pre-change render (B6a).
* I10 no task boundary is deliberately red: every unit leaves the full suite green. The root
  `schema_version` const, `SCHEMA_CONTRACTS["config"]["current_version"]`, the current-mirror
  file the B3 helper returns, and the dogfood marker change only together, in B5.
* I11 no consumer reports a valid legacy-version operator config as invalid because the root
  schema tracks only the current version: every skill or agent that validates an operator
  config selects the schema matching the document's own `schema_version`
  (`resolve_contract_schema_path`). Owners: R1-A A5 (Orchestrator), B4a (`workspace-discovery`,
  before B5), B8 (`install-harness`), B9 (`tune-harness`, plus the sweep that asserts all
  three skills). The one consumer that does not depend on B5 for other reasons lands before
  the cut-over; the two that do (B8, B9) land inside the same unreleased shipment, where no
  intermediate state is released and the full suite stays green (I10).
* I12 a managed agent's default tier is derived by one parse of its template's
  `{{TIER_<N>_FAMILY}}` frontmatter variable for both `managed-rendered` and
  `managed-community` sites; a managed site whose tier cannot be established is reported with
  a reason (`SiteRegistry.unresolved`; for an unbound site `ROUTING_SITE_DEFAULT_UNRESOLVED`
  under the bindings opt-in), never skipped, guessed, or demoted to workspace-authored (B2,
  B6a, B7).
* I13 a subagent site resolves under exactly one of two explicit branches, chosen once by
  whether it is bound: unbound from the template default tier, bound from the binding's route
  with `site.default_tier` never consulted as a field-level fallback (an intentionally empty
  provider or effort stays the runtime default, `context_tier` stays `default`); the branch is
  stated identically in D4, the resolver (B1), the render overlay (B6a), and the drift
  expectation (B7), and a bound chain never names the site default tier.
* I14 the expected frontmatter of any registered site is derived from the same composed
  variables the renderer uses, by one function in `verify_workspace.py`
  (`_compose_site_route_variables`, B6a), with explicit `config.overrides` applied exactly as
  the renderer applies them, so renderer and drift check cannot diverge and an explicit
  `TIER_<N>_*` override is never drift; and a binding on a managed site whose default tier is
  unresolved is rejected (`ROUTING_BINDING_UNRESOLVED_SITE`, B6 and B7), so a bound site can
  never pass B7 while B6a cannot apply its binding.

**Risky actions:**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| B4: publish the 1.2.0 mirror as a new, unreferenced file | medium (new published schema; nothing selects it until B5) | PR review; operator merge approval (P-014) | delete the new file; 1.1.0 and root untouched |
| B4a: edit one paragraph of a global engine skill plus its manifest checksum | low (prose and a checksum; no code; correct before and after the cut-over) | PR review; version-agnostic test | revert the commit |
| B5: atomic cut-over: root schema content, `current_version`, `.autoharness/config.yaml` marker and manifest | high (contract change; operator-owned file; verification semantics) | **operator confirmation recorded 2026-10-12 (`040-DL` OQ9) and cited at Ship intake**; diff must show exactly one changed config line | revert the commit (root, contract, marker, checksum together); 1.1.0 untouched |
| B6/B7: new fail-closed verify checks | medium | PR review; I4 workspace comparison; I14 (a bound site cannot pass B7 while B6a cannot apply its binding) | revert |
| B6a: render-time site composition in the render loop and the in-memory community render, and the shared composition function B7 reads | medium (shared render path; a bug changes every agent render, and the drift verdict) | PR review; I9 byte-identity of unbound renders; I13 and I14 round-trip and override fixtures | revert |
| B10: amend P-013.5 | medium (governance text) | PR review; operator merge approval | revert |
| B3a/B3b: edit four existing test modules | medium (touches pins) | PR review; meaning-preserving diff | revert |

**Added verification (tightens the plan):**

* B3a/B3b gate: after the edits, a grep over the four modules finds no harness-config `1.1.0`
  literal (a deliberate legacy-pin assertion excepted); fixture versions and the mirror path
  come only from the helper. Each module still passes at 1.1.0, unchanged in meaning.
* B4: a test asserts the `git`-tracked 1.1.0 content equals its blob on `origin/main` at
  implementation time (the byte pin in B5 is the durable form). At implementation time Ship
  also diffs the new mirror against the then-current root and confirms the only differences
  are `$id`, the `schema_version` const, `model_routing.additionalProperties`, `routes`, and
  `bindings` (a one-time check, not a committed test, because B5 makes the root equal the
  mirror).
* B4a: the test reads the version and the current mirror only through the B3a helper (no
  hardcoded current-version literal) and asserts both directions of the hazard (the selected
  mirror accepts every known version's fixture; the root rejects every non-current one), so it
  stays green before and after B5 and B5's gate re-runs it unmodified. The manifest checksum is
  computed from the LF-normalized committed blob.
* B5: before committing, run the four B3 modules and the full suite on the cut-over tree;
  all green in the same commit. The lockstep test compares root and the 1.2.0 mirror
  structurally (everything but `$id`). The SHA-256 pin is computed over LF-normalized bytes
  so a Windows autocrlf checkout does not break it. Ship records the computed value in the
  task comment. The config edit is verified with `git diff --stat` showing exactly one
  changed line in `.autoharness/config.yaml`.
* B6: the alias scan is the shared A2a function (bounded to the `model_routing` subtree,
  tolerant of a YAML parse error, detecting merge keys as well as anchors and aliases); B6
  asserts delegation rather than re-testing the scanner. The unknown-key check reads only the keys directly under `model_routing`, never
  mutates the config, and its allowlist is the single `MODEL_ROUTING_KNOWN_KEYS` constant,
  held in sync with the 1.2.0 schema by a test. A binding on a managed site with an unresolved
  default tier fails with `ROUTING_BINDING_UNRESOLVED_SITE` for each of the four reasons.
* B6a: both render seams and B7 call the single `_compose_site_route_variables`; a source
  assertion shows `verify_workspace.py` composes a site's `TIER_<N>_*` variables nowhere else,
  and the render-then-parse equivalence (`_expected_site_route` equals the frontmatter parsed
  back from the rendered bytes) holds in every fixture, overrides and empty bound fields
  included.
* B7: `info` output is bounded (count plus at most 20 ids) so a large workspace does not
  flood the report; the opt-in predicate (`bindings` non-empty) is unit-tested in both
  directions; the reinstall round trip (render output installed, B7 passes; one field
  changed, B7 fails) covers both seams.
* B8: the rendered default config is validated against the 1.2.0 mirror and against the
  unresolved-placeholder scan.
* B10: the Amendment Log version is computed from the file at claim time (next minor), and
  a test asserts the new row is the highest version present.
* Cross-release: after R1-A and R1-B ship, `autoharness routing resolve` for `stage`, `ship`,
  and `orchestrator` on this workspace must print the same tuples as before (no
  routing-value change).

**Closure and rollback detail:** monitoring signal is the closure before/after
`verify-workspace` comparison plus the 1.1.0 hash; rollback trigger is any I1 to I5
violation; rollback is a revert of the shipment PR; owner is Ship; validation window is the
PR review plus the first `tune-harness` run after merge (it should propose the 13 subagent
refreshes as proposals, never apply them).

**Operator checkpoints:** (1) before B5's config edit, Ship cites the recorded OQ9
confirmation (2026-10-12) and verifies the diff is marker-only. (2) at PR merge (P-014):
explicit approval. (3) separate from this release: whether to run the `tune` refresh of the
13 stale subagent frontmatters.

**Review-gate capability risks:** as in R1-A. This session has no reviewer subagent
dispatch and no dispatchable anchor route, so the review is
`single-agent-declared-degradation` with `TOOL_DEGRADED: model-specific-review-routing`;
the appended review must carry literal `dispatch_mode:` and `decision:` markers.

**Unresolved operator decisions that block safe execution:** none. OQ9 (the dogfood marker
bump, scoped to B5) was confirmed by the operator on 2026-10-12 and is recorded in `040-DL`
("Operator Confirmation (2026-10-12)"). OQ1 to OQ8 (`040-DL`) do not block this release
(OQ5 and OQ8 remain open and unrelated to it).

## Plan Review

Review record: `docs/reviews/2026-10-11-model-routing-catalog-bindings-plan-review.md`
(two cycles; recorded 2026-10-12 UTC).

dispatch_mode: single-agent-declared-degradation

decision: PASS

* **Gate decision:** cycle 1 failed on one P1 (B-F1: no unit made the render loop apply a
  binding to a bound subagent, so install, tune, and the render-parity check could not agree
  with the drift check). The plan was revised (new unit B6a, invariant I9, graph and trace
  updates) and re-reviewed; no P0 or P1 findings remain.
* **Plan hardening:** required (`Requires plan hardening: yes`) and satisfied
  (`## Plan Hardening`), including the operator-owned config edit in B5 and the OQ9
  checkpoint.
* **Persona coverage:** Constitution, Python, Scope Boundary, Learnings (always-on, inline
  pass); Architecture Strategist (cross-model, same-model fallback,
  `TOOL_DEGRADED: model-specific-review-routing`); Agent-Native Parity not triggered;
  Security Lens judged not triggered and noted. Every selected persona was covered under
  `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
* **Findings:** B-F1 (P1, fixed); B-F2, B-F3, B-F4 (P2, fixed); B-F5, B-F6, B-F7, B-F8 (P3,
  acknowledged).
* **Runtime verification and closure:** specified for B4/B5, B6/B7, B8, and B9; no gaps.
* **Addendum (PR #513 review-fix cycle 1, 2026-10-12 UTC):** B2 is now disk-first with a
  manifest left-join (B6, B6a, B7 text aligned; B2 resized `S` to `M`), B1 runs under the
  R1-A purity guard, and the backlog encodes the `B3b -> B4` edge. A delta check recorded in
  the review record's addendum leaves the gate decision above unchanged (earlier cycle
  records are not altered).
* **Addendum (PR #513 review-fix cycle 2, 2026-10-12 UTC):** `model_routing` is closed by an
  allowlist in the 1.2.0 schema only, with a named `routing_unknown_keys` check (fail at
  1.2.0, advisory below); B4 now only publishes the unreferenced 1.2.0 mirror and B5 is the
  single atomic cut-over (resized `S` / `low` to `M` / `medium`; the edge reads `B3b -> B5`,
  superseding the `B3b -> B4` edge above); B6's alias check delegates to the shared R1-A
  guard (`207.006-T`). A delta check recorded in the review record's addendum leaves the
  gate decision above unchanged (findings B-F11 to B-F13, all P3).
* **Addendum (PR #513 review-fix cycle 3, 2026-10-12 UTC):** the deferred `workspace-discovery`
  validation wording is materialized as new unit B4a (`208.014-T`, `S` / `low`), ordered
  before B5 with a backlog edge `208.006-T` -> `208.014-T` (and `208.014-T` -> `208.003-T`),
  listed in the `215-S` manifest between B4 and B5; B9 gains an end-of-shipment sweep;
  invariant I11 added; stash `44CB5AE1` archived. A delta check recorded in the review
  record's addendum leaves the gate decision above unchanged (finding B-F14, P3).
* **Addendum (PR #513 review-fix cycle 4, 2026-10-12 UTC; the operator authorized one cycle
  beyond the three-cycle limit):** the site registry derives `default_tier` for
  `managed-community` agents as well as `managed-rendered` ones, by one parse of the template
  tier placeholder (community agents via the manifest `template_path`); an unresolvable
  default is reported with a reason (`SiteRegistry.unresolved`) and follows B7's bindings
  opt-in; B6a overlays the in-memory community render too; invariant I12 added. No task,
  edge, size, or manifest change. A delta check recorded in the review record's addendum
  leaves the gate decision above unchanged (findings B-F17 to B-F20, all P3).
