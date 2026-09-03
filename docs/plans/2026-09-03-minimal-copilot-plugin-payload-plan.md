---
title: "SHIP-10 — Minimal Copilot plugin installation payload"
date: 2026-09-03
slug: minimal-copilot-plugin-payload
doc_type: plan
source_stash: "E9E5E6CC"
source_decision: "docs/decisions/2026-09-03-minimal-copilot-plugin-payload-deliberation.md"
shipment_unit: "SHIP-10"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
---

# SHIP-10 — Minimal Copilot plugin installation payload

> **Canonical current execution contract.** This document states the contract
> that is in force now. It carries no cycle narratives, no historical
> verification tables, and no superseded clauses. Every subject is stated
> exactly once. Review-cycle history and per-cycle dispositions live in
> [`docs/reviews/2026-09-03-minimal-copilot-plugin-payload-plan-review-history.md`](../reviews/2026-09-03-minimal-copilot-plugin-payload-plan-review-history.md).
> Session memory files under `docs/memory/` remain pointers only; raw
> transcripts are not duplicated here or in the review history.

## Problem

`autoharness` ships two installation channels whose payload boundaries are
undeclared, unverified, and demonstrably wrong.

Measured at the current tip:

| Measurement | Value |
|---|---|
| Files reachable from the plugin's `source: "."` declaration | 3,238 tracked files (~18 MB) |
| Of those, `.backlogit/` development backlog | 2,110 files (65% of the payload) |
| `docs/` files force-included into the wheel | 642 files (~6.9 MB) |
| `docs/` files that are actually root guides | 21 tracked files |
| Runtime paths omitted from the wheel | `.github/policies/**` and the skill-referenced `scripts/` subset |

Consequences: the plugin channel publishes the entire development repository,
the wheel channel publishes ~6.9 MB of non-runtime documentation while omitting
files its own skills reference at runtime, and neither channel has a machine
gate that would catch a regression. There is no single declaration of what
belongs in a payload, so every build path re-derives the answer differently.

## Goal

Introduce one declarative payload manifest that is the sole source of truth for
both channels, enforce it with fail-closed gates in CI and in the release
workflow, and make the plugin payload minimal — carrying only what the Copilot
plugin channel actually resolves at runtime.

## Non-goals

* No change to product behaviour of the CLI, skills, instructions, or templates.
* No new install channel, engine, schema framework, or dependency beyond the
  pinned test toolchain required to execute the harness.
* No sdist channel work (deferred, see **Deferred scope**).
* No real offline end-to-end installed-upgrade execution (deferred, see
  **Deferred scope**).
* No repository-wide refactor of `build_support/**` beyond the paths this plan
  names.

## Channel scope

Exactly two channels are in scope: `wheel` and `plugin`.

| Channel | Materialization | `install_root` |
|---|---|---|
| `wheel` | Python distribution built by the project's build backend | `src/autoharness/data/` |
| `plugin` | Per the T1 spike outcome — branch (a) native trimming with no materialized tree, or branch (b) a tracked `plugin-payload/` tree with `marketplace.json` `source` repointed to it | `""` (payload root) |

Under branch (b), `plugin-payload/**` is the **materialization output root**: a
tracked, committed directory the generator writes into, so it resolves in every
consumer checkout. A gitignored `dist/plugin/`-style output path is prohibited,
because a consumer could never fetch it.

`plugin-payload/**` is never an `install_root` prefix, never a manifest source
path, and never a classifier input. Treating it as an install root prefixes
every plugin `dest` with the very directory the generator then writes beneath —
that is what produces recursive nesting. The classifier therefore removes
generated output roots from its input set **before** any pattern matching
occurs.

## Affected surfaces

| Surface | Nature of change |
|---|---|
| `.autoharness/payload-manifest.yaml` (new) | Declarative manifest — sole source of payload paths |
| `schemas/payload-manifest.schema.json` + `schemas/payload-manifest/1.0.0.schema.json` | Manifest schema, live and versioned |
| `build_support/**` | Classifier, resolver, generator, size reporter |
| `tests/**` | 47-case harness (see ledger) |
| `pyproject.toml` | Build tables (T7); `[dependency-groups]` test dependency (T0) |
| `uv.lock` | Pinned test toolchain (T0) |
| `.github/workflows/ci.yml` | Test invocation and toolchain preflight (T0) |
| `.github/workflows/release.yml` | Two release gates (T14) |
| `.github/plugin/marketplace.json` | Plugin channel declaration, generated (T8) |
| `plugin-payload/**` | Plugin materialization output, branch (b) only (T8) |
| `tests/fixtures/payload-baseline/**` | Baseline inventories and digests (T2a) |
| `docs/**` | Plan, review history, guides (T15) |

## Acceptance criteria

### AC1 — Declarative payload manifest is the sole source of payload paths

A single tracked manifest, `.autoharness/payload-manifest.yaml`, declares per
channel the complete set of payload paths. No build path, workflow step, or
script may derive a payload path by any other means. The manifest validates
against the live schema `schemas/payload-manifest.schema.json`, which has an
immutable versioned mirror `schemas/payload-manifest/1.0.0.schema.json` — the
two-file convention every other versioned schema in this repository follows. A
live schema with no versioned mirror is a conformance failure. The pair must
agree, and the manifest contract is registered in `schema_contracts.py`.

The manifest classifies itself: `.autoharness/payload-manifest.yaml` is covered
by the `.autoharness/**` exclude but is also classified explicitly by name, so
its own exclusion is intentional rather than incidental.

### AC1a — Rule shape, install roots, destination injectivity

Each manifest rule is an object with exactly two fields:

```yaml
{ src: "<repo-relative source path or glob>", dest: "<path relative to the channel install root>" }
```

* **Identity shorthand.** A bare string rule is sugar for `{src: X, dest: X}`.
  Most rules are identity mappings and must not restate the path twice.
* **Per-channel install root.** `wheel.install_root` is the installed package
  data root `src/autoharness/data/`. `plugin.install_root` is the empty string
  `""` — the payload root itself. `plugin-payload/**` is the branch-(b)
  materialization *output* root the generator writes into; it is **never** an
  install-root prefix baked into a `dest`.
