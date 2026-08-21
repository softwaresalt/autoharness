---
title: "Ship 145-S / 137-F full-lifecycle execution and closure session"
date: 2026-08-21
shipment: 145-S
feature: 137-F
role: ship
status: complete
---

# Ship 145-S / 137-F Full-Lifecycle Session

## Summary

Executed shipment `145-S` (feature `137-F`, stash `6D62077C` + `8D570CF8`)
end-to-end: claim, executable-set derivation, test-first implementation of
four tasks, local review, feature PR #384, CI + Copilot review handling
(one P0 self-caught pre-PR, one P1 Copilot-caught round 1), merge-commit
merge, P-015 cascade close, post-merge closure PR, operational closure
artifact, and P-020 compact-context.

## Executable set derivation

Manifest: `137-F`, `137.002-T`, `137.001-T`, `137.003-T`, `137.004-T`,
`137.005-T`, `137.006-T`. `137.005-T`/`137.006-T` archived
(`[SUPERSEDED by 137.003-T]`) -> `pre_archived_skipped`, never touched.
Executable set: the four queued tasks, executed in feature-directed order
`137.002-T` -> `137.001-T` -> `137.003-T`, then order-independent
`137.004-T`.

## Task-by-task summary

* **137.002-T** (docs-only): authored
  `docs/design-docs/2026-08-20-template-dogfood-paired-edit-maintenance-contract.md`.
  Independently complete per Amendment F3; no test-file edit.
* **137.001-T** (tests-only): added `_DIVERGENT_PAIR_CAUSES` cause taxonomy
  and a fail-closed membership pin
  (`test_divergent_pair_membership_is_pinned_and_annotated`) plus a
  non-vacuous negative guard to `tests/test_scope_containment_policy_contract.py`.
  Cited the 137.002-T document by path, sole owner of that reference.
* **137.003-T** (atomic migration): migrated
  `templates/agents/_ship.agent.md.tmpl` + `.github/agents/_ship.agent.md`
  Role Boundary + post-merge Step 7, `src/autoharness/verify_workspace.py`
  marker, `tests/test_verify_workspace.py` fixtures,
  `tests/test_scope_containment_policy_contract.py` assertion,
  `tests/test_scope_containment_boundary_contract.py` comment/docstring
  corrections, and `.autoharness/harness-manifest.yaml` checksum, all in
  one commit. Preserved the P-021 C5 removal/archival distinction verbatim.
* **137.004-T** (order-independent): migrated the P-021 C5 clause in
  `templates/policies/workflow-policies.md.tmpl` and added the
  previously-missing `cli_command: "backlogit stash archive {{stash_id}}"`
  to `templates/backlog/registries/backlogit.registry.yaml`'s
  `stash_archive` mapping. Added
  `tests/test_stash_archive_registry_and_policy_migration.py` (test-first;
  confirmed red before the production edit, green after).

## Test-first evidence

Every production change in 137.003-T and 137.004-T was preceded by a
targeted test-file edit and a confirmed RED run before the corresponding
production edit, then a confirmed GREEN run after. Full targeted suite
(all four `test_scope_containment_*`/`test_verify_workspace`/new module):
**241 passed, 284 subtests**. Full local build
(`uv run python -m pytest tests/ -q`): **1677 passed, 20 skipped, 1116
subtests, 5 pre-existing failures** (confirmed `E8158860`, non-reproducing
in isolation, both before and after this shipment's changes).

## Local review + Copilot review findings

1. **P0 (self-caught, pre-PR)**: a code-review subagent pass found a stray
   corrupted line `++ .github/agents/_ship.agent.md` appended to that file
   -- an `apply_patch` tool artifact from an earlier `+++`-header mistake in
   the patch input for the 137.003-T commit. Fixed by directly stripping the
   trailing marker bytes and recomputing the manifest checksum from the
   corrected staged git blob. Re-reviewed clean before PR creation.
2. **P1 (Copilot round 1)**: Copilot correctly identified that
   `_EXPECTED_DIVERGENT_PAIR_MANIFEST_PATHS` was derived from
   `_DIVERGENT_MARKER_ONLY_PAIRS` itself, making the fail-closed membership
   assertion vacuous -- both sides would change together on any mutation of
   the tuple, so the assertion could never actually catch a silent
   inventory change. Fixed by hardcoding the expected set as an independent
   literal; verified locally (simulated shrink/expand) that the guard is
   now genuinely non-vacuous. Thread replied-to and resolved via GraphQL.

## Bookkeeping desync (see compound learning)

A `git stash`/`git stash pop` cycle, used to isolate the pre-existing
E8158860 full-suite failures from this shipment's own changes, desynced the
on-disk `.backlogit/queue/*.md` files for the shipment and its four tasks
back to their pre-claim state, even though the CLI's internal state (and
all committed deliverables) remained correct. Detected via the
`pipeline-topology --phase lifecycle` gate; repaired by re-running the
`queued -> active -> done` transitions and directly correcting the
shipment file's status field, then re-verified via the gate and a full
`backlogit sync`. See
`docs/compound/2026-08-21-backlogit-shipment-status-file-desync-after-git-stash.md`
for the full finding and repair procedure. This is a session-local process
artifact, not a defect in the shipped deliverables.

## PR lifecycle

* Feature PR #384: created, CI green (`ci gate`, `detect code changes`,
  `pipeline-topology (ambient)`, `test`), P-018 `SATISFIED` at final HEAD
  `124fcdaa`, P-009 merge-commit-only confirmed, P-014 PR body Local Review
  Readiness block present and current. Merged via `gh pr merge --merge`
  under operator standing pre-authorization (all current-head gates green,
  bounded to this shipment and its closure PR, no admin fallback).
  Merge commit `a1bce32f...`, two parents confirmed, ancestry confirmed in
  `origin/main`.
* P-015 close path: `classify_shipment_close_path` -> `CASCADE` (137-F
  verified fully-covered root). `backlogit shipment ship 145-S --sha
  a1bce32f...` executed; `archived_ids` exact match, `returned_ids: []`,
  `parent_id` preserved throughout, pre-archived members untouched.
* Post-merge closure branch `post-merge/145-s-harness-consistency-stash-archive-migration`
  created from synced `main`; closure artifact
  `docs/closure/145-S-137-F-post-merge-closure.md` authored; closure PR to
  follow this session's write-up.

## Follow-ups (not actioned by Ship, Stage-owned)

* P-021 deferred entries `E8158860`, `F73BA065`, `90F2A9F8`, `8FA8FC22`
  (pre-existing, unrelated) remain open.
* A new deferred entry captured by Stage during the `6D62077C` spike itself
  (finding F5: `_derive_template_variables` coverage gap) remains open;
  out of scope per the spike and this shipment's manifest.

## Ship role-boundary compliance

No backlog item, shipment, plan, deliberation, or review artifact was
created outside the executed tasks' scope. No triage, prioritization,
re-classification, or discretionary stash removal/archival was performed.
No direct commit to `main`; all work landed via `chore/145-s-*` and
`post-merge/145-s-*` branches and reviewed PRs. Both source stashes
(`6D62077C`, `8D570CF8`) were already retired by Stage before this session
began -- confirmed absent via `backlogit stash get`, no action taken or
required.
