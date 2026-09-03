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
| `schemas/payload-manifest.schema.json` *(new)* | Schema for the manifest |
| `pyproject.toml` | Replace ad-hoc `force-include` with manifest-derived includes |
| `.github/plugin/marketplace.json` | Constrain plugin payload to the manifest |
| `build_support/payload.py` *(new, not shipped)* | Manifest loader + resolver |
| `tests/test_payload_manifest.py` *(new)* | Fail-closed composition test |
| `tests/test_install_e2e.py` *(new)* | Install/upgrade/verify from built artifact |
| `docs/installation.md`, `README.md` | Document payload boundary |
| `CHANGELOG.md` | Record the packaging change |

**Schema note:** `payload-manifest.schema.json` is a **new** schema at
`1.0.0`. No existing schema is mutated in place — this repository has a recorded
three-occurrence history of in-place schema mutation without a version bump
(`docs/compound/2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md`).

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
  artifact, with no new findings versus the untrimmed baseline.
* **Upgrade path:** a workspace installed from v1.5.0 (untrimmed) upgraded to the
  trimmed build passes `verify-workspace` and is left with no orphaned engine
  files. Tested explicitly (R3).
* `_DATA_DIR` resolution (`cli.py:14-21`), including the clone/editable fallback
  to repo root, resolves `templates/` and `schemas/` in all three install methods
  (pip, clone, plugin) (R4).

### AC7 — Cross-environment behavior preserved

`deploy-harness.ps1` / `deploy-harness.sh` `register` phase succeeds for
`vscode`, `copilot-cli`, `claude`, and `codex` against the trimmed payload.

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

`start.ps1` / `start.sh` are called out specifically: they read like engine files
but are generated harness artifacts for *this* workspace, and shipping them would
violate the very "generated output, not engine files" boundary in AC5.

## Test strategy

Tests must run against the **built artifact**, never the source tree — a source-tree
test cannot detect a packaging defect (R1).

| Test | Asserts |
|---|---|
| `test_manifest_validates_against_schema` | AC1 |
| `test_manifest_is_sole_source_of_payload_paths` | AC1 |
| `test_unclassified_tracked_path_fails_build` | AC2, AC8 |
| `test_every_tracked_path_is_classified` | AC11 |
| `test_wheel_excludes_backlogit_explicitly` | AC3 |
| `test_wheel_excludes_dev_directories` | AC3 |
| `test_plugin_payload_excludes_dev_directories` | AC3 |
| `test_start_scripts_and_workspace_config_excluded` | AC11 |
| `test_wheel_contains_required_runtime_set` | AC4 |
| `test_docs_root_guides_only` | AC4 |
| `test_install_emits_only_generated_output` | AC5 |
| `test_skill_docs_refs_resolve_to_workspace_not_payload` | AC5, R2 |
| `test_verify_workspace_parity_trimmed_vs_baseline` | AC6 |
| `test_upgrade_from_1_5_0_leaves_no_orphans` | AC6, R3 |
| `test_data_dir_resolution_all_install_methods` | AC6, R4 |
| `test_core_metadata_version_pins_preserved` | I4, V2 |
| `test_register_phase_all_environments` | AC7 |
| `test_payload_size_reported` | AC8 |
| `test_gate4_crossrefs_intact_in_built_payload` | AC9 |
| `test_version_resolves_on_plugin_install_without_cli` | AC10 |

Baseline capture (pre-change wheel inventory + `verify-workspace` output) is a
prerequisite of the parity tests and is produced by the first task.

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

Ordering satisfies Constitution Principle II (Test-First, NON-NEGOTIABLE): the
composition guard (T5) lands **before** the channel wiring it governs (T6, T7).