* A `dest` that escapes its install root (absolute, or containing `..`) is a
  schema error. With `install_root: ""` the plugin's `dest` values are
  payload-root-relative and the escape check applies unchanged.
* A glob `src` paired with a file `dest` is a schema error, not a silently
  flattened many-to-one write. A glob `src` may pair only with a directory
  `dest`, or use the identity shorthand.
* **Destination injectivity.** Within a channel, no two rules may resolve to the
  same destination path. A collision fails the build.

### AC1b — Package declarations are classified, not implicit

`packages = ["src/autoharness"]` is declared through
`channel_package_declarations` and asserted verbatim against `pyproject.toml`.
An implicit or drifted package declaration fails the gate.

### AC2 — Unclassified tracked paths fail the build

Every tracked path that reaches the classifier must match at least one candidate
rule. Zero candidates is a hard failure naming the path. There is no default
bucket, no silent drop, and no warn-only mode.

### AC2b — Two release gates

The release workflow carries exactly two payload gates.

**Gate A (pre-build, source/static).** Runs before any distribution is built:

* manifest schema validation;
* AC11 classification completeness over all tracked paths;
* the AC2 unclassified-path guard;
* the resolver payload size report;
* the **AC2d P1–P4 derivation predicate** (a static derivation check — it
  asserts nothing about occurrence counts);
* structural assertions over `release.yml` itself.

**Gate B (post-build, pre-publish).** Runs after the distribution is built and
before publication:

* unpacks the built wheel;
* asserts AC3, AC4, AC8, AC9 against the unpacked artifact;
* records the SHA-256 of each `dist/*` member;
* sets `AUTOHARNESS_PAYLOAD_WHEEL` for downstream steps.

Neither gate may carry `continue-on-error` or an `if:` condition. Between
Gate B and publication there must be a structural no-`dist/`-write window: no
step in that span may create, modify, or remove anything under `dist/`.

### AC2b-CI — Test toolchain

The canonical, authoritative test invocation is:

```text
uv run python -m pytest
```

`uv` is installed through a pinned action reference:

```text
astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
```

Skip and xfail are prohibited in every form — decorator, marker, keyword
argument, runtime call, and configuration. A skipped or xfailed case is a gate
failure, not a pass.

### AC2c — Exactly one generation path

Generation is performed only by:

```text
python -m build_support.payload generate --channel {wheel|plugin|all}
```

with a `--check` mode that verifies committed output matches regenerated output.
Single-path-ness is enforced by four decidable predicates:

1. the generator's definition site is unique under AST analysis;
2. no consumer imports a private generation symbol;
3. no CI or workflow step re-derives generation inline;
4. no second build path exists that can emit payload output.

### AC2c-R — Deterministic rendering

The generator emits two kinds of artifact from the manifest: the wheel build
tables inside `pyproject.toml` (TOML) and the plugin channel declaration in
`.github/plugin/marketplace.json` (JSON). The manifest itself is authored YAML and is an input
to the generator, never its output.

* Generated TOML is emitted by a narrow line renderer. `tomli-w`, `tomlkit`,
  and `ruamel` are prohibited.
* Generated JSON is emitted with
  `json.dumps(indent=2, sort_keys=True, ensure_ascii=False, separators=(",", ": "))`.
* Encoding is UTF-8 without BOM, LF line endings only, forward slashes in all
  path text.
* `--check` compares canonical bytes in binary mode.
* Every rendered artifact is round-trip verified: render → parse → re-render
  must be byte-identical.

### AC2d — Target-workspace prefix derivation is centralized

Four predicates define centralization:

* **P1** — the declaration of `classify_target_workspace_path` is unique under
  AST analysis across `build_support/**`.
* **P2** — every call site routes through `classify_target_workspace_path`.
* **P3** — no fixture ingestion path bypasses the classifier.
* **P4** — a frozen, symbol-keyed allow-list of exceptions that may not
  increase, containing exactly two `verify_workspace.py` literals.

**Occurrence semantics are withdrawn.** The tip measures 57 occurrences of the
prefix literal across 23 files; an "exactly one occurrence" criterion is
unsatisfiable and is not part of this contract. Gate A asserts the P1–P4
derivation predicate only.

### AC3 — Development surfaces are excluded from every payload

No payload may contain `.backlogit/`, `.worktrees/`, development-only
directories, or scratch. Exclusion is asserted against the built artifact, not
against the source tree.

### AC3c — Plugin source paths are tracked and fetchable

Every path the plugin channel declares must be tracked in git and fetchable from
the published reference. An untracked or unreachable source path fails the gate.

### AC3d — Generated output roots

```text
generated_output_roots = [
  "plugin-payload/**",
  "dist/.autoharness-scratch/**",
]
```

Generated output roots are removed from the classifier input set **before**
matching. They carry **no** include rule and **no** exclude rule — a redundant
channel exclusion rule for a generated root is itself a defect, because it
implies the root reached the matcher.

### AC3e — Single scratch root and the eight-class write partition

**Scratch root.** There is exactly **ONE** scratch root:

```text
dist/.autoharness-scratch/<run-id>/
```

* `<run-id>` is a UUID4 hex string, unique per run.
* Containment is validated canonically: the resolved scratch path must be a
  strict descendant of the resolved workspace root. Validation failure is
  fail-closed.
* The root is **never** taken from `TMPDIR`, `TEMP`, `TMP`, or any OS temporary
  directory API. `tempfile.TemporaryDirectory()` and the pytest `tmp_path` /
  `tmp_path_factory` fixtures are prohibited for any generated, test, or
  upgrade scratch — both resolve under the OS temporary root, outside the
  repository working tree, where this repository cannot constrain, inspect, or
  exclude what was written. They are rejected for **containment**, not because
  pytest is unavailable: pytest is this repository's declared runner (AC2b-CI).
* It is gitignored by the existing `dist/.gitignore` (`*`).
* It is excluded from classifier input and from payload input before matching.
* It is **never automatically deleted**. Cleanup is a separate operation that
  requires destructive approval.
* `.worktrees/**` is Exclude-only. It is never a scratch root.

**Write partition — eight classes.** Every write is classified into exactly one
of eight labels:

| # | Label | Target | Approval |
|---|---|---|---|
| 1 | `EPHEMERAL_CREATE` | scratch root | none |
| 2 | `EPHEMERAL_NOOP` | scratch root | none |
| 3 | `EPHEMERAL_OVERWRITE` | scratch root | none |
| 4 | `EPHEMERAL_REMOVE` | scratch root | none |
| 5 | `CREATE` | repository, path untracked | none |
| 6 | `NO-OP` | repository, path tracked, bytes identical | none |
| 7 | `OVERWRITE` | repository, path tracked, bytes differ | **required** |
| 8 | `REMOVE` | repository, path tracked | **required** |

The approval set is exactly `OVERWRITE ∪ REMOVE`. It is never branch-keyed,
never channel-keyed, and never derived from the target directory alone.

Tracked-ness is determined by `git ls-files --error-unmatch -- <path>` **in the
tree under test**, never "at a commit".

### AC4 — Runtime completeness

The wheel must contain the complete runtime set, including `.github/policies/**`
and the skill-referenced `scripts/` subset. `docs/` inclusion is limited to root
guides only.

### AC5 — Install emits only generated output

Installation into a target workspace emits only generated output. No engine
records, no payload-internal bookkeeping, and no development artefacts appear in
the target workspace. Skill and docs references resolve to the workspace, not
into the payload.

### AC6 — Upgrade and parity

Trimmed-payload workspace state must match the baseline inventory for the
equivalent operation; upgrade from the prior release must leave no orphaned
files; `--home` and `--version` behave identically across channels.

### AC6a — Python channel resolution

Data directory resolution is asserted for both `pip install` and clone/editable
layouts. The Python channel requires **no** plugin-root artifact (assertion A1).

### AC6b — Plugin channel resolution

The plugin root resolves templates and schemas; version resolves from the plugin
manifest. The plugin channel imports **no** Python package (assertion B1) and
carries **no** Python distribution (assertion B2). The two channel resolver
contracts are disjoint.

### AC7 — Register phase

The register phase succeeds for the Python channel across all environments. A
plugin-only register against the Copilot CLI succeeds. Unsupported targets fail
in exactly the same way as the baseline. The plugin channel excludes the Python
CLI by design.

### AC8 — Payload size is reported

The resolver reports payload size per channel. The report is emitted by Gate A
and is a durable output.

### AC9 — Cross-reference integrity

Gate-4 cross-references remain intact in the built payload: every referenced
file exists at its referenced path within the artifact.

### AC10 — Version resolution without the CLI

Version resolves on plugin install without the Python CLI present. The version
token is written by the generator; in headings and ordinary prose this document
refers to it symbolically as AUTOHARNESS_VERSION, and the literal brace form
appears only inside intentional fenced fixture examples.

### AC11 — Classification selection is deterministic

Selection proceeds in this exact order:

1. **Remove generated output roots** from the input set (AC3d). This happens
   before any matching.
2. **Build the candidate set** — all rules whose pattern matches the path.
3. **Zero candidates fails** (AC2), naming the path.
4. **Select the most specific candidate**, by this deterministic ordering over
   pattern text alone:
   * an exact literal beats any wildcard pattern;
   * a longer literal prefix beats a shorter one;
   * fewer wildcard segments beats more.
5. **Equal specificity fails closed**, naming both patterns.

There is no "exactly one raw match" property and no "no precedence needed"
property. Multiple candidate matches are expected and are resolved by the rule
above; any statement to the contrary is false and is not part of this contract.

## Test strategy

### Class contract

Every case declares exactly one class:

* **RED-FIRST (`R`)** — the case must be authored and observed failing before
  the implementation that satisfies it exists. The red observation's commit must
  precede the red observation record; the green implementation commit must
  precede the green observation record.
* **CHARACTERIZATION (`C`)** — the case pins existing behaviour that must not
  change. It is authored against the current tree and observed passing.

A case may not change class. The class is declared in the ledger and re-declared
in each observation record; a mismatch is a T16 failure.

### Machine enforcement

* Author-before-owner ordering is machine-checked over the dependency DAG: for
  every RED-FIRST case, the authoring task must precede every owning task.
  There are **34** such ordering paths. Case 47 adds none: its author and its
  owner are the same task, and a task cannot need to precede itself.
* Case names are unique across the ledger.
* Every ledger case must be collectable by `uv run python -m pytest --collect-only`.
* Every owner edge must join to a live task ID.

### Runner contract — both governing documents, no policy change

Every case this shipment authors is written as a `unittest.TestCase` method, so
**both** runners collect it. That single authoring convention satisfies two
documents that name different commands, without amending either:

* **P-004** (`.github/policies/workflow-policies.md`) states its red-phase
  precondition literally as `PYTHONPATH=src python -m unittest discover -s tests`
  exiting non-zero. Red evidence taken before the toolchain lands uses that exact
  command.
* **The Constitution** names `pytest`. T0 declares and locks a pinned `pytest`
  and moves CI's authoritative gate to `uv run python -m pytest`, which collects
  unittest-compatible cases unchanged.

Two commands run, at two different levels, and neither displaces the other:

* **P-004's gate confirmation is always the literal unittest command.** P-004's
  precondition is whole-suite and gate-scoped — `PYTHONPATH=src python -m unittest
  discover -s tests` must exit non-zero with expected failure markers before the
  `harness-ready` label. That confirmation is taken with that exact command at
  **every** red-phase gate in this shipment, before and after T0. It costs
  nothing to honour: `unittest` is stdlib, so the command needs no lock, no
  dependency group and no network, and every case here is a `unittest.TestCase`
  method, so `discover` sees all of them. This plan does not amend, narrow or
  reinterpret that precondition.
* **Per-case observation records use the canonical runner once it is locked.**
  `uv run python -m pytest` is the authoritative invocation for the recorded
  ledger observations (AC2b-CI), with **exactly one pre-lock exception**: case
  47's own red, which is taken under the P-004 unittest command because pytest is
  not yet locked when it runs. Its raw log records that command verbatim, so it
  cannot be mistaken for a pytest run. `test_node_id` is a property of a case's file and
class location, fixed when the case is authored, and T16 verifies every node ID
against a **terminal** `--collect-only` run at the end of the shipment — by
which time pytest is locked. No runner field, no schema change, and no policy
expansion is introduced for this.

