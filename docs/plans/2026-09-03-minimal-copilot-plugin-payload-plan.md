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

## Problem

Both autoharness distribution channels deliver the entire development repository.
`.github/plugin/marketplace.json` declares `source: "."` (repo root, 3,238 tracked
files / ~18 MB), and `pyproject.toml` force-includes all 642 `docs/` files into
every wheel. `.backlogit/` — 2,110 files of this workspace's own backlog records,
65% of all tracked files — is shipped to consumers with no runtime role.

Full evidence in the source deliberation.

## Goal

Package and install only the minimum runtime set, from a **single declarative
allowlist manifest** shared by both channels, enforced by a fail-closed
composition test — preserving install, update, verification, and cross-environment
behavior.

## Non-goals

* Splitting the repository (rejected, Option 3).
* Changing what `/install-harness` generates into a target workspace.
* Changing `autoharness_home` resolution order.
* Trimming the repository itself. This changes only what is **packaged**.

## Affected surfaces

| Surface | Change |
|---|---|
| `.autoharness/payload-manifest.yaml` *(new)* | Allowlist manifest — single source of truth |
| `schemas/payload-manifest.schema.json` *(new)* | Schema for the manifest (live contract) |
| `schemas/payload-manifest/1.0.0.schema.json` *(new)* | Immutable versioned mirror — required by the two-file convention below |
| `src/autoharness/schema_contracts.py` | Register `payload-manifest` so the mutation detector covers it from first release |
| `pyproject.toml` | Replace ad-hoc `force-include` with manifest-derived includes |
| `.github/plugin/marketplace.json` | Constrain plugin payload to the manifest |
| `build_support/payload.py` *(new, not shipped)* | Manifest loader + resolver + centralized target-workspace classifier |
| `build_support/` generation entry point *(new, not shipped)* | Single deterministic `generate` / `--check` command (AC2c) |
| `.github/workflows/release.yml` | Add the unbypassable in-job payload-composition gate step (AC2b) |
| `tests/test_payload_manifest.py` *(new)* | Fail-closed composition test |
| `tests/test_install_e2e.py` *(new)* | Install/upgrade/verify from built artifact |
| `docs/installation.md`, `README.md` | Document payload boundary |
| `CHANGELOG.md` | Record the packaging change |

**Schema note:** `payload-manifest.schema.json` is a **new** schema at
`1.0.0`. No existing schema is mutated in place — this repository has a recorded
three-occurrence history of in-place schema mutation without a version bump
(`docs/compound/2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md`).

**Schema publication layout (binding — review-fix cycle 1, Learnings Researcher
P1).** Creating the schema at `1.0.0` is necessary but **not sufficient** to
avoid the recorded bug class. That learning records the shorter, more dangerous
fix path applies precisely to *contracts unregistered in `SCHEMA_CONTRACTS`* —
an unregistered schema has nothing that detects a later in-place mutation, so a
fourth occurrence would land silently. This shipment therefore adopts the
repository's established two-file convention observed on every other versioned
schema here (`harness-config`, `harness-manifest`, `workspace-profile`,
`tool-telemetry-event`, `validation-gates`), rather than shipping a lone
top-level file:

1. Publish **both** `schemas/payload-manifest.schema.json` (the live contract)
   and the immutable versioned mirror `schemas/payload-manifest/1.0.0.schema.json`.
   A top-level schema with **no** versioned mirror is a plan-conformance failure.
2. **Register the contract in `src/autoharness/schema_contracts.py`** so the
   existing mutation detector covers it from its first release. Registration is
   an acceptance criterion, not an optional follow-up.
3. Assert the pair: a test that fails if the live file and the `1.0.0` mirror
   diverge while `$id`/version still reads `1.0.0`. That is the assertion whose
   absence allowed the three prior occurrences.

**Loader placement (review finding P1-6):** the manifest loader is a **build-time**
concern and lives in `build_support/`, which is itself excluded from the payload.
Placing it in `src/autoharness/` would ship the packaging rules inside the very
artifact they trim — contradicting the plan's own minimalism goal.

## Acceptance criteria

### AC1 — Manifest is the single source of truth

* `.autoharness/payload-manifest.yaml` exists, validates against
  `schemas/payload-manifest.schema.json`, and declares `include`, `exclude`, and
  per-channel (`wheel`, `plugin`) overlays.
* Neither `pyproject.toml` nor `marketplace.json` contains a payload path that is
  not derivable from the manifest.

### AC2 — Allowlist semantics, fail closed

* Payload composition is **allowlist-based**: a path not matched by an `include`
  rule is excluded.
* A tracked path that is neither allowlisted nor matched by an explicit `exclude`
  rule **fails the build**. Silent default-inclusion is prohibited.

### AC2b — The fail-closed promise is enforced in the actual release path

*Added in Orchestrator review-fix cycle 1 (finding 6).* Hardening decision **H1**
adopts "generated-and-asserted" rather than a dynamic hatchling build hook, which
means AC2's guarantee lives in a **test**. A test that nothing in the release path
is required to run is not a gate — it is a hope. Without AC2b a release could be
built and published with the composition suite never executed, which is exactly
the failure mode that produced the current untrimmed payload.

`.github/workflows/release.yml` has exactly **one** job (`release`). A separate
gating job with a `needs:` edge is therefore unavailable without restructuring the
workflow, and restructuring is out of scope. The unbypassable form in a single-job
workflow is an **in-job prerequisite step**:

* A payload-composition gate step exists in the `release` job and runs the
  composition suite **and** `payload generate --channel all --check`.
* Its step index is strictly **less than** both the build step index and the
  publish step index.
* It carries **no** `continue-on-error: true` and **no** `if:` expression of any
  kind — no `always()`, no dispatch-input bypass.
* `test_release_workflow_runs_payload_gate_before_publish` parses `release.yml`
  **structurally** and asserts all four properties, so a later edit that reorders,
  conditions, or soft-fails the step is caught by the test suite rather than
  discovered at publish time.

If a future change splits `release.yml` into multiple jobs, the gate should
migrate to a separate job with a `needs:` edge. That restructuring is **not** part
of this shipment.

### AC2c — One deterministic generation command, one source of truth

*Added in Orchestrator review-fix cycle 1 (finding 6).* Because H1 makes the
static `pyproject.toml` include table and the `marketplace.json` payload
declaration **derived** artifacts, they become a second source of truth unless
regeneration is deterministic, single-pathed, and drift-detecting.

