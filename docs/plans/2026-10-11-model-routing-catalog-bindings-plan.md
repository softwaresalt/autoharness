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
* The R1-A resolver resolves `agent:<id>` sites (binding, catalog delta, tier, per-field
  precedence) and reports an ordered `resolution_chain`. The render loop applies a binding
  to the bound agent's route variables, so install, tune, and the render-parity check agree
  with the resolver; unbound artifacts render byte-identically to before.
* `verify-workspace` fails closed on: an unresolved catalog or binding reference, an
  unknown site, a binding on a pipeline site, `routes`/`bindings` declared in a 1.1.0
  config (they would be inert), an unknown key directly under `model_routing` in a 1.2.0
  config (for example a misspelled `routez` or the inert `subagents` block), and YAML
  anchors, aliases, or merge keys under `model_routing` in a 1.2.0 config. For a config
  declaring an older `schema_version` the last two are advisory warnings only, so no
  existing workspace turns red.
* The 1.2.0 schema closes `model_routing` itself with `additionalProperties: false` and an
  allowlist (the ten existing keys plus `routes` and `bindings`), so a 1.2.0 config with an
  unknown `model_routing` key fails schema validation with a named path. The published
  1.1.0 mirror is not touched: a 1.1.0 config with extra keys keeps validating exactly as
  today.
* For workspaces that declare bindings, `verify-workspace` fails closed when an installed,
  manifest-managed subagent's frontmatter route differs from its resolved route; for
  workspace-authored agents it is advisory with a migration proposal. For workspaces that
  declare no bindings it reports the drift as non-blocking `info` only.
* `tune-harness` detects the drift and repeated route blocks and proposes a refresh or a
  catalog extraction (proposal only). Fresh installs render empty `routes`/`bindings`
  blocks at schema 1.2.0.
* P-013.5 is amended to state the catalog, sites, precedence, the anchor prohibition, and
  the resolver as the normative executable definition.
* The dogfood config's `schema_version` marker moves to `1.2.0` (marker only; no routing
  value changes) after operator confirmation.

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
  install/tune surfaces, P-013.5 amendment, docs, the dogfood `schema_version` marker.
* Out of scope: escalation `chain` (R2), review diversity and invocation-time subagent
  directives (R3), phase sites (R4), any routing value in `.autoharness/config.yaml`,
  refreshing the 13 stale subagent frontmatters (a `tune` chore once this ships), CLI
  `--site agent:<id>` support (R3 consumes it), the stale prose in
  `escalation-protocol.instructions.md` (R2).

## Requirements Trace

| # | Requirement (040-DL decision) | Unit |
|---|---|---|
| RB1 | Tier-delta catalog resolves; names and tiers validated; no anchors; unknown `model_routing` keys rejected at 1.2.0 (D2, D10) | B1, B4, B6 |
| RB2 | Bindings resolve for registered `agent:<id>` sites; unknown site fails (D3) | B1, B2, B6 |
| RB2a | A bound subagent renders consistently with install, tune, and the render-parity check (D10) | B6a |
| RB3 | Per-field precedence with a reserved ordered `resolution_chain` (D4) | B1 |
| RB4 | Schema 1.2.0 as a new mirror, with a closed `model_routing` key allowlist; 1.1.0 preserved; contract, migration, and tests (D1, D10, D11) | B3a, B3b, B4, B5 |
| RB5 | Verification: integrity, unknown site, inert keys at 1.1.0, unknown `model_routing` keys, alias-free, subagent drift (D10) | B6, B7 |
| RB6 | Install and tune surfaces (D10, D11) | B8, B9 |
| RB7 | P-013.5 amendment and documentation (D10, D12) | B10, B11 |
| RB8 | Dogfood marker bump, operator-confirmed, no routing value touched (D11) | B5 |

## Planned Contract Extensions (to the R1-A resolver)

* `resolve_site(config, site, *, kind="route", installed_roles=frozenset(), sites=None)`
  where `sites: Mapping[str, SiteSpec] | None` and
  `SiteSpec(site: str, default_tier: str | None, managed: bool)`.
* Site grammar: `orchestrator`, `stage`, `ship`, or `agent:<id>` with
  `<id>` matching `^[a-z0-9][a-z0-9_-]*$`.
* New errors: `ROUTING_REF_UNRESOLVED: <name>`, `ROUTING_UNKNOWN_SITE: <site>`,
  `ROUTING_CATALOG_INVALID: <name>: <reason>`,
  `ROUTING_BINDING_ON_PIPELINE_SITE: <site>`.
