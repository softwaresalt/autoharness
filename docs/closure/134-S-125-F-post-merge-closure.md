---
shipment: 134-S
feature: 125-F
tasks: [125.001-T, 125.002-T, 125.003-T]
feature_pr: 340
closure_pr: 341
merge_commit: afde69344d827d2b883f86f91ad5c842aab72885
merged_at: "2026-08-15T08:58:21Z"
reviewed_head: 4bab0d0f19d2e838ad0d4e177bf0552ba81a5dfe
closure_status: READY
compaction_status: degraded
feature_terminal_status: done
feature_archived_status: done
---

# 134-S / 125-F Post-Merge Closure — Tune Startup-Script Contract Migration

Shipment `134-S` implemented covering feature `125-F`: extending Auto-Tune's
deterministic drift model so installed target-workspace `start.ps1`/`start.sh`
are evaluated against the CURRENT thin-shim startup-script contract, not only
their historical manifest checksum. `125-F` is a root feature (no parent) with
exactly 3 children (`125.001-T`, `125.002-T`, `125.003-T`), all of which are
this shipment's manifest, so `125-F` is fully covered by `134-S` alone —
qualifying for the P-015 verified fully-covered-root cascade close path (see
Backlog Archival below).

This shipment executed under an explicit `DARK_MODE_ACTIVE` bounded
dark-factory continuation record, ordered scope `[134-S, 135-S, 136-S]`, this
invocation covering `134-S` only. Predecessor `133-S` was explicitly excluded
from scope and was never claimed, edited, or shipped — confirmed at closure
time still `archived_status: queued`, unchanged.

## Merge Confirmation

- PR **#340** ("feat(134-S/125-F): tune startup-script contract migration for
  start.ps1/start.sh") merged to `main` at `2026-08-15T08:58:21Z` with merge
  commit `afde69344d827d2b883f86f91ad5c842aab72885`. Confirmed via
  `git log --pretty=%P -1`: two parents
  (`5dc346053d428c6b1340e16a90819c2f641f81b7` prior `main` tip +
  `4bab0d0f19d2e838ad0d4e177bf0552ba81a5dfe` feature branch HEAD), preserving
  the P-009 merge-commit strategy. Confirmed ancestor of `origin/main`
  (`git fetch origin main` then `git merge-base --is-ancestor afde6934...
  origin/main` -> exit 0).
- Repo merge-strategy settings (P-009), verified before merge:
  `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false` — only "Create a merge commit" is possible.
- Reviewed HEAD `4bab0d0f19d2e838ad0d4e177bf0552ba81a5dfe` matches the
  feature-branch parent of the merge commit exactly.
- P-018 Copilot-review gate: `SATISFIED` for the final HEAD, 0 unresolved
  threads, re-verified unconditionally immediately before merge (no HEAD
  advance since the last pass).

## Review-Fix History (PR Lifecycle)

- Local adversarial review (1 of 3 cycles used): fixed a byte-exact tail
  comparison that broke idempotence on trailing whitespace.
- Copilot review (3 of 3 cycles used, all resolved clean by the final round):
  1. `dd92a8b2` — disabled/commented current-marker text misclassified as
     `current`; known-legacy custom-tail extraction/preservation gap.
  2. `a4e8273b` — unattributed manifest-checksum drift wasn't consulted by
     the classifier; fixed by failing closed to `ambiguous`. This correctly
     surfaced this repository's own `start.sh`/`start.ps1` as `ambiguous`
     (pre-existing, intentionally customized dogfood scripts, confirmed via
     independent hash/git-history evidence — not a regression). SKILL.md
     wording corrected to match.
  3. `4bab0d0f` — the preserved custom-section tail (operator-controlled
     content, may include secrets) was serialized raw into on-disk JSON
     verification reports; fixed by replacing it with a non-sensitive
     hash/size summary and re-reading the original file at migration-apply
     time instead.

See `docs/compound/2026-08-15-never-serialize-raw-operator-content-into-json-reports.md`
and `docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`
for the generalizable patterns extracted from findings 3 and 2 above.

## Validator Evidence