### Case ledger — 47 cases

Counts: **47 unique cases** = **33 RED-FIRST** + **14 CHARACTERIZATION**.
Owner assignments: **53** (six cases carry two owners; case 47's author and
owner are the same task).

| # | Case name | Asserts | Class | Author | Owner | Machine-checked dependency |
|---|---|---|---|---|---|---|
| 1 | `test_manifest_validates_against_schema` | AC1, AC1a | R | T3a | T4 | T4←T3a; T4←T2b — red: no manifest/schema |
| 2 | `test_schema_live_and_versioned_mirror_agree` | AC1 | R | T3a | T2b | T2b←T3a |
| 3 | `test_payload_manifest_contract_registered` | AC1 | R | T3a | T2b | T2b←T3a |
| 4 | `test_every_tracked_path_is_classified` | AC11, AC3d | R | T3a | T4 | T4←T3a |
| 5 | `test_start_scripts_and_workspace_config_excluded` | AC11 | R | T3a | T4 | T4←T3a |
| 6 | `test_manifest_is_sole_source_of_payload_paths` | AC1 | R | T3a | T5 | T5←T3a |
| 7 | `test_unclassified_tracked_path_fails_build` | AC2, AC8 | R | T3a | T5 | T5←T3a (injects via typed `tracked_paths` seam; never mutates the git index) |
| 8 | `test_payload_size_reported` | AC8 | R | T3a | T5 | T5←T3a |
| 9 | `test_generated_output_root_excluded_from_classifier_inputs` | AC3d, AC2 | R | T3a | T5 | T5←T3a |
| 10 | `test_generate_emits_expected_tables_to_a_scratch_target` | AC2c | R | T3a | T6 | T6←T5←T3a (also drives tracked-path refusal) |
| 11 | `test_generate_is_byte_deterministic_and_cross_platform` | AC2c | R | T3a | T6 | T6←T5←T3a |
| 12 | `test_only_one_generation_path_exists` | AC2c | R | T3a | T6 | T6←T5←T3a |
| 13 | `test_plugin_generation_is_idempotent` | AC2c, AC3d | R | T3a | T6 | T6←T5←T3a |
| 14 | `test_wheel_generated_table_matches_manifest` | AC2c, AC1a, AC1b | R | T3a | T7 | T7←T3a |
| 15 | `test_docs_root_guides_only` | AC4 | R | T3a | T7 | T7←T3a |
| 16 | `test_wheel_excludes_backlogit_explicitly` | AC3 | C | T3b | T7 | T7←…←T3b |
| 17 | `test_wheel_excludes_dev_directories` | AC3 | C | T3b | T7 | T7←…←T3b |
| 18 | `test_wheel_contains_required_runtime_set` | AC4 | R | T3a | T7 | T7←T3a (red: omits `.github/policies/**` + scripts subset) |
| 19 | `test_core_metadata_version_pins_preserved` | I4, V2 | C | T3b | T7 (sole) | T7←…←T3b |
| 20 | `test_plugin_generated_declaration_matches_manifest` | AC2c | R | T3a | T8 | T8←T3a |
| 21 | `test_plugin_payload_excludes_dev_directories` | AC3 | R | T3a | T8 | T8←T3a |
| 22 | `test_plugin_source_path_is_tracked_and_fetchable` | AC3c | C | T3b | T8 (preservation) | T8←…←T3b; T8←T1 |
| 23 | `test_plugin_payload_conforms_to_the_selected_strategy` | AC3d, AC3c | R | T3a | T8 | T8←T3a; T8←T1 |
| 24 | `test_target_workspace_prefix_derivation_is_centralized` | AC2d | R | T3a | T4 | T4←T3a |
| 25 | `test_install_emits_only_generated_output` | AC5, I3 | C | T9 | T7 / T8 | T7←T9; T8←T9 |
| 26 | `test_no_engine_records_in_target_workspace` | AC5 | C | T9 | T7 / T8 | T7←T9; T8←T9 |
| 27 | `test_skill_docs_refs_resolve_to_workspace_not_payload` | AC5, AC2d, R2 | R | T9 | T5 | T5←T9 |
| 28 | `test_verify_workspace_parity_trimmed_vs_baseline` | AC6 | C | T10 | T7 / T8 | T7←T10; T8←T10 |
| 29 | `test_upgrade_from_1_5_0_leaves_no_orphans` | AC6, R3, V3 | R | T10 | T7 / T8 | T7←T10; T8←T10 |
| 30 | `test_home_and_version_behave_identically` | AC6, I1, I2 | C | T10 | T7 / T8 | T7←T10; T8←T10 |
| 31 | `test_data_dir_resolution_pip_install` | AC6a, R4 | C | T11 | T7 | T7←T11 |
| 32 | `test_data_dir_resolution_clone_editable` | AC6a, R4 | C | T11 | T7 | T7←T11 |
| 33 | `test_python_channel_needs_no_plugin_root_artifact` | AC6a A1 | C | T11 | T7 | T7←T11 |
| 34 | `test_plugin_root_resolves_templates_and_schemas` | AC6b | R | T11 | T8 | T8←T11 |
| 35 | `test_plugin_version_resolves_from_plugin_manifest` | AC6b, AC10 | R | T11 | T8 | T8←T11 |
| 36 | `test_plugin_channel_resolution_imports_no_python_package` | AC6b B1 | R | T11 | T8 | T8←T11 |
| 37 | `test_plugin_payload_has_no_python_distribution` | AC6b B2 | R | T11 | T8 | T8←T11 |
| 38 | `test_channel_resolver_contracts_are_disjoint` | AC6a, AC6b | R | T11 | T8 | T8←T11 |
| 39 | `test_register_phase_all_environments_python_channel` | AC7 | C | T12 | T7 | T7←T12 |
| 40 | `test_plugin_only_register_copilot_cli_succeeds` | AC7 | C | T12 | T8 | T8←T12 |
| 41 | `test_plugin_only_unsupported_targets_fail_the_same_way_as_baseline` | AC7 | C | T12 | T8 | T8←T12 |
| 42 | `test_plugin_channel_excludes_python_cli_by_design` | AC7 | R | T12 | T8 | T8←T12 |
| 43 | `test_gate4_crossrefs_intact_in_built_payload` | AC9, AC2d | R | T13 | T7 / T8 | T7←T13; T8←T13 |
| 44 | `test_version_resolves_on_plugin_install_without_cli` | AC10 | R | T13 | T8 | T8←T13 |
| 45 | `test_release_workflow_runs_payload_gate_before_publish` | AC2b | R | T3a | T14 | T14←T3a |
| 46 | `test_release_gate_covers_all_declared_channels` | AC2b, AC1 | R | T3a | T14 | T14←T3a |
| 47 | `test_ci_invokes_the_locked_canonical_test_runner` | AC2b-CI | R | T0 | T0 | none — author and owner are the same task |