* Exactly one command generates and re-generates both channel tables:
  `python -m build_support.payload generate --channel {wheel|plugin|all}`, with
  `--check` re-deriving and comparing without writing and exiting non-zero on
  drift.
* Output is **byte-deterministic**: stable sort order, no timestamps, no absolute
  paths, no environment values, and **identical on Windows and POSIX** (path
  separators normalized to the forward-slash form both formats expect).
* **Single-path requirement:** adding a second generation path — a Makefile
  target, a shell wrapper, an inline CI snippet, or a test helper that re-derives
  — recreates the multiple-truths defect. CI and the tests **invoke** this
  command; they never reimplement it. A test asserts no other module or workflow
  step derives a channel table.
* Each derived table carries a generated-by header naming the command; `--check`
  is what mechanically detects a hand edit.

### AC2d — Target-workspace path classification is centralized

*Added in Orchestrator review-fix cycle 1 (finding 6).* The judgment "this
`docs/*` reference resolves against the **target workspace**, not the payload"
(risk R2) was stated separately in AC5, AC9, and the R2 allow-list. Duplicated
classification is how that rule drifts.

* The manifest declares **one** `target_workspace_paths` key naming the prefixes
  (`docs/compound`, `docs/plans`, `docs/memory`, `docs/decisions`, `docs/closure`).
* One function, `build_support.payload.classify_target_workspace_path(path)`, is
  the sole decision point and reads that single key.
* AC5's skill-reference test, AC9's Gate 4 allow-list, and the R2 rule all **call
  that function**. Re-listing the prefixes at any call site is prohibited, and a
  test asserts exactly one authored occurrence of the prefix list in the
  repository.

### AC3 — Development artifacts are excluded from both channels

Built wheel and resolved plugin payload contain **zero** files under:
`.backlogit/`, `tests/`, `experiments/`, `references/`, `.githooks/`, `.vscode/`,
`.claude/`, `.engram/`, `.graphtor/`, and the `docs/` history subdirectories
(`archive`, `plans`, `memory`, `decisions`, `closure`, `compound`, `reviews`,
`spikes`, `audits`, `exec-plans`, `telemetry`, `design-docs`, `research`,
`deferred`, `product-specs`).

`.backlogit/` exclusion is asserted **explicitly and by name** in its own test
case — it is the largest disclosure surface and must not depend on a glob.

### AC4 — Runtime payload is complete

Built wheel contains `templates/**`, `schemas/**`, `.github/agents/**`,
`.github/skills/**`, `.github/instructions/**`, `.github/prompts/**`,
`.github/policies/**`, both `copilot-*instructions.md`, the referenced `scripts/`
subset, `AGENTS.md`, and `docs/` **root guides only**.

### AC5 — Target workspaces receive only generated output

* An `/install-harness` run against a scratch workspace produces **no** file that
  is an autoharness engine file copied verbatim from the payload.
* Test asserts the scratch workspace contains no `.backlogit/` records from the
  engine, no `docs/compound` entries from the engine, and no engine
  `docs/decisions`/`docs/plans` content.
* Skill references to `docs/compound`, `docs/plans`, `docs/memory`,
  `docs/decisions`, `docs/closure` are asserted to resolve against the **target
  workspace path**, not the packaged data directory — closing risk R2, which a
  naive dependency scan reads as required payload.

### AC6 — Install, update, and verification behavior preserved

* `autoharness home` and `autoharness version` behave identically pre/post change.
* `autoharness verify-workspace` passes on a workspace installed from the trimmed
  artifact, with **no new findings** versus the untrimmed baseline. Parity is
  asserted as a **set difference** against the recorded baseline finding set, not
  as an absolute "no findings" claim.
* **Upgrade path:** a workspace installed from v1.5.0 (untrimmed) upgraded to the
  trimmed build passes `verify-workspace` and is left with no orphaned engine
  files. Tested explicitly (R3).

Resolution behavior is **not** part of AC6. It is split into two disjoint
per-channel contracts below — see AC6a and AC6b.

### AC6a — Python-channel resolver contract (pip and clone/editable only)

*Split from the original AC6 in Orchestrator review-fix cycle 1 (finding 5).*

The original AC6 required `_DATA_DIR` resolution to work "in all three install
methods (pip, clone, plugin)". **That criterion was unsatisfiable.** The plugin
channel excludes `src/` and `pyproject.toml` (AC3, AC10), so a plugin-only install
has no importable `autoharness` package and therefore **no `_DATA_DIR` at all**.
AC6 demanded a Python resolver in a channel that by construction has no Python.

AC6a applies to exactly the environments where the `autoharness` Python
distribution is importable:

* `_DATA_DIR` (`cli.py:14-21`) resolves `templates/` and `schemas/` from the
  installed wheel's packaged data directory (**pip**).
* The clone/editable fallback to repo root resolves `templates/` and `schemas/`
  (**clone**).
* **Negative assertion A1:** the Python-channel contract requires **no**
  plugin-root artifact. Resolution succeeds with `plugin.json` and
  `.github/plugin/marketplace.json` absent from the environment.
* `_DATA_DIR` resolution **order** is invariant I1/I2 — observed here, never
  modified.

### AC6b — Plugin-root resolver contract (plugin channel only)

Applies to the plugin channel: no Python CLI on `PATH`, no `src/`, no
`pyproject.toml` in the payload.

* `templates/` and `schemas/` resolve relative to the **installed plugin root** —
  the directory the marketplace payload materializes — with no Python import
  involved.
* Version resolves from `plugin.json` / `.github/plugin/marketplace.json` per
  AC10, never from `pyproject.toml` or `src/autoharness/__init__.py`.
* **Negative assertion B1:** no import of the `autoharness` Python package occurs
  on this path; the contract holds with no `autoharness` distribution installed.
* **Negative assertion B2:** `src/`, `pyproject.toml`, and any `_DATA_DIR`-bearing
  package are **absent** from the resolved plugin payload. Their presence is a
  payload-composition regression, not a convenience.

**Disjointness (mandatory assertion).** AC6a and AC6b are disjoint by channel. No
environment is expected to satisfy both, and neither is a fallback for the other.
A dedicated test asserts this — it is what prevents the two contracts silently
re-merging into the old contradictory single claim.

### AC7 — Cross-environment behavior preserved, per channel

