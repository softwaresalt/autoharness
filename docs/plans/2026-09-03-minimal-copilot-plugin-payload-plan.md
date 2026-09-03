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
  15).** The test asserts **exactly one authored occurrence across executable and
  configuration surfaces** — `build_support/**`, `src/**`, `tests/**`,
  `pyproject.toml`, `.github/plugin/marketplace.json`, `.github/workflows/**`, and
  the manifest itself — with the manifest's `target_workspace_paths` key being
  that one occurrence. Documentation, plans, deliberations, and backlog records
  are **outside the test's surface**.

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
* `plugin-payload/**` is classified in AC11: **excluded** from the wheel and sdist
  channels (it is a derived duplicate of payload content, not source), and it is
  the plugin channel's payload root. The manifest excludes it from itself so
  generation cannot recurse.

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
| `pyproject.toml` | Wheel/sdist **build input**; include in the **sdist** payload (a source distribution without its build definition is not buildable); **exclude** from the wheel and plugin payloads | Not a runtime file, but it *is* the sdist's build definition |
| `.github/workflows/**` | Exclude | CI for this repo only |
| `.github/copilot/**` | Classify explicitly at implementation time | Unresolved at plan time |
| `.copilot/**`, `dist/**`, `.worktrees/**` | Exclude | Untracked/build output |
| `build_support/**` | **Exclude** | Build-time only; created by T5/T6. Shipping it would put the packaging rules inside the artifact they trim (P1-6) |
| `plugin-payload/**` | **Exclude** from wheel and sdist; **is** the plugin channel payload root | Tracked generated tree created only under spike branch (b) (AC3c). Excluded from itself so generation cannot recurse, and excluded from the Python channels because it is a derived duplicate of payload content, not source |
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
   (`T3a`, `T3b`, `T9`–`T13`) **blocks** every implementing task (`T7`, `T7b`,
   `T8`, `T14`). No implementation can start until the observation that gives it
   meaning has been recorded.
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

### Case table

`Authored by` is the task that writes the case and records the first observation.
`Green/preservation owner` is the task whose change must produce the second
observation.