| Task | Scope | Size | Complexity |
|---|---|---|---|
| T1 | **Spike:** establish the plugin-channel trimming mechanism | S | high |
| T2 | Baseline capture + payload manifest schema (new, 1.0.0) | S | low |
| T3 | Author `.autoharness/payload-manifest.yaml` allowlist (full AC11 classification) | M | medium |
| T4 | Manifest loader/resolver in `build_support/` (not shipped) | M | medium |
| T5 | Fail-closed composition + exclusion tests (**before** wiring) | M | medium |
| T6 | Wire wheel packaging to manifest (`pyproject.toml`), preserving I4 pins | M | medium |
| T7 | Wire plugin channel per the T1 mechanism | M | high |
| T8 | Install/upgrade/verify e2e + cross-environment tests | M | high |
| T9 | Gate 4 cross-reference + `{{AUTOHARNESS_VERSION}}` resolution tests | S | medium |
| T10 | Docs + CHANGELOG | S | trivial |

**T1 is a blocking spike (review finding P0-1).** The plan assumes the plugin
payload can be constrained, but the only observed mechanism is
`marketplace.json`'s `source: "."`, and no evidence establishes that Copilot CLI
supports an allowlist or ignore file for plugin sources. T1 must determine which
holds:

* **(a)** the marketplace source supports an exclusion/allowlist mechanism → wire
  it directly in T7; or
* **(b)** it does not → T7 instead builds a payload directory (e.g.
  `dist/plugin/`) from the manifest and repoints `source` at it, which changes
  T7's shape and adds a build step.

T7 must not begin until T1 resolves this. Proceeding on assumption (a) without
evidence risks discovering mid-implementation that the plugin half of the plan is
infeasible as written.

Width isolation: T6 (Python packaging) and T7 (plugin channel) are separate tasks;
T5 (composition), T8 (e2e), and T9 (integrity/version) are separated by test kind.

## Traceability

* Source stash: `E9E5E6CC`
* Deliberation: `docs/decisions/2026-09-03-minimal-copilot-plugin-payload-deliberation.md`
* Hardening: `## Plan Hardening` section below (appended in place per skill contract)
* Review: `## Plan Review` section below (appended in place per skill contract)

## Plan Hardening

### Hardening signals present

| Signal | Present | Detail |
|---|---|---|
| Public API / schema / contract change | **Yes** | New `payload-manifest.schema.json`; packaging contract for both channels |
| Migration / irreversible step | **Yes (bounded)** | Consumer upgrade v1.5.0 → trimmed payload |
| External integration | **Yes** | PyPI publish pipeline; Copilot plugin marketplace |
| High blast radius | **Yes** | CLI distribution — a defect reaches every consumer install |
| Security / sensitive data | **Yes** | `.backlogit/` disclosure removal |

Hardening is required. The dominant risk is that **packaging defects do not fail
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
`T4` is scoped to option (b); a build hook is explicitly out of scope.

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

* **CP1** — Before `T4`/`T5` wiring lands: operator reviews the resolved allowlist
  and confirms no required path is missing.
* **CP2** — Before publication (Ship/Orchestrator scope, outside this plan):
  release-pipeline dry run confirming metadata pins intact.

### Risky actions

| Action | Risk | Mitigation | Rollback state |
|---|---|---|---|
| Rewrite `pyproject.toml` build tables | **High** — breaks publish | Preserve I4 pins; assert by test; V2 | Revert file; payload returns to untrimmed |
| Constrain `marketplace.json` payload | **Medium** — breaks plugin install | V1 + CP1 | Revert to `source: "."` |
| Exclude `docs/` history | **Low** — false-positive refs | AC5 test; allow-list learning | Re-add to manifest include |
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
backlog follow-up on `T4`; not harvest-blocking.

**P2-8 — Forward-only disclosure remediation.** *(Security Lens Reviewer)* Removing
`.backlogit/` does not un-publish it: v1.5.0 artifacts already distributed contain
those 2,110 files and remain public (invariant I5 correctly forbids retraction).
The plan should not imply retroactive remediation. A content sensitivity
assessment of what was already published is recorded as a follow-up. Not
harvest-blocking — the records are development backlog metadata, not credentials.

**P2-9 — Compound learning not scheduled.** *(Learnings Researcher)* Capture a
`docs/compound/` learning on completion (allowlist-over-denylist packaging;
"referenced ≠ required payload"). Follow-up.

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