*Rewritten in Orchestrator review-fix cycle 1 (finding 5).* The original AC7
listed `vscode`, `copilot-cli`, `claude`, `codex` as a flat set of "supported
environments" while the corresponding task noted in prose that plugin-only
consumers cannot use three of them. Registration support is a function of
**(channel, environment)**, not of environment alone, and is asserted as such.

| Registration target | pip / clone (Python CLI present) | plugin-only (no Python CLI) |
|---|---|---|
| `register --vscode` / `setup-vscode` | Supported | **Not supported** *(pre-existing)* |
| `register --copilot-cli` | Supported | **Supported** — the plugin channel's own target |
| `register --claude` / `setup-claude` | Supported | **Not supported** *(pre-existing)* |
| `register --codex` / `setup-codex` | Supported | **Not supported** *(pre-existing)* |
| `autoharness verify-workspace` | Supported | **Not supported** *(pre-existing)* |

**Evidence for "pre-existing".** `docs/installation.md` states the plugin path
"gives Copilot CLI users built-in versioning and update management with no Python
dependency" and that "the Python CLI is still needed for `setup-vscode`,
`verify-workspace`, and registering with Claude Code or Codex." Excluding `src/`
from the plugin channel **preserves** that documented state; it does not create it.

**Negative assertions are mandatory, not prose.** For each *Not supported* cell the
test asserts the plugin-only environment fails **and** that the failure is
identical in kind to the v1.5.0 untrimmed baseline's failure in the same
environment. The assertion is *unchanged*, not merely *fails* — a test that only
asserts failure cannot distinguish a preserved limitation from a regression this
shipment introduced.

### AC8 — Drift guard

The composition test fails closed when a new top-level tracked path appears that
the manifest does not classify (R5), and reports measured file count and byte size
per channel so payload growth is observable in CI.

### AC9 — Cross-reference integrity in the shipped payload (Gate 4)

Constitution Quality Gate 4 requires that all referenced files, skills, and agents
exist. Trimming can break this **inside the delivered artifact** even while the
source tree stays intact.

* Gate 4 is run against the **built payload**, not the source tree.
* No shipped file may contain a relative reference to a path excluded by the
  manifest.
* Where a shipped engine file legitimately *mentions* an excluded path as
  instructional text (the `docs/compound/012-S-portability-scan-allow-list.md`
  pattern), it is recorded in an explicit `(file, reference)` allow-list rather
  than silently tolerated.

### AC10 — `{{AUTOHARNESS_VERSION}}` still resolves on a trimmed plugin install

`install-harness` **fails the install** if `{{AUTOHARNESS_VERSION}}` is
unresolved. Its resolution chain is: (1) `autoharness version` CLI; (2)
`autoharness_home/pyproject.toml` or `src/autoharness/__init__.py`; (3) for
plugin installs with no Python CLI, the plugin/package manifest version.

Because the plugin channel excludes `src/` and `pyproject.toml`, source (3) is the
**only** remaining resolver for plugin-only consumers.

* `plugin.json` and `.github/plugin/marketplace.json` — both carrying a concrete
  `version` — are mandatory payload members, asserted by name.
* Test: install from the trimmed plugin payload with no Python CLI on `PATH` and
  assert the manifest records a concrete version and never a literal
  `{{AUTOHARNESS_VERSION}}`.

### AC11 — Complete path classification (closes AC2 against this plan itself)

AC2 fails the build on any unclassified tracked path. The manifest must therefore
classify **every** tracked path, including these previously unenumerated ones:

| Path | Disposition | Reason |
|---|---|---|
| `start.ps1`, `start.sh` | **Exclude** | Dogfood *output* generated from `templates/scripts`, not engine payload |
| `.mcp.json` | Exclude | Workspace MCP config (generated output) |
| `autoharness.code-workspace`, `.vscode/**` | Exclude | Workspace editor config |
| `.gitattributes`, `.gitignore`, `.gitmodules` | Exclude | Repo-development config |
| `.markdownlint.json`, `.markdownlintignore` | Exclude | Lint config |
| `uv.lock` | Exclude | Dev lockfile |
| `pyproject.toml` | Wheel/sdist build input; **exclude** from plugin payload | Not a plugin runtime file |
| `.github/workflows/**` | Exclude | CI for this repo only |
| `.github/copilot/**` | Classify explicitly at implementation time | Unresolved at plan time |
| `.copilot/**`, `dist/**`, `.worktrees/**` | Exclude | Untracked/build output |
| `build_support/**` | **Exclude** | Build-time only; created by T5/T6. Shipping it would put the packaging rules inside the artifact they trim (P1-6) |
| `dist/plugin/**` | **Exclude** | Generated staging directory materialized only under spike branch (b); never payload |
| `.autoharness/payload-manifest.yaml` | **Exclude (by name)** | Covered by the `.autoharness/**` rule, but classified explicitly so the manifest's own exclusion is intentional rather than incidental |
| `schemas/payload-manifest/**` | **Include** | New versioned-mirror directory created by T2. Already covered by the existing `schemas/**` include (payload boundary line 188), but classified explicitly for the same reason as the rows above: it is a path this shipment creates, so its disposition must be intentional, not incidental |

The last three rows were **added in Orchestrator review-fix cycle 1 (finding 6)**;
the `schemas/payload-manifest/**` row was added in the same cycle by the
plan-review Learnings Researcher persona alongside the versioned-mirror
requirement.
`build_support/**` and `dist/plugin/**` are *created by this shipment*, so without
an explicit classification AC2 would fail the build on the shipment's own output —
the same self-contradiction class as P1-4.

`start.ps1` / `start.sh` are called out specifically: they read like engine files
but are generated harness artifacts for *this* workspace, and shipping them would
violate the very "generated output, not engine files" boundary in AC5.

## Test strategy

Tests must run against the **built artifact**, never the source tree — a source-tree
test cannot detect a packaging defect (R1).

**Red/green ownership is explicit (Orchestrator review-fix cycle 1, finding 2).**
`T3` authors the composition harness and **completes at red**; it neither can nor
may be completed by making any case pass, because at that moment the manifest, the
loader, and both channel wirings do not exist. Every case therefore names the task
that owns its **green** transition, so no case is orphaned and no task is asked to
go green on behaviour it does not build.

