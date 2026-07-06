# Changelog

## 1.4.7 - 2026-07-06

### Added

- Added deterministic validation gates for the autoharness CLI, including the
  `lifecycle_hooks` configuration schema, gate diff discovery, glob matching,
  injection-safe subprocess execution, `autoharness gate check`, correction
  reports, force-audit behavior, and gate policy tests.
- Added install-manifest autoharness version recording and placeholder
  verification so installed workspaces can compare against the current
  autoharness version.
- Added telemetry capture foundations with execution epochs, JSONL/SQLite sinks,
  capture CLI support, and documentation for the telemetry contract.
- Added evaluation-runner foundations, including model-matrix loading,
  frozen-state execution, deterministic reviewer-matrix diff grading,
  comparative baseline summaries, and `eval run` CLI wiring.
- Added shipment-closure safety hardening: P-015 single-artifact safe-close
  policy, shipment reconciliation updates, and Ship closure guidance to avoid
  backlogit shipment cascade side effects.
- Added manifest placeholder scan coverage for scalar fields such as
  `.autoharness/harness-manifest.yaml` `autoharness_version`.
- Added P-016 single-implementation-branch/worktree policy coverage across the
  foundation, Orchestrator, Stage, Ship, entrypoint prompts, verification, and
  closure surfaces.
- Added P-017 dark factory mode semantics, including explicit trigger phrases,
  bounded scope, local-review-first merge readiness, admin fallback rules,
  operator-visible telemetry, `/feature-flow-dark`, and verification coverage.
- Added output timestamp instructions and intercom progress timestamp weaving for
  long-running agent phases.
- Added `autoharness gate check --json` `repeated_failure` metadata and
  `--no-count` advisory/manual gate-check mode for backlogit gate-broker
  integration.

### Changed

- Kept workspace MCP and local environment configuration out of tracked release
  artifacts, and updated startup behavior to preserve local environment values.
- Made the sequential single-PR-at-a-time workflow the explicit default.
- Removed deprecated per-agent `model_routing` frontmatter in favor of
  `model_tier` / `max_subagent_tier`, while preserving config-level
  `model_routing` tier bindings.
- Required a successful full local build before code-changing PRs are submitted
  or updated, and documented the non-applicability path for docs/backlog-only
  PRs.
- Documented the CI build-action scope decision for reducing unnecessary build
  runs on non-code changes.
- Recorded the reference-adoption evaluation spike and its follow-on guidance
  for future template curation work.

### Fixed

- Fixed eval CLI help-token handling so only a leading help token triggers usage
  output.
- Fixed unified-diff parsing for added lines whose content begins with `+++ `.
- Fixed dark-factory verification so policy-only installs do not trigger
  dark-mode checks unless the dark prompt artifact is installed.
- Normalized invalid `repeated_failure.action` values to `block` and made
  `--force` mutually exclusive with `--no-count` to avoid ambiguous gate
  counter behavior.

## 1.4.6 - 2026-06-24

### Changed