| Test | Asserts | Class | Authored by | Green/preservation owner |
|---|---|---|---|---|
| `test_manifest_validates_against_schema` | AC1 | RED-FIRST | T3a | T4 |
| `test_schema_live_and_versioned_mirror_agree` | AC1 | RED-FIRST | T3a | T2b |
| `test_payload_manifest_contract_registered` | AC1 | RED-FIRST | T3a | T2b |
| `test_every_tracked_path_is_classified` | AC11 | RED-FIRST | T3a | T4 |
| `test_start_scripts_and_workspace_config_excluded` | AC11 | RED-FIRST | T3a | T4 |
| `test_manifest_is_sole_source_of_payload_paths` | AC1 | RED-FIRST | T3a | T5 |
| `test_unclassified_tracked_path_fails_build` | AC2, AC8 | RED-FIRST | T3a | T5 |
| `test_payload_size_reported` | AC8 | RED-FIRST | T3a | T5 |
| `test_generate_emits_expected_tables_to_a_scratch_target` | AC2c | RED-FIRST | T3a | T6 |
| `test_generate_is_byte_deterministic_and_cross_platform` | AC2c | RED-FIRST | T3a | T6 |
| `test_only_one_generation_path_exists` | AC2c | RED-FIRST | T3a | T6 |
| `test_wheel_generated_table_matches_manifest` | AC2c | RED-FIRST | T3a | T7 |
| `test_docs_root_guides_only` | AC4 | RED-FIRST | T3a | T7 |
| `test_wheel_excludes_backlogit_explicitly` | AC3 | **CHARACTERIZATION** | T3b | T7 |
| `test_wheel_excludes_dev_directories` | AC3 | **CHARACTERIZATION** | T3b | T7 |
| `test_wheel_contains_required_runtime_set` | AC4 | **CHARACTERIZATION** | T3b | T7 |
| `test_core_metadata_version_pins_preserved` | I4, V2 | **CHARACTERIZATION** | T3b | T7 / T7b |
| `test_sdist_generated_table_matches_manifest` | AC2c, AC3b | RED-FIRST | T3a | T7b |
| `test_sdist_excludes_backlogit_explicitly` | AC3b | RED-FIRST | T3a | T7b |
| `test_sdist_excludes_dev_directories` | AC3b | RED-FIRST | T3a | T7b |
| `test_sdist_byte_size_and_disclosure_reported` | AC3b, AC8 | RED-FIRST | T3a | T7b |
| `test_sdist_contains_required_runtime_set` | AC3b, AC4 | **CHARACTERIZATION** | T3b | T7b |
| `test_sdist_includes_build_definition` | AC3b, AC11 | **CHARACTERIZATION** | T3b | T7b |
| `test_plugin_generated_declaration_matches_manifest` | AC2c | RED-FIRST | T3a | T8 |
| `test_plugin_payload_excludes_dev_directories` | AC3 | RED-FIRST | T3a | T8 |
| `test_plugin_source_path_is_tracked_and_fetchable` | AC3c | RED-FIRST | T3a | T8 |
| `test_install_emits_only_generated_output` | AC5, I3 | **CHARACTERIZATION** | T9 | T7 / T7b / T8 |
| `test_skill_docs_refs_resolve_to_workspace_not_payload` | AC5, AC2d, R2 | RED-FIRST | T9 | T5 |
| `test_no_engine_records_in_target_workspace` | AC5 | RED-FIRST | T9 | T7 / T8 |
| `test_verify_workspace_parity_trimmed_vs_baseline` | AC6 | **CHARACTERIZATION** | T10 | T7 / T7b / T8 |
| `test_upgrade_from_1_5_0_leaves_no_orphans` | AC6, R3 | RED-FIRST | T10 | T7 / T7b / T8 |
| `test_data_dir_resolution_pip_install` | AC6a, R4 | **CHARACTERIZATION** | T11 | T7 / T7b |
| `test_data_dir_resolution_clone_editable` | AC6a, R4 | **CHARACTERIZATION** | T11 | T7 / T7b |
| `test_python_channel_needs_no_plugin_root_artifact` | AC6a (A1) | **CHARACTERIZATION** | T11 | T7 / T7b |
| `test_plugin_root_resolves_templates_and_schemas` | AC6b | RED-FIRST | T11 | T8 |
| `test_plugin_payload_has_no_python_distribution` | AC6b (B2) | RED-FIRST | T11 | T8 |
| `test_channel_resolver_contracts_are_disjoint` | AC6a, AC6b | RED-FIRST | T11 | T8 |
| `test_register_phase_all_environments_python_channel` | AC7 | **CHARACTERIZATION** | T12 | T7 / T7b |
| `test_plugin_only_register_copilot_cli_succeeds` | AC7 | **CHARACTERIZATION** | T12 | T8 |
| `test_plugin_only_unsupported_targets_fail_the_same_way_as_baseline` | AC7 | **CHARACTERIZATION** | T12 | T8 |
| `test_plugin_channel_excludes_python_cli_by_design` | AC7 | RED-FIRST | T12 | T8 |
| `test_gate4_crossrefs_intact_in_built_payload` | AC9, AC2d | RED-FIRST | T13 | T7 / T7b / T8 |
| `test_version_resolves_on_plugin_install_without_cli` | AC10 | RED-FIRST | T13 | T8 |
| `test_release_workflow_runs_payload_gate_before_publish` | AC2b | RED-FIRST | T3a | T14 |
| `test_release_gate_covers_all_three_channels` | AC2b, AC3b | RED-FIRST | T3a | T14 |

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
recorded durably. CHARACTERIZATION cases are observed green **against that
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
| `160.004-T` (T5) | `160.005-T`, `160.003-T` |
| `160.014-T` (T6) | `160.004-T` |
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
* `T9`–`T13` are blocked by `T2a`, `T3a`, and `T3b` and **block** `T7` and `T8`.
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
  `plugin-payload/` from the manifest and repoints `source` at it (AC3c); or
* **(c)** neither is acceptable → `T1` **halts to the operator** with the evidence
  and the alternatives.