| Test | Asserts | Authored red by | Green owned by |
|---|---|---|---|
| `test_manifest_validates_against_schema` | AC1 | T3 | T4 |
| `test_every_tracked_path_is_classified` | AC11 | T3 | T4 |
| `test_start_scripts_and_workspace_config_excluded` | AC11 | T3 | T4 |
| `test_manifest_is_sole_source_of_payload_paths` | AC1 | T3 | T5 |
| `test_unclassified_tracked_path_fails_build` | AC2, AC8 | T3 | T5 |
| `test_payload_size_reported` | AC8 | T3 | T5 |
| `test_generated_tables_match_manifest` | AC2c | T3 | T6 |
| `test_generate_is_byte_deterministic_and_cross_platform` | AC2c | T3 | T6 |
| `test_wheel_excludes_backlogit_explicitly` | AC3 | T3 | T7 |
| `test_wheel_excludes_dev_directories` | AC3 | T3 | T7 |
| `test_wheel_contains_required_runtime_set` | AC4 | T3 | T7 |
| `test_docs_root_guides_only` | AC4 | T3 | T7 |
| `test_core_metadata_version_pins_preserved` | I4, V2 | T3 | T7 |
| `test_plugin_payload_excludes_dev_directories` | AC3 | T3 | T8 |
| `test_install_emits_only_generated_output` | AC5 | — | T9 |
| `test_skill_docs_refs_resolve_to_workspace_not_payload` | AC5, AC2d, R2 | — | T9 |
| `test_verify_workspace_parity_trimmed_vs_baseline` | AC6 | — | T10 |
| `test_upgrade_from_1_5_0_leaves_no_orphans` | AC6, R3 | — | T10 |
| `test_data_dir_resolution_pip_install` | AC6a, R4 | — | T11 |
| `test_data_dir_resolution_clone_editable` | AC6a, R4 | — | T11 |
| `test_plugin_root_resolves_templates_and_schemas` | AC6b | — | T11 |
| `test_plugin_version_resolves_from_plugin_manifest` | AC6b, AC10 | — | T11 |
| `test_channel_resolver_contracts_are_disjoint` | AC6a, AC6b | — | T11 |
| `test_register_phase_all_environments_python_channel` | AC7 | — | T12 |
| `test_plugin_only_register_copilot_cli_succeeds` | AC7 | — | T12 |
| `test_plugin_only_unsupported_targets_fail_the_same_way_as_baseline` | AC7 | — | T12 |
| `test_plugin_channel_excludes_python_cli_by_design` | AC7 | — | T12 |
| `test_gate4_crossrefs_intact_in_built_payload` | AC9, AC2d | — | T13 |
| `test_version_resolves_on_plugin_install_without_cli` | AC10 | — | T13 |
| `test_release_workflow_runs_payload_gate_before_publish` | AC2b | T3 | T14 |

Baseline capture (pre-change wheel inventory, `verify-workspace` **finding set**,
`/install-harness` output inventory, and the v1.5.0 plugin-only registration
failure modes) is a prerequisite of the parity, upgrade, and registration tests
and is produced by `T2`. A baseline that exists only in a transcript cannot be
asserted against; it is recorded durably.

## Security and reliability

* **Disclosure (primary):** `.backlogit/` carries 2,110 files of internal backlog
  records — titles, plans, decisions, review findings — currently published to
  every plugin consumer. Removal is the security core of this work.
* **Attack surface:** shipping `tests/` and `experiments/` delivers executable
  content with no consumer runtime role.
* **Integrity:** allowlist-by-default means a future directory of secrets or
  internal records is excluded unless explicitly added.
* **Fail-closed build:** an unclassified path fails the build rather than being
  silently published — the failure mode that produced the current state.
* **No secrets:** the manifest contains only path globs.

## Rollback

Each step is independently revertible.

1. **Trigger:** any AC6/AC7 failure, or a consumer install/upgrade regression.
2. **Immediate:** revert the `pyproject.toml` and `marketplace.json` wiring
   commits. Payload returns to the current untrimmed superset — degraded (bloated)
   but functional. The manifest, schema, and tests may remain in place inert.
3. **Version safety:** the trimmed payload ships under a **new version**; v1.5.0
   artifacts already published are untouched, so rollback never requires
   retracting a release.
4. **Consumer recovery:** reinstall/upgrade from the prior version restores the
   full payload; no consumer workspace state is mutated by this change.
5. **Point of no return:** none before publication. Publication is Ship/Orchestrator
   scope and out of this plan's authority.

## Sequencing

Placed **between `166-S` and `167-S`**: it does not supersede the reviewed
reliability/security portfolio `159-S`–`166-S`, but does supersede `167-S`
(documentation/record hygiene).

`159-S → 160-S → 161-S → 162-S → 163-S → 164-S → 165-S → 166-S → 168-S → 167-S`

## Task decomposition

Rows are in **execution order** and carry an explicit **Task ID** column
(Orchestrator review-fix cycle 1, finding 4). The previous table listed 10 rows
against 11 queued tasks, and the `(Tn)` back-references in the queue records had
drifted by one from `T9` onward. Task IDs and `T#` labels are now the single
coherent mapping in both directions.

Ordering satisfies Constitution Principle II (Test-First, NON-NEGOTIABLE): the
composition harness (`T3`) is authored and **observed red** before the manifest,
loader, and channel wiring it governs.

| T# | Task ID | Scope | Size | Complexity |
|---|---|---|---|---|
| T1 | `160.002-T` | **Spike:** establish the plugin-channel trimming mechanism | S | high |
| T2 | `160.001-T` | Baseline capture + payload-manifest schema (new, 1.0.0) | S | low |
| T3 | `160.005-T` | Fail-closed composition **RED harness** (completes at red) | M | medium |
| T4 | `160.003-T` | Author `.autoharness/payload-manifest.yaml` allowlist (full AC11 classification) | M | medium |
| T5 | `160.004-T` | Manifest loader/resolver + centralized target-workspace classifier, in `build_support/` | M | medium |
| T6 | `160.014-T` | Deterministic single-path generation command (`generate` / `--check`) | S | medium |
| T7 | `160.006-T` | Wire wheel packaging to the manifest, preserving I4 pins | M | medium |
| T8 | `160.007-T` | Wire plugin channel per the `T1` mechanism | M | high |
| T9 | `160.008-T` | Install-time payload boundary e2e (AC5, I3) | S | medium |
| T10 | `160.012-T` | Upgrade-path + `verify-workspace` parity e2e | S | medium |
| T11 | `160.013-T` | Channel resolver contract tests (AC6a Python, AC6b plugin-root) | S | medium |
| T12 | `160.009-T` | Cross-environment registration support matrix (AC7) | S | medium |
| T13 | `160.010-T` | Gate 4 cross-reference + version-resolution tests | S | medium |
| T14 | `160.015-T` | Unbypassable release-path payload gate (AC2b) | S | medium |
| T15 | `160.011-T` | Docs + CHANGELOG | S | trivial |

