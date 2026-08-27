---
title: Compacted historical docs/memory index — pre-2026-07-16 completed units
doc_type: memory
memory_class: compacted
created: 2026-07-30
scope: historical-sweep
source_stash: [5F14396E]
threshold_days: 14
compaction_pass: docs/memory broad historical sweep (54 -> under 40-file working threshold)
consolidates:
  # Batch A — 2026-04 -> 2026-05 (early harness-surface + validator-framework era)
  - docs/archive/memory/2026-04-26-ship-005-s-execution.md
  - docs/archive/memory/2026-04-26-stage-autotune-follow-up-hardening.md
  - docs/archive/memory/2026-05-05-ship-006-s-security-harness-surface.md
  - docs/archive/memory/2026-05-05-ship-007-s-closure.md
  - docs/archive/memory/2026-05-05-stage-007-s-restaging.md
  - docs/archive/memory/2026-05-05-stage-atv-security-integration.md
  - docs/archive/memory/2026-05-06-ship-008-s-harness-doctor.md
  - docs/archive/memory/2026-05-06-ship-009-s-agent-session-discipline.md
  - docs/archive/memory/2026-05-21-stage-stash-triage-046-047.md
  - docs/archive/memory/2026-05-22-ship-041-s-multi-model-review.md
  - docs/archive/memory/2026-05-22-ship-048-s-subagents-flat-install-paths.md
  - docs/archive/memory/2026-05-22-stage-session-0EBC97D5-recovery.md
  - docs/archive/memory/2026-05-23-ship-050-s-runtime-validator-framework.md
  - docs/archive/memory/2026-05-24-ship-051-s-reference-adoption-follow-ups.md
  # Batch B — 2026-06-30 -> 2026-07-12 (deterministic-gates + P-015/P-016/P-017 foundations)
  - docs/archive/memory/2026-06-30-stage-deterministic-gates-staging.md
  - docs/archive/memory/2026-07-01-ship-052-s-deterministic-gates.md
  - docs/archive/memory/2026-07-01-ship-053-s-single-pr-default.md
  - docs/archive/memory/2026-07-01-ship-054-s-record-version.md
  - docs/archive/memory/2026-07-01-ship-055-s-telemetry-core.md
  - docs/archive/memory/2026-07-02-ship-056-s-eval-runner-reviewer.md
  - docs/archive/memory/2026-07-02-ship-057-s-closure-cascade-guard.md
  - docs/archive/memory/2026-07-03-ship-058-s-model-routing-construct1.md
  - docs/archive/memory/2026-07-03-ship-059-s-manifest-placeholder-scan.md
  - docs/archive/memory/2026-07-03-ship-060-s-no-parallel-policy-foundation.md
  - docs/archive/memory/2026-07-04-ship-061-s-ship-worktree-gate.md
  - docs/archive/memory/2026-07-04-ship-062-s-stage-orchestrator-p016-guidance.md
  - docs/archive/memory/2026-07-04-ship-063-s-p016-entrypoint-verification.md
  - docs/archive/memory/2026-07-04-ship-064-s-dark-factory-policy-contract.md
  - docs/archive/memory/2026-07-12-close-053-model-tier-removal.md
  - docs/archive/memory/2026-07-12-ping-loop-removal-acp-consolidation.md
  # Batch C — legacy undated (releases 1.4.x, early shipments 010-012, closures 034-088)
  - docs/archive/memory/034-S-session.md
  - docs/archive/memory/035-S-release-1.4.3.md
  - docs/archive/memory/036-S-pr89-followup-closure.md
  - docs/archive/memory/037-S-closure.md
  - docs/archive/memory/039-S-closure.md
  - docs/archive/memory/040-S-closure.md
  - docs/archive/memory/082-S-closure.md
  - docs/archive/memory/083-S-closure.md
  - docs/archive/memory/088-S-closure.md
  - docs/archive/memory/release-1.4.4-closure.md
  - docs/archive/memory/release-1.4.5-closure.md
  - docs/archive/memory/ship-010-S.md
  - docs/archive/memory/ship-011-S.md
  - docs/archive/memory/ship-012-S.md