**Per-author (R/C).** T0 1/0 · T3a 22/0 · T3b 0/4 · T9 1/2 · T10 1/2 ·
T11 5/3 · T12 1/3 · T13 2/0. Totals 33 R, 14 C.

**Per-owner edges.** T0 1 · T2b 2 · T4 4 · T5 5 · T6 4 · T7 16 · T8 19 ·
T14 2 = **53**. The six two-owner cases are #25, #26, #28, #29, #30, #43. Case #47 is the only case whose author and owner are the same task.

Case 24 is the AC2d case. Its name states the derivation property the plan
actually asserts; it carries no occurrence semantics.

### Baseline (T2a)

T2a records baseline facts only. It performs **no** rebuild that another task
consumes as input, and it uses **no** OS temporary directory.

| Record | Content |
|---|---|
| **E1** | Member inventories per artifact, plus an aggregate digest. For the wheel this is the distribution's own `RECORD` / archive-member inventory — **not** an installed-workspace or `site-packages` listing |
| **E2** | Full 40-character SHA of the baseline commit — authoritative over branch name or `HEAD` |
| **E3** | The deterministic rebuild recipe and environment dimensions, recorded as **T2a's own reproducibility record only** |
| **E4** | Observation provenance for each recorded fact |

**Aggregate digest definition (single definition, used everywhere).** The
aggregate digest is the SHA-256 of the newline-joined, path-lexicographically
sorted sequence of `(path, size, sha256)` triples, with fields separated by the
ASCII unit separator, forward slashes in paths, encoded UTF-8.

No binary artifact is committed. T10 consumes T2a's **recorded facts**; it does
not rebuild the baseline.

**Like-for-like comparison (T10).** T10's orphan verdict is a set difference
between **two wheel `RECORD` member-path sets**: the baseline side from T2a's
normalized E1 wheel inventory, the trimmed side from the actual built wheel's own
`RECORD`. Comparing a generated workspace path listing against `site-packages`
paths is prohibited — the two are different path universes, so nearly every path
would differ even when nothing moved, producing a phantom orphan set
indistinguishable from a real regression.

Allowed metadata differences, excluded from the verdict (**closed list** — a
difference not named here is a real difference and must be reported): the
`RECORD` row for `RECORD` itself; `.dist-info/WHEEL` generator and tag lines;
`.dist-info/METADATA` version-derived fields; the `.dist-info` directory name's
version component; `*.pyc` and `__pycache__` members.

Real offline installed-upgrade execution remains deferred as `60C207F1`.

### Evidence-verification contract for 160.017-T

There is exactly one canonical evidence record shape. Producers **reference**
this table; producers do not restate field lists.

| Field | Definition |
|---|---|
| `case_name` | The logical case key — one of the 47 ledger names. Bare identifier: must contain neither `::` nor `/` |
| `test_node_id` | The full pytest node ID. Must contain `::` |
| `declared_class` | `RED-FIRST` or `CHARACTERIZATION`, matching the ledger |
| `author_task` | Authoring task ID, matching the ledger |
| `owner_task` | Owning task ID, matching the ledger |
| `observation_phase` | `baseline` or `post-change` |
| `expected_outcome` | The outcome the class contract requires for this phase |
| `exit_status` | Strict integer. A boolean is rejected |
| `evidence_ref` | Path to the raw log |
| `evidence_sha256` | SHA-256 of the raw log bytes |
| `evidence_bytes` | Byte length of the raw log |
| `source_commit` | Full 40-character commit SHA captured before the command ran |
| `worktree_status` | `git status --porcelain=v1` output captured before the command ran |
| `artifact_ref` | Reference to the artifact the observation was made against |

`case_name` and `test_node_id` are distinct fields with distinct roles. No
single field serves both; `case_name` is the ledger join key and `test_node_id`
is the collection identity.

**Provenance protocol.** Commit first. Then capture `git rev-parse HEAD` and
`git status --porcelain=v1` into the head of the raw log, before the command
runs. Then run the case. A recorded observation requires a clean, committed
tree.

**Artifact identity — always phase-selected.** `artifact_ref` validation is
**always** selected by `observation_phase`. There is **no** unconditional
baseline check anywhere in the contract:

| `observation_phase` | Artifact assertion (wheel) | Artifact assertion (plugin) | Static contract assertion |
|---|---|---|---|
| `baseline` | T2a baseline **wheel** inventory (E1) | T2a baseline **plugin** inventory (E1) | T2a baseline commit SHA (E2) |
| `post-change` | Current **trimmed wheel** inventory | Current **trimmed plugin** inventory | The observation's own `source_commit` |

A `post-change` artifact digest is **never** required to equal the baseline
digest. Requiring equality would make the plan's own trimming goal unachievable.

The static-contract column exists for case #47, which builds nothing and asserts
over repository source files only. It is **not** an exemption: that case is still
phase-selected and still validated — its identity source is a source tree rather
than an archive, because inventing an artifact digest for a case that produces no
artifact would be a fabricated value.

**T16 validates:**

1. every record's `case_name` joins to exactly one ledger row, and every ledger
   row is covered;
2. every `test_node_id` is present in `uv run python -m pytest --collect-only` output;
3. `source_commit` re-derives to the captured value and `worktree_status` is
   empty — a dirty tree is rejected;
4. `evidence_sha256` and `evidence_bytes` match the raw log bytes;
5. `artifact_ref` validates against the phase-appropriate identity source above;
6. RED-FIRST ordering: the red test commit precedes the red observation and the
   green implementation commit precedes the green observation.