* `MODEL_ROUTING_KNOWN_KEYS: frozenset[str]`: the closed set of keys the resolver
  understands directly under `model_routing` (`tier1`, `tier2`, `tier3`, `orchestrator`,
  `stage`, `ship`, `escalation`, `anchor_review`, `alt_review`, `alt_doc_review`, `routes`,
  `bindings`). It is a constant in the pure module (no I/O). The 1.2.0 schema allowlist (B4)
  and the verify-workspace unknown-key check (B6) must agree with it, and a sync test (B6)
  fails if the constant and the schema's `model_routing.properties` diverge.
* Precedence for `agent:<id>` (per field, first non-empty): binding field override; the
  binding's `route` (catalog delta then its `tier`, or the bare tier); the site's
  `default_tier`; terminal `default` for `context_tier` only. `model_family` unresolved is
  `ROUTING_UNRESOLVED`. The `resolution_chain` lists the contributing layers in order so a
  later derived-route layer (`9B582824`) can be inserted without changing consumers.
* The pure module stays pure. Building `sites` is I/O (it enumerates installed agent files,
  then joins them to the workspace manifest and templates) and lives in a separate
  `src/autoharness/model_routing_sites.py`.

## Implementation Units

Execution posture: test-first for every code unit (the harness-architect generates the
expected-RED roster at Ship time); migration-first discipline for the schema bump (B3a and
B3b make the existing tests version-agnostic **before** the root schema changes, and B5
then flips the root schema, the contract version, the current-mirror pairing, and the
dogfood marker in one commit). **No task boundary is deliberately red:** every unit leaves
the full suite green. Canonical test gate: `$env:PYTHONPATH='src'; python -m unittest discover -s tests`.

### B1: Resolver: tier-delta catalog and bindings

**Files (3, one is a data fixture):** `src/autoharness/model_routing.py`,
`tests/test_model_routing_catalog_bindings.py` (new),
`tests/fixtures/model_routing/catalog-bindings.json` (new).

**Change:** Extend `resolve_site` per the planned extensions: catalog name and `tier`
validation, bare-tier references, binding overrides, per-field precedence, error taxonomy,
`resolution_chain`, and the `MODEL_ROUTING_KNOWN_KEYS` constant (a plain frozenset; no
logic, so the module stays pure). Vectors cover: a binding to a catalog route; a binding to a bare tier;
a binding with a field override; a route or binding that declares no `model_provider` (valid:
the runtime default; only an unresolved `model_family` is `ROUTING_UNRESOLVED`); a catalog
route named like a tier; a route with no `tier`;
an unknown reference; a binding on `agent:_stage`; no binding falls to the site default
tier; `context_tier` precedence; the baseline's six profiles expressed as deltas.

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
bound site names each contributing layer in order; `MODEL_ROUTING_KNOWN_KEYS` has exactly
the twelve documented members.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** none within this plan (shipment-level: R1-A shipped).

### B2: Site registry builder and template sync test

**Files (2):** `src/autoharness/model_routing_sites.py` (new),
`tests/test_model_routing_sites.py` (new).

**Change:** `build_site_registry(workspace_path, autoharness_home, manifest, profile=None)`
returns a frozen `SiteRegistry(sites: Mapping[str, SiteSpec], orphans: tuple[str, ...],
conflicts: tuple[str, ...])`. The builder is **disk-first**: it enumerates the installed
agent files first and only then joins them to the manifest. A workspace-authored agent has no
manifest provenance by definition, so a candidate set drawn only from `manifest.artifacts[]`
could never contain one and the unmanaged branch would be unreachable.

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
   path classifies as workspace-authored). A file whose class is managed (`FC_MANAGED_CLASSES`)
   registers with `managed=True`; `default_tier` is parsed only for a `managed-rendered` file,
   from the named template's frontmatter `{{TIER_<N>_FAMILY}}` variable by a targeted regex
   over the frontmatter block (not a full YAML parse, because template frontmatter can carry
   unquoted `{{...}}` values that are not valid YAML), for example
   `agents/review/correctness-reviewer.agent.md.tmpl`. A `managed-source` file (`auto-tune`,
   `auto-mergeinstall`; manifest label "global agent definition", and the frontmatter
   contract forbids route-value keys on them) is dropped. Every other file registers as
   **workspace-authored**: `default_tier=None, managed=False` (no manifest entry, a
   workspace-source label, or unestablished provenance, as in `frontmatter_conformity`).