---

# Compacted historical docs/memory index (pre-2026-07-16 completed units)

Dense consolidation of 44 historical agent-session memory notes from completed
release units (2026-04-26 through 2026-07-12). This is a **broad historical
sweep** performed as a dedicated `compact-context` pass (target `docs/memory`),
consuming deferred stash `5F14396E`. It is distinct from the per-release-unit
post-merge floor compactions that produced the `104S-099F` and `105S-101F`
compacted indexes in this same directory.

**Forwarding rule.** Every file listed below was moved (with Git history preserved via
rename detection) from `docs/memory/<name>` to `docs/archive/memory/<name>`. Content is
otherwise unchanged, with one deliberate exception: where an archived note contained a
relative link to another artifact that this same compaction relocated, that link was
repointed to the artifact's new path so the reference still resolves. No prose, findings,
or institutional knowledge were altered or deleted — the dense takeaway lives here and the
full verbose original lives at the archive path. To read the full note for any row,
prepend `docs/archive/memory/` to the filename.

**Preserved in place (not compacted):** `docs/memory/compacted/*` (this index +
the two per-unit indexes), the `.gitkeep`, `docs/memory/098-S-closure.md` (closed
2026-07-29 — within the 14-day threshold, so preserved despite its undated
filename), and all within-threshold recent notes under `docs/memory/2026-07-26/`,
`docs/memory/2026-07-27/`, and `docs/memory/2026-07-28/` (all newer than the
14-day threshold).

## Batch A — early harness-surface + validator-framework era (2026-04 to 2026-05)

| Archived file (prepend `docs/archive/memory/`) | Durable takeaway |
|---|---|
| `2026-04-26-ship-005-s-execution.md` | 005-S Auto-Tune follow-up hardening: `verify_workspace.py` emits deterministic `learning_signals{}` and enforces Step 1.8 learning-loop checks; `tune-harness`/`auto-tune` consume structured signals; self-install routes through `distribution.local_agents_dir`. Lesson: work was wrongly started on `main`, corrected to a feature branch preserving the dirty worktree. |
| `2026-04-26-stage-autotune-follow-up-hardening.md` | Stage grouped stash `50AFB1E5`/`D1B73D17`/`ADB5C4C8` into 005-F/005-S; kept `51390A3D` stashed (post-merge closure hardening) to avoid a low-value singleton shipment. |
| `2026-05-05-ship-006-s-security-harness-surface.md` | 006-S made security a **core** harness surface: `security-audit` SKILL, review/plan-review security personas, `security-sentinel` agent, 7 install vars, `verify_workspace` security assertions. Rules: file-writing agents must declare `edit`; STRIDE evidence uses anchors, not `file:line`. |
| `2026-05-05-ship-007-s-closure.md` | 007-S shipped `browser-automation` + `iterative-experiment` skills + install wiring. Rules: new vars must round-trip through `harness-config.yaml.tmpl`; config override beats auto-detection; make `auth:none` explicit; validate traversal via `Path.parts`. |
| `2026-05-05-stage-007-s-restaging.md` | Restaged 007-S: collision-resistant experiment filenames under `{{EXPERIMENT_RESULTS_DIR}}`; split 007.004-T as explicit verification to preserve width-isolation / 2-hour rule. |
| `2026-05-05-stage-atv-security-integration.md` | ATV starterkit triaged into 006/007/008-S with security as core; ship order set by priority 006 -> 007 -> 008; low-priority "evaluate" items stay in stash. |
| `2026-05-06-ship-008-s-harness-doctor.md` | 008-S added always-installed `harness-doctor` skill. Policy: `mode:fix` **quarantines** orphaned `.tmpl` files under `.autoharness/quarantine/` (never deletes); read `artifacts[*].path`; keep in its own "Always-installed skills" section. |
| `2026-05-06-ship-009-s-agent-session-discipline.md` | 009-S codified **P-010** (stage/ship boundary), **P-011** (mandatory branch creation), **P-012** (pre-flight MCP tool availability); P-005 is telemetry only. Dispatch must be registry-driven, not template-only. |
| `2026-05-21-stage-stash-triage-046-047.md` | Triaged 3 stash entries into 046-F (isolated `verify_workspace` output-path bug) + 047-F (grouped multi-model review). Ship order 040 -> 041; 044/045 stayed in deliberation. |
| `2026-05-22-ship-041-s-multi-model-review.md` | 041-S shipped `doc-review` skill + adversarial-review alt-model routing + post-remediation recursion. Rule: `.tmpl` prose must not contain literal unresolved `{{VARIABLE}}` text; describe placeholders abstractly. |
| `2026-05-22-ship-048-s-subagents-flat-install-paths.md` | 048-S consolidated non-top-level agents into `agents/subagents/`. Key distinction: install-path tables document runtime destinations; Primitive-map tables keep template-**source** paths stable (a wrong source-path change was reverted). |
| `2026-05-22-stage-session-0EBC97D5-recovery.md` | Recovered lost stash `0EBC97D5` as feature 048-F (absent from active+archived stash); no `verify_workspace` change needed (no hardcoded review/research path assertions). |
| `2026-05-23-ship-050-s-runtime-validator-framework.md` | 050-S established the runtime-validator / releasability contract: schema + Ship flow + `runtime-verification` + `operational-closure` skills + overlays + verifier assertions + dogfood profile. Rule: schema/terminology changes land in **both** versioned and unversioned workspace-profile schemas + verifier constants together. Merged PR #108. |
| `2026-05-24-ship-051-s-reference-adoption-follow-ups.md` | 051-S installed `coding-discipline.instructions` template, added correctness/maintainability review personas, extended circuit-breaker with bounded cooldown; archived released 049 scope under 051-S. Merged PR #110. |