**Log bounds — one rule, fail closed.** Each raw log is at most 256 KiB **and**
at most 2,000 lines. **A log exceeding either limit is rejected.** There is no
truncation path, no `truncated` field, and no pre-truncation counts — those
would be three extension fields that nothing else consumes, self-reported by the
producer whose output the bound exists to constrain. A producer that cannot fit
an observation inside the bound **halts and reports**; it does not truncate.
When T16 rejects an over-bound log it cites the path, digest, byte size and line
count **only**, never the content. At most 3 logs per case. At most 200 files per
shipment. No binaries.

### Mandatory durable outputs

| Output | Owner |
|---|---|
| `.autoharness/payload-manifest.yaml` | T4 |
| `schemas/payload-manifest.schema.json` + `schemas/payload-manifest/1.0.0.schema.json` | T2b |
| Payload size report (per channel) | T5 |
| Generated wheel tables | T7 |
| Generated `.github/plugin/marketplace.json` declaration, plus `plugin-payload/**` under branch (b) | T8 |
| Baseline inventories, aggregate digest, reproducibility record | T2a |
| Per-producer observation records and raw logs | each producer |
| Evidence verification report | T16 |
| Release gate logs (Gate A, Gate B) | T14 |
| Updated docs and this plan | T15 |

The upgrade-orphan guarantee (V3) is delivered in its **local-artifact /
`RECORD`** form only. It consumes T2a's recorded facts. It is not, and does not
claim to be, a real installed-upgrade execution, a network fetch, or a hermetic
rebuild.

## Security

* No secret, token, or credential enters the payload, the manifest, the
  generated output, or any observation record.
* Action references are pinned to a full commit SHA with a version comment.
* The plugin channel carries no executable Python distribution (AC6b B2).
* Gate B computes and records SHA-256 for every `dist/*` member before publish.
* Scratch is workspace-contained and gitignored; it never reaches an OS
  temporary directory where another process could read or substitute it.

## Rollback

| ID | Rule |
|---|---|
| **R-1** | Forward revert is the default rollback: revert the change commits and re-run the gates |
| **R-2** | Captured pre-change bytes are **evidence**, not restoration authority |
| **R-3** | Any destructive restore requires fresh, live, non-synthesizable operator approval |
| **R-4** | If a channel cannot be resolved, halt — do not publish a partial payload |
| **R-5** | Read-only alternatives are preferred over any mutating recovery step |

## Sequencing

```text
159-S → 160-S → 161-S → 162-S → 163-S → 164-S → 165-S → 166-S → 168-S → 167-S
```

`168-S` is this shipment. It carries the covering feature `160-F` and all 19
tasks — 20 manifest entries.

## Task decomposition

19 live tasks. `T7b` / `160.019-T` was retired; its record is a tombstone in
`.backlogit/archive/` and the ID is never reused.

| T# | Task ID | Scope |
|---|---|---|
| T0 | `160.020-T` | Test-toolchain alignment: pinned pytest dependency, `uv.lock`, CI invocation, plus case #47 |
| T1 | `160.002-T` | Plugin source-strategy spike and decision record |
| T2a | `160.001-T` | Baseline inventories, aggregate digests, reproducibility record |
| T2b | `160.018-T` | Manifest schema — live file, versioned mirror, contract registration |
| T3a | `160.005-T` | RED-FIRST case authoring (22 cases) |
| T3b | `160.016-T` | CHARACTERIZATION case authoring (4 cases) |
| T4 | `160.003-T` | `.autoharness/payload-manifest.yaml` authoring |
| T5 | `160.004-T` | Classifier, resolver, size report |
| T6 | `160.014-T` | Generator single path and deterministic rendering |
| T7 | `160.006-T` | Wheel channel build tables |
| T8 | `160.007-T` | Plugin channel declaration and materialization |
| T9 | `160.008-T` | Install-emission cases |
| T10 | `160.012-T` | Parity / upgrade / home-version cases |
| T11 | `160.013-T` | Channel resolution cases |
| T12 | `160.009-T` | Register-phase cases |
| T13 | `160.010-T` | Cross-reference and version-resolution cases |
| T14 | `160.015-T` | Release workflow gates |
| T15 | `160.011-T` | Documentation |
| T16 | `160.017-T` | Evidence verification |

### T0 — `ci.yml` changes (exactly three)

1. Pin `astral-sh/setup-uv` to the full commit SHA with the version comment.
2. Add a fail-closed pytest availability preflight that halts the job when
   pytest is not resolvable.
3. Replace the existing `unittest` invocation with `uv run python -m pytest` as
   the authoritative test command.

T0 owns only the `pyproject.toml` test-dependency region, `uv.lock`, `ci.yml`,
and the single case-#47 test file.

### T0 — red-first before implementation

T0 is **not** exempt from the class contract. It authors ledger case #47,
`test_ci_invokes_the_locked_canonical_test_runner` — a static contract test that
reads `pyproject.toml`, `uv.lock` and `ci.yml` and asserts the pinned pytest
declaration, the locked `pytest` node, the `uv run python -m pytest` invocation,
the pinned setup-uv step, and the fail-closed preflight. It builds nothing.

Binding order inside T0: author the case → **commit** → observe it **red** under
P-004's `PYTHONPATH=src python -m unittest discover -s tests` on the committed
pre-change tree → apply the three deliverables → **commit** → observe it **green**
under `uv run python -m pytest`. T0 authors and owns this one case and **no**
payload behaviour test of any kind.

### Tracked-write approval — T0, T7, T8, T14

Every tracked write whose bytes change is class `OVERWRITE`, and **a tracked
`OVERWRITE` requires external, fresh, live operator approval regardless of which
task performs it and regardless of whether a generator was involved.**

What is generator-scoped is the AC3e *classification machinery* (Layer 1). The
Layer-2 *approval obligation* is not. Exempting an authored edit would make
"author it by hand" a silent bypass of the control Principle VII imposes — a
strictly worse outcome than running the generator.

So T0 (`pyproject.toml`, `uv.lock`, `ci.yml`) and T14 (`release.yml`) follow the
same four steps as T7 and T8: compute and record the reviewed OVERWRITE/REMOVE
partition; obtain fresh live approval out-of-band over that exact partition;
apply the exact reviewed diff, re-verify the resulting bytes and **halt on any
divergence**; append the reviewed-partition record to the same pre-change byte
record. **Recorded bytes never authorize** (R-2). T16 verifies all four records.

