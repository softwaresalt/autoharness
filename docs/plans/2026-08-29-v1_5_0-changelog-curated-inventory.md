---
title: "v1.5.0 curated changelog inventory (150.003-T)"
date: 2026-08-29
doc_type: plan
agent: "Ship"
---

# v1.5.0 Curated Changelog Inventory

Task: `150.003-T` (curation half of the changelog work; consumed by
`150.004-T`, the authoring half). Source basis: the 34 closure records in
`docs/closure/` (shipments `134-S`-`157-S` / features `125-F`-`149-F`, plus
10 thematic closure summaries), plus the existing `CHANGELOG.md`
`## Unreleased` block (L3-L104), which is mapped into this inventory rather
than dropped (PA-5).

This is a curation artifact, not the final `CHANGELOG.md` text. `150.004-T`
authors the actual `## 1.5.0 - YYYY-MM-DD` section from this inventory.

## Added

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

## Changed

- The backlog storage-root contract is now `.backlog`-first (`BACKLOGIT_WORKSPACE_DIR` -> `.backlog` -> `.backlogit`) for new/default lookup, while existing `.backlogit` workspaces remain fully supported and are **not** expected to self-migrate. (126-F / 135-S; 129-F / 138-S)
- Model routing now supports nested per-role escalation overrides (`model_routing.stage.escalation` / `.ship.escalation`) ahead of the legacy flat key, with `schema_version: 1.1.0` for the nested form and untouched `1.0.0` validation for legacy configs. (113-F / 121-S)
- Bundled/dogfood routing examples now use `claude-opus-5`, while `claude-opus-4.8` remains a valid unconstrained value for workspace configs. (113-F / 121-S)
- The canonical dogfood Stage/Ship agent artifacts are underscore-prefixed (`_stage.agent.md`, `_ship.agent.md`, `_Stage`, `_Ship`); legacy dot-prefixed names remain upgrade aliases, and redundant per-agent `model_tier` frontmatter has been removed in favor of config-resolved routing plus `max_subagent_tier`. (113-F / 121-S)
- Reverted the Python supervisor architecture in favor of self-contained start scripts, superseding earlier Plan-1 supervisor/`autoharness run`-style contract assumptions. (127-F / 136-S)
- Expanded operator-facing capability-pack documentation and runtime detection: Engram tool-surface guidance was corrected, capability-pack runtime availability became bounded/detectable, and cross-pack telemetry/evidence mapping was documented. (099-F / 104-S; 114-F / 122-S; 082-F / 120-S)
- Added policy P-021 across the workflow stack: bounded fix-cycle scope containment, mandatory deferred-scope-expansion capture, Stage-only deliberation before expansion work, and explicit Ship capture-only carve-outs. (134-F / 143-S)
- `verify-workspace` now derives and composes template variables to match the install-harness contract, including role-aware routing values, shell-safe quoting for generated args, and fail-closed unresolved-variable behavior; the dogfood workspace now verifies at 0 unresolved / 0 blockers / 0 warnings. (142-F / 150-S)
- Introduced an explicit paired-edit maintenance contract for intentional template <-> dogfood divergence, so the allowed divergent pair set is pinned and verified rather than drifting silently. (137-F / 145-S)
- The cascade-close contract now matches real backlog behavior: pre-archived manifest members are handled explicitly, Ship derives an executable set that skips pre-archived superseded tasks, and the postcondition uses `allowed_ids` / `required_ids` semantics instead of raw manifest-equality assumptions. (132-F / 141-S; 139-F / 147-S; 147-F / 155-S)
- Compound/history documentation became stricter and clearer: `docs/compound` entries now require self-referential `source` semantics and standard docline fields, and the large P-020 history compaction pass repaired live status claims, dangling refs, operator-decision restoration, and supersession markers in historical docs. (140-F / 148-S; 146-F / 154-S; PR #411 / no shipment)

## Fixed

- Hardened the telemetry subsystem with idempotent disabled summaries, better provenance visibility, reusable JSONL scanning, Ship-lifecycle freshness coverage, and monotonic derived-size accounting. (092-F / 097-S)
- Fixed invocation-time model-routing enforcement and the escalation contract so verifier/template checks stay in sync, including the additive `resolved_escalation_route` payload field. (104-F / 108-S; 106-F / 110-S; PR #348 / no shipment)
- Fixed dark-factory multi-shipment sequencing and Ship claim integrity so queued-with-active-work anomalies fail closed instead of silently proceeding. (101-F / 105-S; 102-F / 106-S)
- Fixed the topology gate's predecessor logic and closure gating: the directional predecessor predicate no longer suppresses the target's own numeric fallback incorrectly, and releasability/closure completeness checks are enforced correctly. (131-F / 140-S; 109-F / 114-S; 109-F / 115-S)
- Fixed startup-script contract migration detection so `start.ps1` / `start.sh` are evaluated against the current thin-shim contract, ambiguous customized scripts surface for manual review, and preserved custom tails are summarized safely instead of being serialized raw into JSON reports. (125-F / 134-S)
- Fixed spike/docline and compound-frontmatter conformance end-to-end: valid spike `docline` nesting, restored workspace-wide docline lint traversal, required `source`/`doc_type` coverage in `docs/compound`, and stronger `source`-value validation. (128-F / 137-S; 138-F / 146-S; 136-F / 144-S; 140-F / 148-S; 146-F / 154-S)
- Removed accidentally committed root JSON outputs and added a tracked-root allowlist guard so stray `verify-workspace --format json` artifacts do not reappear in the repository root. (133-F / 142-S)
- Fixed Windows-local canonical test execution by containing destructive ambient `GIT_CONFIG_*` environment mutations; the supported Windows full-suite path now runs green, and a related topology `_run_git` failure path no longer launders infrastructure errors into misleading gate diagnoses. (144-F / 152-S)

## Deprecated

- The legacy flat `model_routing.escalation` key is retained only as a compatibility fallback; per-role `model_routing.stage.escalation` / `.ship.escalation` is the forward path. (113-F / 121-S)
- Legacy dot-prefixed Stage/Ship dogfood agent filenames/handles are compatibility aliases only; `_stage.agent.md`, `_ship.agent.md`, `_Stage`, and `_Ship` are the canonical names. (113-F / 121-S)
- Ship's post-merge source-stash retirement should now use stash-archive semantics; `backlogit_stash_remove` is no longer the prescribed cleanup route for that path. (137-F / 145-S)

### Internal-only (excluded from CHANGELOG)

- `149-S-141-F-post-merge-closure.md` -- test-isolation diagnosis and ambient-cwd cleanup only; no shipped CLI/schema/template/agent behavior changed. (141-F / 149-S)
- `151-S-143-F-post-merge-closure.md` -- failure-message hardening and residual-defect capture for a pre-existing Windows test issue only; no new operator-facing surface. (143-F / 151-S)
- `153-S-145-F-post-merge-closure.md` -- measurement-only confirmation that a suspected order-dependence issue was already subsumed; no product/template/runtime change shipped. (145-F / 153-S)
- `pr342-pr339-review-remediation-closure.md` -- staging-plan/backlog remediation only; no source/template/schema/CLI behavior shipped. (PR #342 / no shipment)

### Coverage ledger (all 34 source records processed)

| Source record | Accounted for as |
|---|---|
| `134-S-125-F-post-merge-closure.md` | Fixed -- startup-script contract migration/reporting |
| `135-S-126-F-post-merge-closure.md` | Changed -- `.backlog`-first root support |
| `136-S-127-F-post-merge-closure.md` | Changed -- revert to self-contained start scripts |
| `137-S-128-F-post-merge-closure.md` | Fixed -- spike/docline frontmatter conformance |
| `138-S-129-F-cancellation-closure.md` | Changed -- no migration obligation for existing `.backlogit` workspaces |
| `139-S-130-F-post-merge-closure.md` | Added -- checkpoint payload contract |
| `140-S-131-F-post-merge-closure.md` | Fixed -- topology directional-predicate hotfix |
| `141-S-132-F-post-merge-closure.md` | Changed/Fixed -- explicit pre-archived cascade handling |
| `142-S-133-F-post-merge-closure.md` | Fixed -- remove stray root JSON artifacts + guard |
| `143-S-134-F-post-merge-closure.md` | Changed -- P-021 policy |
| `144-S-136-F-post-merge-closure.md` | Fixed -- restore workspace-wide docline lint guard |
| `145-S-137-F-post-merge-closure.md` | Changed/Deprecated -- paired-edit contract + stash-archive migration |
| `146-S-138-F-post-merge-closure.md` | Fixed -- baseline docline/YAML/path repair |
| `147-S-139-F-post-merge-closure.md` | Changed/Fixed -- Ship executable set skips pre-archived members |
| `148-S-140-F-post-merge-closure.md` | Changed/Fixed -- `docs/compound` docline backfill/template alignment |
| `149-S-141-F-post-merge-closure.md` | Internal-only |
| `150-S-142-F-post-merge-closure.md` | Changed -- verify-workspace template-variable derivation conformance |
| `151-S-143-F-post-merge-closure.md` | Internal-only |
| `152-S-144-F-post-merge-closure.md` | Fixed -- Windows env containment + honest git-failure diagnostics |
| `153-S-145-F-post-merge-closure.md` | Internal-only |
| `154-S-146-F-post-merge-closure.md` | Changed/Fixed -- `docs/compound` `source` semantics |
| `155-S-147-F-post-merge-closure.md` | Changed/Fixed -- cascade-close two-set gate |
| `156-S-148-F-post-merge-closure.md` | Added -- policy registry + review-persona layer install/restore |
| `157-S-149-F-post-merge-closure.md` | Added -- pre-review detector SDK / `gate pre-review` |
| `2026-07-26-088f-compression-experiment-review-telemetry-closure-summary.md` | Added/Fixed -- compression experiment, review routing, telemetry hardening |
| `2026-07-30-engram-dark-factory-ship-claim-integrity-closure-summary.md` | Changed/Fixed -- capability-pack docs, dark-factory sequencing, claim integrity |
| `2026-08-01-telemetry-model-routing-escalation-closure-summary.md` | Added/Changed/Fixed -- telemetry events, routing enforcement, escalation protocol |
| `2026-08-03-benchmark-staging-backlogit-telemetry-closure-summary.md` | Added -- benchmark suite, size/complexity metadata, backlogit telemetry mapping |
| `2026-08-05-pipeline-topology-gates-abc-closure-summary.md` | Added/Fixed -- topology gates A/B/C + DAG readiness |
| `2026-08-06-shipment-status-crash-resumption-crosspack-closure-summary.md` | Added/Changed -- shipment diagnostics, crash resumption, cross-pack docs |
| `2026-08-08-model-routing-capability-pack-resumption-closure-summary.md` | Changed/Deprecated -- F02FD596 hierarchy/schema-versioning; Added -- capability-pack runtime detection and resume advisory |
| `pr342-pr339-review-remediation-closure.md` | Internal-only |
| `pr348-circuit-breaker-diagnostic-escalation-policy-closure.md` | Fixed -- `resolved_escalation_route` escalation-contract enforcement |
| `pr411-p020-context-compaction-closure.md` | Changed -- historical docs compaction/repair |

## Handoff

`150.004-T` authors the `## 1.5.0 - YYYY-MM-DD` CHANGELOG.md section from
this inventory, folding the existing `## Unreleased` content (already
reflected in the Changed/Deprecated groups above, tagged `113-F / 121-S`)
into the new section and leaving `## Unreleased` empty.
