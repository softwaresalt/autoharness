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

**All three** autoharness distribution channels — **wheel, sdist, and plugin** —
deliver the entire development repository.
`.github/plugin/marketplace.json` declares `source: "."` (repo root, 3,238 tracked
files / ~18 MB); `pyproject.toml` force-includes all 642 `docs/` files into
every wheel; and the **sdist** target declares no payload table at all, so
hatchling's default sweep packages the working tree wholesale — the most
disclosing of the three. `.backlogit/` — 2,110 files of this workspace's own
backlog records, 65% of all tracked files — is shipped to consumers through every
one of them with no runtime role.

> **Channel-count correction (extended review-fix cycle 4, finding 11).** This
> paragraph previously read "Both autoharness distribution channels", counting
> **two**. That count was accurate when the deliberation was written and became
> stale in plan review-fix cycle 2 (finding 3), which added **AC3b** and the
> `T7b` sdist task on the finding that the sdist is a *separate, untrimmed,
> disclosure-critical* channel. The authoritative count throughout this plan and
> its current decision is **three: wheel, sdist, plugin**. Historical two-channel
> text is preserved **only** where it is explicitly marked as a record of an
> earlier moment (see the deliberation's *Options considered* section); it is not
> preserved in any statement that reads as currently authoritative.

Full evidence in the source deliberation.

## Goal

Package and install only the minimum runtime set, from a **single declarative
allowlist manifest** shared by **all three channels — wheel, sdist, and plugin** —
enforced by a fail-closed composition test — preserving install, update,
verification, and cross-environment behavior.

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
| `pyproject.toml` (wheel target) | Replace ad-hoc `force-include` with manifest-derived includes |
| `pyproject.toml` (**sdist target**) | Add manifest-derived `include`/`exclude`. **Today the sdist target declares only `core-metadata-version`, so hatchling's default sweep ships the entire project — `.backlogit/`, `tests/`, `experiments/`, all of `docs/`.** `release.yml` builds with `uv build` and publishes `dist/*`, so the sdist is published to PyPI *and* attached to the GitHub release. Trimming only the wheel leaves the disclosure surface fully intact (**review-fix cycle 2, finding 3**) |
| `.github/plugin/marketplace.json` | Constrain plugin payload to the manifest |
| `plugin-payload/` *(new, tracked — only under spike branch (b))* | Committed, generated plugin payload tree that `source` can actually point at. **Never `dist/plugin/`** — `dist/.gitignore` contains `*`, so a consumer checkout has no such directory (**review-fix cycle 2, finding 5**) |
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
  `schemas/payload-manifest.schema.json`, and declares `include`, `exclude`,
  `target_workspace_paths`, `generated_output_roots`, and per-channel overlays for
  the **closed three-channel set `{wheel, sdist, plugin}`** *(corrected in
  review-fix cycle 3, finding 4 — cycle 2 added the sdist channel everywhere
  except this criterion, which still read "`wheel`, `plugin`"; a criterion naming
  two of three channels cannot accept a three-channel manifest)*.
* The channel enum is **closed** and identical in every surface that names it:
  this criterion, AC2b, AC2c, AC3, AC3b, AC11, the schema (`T2b`), the manifest
  (`T4`), the resolver (`T5`), the generation command (`T6`), and the release gate
  (`T14`). `all` means **wheel, sdist and plugin** — never a subset. The closure is
  machine-checked by `test_manifest_validates_against_schema` (the schema's channel
  enum is closed, so a fourth or missing channel fails validation) and by
  `test_release_gate_covers_all_three_channels` (the gate's resolved channel set
  must equal the full three), so the set cannot drift back to two in one surface.
* Neither `pyproject.toml` (wheel target **or** sdist target) nor
  `marketplace.json` contains a payload path that is not derivable from the
  manifest.

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
  publish step index. The build step is `uv build`, which produces **wheel and
  sdist together**, and the publish step ships `dist/*` — so the gate must precede
  the single command that produces every published artifact.
* It carries **no** `continue-on-error: true` and **no** `if:` expression of any
  kind — no `always()`, no dispatch-input bypass.
* **All three channels are covered** *(review-fix cycle 2, finding 3)*: `--channel
  all` means `wheel`, `sdist`, and `plugin`. `test_release_gate_covers_all_three_channels`
  asserts the gate's channel argument resolves to the complete set, so a channel
  added later cannot silently fall outside the gate.
* `test_release_workflow_runs_payload_gate_before_publish` parses `release.yml`
  **structurally** and asserts the ordering and bypass properties, so a later edit
  that reorders, conditions, or soft-fails the step is caught by the test suite
  rather than discovered at publish time.

If a future change splits `release.yml` into multiple jobs, the gate should
migrate to a separate job with a `needs:` edge. That restructuring is **not** part
of this shipment.

### AC2c — One deterministic generation command, one source of truth

*Added in Orchestrator review-fix cycle 1 (finding 6).* Because H1 makes the
static `pyproject.toml` include table and the `marketplace.json` payload
declaration **derived** artifacts, they become a second source of truth unless
regeneration is deterministic, single-pathed, and drift-detecting.

* Exactly one command generates and re-generates every channel table:
  `python -m build_support.payload generate --channel {wheel|sdist|plugin|all}`, with
  `--check` re-deriving and comparing without writing and exiting non-zero on
  drift. `all` means **wheel, sdist and plugin** — the enum is closed and the
  release gate uses `all` (AC3b).
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

* The manifest declares **one** `target_workspace_paths` key. The prefix values
  live **only** there.
* One function, `build_support.payload.classify_target_workspace_path(path)`, is
  the sole decision point and reads that single key.
* AC5's skill-reference test, AC9's Gate 4 allow-list, and the R2 rule all **call
  that function**. Re-listing the prefixes at any call site is prohibited.
* **Scope of the single-occurrence test (corrected in review-fix cycle 2, finding
  15; fixture carve-out added in extended review-fix cycle 4, finding 9).** The
  test asserts **exactly one authored occurrence across executable and
  configuration surfaces** — `build_support/**`, `src/**`, `tests/**`
  **excluding `tests/fixtures/**`**,
  `pyproject.toml`, `.github/plugin/marketplace.json`, `.github/workflows/**`, and
  the manifest itself — with the manifest's `target_workspace_paths` key being
  that one occurrence. Documentation, plans, deliberations, and backlog records
  are **outside the test's surface**. The named case is
  `test_target_workspace_prefixes_have_exactly_one_authored_occurrence`
  (RED-FIRST, authored `T3a`, green owner `T4`).

  **Why `tests/fixtures/**` is carved out, and what replaces the guarantee it
  would otherwise give.** `T2a`'s baseline fixtures under
  `tests/fixtures/payload-baseline/**` are *recorded observations of what the
  payload contained*, so they may legitimately contain a target-workspace prefix
  as **data**. With `tests/**` scanned wholesale, `160.018-T` simultaneously
  permitted fixtures to name a prefix and the scan forbade a second occurrence
  anywhere in `tests/**` — a direct contradiction in which recording an accurate
  baseline would fail the drift test. Carving the fixture tree out of the *scan*
  does **not** weaken the guarantee, because the guarantee is about **derivation**,
  not about textual appearance. It is preserved by a **second, explicit
  assertion** in the same case: **no module under `build_support/**` or `src/**`
  may obtain target-workspace prefixes from a fixture, a test constant, or any
  source other than `classify_target_workspace_path` reading the manifest key.**
  A fixture literal is inert data; a fixture literal that something *executable*
  reads is a second source of truth, and that — not its existence — is the drift
  this rule exists to stop. Both halves are asserted, so the carve-out is tested
  rather than assumed.

  The earlier "exactly one authored occurrence in the repository" wording was
  **unsatisfiable by construction**: this plan, the deliberation, and the task
  record each necessarily enumerate the prefixes in order to specify the rule, so
  the contract failed the moment it was written down. Narrowing the surface to the
  places where duplication actually causes drift keeps the guarantee — one
  executable source of truth — while letting prose explain it.
* **Prose refers symbolically.** Outside the manifest, plan and task text names the
  key `target_workspace_paths`, not its values, wherever the values are not the
  subject being specified.

### AC3 — Development artifacts are excluded from all three channels

Built wheel, built **sdist**, and resolved plugin payload contain **zero** files under:
`.backlogit/`, `tests/`, `experiments/`, `references/`, `.githooks/`, `.vscode/`,
`.claude/`, `.engram/`, `.graphtor/`, and the `docs/` history subdirectories
(`archive`, `plans`, `memory`, `decisions`, `closure`, `compound`, `reviews`,
`spikes`, `audits`, `exec-plans`, `telemetry`, `design-docs`, `research`,
`deferred`, `product-specs`).

`.backlogit/` exclusion is asserted **explicitly and by name** in its own test
case — it is the largest disclosure surface and must not depend on a glob.

### AC3b — The sdist is trimmed by the same manifest, not left as a bypass

*Added in review-fix cycle 2 (finding 3).* `[tool.hatch.build.targets.sdist]`
currently declares **only** `core-metadata-version = "2.4"`. With no `include` or
`exclude`, hatchling's default sweep packages the whole project directory. The
release job builds **wheel and sdist** (`uv build`) and publishes **`dist/*`** —
to PyPI *and* as GitHub release assets. A wheel-only trim therefore removes
nothing: every file this shipment exists to withhold still ships, in the sdist,
from the same command, in the same release.

* The sdist target carries a **manifest-derived** `include`/`exclude` table,
  generated by the same single command (`generate --channel sdist`) and asserted
  equal, exactly as the wheel table is.
* AC3's exclusion set and AC4's runtime set apply to the sdist **by name**, not by
  implication: `test_sdist_excludes_backlogit_explicitly`,
  `test_sdist_excludes_dev_directories`, `test_sdist_contains_required_runtime_set`.
* **Byte-size and disclosure check:** the built sdist's measured file count and
  byte size are reported per channel (AC8) and a dedicated case asserts the sdist
  contains **zero** files under the AC3 exclusion set. Size reduction is reported;
  the disclosure assertion is what gates.
* **Metadata pin preservation (I4):** `core-metadata-version = "2.4"` must survive
  on the sdist target across the refactor. This is the pin most at risk, because
  the sdist target's *only* current key is that pin — a table rewrite that
  replaces rather than extends it drops the pin silently and breaks publishing.
* **Release-path coverage:** the AC2b gate step runs
  `generate --channel all --check`, where `all` covers `wheel`, `sdist`, and
  `plugin`. A gate that checks two of three channels is not a gate for the third.

### AC3c — The plugin payload source must be fetchable from a consumer checkout

*Added in review-fix cycle 2 (finding 5).* Spike branch (b) previously repointed
`marketplace.json`'s `source` at `dist/plugin/`. **`dist/.gitignore` contains
`*`**, so nothing under `dist/` is tracked and a consumer cloning or fetching this
repository has no such directory. That branch published a payload declaration
pointing at a path that does not exist for the consumer — an install failure, not
a trim.

* `source` MUST resolve to a path that is **present in a consumer-fetchable
  checkout** of this repository.
* Branch (b) therefore materializes a **tracked, committed, generated** payload
  tree at `plugin-payload/` — same "generated-and-asserted" shape H1 already
  adopts for the wheel table: produced by the one generation command, committed,
  and drift-detected by `generate --check` in the release gate.
* **Prohibited:** pointing `source` at any gitignored, untracked, or
  build-output-only path, and assuming any marketplace exclusion, ignore-file, or
  filtering behavior that spike `T1` has not evidenced.
* If neither branch (a) nor a tracked generated tree is acceptable, `T1`
  **halts to the operator** with the evidence and the alternatives; it does not
  invent a mechanism.
* `plugin-payload/**` is classified in AC11 under the **generated-output-root**
  semantics defined in **AC3d**: it is **excluded from the classifier's input
  domain** in *every* channel — including the plugin channel — while remaining the
  directory the plugin payload is materialized **into** and the directory
  `marketplace.json`'s `source` publishes. Input and output are different roles and
  the manifest states them with different keys.

### AC3d — Generated output roots are excluded from classifier input, not from publication

*Added in review-fix cycle 3 (finding 9).* Cycle 2 classified `plugin-payload/**`
as **"INCLUDE in the plugin channel"**. That is a **recursion defect**, not a
wording nit: the plugin channel's generator *materializes into that same tree*, so
an `include` rule naming it makes the generator's own output part of its next
run's input. The second run resolves `plugin-payload/**` as source and writes it
**inside** `plugin-payload/`, producing `plugin-payload/plugin-payload/...`; the
third run nests again. `generate --check` then reports drift that regenerating
cannot clear, because every regeneration deepens the tree — **permanent drift**
that fails the release gate on every subsequent run. Prose saying "excluded from
itself so generation cannot recurse" contradicted the same row's `include`
disposition; the manifest must express the distinction structurally, not
narratively.

The manifest therefore declares **two different things with two different keys**:

* **Source classification (`include` / `exclude` / per-channel overlays).** These
  rules classify **tracked source paths** — the classifier's **input domain**.
  `plugin-payload/**` is **never** an `include` rule in any channel.
* **Generated output roots (`generated_output_roots`).** A closed list naming, per
  channel, the directory the resolved payload is **materialized into**.
  `plugin-payload/` is the **plugin channel's** output root. This key declares an
  **output destination**, never an input classification.

Binding semantics:

1. **Input self-exclusion (fail-closed against recursion).** Before any
   classification runs, every path under a declared `generated_output_roots` entry
   is **removed from the tracked-path enumeration**. It is therefore neither
   "classified" nor "unclassified", so **AC2's unclassified-path build failure is
   not triggered by generated content** and the generator can never read its own
   output. This removal is unconditional and applies to **all three channels**, so
   the wheel and sdist cannot pick the tree up either — it is a derived duplicate
   of payload content, not source.
2. **Output-root emptiness is not a payload.** The plugin channel's payload is the
   resolved **source** file set. The output root is where that set is written. A
   channel whose resolved source set is empty produces an empty output root; it
   does not fall back to "ship the output root's existing contents".
3. **Publication is unchanged.** `plugin-payload/` remains **tracked and
   committed**, and `marketplace.json`'s `source` points at it, so the strategy
   stays publishable from a plain repository checkout (AC3c). Excluding a directory
   from *classifier input* has no effect on whether it is *published* — those are
   independent properties, and conflating them is what produced the cycle-2 row.
4. **Required assertions** (green owners in parentheses):
   * `test_generated_output_root_excluded_from_classifier_inputs` — no path under
     any declared output root appears in **any** channel's resolved input set, and
     the AC2 unclassified-path check does not flag generated content (**T5**).
   * `test_plugin_generation_is_idempotent` — running `generate --channel plugin`
     twice against a scratch target yields a **byte-identical** tree and an
     identical resolved input set on both runs (**T6**).
   * `test_plugin_payload_conforms_to_the_selected_strategy` — **branch-aware**
     (cycle 4, finding 6). Under **branch (b)**: the committed tree contains **no**
     nested directory named `plugin-payload`, and `generate --channel plugin
     --check` reports **no drift** immediately after a regeneration — this is the
     assertion that would have failed on the cycle-2 classification, and it is what
     proves the drift is not permanent. Under **branch (a)**: **no** output tree is
     materialized **and** the natively-filtered payload equals the manifest-derived
     plugin set. The strategy must be **declared**; an undeclared strategy fails
     the case (**T8**).
5. **Prohibited:** adding `plugin-payload/**` (or any declared output root) to an
   `include` rule in any channel; relying on ordering between rules to "win" the
   exclusion; or implementing the exclusion inside the generator instead of the
   resolver, which would leave every other consumer of the resolver — the AC2
   classification check, the size report, `--check` — still seeing the output tree
   as input.

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
classify **every** tracked path in the classifier's **input domain**, including
these previously unenumerated ones. The input domain is the tracked-path set
**minus** every path under a declared `generated_output_roots` entry (**AC3d**);
generated output is neither classified nor unclassified, so it never trips AC2.

| Path | Disposition | Reason |
|---|---|---|
| `start.ps1`, `start.sh` | **Exclude** | Dogfood *output* generated from `templates/scripts`, not engine payload |
| `.mcp.json` | Exclude | Workspace MCP config (generated output) |
| `autoharness.code-workspace`, `.vscode/**` | Exclude | Workspace editor config |
| `.gitattributes`, `.gitignore`, `.gitmodules` | Exclude | Repo-development config |
| `.markdownlint.json`, `.markdownlintignore` | Exclude | Lint config |
| `uv.lock` | Exclude | Dev lockfile |
| `pyproject.toml` | Wheel/sdist **build input**; include in the **sdist** payload (a source distribution without its build definition is not buildable); **exclude** from the wheel and plugin payloads | Not a runtime file, but it *is* the sdist's build definition |
| `.github/workflows/**` | Exclude | CI for this repo only |
| `.github/copilot/**` | Classify explicitly at implementation time | Unresolved at plan time |
| `.copilot/**`, `dist/**`, `.worktrees/**` | Exclude | Untracked/build output |
| `build_support/**` | **Exclude** | Build-time only; created by T5/T6. Shipping it would put the packaging rules inside the artifact they trim (P1-6) |
| `plugin-payload/**` | **Generated output root (AC3d)** — removed from the classifier's **input domain** in **all three** channels; **not** an `include` rule anywhere; **is** the plugin channel's materialization target and the published `source` | Tracked generated tree created only under spike branch (b) (AC3c). Declared in `generated_output_roots`, not in `include`/`exclude`, so the generator can never read its own output and cannot nest (`plugin-payload/plugin-payload/…`). Being removed from the input domain means AC2's unclassified-path failure is not triggered by generated content. Being **tracked** is what keeps `source` consumer-fetchable |
| `dist/plugin/**` | **Exclude** — and **prohibited as a `source` target** | Covered by the `dist/**` rule. `dist/.gitignore` is `*`, so nothing here is tracked or consumer-fetchable; AC3c forbids pointing `marketplace.json`'s `source` at it. Retained as an explicit row so the prohibition is visible where the classification lives |
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

### Every case is classified, and the class determines the required observation

*Rewritten in review-fix cycle 2 (finding 1).* Cycle 1 required **every** case to
be observed red before implementation. That was wrong in two directions at once,
and both errors corrupt the evidence:

* Several cases **legitimately start green**. The wheel's `force-include` table
  already lists only `templates`, `schemas`, four `.github/` subtrees, two
  instruction files, `docs`, and `AGENTS.md`, so `.backlogit/`, `tests/`, and
  `experiments/` are *already* absent from the wheel. Both
  `core-metadata-version = "2.4"` pins already exist. Demanding a red observation
  on these forces an author to either fabricate a failure or weaken a correct
  assertion until it breaks — manufacturing red is worse than no red, because it
  destroys the signal for the cases where red is real.
* Several cases had **no red owner at all** — the install, upgrade, resolver,
  registration, and integrity families were authored *after* the wiring they
  govern, which is the defect Test-First exists to prevent.

Every case therefore carries exactly **one declared class**, and the class fixes
what must be observed and when:

| Class | Required observation | Meaning |
|---|---|---|
| **RED-FIRST** | Observed **failing** before its green owner starts, then observed passing after. Both observations recorded. | The case asserts behaviour that does **not exist today**. A green-on-arrival RED-FIRST case is a **defect of the authoring task**: it does not exercise the not-yet-built behaviour and must be strengthened until it fails. |
| **CHARACTERIZATION** | Observed **passing against the baseline (untrimmed) build** at authoring time, then observed passing again against the changed artifact. Both observations recorded. | The case asserts existing, correct behaviour this shipment must **preserve**. A red-on-arrival CHARACTERIZATION case is a **defect of the authoring task**: the baseline claim is false and must be corrected before anything is built on it. These are **not** falsely required to be red. |

The two classes are **mutually exclusive and exhaustive** — no case may be
unclassified, and no case may carry both. Classification is authored data, not
commentary: it lives in the case table below and is reproduced in each owning
task record.

### Machine enforcement

The class contract is enforced by dependency edges and by a terminal ledger, not
by prose:

1. **Two authoring harnesses, not one.** `T3a` authors only RED-FIRST cases and
   completes at **red**. `T3b` authors only CHARACTERIZATION cases and completes
   at **green-on-baseline**. Neither can complete by doing the other's job.
2. **Authoring precedes implementation by edge.** Every authoring task
   (`T3a`, `T3b`, `T9`–`T13`) **blocks** every implementing task that owns one of
   its cases' green transitions — `T7`, `T7b`, `T8`, `T14`, and (added in
   review-fix cycle 3, finding 5) **`T5`**, which owns the green for `T9`'s
   `test_skill_docs_refs_resolve_to_workspace_not_payload`. No implementation can
   start until the observation that gives it meaning has been recorded. The rule
   is *author-before-owner for every case*, not *author-before-a-fixed-list*; the
   fixed list is what let the `T9 → T5` pair go unencoded through two cycles.