### Prerequisite DAG (machine-encoded)

Encoded as backlogit `blocks` dependency edges, not narrative ordering
(Orchestrator review-fix cycle 1, finding 2). A backlogit `dependencies:` entry
means *blocked by*.

| Task | Blocked by |
|---|---|
| `160.002-T` (T1) | — |
| `160.001-T` (T2) | — |
| `160.005-T` (T3) | `160.001-T` |
| `160.003-T` (T4) | `160.005-T` |
| `160.004-T` (T5) | `160.005-T`, `160.003-T` |
| `160.014-T` (T6) | `160.004-T` |
| `160.006-T` (T7) | `160.014-T` |
| `160.007-T` (T8) | `160.002-T`, `160.014-T` |
| `160.008-T` (T9) | `160.006-T`, `160.007-T` |
| `160.012-T` (T10) | `160.006-T`, `160.007-T` |
| `160.013-T` (T11) | `160.006-T`, `160.007-T` |
| `160.009-T` (T12) | `160.006-T`, `160.007-T` |
| `160.010-T` (T13) | `160.006-T`, `160.007-T` |
| `160.015-T` (T14) | `160.006-T`, `160.007-T` |
| `160.011-T` (T15) | `160.008-T`, `160.012-T`, `160.013-T`, `160.009-T`, `160.010-T`, `160.015-T` |

The graph is acyclic with two roots (`T1`, `T2`) and a single sink (`T15`).

**Red-before-green is enforced by the edges, not by prose.** `T3` is blocked only
by `T2` (the schema it validates against) and blocks `T4`, which blocks `T5`,
which blocks `T6`, which blocks both wiring tasks. Nothing that could turn a
composition case green can start until the harness that observes it red has
completed. `T3`'s completion criterion is *red observed and recorded*; it is
explicitly **not** blocked on green, which resolved the prior defect where `T3`
could not complete before wiring existed.

**T1 is a blocking spike (review finding P0-1).** The plan assumes the plugin
payload can be constrained, but the only observed mechanism is
`marketplace.json`'s `source: "."`, and no evidence establishes that Copilot CLI
supports an allowlist or ignore file for plugin sources. T1 must determine which
holds:

* **(a)** the marketplace source supports an exclusion/allowlist mechanism → wire
  it directly in T8; or
* **(b)** it does not → T8 instead builds a payload directory (`dist/plugin/`)
  from the manifest and repoints `source` at it, which changes T8's shape and
  adds a build step.

T8 must not begin until T1 resolves this. Proceeding on assumption (a) without
evidence risks discovering mid-implementation that the plugin half of the plan is
infeasible as written.

**Width isolation.** T7 (Python packaging), T8 (plugin channel), and T14 (CI
workflow) are separate tasks on separate surfaces with separate blast radii. T9
(install boundary), T10 (upgrade/parity), T11 (resolver contracts), T12
(registration), and T13 (integrity) are separated by failure domain — each has an
independent diagnosis path. T6 (codegen) is separated from T5 (resolution) because
serializing two output formats deterministically is a distinct deliverable from
resolving a manifest.

## Traceability

* Source stash: `E9E5E6CC`
* Deliberation: `docs/decisions/2026-09-03-minimal-copilot-plugin-payload-deliberation.md`
* Hardening: `## Plan Hardening` section below (appended in place per skill contract)
* Review: `## Plan Review` section below (appended in place per skill contract)

### Deferred scope (P-021 C2 captures)

Recorded as compliant capture-only stash entries with generated IDs during
Orchestrator review-fix cycle 1. Neither blocks this shipment.

| Ref | Capture | Residual risk if never built |
|---|---|---|
| `00C2B1F9` | **Content sensitivity assessment of already-published v1.5.0 artifacts.** P-021 C1 discrimination: assessing the sensitivity of already-published historical records is a security-analysis activity over a *different artifact set* (published release contents), not a change to the packaging contract this shipment defines. No acceptance criterion here can verify it. | **Low.** The disclosed records are development backlog metadata — titles, plans, review findings — not credentials. Removal is forward-only by design (I5 forbids retraction), and that framing is enforced as a wording constraint on T15's docs. |
| `F73A04A2` | **Compound learning capture** on allowlist-over-denylist packaging and "referenced ≠ required payload". P-021 C1 discrimination: a knowledge-library contribution whose surface is `docs/compound/`, which this shipment explicitly *excludes* from the payload and does not otherwise modify. It is also retrospective — it cannot be written truthfully until the shipment has shipped and its outcome is known. | **Low.** The insight is already recorded in this plan (AC2, AC2d, R2) and in the task records; the compound entry is a durability improvement, not the only record. |

## Plan Hardening

### Hardening signals present

| Signal | Present | Detail |
|---|---|---|
| Public API / schema / contract change | **Yes** | New `payload-manifest.schema.json`; packaging contract for both channels |
| Migration / irreversible step | **Yes (bounded)** | Consumer upgrade v1.5.0 → trimmed payload |
| External integration | **Yes** | PyPI publish pipeline; Copilot plugin marketplace |
| High blast radius | **Yes** | CLI distribution — a defect reaches every consumer install |
| Security / sensitive data | **Yes** | `.backlogit/` disclosure removal |

Hardening is required, and a bounded safety mode is **declared** in **H2** below.
The dominant risk is that **packaging defects do not fail
in CI — they fail at consumer install time**, after publication.

### Protected invariants

* **I1** — `autoharness_home` resolution order (env var → `autoharness home` →
  traversal → `~/.autoharness/`) is unchanged.
* **I2** — `templates/` and `schemas/` resolve under all three install methods.
* **I3** — `/install-harness` output into a target workspace is byte-identical
  pre/post change.
* **I4** — `core-metadata-version = 2.4` pins remain on **both** the wheel and
  sdist targets.
* **I5** — Already-published v1.5.0 artifacts are never mutated or retracted.

### Learnings consulted