3. **Manifest orphans.** A manifest `artifacts[]` entry whose path is an agent path under a
   scan directory but has no file on disk is a distinct case. It is returned in `orphans`
   (sorted paths), is not a site (nothing is installed to bind), and is not re-reported here:
   the artifact checksum scan already reports the missing managed file.
4. **Conflicts.** Two on-disk files that yield the same site id register neither; the id is
   listed in `conflicts`.

The site id is the file name without `.agent.md`, so the `technology-reviewer` template
installed as `python-reviewer` registers as `python-reviewer`. The builder is read-only.
`verify_workspace` imports this module, so the shared helpers are imported function-locally
or injected, never at module top level (no import cycle).

**Tests (scenarios):** every shipped subagent template maps to a tier (sync test: a new
template without a recognizable tier variable fails the test, forcing an explicit decision).
Fixture workspaces (temporary directories) cover each branch of the join:

* a **managed agent**: file on disk plus a manifest entry with its template registers
  `managed=True` with the template's default tier;
* a **workspace-authored agent**: file on disk with **no manifest entry** registers
  `managed=False, default_tier=None` (this is the branch a manifest-derived candidate set
  could never reach);
* a **manifest orphan**: a manifest entry whose file is missing is absent from `sites` and
  present in `orphans`;
* pipeline agents and `managed-source` agents are excluded; two files with the same site id
  land in `conflicts` and are registered as neither;