- Renamed the source-controlled workflow agents and their templates for sort
  priority and explicit identity: `orchestrator.agent.md` →
  `_orchestrator.agent.md` (`_Orchestrator`), `stage.agent.md` →
  `.stage.agent.md` (`.Stage`), and `ship.agent.md` → `.ship.agent.md`
  (`.Ship`). Updated the dogfood harness manifest, workspace profile, install
  guidance, verification logic, tests, and documentation to match the new
  filenames and frontmatter identities (PR #112).
- Added developer-friendly Orchestrator workflow entrypoints:
  `/feature-flow` for the standard sequential Stage → Ship lifecycle and
  `/feature-flow-parallel` for the pipelined preference path. The prompts,
  installer wiring, user-facing docs, and regression tests now treat them as
  aliases over the existing Orchestrator workflow rather than a separate
  pipeline (PR #113).
- Standardized on a tracked workspace-root `.mcp.json` as the canonical shared
  MCP configuration surface across agent IDEs. Removed tracked editor-specific
  `.vscode/mcp.json` and `.cursor/mcp.json`, made the shared config portable,
  and updated discovery/install/tuning guidance so editor-local MCP files are
  treated only as legacy compatibility fallbacks (PR #113).

## 1.4.5 - 2026-05-18

### Changed

- Clarified the stable Python CLI install path across README, getting-started
  docs, and CLI guidance so users switch from Git-URL or `uv tool` installs to
  the PyPI wheel with an explicit uninstall-then-reinstall migration step.
- Synchronized the packaged plugin manifests with the 1.4.5 Python distribution
  version so release metadata stays aligned across `pyproject.toml`,
  `plugin.json`, and `.github/plugin/marketplace.json`.

## 1.4.4 - 2026-05-17

### Changed

- Hardened the Copilot Review Merge Gate (P-014) across the full Ship pipeline:
  added defense-in-depth pre-merge verification (§1.9) to `ship.agent.md`,
  `pr-lifecycle/SKILL.md.tmpl`, and `workflow-policies.md.tmpl`. Every PR —
  including post-merge closure PRs — must pass the paginated GraphQL thread-
  resolution check against the current HEAD before merge is presented or
  executed (PR #90, shipment 036-S follow-up).
- Installed `github-pr-automation.instructions.md` with §1.9 pre-merge
  readiness gate and §1.10 post-merge closure PR Copilot surveillance protocol.
  Ship agents now enforce Copilot review freshness and zero-unresolved-thread
  requirements as a non-negotiable pre-merge step (PR #90).

### Fixed

- Corrected `035-S` archive frontmatter: status set to `shipped`, commit SHA
  aligned to the actual merge SHA (`38a6c77`). Reconciled post-merge closure
  artifacts from PR #89 follow-up (PR #91, shipment 036-S).
- Archived 036-S shipment artifacts and session memory; corrected
  `archived_from` queue paths in frontmatter (chore/036-S-post-merge-closure).

## 1.4.3 - 2026-05-17

### Added

- Added full capability-pack overlay weave for all three capability packs:
  `agent-engram`, `agent-intercom`, and `graphtor-docs`. Each pack is now
  woven coherently across Stage and Ship agent templates, the install-harness
  SKILL, and copilot-instructions. A partially-woven or isolated instruction
  file is no longer a valid overlay — all packs must touch every declared
  overlay target (PR #86, shipment 034-S).

### Changed

- Strengthened P-001 (single top-level release-unit completion): Ship execution
  is now blocked until the full post-merge release closure for the current
  shipment is complete. This closes the policy gap where a Ship session could
  begin before the previous release cycle was fully recorded and tagged
  (PR #86 commit 943c079).

- Fixed `binary_on_path` → `binary_path` field-name drift in
  `schemas/workspace-profile.schema.json`, `docs/capability-packs.md`, and
  `.autoharness/workspace-profile.yaml` to match the canonical field name
  established in the workspace-discovery SKILL and emitted by actual
  workspace-profile output (039.007-T, stash 8FDEC777).

## 1.4.2 - 2026-05-17

### Added

- Added a PyPI-backed release pipeline: on every `v*` tag push, the release
  workflow builds a wheel and sdist, validates with twine, publishes to PyPI
  via OIDC Trusted Publisher, smoke-tests the published package, and creates
  or updates the GitHub Release. `uv tool install autoharness` and
  `uv tool upgrade autoharness` now resolve from PyPI rather than requiring a
  Git URL clone. The Git URL remains valid as an explicit snapshot or developer
  install path.

### Changed

- Packaged the already-merged PR #80 template and startup-script changes into the v1.4.2 release for downstream merge-install propagation.
- Preserved the intentional `start.ps1` / `templates/scripts/start.ps1.tmpl` launch flow, including Engram/backlogit startup, non-fatal GitHub token lookup, and `--remote` Copilot launch behavior.
- Added a defense-in-depth pre-merge Copilot review readiness gate across the GitHub PR automation instructions, Ship template, and PR lifecycle skill.

## 1.4.0 - 2026-05-11

### Added

- Added context-efficiency instruction template teaching agents tool result offloading, committed change eviction, and proactive compaction triggers (Primitive 1).
- Added role enforcement system for the two-agent Stage/Ship workflow: fail-closed pre-mutation self-check, Role Boundary tables in both agent templates, conditional weaving based on two-agent model detection, and verify_workspace assertions for role consistency.
- Added orchestrator elective agent routing: Auto-MergeInstall and Auto-Tune are now invocable as optional subagents from the Orchestrator with concurrency constraints and intercom events.
- Added compact-context intercom broadcasts for agent-intercom capability pack (Phase 1 start, Phase 2 candidates, Phase 4 completion).

### Changed

- Synchronized backlogit capability pack with full MCP surface (53/53 tools): added 23 missing operation mappings across stash management, semantic links, lifecycle, discovery/metadata, telemetry, deliberation, and maintenance categories.
- Synchronized agent-engram capability pack with full MCP surface (20/20 tools): added 8 missing tools including query_graph_neighborhood, observability/diagnostics tools, and documented resilience features.
- Updated install-harness to register context-efficiency instruction universally and role-enforcement instruction conditionally.

## 1.3.4 - 2026-04-27

### Added

- Added GitHub Copilot CLI plugin and self-hosted marketplace manifests so Copilot CLI users can install autoharness through a registered marketplace and browse it from Copilot CLI.
- Added deterministic regression coverage that keeps `pyproject.toml`, `src/autoharness/__init__.py`, `plugin.json`, and `.github/plugin/marketplace.json` version fields in sync across release bumps.

### Changed

- Updated CLI help text to recommend the Copilot CLI plugin install path, deprecate `setup-copilot-cli`, and describe the CLI as both an agent path resolver and a user-facing setup and verification surface.
- Corrected marketplace metadata versioning so the published marketplace manifest matches the `1.3.4` package/plugin release.

### Documentation

- Updated README and environment setup guidance to document the recommended Copilot CLI plugin install flow and the optional marketplace registration flow.

## 1.3.2 - 2026-04-26

### Changed

- Added branch management guardrails to Ship agent template: Branch Retention (NON-NEGOTIABLE) directive in Step 5 prevents premature checkout of the default branch while a feature PR is pending; Post-Merge Branch Protocol (NON-NEGOTIABLE) in Step 6 requires all closure work on a dedicated `post-merge/{feature_slug}` branch with its own PR; Branch Management Rules section consolidates the constraints.
- Added branch retention and post-merge branch protocol to pr-lifecycle skill template: Step 5 now includes a NON-NEGOTIABLE branch retention directive; Step 6 explicitly prohibits working on the default branch after merge.
- Added `ship_branch_management` and `pr_lifecycle_branch_retention` foundation assertions to `verify-workspace` so installed harnesses are validated for the new branch management markers.

## 1.3.1 - 2026-04-26

### Changed

- Enforced deterministic step-sequence execution in the Stage agent template with a NON-NEGOTIABLE step sequence contract, forward pointers after harvest, mandatory shipment assembly language, and a pre-summary verification gate that halts if `shipment_id` is missing.
- Hardened Ship agent fallback path to recommend running Stage first when no shipment exists, rather than silently proceeding with direct assembly.
- Added `stage_shipment_determinism` foundation assertion to `verify-workspace` so installed harnesses are validated for the new determinism markers.
- Added three behavioral constraints to Stage prohibiting: skipping shipment assembly, handing off feature ID instead of shipment ID, and presenting summary before all steps complete.

## 1.3.0 - 2026-04-25

### Added

- Recognized legacy `0.9.0` schema contracts for harness config, workspace profile, and harness manifest, with explicit migration proposals instead of treating them as unknown contract failures.
- Added backlogit SQL schema and YAML frontmatter/tooling instruction templates so backlog-aware harnesses can use `backlogit_query_sql` and field-level tooling guidance deterministically.
- Added deterministic regression coverage for backlogit overlay docs, intercom review workflow ordering, foundation copilot guidance, and install/tune branch-safety guidance.

### Changed

- Expanded `verify-workspace` targeted checks and warning reporting so repeated compatibility drift is grouped into clearer summaries while preserving the underlying finding count.
- Updated install and tune workflow guidance to keep generated output on feature branches or as local uncommitted changes pending pull-request review, rather than recommending direct default-branch commit or push.
- Replaced heuristic backlogit stale-artifact cleanup with explicit source-artifact cleanup driven by stable backlogit metadata when the `backlogit` capability pack is enabled.

### Documentation

- Updated README, Getting Started, Tuning Guide, Capability Packs, and backlogit integration docs to match the current install/tune behavior, schema-contract handling, and backlogit overlay surface.