* `docs/compound/2026-08-30-unpinned-hatchling-metadata-version-vs-pinned-publish-action.md`
  — **directly governing.** `pyproject.toml`'s `core-metadata-version = 2.4` pins
  exist because hatchling 1.32.0 defaults to Metadata-Version 2.5, which the
  SHA-pinned `pypa/gh-action-pypi-publish` action's bundled twine < 7.0.0 rejects.
  This plan edits the same file. **Any refactor of the build target tables MUST
  preserve both pins.** The learning also records that local `uvx twine check`
  *cannot reproduce* the failure — so a local build check is not sufficient
  evidence that publishing will succeed.
* `docs/compound/012-S-portability-scan-allow-list.md` — establishes the
  `(rule, file_glob)` allow-list precedent and the principle that engine files
  legitimately reference installation paths. Reinforces AC5/R2: a path *mentioned*
  by an engine file is not thereby *required payload*.
* `docs/compound/2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md`
  — three recorded occurrences of in-place schema mutation without a version bump.
  The new manifest schema is created at `1.0.0`; no existing schema is touched.
* `docs/compound/096-S-canonical-subagent-install-path.md` — subagent identities
  install under `.github/agents/subagents/`; that path must be inside the allowlist
  or reviewer personas break for consumers.

### Hardening decision — H2: required safety mode (`careful` + `freeze-scope`)

*Added in Orchestrator review-fix cycle 1 (finding 3).* The hardening signal table
above declares **high blast radius** — a defect reaches every consumer install —
yet the plan previously declared **no safety mode**, so nothing bounded what an
executing agent was permitted to touch. The mode below is **required**, bounded,
and **propagated verbatim into every executable task record**.

**Mode: `careful` + `freeze-scope`.**

**CAREFUL** — every change is behaviour-preserving outside the single declared
payload-composition change:

* `pyproject.toml`: build tables **only**. Project metadata, dependencies,
  version, entry points, and **both** `core-metadata-version = "2.4"` pins (I4)
  are asserted unchanged.
* `.github/workflows/release.yml`: **add one gate step only** (T14). No trigger,
  no `permissions:` block, no secret reference, and no pinned action SHA may be
  altered. A non-regression test asserts that set is byte-identical before and
  after.
* `.github/plugin/marketplace.json`: payload/source declaration **only**. Plugin
  name, version, publisher identity, and marketplace coordinates asserted
  unchanged.

**FREEZE-SCOPE** — `src/autoharness/` runtime behaviour is **read-only** for this
shipment. `_DATA_DIR` resolution *order*, `autoharness home`, and `autoharness
version` are protected invariants I1/I2: they are **observed** by the verification
tasks, never modified. The complete writable surface is exactly:

`.autoharness/payload-manifest.yaml`, `schemas/payload-manifest.schema.json`,
`build_support/**`, `tests/**`, `pyproject.toml` (build tables), 
`.github/plugin/marketplace.json` (payload declaration), 
`.github/workflows/release.yml` (gate step), and the three documents named in T15.

Anything outside that list is out of bounds. If a supported behaviour fails, the
fix belongs to the task that owns the surface, never to the task that observed it.

#### Bounded checkpoints

| Checkpoint | Applies to | Rule |
|---|---|---|
| **No-publish** | Every task | No `twine upload`, no `gh release create`, no `copilot plugin publish`, no marketplace push, no dispatch of `release.yml`'s publish path. Publication is Ship/Orchestrator scope (CP2). Recording a version in `CHANGELOG.md` is not publication. |
| **Rollback** | T7, T8, T14 | Before the task lands, record the exact pre-change bytes of the file it mutates (`pyproject.toml`, `marketplace.json`, `release.yml`). Rollback is a single-file restore returning the payload to the untrimmed superset — degraded but functional. |
| **Destructive-operation** | T8 (branch (b)), all verification tasks | Any step that materializes or cleans a payload directory writes **only** under a gitignored build-output path and **must never** delete, move, or overwrite a tracked file. Asserted by running materialization against a dirty working tree and verifying the tracked file set is unchanged. Scratch workspaces and simulated environments live under gitignored temporary paths and must not mutate the developer's real workspace, `~/.autoharness/`, installed interpreter, VS Code settings, Claude/Codex config, or Copilot CLI plugin registry. |
| **Published-artifact immutability** | T2, T10 | v1.5.0 artifacts used as baselines are already published and must never be mutated or retracted (invariant I5). |
| **Red-preservation** | T3 | T3 authors test files under `tests/` only. It must not author or modify the manifest, schema, `build_support/`, `pyproject.toml`, `marketplace.json`, or `release.yml` — doing so would make its own cases green and destroy the red observation. |

#### Point of no return

None inside this shipment. Publication is the only irreversible step and is
outside this plan's authority (see Rollback §5 and CP2).

### Hardening decision — H1: generated-and-asserted, not a dynamic build hook

Hatchling's `force-include` is **static TOML**. It cannot read
`.autoharness/payload-manifest.yaml` at build time without a custom
`hatch_build.py` build hook. Two options:

* **(a) Custom hatchling build hook** — dynamic, but adds a build-time code path
  and a new failure mode into the release pipeline that the pinned-toolchain
  learning above shows is the hardest place to debug.
* **(b) Manifest as source of truth; `pyproject.toml` include table generated from
  it and asserted equal by test** — no build-time machinery, same fail-closed
  guarantee, failure surfaces in CI rather than at publish.

**Adopt (b).** Rationale: *simplicity supersedes complexity*, and it keeps the
release pipeline's build path byte-for-byte as risky as it is today and no more.
`T5`/`T6` are scoped to option (b); a build hook is explicitly out of scope. `T14` makes the resulting assertion unbypassable in the release path (AC2b).

### Reinforced verification

* **V1 — Build-artifact inspection, not source-tree inspection.** All composition
  assertions unpack the actual built wheel and the resolved plugin payload. A
  source-tree assertion cannot detect a packaging defect (R1).
* **V2 — Publish-toolchain check is not satisfied locally.** Per the hatchling
  learning, a local `twine check` is insufficient. Metadata validation must run
  against the **same pinned action toolchain** used by `release.yml`, or be
  explicitly recorded as unverified-until-release. Add an assertion that both
  `core-metadata-version` pins survive the refactor (I4).
* **V3 — Upgrade orphan scan.** Install v1.5.0 into a scratch workspace, upgrade to
  the trimmed build, then enumerate residual engine files and assert the set is
  empty or explicitly expected (R3).