This approval binds at **implementation** time, when Ship executes these tasks.
It is not a gate on Stage publication of the backlog records, which mutate no
tracked source, config or workflow file.

### Pre-change captures (exactly six)

| Capture | Owner |
|---|---|
| `pyproject.toml` test-dependency region | T0 |
| `uv.lock` | T0 |
| `.github/workflows/ci.yml` | T0 |
| `pyproject.toml` build-table region | T7 |
| `.github/plugin/marketplace.json` | T8 |
| `.github/workflows/release.yml` | T14 |

Six captures across four tasks. T14 never owns `ci.yml`; T0 is its sole owner.

## Prerequisite DAG

19 nodes, **51 edges**, acyclic. Roots: `T0`, `T1`, `T2a`. Sink: `T15`.

| Task | Depends on |
|---|---|
| `160.020-T` (T0) | — |
| `160.002-T` (T1) | — |
| `160.001-T` (T2a) | — |
| `160.005-T` (T3a) | `160.001-T`, `160.020-T` |
| `160.016-T` (T3b) | `160.001-T`, `160.020-T` |
| `160.018-T` (T2b) | `160.005-T` |
| `160.003-T` (T4) | `160.005-T`, `160.018-T` |
| `160.004-T` (T5) | `160.005-T`, `160.003-T`, `160.008-T` |
| `160.014-T` (T6) | `160.004-T`, `160.002-T` |
| `160.008-T` (T9) | `160.001-T`, `160.005-T`, `160.016-T` |
| `160.012-T` (T10) | `160.001-T`, `160.005-T`, `160.016-T` |
| `160.013-T` (T11) | `160.001-T`, `160.005-T`, `160.016-T` |
| `160.009-T` (T12) | `160.001-T`, `160.005-T`, `160.016-T` |
| `160.010-T` (T13) | `160.001-T`, `160.005-T`, `160.016-T` |
| `160.006-T` (T7) | `160.014-T`, `160.008-T`, `160.012-T`, `160.013-T`, `160.009-T`, `160.010-T` |
| `160.007-T` (T8) | `160.002-T`, `160.014-T`, `160.008-T`, `160.012-T`, `160.013-T`, `160.009-T`, `160.010-T` |
| `160.015-T` (T14) | `160.006-T`, `160.007-T`, `160.020-T` |
| `160.017-T` (T16) | `160.015-T` |
| `160.011-T` (T15) | `160.017-T`, `160.008-T`, `160.012-T`, `160.013-T`, `160.009-T`, `160.010-T`, `160.015-T` |

Topological order:

```text
T0, T1, T2a, T3a, T3b, T2b, T9, T10, T11, T12, T13, T4, T5, T6, T7, T8, T14, T16, T15
```

T0 precedes every task that authors or executes a pytest case, and precedes T14.

## Traceability

* Source stash entry `E9E5E6CC`, archived at `.backlogit/archive/stash.jsonl`.
* `AB387F16` was a pre-persistence temporary identifier with no durable record;
  it is retained here only so the reference resolves.
* The forward-correction comment series on `160-F` is authoritative for the
  current 19-task set.
* Deliberation: `docs/decisions/2026-09-03-minimal-copilot-plugin-payload-deliberation.md`.
* Review history: `docs/reviews/2026-09-03-minimal-copilot-plugin-payload-plan-review-history.md`.

## Deferred scope

| ID | Item | Priority | Status |
|---|---|---|---|
| `99818C6D` | sdist channel payload declaration and gating | high | Deferred — out of scope for SHIP-10 |
| `60C207F1` | Real offline end-to-end installed-upgrade execution | high | Deferred — **current residual risk**, not closed |
| `00C2B1F9` | Payload size budget enforcement thresholds | low | Deferred |
| `F73A04A2` | Per-channel payload diff reporting | low | Deferred |
| `0B83AC8F` | T3a (`160.005-T`) execution-planning split review — 22-case sizing against the 2-hour bound | medium | Deferred — **current residual risk**, not closed |

`60C207F1` is an open residual risk. This plan delivers the narrowed
local-artifact / `RECORD` upgrade guarantee (V3) and makes no claim of real
installed-upgrade execution, network fetch, or hermetic rebuild.

## Plan Hardening

### Hardening signals

Elevated blast radius: schema evolution, CI and release workflow modification,
build backend configuration, and two distribution channels. Hardening is
required and has been applied.

### Invariants

| ID | Invariant |
|---|---|
| **I1** | `--home` behaviour is identical across channels |
| **I2** | `--version` behaviour is identical across channels |
| **I3** | Installation emits only generated output into the target workspace |
| **I4** | Both `core-metadata-version = "2.4"` pins are preserved |
| **I5** | The manifest is the sole source of payload paths in every code path |

### Applicable learnings

* Unpinned hatchling silently changed the emitted metadata version — pins are
  asserted, not assumed (I4, V2).
* `012-S` portability allow-list: frozen, symbol-keyed, non-increasing (the P4
  pattern).
* Schema-mutation third-occurrence rule: a third attempt at the same schema
  mutation opens the circuit and the approach is withdrawn rather than retried.
* `096-S` canonical subagent path: one canonical location, referenced, never
  duplicated.

### H1 — Failure modes and mitigations

| Failure mode | Mitigation |
|---|---|
| Manifest drifts from build reality | Gate A validates and Gate B asserts against the built artifact |
| A second generation path appears | AC2c four-predicate single-path check |
| Classification ambiguity silently resolves the wrong way | AC11 most-specific selection with equal-specificity fail-closed |
| Generated output recursively re-enters the payload | Generated roots removed from classifier input before matching (AC3d) |
| Scratch escapes the workspace | Canonical containment validation, fail-closed (AC3e) |
| Evidence fabricated or stale | T16 re-derives `source_commit`, rejects dirty trees, verifies log digests |
| Post-change artifact wrongly compared to baseline | Phase-selected artifact identity sources |
| Test toolchain unavailable in CI | T0 fail-closed pytest preflight |

### H2 — Writable surface table

Each surface has exactly one owner set. A write outside this table is a
contract violation.