3. **Verification families author before they verify.** `T9`–`T13` are re-scoped
   from *write tests after the change* to *author and observe against the baseline
   build*, then hand their cases to the terminal ledger for the post-change
   observation. This is what gives the install/upgrade/resolver/registration/
   integrity families a real red (or real green-on-baseline) owner.
4. **A terminal ledger closes the loop.** `T16` re-runs the complete suite against
   the built trimmed wheel, sdist, and plugin payload and asserts each case
   transitioned **exactly as its class declares** — RED-FIRST red→green,
   CHARACTERIZATION green→green. Any case that did not transition as declared
   fails the shipment. A declared class with no recorded transition is a failure,
   not a pass.

### Case table (canonical, bijective — rewritten in review-fix cycle 3, finding 5)

This table is the **single authoritative case ledger**. Every row is reproduced in
its authoring task record and in its green/preservation owner's record, with the
**same test name, same class, same author, same owner, and same observed initial
state**; any divergence is a plan/queue drift defect, not a documentation nit.

* **Authored by** — the task that writes the case and records the **first**
  observation.
* **Observed initial state** — what the first observation *is*, and why. A
  RED-FIRST row states the concrete failure mode (import error, missing artifact,
  or assertion failure); a CHARACTERIZATION row states why the case is green on the
  untrimmed baseline. A row with no stated initial state is unverifiable by `T16`.
* **Green / preservation owner** — the task whose change must produce the **second**
  observation.
* **Machine dependency** — the encoded edge that forces the author to run before
  the owner. Every RED-FIRST row must name one.

| Test | Asserts | Class | Authored by | Observed initial state | Green / preservation owner | Machine dependency |
|---|---|---|---|---|---|---|
| `test_manifest_validates_against_schema` | AC1 | RED-FIRST | T3a | **red** — neither the manifest nor the `1.0.0` schema exists (missing artifact) | T4 | T4 ← T3a; T4 ← T2b |
| `test_schema_live_and_versioned_mirror_agree` | AC1 | RED-FIRST | T3a | **red** — neither schema file exists (missing artifact) | T2b | T2b ← T3a |
| `test_payload_manifest_contract_registered` | AC1 | RED-FIRST | T3a | **red** — `payload-manifest` absent from `SCHEMA_CONTRACTS` | T2b | T2b ← T3a |
| `test_every_tracked_path_is_classified` | AC11, AC3d | RED-FIRST | T3a | **red** — no manifest, so no path is classified | T4 | T4 ← T3a |
| `test_start_scripts_and_workspace_config_excluded` | AC11 | RED-FIRST | T3a | **red** — no manifest | T4 | T4 ← T3a |
| `test_manifest_is_sole_source_of_payload_paths` | AC1 | RED-FIRST | T3a | **red** — `build_support.payload` is not importable | T5 | T5 ← T3a |
| `test_unclassified_tracked_path_fails_build` | AC2, AC8 | RED-FIRST | T3a | **red** — no fail-closed guard exists; a synthetic unclassified path is silently accepted (V4) | T5 | T5 ← T3a |
| `test_payload_size_reported` | AC8 | RED-FIRST | T3a | **red** — no per-channel file-count/byte-size report exists | T5 | T5 ← T3a |
| `test_generated_output_root_excluded_from_classifier_inputs` | AC3d, AC2 | RED-FIRST | T3a | **red** — neither the resolver nor the `generated_output_roots` key exists | T5 | T5 ← T3a |
| `test_generate_emits_expected_tables_to_a_scratch_target` | AC2c | RED-FIRST | T3a | **red** — the generation command does not exist | T6 | T6 ← T5 ← T3a |
| `test_generate_is_byte_deterministic_and_cross_platform` | AC2c | RED-FIRST | T3a | **red** — the generation command does not exist | T6 | T6 ← T5 ← T3a |
| `test_only_one_generation_path_exists` | AC2c | RED-FIRST | T3a | **red** — the generation command does not exist | T6 | T6 ← T5 ← T3a |
| `test_plugin_generation_is_idempotent` | AC2c, AC3d | RED-FIRST | T3a | **red** — the generation command does not exist | T6 | T6 ← T5 ← T3a |
| `test_wheel_generated_table_matches_manifest` | AC2c | RED-FIRST | T3a | **red** — the committed wheel table is hand-authored, not manifest-derived | T7 | T7 ← T3a |
| `test_docs_root_guides_only` | AC4 | RED-FIRST | T3a | **red** — the wheel currently ships all 642 `docs/` files | T7 | T7 ← T3a |
| `test_wheel_excludes_backlogit_explicitly` | AC3 | **CHARACTERIZATION** | T3b | **green on baseline** — `force-include` already lists only the runtime set, so `.backlogit/` is already absent | T7 | T7 ← … ← T3b |
| `test_wheel_excludes_dev_directories` | AC3 | **CHARACTERIZATION** | T3b | **green on baseline** — `tests/`, `experiments/`, `references/` are already absent from the wheel | T7 | T7 ← … ← T3b |
| `test_wheel_contains_required_runtime_set` | AC4 | **CHARACTERIZATION** | T3b | **green on baseline** — the runtime set is already force-included | T7 | T7 ← … ← T3b |
| `test_core_metadata_version_pins_preserved` | I4, V2 | **CHARACTERIZATION** | T3b | **green on baseline** — both `core-metadata-version = "2.4"` pins already exist | T7 (wheel pin) / T7b (sdist pin) | T7 ← … ← T3b; T7b ← T7 |
| `test_sdist_generated_table_matches_manifest` | AC2c, AC3b | RED-FIRST | T3a | **red** — the sdist target declares no table at all | T7b | T7b ← T7 ← T3a |
| `test_sdist_excludes_backlogit_explicitly` | AC3b | RED-FIRST | T3a | **red** — the default sweep packages `.backlogit/` | T7b | T7b ← T7 ← T3a |
| `test_sdist_excludes_dev_directories` | AC3b | RED-FIRST | T3a | **red** — the default sweep packages `tests/`, `experiments/`, `references/` | T7b | T7b ← T7 ← T3a |
| `test_sdist_byte_size_and_disclosure_reported` | AC3b, AC8 | RED-FIRST | T3a | **red** — no per-channel disclosure report exists | T7b | T7b ← T7 ← T3a |
| `test_sdist_contains_required_runtime_set` | AC3b, AC4 | **CHARACTERIZATION** | T3b | **green on baseline** — the default sweep already contains the runtime set | T7b | T7b ← T7 ← … ← T3b |
| `test_sdist_includes_build_definition` | AC3b, AC11 | **CHARACTERIZATION** | T3b | **green on baseline** — `pyproject.toml` is in the default sweep | T7b | T7b ← T7 ← … ← T3b |
| `test_plugin_generated_declaration_matches_manifest` | AC2c | RED-FIRST | T3a | **red** — `marketplace.json` declares `source: "."`, derived from nothing | T8 | T8 ← T3a |
| `test_plugin_payload_excludes_dev_directories` | AC3 | RED-FIRST | T3a | **red** — `source: "."` ships the entire repository | T8 | T8 ← T3a |
| `test_plugin_source_path_is_tracked_and_fetchable` | AC3c | **CHARACTERIZATION** | T3b | **green on baseline** — the baseline `source: "."` resolves to the repository root, which *is* tracked and *is* present in every consumer checkout, so the tracked-and-fetchable property already holds. **Reclassified from RED-FIRST in cycle 4, finding 5:** it was declared red on the ground that "no branch decision and no tracked payload root exist yet", but the case asserts a property of the *resolved `source` path*, not the existence of a payload root — and that property is baseline-true. It is also **branch-neutral in the wrong direction for red**: branch (a) *preserves* `source: "."`, so the case would be green at authoring, green throughout, and would never transition. Demanding red would have forced the author to weaken the assertion until the baseline broke it — manufacturing red, which destroys the signal. Its real job is **preservation**: whatever `T1` selects, the resolved `source` must remain tracked and consumer-fetchable, which is exactly the `dist/plugin/` failure mode cycle-1 finding 5 identified | T8 (preservation) | T8 ← … ← T3b; T8 ← T1 |
| `test_plugin_payload_conforms_to_the_selected_strategy` *(renamed from `test_plugin_payload_tree_is_self_excluded_and_flat` in cycle 4, finding 6)* | AC3d, AC3c | RED-FIRST | T3a | **red** — **branch-parametric, and red under *both* branches for the same reason.** The case reads the selected strategy from the manifest's declared plugin-strategy key and asserts the branch-specific conjunction below. At authoring time the manifest does not exist, so the strategy is undeclared *and* the baseline plugin payload is the entire repository: the case fails on **strategy-undeclared** and would still fail on the payload assertion once declared. **The cycle-3 initial state ("the tracked tree does not exist") is withdrawn** — under branch (a) the tree *legitimately never exists*, so tree-absence is a valid final state there and cannot serve as the red condition | T8 | T8 ← T3a; **T8 ← T1** |
| `test_target_workspace_prefixes_have_exactly_one_authored_occurrence` *(added in cycle 4, finding 9)* | AC2d | RED-FIRST | T3a | **red** — the manifest and its `target_workspace_paths` key do not exist, so the scan over the executable-and-configuration surface finds **zero** authored occurrences and the exactly-one assertion fails. This is the case AC2d described in prose ("the test asserts exactly one authored occurrence") but that no ledger row ever named — an unnamed assertion is invisible to `T16` and therefore unowned | T4 | T4 ← T3a |
| `test_install_emits_only_generated_output` | AC5, I3 | **CHARACTERIZATION** | T9 | **green on baseline** — `/install-harness` already emits only generated output; byte-identity is measured against the `T2a` baseline inventory | T7 / T7b / T8 | T7 ← T9; T8 ← T9; T7b ← T7 |
| `test_no_engine_records_in_target_workspace` | AC5 | **CHARACTERIZATION** | T9 | **green on baseline** — the installer generates and never copies engine records, so the scratch workspace is already clean *(reclassified from RED-FIRST in cycle 3: it is baseline-true, and demanding red here would require breaking a correct installer)* | T7 / T7b / T8 | T7 ← T9; T8 ← T9 |
| `test_skill_docs_refs_resolve_to_workspace_not_payload` | AC5, AC2d, R2 | RED-FIRST | T9 | **red** — `build_support.payload.classify_target_workspace_path` is not importable; the case targets the expected-absent interface deliberately rather than waiting for it | T5 | **T5 ← T9** *(edge added in cycle 3, finding 5 — the author must precede the green owner)* |
| `test_verify_workspace_parity_trimmed_vs_baseline` | AC6 | **CHARACTERIZATION** | T10 | **green on baseline** — parity of the baseline finding set with itself, as a set difference | T7 / T7b / T8 | T7 ← T10; T8 ← T10 |
| `test_upgrade_from_1_5_0_leaves_no_orphans` | AC6, R3, V3 | RED-FIRST | T10 | **red** — the trimmed build to upgrade *to* does not exist (missing artifact); orphans are created *by* trimming, so there is nothing to observe green on the baseline | T7 / T7b / T8 | T7 ← T10; T8 ← T10 |
| `test_home_and_version_behave_identically` | AC6, I1, I2 | **CHARACTERIZATION** | T10 | **green on baseline** — `autoharness home` / `version` behave as recorded by `T2a` *(named in cycle 3; it was an unnamed assertion and therefore invisible to the ledger)* | T7 / T7b / T8 | T7 ← T10; T8 ← T10 |
| `test_data_dir_resolution_pip_install` | AC6a, R4 | **CHARACTERIZATION** | T11 | **green on baseline** — `_DATA_DIR` already resolves from the installed wheel | T7 / T7b | T7 ← T11; T7b ← T7 |
| `test_data_dir_resolution_clone_editable` | AC6a, R4 | **CHARACTERIZATION** | T11 | **green on baseline** — the clone/editable fallback already resolves | T7 / T7b | T7 ← T11; T7b ← T7 |
| `test_python_channel_needs_no_plugin_root_artifact` | AC6a (A1) | **CHARACTERIZATION** | T11 | **green on baseline** — Python-channel resolution already succeeds with plugin-root artifacts absent | T7 / T7b | T7 ← T11; T7b ← T7 |
| `test_plugin_root_resolves_templates_and_schemas` | AC6b | RED-FIRST | T11 | **red** — no plugin-root resolver and no trimmed plugin root exist | T8 | T8 ← T11 |
| `test_plugin_version_resolves_from_plugin_manifest` | AC6b, AC10 | RED-FIRST | T11 | **red** — the baseline plugin payload is the whole repository, so version resolves from `pyproject.toml`/`__init__.py`; the manifest-only path is unexercised and the assertion fails *(added in cycle 3, finding 5 — the case existed in `160.013-T` but was absent from this ledger)* | T8 | T8 ← T11 |
| `test_plugin_channel_resolution_imports_no_python_package` | AC6b (B1) | RED-FIRST | T11 | **red** — the baseline plugin payload contains `src/`, so the no-import path cannot be exercised *(named in cycle 3; previously an unnamed "negative assertion B1")* | T8 | T8 ← T11 |
| `test_plugin_payload_has_no_python_distribution` | AC6b (B2) | RED-FIRST | T11 | **red** — the baseline plugin payload contains `src/` and `pyproject.toml` | T8 | T8 ← T11 |
| `test_channel_resolver_contracts_are_disjoint` | AC6a, AC6b | RED-FIRST | T11 | **red** — the AC6b resolver does not exist, so disjointness is unassertable | T8 | T8 ← T11 |
| `test_register_phase_all_environments_python_channel` | AC7 | **CHARACTERIZATION** | T12 | **green on baseline** — all four Python-channel registration targets already succeed | T7 / T7b | T7 ← T12; T7b ← T7 |
| `test_plugin_only_register_copilot_cli_succeeds` | AC7 | **CHARACTERIZATION** | T12 | **green on baseline** — the one supported plugin-channel cell already succeeds | T8 | T8 ← T12 |
| `test_plugin_only_unsupported_targets_fail_the_same_way_as_baseline` | AC7 | **CHARACTERIZATION** | T12 | **green on baseline** — the four limitations are pre-existing and documented; the case compares the baseline against its own recorded failure modes | T8 | T8 ← T12 |
| `test_plugin_channel_excludes_python_cli_by_design` | AC7 | RED-FIRST | T12 | **red** — `source: "."` means `src/` and `pyproject.toml` **are** in the baseline plugin payload, so the "unsupported for the declared reason" assertion fails | T8 | T8 ← T12 |
| `test_gate4_crossrefs_intact_in_built_payload` | AC9, AC2d | RED-FIRST | T13 | **red** — the *trimmed* built payload does not exist (missing artifact); additionally `classify_target_workspace_path` is not importable until `T5`. The case is scoped to the trimmed artifact precisely so it is not vacuously green against an untrimmed payload that contains everything | T7 / T7b / T8 | T7 ← T13; T8 ← T13 |
| `test_version_resolves_on_plugin_install_without_cli` | AC10 | RED-FIRST | T13 | **red** — there is no trimmed plugin payload to install from (missing artifact) | T8 | T8 ← T13 |
| `test_release_workflow_runs_payload_gate_before_publish` | AC2b | RED-FIRST | T3a | **red** — `release.yml` contains no payload-composition gate step | T14 | T14 ← T3a |
| `test_release_gate_covers_all_three_channels` | AC2b, AC3b | RED-FIRST | T3a | **red** — no gate step exists, so no channel argument resolves | T14 | T14 ← T3a |