* **V4 — Negative test for the allowlist.** Inject a synthetic unclassified tracked
  path and assert the build **fails**. A fail-closed guard that is never observed
  failing is not known to be fail-closed (AC2/AC8).
* **V5 — Install parity baseline.** Capture `/install-harness` output from the
  untrimmed build first; assert byte-identical output from the trimmed build (I3).

### Operator checkpoints

* **CP1** — Before `T7`/`T8` wiring lands: operator reviews the resolved allowlist
  and confirms no required path is missing.
* **CP2** — Before publication (Ship/Orchestrator scope, outside this plan):
  release-pipeline dry run confirming metadata pins intact.

### Risky actions

| Action | Risk | Mitigation | Rollback state |
|---|---|---|---|
| Rewrite `pyproject.toml` build tables | **High** — breaks publish | Preserve I4 pins; assert by test; V2 | Revert file; payload returns to untrimmed |
| Add gate step to `release.yml` | **High** — a malformed workflow blocks all releases | Structural test (AC2b) + byte-identity non-regression assertion on triggers/permissions/secrets/SHAs | Revert file; release path returns to current behaviour |
| Constrain `marketplace.json` payload | **Medium** — breaks plugin install | V1 + CP1 | Revert to `source: "."` |
| Materialize `dist/plugin/` (branch (b)) | **Medium** — a build step that writes to the tree | Gitignored output path only; never deletes a tracked file; asserted against a dirty working tree | Delete the generated directory; revert `source` |
| Exclude `docs/` history | **Low** — false-positive refs | AC5 test; allow-list learning; AC2d single classifier | Re-add to manifest include |
| Exclude `.backlogit/` | **Low** runtime, **high** value | Explicit named test (AC3) | Re-add to manifest include |

### Review-gate capability risks

No reviewer subagent dispatch surface is exposed in the current session, and no
`agent-engram` / `graphtor-docs` retrieval tools are available. Plan review must
therefore expect `dispatch_mode: single-agent-declared-degradation` with full
inline persona coverage, and must record the P-012 degraded conditions rather than
silently narrowing persona coverage.

### Residual risk accepted

Publish-time metadata compatibility (V2) cannot be fully verified before release
because the failure reproduces only under the pinned CI toolchain. Accepted and
carried to CP2 as an explicit pre-publication check, not silently absorbed.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

### Capability declaration (P-012)

| Capability | Status |
|---|---|
| Reviewer subagent dispatch | `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass` |
| Model-specific reviewer routing | `TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass` |
| Indexed knowledge retrieval (`agent-engram`) | `TOOL_DEGRADED: engram — declared fallback: file-based grep/view` |
| Documentation retrieval (`graphtor-docs`) | `TOOL_UNAVAILABLE: graphtor-docs — declared fallback: file-based docs search` |
| Intercom visibility | `TOOL_DEGRADED: agent-intercom — operator visibility reduced` |

No reviewer subagent dispatch surface is exposed in this session. Every selected
persona was covered **inline** using the Persona Rubric Adapter focus, and all
findings are normalized to the P0–P3 scale. No persona was skipped. Anchor
cross-model routing was unavailable; degradation is declared, not silent.

### Personas applied

| Persona | Trigger | Findings |
|---|---|---|
| Constitution Reviewer | Always-on | P1-2, P1-3 |
| Python Reviewer | Always-on | P2-7 |
| Scope Boundary Auditor | Always-on | P0-1, P1-4 |
| Learnings Researcher | Always-on | P2-9 |
| Architecture Strategist | Dependency chains, module boundaries | P0-1, P1-6 |
| Security Lens Reviewer | Sensitive-data disclosure in payload | P2-8 |
| Agent-Native Parity Reviewer | Payload delivers agents/skills to consumers | P1-5 |

### Cycle 1 findings

**P0-1 — Plugin-channel trimming mechanism is unverified.** *(Scope Boundary
Auditor, Architecture Strategist)* The plan directs "constrain plugin payload to
the manifest", but the only observed mechanism is `marketplace.json`'s
`source: "."`, and nothing establishes that Copilot CLI supports an exclusion or
allowlist for plugin sources. If it does not, the plugin half of the plan is
infeasible as written and requires a build-produced payload directory that no task
created. Blocks harvest.
**Remediation:** added blocking spike **T1** with explicit branch (a)/(b) outcomes;
`T7` may not begin until `T1` resolves. **Resolved.**

**P1-2 — Task order violates Test-First (Constitution II, NON-NEGOTIABLE).**
*(Constitution Reviewer)* Wiring tasks preceded the composition guard that governs
them.
**Remediation:** reordered — composition tests (`T5`) now land before wheel (`T6`)
and plugin (`T7`) wiring. **Resolved.**

**P1-3 — Gate 4 cross-reference integrity not asserted on the built payload.**
*(Constitution Reviewer)* Trimming `docs/` can break references *inside the
delivered artifact* while the source tree remains valid. No AC covered this.
**Remediation:** added **AC9** (Gate 4 run against the built payload, with an
explicit `(file, reference)` allow-list following the `012-S` precedent) and test
`test_gate4_crossrefs_intact_in_built_payload`. **Resolved.**

**P1-4 — Plan contradicted its own AC2.** *(Scope Boundary Auditor)* AC2 fails the
build on any unclassified tracked path, yet the payload boundary omitted ~12
tracked paths (`start.ps1`, `start.sh`, `.mcp.json`, `uv.lock`,
`autoharness.code-workspace`, `.gitattributes`, `.gitignore`, `.gitmodules`,
`.markdownlint*`, `.github/workflows/**`, `.github/copilot/**`). The plan would
have failed its own gate.
**Remediation:** added **AC11** with a complete disposition table. Notably
`start.ps1`/`start.sh` are *generated dogfood output*, not engine payload —
shipping them would violate AC5. **Resolved.**

**P1-5 — `{{AUTOHARNESS_VERSION}}` resolution unaddressed.** *(Agent-Native Parity
Reviewer)* `install-harness` **fails the install** when this variable is
unresolved. Its chain is CLI → `pyproject.toml`/`__init__.py` → plugin manifest.
The plugin channel excludes the first two sources, making the plugin manifest the
sole resolver — a dependency the plan never stated or protected.
**Remediation:** added **AC10** making `plugin.json` and `marketplace.json`
mandatory payload members asserted by name, plus a no-Python-CLI install test.
**Resolved.**