## Batch B — deterministic-gates + P-015/P-016/P-017 foundations (2026-06-30 to 2026-07-12)

| Archived file (prepend `docs/archive/memory/`) | Durable takeaway |
|---|---|
| `2026-06-30-stage-deterministic-gates-staging.md` | Established the Phase-1/Phase-2 split for deterministic gates + telemetry/eval. Locked policies: atomic all-or-nothing gating, absolute enforcement with operator-only `--force`, 3-failure block+requeue, and "no in-process execution loop" for `autoharness gate check`. IDs: 050-F/052-S, 051-F, 052-F, 053-F, 054-F. |
| `2026-07-01-ship-052-s-deterministic-gates.md` | 052-S shipped Phase-1 `autoharness gate check`: additive/optional config, fail-open-to-current, hermetic subprocess runner, absolute enforcement, telemetry under `.autoharness/gates/`. Schema `validation-gates/1.0.0`. |
| `2026-07-01-ship-053-s-single-pr-default.md` | 053-S made sequential single-PR-at-a-time the documented default; parallel/pipelined shipping is opt-in under P-001. Correction: wording is "at most one" active release unit, not "exactly one". |
| `2026-07-01-ship-054-s-record-version.md` | 054-S fixed a false-drift bug so install writes the real `autoharness_version` instead of a baked literal. Lesson: trace producer -> field -> consumer end-to-end; schema-required fields can still be wrong when the producer bakes constants. |
| `2026-07-01-ship-055-s-telemetry-core.md` | 055-S Phase-2 telemetry core: Execution Epochs -> SQLite + JSONL, fail-open dispatch, workspace confinement, atomic writes, CLI wiring. Lesson: including the parent feature in a partial shipment caused `backlogit shipment ship` to cascade/archive unshipped children — carry only delivered tasks. |
| `2026-07-02-ship-056-s-eval-runner-reviewer.md` | 056-S shipped headless eval runner + deterministic reviewer matrix (replay-only, line-cited diff grading). Bug fixes: unified-diff parsing must respect hunk state/new-line counts; CLI help detection inspects only the leading token. Documented the backlogit cascade bug + safe single-artifact workaround. |
| `2026-07-02-ship-057-s-closure-cascade-guard.md` | 057-S introduced **P-015 safe-close**: item-by-item closure with verify-after-each and git-revert-on-cascade, preserving protected siblings/parent (with P-007 archive integrity). First applied to its own shipment record. Full-feature shipments may leave the completed parent queued by design. |
| `2026-07-03-ship-058-s-model-routing-construct1.md` | 058-S removed the deprecated per-agent `model_routing:` frontmatter **string** (Construct 1) while preserving the config-binding **object** (Construct 2). Safe-close preserved blocked sibling 053.004-T and left the feature queued. |
| `2026-07-03-ship-059-s-manifest-placeholder-scan.md` | 059-S hardened `verify_workspace` to scan top-level scalar fields in `.autoharness/harness-manifest.yaml` for unresolved `{{...}}` (catches `autoharness_version` literals); loosened MCP policy to allow an absent/local-only root `.mcp.json` while still enforcing required servers when present. |
| `2026-07-03-ship-060-s-no-parallel-policy-foundation.md` | 060-S established **P-016 No Parallel Branch/Worktree Execution**, threading the single-active-worktree rule through constitution/policies/templates. Learned terminal states differ by artifact type (`done` vs `shipped`). |
| `2026-07-04-ship-061-s-ship-worktree-gate.md` | 061-S wired P-016 into Ship intake: branch/worktree topology check before branch creation, fallback assembly, or shipment claim; invalid/ambiguous worktrees fail closed with `WORKTREE_TOPOLOGY_BLOCKED`. |
| `2026-07-04-ship-062-s-stage-orchestrator-p016-guidance.md` | 062-S aligned Stage (explicit spike/research worktree exception) and Orchestrator (no parallel branch/worktree pipelining implication) with P-016 for entry-point coherence. |
| `2026-07-04-ship-063-s-p016-entrypoint-verification.md` | 063-S made the P-016 no-parallel rule discoverable from root/generated entry points, install-verification guidance, architecture instructions, prompts, README, and getting-started; closed feature 060-F. Discoverability is part of enforcement, not just runtime checks. |
| `2026-07-04-ship-064-s-dark-factory-policy-contract.md` | 064-S introduced **P-017 Dark Factory Autonomy Contract**: bounded dark-mode triggers, local-review authority, CI/check gating, advisory hosted-review posture, merge approval/admin fallback, stop conditions, visibility events. |
| `2026-07-12-close-053-model-tier-removal.md` | Removed redundant per-agent `model_tier` frontmatter while preserving config-driven routing (`model_routing`, `max_subagent_tier`, `model_family`, `model_provider`, `reasoning_effort`, `subagent_depth`). Added backward-compat coverage proving installs with leftover `model_tier` do not regress. |
| `2026-07-12-ping-loop-removal-acp-consolidation.md` | Removed the retired `ping-loop.prompt` artifact + live references, consolidating `agent-intercom` on ACP mode while preserving heartbeat behavior. Caveat: broader MCP -> ACP transport consolidation and external-workspace retired-artifact migration remain open follow-ups. |