**Ledger totals: 52 cases — 35 RED-FIRST, 17 CHARACTERIZATION.** *(Recalculated in
extended review-fix cycle 4: cycle 3's 51 = 35 + 16 became 52 = 35 + 17 through two
independent changes — finding 5 moved `test_plugin_source_path_is_tracked_and_fetchable`
from RED-FIRST/`T3a` to CHARACTERIZATION/`T3b` (−1 RED, +1 CHAR, total unchanged), and
finding 9 added `test_target_workspace_prefixes_have_exactly_one_authored_occurrence` as
RED-FIRST/`T3a` (+1 RED, +1 total). `T3a`'s red count is therefore unchanged at 25 by
coincidence of the two offsetting moves, not by oversight.)* Authorship,
with the per-author class split spelled out so a miscount in either direction is
mechanically detectable:

| Author | RED-FIRST | CHARACTERIZATION | Total |
|---|---|---|---|
| `T3a` (`160.005-T`) | 25 | 0 | 25 |
| `T3b` (`160.016-T`) | 0 | 7 | 7 |
| `T9` (`160.008-T`) | 1 | 2 | 3 |
| `T10` (`160.012-T`) | 1 | 2 | 3 |
| `T11` (`160.013-T`) | 5 | 3 | 8 |
| `T12` (`160.009-T`) | 1 | 3 | 4 |
| `T13` (`160.010-T`) | 2 | 0 | 2 |
| **Total** | **35** | **17** | **52** |

**Branch-aware semantics for `test_plugin_payload_conforms_to_the_selected_strategy`**
*(cycle 4, finding 6).* The case is **one** case with **one** class (RED-FIRST) and
**one** green owner (`T8`), parameterized by the strategy `T1` selects. The selected
strategy is **required data**: a run in which no strategy is declared **fails**, so
the case can never be satisfied by silence.

* **Branch (a) — native exclusion.** Assert (i) **no** `plugin-payload/` tree is
  materialized anywhere in the tree, **and** (ii) the payload the native mechanism
  actually resolves is the **manifest-derived plugin set** — file-set equality
  against the resolver's output, not a subset check and not merely "smaller than the
  repository". Conjunct (ii) is what makes branch (a) meaningfully red at baseline:
  absence of the tree is already true, but the baseline payload is the whole
  repository, so the conjunction fails.
* **Branch (b) — materialized tree.** Assert the tracked `plugin-payload/` tree
  **exists**, is **tracked**, is **flat** (contains no nested directory named
  `plugin-payload`), is **self-excluded** from every channel's classifier input, and
  that `generate --channel plugin --check` reports **no drift** immediately after a
  regeneration.
* **Branch (c).** `T1` halts; `T8` does not begin and this case is never observed
  green. A halted shipment is not a passing one.

Under **both** (a) and (b) the initial observation is a **real red** and the final
observation is a **real green over a non-trivial assertion**. The withdrawn cycle-3
formulation used tree-absence as the red condition, which made the case *vacuously
green on arrival* under branch (a) — the exact defect the two-class contract exists
to prevent.

Every case has
exactly one class, exactly one author, at least one green/preservation owner, a
stated observed initial state, and — for every RED-FIRST case — an encoded edge
placing its author before its owner. `T16` verifies all 52 pairs.

**Cycle-3 reconciliation notes (finding 5).** Four kinds of divergence between this
table and the `160.*` task bodies were closed, in the direction the substance
requires rather than by making one side copy the other:

* **Cases that existed only in a task record** are now in the ledger:
  `test_plugin_version_resolves_from_plugin_manifest`,
  `test_plugin_channel_resolution_imports_no_python_package` (was "negative
  assertion B1"), and `test_home_and_version_behave_identically` (was an unnamed
  bullet). An unnamed assertion cannot be verified by the transition ledger, so it
  was effectively unowned.
* **Whole-family class labels are withdrawn.** `160.008-T`, `160.009-T`,
  `160.010-T`, `160.012-T` and `160.013-T` each declared a single class "for this
  family". Four of the five families are genuinely **mixed**, so the family label
  contradicted the per-case truth. Class is declared **per case** and nowhere else.
* **Two cases were reclassified on the merits.**
  `test_no_engine_records_in_target_workspace` is **CHARACTERIZATION** (it is
  baseline-true; the plan previously said RED-FIRST).
  `test_gate4_crossrefs_intact_in_built_payload` is **RED-FIRST** scoped to the
  *trimmed* artifact (the task record previously said CHARACTERIZATION, which
  would have made it vacuous against an untrimmed payload containing everything).
* **One missing edge was added.** `test_skill_docs_refs_resolve_to_workspace_not_payload`
  is authored by `T9` with green owned by `T5`, but no edge forced `T9` before
  `T5`. The edge **`T5` ← `T9`** is now encoded. `T9` authors the case against the
  **expected-absent** `classify_target_workspace_path` interface — an import-error
  red — rather than deferring authorship until `T5` has implemented it, which is
  what created the ordering gap.

**Why `test_generated_tables_match_manifest` no longer exists as a single case
(review-fix cycle 2, finding 2).** Cycle 1 made `T6` the green owner of a case
asserting that the **committed** `pyproject.toml` and `marketplace.json` tables
equal the derived tables — while `T6`'s own safety scope forbade it from
committing into either file, because those files belong to `T7`/`T8`. `T6` was
required to reach a state it was forbidden to create, so it had **no achievable
committed completion state**.

The case was conflating two different properties. It is split along that seam:

* **`test_generate_emits_expected_tables_to_a_scratch_target`** — a property of
  the *generator*: given the manifest, `generate` writes the expected content to a
  caller-supplied target directory, mutating no repository file. **`T6` owns
  green**, and can reach it entirely within its own scope.
* **`test_{wheel,sdist,plugin}_generated_table_matches_manifest`** — a property of
  the *wiring*: the committed table in each channel's real file equals what
  `generate --check` derives. **`T7`, `T7b`, and `T8` own green**, each for the
  file it is authorized to edit.

`T6`'s scope is unchanged and still forbids committing generated content into
`pyproject.toml`, `marketplace.json`, or `plugin-payload/`; it simply no longer
owns a case that required doing so. Downstream gating is preserved and in fact
sharpened — each channel's committed-parity case now blocks on that channel's own
wiring task rather than on a single shared case.

### Baseline

Baseline capture (pre-change **wheel and sdist** inventories, `verify-workspace`
**finding set**, `/install-harness` output inventory, and the v1.5.0 plugin-only
registration failure modes) is a prerequisite of every CHARACTERIZATION case and
of the parity, upgrade, and registration families, and is produced by `T2a`. A
baseline that exists only in a transcript cannot be asserted against; it is
recorded durably, in the two destinations authorized by H2 (cycle 3, finding 6):
the narrative record in `docs/audits/2026-09-03-ship10-payload-evidence/` and the
machine-readable inventories and finding sets in
`tests/fixtures/payload-baseline/**`. The split is deliberate — `T16` and the
characterization families **diff** the fixtures, and a prose document is not
diffable. CHARACTERIZATION cases are observed green **against that
baseline build**, which is what makes their first observation meaningful rather
than vacuous.

## Security and reliability

* **Disclosure (primary):** `.backlogit/` carries 2,110 files of internal backlog
  records — titles, plans, decisions, review findings — currently published to
  every plugin consumer **and to every sdist consumer**. The sdist target declares
  no `include`/`exclude` at all, so hatchling's default sweep packages the whole
  project and `uv build` publishes it to PyPI and attaches it to the GitHub
  release (AC3b). Removal from **all three** channels is the security core of this
  work; a wheel-only trim removes nothing.
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
2. **Immediate:** revert the `pyproject.toml` (wheel **and** sdist tables),
   `marketplace.json`, and `plugin-payload/` wiring commits. Payload returns to the
   current untrimmed superset — degraded (bloated) but functional. The manifest,
   schema, and tests may remain in place inert.
3. **Version safety:** the trimmed payload ships under a **new version**; v1.5.0
   artifacts already published are untouched, so rollback never requires
   retracting a release.
4. **Consumer recovery:** reinstall/upgrade from the prior version restores the
   full payload; no consumer workspace state is mutated by this change.
5. **Point of no return:** none before publication. Publication is Ship/Orchestrator
   scope and out of this plan's authority.

### Rollback is non-destructive by default (binding, review-fix cycle 2, finding 11)

Cycle 1's rollback checkpoint read "rollback is a single-file restore". A restore
that overwrites working-tree state is a **destructive command**, and Constitution
Principle VII requires operator approval for one. Prescribing it as the standard
recovery path pre-authorized a destructive overwrite that no operator had agreed
to, at the exact moment — a failed release — when the working tree is most likely
to hold unrelated uncommitted work. This shipment adopts the same authorization
contract SHIP-4 Decision G established for the P-007 `git restore` remediation, so
the harness does not carry two different answers to the same question.

* **R-1 — the default rollback is forward and non-destructive.** Recovery is a
  **new revert commit** (`git revert`, or a fresh edit restoring the recorded
  bytes) applied on top of history. It overwrites no working-tree state, destroys
  no uncommitted work, and leaves a complete audit trail. This is the path an agent
  may take unaided.
* **R-2 — pre-change bytes are recorded as evidence, not as a restore trigger.**
  The rollback checkpoint on `T7`, `T7b`, `T8`, and `T14` records the exact
  pre-change bytes of the file it mutates into a durable evidence artifact. That
  record exists so a human can verify or reconstruct the prior content. It is
  **not** an authorization to overwrite, and its presence never shortens or
  pre-satisfies an approval.
* **R-3 — any destructive restore or overwrite requires fresh live operator
  approval.** `git restore`, `git checkout --`, `git clean`, a forced file
  overwrite, or deletion of a tracked file requires a **live approval result
  obtained at the moment of the request over an independent operator channel the
  executing agent cannot synthesize** — intercom approval/clearance, an
  interactive ask/confirm, or the operator session channel. The defining property
  is **non-synthesizability**. A backlog comment, task note, plan sentence, or
  checkpoint record is **evidence only, never authority**, and must never be read
  back as approval. Each attempt requires its own fresh approval; approvals do not
  cache.
