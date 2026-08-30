# Changelog

## 1.5.0 - 2026-08-30

### Added

- Added an opt-in, disabled-by-default Copilot CLI output-compression experiment, with benchmark/evidence plumbing and a follow-up hardening pass for fail-safe passthrough and honest benchmark reporting. (088-F / 093-S; 089-F / 094-S)
- Added multi-model review-routing improvements, including anchor-review route defaults, plurality-confidence handling, and normalized reviewer persona install paths under `.github/agents/subagents/`. (091-F / 096-S)
- Added deterministic telemetry event journaling/execution epochs, plus backlogit telemetry evidence mapping onto the shared `ToolTelemetryEvent` / `ExecutionEpoch` contract with a distinct task-level `complexity` dimension. (084-F / 107-S; 108-F / 113-S)
- Added a structural-navigation benchmark suite with scenario corpus loading, isolated telemetry capture, correctness scoring, A/B delta reporting, and reproducibility controls. (085-F / 111-S)
- Added first-class task `size` and `complexity` planning metadata, with fail-closed validation and granularity-gate enforcement across Stage/harvest flows. (107-F / 112-S)
- Added `autoharness gate pipeline-topology` in staged A/B/C rollout form, covering local lifecycle checks, hook/install integration, and remote CI backstop use, plus read-only DAG readiness / critical-path reporting. (109-F / 114-S; 109-F / 115-S; 109-F / 116-S; 110-F / 117-S)
- Added read-only shipment-record status diagnostics, operator-confirmed crash-resumption / prune-on-restore rules, and a deterministic `next_eligible` resumption advisory. (112-F / 118-S; 111-F / 119-S; 115-F / 123-S)
- Added a canonical CheckpointV1 payload contract for backlog checkpoints, including `schema_version: 1`, official write paths, required top-level resume metadata, and `context`-nested domain payloads. (130-F / 139-S)
- Added installation/restore of the policy registry plus the review-persona layer into generated workspaces, backed by end-to-end verification. (148-F / 156-S)
- Added a report-only pre-review detector SDK: detector registry/schema, applicability engine, DAG assembly, append-only reporting, `autoharness gate pre-review`, and the first ART-01 detector. (149-F / 157-S)

### Changed

- The backlog storage-root contract is now `.backlog`-first (`BACKLOGIT_WORKSPACE_DIR` -> `.backlog` -> `.backlogit`) for new/default lookup, while existing `.backlogit` workspaces remain fully supported and are **not** expected to self-migrate. (126-F / 135-S; 129-F / 138-S)
- **F02FD596**: Added a nested per-role escalation hierarchy for P-013.6
  telemetry-driven auto-escalation. `model_routing.stage.escalation` and
  `model_routing.ship.escalation` now take precedence over the legacy flat
  `model_routing.escalation` (retained, DEPRECATED, for backward
  compatibility), which in turn falls back per-field to `model_routing.tier3`.
  Declaring both a non-empty legacy flat `escalation` and any nested
  `<role>.escalation` is AMBIGUOUS and fails closed at both the schema level
  (`harness-config.schema.json` / `harness-config/1.1.0.schema.json`) and the
  `verify_workspace` loader/verification layer (H2). The `ESCALATION_DEGRADED`
  same-route guard is now role-scoped: it compares the acting role's own
  resolved escalation tuple only against that same role's own resolved role
  route, never a different role's route (H3). A nested override missing some
  sub-fields falls back per-field to `tier3` only, never to the legacy flat
  route (H4). Updated `escalation-protocol.instructions.md` (template and
  installed mirror), `workflow-policies.md.tmpl` (P-013.6, changelog `1.18.0`),
  `_stage.agent.md.tmpl` / `_ship.agent.md.tmpl`, and
  `install-harness/SKILL.md`'s variable-resolution table accordingly.