**P1-6 — Build-time logic placed inside the runtime payload.** *(Architecture
Strategist)* `src/autoharness/packaging.py` would ship the packaging rules inside
the artifact they trim — a coupling inversion contradicting the plan's own
minimalism goal.
**Remediation:** relocated to `build_support/`, excluded from the payload.
**Resolved.**

**P2-7 — Loader error handling unspecified.** *(Python Reviewer)* Behavior on a
malformed or schema-invalid manifest is undefined; it must fail closed with a
specific exception rather than degrading to a permissive payload. Recorded as a
backlog follow-up on `T5` (`160.004-T`); not harvest-blocking.

**P2-8 — Forward-only disclosure remediation.** *(Security Lens Reviewer)* Removing
`.backlogit/` does not un-publish it: v1.5.0 artifacts already distributed contain
those 2,110 files and remain public (invariant I5 correctly forbids retraction).
The plan should not imply retroactive remediation. A content sensitivity
assessment of what was already published is recorded as a follow-up. Not
harvest-blocking — the records are development backlog metadata, not credentials.
*Cycle 1 update:* the assessment was a required deliverable on `T15` with no
P-021 disposition; it is now captured as deferred entry `00C2B1F9`. The in-scope
forward-only **wording constraint** on `T15`'s documentation is retained.

**P2-9 — Compound learning not scheduled.** *(Learnings Researcher)* Capture a
`docs/compound/` learning on completion (allowlist-over-denylist packaging;
"referenced ≠ required payload"). Follow-up. *Cycle 1 update:* removed from `T15`
as a required deliverable and captured as deferred entry `F73A04A2`.

**P3-10 — Target version for the trimmed payload unspecified.** Advisory;
resolved at release time by Ship/Orchestrator.

### Cycle 2 verification

All six P0/P1 findings remediated in place and re-verified against the amended
plan: P0-1 → `T1` spike gate; P1-2 → task reorder; P1-3 → AC9; P1-4 → AC11;
P1-5 → AC10; P1-6 → `build_support/` relocation.

No new P0/P1 findings. Two review cycles used of the three-cycle limit.
P2-7, P2-8, and P2-9 are accepted as recorded follow-ups per the severity scale
(P2 = backlog follow-up, does not block harvest).

**Gate: PASS — plan is harvest-ready.**

### Review-fix cycle 1 (Orchestrator local review of `35c081d5`)

The Orchestrator's local review of the publication branch returned **BLOCKED**.
Seven of its twenty findings targeted this plan. All seven are remediated in
place; the amendments are marked inline above at each affected section.

| Finding | Verdict | Remediation |
|---|---|---|
| **2 — TDD/DAG not machine-enforced** | **Legitimate P0** | `T3` (`160.005-T`) rewritten to *red-harness-completion* semantics — it completes when every case is authored and **observed red**, and is explicitly not blocked on green. Green ownership is assigned per case to `T4`/`T5`/`T6`/`T7`/`T8`/`T14` in the Test strategy table, so no case is orphaned. The full prerequisite DAG is encoded as backlogit `blocks` edges (see *Prerequisite DAG*), not narrative ordering. This also resolved the defect that `T3` could not reach green before wiring existed. |
| **3 — High blast radius, no safety mode** | **Legitimate P0** | **H2** declares a bounded `careful` + `freeze-scope` mode with an explicit writable-surface allow-list and five bounded checkpoints (no-publish, rollback, destructive-operation, published-artifact immutability, red-preservation). The mode is propagated verbatim into all 15 executable task records. |
| **4 — Decomposition drift (10 plan rows vs 11 queued tasks)** | **Legitimate P1** | Confirmed: harvest had split plan-`T8` into two tasks, shifting every back-reference from `T9` onward by one, with `160.011-T` pointing at a nonexistent `T11`. The decomposition table is rewritten in **execution order** with an explicit **Task ID** column, and every task's `(Tn)` back-reference is corrected through official `backlogit update` operations. Mapping is now coherent in both directions. |
| **5 — Channel contract contradictions** | **Legitimate P0** | Confirmed: AC6 required Python `_DATA_DIR` resolution in the plugin channel, which by construction has no Python. AC6 is split into **AC6a** (Python channel: pip + clone/editable) and **AC6b** (plugin-root resolver), each with negative assertions, plus a mandatory **disjointness** assertion preventing re-merge. AC7 is rewritten as an explicit **channel × environment support matrix** whose *Not supported* cells assert the limitation is **unchanged** versus the v1.5.0 baseline, not merely present. |
| **6 — Payload/build correctness** | **Legitimate P1** | Four fixes. (a) `build_support/**`, `dist/plugin/**`, and the manifest itself added to AC11 — they are created by this shipment and would otherwise fail its own AC2, the same self-contradiction class as P1-4. (b) **AC2b** makes the fail-closed promise enforceable in the real release path via an unbypassable in-job prerequisite step, correctly scoped to `release.yml`'s actual single-job structure. (c) **AC2c** defines one deterministic, cross-platform, single-path generation command with a drift-detecting `--check`. (d) **AC2d** centralizes target-workspace path classification behind one manifest key and one function, replacing per-reference duplication. |
| **7 — `160.008-T` combined too many failure domains** | **Legitimate P1** | Split into `160.008-T` (install boundary), `160.012-T` (upgrade/parity), and `160.013-T` (resolver contracts). Applying the same two-axis gate to the findings-6 additions also split `160.004-T` → `160.014-T` (codegen) and `160.006-T` → `160.015-T` (CI gate), preserving width isolation between packaging, plugin, and CI surfaces. Task count is now **15**; shipment `168-S` membership, dependencies, sizing, and this plan's tables are all updated to match. |
| **8 — `160.011-T` required out-of-scope knowledge work** | **Legitimate P2** | Confirmed: P2-8 and P2-9 were required deliverables with no compliant P-021 disposition. Both removed from the task and captured as `00C2B1F9` and `F73A04A2` with C1 discrimination recorded (see *Deferred scope*). The **in-scope** portion of P2-8 — the forward-only wording constraint on the docs T15 itself writes — is retained, because that *is* same-contract-surface work. |

Three review-fix cycles remain available; one is used.

**Gate after cycle 1: PASS — 15 tasks, DAG acyclic, safety mode declared and
propagated, all channel contracts disjoint and asserted.**