| Surface | Owner(s) |
|---|---|
| `.autoharness/payload-manifest.yaml` | T4 |
| `schemas/payload-manifest.schema.json` and `schemas/payload-manifest/1.0.0.schema.json` | T2b |
| `src/autoharness/schema_contracts.py` (registration entry only) | T2b only (narrow, explicit exception) |
| `build_support/**` | T5, T6 |
| `tests/**` | T0 (case #47 file only), T3a, T3b, T9, T10, T11, T12, T13, T16 (**not** T2b, **not** T6) |
| `pyproject.toml` — build tables | T7 |
| `pyproject.toml` — `[dependency-groups]` | T0 |
| `uv.lock` | T0 only |
| `.github/workflows/ci.yml` | **T0 only** |
| `.github/workflows/release.yml` | T14 |
| `.github/plugin/marketplace.json` | T8 |
| `plugin-payload/**` | T8 |
| `docs/spikes/2026-09-03-ship10-plugin-channel-mechanism.md` | T1 |
| `docs/audits/2026-09-03-ship10-payload-evidence/` | T0, T2a, T3a, T3b, T9, T10, T11, T12, T13, T7, T8, T14, T16 |
| Per-producer observation JSON and raw logs | the producing task |
| `tests/fixtures/payload-baseline/**` | T2a only |
| `docs/**` | T15 |

### Checkpoints

An operator checkpoint is required before: the first `ci.yml` / `uv.lock` /
`[dependency-groups]` write (T0), the first schema write (T2b), the first
`pyproject.toml` build-table write (T7), the first `release.yml` write (T14),
and any `OVERWRITE` or `REMOVE` class write.

### Principle VII — two-layer approval

**Layer 1 — generator.** The generator computes the write class, reports it,
and **unconditionally refuses** any tracked `OVERWRITE` or `REMOVE`. It accepts
no approval input of any kind. Because it cannot be told "approved", its refusal
is unforgeable.

**Layer 2 — approval.** Approval is an external agent-protocol gate operating on
the reviewed diff. **T0, T7, T8 and T14** — every task that performs a tracked
write — apply exactly the reviewed diff, re-verify byte-for-byte, and halt on any
divergence. Layer 2 is not generator-scoped; see *Tracked-write approval*.

Principle VII rule 9 refers to the single ephemeral root defined once in AC3e;
it is not restated here.

### V1–V6 — verification commitments

| ID | Commitment |
|---|---|
| **V1** | Assertions are made against the built artifact, not against source |
| **V2** | The publish toolchain is not verifiable locally; both `core-metadata-version = "2.4"` pins are asserted instead (I4) |
| **V3** | The upgrade orphan scan is delivered in **local-artifact / `RECORD` form only** |
| **V4** | A negative allow-list test asserts the allow-list cannot silently grow |
| **V5** | Install parity is asserted across channels |
| **V6** | A verified class-transition ledger records every write class transition |

### Risky actions

| Action | Control |
|---|---|
| Modifying `release.yml` | Structural assertions in Gate A; operator checkpoint |
| Modifying `ci.yml` | Exactly three enumerated changes; pre-change capture; reviewed OVERWRITE partition with fresh live approval |
| Regenerating `plugin-payload/**` | Idempotence case #13; generated-root exclusion |
| Any tracked overwrite or removal | Two-layer approval; fresh live operator approval over the exact reviewed partition; re-verify applied bytes and halt on divergence (T0, T7, T8, T14) |
| Scratch cleanup | Separate destructive-approval operation; never automatic |

### Residual risk

* **`60C207F1` — offline installed-upgrade execution is deferred and open.**
  V3's guarantee is narrowed to the local-artifact / `RECORD` form. This is a
  live residual risk carried into execution, not a closed item.
* **`0B83AC8F` — T3a's 22-case size is unconfirmed against the 2-hour bound.**
  T3a authors 22 RED-FIRST cases and records 22 red observations under the full
  provenance protocol. That is a lot of work, it sits at the top of the M band,
  and it may exceed the bound that forces a split. It is not "a few scenarios".
  Splitting it is separate execution-planning work — a split boundary must be
  chosen, the author column re-derived for 22 rows, a DAG node and its edges
  added, and the ordering paths recomputed — so it is captured rather than done
  in place. **Disposition required before or during execution:** measure the real
  authoring cost on the first few cases and split if it exceeds the bound, or
  record a measured confirmation that it fits. **Residual risk if neither
  happens:** an over-bound task degrades agent reliability, and T3a is the
  RED-FIRST harness on which 34 ordering paths and every downstream green
  transition depend, so an incomplete red harness silently weakens the whole
  evidence contract.
* `99818C6D` — the sdist channel remains ungated.
* The publish toolchain's emitted metadata cannot be verified before publish;
  V2's pin assertions are the compensating control.

### Publication readiness

**`READY_WITH_FOLLOWUPS`**, carrying `0B83AC8F` (T3a sizing) and `60C207F1`
(offline installed upgrade). Not `READY`: both carry a concrete ID and a stated
residual risk, and neither is closed.

## Plan review

Current verdict: **PASS** — zero current P0 and zero current P1 findings
(cycle-11 fresh multi-persona review over the changed backlog and docs
artifacts: architecture, security, test/QA, release/ops,
simplicity/maintainability, policy).

Scope of the current review: the canonical plan (this document), the 19 task
records, `160-F`, and `168-S`. Missing future implementation artifacts and
currently unchanged CI or release files are **not** findings — queued plan
readiness is not implementation completion.

Open P2 (tracked, non-blocking): `backlogit shipment get 168-S` derives
`size_composition` by resolving `160-F` into every child with `parent_id: 160-F`,
including the archived, retired `160.019-T`. The derived rollup therefore reads
`M:12, S:8` over 20 members while the **live 19-task histogram is `M:11, S:8`**.
The 20-entry manifest itself is correct and does not contain `160.019-T`. This
is a backlogit rollup behaviour, not a plan or manifest defect.

Full per-cycle history, findings, and dispositions:
[`docs/reviews/2026-09-03-minimal-copilot-plugin-payload-plan-review-history.md`](../reviews/2026-09-03-minimal-copilot-plugin-payload-plan-review-history.md).