Branch (b) may **not** point `source` at `dist/plugin/` or any other gitignored or
untracked path — `dist/.gitignore` is `*`, so a consumer checkout has no such
directory and the install simply fails (finding 5). `T8` must not begin until `T1`
resolves this.

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
* **`AB387F16`** — a **pre-persistence temporary working ID**, superseded by
  `E9E5E6CC` before any stash record was written. It has **no** durable stash
  entry and must not be given one; fabricating a record to satisfy a lookup would
  manufacture false provenance. It survives only as the superseded-ID note on
  `160-F`, which is the correct and complete disposition.
* Feature: `160-F` (records the source-stash linkage and the superseded temporary ID)
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
| `tests/**` | T3a, T3b, T9–T13, T16 | Test authoring and execution only |
| `pyproject.toml` | T7 (wheel target), T7b (sdist target) | Build tables only; serialized by edge to avoid same-file collision |
| `.github/plugin/marketplace.json` | T8 | Payload/`source` declaration only |
| `plugin-payload/**` | T8 | Tracked generated payload tree; branch (b) only (AC3c) |
| `.github/workflows/release.yml` | T14 | The one added gate step only |
| `docs/installation.md`, `README.md`, `CHANGELOG.md` | T15 | The three documents named in T15 |

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
| **Rollback** | T7, T7b, T8, T14 | Before the task lands, record the exact pre-change bytes of the file it mutates (`pyproject.toml`, `marketplace.json`, `release.yml`) into a durable **evidence artifact**. That record is evidence, never authorization. Recovery is a **forward revert commit** (Rollback R-1). **A destructive restore or overwrite requires fresh live operator approval over a channel the agent cannot synthesize (R-3); with no channel available the agent halts and does not restore (R-4).** *Corrected in cycle 2, finding 11 — cycle 1 prescribed "a single-file restore" as the standard path, pre-authorizing a destructive overwrite that Constitution Principle VII requires an operator to approve.* |
| **Destructive-operation** | T8 (branch (b)), all verification tasks | Generation into the tracked `plugin-payload/` tree writes **only** files the manifest resolves, **must never** delete, move, or overwrite a tracked file outside that tree, and **must never** remove a tracked file without R-3 approval. Asserted by running generation against a dirty working tree and verifying the tracked file set outside `plugin-payload/` is unchanged. Scratch workspaces and simulated environments live under gitignored temporary paths and must not mutate the developer's real workspace, `~/.autoharness/`, installed interpreter, VS Code settings, Claude/Codex config, or Copilot CLI plugin registry. |
| **Published-artifact immutability** | T2a, T10 | v1.5.0 artifacts used as baselines are already published and must never be mutated or retracted (invariant I5). |
| **Red-preservation** | T3a | T3a authors test files under `tests/` only. It must not author or modify the manifest, either schema file, `schema_contracts.py`, `build_support/`, `pyproject.toml`, `marketplace.json`, `plugin-payload/`, or `release.yml` — doing so would make its own cases green and destroy the red observation. |
| **Baseline-fidelity** | T3b, T9–T13 | CHARACTERIZATION cases are observed green **against the baseline (untrimmed) build** from T2a, never against a partially-changed tree. Authoring a CHARACTERIZATION case that is red on the baseline is a defect of the authoring task, not a finding about the baseline. |

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