* **R-4 — no channel means halt, do not restore.** If no independent approval
  channel is available — degraded, unreachable, absent, or present but unanswered
  — the agent **halts and does not restore**. It records the failure, names the
  exact command a human can run, and leaves the working tree untouched. Absence of
  a channel is never implicit approval. In dark-factory/AFK mode no operator is
  present, so a destructive restore **never runs**; the run reports and stops.
* **R-5 — non-destructive alternative evidence.** Where the goal is to *verify*
  the prior state rather than to *restore* it, the agent uses read-only
  alternatives — `git show <sha>:<path>`, `git diff`, or materializing the prior
  content into a scratch path under a gitignored directory — none of which touch
  the working tree and none of which need approval.

## Sequencing

Placed **between `166-S` and `167-S`**: it does not supersede the reviewed
reliability/security portfolio `159-S`–`166-S`, but does supersede `167-S`
(documentation/record hygiene).

`159-S → 160-S → 161-S → 162-S → 163-S → 164-S → 165-S → 166-S → 168-S → 167-S`


## Task decomposition

Rows are in **execution order** and carry an explicit **Task ID** column. Task IDs
and `T#` labels are the single coherent mapping in both directions; every task
record's `(Tn)` back-reference matches this table exactly.

Ordering satisfies Constitution Principle II (Test-First, NON-NEGOTIABLE) under
the two-class contract in **§Test strategy**: RED-FIRST cases are authored and
observed **red** before the change that turns them green, and CHARACTERIZATION
cases are authored and observed **green against the baseline build** before the
change they must survive. Neither observation can be skipped, and neither class
can masquerade as the other.

**Changes in review-fix cycle 2.** `T2` split into `T2a`/`T2b` (finding 16);
`T3` split into `T3a`/`T3b` (finding 1); `T7b` added for the sdist channel
(finding 3); `T16` added as the terminal transition ledger (finding 1); `T9`–`T13`
re-scoped from post-change test authoring to baseline authoring + observation
(finding 1).

| T# | Task ID | Scope | Size | Complexity |
|---|---|---|---|---|
| T1 | `160.002-T` | **Spike:** establish the plugin-channel trimming mechanism | S | high |
| T2a | `160.001-T` | **Baseline characterization capture** (wheel + sdist + plugin inventories, finding sets, install output, registration failure modes) | S | low |
| T3a | `160.005-T` | **RED-FIRST harness** — authors RED-FIRST cases, completes at red | M | medium |
| T3b | `160.016-T` | **CHARACTERIZATION harness** — authors CHARACTERIZATION cases, completes at green-on-baseline | S | low |
| T2b | `160.018-T` | **Payload-manifest schema publication** (live + `1.0.0` mirror) + `SCHEMA_CONTRACTS` registration + pair-divergence assertion | S | medium |
| T4 | `160.003-T` | Author `.autoharness/payload-manifest.yaml` allowlist (full AC11 classification) | M | medium |
| T5 | `160.004-T` | Manifest loader/resolver + centralized target-workspace classifier, in `build_support/` | M | medium |
| T6 | `160.014-T` | Deterministic single-path generation command (`generate` / `--check`) | S | medium |
| T9 | `160.008-T` | Install-time payload boundary cases — authored + observed vs baseline (AC5, I3) | S | medium |
| T10 | `160.012-T` | Upgrade-path + `verify-workspace` parity cases — authored + observed vs baseline | S | medium |
| T11 | `160.013-T` | Channel resolver contract cases (AC6a Python, AC6b plugin-root) — authored + observed vs baseline | S | medium |
| T12 | `160.009-T` | Cross-environment registration support matrix cases (AC7) — authored + observed vs baseline | S | medium |
| T13 | `160.010-T` | Gate 4 cross-reference + version-resolution cases — authored + observed vs baseline | S | medium |
| T7 | `160.006-T` | Wire **wheel** packaging to the manifest, preserving I4 pins | M | medium |
| T7b | `160.019-T` | Wire **sdist** packaging to the manifest (AC3b) — the disclosure-critical channel | M | medium |
| T8 | `160.007-T` | Wire plugin channel per the `T1` mechanism (AC3c) | M | high |
| T14 | `160.015-T` | Unbypassable release-path payload gate covering all three channels (AC2b) | S | medium |
| T16 | `160.017-T` | **Transition ledger** — re-run the full suite against built artifacts; assert every case transitioned exactly as its class declares | S | medium |
| T15 | `160.011-T` | Docs + CHANGELOG | S | trivial |

### Prerequisite DAG (machine-encoded)

Encoded as backlogit `blocks` dependency edges, not narrative ordering. A backlogit
`dependencies:` entry means *blocked by*.

| Task | Blocked by |
|---|---|
| `160.002-T` (T1) | — |
| `160.001-T` (T2a) | — |
| `160.005-T` (T3a) | `160.001-T` |
| `160.016-T` (T3b) | `160.001-T` |
| `160.018-T` (T2b) | `160.005-T` |
| `160.003-T` (T4) | `160.005-T`, `160.018-T` |
| `160.004-T` (T5) | `160.005-T`, `160.003-T`, `160.008-T` |
| `160.014-T` (T6) | `160.004-T`, **`160.002-T`** |
| `160.008-T` (T9) | `160.001-T`, `160.005-T`, `160.016-T` |
| `160.012-T` (T10) | `160.001-T`, `160.005-T`, `160.016-T` |
| `160.013-T` (T11) | `160.001-T`, `160.005-T`, `160.016-T` |
| `160.009-T` (T12) | `160.001-T`, `160.005-T`, `160.016-T` |
| `160.010-T` (T13) | `160.001-T`, `160.005-T`, `160.016-T` |
| `160.006-T` (T7) | `160.014-T`, `160.008-T`, `160.012-T`, `160.013-T`, `160.009-T`, `160.010-T` |
| `160.019-T` (T7b) | `160.014-T`, `160.006-T` |
| `160.007-T` (T8) | `160.002-T`, `160.014-T`, `160.008-T`, `160.012-T`, `160.013-T`, `160.009-T`, `160.010-T` |
| `160.015-T` (T14) | `160.006-T`, `160.019-T`, `160.007-T` |
| `160.017-T` (T16) | `160.015-T` |
| `160.011-T` (T15) | `160.017-T`, plus the retained cycle-1 edges `160.008-T`, `160.012-T`, `160.013-T`, `160.009-T`, `160.010-T`, `160.015-T` |

The graph is acyclic with two roots (`T1`, `T2a`) and a single sink (`T15`).
A valid topological order is: `T1`, `T2a`, `T3a`, `T3b`, `T2b`, `T9`, `T10`,
`T11`, `T12`, `T13`, `T4`, `T5`, `T6`, `T7`, `T7b`, `T8`, `T14`, `T16`, `T15`
(19 nodes, every edge respected).

**Edge added in extended review-fix cycle 4 (finding 4).** `160.014-T` (T6) is now
blocked by `160.002-T` (T1). **T6's behaviour is branch-dependent**: the generation
command's plugin channel emits "the payload/`source` declaration *and, under branch
(b), the materialized tree*", and its `test_plugin_generation_is_idempotent` case is
about writing into a tracked output root that **only exists under branch (b)**.
Under branch (a) there is no output root, the plugin channel emits a declaration
only, and the CREATE/OVERWRITE partition of §Principle VII generation rule is empty
by construction. Building the generator before knowing which branch holds means
either implementing both paths speculatively or discovering mid-task that the one
implemented is the wrong one — the same failure `T8 ← T1` already prevents for the
wiring task. **No cycle is introduced:** `T1` is a root with no prerequisites, so it
cannot be reachable from `T6`. The topological order above is unchanged — `T1`
already precedes `T6` in it — so the added edge tightens the machine encoding to
match a constraint the order was already honouring by luck rather than by rule.

**Edge added in review-fix cycle 3 (finding 5).** `160.004-T` (T5) is now blocked
by `160.008-T` (T9). `T9` authors
`test_skill_docs_refs_resolve_to_workspace_not_payload`, whose green owner is
`T5` — but through cycles 1 and 2 no edge forced `T9` first, so `T5` could have
implemented `classify_target_workspace_path` before the case that must observe it
red ever existed. The addition does not create a cycle: `T9`'s only ancestors are
`T2a`, `T3a`, and `T3b`, and `T5` is not among them. Note the consequence for
execution order — the five verification families now run **before** `T4`/`T5`, not
after; the topological order above reflects this.

**On `T15`'s retained edges.** Those six are *transitively implied* by
`160.017-T` (T16), which is blocked by `T14`, which is blocked by `T7`/`T7b`/`T8`,
which are blocked by `T9`–`T13`. They are recorded here rather than pruned because
they were authored in cycle 1 as deliberate statements that the terminal
documentation task must not run before each verification family has reported, and
deleting a true edge to make a table shorter trades a real constraint for
tidiness. They are listed explicitly so this table is an **exact** mirror of the
machine-encoded edge set rather than a simplified view of it — a documented DAG
that omits real edges is how plan/queue drift starts.

**Red-before-green is enforced by the edges, not by prose.**

* `T3a` (RED-FIRST harness) is blocked only by `T2a`, and it blocks `T2b`, `T4`,
  and `T5`. **Nothing that could turn a RED-FIRST case green can start until the
  harness that observes it red has completed** — including the schema itself.
  Cycle 1 let `T2` publish `schemas/payload-manifest.schema.json`, its versioned
  mirror, and the `SCHEMA_CONTRACTS` registration with **no red owner anywhere**;
  those three deliverables are now `T2b`, which is blocked by `T3a` and named as
  the green owner of `test_schema_live_and_versioned_mirror_agree` and
  `test_payload_manifest_contract_registered` (finding 1).
* `T3b` (CHARACTERIZATION harness) is blocked by `T2a` because a
  green-on-baseline observation requires the baseline build to exist. It blocks
  the five verification families and, transitively, every wiring task — so no
  invariant can be broken before it has been pinned.
* `T9`–`T13` are blocked by `T2a`, `T3a`, and `T3b` and **block** `T7` and `T8`;
  `T9` additionally blocks `T5` (cycle 3, finding 5).
  Cycle 1 had them running *after* the wiring, which meant the install, upgrade,
  resolver, registration, and integrity families were written against the finished
  change and could never have been red. The edges now make that impossible
  (finding 1).
* `T7b` is blocked by `T7` as well as `T6`. Both edit `pyproject.toml`; a
  same-file collision is prevented by a machine-encoded edge rather than by prose,
  following the precedent set in SHIP-3 finding 15.
* `T16` is blocked by `T14` and blocks `T15`. It is the only task that observes
  post-change transitions, and it fails the shipment if any case did not
  transition exactly as its class declares.

**T1 is a blocking spike.** The plan assumes the plugin payload can be
constrained, but the only observed mechanism is `marketplace.json`'s `source: "."`,
and no evidence establishes that Copilot CLI supports an allowlist or ignore file
for plugin sources. T1 must determine which holds:

* **(a)** the marketplace source supports a native exclusion/allowlist mechanism →
  wire it directly in `T8`; or
* **(b)** it does not → `T8` builds a **tracked, committed** payload tree at
  `plugin-payload/` from the manifest and repoints `source` at it (AC3c). That
  tree is declared in the manifest's `generated_output_roots`, **not** in any
  channel's `include` rules, so it is removed from the classifier's input domain
  and the generator can never consume its own output (**AC3d**, cycle-3 finding 9);
  or
* **(c)** neither is acceptable → `T1` **halts to the operator** with the evidence
  and the alternatives.

Branch (b) may **not** point `source` at `dist/plugin/` or any other gitignored or
untracked path — `dist/.gitignore` is `*`, so a consumer checkout has no such
directory and the install simply fails (*review-fix cycle 1, finding 5*). `T8`
must not begin until `T1` resolves this.

**Width isolation.** `T7` (wheel packaging), `T7b` (sdist packaging), `T8` (plugin
channel), and `T14` (CI workflow) are separate tasks with separate blast radii;
`T7`/`T7b` share a file and are therefore serialized by edge. `T9`–`T13` are
separated by failure domain — each has an independent diagnosis path. `T6`
(codegen) is separated from `T5` (resolution) because serializing three output
formats deterministically is a distinct deliverable from resolving a manifest.
`T2a` (baseline evidence) is separated from `T2b` (schema publication) because
recording what exists today and publishing a new versioned contract are different
kinds of work with different reversibility, and cycle 1's combined `S`/`low` task
understated both (finding 16).

## Traceability

* **Source stash: `E9E5E6CC`** — durable and verifiable at HEAD in the official
  backlogit archive record `.backlogit/archive/stash.jsonl` (tracked; blob
  `aef5f126` at `73cb51e6`), carrying its own forward reference to feature
  `160-F` and shipment `168-S`. *Review-fix cycle 2, finding 13 reported this
  entry as unfindable; it is present in the archive, and the finding is recorded
  as a false positive with the evidence above.* Consumed stash entries are
  **archived**, not left in the active stash, so an active-stash-only search
  necessarily misses them.
* **The archived harvest annotation is intentionally left uncorrected.**
  `E9E5E6CC` records the harvest scope as `160.001-T..160.011-T` — true when
  written, incomplete now that the feature carries nineteen tasks. It is an
  **archived** record and therefore immutable by design; rewriting it would erase
  the historical fact that the harvest produced eleven tasks and would make the
  archive an unreliable witness for every other entry in it.