## Batch C — legacy releases 1.4.x + early shipments/closures (undated)

| Archived file (prepend `docs/archive/memory/`) | Durable takeaway |
|---|---|
| `034-S-session.md` | Installed capability packs `agent-engram`, `agent-intercom`, `graphtor-docs` into dogfood. Rule: `graphtor-docs.instructions` placeholders resolve at install time; compare installed checksum against a **re-rendered** template, not raw template text. Captured `binary_path` vs `binary_on_path` correction and multi-block-edit heading preservation. |
| `035-S-release-1.4.3.md` | v1.4.3 released/published; all 039.xxx shipped incl. graphtor-docs `binary_path` field alignment. Policy: PR-Required ruleset can block merge even when classic protection looks null; owner `gh pr merge --admin` bypass was the accepted path; `require_last_push_approval` mattered with COMMENTED-only Copilot reviews. |
| `036-S-pr89-followup-closure.md` | Closed PR #89 follow-up hygiene: fixed the 035-S memory note, added `archived_from` + commit provenance to `.backlogit/archive/035-S.md`, deleted the stale `.backlogit/queue/035-S.md`. Rule: shipment archive records keep `status: shipped`, not `archived`. |
| `037-S-closure.md` | Elevated the P-014 Copilot review gate + post-merge closure surveillance into first-class policy and ship/pr templates. Lesson: `require_last_push_approval` can force §1.9 recheck failures after minor fix commits; operator-approved admin bypass is acceptable when the failure is only that review-policy interaction. |
| `039-S-closure.md` | Repository hygiene: removed accidental `.worktrees` gitlink tracking and ignored `.worktrees/`. Re-validated mergeable state from scratch before merge; no release/tag obligations. |
| `040-S-closure.md` | Fixed `verify_workspace` output placement so reports stay under `.autoharness/staging/` (no silent root fallback). Practices: create closure branches from `origin/main`; use `git stash push --include-untracked` to preserve unrelated dirty work during closure. |
| `082-S-closure.md` | Shipped scripted install/deploy automation + consolidated installation guide. Conventions: compose is handoff-only, scaffolding is cwd-contained, config backup precedes overwrite, and never `backlogit shipment ship` when P-015 single-artifact closure would cascade. Recorded FU-1 (explicit `--packs` subset overridden by `--preset starter`; later fixed in 096). |
| `083-S-closure.md` | Renamed the dogfood CI aggregation gate `build` -> `ci gate` preserving behavior (`always()`, `needs: [changes, test]`). Used local move/archive (not shipment ship); single-task parent feature treated as fully shipped. |
| `088-S-closure.md` | Completed `graphtor-docs` full-preset parity. Pattern: versioned schemas must be deep-equal to the corresponding root-schema blocks; dogfood verification may be composition-only when the external tool degrades gracefully; commit backlog relocations on `main` when local-only closure would be reverted by a hard reset. |
| `release-1.4.4-closure.md` | v1.4.4 shipped + PyPI-confirmed. Lesson: GitHub classic protection can look permissive while a ruleset still blocks merge; check rulesets directly; admin bypass works when the owner is Admin and the ruleset allows pull-request bypass. |
| `release-1.4.5-closure.md` | v1.4.5 released + PyPI-confirmed, but repo-tracked closure artifacts still needed a post-merge closure PR to land on `main`. Reminder: release closure is incomplete until backlog archive provenance is reconciled and the closure PR passes P-014 readiness + explicit operator approval. |
| `ship-010-S.md` | Established session lifecycle gates + backlogit sync behavior for Stage/Ship templates. Enduring gate: non-negotiable merge confirmation via `git merge-base --is-ancestor`; backlog index sync moved into the operational flow; closure-sync-failure broadcast gated behind `agent-intercom`. |
| `ship-011-S.md` | Spike research adopted a coding-discipline instructions template, a review-persona subset, a cooldown-only SDK-guardrail interpretation, and a portability audit pattern. Constraint: portability exemptions are path-scoped via `(rule, file_glob)` allow-list tuples, not content-pattern exceptions. |
| `ship-012-S.md` | Added workspace portability scanning + dynamic policy-proposal generation. Policy: detected policy-gap candidates create operator-review **proposals** only (never auto-installed); scan allow-lists must be explicit and file-glob scoped to avoid false positives. |