**T-number reconciliation notice (review-fix cycle 2, finding 14).** The cycle-1
table above and the cycle-1 findings text use the **cycle-1** `T#` labels, which
cycle 2 superseded. Cycle 1's `T2` is now `T2a` + `T2b`; its `T3` is now `T3a` +
`T3b`; `T7b` and `T16` are new. Where the cycle-1 record above says `T2`, `T3`,
`T5`, `T6`, or `T7`, read it against the **cycle-1** decomposition, which is
preserved here as a historical record and is **not** the current contract. The
authoritative mapping in both directions is the **§Task decomposition** table and
the **§Prerequisite DAG**; every queued task record's `(Tn)` back-reference was
re-verified against those two tables in cycle 2.

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
| **5 — Plugin fallback branch (b) unpublishable** | **Legitimate P0** | Confirmed: `dist/.gitignore` contains `*`, so `source: "dist/plugin"` points at a path absent from any consumer checkout — an install failure, not a trim. Added **AC3c**: `source` must resolve to a consumer-fetchable path; branch (b) generates a **tracked, committed** `plugin-payload/` tree via the same generate-and-assert shape H1 already uses for the wheel table; pointing `source` at any gitignored/untracked path is prohibited, as is assuming unevidenced marketplace filtering behavior; and a branch **(c)** is added so `T1` halts to the operator rather than inventing a mechanism. `plugin-payload/**` is classified in AC11 and excluded from itself so generation cannot recurse. |
| **11 — Destructive rollback self-authorized** | **Legitimate P1** | Confirmed: the H2 rollback checkpoint prescribed "a single-file restore" as the standard recovery path, pre-authorizing a destructive working-tree overwrite that Constitution Principle VII requires an operator to approve — at the moment (a failed release) when the tree most likely holds unrelated uncommitted work. Added **Rollback R-1…R-5**, adopting SHIP-4 Decision G's authorization contract verbatim so the harness carries one answer, not two: forward revert commits are the default; recorded pre-change bytes are **evidence, never authority**; any destructive restore needs a **fresh live non-synthesizable operator approval**; no channel means **halt, do not restore**; and read-only alternatives (`git show`, `git diff`, scratch materialization) cover the verify-don't-restore case. Added operator checkpoint **CP3**. |
| **13 — Source traceability unauditable** | **Partially legitimate; one half a false positive** | `E9E5E6CC` **is** durable at HEAD in the official archive record `.backlogit/archive/stash.jsonl` (tracked, blob `aef5f126`), carrying its own forward reference to `160-F`/`168-S`. The reviewer's search missed it because consumed entries are **archived**, not retained in the active stash — recorded as a false positive with evidence. The legitimate half: the archived entry's `HARVESTED` annotation still read `160.001-T..160.011-T`, stale against the 19-task set; it is reconciled through the official stash-edit operation. `AB387F16` is a **pre-persistence temporary working ID** superseded before any record was written; it has no durable entry and is **not** given one, because fabricating a record to satisfy a lookup manufactures false provenance. Its correct and complete disposition is the superseded-ID note on `160-F`. §Traceability now states all of this explicitly. |
| **14 — Stale ownership and numbering references** | **Legitimate P1** | Confirmed: `160.002-T` pointed generation at `160.004-T` (it is `160.014-T`) and the release gate at `160.006-T` (it is `160.015-T`); `160.007-T` repeated both errors. Corrected through official `backlogit update` operations, and every `(Tn)` back-reference re-verified against the rewritten decomposition table and DAG. The cycle-1 review record above is explicitly marked as historical with a mapping notice rather than silently rewritten, so the audit trail survives. |
| **15 — Centralization contract unsatisfiable** | **Legitimate P1** | Confirmed: AC2d demanded "exactly one authored occurrence of the prefix list **in the repository**", but the plan, the deliberation, and the task record each necessarily enumerate the prefixes to specify the rule — so the contract failed the moment it was written. The test's surface is narrowed to **executable and configuration surfaces** (`build_support/**`, `src/**`, `tests/**`, `pyproject.toml`, `marketplace.json`, `.github/workflows/**`, and the manifest), with the manifest's `target_workspace_paths` key as the one occurrence; documentation and backlog records are outside it. Prose now refers to the key symbolically wherever the values are not themselves the subject. The drift guarantee is preserved — one executable source of truth — without making explanation illegal. |
| **16 — `160.001-T` under-scoped and under-sized** | **Legitimate P1** | Confirmed: one `S`/`low` task combined baseline capture across three channels, two schema documents, runtime contract registration, and an immutability assertion — four deliverables with different reversibility. Split into `T2a` (`160.001-T`, baseline characterization capture, `S`/`low`) and `T2b` (`160.018-T`, schema publication + registration + pair-divergence assertion, `S`/`medium`). IDs, shipment membership, the decomposition table, the DAG, and this review are all updated to match. |
| **17 — Keep it simple and composable** | **Accepted as a constraint** | Honoured by construction. The remediation adds **one concept** (a two-valued case class) and **four tasks**, and otherwise reuses shapes the plan already had: the sdist reuses the wheel's generate-and-assert mechanism; branch (b) reuses the same mechanism for a tracked tree; the rollback contract reuses SHIP-4 Decision G rather than inventing an approval model; the centralization fix *narrows* a test rather than adding indirection. No build hook, no runtime framework, no new CLI, no speculative abstraction was introduced. |
| **6 — SHIP-2 C6 must fail closed** | **Legitimate P0 — remediated in SHIP-2** | Confirmed. The probe requests the *exact-version* endpoint `https://pypi.org/pypi/autoharness/{version}/json`, which names the version in the path, so a conforming PyPI can return only `404` or a `200` naming *that* version. A `200` naming a different version is a response the protocol does not permit — positive evidence of a cache, mirror, or interception anomaly, not evidence of absence. Cycle 1's "probe proceeds" discarded a *detected* anomaly, which is worse than the original fail-open `else:` branch. Fixed in `docs/plans/2026-08-31-ship2-release-ci-fail-closed-gates-plan.md` (new binding **H2b**, C6 row reversed) and in `152.002-T`, with a hermetic expectation asserting the helper **raises** and neither proceeds nor exits with C2's already-published code. **Discriminating power preserved**: C2 and C6 still differ *in kind*, so a "did the request succeed" probe still passes C2 and fails C6. |
| **7 — SHIP-6 tool-name prohibition too broad** | **Legitimate P1 — remediated in SHIP-6** | Confirmed and narrow. The H6a-CLARIFICATION body was already correct; the defect was the trailing **ACCEPTANCE** line, "no hardcoded tool-name literal anywhere in renderer, template, or test fixtures", which contradicted **H1** (concrete tool-scoped block declarations are *required*) and the H6a synthetic-registry test (which needs a fixture carrying a concrete synthetic `tool_name`). The task's acceptance therefore forbade the artifacts its own binding requirements mandate and was unsatisfiable. `156.002-T` now prohibits exactly the **duplicated validation set** — zero authored occurrences of a hardcoded *list/set/enum/default* of valid names — and explicitly permits declarative identities, fixture values, and prose. The discriminator is the synthetic-registry test, not a grep. |
| **8 — SHIP-7 enumerated fields miss future keys** | **Legitimate P1 — remediated in SHIP-7** | Confirmed. An enumerated surface table is a denylist wearing an allowlist's clothes: it omitted top-level `schema_version` (declared `1.0.0` in this workspace) and would omit every future template-owned key. Replaced with **H3a-RECURSIVE** in the SHIP-7 plan and in `157.002-T`: recursive value parity over **every leaf path in the parsed template document**, minus the closed, path-specific **H3b** override allow-list. Template-present/installed-absent is a failure; installed-only paths are INFO. Also resolved a cycle-1 self-contradiction — `directory` was listed *both* as value-equality and as override-eligible; it is **override-eligible** (this workspace uses the legacy `.backlogit` root). |
| **9 — SHIP-8 undefined budget language** | **Legitimate P1 — remediated in SHIP-8** | Confirmed. The SHIP-8 plan had already withdrawn the aggregate budget in favour of the unsized-only predicate (`size_composition.unsized == 0`), but `158.003-T` still required failing "when the composition exceeds the declared budget" — a threshold that is declared nowhere, so an implementer would have had to *invent* a number and gate shipments on it. Removed, and all five plan-declared boundary cases **B1–B5** are now required by name, including the two fail-closed ones cycle 1 omitted: **B3** (empty histogram → pass) and **B4** (absent `unsized` → **fail closed**; a missing key is not zero). B3/B4 are the two directions a naive `if unsized:` truthiness check gets wrong. |
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
consistent in both directions; 45 test cases each carrying a declared class, an
author, and a real implementing green/preservation owner; all three publication
channels (wheel, sdist, plugin) covered by manifest overlay, generation, wiring,
and release gate; safety-mode allowlist coherent with acceptance criteria; and no
destructive operation self-authorized.**

Two review-fix cycles used of the three available; one remains.
