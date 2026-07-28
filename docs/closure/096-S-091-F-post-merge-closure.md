---
shipment: 096-S
feature: 091-F
pr: 238
merge_commit: 42a5d6b9ae6649b997e60efb56f30ea3aae9f4af
merged_at: "2026-07-28T06:22:42Z"
closure_status: READY
---

# 096-S / 091-F Post-Merge Closure — Multi-Model Review Routing Enhancements

Shipment 096-S installed multi-model adversarial review routing enhancements for
autoharness templates, schemas, skills, and documentation. The merged PR changed
source-of-truth harness artifacts only; no application runtime or deployed service
surface was introduced.

## Merge Confirmation

- PR #238 merged to `main` with merge commit
  `42a5d6b9ae6649b997e60efb56f30ea3aae9f4af`.
- Merge commit parents were `48269d5` and `313ea3e`, preserving the P-009
  merge-commit strategy (no squash/rebase).
- `main` and `origin/main` were synced at `42a5d6b` before closure began.

## Runtime Verification

**Surface**: not applicable — no product runtime surface; this shipment changed
harness templates, schemas, skills, policies, tests, and documentation only.
Verification is deterministic structural/schema/unit verification, not live
runtime probing.

| Check | Evidence | Result |
|---|---|---|
| Targeted anchor review routing tests | `python -m pytest -q tests\test_anchor_review_routing.py` | **PASS** — 10 passed |
| Repository test suite | `python -m unittest discover -s tests -q` | **PASS** — 711 tests OK |
| Manifest checksum drift | `autoharness verify-workspace --workspace . --autoharness-home . --json` checksum scan | **PASS for tracked skill drift** — install/verify skill checksums reported `unchanged`; command still reports pre-existing unresolved staging placeholders/targeted checks outside this closure |
| CI on PR #238 | GitHub Actions `detect code changes`, `test`, `ci gate` | **PASS** |
| Backlog close | Operator-directed `C:\Tools\backlogit.exe shipment ship 096-S`; `C:\Tools\backlogit.exe sync` | **PASS WITH RECORDED P-015 DEVIATION** — cascade archived exactly the task-only manifest plus derived covering feature `091-F`; verified shipment, tasks, and feature archived |

No manual runtime checkpoint was required: there is no UI, server, CLI runtime
behavior, database migration, or deployed service to exercise.

## Operational Closure

- **Healthy signals**:
  - CI was green before merge (`detect code changes`, `test`, `ci gate`).
  - Local deterministic checks covered schema parity, anchor route defaults,
    placeholder placement, persona path integrity, plan-review markers, and
    harvest/plan-harden gates.
  - Manifest checksums for edited global skills were refreshed and reported
    drift-clean in checksum scan.
  - Backlog closure archived shipment `096-S`, tasks `091.001-T` through
    `091.008-T`, and covering feature `091-F`. The operator explicitly directed
    `backlogit shipment ship 096-S`; this is recorded as a bounded P-015 deviation
    from Ship's current single-artifact safe-close contract because the command is
    normally forbidden for partial-feature shipments.
- **Anchor route behavior**: `model_routing.anchor_review` defaults to
  provider `openai`, family `gpt-5.6-sol`, and reasoning effort `high` when no
  workspace override exists. Global, non-rendered skills resolve this route from
  target workspace config at runtime and declare degradation only when the
  resolved route cannot be dispatched.
- **Adversarial-review confidence handling**: four-reviewer anchor-enabled pools
  now classify plural non-majority agreement (for example, 2-of-4) as a
  MEDIUM-confidence Plurality section, preserving consensus / majority / unique
  semantics while making every agreement count total.
- **Persona install-path normalization**: plan-review and install-harness persona
  identity mappings now use the canonical flat `.github/agents/subagents/`
  destination for non-top-level agents, not the retired categorized
  `review/` / `research/` layout.
- **Failure signals to watch**: future reviews should treat unresolved
  `{{ANCHOR_REVIEW_*}}` placeholders in source-controlled global skills, or
  `.github/agents/review/` / `.github/agents/research/` installed identity paths,
  as regression signals.
- **Rollback**: revert merge commit `42a5d6b9ae6649b997e60efb56f30ea3aae9f4af`
  if the harness routing contract must be removed.
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for any
  follow-up routing.
- **Residual follow-ups**: none.

**Closure verdict: READY.** No release conditions outstanding.

## Backlog Reconciliation

Operator-directed `backlogit shipment ship 096-S` closed the task-only shipment
manifest and archived the derived covering feature from the `091` task-ID prefix.
This closure records the P-015 deviation explicitly because Ship's current agent
definition normally requires single-artifact archival instead of the cascade
command. Post-command verification found only the intended shipment, manifest
tasks, and covering feature archived:

| Item | Final state |
|---|---|
| `096-S` | `archived` with `archived_status: shipped` |
| `091-F` | `archived` with `archived_status: done` |
| `091.001-T` … `091.008-T` | each `archived` with `archived_status: done` |