| Area | Verdict | Evidence |
|---|---|---|
| Targeted suite (`test_startup_script_contract.py` + `test_verify_workspace.py`) | PASS | `178 passed, 95 subtests passed` |
| Full repository suite (excluding one pre-existing unrelated flaky test) | PASS | `1987 passed, 24 skipped, 789 subtests passed` |
| CLI smoke test | PASS | `.venv\Scripts\autoharness.exe --help` exits 0 |
| Self-verify-workspace against this repo's own install | PASS | 0 strict schema blockers, 0 blockers, 0 warnings; 2 expected `ambiguous` migration proposals (`start.sh`, `start.ps1`) — correct, non-regressive, `manual_review: true`, never auto-applied |
| Current-head local review (PR #340) | PASS | Reviewed HEAD `4bab0d0f`; `P0=0, P1=0` |
| Copilot review gate (PR #340) | PASS | `SATISFIED`; all 4 Copilot-authored threads (across 3 rounds) replied-to and resolved |
| GitHub Actions (PR #340) | PASS | `test`, `ci gate` green; `pipeline-topology (ambient)` advisory failure (expected, audited, non-blocking — no branch protection on `main`, gate-required repo variable unset) |

## Runtime Verification

Runtime surface touched: CLI (`autoharness verify-workspace` / `autoharness
--help`) per `.autoharness/workspace-profile.yaml`
`runtime_validation.validator_manifest`. Probe `cli-help` executed:
`.venv\Scripts\autoharness.exe --help` exits 0 and prints CLI help text
(PASS, matches `expected_signal`). Additionally ran
`autoharness verify-workspace --workspace . --autoharness-home .` against
this repository's own self-installed harness: 0 strict schema blockers, 0
blockers, 0 warnings, 2 migration proposals (`start.sh`/`start.ps1`, both
`ambiguous`, `manual_review: true`, never auto-applied) — the correct,
expected, fail-closed outcome of the round-2 checksum-drift fix against this
repo's own pre-existing customized root scripts, not a regression.
`minimum_verdict: PASS` met.

## Invariants Preserved

- The new classifier is strictly additive to the existing generic manifest
  checksum scan in `verify_workspace` — never replaces it.
- No auto-apply of any migration proposal; `ambiguous` always requires
  operator review.
- This repository's own root `start.ps1`/`start.sh` and the canonical
  templates remain the reference/source of truth and were never modified by
  this shipment's code (only the classification/report layer changed).
- Custom-section tail content (operator secrets risk) is never embedded raw
  in any serialized classification/proposal structure.

## Pre-Deploy Audits and Deployment Path

Pure CLI/library/documentation change to an offline verifier and skill
documentation; released by merge-only deployment to `main`. No runtime
service, background job, deployment surface, or public API is introduced or
altered. No pre-deploy audit beyond the full regression suite and CLI smoke
test above is applicable.

## Monitoring and Healthy Signals

Healthy operation is observed via `autoharness verify-workspace` output on
any target workspace: `missing`/`known-legacy`/`customized` classifications
should produce non-destructive, evidence-backed migration proposals;
`ambiguous` classifications should never be auto-applied. No dedicated
monitoring window beyond normal CI/verification usage is required.

## Failure Signals and Rollback

If a future target-workspace refresh is observed to have discarded operator
customizations from a `start.ps1`/`start.sh` that this classifier previously
reported as `known-legacy`/`customized` with a `custom_sections` summary,
treat this as a regression of the fix in this shipment: halt any further
auto-refresh usage of the `tune-harness` skill's startup-script migration
path and revert to manual migration until root-caused. Rollback is to
disable/skip the startup-script contract classification step (the feature is
additive; the pre-existing generic checksum scan continues to function
independently) and redeploy the prior `main` revision if necessary.

## Releasability Evidence

`closure_status: READY`. Merge, review (local + Copilot, both clean at final
HEAD), CI, and full regression-suite evidence are complete for the code that
shipped in PR #340. The CLI runtime surface touched by this change was
identified and validated (see Runtime Verification above); no runtime
service, background job, or additional deployment surface is introduced or
altered. No outstanding follow-up conditions.

## P-020 Compaction

`compaction_status: degraded`. The mandatory `compact-context` invocation was
attempted at post-merge closure, but no installed/executable runtime skill
exists in this environment — only the repository's own authored template at
`templates/skills/compact-context/SKILL.md.tmpl` (this self-hosting repo does
not resolve `.github/skills/compact-context/SKILL.md`), consistent with the
`130-S`/`121-F` closure precedent. This session's own manual consolidation —
two compound-learning documents and one session-memory document, all written
during this same closure — constitutes the bounded, cheap Tier-1
consolidation of this shipment's fresh memory that a working `compact-context`
tool would otherwise perform. Recorded as attempted-and-degraded, non-blocking,
per P-020.

## Backlog Archival

- Feature `125-F` and its 3 tasks (`125.001-T`, `125.002-T`, `125.003-T`)
  closed via the **P-015 verified fully-covered-root cascade** path
  (`classify_shipment_close_path` confirmed eligibility): `backlogit
  shipment ship 134-S --sha afde69344d827d2b883f86f91ad5c842aab72885`
  returned `returned_ids=[]` and `archived_ids` matching exactly
  `[125.001-T, 125.002-T, 125.003-T, 125-F, 134-S]` — nothing extra.
  `parent_id: 125-F` verified preserved on all 3 archived tasks against the
  pre-close snapshot. Feature archived with `archived_status: done`; all 3
  tasks archived with `status: done`.
- Shipment `134-S` archived with `archived_status: shipped` and commit
  `afde69344d827d2b883f86f91ad5c842aab72885`.
- Predecessor `133-S` untouched throughout: verified still
  `archived_status: queued` at closure time, per dark-factory scope
  exclusion.