* **Forward correction (authoritative for the current task set).** The join
  between the archived annotation and today's scope is the **`SOURCE-TRACEABILITY
  FORWARD CORRECTION` comment on feature `160-F`** *(review-fix cycle 3, finding
  11; `.backlogit/logs/160-F.jsonl`, actor `stage`, the sixth event)*. It
  **enumerates** the full chain
  `E9E5E6CC → 160-F → 160.001-T … 160.019-T → 168-S` member by member rather
  than as a range, records the provenance of each of the eight tasks added after
  harvest, and supersedes the cycle-2 repair comment, which expressed scope as a
  range. A range silently asserts the interval is dense: had any ID in it been
  absent or retired, the range would still have read as correct. Where that
  comment and any earlier statement disagree about the **current** task set, the
  comment governs; where they disagree about what was true **at harvest time**,
  the archived annotation governs.
* **`AB387F16`** — a **pre-persistence temporary working ID**, superseded by
  `E9E5E6CC` before any stash record was written. It has **no** durable stash
  entry and must not be given one; fabricating a record to satisfy a lookup would
  manufacture false provenance. It survives only as the superseded-ID note on
  `160-F` and in the forward-correction comment, which is the correct and
  complete disposition.
* Feature: `160-F` (records the source-stash linkage, the superseded temporary ID,
  and the forward-correction comment above)
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
| Public API / schema / contract change | **Yes** | New `payload-manifest.schema.json`; packaging contract for all three channels (wheel, sdist, plugin) |
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
tasks, never modified.

**The writable surface is exactly the following, and nothing else** *(corrected in
review-fix cycle 2, finding 4 — cycle 1's list omitted two files the plan itself
declares mandatory, so the plan's own acceptance criteria were unexecutable under
its own safety mode)*:

| Writable path | Authorized task(s) | Bound |
|---|---|---|
| `.autoharness/payload-manifest.yaml` | T4 | Whole file (new) |
| `schemas/payload-manifest.schema.json` | T2b | Whole file (new) |
| `schemas/payload-manifest/1.0.0.schema.json` | T2b | Whole file (new). **Added in cycle 2** — the two-file convention makes the versioned mirror mandatory (AC1, Schema publication layout), yet cycle 1's allowlist named only the live file, so the mirror could not legally be created |
| `src/autoharness/schema_contracts.py` | **T2b only** | **Narrow, single-purpose exception to freeze-scope.** Add the `payload-manifest` contract registration entry **only**. No other statement, function, or file in `src/autoharness/` may be touched, by this task or any other. **Added in cycle 2** — cycle 1 simultaneously forbade all `src/` edits and required this registration as a non-deferrable acceptance criterion, a direct contradiction |
| `build_support/**` | T5, T6 | New tree, excluded from every payload |
| `tests/**` | T3a, T3b, T9–T13, T16 | Test authoring and execution only. **`T2b` and `T6` are deliberately NOT on this row** (cycle 4, finding 8) — both are *green owners only*, author no case, and must reach green through production/schema/`build_support` change alone |
| `pyproject.toml` | T7 (wheel target), T7b (sdist target) | Build tables only; serialized by edge to avoid same-file collision |
| `.github/plugin/marketplace.json` | T8 | Payload/`source` declaration only |
| `plugin-payload/**` | T8 | Tracked generated payload tree; branch (b) only (AC3c). **Writes into this tree are subject to the Destructive-operation checkpoint's Principle VII approval rule** — being a declared output root does not make an overwrite of tracked content non-destructive |
| `.github/workflows/release.yml` | T14 | The one added gate step only |
| `docs/spikes/2026-09-03-ship10-plugin-channel-mechanism.md` | T1 | Whole file (new). **Added in cycle 3, finding 6** — `T1` is a *blocking spike* whose branch (a)/(b)/(c) determination gates `T8`; that determination must be durable and reviewable, and the existing `docs/spikes/` convention is its home |
| `docs/audits/2026-09-03-ship10-payload-evidence/**` | T2a, **T3a, T3b, T9, T10, T11, T12, T13,** T7, T7b, T8, T14, T16 | **The single bounded evidence surface. Added in cycle 3, finding 6; extended to the observation producers in cycle 4, finding 7.** One directory, one date-stamped name, one shipment. It holds exactly **five** kinds of artifact and nothing else: (1) `T2a`'s durable baseline characterization record; (2) the `Rollback` checkpoint's pre-change byte records for `T7`/`T7b`/`T8`/`T14`; (3) `T16`'s transition ledger; (4) **`observations/` — the first-observation records of every authoring task (`T3a`, `T3b`, `T9`–`T13`), see the handoff contract below**; (5) the raw observation logs those cite. No new store, no new tool, no new convention — `docs/audits/` already exists in this workspace |
| `tests/fixtures/payload-baseline/**` | **T2a only** | **Added in cycle 3, finding 6.** The machine-readable half of the `T2a` baseline — wheel/sdist/plugin inventories and finding sets that `T3b` and `T9`–`T13` load as fixtures and that `T16` diffs against. `T2a` is *not* otherwise authorized under `tests/**`; this row extends it to fixture data only and grants no test-authoring rights |
| `docs/installation.md`, `README.md`, `CHANGELOG.md` | T15 | The three documents named in T15 |

**Every mandatory durable output is now authorized** *(cycle 3, finding 6)*. Cycle
2's table authorized the *code* surfaces but not the *evidence* surfaces, while the
plan simultaneously made several evidence artifacts non-deferrable acceptance
conditions — the same class of self-contradiction cycle 2 fixed for
`schema_contracts.py`. The concrete gap: `T2a` is required to produce a **durable**
baseline characterization that `T3b`, `T9`–`T13` and `T16` all consume, yet it had
no writable destination anywhere in the table, so under `freeze-scope` it could
not legally write its own deliverable. The audit below is exhaustive:

| Mandatory durable output | Producer | Authorized destination |
|---|---|---|
| Branch (a)/(b)/(c) spike determination + evidence | T1 | `docs/spikes/2026-09-03-ship10-plugin-channel-mechanism.md` |
| Baseline characterization — narrative record | T2a | `docs/audits/2026-09-03-ship10-payload-evidence/` |
| Baseline characterization — machine-readable inventories/finding sets | T2a | `tests/fixtures/payload-baseline/**` |
| **First observation (red) of each RED-FIRST case it authors** | **T3a** | **`docs/audits/2026-09-03-ship10-payload-evidence/observations/`** |
| **First observation (green-on-baseline) of each CHARACTERIZATION case it authors** | **T3b** | **`docs/audits/2026-09-03-ship10-payload-evidence/observations/`** |
| **First observation of each case it authors (mixed classes)** | **T9, T10, T11, T12, T13** | **`docs/audits/2026-09-03-ship10-payload-evidence/observations/`** |
| Pre-change bytes of `pyproject.toml` (wheel target) | T7 | `docs/audits/2026-09-03-ship10-payload-evidence/` |
| Pre-change bytes of `pyproject.toml` (sdist target) | T7b | `docs/audits/2026-09-03-ship10-payload-evidence/` |
| Pre-change bytes of `marketplace.json` | T8 | `docs/audits/2026-09-03-ship10-payload-evidence/` |
| Pre-change bytes of `release.yml` | T14 | `docs/audits/2026-09-03-ship10-payload-evidence/` |
| Transition ledger — all 52 cases, class vs. observed transition | T16 | `docs/audits/2026-09-03-ship10-payload-evidence/` |

**First-observation handoff contract** *(added in cycle 4, finding 7; closes the
finding-10 completeness audit).* Cycle 3 authorized `T1`'s spike record, `T2a`'s
baseline, the four pre-change byte records, and `T16`'s ledger — but **not** the
first observations of the seven authoring tasks, even though `V6` and `T16` make
those observations a non-deferrable acceptance condition of the shipment. Under
`freeze-scope` the seven authors therefore had **no legal destination for their own
mandatory deliverable**, which is the identical class of self-contradiction cycle 2
fixed for `schema_contracts.py` and cycle 3 fixed for `T2a`. Recording a red only in
a transcript makes it unciteable, and `T16` cannot verify a pair whose first half
does not durably exist.

The extension is **one subdirectory inside the store that already exists** — no
second store, no new tool, no new convention:

* **Location.** `docs/audits/2026-09-03-ship10-payload-evidence/observations/`,
  one file per authoring task, named for that task (e.g. `T3a.json`).
* **Format.** JSON, one record per case, with exactly these fields:
  `test_name` (string, matches the ledger row verbatim), `declared_class`
  (`RED-FIRST` | `CHARACTERIZATION`), `author_task` (task ID),
  `first_observation` (`red` | `green-on-baseline`), `observed_at` (ISO-8601),
  `command` (the exact invocation), `exit_status` (int),
  `failing_assertion` (string for `red`, `null` for `green-on-baseline`),
  `evidence_ref` (path to the raw log in the same directory).
* **`T16` consumes it as data, not prose.** `T16` joins `observations/` to the
  canonical case table on `test_name` and asserts, for all **52** cases:
  every ledger row has exactly one observation record; `declared_class` and
  `author_task` match the ledger; `first_observation` is `red` iff the class is
  RED-FIRST and `green-on-baseline` iff CHARACTERIZATION; and the post-change
  re-run produces the second half of the declared pair. A ledger row with no
  record, a record with no ledger row, or any field mismatch **fails the
  shipment** — this is what makes `V6` a machine check rather than a promise.
* **Bound.** Observation records are **append-only within the shipment** and are
  written **only** by the task that made the observation. No task may write
  another task's record, and `T16` **reads** them without modifying them.

Two deliberate choices: the baseline is **split** across a prose record and a
fixture tree because its two consumers differ (a human reviewer reads the record;
`T16` and the characterization families diff the fixtures, and a prose document is
not diffable); and all four pre-change byte records plus the ledger share **one**
directory rather than getting a store each, because five stores for five artifacts
of the same shipment is the kind of proliferation that makes evidence
unfindable. `docs/spikes/`, `docs/audits/`, and `tests/fixtures/` all already
exist — this adds no convention.

Anything outside that table is out of bounds. If a supported behaviour fails, the
fix belongs to the task that owns the surface, never to the task that observed it.

**The two `src/autoharness/` rules are not in conflict, and must not be read as
one.** The freeze-scope prohibition governs **runtime behaviour** — resolution
order, `home`, `version`, `_DATA_DIR`, and every module implementing them. The
`schema_contracts.py` authorization governs a **contract-registry declaration**,
which changes no runtime behaviour and exists precisely so the mutation detector
covers `payload-manifest` from its first release. `T2b` carries a single-line
registration; it does not carry a licence to edit `src/`.

#### Bounded checkpoints

| Checkpoint | Applies to | Rule |
|---|---|---|
| **No-publish** | Every task | No `twine upload`, no `gh release create`, no `copilot plugin publish`, no marketplace push, no dispatch of `release.yml`'s publish path. Publication is Ship/Orchestrator scope (CP2). Recording a version in `CHANGELOG.md` is not publication. |
| **Rollback** | T7, T7b, T8, T14 | Before the task lands, record the exact pre-change bytes of the file it mutates (`pyproject.toml`, `marketplace.json`, `release.yml`) into `docs/audits/2026-09-03-ship10-payload-evidence/` (the destination authorized in the writable-surface table, cycle 3 finding 6). That record is evidence, never authorization. Recovery is a **forward revert commit** (Rollback R-1). **A destructive restore or overwrite requires fresh live operator approval over a channel the agent cannot synthesize (R-3); with no channel available the agent halts and does not restore (R-4).** *Corrected in cycle 2, finding 11 — cycle 1 prescribed "a single-file restore" as the standard path, pre-authorizing a destructive overwrite that Constitution Principle VII requires an operator to approve.* |
| **Destructive-operation** | T8 (branch (b)), T5, T6, all verification tasks | **Rewritten in cycle 4, finding 3, to close a Constitution Principle VII gap.** The cycle-3 rule prohibited deleting, moving, or overwriting a tracked file **outside** `plugin-payload/` and treated regeneration **into** that tree as "the normal, non-destructive path". That carve-out is wrong: **overwriting or removing tracked content is destructive regardless of which directory it sits in, regardless of whether the manifest resolves it, and regardless of how trusted the generator is.** A trusted generator writing over a tracked file still destroys committed content the operator has not consented to lose, and "it is a declared output root" describes the path's *role*, not the *reversibility* of the write. See the **Principle VII generation rule** below for the binding form. |
| **Published-artifact immutability** | T2a, T10 | v1.5.0 artifacts used as baselines are already published and must never be mutated or retracted (invariant I5). |
| **Red-preservation** | T3a | T3a authors test files under `tests/` only. It must not author or modify the manifest, either schema file, `schema_contracts.py`, `build_support/`, `pyproject.toml`, `marketplace.json`, `plugin-payload/`, or `release.yml` — doing so would make its own cases green and destroy the red observation. |
| **Baseline-fidelity** | T3b, T9–T13 | CHARACTERIZATION cases are observed green **against the baseline (untrimmed) build** from T2a, never against a partially-changed tree. Authoring a CHARACTERIZATION case that is red on the baseline is a defect of the authoring task, not a finding about the baseline. |

#### Point of no return

**Principle VII generation rule (binding; added in cycle 4, finding 3).**

**Classification, evaluated per planned write, before anything is written.** Every
generation run partitions its planned writes into exactly three sets:

* **CREATE** — the target path is **absent** from the working tree **and
  untracked**. Creating it destroys nothing.
* **NO-OP** — the target path is tracked and the bytes to be written are
  **byte-identical** to the tracked content. Nothing is destroyed, so this is
  treated as CREATE-equivalent. *(This is what keeps idempotent regeneration —
  `test_plugin_generation_is_idempotent` — from tripping the gate on every run.)*
* **DESTRUCTIVE** — the target path is **tracked** and either the bytes differ
  (**OVERWRITE**) or the path is no longer resolved by the manifest and would be
  deleted (**REMOVE**).

**The rule.**

1. **A non-empty DESTRUCTIVE set requires fresh, live operator approval, obtained
   in the session performing the run, over a channel the agent cannot
   synthesize (R-3).** This applies **inside** `plugin-payload/` exactly as it
   applies anywhere else. Standing approvals, blanket approvals, approvals
   inferred from a task's acceptance text, approvals recorded in a backlog
   comment, prior-session approvals, and any approval the agent could itself
   author are **audit evidence only and can never serve as this authorization**.
2. **With no such channel available, the agent HALTS and does not perform the
   destructive generation (R-4).** It does not downgrade, partially apply, or
   defer-and-proceed.
3. **A generation run whose DESTRUCTIVE set is empty requires no approval and must
   not demand one.** Creating files that are absent and untracked is explicitly
   permitted unattended. Gating the non-destructive path would train operators to
   approve reflexively, which destroys the value of the gate on the run that
   actually matters.
4. **Branch (a) carries no approval requirement at all.** Under branch (a) no
   `plugin-payload/` tree is materialized, no generation run writes into a tracked
   output root, and the DESTRUCTIVE set is therefore **empty by construction**.
   Requiring — or requesting — operator approval on the no-tree path is a **false
   gate** and is prohibited.
5. **The generator must be able to report the partition before writing.**
   `generate` computes and can print the CREATE / NO-OP / OVERWRITE / REMOVE
   partition of its planned writes, and **refuses to proceed** on a non-empty
   OVERWRITE ∪ REMOVE set without R-3 approval. This is a property of the
   generator (`T6`) consuming the resolver (`T5`), not a property of the plugin
   wiring alone, so **every** consumer of the generation path inherits it.
6. **`generate --check` is read-only and never requires approval.** It writes
   nothing by construction.
7. **Unchanged from cycle 3:** generation writes **only** files the manifest
   resolves; it must never delete, move, or overwrite a tracked file **outside** a
   declared output root under any circumstances, approval or not. Asserted by
   running generation against a dirty working tree and verifying the tracked file
   set outside the output root is unchanged. Scratch workspaces and simulated
   environments live under gitignored temporary paths and must not mutate the
   developer's real workspace, `~/.autoharness/`, installed interpreter, VS Code
   settings, Claude/Codex config, or Copilot CLI plugin registry.

**Why this is not merely procedural.** The first materialization of
`plugin-payload/` under branch (b) is entirely CREATE and needs no approval.
Every **subsequent** regeneration after the manifest changes is OVERWRITE and/or
REMOVE over tracked content — and that is precisely the run in which a manifest
mistake silently deletes payload files a consumer depends on. The cycle-3 wording
exempted exactly that run.

#### Point of no return (irreversibility)

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
  assertions unpack the actual built wheel, the actual built **sdist**, and the
  resolved plugin payload. A source-tree assertion cannot detect a packaging
  defect (R1), and a wheel-only assertion cannot detect an sdist defect (AC3b).
* **V2 — Publish-toolchain check is not satisfied locally.** Per the hatchling
  learning, a local `twine check` is insufficient. Metadata validation must run
  against the **same pinned action toolchain** used by `release.yml`, or be
  explicitly recorded as unverified-until-release. Add an assertion that both
  `core-metadata-version` pins — wheel **and sdist** — survive the refactor (I4).
  The sdist pin is the more fragile of the two: it is currently the sdist target's
  **only** key, so a table rewrite that replaces rather than extends the target
  drops it silently.
* **V3 — Upgrade orphan scan.** Install v1.5.0 into a scratch workspace, upgrade to
  the trimmed build, then enumerate residual engine files and assert the set is
  empty or explicitly expected (R3).
* **V4 — Negative test for the allowlist.** Inject a synthetic unclassified tracked
  path and assert the build **fails**. A fail-closed guard that is never observed
  failing is not known to be fail-closed (AC2/AC8).
* **V5 — Install parity baseline.** Capture `/install-harness` output from the
  untrimmed build first; assert byte-identical output from the trimmed build (I3).
* **V6 — Class-transition ledger.** Every case's declared class implies a required
  pair of observations; `T16` asserts each pair actually occurred (RED-FIRST
  red→green, CHARACTERIZATION green→green). A declared class with no recorded
  transition fails the shipment. This is what stops the two-class contract from
  degrading into unverified labelling.

### Operator checkpoints

* **CP1** — Before `T7`/`T7b`/`T8` wiring lands: operator reviews the resolved
  allowlist and confirms no required path is missing.
* **CP2** — Before publication (Ship/Orchestrator scope, outside this plan):
  release-pipeline dry run confirming **both** metadata pins intact.
* **CP3** — Before any destructive restore or overwrite at any point in this
  shipment: fresh live operator approval per Rollback **R-3**; no channel means
  halt per **R-4**.

### Risky actions

| Action | Risk | Mitigation | Rollback state |
|---|---|---|---|
| Rewrite `pyproject.toml` wheel build table | **High** — breaks publish | Preserve I4 pins; assert by test; V2 | Forward revert commit; payload returns to untrimmed (R-1) |
| Add an sdist `include`/`exclude` table | **High** — the sdist target's only current key is the I4 pin, so a replace-instead-of-extend edit silently drops it and breaks publishing | `test_core_metadata_version_pins_preserved` covers **both** targets as a CHARACTERIZATION case; V2; serialized after T7 by edge | Forward revert commit; sdist returns to untrimmed default sweep (R-1) |
| Add gate step to `release.yml` | **High** — a malformed workflow blocks all releases | Structural test (AC2b) + byte-identity non-regression assertion on triggers/permissions/secrets/SHAs | Forward revert commit; release path returns to current behaviour (R-1) |
| Constrain `marketplace.json` payload | **Medium** — breaks plugin install | V1 + CP1 + AC3c fetchability assertion | Forward revert to `source: "."` (R-1) |
| Generate the tracked `plugin-payload/` tree (branch (b)) | **Medium** — a generation step that writes tracked files | Writes only manifest-resolved files inside `plugin-payload/`; never deletes, moves, or overwrites a tracked file outside it; asserted against a dirty working tree; any removal needs R-3 approval | Forward revert commit removing the tree and restoring `source` (R-1) |
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

> **HISTORICAL `T#` LABELS — READ THIS FIRST (review-fix cycle 3, finding 10).**
> Everything in this subsection and in *§Review-fix cycle 1* below uses the
> **cycle-1** `T#` labels, which later cycles superseded. They are preserved
> verbatim as an audit trail and are **not** the current contract. The
> authoritative current mapping is *§Task decomposition* and *§Prerequisite DAG*.
> The complete cycle-1 → current translation is:
>
> | Cycle-1 label | Current label | Current task ID | Subject |
> |---|---|---|---|
> | `T1` | `T1` | `160.002-T` | plugin-mechanism spike |
> | `T2` | `T2a` + `T2b` | `160.001-T` + `160.018-T` | baseline capture; schema publication |
> | `T3` | `T3a` + `T3b` | `160.005-T` + `160.016-T` | RED-FIRST harness; CHARACTERIZATION harness |
> | `T4` | `T4` | `160.003-T` | manifest authoring |
> | `T5` | `T5` | `160.004-T` | resolver + classifier |
> | `T6` | `T7` | `160.006-T` | **wheel** wiring |
> | `T7` | `T8` | `160.007-T` | **plugin** wiring |
> | *(none)* | `T6` | `160.014-T` | generation command *(added cycle 1, finding 7)* |
> | *(none)* | `T7b` | `160.019-T` | **sdist** wiring *(added cycle 2, finding 3)* |
> | *(none)* | `T14` | `160.015-T` | release-path gate *(added cycle 1, finding 7)* |
> | *(none)* | `T16` | `160.017-T` | transition ledger *(added cycle 2, finding 1)* |
> | `T9`–`T13` | `T9`–`T13` | `160.008/012/013/009/010-T` | verification families |
> | `T15` | `T15` | `160.011-T` | docs + CHANGELOG |
>
> Two references below are **already correct under the current mapping** and are
> not translations: "backlog follow-up on `T5` (`160.004-T`)" and "required
> deliverable on `T15`". Every other `T5`/`T6`/`T7` occurrence in this subsection
> is a cycle-1 label — read it through the table above.

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

**T-number reconciliation notice (review-fix cycle 2, finding 14; extended in
cycle 3, finding 10).** The cycle-1 table above and the cycle-1 findings text use
the **cycle-1** `T#` labels, which later cycles superseded. The complete
cycle-1 → current translation table is at the head of *§Cycle 1 findings*; that
table is the single place the mapping is stated. The cycle-1 record is preserved
here as a historical audit trail and is **not** the current contract. The
authoritative current mapping in both directions is the **§Task decomposition**
table and the **§Prerequisite DAG**; every queued task record's `(Tn)`
back-reference was re-verified against those two tables in cycle 3.

### Review-fix cycle 2 (Stage remediation of the current-head seven-persona re-review)

The seven-persona re-review of `73cb51e6` returned **BLOCKED** with 17 findings.
**All 17 are dispositioned below**, including the five whose remediation surface
is another shipment — recorded here so this plan's disposition table is complete
and a later reader does not have to reconstruct which findings were handled where.

| Finding | Verdict | Remediation |
|---|---|---|
| **1 — TDD architecture incomplete** | **Legitimate P0** | The single "everything must be red" rule was wrong in both directions: it demanded a manufactured red on cases that *correctly* start green (the wheel already excludes `.backlogit/`/`tests/`/`experiments/`; both `core-metadata-version` pins already exist), and it left the install/upgrade/resolver/registration/integrity families with **no red owner at all** because they were authored after the wiring. Replaced with a **two-class contract** — `RED-FIRST` (observed failing, then green) and `CHARACTERIZATION` (observed green **against the baseline build**, then green again). Classes are mutually exclusive and exhaustive; a green-on-arrival RED-FIRST case and a red-on-arrival CHARACTERIZATION case are each defects of the *authoring* task. Enforced by edges, not prose: `T3a`/`T3b` split the harness by class; `T9`–`T13` are re-scoped to author and observe **against the baseline** and now **block** `T7`/`T8`; schema publication moved out of `T2` into `T2b`, which is blocked by `T3a` and named green owner of two RED-FIRST cases, closing the "production before a red owner" gap; and `T16` is a terminal ledger asserting every declared class actually transitioned as declared. |
| **2 — `160.014-T` had no achievable committed completion state** | **Legitimate P0** | Confirmed: `T6` was green owner of `test_generated_tables_match_manifest`, which asserts the **committed** tables match — while `T6`'s own scope forbade committing into `pyproject.toml`/`marketplace.json` because those files belong to `T7`/`T8`. The case conflated a *generator* property with a *wiring* property and is split along that seam: `test_generate_emits_expected_tables_to_a_scratch_target` (green owned by `T6`, reachable entirely in scope, mutates no repository file) and `test_{wheel,sdist,plugin}_generated_table_matches_manifest` (green owned by `T7`/`T7b`/`T8`, each for the file it may edit). `T6`'s prohibition is unchanged; downstream gating is sharpened, since each channel's parity case now blocks on that channel's own wiring task. |
| **3 — Python sdist omitted** | **Legitimate P0** | Confirmed and the most consequential finding. `[tool.hatch.build.targets.sdist]` declares **only** `core-metadata-version = "2.4"` — no `include`, no `exclude` — so hatchling's default sweep packages the entire project, and `release.yml`'s `uv build` → `dist/*` publishes it to PyPI **and** attaches it to the GitHub release. A wheel-only trim removes **nothing**: every withheld file still ships. Added **AC3b** (manifest-derived sdist table, named exclusion/inclusion cases, byte-size + disclosure reporting, I4 pin preservation on the sdist target, release-path coverage), added task **`T7b` (`160.019-T`)** decomposed out of `T7` on size and serialized after it by edge (same file), extended the generation command's channel enum to `{wheel\|sdist\|plugin\|all}`, and extended AC2b's gate to assert all three channels are covered. |
| **4 — Freeze-scope allowlist incoherent** | **Legitimate P1** | Confirmed: H2's writable surface omitted `schemas/payload-manifest/1.0.0.schema.json` while AC1 made the versioned mirror mandatory, and forbade **all** `src/` edits while requiring `SCHEMA_CONTRACTS` registration as a non-deferrable criterion — so the plan's acceptance criteria were unexecutable under the plan's own safety mode. H2's writable surface is now an explicit **path → authorized task → bound** table naming both schema documents and narrowly authorizing `src/autoharness/schema_contracts.py` **for `T2b` only, registration entry only**, with an explicit statement of why the runtime-behaviour freeze and the contract-registry authorization are not in conflict. |
| **5 — Plugin fallback branch (b) unpublishable** | **Legitimate P0** | Confirmed: `dist/.gitignore` contains `*`, so `source: "dist/plugin"` points at a path absent from any consumer checkout — an install failure, not a trim. Added **AC3c**: `source` must resolve to a consumer-fetchable path; branch (b) generates a **tracked, committed** `plugin-payload/` tree via the same generate-and-assert shape H1 already uses for the wheel table; pointing `source` at any gitignored/untracked path is prohibited, as is assuming unevidenced marketplace filtering behavior; and a branch **(c)** is added so `T1` halts to the operator rather than inventing a mechanism. `plugin-payload/**` is classified in AC11 and excluded from itself so generation cannot recurse. *(Superseded in cycle 3, finding 9: "classified in AC11 as a plugin **input**" was the defect — the tree is now an **`AC3d` generated output root**, removed from classifier inputs before classification in all three channels while remaining the published, tracked directory. See §AC3d.)* |
| **11 — Destructive rollback self-authorized** | **Legitimate P1** | Confirmed: the H2 rollback checkpoint prescribed "a single-file restore" as the standard recovery path, pre-authorizing a destructive working-tree overwrite that Constitution Principle VII requires an operator to approve — at the moment (a failed release) when the tree most likely holds unrelated uncommitted work. Added **Rollback R-1…R-5**, adopting SHIP-4 Decision G's authorization contract verbatim so the harness carries one answer, not two: forward revert commits are the default; recorded pre-change bytes are **evidence, never authority**; any destructive restore needs a **fresh live non-synthesizable operator approval**; no channel means **halt, do not restore**; and read-only alternatives (`git show`, `git diff`, scratch materialization) cover the verify-don't-restore case. Added operator checkpoint **CP3**. |
| **13 — Source traceability unauditable** | **Partially legitimate; one half a false positive** | `E9E5E6CC` **is** durable at HEAD in the official archive record `.backlogit/archive/stash.jsonl` (tracked, blob `aef5f126`), carrying its own forward reference to `160-F`/`168-S`. The reviewer's search missed it because consumed entries are **archived**, not retained in the active stash — recorded as a false positive with evidence. The legitimate half: the archived entry's `HARVESTED` annotation still read `160.001-T..160.011-T`, stale against the 19-task set; it is reconciled through the official stash-edit operation. `AB387F16` is a **pre-persistence temporary working ID** superseded before any record was written; it has no durable entry and is **not** given one, because fabricating a record to satisfy a lookup manufactures false provenance. Its correct and complete disposition is the superseded-ID note on `160-F`. §Traceability now states all of this explicitly. |
| **14 — Stale ownership and numbering references** | **Legitimate P1** | Confirmed: `160.002-T` pointed generation at `160.004-T` (it is `160.014-T`) and the release gate at `160.006-T` (it is `160.015-T`); `160.007-T` repeated both errors. Corrected through official `backlogit update` operations, and every `(Tn)` back-reference re-verified against the rewritten decomposition table and DAG. The cycle-1 review record above is explicitly marked as historical with a mapping notice rather than silently rewritten, so the audit trail survives. |
| **15 — Centralization contract unsatisfiable** | **Legitimate P1** | Confirmed: AC2d demanded "exactly one authored occurrence of the prefix list **in the repository**", but the plan, the deliberation, and the task record each necessarily enumerate the prefixes to specify the rule — so the contract failed the moment it was written. The test's surface is narrowed to **executable and configuration surfaces** (`build_support/**`, `src/**`, `tests/**`, `pyproject.toml`, `marketplace.json`, `.github/workflows/**`, and the manifest), with the manifest's `target_workspace_paths` key as the one occurrence; documentation and backlog records are outside it. Prose now refers to the key symbolically wherever the values are not themselves the subject. The drift guarantee is preserved — one executable source of truth — without making explanation illegal. |
| **16 — `160.001-T` under-scoped and under-sized** | **Legitimate P1** | Confirmed: one `S`/`low` task combined baseline capture across three channels, two schema documents, runtime contract registration, and an immutability assertion — four deliverables with different reversibility. Split into `T2a` (`160.001-T`, baseline characterization capture, `S`/`low`) and `T2b` (`160.018-T`, schema publication + registration + pair-divergence assertion, `S`/`medium`). IDs, shipment membership, the decomposition table, the DAG, and this review are all updated to match. |
| **17 — Keep it simple and composable** | **Accepted as a constraint** | Honoured by construction. The remediation adds **one concept** (a two-valued case class) and **four tasks**, and otherwise reuses shapes the plan already had: the sdist reuses the wheel's generate-and-assert mechanism; branch (b) reuses the same mechanism for a tracked tree; the rollback contract reuses SHIP-4 Decision G rather than inventing an approval model; the centralization fix *narrows* a test rather than adding indirection. No build hook, no runtime framework, no new CLI, no speculative abstraction was introduced. |
| **6 — SHIP-2 C6 must fail closed** | **Legitimate P0 — remediated in SHIP-2** | Confirmed. The probe requests the *exact-version* endpoint `https://pypi.org/pypi/autoharness/{version}/json`, which names the version in the path, so a conforming PyPI can return only `404` or a `200` naming *that* version. A `200` naming a different version is a response the protocol does not permit — positive evidence of a cache, mirror, or interception anomaly, not evidence of absence. Cycle 1's "probe proceeds" discarded a *detected* anomaly, which is worse than the original fail-open `else:` branch. Fixed in `docs/plans/2026-08-31-ship2-release-ci-fail-closed-gates-plan.md` (new binding **H2b**, C6 row reversed) and in `152.002-T`, with a hermetic expectation asserting the helper **raises** and neither proceeds nor exits with C2's already-published code. **Discriminating power preserved**: C2 and C6 still differ *in kind*, so a "did the request succeed" probe still passes C2 and fails C6. |
| **7 — SHIP-6 tool-name prohibition too broad** | **Legitimate P1 — remediated in SHIP-6** | Confirmed and narrow. The H6a-CLARIFICATION body was already correct; the defect was the trailing **ACCEPTANCE** line, "no hardcoded tool-name literal anywhere in renderer, template, or test fixtures", which contradicted **H1** (concrete tool-scoped block declarations are *required*) and the H6a synthetic-registry test (which needs a fixture carrying a concrete synthetic `tool_name`). The task's acceptance therefore forbade the artifacts its own binding requirements mandate and was unsatisfiable. `156.002-T` now prohibits exactly the **duplicated validation set** — zero authored occurrences of a hardcoded *list/set/enum/default* of valid names — and explicitly permits declarative identities, fixture values, and prose. The discriminator is the synthetic-registry test, not a grep. |
| **8 — SHIP-7 enumerated fields miss future keys** | **Legitimate P1 — remediated in SHIP-7** | Confirmed. An enumerated surface table is a denylist wearing an allowlist's clothes: it omitted top-level `schema_version` (declared `1.0.0` in this workspace) and would omit every future template-owned key. Replaced with **H3a-RECURSIVE** in the SHIP-7 plan and in `157.002-T`: recursive value parity over **every leaf path in the parsed template document**, minus the closed, path-specific **H3b** override allow-list. Template-present/installed-absent is a failure; installed-only paths are INFO. Also resolved a cycle-1 self-contradiction — `directory` was listed *both* as value-equality and as override-eligible; it is **override-eligible** (this workspace uses the legacy `.backlogit` root). |
| **9 — SHIP-8 undefined budget language** | **Legitimate P1 — remediated in SHIP-8** | Confirmed. The SHIP-8 plan had already withdrawn the aggregate budget in favour of the unsized-only predicate (`size_composition.unsized == 0`), but `158.003-T` still required failing "when the composition exceeds the declared budget" — a threshold that is declared nowhere, so an implementer would have had to *invent* a number and gate shipments on it. Removed, and all five plan-declared boundary cases **B1–B5** are now required by name, including the two fail-closed ones cycle 1 omitted: **B3** (empty histogram → pass) and **B4** (absent `unsized` → **fail closed**; a missing key is not zero). B3/B4 are the two directions a naive `if unsized:` truthiness check gets wrong. *(Extended in cycle 3, finding 3: the required boundary set is now **B1–B11**, adding malformed-value cases — `false`, `0.0`, `null`, string `"0"`, negative, and malformed histogram — because `unsized == 0` is `True` for `False` and `0.0` in Python, so the cycle-2 predicate still failed open on a bool. Validation now precedes the equality.)* |
| **10 — SHIP-4 missing outcome matrix and stale approval text** | **Legitimate P1 (two parts) — remediated in SHIP-4** | Both confirmed, both narrow. (a) `154.004-T` had Conditions A/B/C in prose only, burying two distinguishable outcomes inside Condition A — one of them a **halt**. Added a binding five-row matrix **M1–M5** (language variant / generic fallback / neither-template fail-closed halt / reviewer-not-selected no-op / already-composed graceful reference), each a required test case with an asserted observable, and each with the distinguishing marker that stops one branch silently passing for another. (b) Decision G (G1–G9) was already fully correct and had demoted the `APPROVAL: P-007-ARCHIVE-RESTORE` comment to evidence-only, but the plan's Tasks-table row 2 and `154.002-T`'s **title** still read "gate … behind the named `APPROVAL: P-007-ARCHIVE-RESTORE` signal" — the exact self-satisfiable formulation finding 14 withdrew. **Titles are executed**, so both were rewritten to require Decision G1's fresh, live, non-synthesizable operator approval, and an explicit executable-text rule was added to the plan. |
| **12 — SHIP-3 fixed-length vector matrix contradictory** | **Legitimate P1 — remediated in SHIP-3** | Confirmed. **TC2** declares the token encoding *fixed length*, so there is exactly one valid length and no distinct minimum-valid and maximum-valid token; **V-c** nonetheless demanded both. An author honouring both clauses would have had to invent a variable-length encoding (contradicting TC2 and reopening the shell-safety and truncation risks it closes) or record the same token twice under two labels. Replaced with **one canonical valid vector**, plus new **V-c2** one-short/one-long **invalid** boundary vectors whose expected observable is fail-closed (non-zero exit, named error, no lock, **no digest** — they are rejected before a digest exists), plus new **V-c3** cross-platform interoperability expectations, because a length check written with `.Length` over UTF-16 code units versus a byte-oriented POSIX check is exactly where the two implementations silently disagree. |

**Defect found and fixed during cycle-2 self-review (not reported by the
reviewer).** Ten rows of the new case table named `T16` — the transition ledger —
as their `Green/preservation owner`. That is incoherent: `T16` *verifies* that
transitions happened as declared and implements nothing, so a RED-FIRST case
green-owned by `T16` had **no implementing task at all**, and a CHARACTERIZATION
case preservation-owned by `T16` named a task that changes nothing it could break.
All ten now name the task whose change actually produces the second observation
(`T7`, `T7b`, `T8`, or the combination). `T16` is now purely a verifier, which is
what the two-class contract requires of it. Recorded here because a fix nobody
asked for is exactly the kind that gets silently reverted later.

**Gate after cycle 2: PASS — 19 tasks; DAG acyclic and machine-encoded (2 roots
`T1`/`T2a`, 1 sink `T15`, 19-node topological order verified); plan table ↔ queue
↔ shipment `168-S` bijection exact at 19/19/19; all 19 `Tn` back-references
consistent in both directions; the cycle-2 case set (45 cases) each carrying a declared class, an
author, and a real implementing green/preservation owner; all three publication
channels (wheel, sdist, plugin) covered by manifest overlay, generation, wiring,
and release gate; safety-mode allowlist coherent with acceptance criteria; and no
destructive operation self-authorized.**

Two review-fix cycles used of the three available; one remains.

*Cycle-3 note: the `45 test cases` figure above is the **cycle-2** ledger size. Cycle 3's finding-5 reconciliation raised the canonical ledger to **51 cases (35 RED-FIRST, 16 CHARACTERIZATION)**; see §Case table, which is authoritative.* **Cycle-4 superseding note (findings 5, 9, 15): the canonical ledger is now 52 cases — 35 RED-FIRST, 17 CHARACTERIZATION. The 51/35/16 figure is a cycle-3 record and is no longer current.**


### Review-fix cycle 3 (Stage remediation of the final seven-persona review)

The final seven-persona review of `67636bad` returned **BLOCKED** with fifteen
findings. This is the **third and last** permitted fix cycle, so nothing in scope
is deferred: every legitimate same-contract-surface P0/P1 finding and every
tightly-coupled P2 consistency defect is remediated here, through official
backlogit operations, with **no Git, source-implementation, PR, claim, or
worktree action taken**.

**Method note (finding 14).** Two prior cycles amended task records by
**appending** `=== REVIEW-FIX CYCLE n AMENDMENTS ===` blocks. That is how the
authoritative ledger and the executable records drifted: a reader met the
superseded paragraph first and the correction second, and nothing said which
won. Every task body touched in this cycle was **replaced wholesale** via
`backlogit update --description`, so each record now carries exactly **one
canonical statement per subject** and every append seam is gone. A repository-wide
scan for `=== REVIEW-FIX`, `=== ORIGINAL TASK`, and `=== RE-SCOPE` markers across
`.backlogit/queue/**` returns zero hits.

| # | Finding | Verdict | Remediation |
|---|---|---|---|
| **1** | SHIP-2 `152.001-T` still said a mismatched-version `200` means PROCEED | **Legitimate P0** | Body replaced. New **BINDING H2b** paragraph makes a version mismatch a fail-closed re-raised transport/integrity error and names the cycle-1 "probe proceeds" rule **WITHDRAWN**, so the record carries one answer. C2/C6 discriminating power is restated and preserved: the two still differ *in kind*. `152.002-T` was re-read and already correct — no change, recorded so the no-op is not mistaken for an omission. |
| **2** | SHIP-4 `154.004-T` M4 asserted `{L}.instructions.md` is globally absent when the technology reviewer is not selected | **Legitimate P1** | Confirmed: that assertion conflicts with unconditional primary-language instruction generation, so M4 would fail on a workspace that correctly installs the instruction for other reasons. M4's required outcome is rewritten to **"the F1 co-installation rule does not fire"**, observed through **install-unit / provenance attribution** — never through file presence or absence. Added **M4 SCOPE** and **M4 DISCRIMINATING POWER** paragraphs, and matching edits to the SHIP-4 plan's Decision F Condition B row and its Propagation block. Independently required primary-language instructions are no longer suppressed by M4. |
| **3** | SHIP-8 unsized predicate still fails open on malformed values | **Legitimate P0** | Confirmed: `unsized == 0` is `True` for `False` **and** for `0.0` in Python, so the cycle-2 predicate passed a shipment whose `unsized` was a bool. `158.003-T` now requires **value validation before the equality** — `isinstance(x, int) and not isinstance(x, bool)`, non-negative, mapping-shaped histogram — with named type/range/shape errors. The plan's boundary table grows **B1–B5 → B1–B11**, adding `false`, `0.0`, `null`, string `"0"`, negative, and malformed-histogram cases, each fail-closed. `158.002-T` (the red half) now requires T2's red observation to cover **both** B2 (`unsized: 1`) and B6 (`unsized: false`) — B6 is the discriminator a fail-open implementation passes. |
| **4** | SHIP-10 AC1 still named wheel + plugin only | **Legitimate P1** | AC1 and every closed-channel statement in the plan now read **wheel + sdist + plugin**. Eleven occurrences aligned. The channel enum is closed at three members plus the `all` aggregate in AC2c, in `160.014-T`, in `160.018-T`'s schema declaration, and in `160.004-T`'s resolver. |
| **5** | Canonical case ledger and task records inconsistent, especially T9–T13 | **Legitimate P0** | The **§Case table** is rewritten as a bijective 51-row ledger carrying, per case: exact test name, class, author, **observed initial state with its concrete failure mode**, green/preservation owner, and the machine edge forcing author before owner. Five previously unnamed or unledgered cases are added — including **`test_plugin_version_resolves_from_plugin_manifest`**, which existed in `160.013-T` but in no ledger. Two cases are reclassified on the merits: `test_no_engine_records_in_target_workspace` → CHARACTERIZATION (baseline-true; demanding red would require breaking a correct installer), `test_gate4_crossrefs_intact_in_built_payload` → RED-FIRST scoped to the **trimmed** artifact (as CHARACTERIZATION it was vacuous against an untrimmed payload containing everything). Whole-family class labels are withdrawn — four of five families are genuinely mixed, so class is declared **per case** only. One missing edge is encoded: **`T5` ← `T9`**, because `T9` authors a case `T5` greens. `T9` authors it against the **expected-absent** `classify_target_workspace_path` interface (an import-error red) rather than waiting for `T5` to build it, which is what created the ordering gap. All nineteen task bodies were replaced to match the ledger row-for-row. |
| **6** | `T2a`'s durable baseline had no H2-writable destination | **Legitimate P1** | Confirmed, and broader than reported: **six** mandatory durable outputs had no authorized destination. H2's writable-surface table gains **three** rows, deliberately few: `docs/spikes/2026-09-03-ship10-plugin-channel-mechanism.md` (T1's finding); **`docs/audits/2026-09-03-ship10-payload-evidence/**`** — one bounded evidence surface shared by T2a's baseline, T7/T7b/T8/T14's pre-change-byte captures, and T16's transition ledger; and `tests/fixtures/payload-baseline/**` for T2a **fixture data only**, added because the baseline inventory is consumed by tests. An eight-row **mandatory-durable-output audit table** now names every required artifact, its producing task, and its authorized path, so a later addition cannot quietly land without one. No new store was invented — existing `docs/`, `tests/` and closure conventions are reused. |
| **7** | `T14` (`160.015-T`) still prescribed a single-file restore | **Legitimate P1** | Body replaced. Single-file restore is marked **WITHDRAWN**; the default and only pre-authorized recovery is a **forward revert commit** (R-1). Any destructive restore or overwrite requires **fresh live operator approval obtained in the session performing it over a channel the agent cannot synthesize** (R-3); with no channel available the agent **halts and does not restore** (R-4). Recorded pre-change bytes are **evidence, never authorization**. The same contract is now stated identically in `160.006-T`, `160.007-T`, and `160.019-T`, each naming its evidence destination. |
| **8** | `T5` (`160.004-T`) carried a stale command set and a repository-wide prefix rule | **Legitimate P2, tightly coupled** | Superseded text removed rather than annotated. One authoritative command remains — `python -m build_support.payload generate --channel {wheel\|sdist\|plugin\|all}`, `all` meaning all three — and the AC2d single-occurrence rule is scoped to **executable and configuration surfaces** (`build_support/**`, `src/**`, `tests/**`, `pyproject.toml`, `marketplace.json`, `.github/workflows/**`, the manifest). A repository-wide rule was unsatisfiable: the plan, the deliberation, and the task records must all name the prefixes to be intelligible. |
| **9** | Branch (b) recursive-output defect | **Legitimate P0** | Confirmed and load-bearing. Classifying `plugin-payload/**` as a plugin **input** while the generator materializes **into** that tree makes run two resolve `plugin-payload/**` as source and write it inside itself — `plugin-payload/plugin-payload/…`, deeper every run — and `generate --check` would then report drift that regenerating can **never** clear, failing the release gate permanently. New **§AC3d** defines `generated_output_roots` as a key **distinct from** `include`/`exclude`: paths beneath a declared output root are removed from the tracked-path enumeration **before** classification, in **all three** channels, and are therefore neither classified nor unclassified (so AC2 never fires on generated content). **Exclusion from classifier input is not exclusion from publication** — the tree stays tracked, committed, consumer-fetchable, and remains what `source` points at, preserving the accepted publishable-fallback decision. Self-exclusion lives in the **resolver**, not the generator, so every resolver consumer is protected. Three guard cases added: `test_generated_output_root_excluded_from_classifier_inputs` (green T5), `test_plugin_generation_is_idempotent` (green T6), `test_plugin_payload_tree_is_self_excluded_and_flat` (green T8). **Cycle-4 superseding note (finding 6): the third case is now `test_plugin_payload_conforms_to_the_selected_strategy`, with branch-aware semantics — tree-absence could not serve as its red condition because branch (a) validly leaves the tree absent. Green owner is unchanged (T8).** |
| **10** | Stale `T#` and ownership references | **Legitimate P2, tightly coupled** | `160.012-T` said `(T2)` where it meant `(T2a)` — corrected. Spike and release-owner references re-verified across all nineteen records. The appended plan-review sections retain the **cycle-1** labels as an audit trail, but a complete **cycle-1 → current translation table** now sits at the head of §Cycle 1 findings, naming every label, its current label, its task ID, and its subject, plus an explicit note of the two references that are already correct under the current mapping and are not translations. All nineteen `(Tn)` back-references were re-verified mechanically in both directions. |
| **11** | Archived stash `E9E5E6CC` traceability | **Legitimate P1 (as scoped)** | The archived entry is **not** hand-edited: it is immutable by design, and rewriting it would erase the historical fact that the harvest produced eleven tasks and make the archive an unreliable witness for every other entry. Instead a durable **forward correction** was appended to feature `160-F` through the official comment operation (`.backlogit/logs/160-F.jsonl`, actor `stage`), **enumerating** `E9E5E6CC → 160-F → 160.001-T … 160.019-T → 168-S` member by member rather than as a range — a range silently asserts density, so a retired ID inside it would still read as correct. `160-F`'s body and §Traceability both reference the correction. **`AB387F16` is not fabricated**: it is a pre-persistence temporary working ID that never had a durable record, and manufacturing one to satisfy a lookup would manufacture false provenance. |
| **12** | P-021 capture completeness and a duplicate pair | **Legitimate P1** | `477D37BD`, `2FA67AAC`, `39A4DDEB`, and `75A78433` each now state **PR number, review-thread ID, task ID, feature ID, and shipment ID independently**, as a concrete value or an explicit `N/A` with its reason; `75A78433` also gained the missing `requires deliberation:` line (three separable decisions, the destructive migration among them, so it cannot be auto-authorized) and a `DISCOVERY-STATUS: CLEAN` record. Where an ID exists only as **coupling** rather than ownership (`2FA67AAC` → `155.004-T`/`155-F`/`163-S`; `39A4DDEB` → `155-F`/`163-S` as observed instances) it is recorded as such and **not** promoted into an owning field. Duplicate pair `9938CA1D` / `24374649` reconciled into the **earliest** entry `24374649` (08:51:58 vs 08:52:34), absorbing the duplicate's five source-ref fields and its residual-risk statement; `9938CA1D` was **archived** via the official `backlogit stash archive` operation, never destructively removed, because a duplicate is itself evidence that one expansion was captured through two intake paths. |
| **13** | `160.009-T` support-matrix table missing its delimiter row | **Legitimate P2, tightly coupled** | Delimiter row `\|---\|---\|---\|` added; the table now renders as a table rather than as three run-together lines. |
| **14** | Authoritative ledger and executable records had already drifted | **Legitimate P1 (maintainability)** | Addressed structurally rather than cosmetically — see the **Method note** above. Superseded paragraphs were **removed**, not annotated, wherever backlogit's whole-body replacement supported it. Where a *review-history* record had to stay (it is an audit trail, and rewriting history is the failure mode this finding warns about), the superseding cycle-3 statement is attached inline at the point of the stale claim, so no reader meets a superseded assertion without its correction. |
| **15** | Re-evaluate all 19 tasks after correction | **Required, performed** | Results in §Cycle 3 deterministic verification below. |

#### Cycle 3 deterministic verification

Every check below was executed mechanically against the working tree, not asserted.

| Check | Result |
|---|---|
| Task count | **19** tasks under `160-F` |
| Plan ↔ queue ↔ shipment bijection | **19 / 19 / 19**; `168-S` manifest carries **20** members (feature + 19 tasks) |
| `(Tn)` back-references | 19/19 present, **unique**, and consistent with §Task decomposition in both directions |
| Size enum | all `S` or `M` — **zero** tasks at `L`/`XL`, so no task exceeds the 2-hour rule on the effort axis |
| Complexity enum | all in `{trivial, low, medium, high}`; the two `high` tasks (`T1` spike, `T8` plugin wiring) are de-risked by the blocking spike edge `T8 ← T1` |
| DAG acyclicity | **acyclic** — all 19 nodes topologically ordered; roots `T1`/`T2a`, sink `T15` |
| Encoded edges ↔ documented DAG | exact match, including the retained `T15` edges and the new `T5 ← T9` |
| Case-ledger bijection | plan **51** unique cases ↔ queue **51** unique cases; **zero** in one and not the other |
| Class totals | **35 RED-FIRST / 16 CHARACTERIZATION**; per-author split verified against the ledger table row by row |
| Author attribution | every case name present in its **authoring** task record — 51/51 |
| Owner attribution | every case name present in **every** named green/preservation owner record — 51/51 (four Python-channel preservation cases were missing from `T7b` and were added) |
| Observed initial state | **51/51** rows state a concrete initial state; **zero** missing RED observations |
| RED-FIRST ordering | all **35** red cases have an encoded edge placing the author before every green owner |
| Append seams | **zero** `=== REVIEW-FIX` / `=== ORIGINAL TASK` / `=== RE-SCOPE` markers remain in `.backlogit/queue/**` |
| Preserved decisions | wheel + sdist + plugin closed channels ✔; tracked publishable plugin fallback with self-excluded generator input ✔; `167-S` blocked by `168-S` ✔; workspace-wide section-marker issue still separately captured ✔ |

**Gate after cycle 3: PASS. No in-scope P0 or P1 finding remains open.** Three
review-fix cycles used of the three available; the budget is exhausted, and this
plan is harvest-complete and execution-ready for Ship.

> **Cycle-3 gate verdict SUPERSEDED.** Post-cycle-3 verification found fifteen
> further in-scope defects (below). The operator explicitly extended the Stage
> review-fix budget beyond the normal three-cycle limit to close them. The
> authoritative gate verdict for this plan is the **cycle 4** verdict at the end
> of this document; the PASS above is a record of the cycle-3 moment only.
### Review-fix cycle 4 (Stage remediation under an operator-extended budget)

The operator explicitly extended the Stage review-fix budget beyond the normal
three-cycle limit and directed autonomous continuation until the staging gate is
genuinely complete. This cycle closed fifteen post-cycle-3 findings. Every fix
used official backlogit operations; no Git, source, PR, claim, or worktree action
was taken. Where a correction touched executable text, the task section was
**replaced wholesale** rather than annotated, so no superseded instruction remains
readable as live guidance; clearly-marked historical review records are preserved.

| # | Finding | Verdict | Remediation |
|---|---|---|---|
| 1 | SHIP-4 `154.003-T`: acceptance demanded "both instruction templates + dogfood mirrors" while the body established that `harness-architecture.instructions.md.tmpl` does not exist and must not be created | **Legitimate P0** (self-contradictory acceptance) | Body replaced. Acceptance now names an explicitly **asymmetric** three-file set — one role-enforcement template + its mirror, plus the harness-architecture **dogfood mirror only**. Creating the nonexistent template now **fails** acceptance |
| 2 | SHIP-8 `158.002-T` authored red tests for **B2/B6 only**; B1, B3–B5, B7–B11 were "authored there" inside the implementing task `158.003-T` | **Legitimate P0** (implementer authors its own tests) | `158.002-T` replaced: owns **all** B1–B11, partitioned **Class R** (8 red-first: B2, B4, B6, B7, B8, B9, B10, B11 — including the strict-integer discriminator B7 `0.0`/bool/null/string/missing/negative and the malformed/empty histogram) and **Class C** (3 characterization: B1, B3, B5, which expect a pass and are therefore green at baseline and provably not red-able). `158.003-T` authors **no** case and accounts for 8 red→green + 3 green→green = 11. Direct edge `158.003-T ← 158.002-T` encoded |
| 3 | Principle VII exempted generation overwrites **inside** tracked `plugin-payload/` from live approval | **Legitimate P0** (the dangerous run was the exempted one) | Planned writes are partitioned **CREATE / NO-OP (byte-identical) / OVERWRITE / REMOVE**. A non-empty OVERWRITE ∪ REMOVE requires **fresh, live, non-synthesizable operator approval** (R-3) or **HALT** (R-4), regardless of generator trust or directory. An empty set proceeds with **no** approval, and branch (a) — empty by construction — **must not** demand one (false gates prohibited). `--check` is read-only and never gated. Enforcement sits in the generator (T6) so all callers inherit it |
| 4 | T6 `160.014-T` did not depend on spike T1 `160.002-T`, though branch a/b/c determines generator behavior | **Legitimate P1** | Edge `160.014-T ← 160.002-T` encoded and documented in the DAG and plan tables. **No cycle**: T1 is a DAG root with no prerequisites |
| 5 | `test_plugin_source_path_is_tracked_and_fetchable` cannot be red-first — baseline `source: "."` is already tracked and fetchable, and branch (a) preserves it | **Legitimate P1** (unachievable red) | Reclassified **CHARACTERIZATION**, author moved **T3a → T3b**, T8 becomes **preservation** owner. Author/class totals, owner edges, ledger, task text and T16 all updated |
| 6 | `test_plugin_payload_tree_is_self_excluded_and_flat` used tree **absence** as initial red, but branch (a) validly leaves the tree absent forever | **Legitimate P1** (branch-invalid red) | Renamed `test_plugin_payload_conforms_to_the_selected_strategy` and made **branch-parametric**: the selected manifest-derived strategy is **required data** (undeclared ⇒ fail). Branch (a) asserts **no materialized tree and a natively-filtered payload**; branch (b) asserts a **tracked, flat, self-excluded tree**. Baseline red survives in **both** branches via the conjunction with file-set equality (the baseline payload is the whole repo). Class/author/owner unchanged |
| 7 | T3a/T3b/T9–T13 first observations — mandatory and consumed by T16 — had **no authorized durable destination** | **Legitimate P0** (task cannot legally produce its own required deliverable) | The **single** bounded evidence surface was extended, not duplicated: `docs/audits/2026-09-03-ship10-payload-evidence/observations/{T3a,T3b,T9,T10,T11,T12,T13}.json`, one file per authoring task. Machine-readable handoff fields: `test_name`, `declared_class`, `author_task`, `first_observation`, `observed_at`, `command`, `exit_status`, `failing_assertion`, `evidence_ref`. T16 **joins on `test_name`** and reads without modifying |
| 8 | T2b `160.018-T` and T6 `160.014-T` are green owners that author no case, yet both granted themselves `tests/` writes | **Legitimate P0** (green owner could weaken its own tests) | `tests/**` write grants removed from both. T2b is confined to exactly three files; T6 to `build_support/` and nothing else. T2b deliverable (3) reworded to **satisfy** `test_schema_live_and_versioned_mirror_agree` (authored by T3a), not author it. H2 aligned |
| 9 | AC2d scanned `tests/**` wholesale for exactly-one occurrence while `160.018-T` permitted fixtures to name target prefixes | **Legitimate P1** (mutually unsatisfiable) | One consistent rule adopted: **exactly one authored occurrence** across `build_support/**`, `src/**`, `tests/**` **excluding `tests/fixtures/**`**, `pyproject.toml`, `marketplace.json`, `.github/workflows/**` and the manifest. The guarantee is preserved by a **derivation assertion** — nothing executable may read prefixes from a fixture or test constant; only `classify_target_workspace_path` reading the manifest key. A fixture literal is inert data; a fixture literal something *reads* is a second source of truth. Both halves are asserted by the new case `test_target_workspace_prefixes_have_exactly_one_authored_occurrence` (AC2d had described this test in prose but **no ledger row ever named it**, leaving it invisible to T16 and unowned) |
| 10 | H2 writable surfaces did not cover every mandatory writer | **Legitimate P1** | Audited every task against its declared surface. T1 spike record, T2a baseline, all seven observation producers, the four pre-change byte captures and the T16 ledger are now authorized. The seven producers carry the authorization **in the operative SAFETY MODE clause**, not merely further down the record, since a destination named only in prose still reads as unauthorized under freeze-scope. One bounded `docs/audits/…` surface plus the explicit fixture path; **no task requires an unauthorized path** |
| 11 | Live decision and plan Problem/Goal text still said "both channels" (wheel + plugin) after the sdist became a third channel in cycle 2 | **Legitimate P2** (stale authoritative text) | Current deliberation Decision and plan Problem/Goal/hardening rows now read **wheel + sdist + plugin**. Historical two-channel framing (Options considered, Channel A/B, the Option 2 label) is **preserved verbatim and explicitly marked** as historical |
| 12 | `160.010-T` carried a bare `{{AUTOHARNESS_VERSION}}` token in ordinary prose while claiming none | **Legitimate P2** | Prose made symbolic; the exact literal is reserved to a single fenced fixture/test example. Verified **zero** bare tokens outside fences |
| 13 | Forward-correction comment pinned whole-archive blob `aef5f126` "at HEAD", made stale by later archive mutation | **Legitimate P2** | Correction **appended** (no history rewritten). Durable reference is entry ID **`E9E5E6CC`** + path; the blob reference is now **commit-qualified** (`35c081d5:.backlogit/archive/stash.jsonl` = `aef5f126…`), with HEAD blob `7a92cc5f` at `a03a6ff0` recorded as measurement only. A whole-file blob is inherently unstable for an append-only archive, so blob refs must always be commit-qualified |
| 14 | SHIP-4 `154.004-T` said "four distinguishable outcomes" / "two of the four under Condition A" though the matrix enumerates five rows, three under A | **Legitimate P2** (tightly coupled prose) | Corrected to **five** and **three (M1, M2, M3)**, noting M3 is a HALT. Withdrawn wording quoted only inside the correction |
| 15 | Terminal PASS must not be restored until every derived number is recalculated | **Legitimate P1** (process) | All derived values recomputed **mechanically** below, not asserted. Cycle-3 PASS marked SUPERSEDED in place |

#### Cycle 4 deterministic verification

Every check was executed mechanically against the working tree at
`a03a6ff05b1faedfd13b66984933a76f59d1b338`.

| Check | Result |
|---|---|
| Task count | **19** tasks under `160-F` — unchanged; cycle 4 created, retired and re-parented **no** task |
| Shipment manifest | `168-S` carries **20** members (feature + 19 tasks); `unsized: 0`; size histogram `S=13, M=6` |
| Shipment sequencing | chain intact and **all queued, none claimed**: `159-S → 160-S → 161-S → 162-S → 163-S → 164-S → 165-S → 166-S → 168-S → 167-S` |
| `(Tn)` back-references | **19/19** present and unique, resolving T1–T16 (incl. T2a/T2b, T3a/T3b, T7/T7b) |
| Size enum | all `S` or `M` — **zero** at `L`/`XL`; no task exceeds the 2-hour effort axis |
| Complexity enum | `trivial=1, low=2, medium=14, high=2`; both `high` tasks remain de-risked by blocking spike edges |
| DAG acyclicity | **acyclic** — all **19/19** nodes topologically ordered after the new `T6 ← T1` edge |
| New edges encoded | `160.014-T ← 160.002-T` (finding 4) and `158.003-T ← 158.002-T` (finding 2) both present |
| Case-ledger bijection | plan **52** unique cases ↔ queue **52**; zero in one and not the other |
| Class totals | **35 RED-FIRST / 17 CHARACTERIZATION = 52**, recomputed from the table rows |
| Per-author split | T3a 25R/0C, T3b 0R/7C, T9 1R/2C, T10 1R/2C, T11 5R/3C, T12 1R/3C, T13 2R/0C. Columns reconcile: 25+0+1+1+5+1+2 = **35**; 0+7+2+2+3+3+0 = **17**; total **52**. T3a's red count is unchanged at 25 by **two offsetting moves** (finding 5 removed one, finding 9 added one), not by oversight |
| Author attribution | **52/52** author edges — every case present in its authoring record; **zero** misses |
| Owner attribution | **69/69** green/preservation owner edges — every case present in every named owner record; **zero** misses |
| RED-FIRST ordering | **39/39** author-before-owner prerequisite paths hold transitively; **zero** violations |
| Observation destinations | **7/7** authoring tasks authorize their `observations/*.json` write in the operative SAFETY MODE clause; T16 consumes all seven |
| Test-write authority | `tests/**` grants absent from both green-owner tasks (`160.018-T` three files; `160.014-T` `build_support/` only) |
| Stale case name | the pre-rename name appears **only** inside explicit "renamed from" annotations; zero live uses |
| Stale counts | zero occurrences of `51` cases / `16 CHARACTERIZATION` outside the marked supersession note |
| Bare `{{…}}` tokens | **zero** outside fenced blocks |
| Append seams | **zero** `=== REVIEW-FIX` / `=== ORIGINAL TASK` / `=== RE-SCOPE` markers in `.backlogit/queue/**` |
| Preserved decisions | wheel + sdist + plugin closed channels ✔; tracked publishable plugin fallback with self-excluded generator input ✔; `167-S` blocked by `168-S` ✔; P-021 captures intact ✔ |

**Gate after cycle 4: PASS. No in-scope P0 or P1 finding remains open, and the
tightly-coupled P2 inconsistencies are closed.** All fifteen findings were
confirmed legitimate and remediated; every derived number above was recalculated
mechanically after the last edit. This plan is harvest-complete and
execution-ready for Ship.