## Cross-cutting institutional learnings

Distilled patterns that recur across all three batches — the durable "why" behind
the current harness contracts:

- **Core-surface promotion.** Security, review, validation, runtime-validator, and
  telemetry surfaces were progressively promoted from optional packs to core
  harness wiring. Every template/variable addition must round-trip through
  `install-harness` registration + `harness-config.yaml.tmpl` + `verify_workspace`
  assertions in lockstep — a template alone is never sufficient.
- **Source vs install destination.** A recurring documentation pitfall: install-path
  tables document runtime destinations; Primitive-map / template-source paths must
  stay stable. Changing source paths to match install layout is a false move.
- **Safe-close / cascade-guard lineage (P-015 + P-007).** Partial-feature shipments
  must close item-by-item with verify-after-each + git-revert-on-cascade; never
  `backlogit shipment ship` when it would cascade protected siblings/parent; carry
  only delivered tasks in a partial shipment, never the parent unless fully complete.
- **Workflow-discipline policy stack.** P-010 (stage/ship boundary), P-011 (mandatory
  branch creation), P-012 (pre-flight tool availability), P-016 (no parallel
  branch/worktree — enforced at Ship intake and made discoverable at every entry
  point), P-017 (dark-factory autonomy contract). P-005 is telemetry only, not a
  behavioral policy.