- **F02FD596 schema-versioning fix (PR #316 Copilot review)**: The nested
  `stage.escalation`/`ship.escalation` properties and the model_routing-level
  ambiguity `not` constraint were initially added in place to the published
  `harness-config/1.0.0.schema.json` mirror, which made the "1.0.0" version
  identifier ambiguous (an old 1.0.0 validator would reject a document using
  the new nested override; the patched-in-place 1.0.0 validator would accept
  it) — forbidden by the versioned-contract discipline in
  `src/autoharness/schema_contracts.py`. Fixed by restoring
  `harness-config/1.0.0.schema.json` to its exact pre-F02FD596 bytes and
  publishing the nested-escalation additions under a new
  `harness-config/1.1.0.schema.json` mirror instead (mirroring the
  tool-telemetry-event v1.0->v1.1 precedent). `schema_contracts.py`'s
  `current_version`/`known_versions` for the `config` contract now track
  `1.1.0`; the root `schemas/harness-config.schema.json` and
  `templates/harness-config.yaml.tmpl`'s default `schema_version` both bumped
  to `1.1.0`; this repository's own dogfood `.autoharness/config.yaml` bumped
  its `schema_version` to `1.1.0` accordingly (no escalation data values
  changed). A config declaring `schema_version: 1.0.0` continues to validate
  unmodified against the untouched, restored 1.0.0 contract; adopting nested
  per-role escalation requires declaring `schema_version: 1.1.0`.
- Renamed this repository's own dogfood Stage/tier3 model-routing assignment
  from `claude-opus-4.8` to `claude-opus-5` in `.autoharness/config.yaml`,
  `_stage.agent.md`, `_orchestrator.agent.md` (and its template), and the
  illustrative examples in `install-harness/SKILL.md`,
  `harness-config.yaml.tmpl`, `getting-started.md`, and
  `orchestrator-model-routing-spec.md`. This is a dogfood configuration/
  documentation update only; the flat/legacy `claude-opus-4.8` string remains
  a valid, unrestricted `model_family` value for any workspace that chooses
  it — no schema enum or install default forces this specific family.
- **P-021**: Added a new "Bounded Fix-Cycle Scope Containment and Deferred
  Expansion Capture" policy to the workflow policy registry
  (`workflow-policies.md.tmpl`, Amendment Log `1.20.0`). C1 defines a narrow
  same-contract-surface scope test (with a worked discrimination drawn from
  `docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`)
  that rejects "same file/function/PR/subsystem" or "related" as sufficient
  in-scope tests and resolves genuine ambiguity out of scope. C2 mandates a
  six-field capture payload (greppable `DEFERRED SCOPE EXPANSION` token,
  one-sentence expansion statement, C1-citing rationale, independently-judged
  PR-number/review-thread-ID/task/feature/shipment source refs with explicit
  `N/A` for unavailable identifiers, a `requires deliberation` flag, and
  kind/provisional priority) that is never conditional on a PR or thread
  existing. C3 requires bounded resolution of the in-scope finding, with the
  deferred-entry reference obligation conditional on actual review-thread
  availability — reply-then-resolve where a thread exists, residual-risk-record
  citation alone where none exists (pre-PR local review, build/CI findings) —
  plus a C3 symmetric guard that a same-surface completion must be fixed, not
  deferred. C4 makes the boundary unconditional: no authorization, including
  explicit operator authorization, expands the fix cycle that discovered the
  expansion in place; authorization can only open a separate forward work unit
  through the normal C2-capture-then-C6-deliberation intake path. C5 gives Ship
  a capture-only stash carve-out (create for capture only; no triage,
  prioritization, edit, harvest, deliberation, or discretionary removal/archival
  — while the existing manifest-derived post-merge source-stash retirement
  remains allowed). C6 requires every captured entry to route through Stage's
  `deliberate` skill before any planning. C7 is the violation action (P-005
  telemetry, `violation_policy: P-021`, halt). Relationship subsections tie
  P-021 to P-010 (the C5 carve-out is a narrow addition to Ship's existing Role
  Boundary), P-017 (preserved in full in dark factory mode), and P-018 (a
  threadless C3 discharge raises no P-018 obligation, since P-018 governs review
  threads only).
- Renamed the two dogfood pipeline agent definitions and their templates from
  dot-prefixed to underscore-prefixed filenames: the Stage and Ship agents now
  live at `_stage.agent.md` / `_ship.agent.md` (and `_stage.agent.md.tmpl` /
  `_ship.agent.md.tmpl`), with frontmatter `name` handles updated to `_Stage`
  and `_Ship`. Cross-references across docs, instructions, `.gitattributes`, the
  workspace profile, installer/tuner logic, tests, and the harness manifest were
  swept to the new names, and `.gitattributes` now pins both agent files to LF
  for portable checksums. `verify_workspace` retains the previous dot-prefixed
  filenames and handles as legacy migration aliases so existing installs upgrade
  cleanly.
- Removed the redundant per-agent `model_tier` frontmatter integer from all
  agent definitions (templates and installed instances). Config-driven agent
  model routing is unchanged: each agent's tier is bound by the `model_routing`
  map in `.autoharness/config.yaml` and resolved at install time into its
  `model_family` / `model_provider` / `reasoning_effort` frontmatter, while
  `max_subagent_tier` continues to declare the delegation ceiling. P-013.1 and
  P-013.4 were reframed from "declared `model_tier`" to config-resolved tier,
  `verify-workspace` now validates only `max_subagent_tier`, and the doc-review
  frontmatter check recommends `max_subagent_tier` instead of `model_tier`.
- Reverted the Python supervisor architecture in favor of self-contained start scripts, superseding earlier Plan-1 supervisor/`autoharness run`-style contract assumptions. (127-F / 136-S)
- Expanded operator-facing capability-pack documentation and runtime detection: Engram tool-surface guidance was corrected, capability-pack runtime availability became bounded/detectable, and cross-pack telemetry/evidence mapping was documented. (099-F / 104-S; 114-F / 122-S; 082-F / 120-S)
- `verify-workspace` now derives and composes template variables to match the install-harness contract, including role-aware routing values, shell-safe quoting for generated args, and fail-closed unresolved-variable behavior; the dogfood workspace now verifies at 0 unresolved / 0 blockers / 0 warnings. (142-F / 150-S)
- Introduced an explicit paired-edit maintenance contract for intentional template <-> dogfood divergence, so the allowed divergent pair set is pinned and verified rather than drifting silently. (137-F / 145-S)
- The cascade-close contract now matches real backlog behavior: pre-archived manifest members are handled explicitly, Ship derives an executable set that skips pre-archived superseded tasks, and the postcondition uses `allowed_ids` / `required_ids` semantics instead of raw manifest-equality assumptions. (132-F / 141-S; 139-F / 147-S; 147-F / 155-S)
- Compound/history documentation became stricter and clearer: `docs/compound` entries now require self-referential `source` semantics and standard docline fields, and the large P-020 history compaction pass repaired live status claims, dangling refs, operator-decision restoration, and supersession markers in historical docs. (140-F / 148-S; 146-F / 154-S; PR #411 / no shipment)

### Fixed

- Hardened the telemetry subsystem with idempotent disabled summaries, better provenance visibility, reusable JSONL scanning, Ship-lifecycle freshness coverage, and monotonic derived-size accounting. (092-F / 097-S)
- Fixed invocation-time model-routing enforcement and the escalation contract so verifier/template checks stay in sync, including the additive `resolved_escalation_route` payload field. (104-F / 108-S; 106-F / 110-S; PR #348 / no shipment)
- Fixed dark-factory multi-shipment sequencing and Ship claim integrity so queued-with-active-work anomalies fail closed instead of silently proceeding. (101-F / 105-S; 102-F / 106-S)
- Fixed the topology gate's predecessor logic and closure gating: the directional predecessor predicate no longer suppresses the target's own numeric fallback incorrectly, and releasability/closure completeness checks are enforced correctly. (131-F / 140-S; 109-F / 114-S; 109-F / 115-S)
- Fixed startup-script contract migration detection so `start.ps1` / `start.sh` are evaluated against the current thin-shim contract, ambiguous customized scripts surface for manual review, and preserved custom tails are summarized safely instead of being serialized raw into JSON reports. (125-F / 134-S)
- Fixed spike/docline and compound-frontmatter conformance end-to-end: valid spike `docline` nesting, restored workspace-wide docline lint traversal, required `source`/`doc_type` coverage in `docs/compound`, and stronger `source`-value validation. (128-F / 137-S; 138-F / 146-S; 136-F / 144-S; 140-F / 148-S; 146-F / 154-S)
- Removed accidentally committed root JSON outputs and added a tracked-root allowlist guard so stray `verify-workspace --format json` artifacts do not reappear in the repository root. (133-F / 142-S)
- Fixed Windows-local canonical test execution by containing destructive ambient `GIT_CONFIG_*` environment mutations; the supported Windows full-suite path now runs green, and a related topology `_run_git` failure path no longer launders infrastructure errors into misleading gate diagnoses. (144-F / 152-S)
- Hardened the circuit-breaker checkpoint format: an H1 heading now separates the frontmatter from the failure-chain body (fixing MD041), and the four free-form frontmatter values (`agent`, `skill`, `operation`, `identity`) are now prescribed as JSON string literals instead of naive double-quoting, fixing silent truncation and parse failures on embedded quotes, backslashes, colon-space, and space-hash. (150-F / 158-S)
- Refreshed a stale `harness-manifest.yaml` checksum for `workspace-discovery/SKILL.md` that had not been updated since the file's content last changed, which was causing `verify_workspace` to falsely report the file as user-modified. (150-F / 158-S)

### Deprecated

- The legacy flat `model_routing.escalation` key is retained only as a compatibility fallback; per-role `model_routing.stage.escalation` / `.ship.escalation` is the forward path. (113-F / 121-S)
- Legacy dot-prefixed Stage/Ship dogfood agent filenames/handles are compatibility aliases only; `_stage.agent.md`, `_ship.agent.md`, `_Stage`, and `_Ship` are the canonical names. (113-F / 121-S)
- Ship's post-merge source-stash retirement should now use stash-archive semantics; `backlogit_stash_remove` is no longer the prescribed cleanup route for that path. (137-F / 145-S)

## 1.4.11 - 2026-07-08

### Fixed

- Fixed new-artifact detection so the P-017 dark-factory trigger shim
  (`feature-flow-dark.prompt.md`) is never annotated `applicable: true` on
  primitive membership alone. Its documented install rule requires both
  Primitive 4 **and** P-017 opt-in, but applicability was derived solely from
  `primitives_installed`, so a workspace with Primitive 4 but no P-017 opt-in
  would have been offered the dark-mode shim as an auto-installable Growth
  artifact (a scope/policy over-reach given tune Step 4.2 installs
  `applicable: true` entries by default). Policy-gated prompts now carry a
  `requires_opt_in` annotation that forces `applicable: null` (operator-decides),
  and the tune-harness skill was updated to never auto-install an entry carrying
  `requires_opt_in` without explicit operator opt-in.

## 1.4.10 - 2026-07-08

### Added

- Added new-artifact (uninstalled template) detection to `verify-workspace`. The
  deterministic drift scan only re-hashed artifacts already recorded in the
  manifest, so templates newly added by a harness upgrade (for example new prompt
  variants) had no manifest entry and were invisible to tune's drift detection.
  The new `_scan_uninstalled_templates` scan diffs the `autoharness_home`
  template catalog against installed artifacts — matching by manifest artifact
  path, manifest template source, community-template install path, and file
  presence on disk — and surfaces uninstalled templates as advisory
  `new-artifact` findings in `new_artifacts[]`. The scan is scoped conservatively
  to the prompt class (extensible) and annotates each prompt finding with its
  documented install rule and applicability against the installed primitive set.
  Findings are advisory and never fail verification.
- Documented the new-artifact flow in the tune-harness skill: `verify-workspace`
  now feeds `new_artifacts[]` into a new Step 1.3b (New Artifact Detection),
  categorizes them as Growth drift, and installs accepted, applicable entries in
  Step 4.2 (Generate New Artifacts).

## 1.4.9 - 2026-07-08

### Added

- Added a stable, filename-independent `id:` frontmatter field to the three
  pipeline agents (`_orchestrator`/`autoharness/pipeline/orchestrator`,
  `.stage`/`autoharness/pipeline/stage`, `.ship`/`autoharness/pipeline/ship`) in
  both the templates and the installed mirrors, so an agent can be recognized as
  a pipeline agent even after an arbitrary rename.
- Added agent-identity migration detection to `verify-workspace`: it scans the
  agent directories and emits `contract: agent-identity` migration proposals when
  an installed pipeline agent drifted from its canonical filename or `name:`.
  Detection prefers the stable `id:` (survives arbitrary renames) and falls back
  to a legacy filename/`name:` alias registry (`orchestrator`/`dispatch`,
  `stage`, `ship`) for agents authored before the `id:` field existed. Elective
  and review/research agents are never proposed for renaming.
- Documented the agent-identity standardization workflow in the install-harness
  (Step 2.4) and tune-harness (Step 1.5b) skills, including the `id:`-preferred
  detection rules and the back-up / rename / cross-reference / manifest
  reconciliation procedure.

### Changed

- Restricted the globally distributed plugin agents to `auto-mergeinstall` and
  `auto-tune` only (explicit `plugin.json` `agents` array). The pipeline agents
  (`_orchestrator`, `.stage`, `.ship`) are local-only and are no longer eligible
  for global distribution.
- Stopped the startup scripts and the `setup-copilot-cli` / `setup-claude`
  helpers from copying the two global plugin agents into a workspace-local
  `.copilot`. Those agents are upgraded globally and must remain the versions
  used during an upgrade, not local installs. The startup script headers and the
  environment-setup guide were corrected accordingly.
- Updated the default model routing for new installs (tier2 →
  `claude-sonnet-5`, tier3 → `claude-opus-4.8`) and refreshed the illustrative
  model examples across the orchestrator agent template, harness-config
  template, harness-config schemas, and telemetry reference.

## 1.4.8 - 2026-07-08

### Added

- Added a tracked `templates/scripts/.env.local.tmpl` template that seeds a
  gitignored `.env.local` at the workspace root with a `workspaceFolder` anchor.
  It is generated only when absent, so per-developer secrets and machine-specific
  values survive re-installs and tunes.
- Added a parity `.env.local` loader to the bash startup script (`start.sh` and
  `start.sh.tmpl`) matching the PowerShell loader: each `KEY=VALUE` line is
  exported only when the variable is unset, one matching pair of surrounding
  quotes is stripped, and trailing whitespace is trimmed.
- Added a graphtor-docs-conditional `GRAPHTOR_EMBED_MODEL_DIR` entry to
  `.env.local` (via the `{{GRAPHTOR_ENV_BLOCK}}` variable), defaulting to
  `<workspace_root>/.graphtor/models/all-MiniLM-L6-v2` and overridable through the
  new `graphtor_docs.embed_model_dir` field in the harness-config and
  workspace-profile schemas.

### Changed

- Wired `.env.local` generation through the install-harness skill (new
  `{{WORKSPACE_ROOT}}` variable, only-if-absent generation, and gitignore
  negation that keeps the tracked `.tmpl` while ignoring the rendered file) and
  documented the workflow in the environment-setup guide.

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
