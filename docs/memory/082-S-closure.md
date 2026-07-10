---
type: post-merge-closure
shipment: 082-S
feature: 070-F
date: 2026-07-10
merge_sha: 7839eb9721281ba66909c5655ead0a2271dd5c8d
pr: 189
category: release-closure
tags: [closure, install-automation, deploy-harness, capability-pack-registry, installation-guide]
---

# 082-S Post-Merge Closure Memory

**Date**: 2026-07-10
**Shipment**: 082-S — Scripted install/deploy automation + consolidated installation guide
**Parent feature**: 070-F
**Merge SHA**: 7839eb9721281ba66909c5655ead0a2271dd5c8d (2 parents: 28b02cf base + 86bab12 head)
**PR**: #189 (merged 2026-07-10T08:56:07Z)

## What Was Shipped

All six manifest tasks under 070-F (respecting the dependency graph):

- `070.001-T` — `schemas/capability-pack-registry.schema.json` (draft-07 additive registry schema)
- `070.002-T` — `templates/packs/capability-pack-registry.yaml` (9 packs; ids match the harness-config enum)
- `070.003-T` — `templates/scripts/deploy-harness.ps1.tmpl` + `deploy-harness.sh.tmpl` (cross-platform six-phase deploy scripts)
- `070.004-T` — `scripts/deploy-harness.ps1` + `scripts/deploy-harness.sh` (dogfood rendered instances)
- `070.005-T` — install-harness + workspace-discovery skill wiring
- `070.006-T` — `docs/installation.md` (consolidated authoritative install guide) + doc supersede/nav updates

## Design Guardrails Honored

- **Compose is handoff-only** — scripts never resolve `{{VARIABLE}}` templates; they print the `/install-harness` command and hand composition + adversarial verification to the agent.
- **cwd containment** — scaffold/verify write only inside the workspace; out-of-cwd global install gated behind explicit `-Bootstrap`/`--bootstrap`; scaffold refuses to write when `.autoharness`/`config.yaml` is a symlink/reparse point.
- **Data safety** — `config.yaml` backed up before overwrite; `.env.local` never clobbered.
- **Additive registry** — no existing pack-enum consumers refactored (deferred, decision D3).

## Runtime Verification (depth: docs + scripts + schema)

- PowerShell: both `.ps1` scripts parse via `[Parser]::ParseFile` — OK. Native failures detected via explicit `$LASTEXITCODE` checks (Windows PowerShell 5.1 + 7.3+).
- Shell: both `.sh` scripts pass `bash -n` — OK.
- Dry-run under a python3-only host (WSL): `deploy-harness.sh --dry-run` → **EXIT 0**, 0 mutations, scaffold contained to cwd.
- Full test suite: `PYTHONPATH=src python -m unittest discover -s tests` → **Ran 445 tests, OK** (baseline 427 + 8 registry + 10 deploy-harness script tests).
- Template↔instance parity enforced by `test_template_renders_to_committed_instance`.
- Schema/registry: registry validates against the new schema; pack ids match the harness-config enum.

## Releasability: READY

- Green tests + successful script dry-run + schema validation satisfy the release gate for a docs/scripts/schema change.
- No runtime service, database, or rollout-sensitive surface is introduced; scripts are opt-in and non-destructive by default (dry-run = 0 mutations; an existing `config.yaml` is preserved unless `-Force`/`--force` is passed, in which case it is timestamp-backed-up before overwrite; `.env.local` is never clobbered). Note: repeated forced runs accumulate timestamped backups, so the forced-overwrite path is not strictly byte-idempotent.
- **Monitoring**: none required — no long-running runtime surface. Operators observe script exit codes (0 success; 1 preflight; 2 bootstrap; 3 register; 4 scaffold; 5 verify).
- **Rollback**: revert merge commit `7839eb9`; scripts are additive files with no migration/state.
- **Owner**: Ship agent (softwaresalt/autoharness).

## Review & Merge

- Local adversarial review + hardening applied before PR (`8b17adc`).
- Copilot review: **4 rounds**. Findings A–F (cycle 1, `29191fb`), G–J (cycle 2, `e1e46a3`), K–O (cycle 3, `86bab12`) all fixed + resolved. A 4th round raised further observations; per §1.8 3-cycle cap these were converted to tracked follow-ups (below) and all threads replied to + resolved.
- **0 unresolved review threads** at merge; `required_review_thread_resolution` satisfied.
- CI: `detect code changes` → `test` → `build` all passed on `86bab12`.
- Merged with a merge commit via `--admin` (author self-approval not possible under the PR-Required ruleset; Admin bypass granted).

## P-015 Safe Closure (single-artifact ops only)

- Each of the 6 tasks moved `queued → active → done` (native queue→archive relocation), verified individually.
- Parent `070-F` and shipment `082-S` moved to done + archived.
- **Cascade guard**: all 14 protected siblings (024-S, 025-S, 026-S, 027-S, 028-S, 029-S, 030-S, 033-S, 053-F, 053.004-T, 065-F, 071-F, 071.001-T, 083-S) remained in `.backlogit/queue/` after every op. `backlogit shipment ship` was NOT used (P-015; incidents 055-S/056-S).
- Backlog `.backlogit/` state churn is intentionally left uncommitted per operator instruction (working tree carries pre-existing foreign uncommitted changes that must not be swept into a commit).

## Follow-Ups (deferred per §1.8 review-fix cycle cap)

- **FU-1** — `--packs`/`-Packs` explicit subset is overridden when `--preset starter` is selected; clarify precedence or document that preset determines the pack set.
- **FU-2** — non-copilot-cli register path reports success when the `autoharness` executable is absent; add an executable-presence check.
- **FU-3** — decision-doc phase-ordering prose (~line 112) lists verify before compose/handoff; align wording with D2 and the scripts.
- **FU-4** — review `$ErrorActionPreference`/`$PSNativeCommandUseErrorActionPreference` interaction beyond the explicit `$LASTEXITCODE` checks already added.
- **FU-5** — registry-vs-enums drift check (decision D3): explicit tuning follow-up, intentionally not built in this shipment.