- **Merge-gating reality.** PR-Required rulesets can block merge even when classic
  branch protection looks permissive; `require_last_push_approval` plus
  COMMENTED-only Copilot reviews force §1.9 rechecks after fix commits. Historically,
  operator-approved `--admin` bypass was the accepted escape hatch for
  review-policy-only failures. (Current repo posture layers on **P-009 merge-commits-only**
  and **P-014 explicit operator approval** per merge. Under **P-018**, `--admin` does
  NOT bypass an engaged/incomplete current-HEAD Copilot review or unresolved
  Copilot-authored threads — only an audited, operator-authorized
  `autoharness gate copilot-review --force` may override that block.)
- **Deterministic-gates framework.** Schema-driven, additive/optional config,
  fail-open-to-current defaults, atomic all-or-nothing enforcement, hermetic
  subprocess runner, operator-only `--force`, 3-failure block+requeue, local
  telemetry under `.autoharness/gates/`.
- **Model-routing evolution.** Remove only deprecated per-agent frontmatter forms
  (the `model_routing` Construct-1 string, `model_tier`); config-driven routing is
  the real control plane. Keep backward-compat coverage for leftover fields.
- **Failure-mode hardening pattern.** Broaden detectors conservatively; prefer
  mandatory/explicit separators over permissive regexes; ship negative controls;
  scope allow-lists by `(rule, file_glob)` tuples, not content patterns.
- **Install/runtime integrity.** Record the real version (no baked literals); scan
  manifests for unresolved placeholders; keep schema parity (versioned == unversioned
  == verifier constants); allow graceful external-tool degradation in dogfood
  verification.
- **Release discipline (1.4.x line).** Merge commits, annotated tags, workflow runs,
  PyPI confirmation, and backlog archive-provenance reconciliation are all part of
  closure. Release closure is not complete until the closure PR lands on `main` with
  P-014 approval.

## Traceability and compaction metadata

- **Pass type:** broad historical sweep (`compact-context`, target `docs/memory`),
  distinct from the per-release-unit P-020 post-merge floor.
- **Stash consumed:** `5F14396E` (Stage-triaged 2026-07-29, DEFERRED as operational
  maintenance; the compaction work it requested is done. Stash-entry archival is
  handed to Stage per the P-010 role boundary — stash operations are Stage-owned).
- **Files consolidated:** 44 verbose memory notes -> `docs/archive/memory/` (via
  `git mv`, git history preserved). This index is the dense, discoverable summary;
  the archive holds the full originals.
- **`docs/memory/` file count:** 54 before -> 11 after (`.gitkeep`, three
  `compacted/` indexes, `098-S-closure.md`, and six within-threshold recent notes
  remain in place), restoring the directory to well under the 40-file working threshold.
- **Nothing deleted.** Every consolidated note remains readable at its archive path;
  the `consolidates:` frontmatter list is the machine-readable forwarding map.