* a scan root or file that escapes the workspace (or is a symlink) is not read;
* the builder is read-only, asserted rather than claimed: a before/after snapshot of the
  fixture workspace tree (relative paths plus SHA-256 of each file's bytes) is identical
  after every call above;
* `autoharness.model_routing_sites` imports standalone (no cycle with `verify_workspace`).

**Acceptance criteria:** the registry for this workspace has `sites` containing the 13
installed subagents (managed, with their template default tiers), excludes `_orchestrator`,
`_stage`, `_ship`, `auto-tune`, and `auto-mergeinstall`, and has empty `orphans` and
`conflicts`; the managed, workspace-authored, and manifest-orphan fixtures pass.

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
config `known-legacy` with the new proposal; the four B3 modules pass unmodified.

**Acceptance criteria:** the full suite is green in this unit's commit with no test changing
meaning; verify-workspace on this workspace reports the config contract as current with no
schema warning; the config diff is exactly one line.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium` (resized from `S` / `low`: the root schema file joins the unit and atomicity raises
the integration risk; size and complexity are both re-estimated under `ah-stage-sizing-v1`).
**Depends on:** B3b, B4.

### B6: verify-workspace: catalog, binding, site, inert-key, unknown-key, and alias checks

**Files (2):** `src/autoharness/verify_workspace.py`,
`tests/test_verify_workspace_routing_catalog.py` (new).

**Change:** Add targeted checks (existence-gated: they pass silently when `routes`/`bindings`
are absent, `model_routing` has no unknown key, and the config has no anchors):

* `routing_catalog_integrity`: every catalog route is valid and every binding `route`
  resolves (uses the resolver); unknown site, pipeline-site binding, and tier-named catalog
  entries fail.
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
* `routing_anchor_alias_free`: scan `.autoharness/config.yaml` with `yaml.parse` events;
  an anchor, alias, or merge key anywhere under `model_routing` fails
  (`ROUTING_ANCHOR_UNSUPPORTED`) in a 1.2.0 config and is an advisory warning in older
  configs.

Use `model_routing_sites.build_site_registry(...).sites` as the site set. A binding whose
id is in the registry's `orphans` (manifest entry, file missing) or `conflicts` (duplicate
site id) fails as `ROUTING_UNKNOWN_SITE` and the message names that cause.

**Tests (scenarios):** valid catalog and binding pass; unresolved reference, unknown site,
pipeline-site binding, tier-named route each fail with their code; a binding to a
workspace-authored agent (on disk, no manifest entry) is a known site and passes; a binding
to a manifest-orphan id (manifest entry, file missing) fails as `ROUTING_UNKNOWN_SITE` naming
the missing file; `routes` in a 1.1.0 config fails; the baseline block (with anchors
defined) fails the alias check at 1.2.0 and warns at 1.1.0; **an otherwise-valid 1.2.0
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
`medium`. **Depends on:** B1, B2, B5.

### B6a: Render-time site composition for bound subagents

**Files (2):** `src/autoharness/verify_workspace.py`,
`tests/test_verify_workspace_site_composition.py` (new).

**Change:** The render loop already composes per-artifact variables for the role artifacts
(`_resolve_artifact_role` plus `_compose_artifact_variables`). Add the equivalent **site
overlay**: for an artifact at `.github/agents/**/<id>.agent.md` whose `agent:<id>` site has a
binding, overlay that artifact's four route variables (`TIER_<N>_FAMILY`,
`TIER_<N>_PROVIDER`, `TIER_<N>_REASONING_EFFORT`, `TIER_<N>_CONTEXT_TIER`, with `N` the
site's default tier) with the resolver's output for the site, so the in-memory render of a
bound agent equals what install and tune write. An artifact with no resolved site, and every
pipeline artifact, gets the base map back unchanged (the same "no resolved role means base
map" constraint as the role overlay). `config.overrides` precedence mirrors the role
overlay. A workspace-authored agent is not a manifest artifact, has no template render, and
has `default_tier=None`, so it receives no overlay. Without this unit, a bound agent could
never satisfy both the render-parity check and the B7 drift check.

**Tests (scenarios):** a bound agent renders with the binding's values; every unbound agent
renders byte-identically to the pre-change render (guards invariant I9); `config.overrides`
precedence; pipeline agents unchanged.

**Acceptance criteria:** all existing render-parity and checksum-scan tests pass unchanged;
the render of every agent in this workspace (no bindings) is byte-identical before and
after.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** B6.

### B7: verify-workspace: installed subagent route drift

**Files (2):** `src/autoharness/verify_workspace.py`,
`tests/test_verify_workspace_subagent_route_drift.py` (new).

**Change:** Add `subagent_route_drift`. For each registry site (`build_site_registry(...).sites`,
which includes managed and workspace-authored agents enumerated from disk), compare the
installed frontmatter `model_family`, `model_provider`, `reasoning_effort`, `context_tier` to
the resolver's output. A workspace-authored agent has no default tier, so it resolves a route
only when it has a binding; an unbound workspace-authored agent has nothing to compare and is
skipped. Behavior depends on whether the workspace **declares bindings** (the
opt-in): with bindings, a managed (manifest-rendered) agent that drifts fails closed and a
(bound) workspace-authored agent produces one advisory warning (provenance split reused from
`frontmatter_conformity`); without bindings, drift is reported only as non-blocking `info`
lines (count plus ids). Every drift also yields a `refresh-route-frontmatter` migration
proposal. The opt-in is `bindings` non-empty, **not** `schema_version`, so this workspace
(which will be at 1.2.0 with no bindings) does not turn red over its 13 stale subagents.

**Tests (scenarios):** bindings declared plus managed drift fails; bindings declared plus
bound workspace-authored drift (an on-disk agent with no manifest entry) warns and does not
change `ok`; an unbound workspace-authored agent is skipped; no bindings plus drift is info
only and `ok` stays true; matching frontmatter passes; proposals are emitted.

**Acceptance criteria:** verify-workspace on this workspace stays `ok` and reports the 13
drifted subagents as `info`.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** B6a.

### B8: Config template and install-harness surfaces

**Files (3):** `templates/harness-config.yaml.tmpl`,
`.github/skills/install-harness/SKILL.md`, `tests/test_config_template_routes_bindings.py`
(new).

**Change:** The template renders `schema_version: "1.2.0"` and, under `model_routing`, empty
`routes: {}` and `bindings: {}` blocks with a short comment (tier-delta catalog; no YAML
anchors; sites are `agent:<id>`). The install-harness validation step validates against the
schema version matching the document's own `schema_version`, and states that for an agent
with a binding the four route variables of that artifact come from the resolver
(per-artifact composition, as for the role artifacts; B6a). No new template variables.
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

### B9: tune-harness: route drift and catalog proposals

**Files (triple + test):** `.github/skills/tune-harness/SKILL.md`,
`.autoharness/harness-manifest.yaml` (checksum), `tests/test_tune_harness_route_guidance.py`
(new).

**Change:** Add a tune step that (a) validates the loaded config against the schema version
matching its own `schema_version`; (b) reads `subagent_route_drift` and proposes a
`refresh-route-frontmatter` update per drifted agent (proposal only, never auto-applied;
workspace-authored agents advisory); (c) proposes extracting a catalog entry when three or
more route blocks are field-identical; (d) proposes the 1.1.0 to 1.2.0 `schema_version`
bump. Preserve the existing Ship-route preservation rule (this repository's
`dogfood_ship_route_pin` posture). The tune-harness skill is global and non-rendered: read
route values from the workspace config at runtime; add no install-time placeholders (the
same rule as B8).

**Tests (scenarios):** the new step markers exist; proposals are described as proposal-only;
the existing tune contract tests (`test_context_tier_tune_guidance`,
`test_frontmatter_conformity_guidance`) pass unchanged.

**Acceptance criteria:** manifest checksum equals the committed skill.

**Harness surface:** `harness-surface:none`. **Size/complexity:** `S` / `low`. **Depends
on:** B7, B8.

### B10: P-013.5 amendment

**Files (triple + test):** `templates/policies/workflow-policies.md.tmpl`,
`.github/policies/workflow-policies.md`, `.autoharness/harness-manifest.yaml` (checksum),
`tests/test_route_catalog_policy_contract.py` (new).

**Change:** Amend P-013.5 with a "Route catalog and site bindings" clause covering: catalog
entries are tier deltas (not a parallel taxonomy); sites and bindings; per-field precedence;
frontmatter is a rendered default and is drift-checked; YAML anchors, aliases, and merge
keys are unsupported under `model_routing`; unknown sites fail verification; the resolver
module and CLI are the normative executable definition; skills still inherit and are not
sites. Add the fail-closed verification items (B6/B7) to the P-013.5 verification list. Add
an Amendment Log row using the **next minor version after the latest row at claim time**
(do not hardcode a number; the queued `209-S` to `213-S` chain also appends rows). Do not
claim P-013.7 (reserved for `9B582824`).

**Tests (scenarios):** the clause markers exist in template and mirror; the amendment row is
present; the existing P-013 policy contract tests pass unchanged.

**Acceptance criteria:** template/mirror/manifest triple consistent; Amendment Log row
version is the next in sequence.

**Harness surface:** `harness-surface:none`. **Size/complexity:** `M` / `low`. **Depends
on:** B9.

### B11: Documentation and changelog

**Files (3):** `docs/tuning-guide.md`, `CHANGELOG.md`,
`docs/design-docs/model-routing-v2.md` (status banner only).

**Change:** Document the catalog, bindings, sites, precedence, the opt-in drift behavior, and
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
B4 -> B5
{B1, B2, B5} -> B6 -> B6a -> B7
B5 -> B8
{B7, B8} -> B9 -> B10 -> B11
```

No cycles. Serial by file: `model_routing.py` (B1), `verify_workspace.py` (B6, B6a, B7),
`harness-manifest.yaml` (B5, B9, B10). B4 only adds new files and is independent of B3a/B3b;
B5 is the single unit that changes the root schema, the contract version, and the dogfood
marker, so it waits for both the B3 migration and the B4 mirror. The manifest lists B4
before B5 and B3b before B5.

## Decisions and Rationale

* **One release for schema, resolver, verification, and surfaces.** Accepted-but-inert keys
  are the defect class being removed, so no key lands without its enforcement.
* **Migration-first, then one atomic cut-over.** B3a/B3b remove the test coupling to the
  literal `1.1.0` before anything else changes. B4 then publishes the 1.2.0 mirror
  *unreferenced* (a new file nothing selects), and B5 flips the root const, the contract
  version, the current-mirror pairing, and the dogfood marker in one commit. The two
  alternatives were rejected: changing the root const in B4 and the contract in B5 leaves the
  four B3 modules (which validate current-version fixtures and the dogfood config against both
  the root and the current mirror) deliberately red between the two units; folding all of
  B4 and B5 into one unit would exceed the 2-hour rule. The recurrence history of
  schema-mirror mutation (`docs/compound/2026-08-08-*`, `2026-08-30-*`) is why the 1.1.0
  byte pin exists.
* **Drift opt-in is "bindings declared".** Keying it to `schema_version` would turn this
  workspace red the moment its marker moves to 1.2.0, over drift that predates this work.
* **Catalog entries are tier deltas.** Preserves the P-013.5 invariant (a targeted override,
  never a parallel taxonomy) and P-013.2 tier-class semantics, and avoids reintroducing
  four-field copies.
* **Registry is derived from disk and classified by the manifest, in a separate I/O module.**
  Keeps the resolver pure and portable, and makes workspace-authored agents (which have no
  manifest entry) reachable.
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
| A global skill still tells agents to validate an operator config against the root schema file, which carries const 1.2.0 after B5 (found while checking for the red-boundary pattern: `workspace-discovery` Phase 0; B8, B9, and R1-A A5 already rewrite the install, tune, and Orchestrator wording) | Out of scope for this plan (P-021 C1: a different contract surface, no test boundary goes red). Captured as `DEFERRED SCOPE EXPANSION` stash `44CB5AE1`, which must route through `deliberate` (P-021 C6); decide before `215-S` is claimed. `verify-workspace` is unaffected (it selects the matching mirror). |
| In-place mutation of the 1.1.0 mirror (third-occurrence bug class) | B4 forbids editing it; B5 pins its bytes. |
| Verify turns red on this workspace | Drift opt-in is bindings-only; inert-key, unknown-key, and alias checks are existence-gated; B6/B7 acceptance includes "this workspace unchanged except new passing keys and info". |
| A 1.2.0 allowlist rejects a hand-edited config with a key it does not know (for example a `subagents` block carried over from the baseline) | Intended: the key was inert. The failure names the key and the allowed set. Configs below 1.2.0 are untouched (schema) and get a non-blocking advisory (B6); the operator chooses when to bump `schema_version`. |
| Dogfood marker bump exceeds the marker or its confirmation record is missing | Operator confirmed 2026-10-12 (`040-DL` OQ9); Ship cites the record and checks the diff is one marker line; if either fails Ship halts with the reason; no half-state. |
| Amendment Log version collision with the `209-S` to `213-S` chain | Version chosen at claim time as the next minor; shipment sequenced after `213-S`; rebase at claim. |
| Site registry diverges from templates | B2 sync test. |
| `build_site_registry` misclassifies a workspace-authored agent as managed, or never sees one | Disk-first: installed agent files are enumerated, then left-joined to the manifest provenance index (the classification `frontmatter_conformity` uses); fixtures for managed, workspace-authored (no manifest entry), and manifest-orphan agents. |
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
| B6/B7 | `verify-workspace` | Run on this workspace: all prior keys unchanged, new keys passing, 13 subagents reported as `info` drift. Run on a scratch copy with a deliberately broken binding, an anchor, an unknown `model_routing` key (`routez`), and a drifted managed subagent: each fails at 1.2.0 with its documented code; the unknown key and the anchor warn only on a scratch copy declared at 1.1.0. |
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

**Risky actions:**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| B4: publish the 1.2.0 mirror as a new, unreferenced file | medium (new published schema; nothing selects it until B5) | PR review; operator merge approval (P-014) | delete the new file; 1.1.0 and root untouched |
| B5: atomic cut-over: root schema content, `current_version`, `.autoharness/config.yaml` marker and manifest | high (contract change; operator-owned file; verification semantics) | **operator confirmation recorded 2026-10-12 (`040-DL` OQ9) and cited at Ship intake**; diff must show exactly one changed config line | revert the commit (root, contract, marker, checksum together); 1.1.0 untouched |
| B6/B7: new fail-closed verify checks | medium | PR review; I4 workspace comparison | revert |
| B6a: render-time site composition in the render loop | medium (shared render path; a bug changes every agent render) | PR review; I9 byte-identity of unbound renders | revert |
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
* B5: before committing, run the four B3 modules and the full suite on the cut-over tree;
  all green in the same commit. The lockstep test compares root and the 1.2.0 mirror
  structurally (everything but `$id`). The SHA-256 pin is computed over LF-normalized bytes
  so a Windows autocrlf checkout does not break it. Ship records the computed value in the
  task comment. The config edit is verified with `git diff --stat` showing exactly one
  changed line in `.autoharness/config.yaml`.
* B6: the alias scan is bounded to the `model_routing` subtree, tolerates a YAML parse
  error (reported, not raised), and detects merge keys (`<<`) as well as anchors and
  aliases. The unknown-key check reads only the keys directly under `model_routing`, never
  mutates the config, and its allowlist is the single `MODEL_ROUTING_KNOWN_KEYS` constant,
  held in sync with the 1.2.0 schema by a test.
* B7: `info` output is bounded (count plus at most 20 ids) so a large workspace does not
  flood the report; the opt-in predicate (`bindings` non-empty) is unit-tested in both
  directions.
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
