---
shipment: 158-S
feature: 150-F
tasks:
    - 150.001-T
    - 150.002-T
    - 150.003-T
    - 150.004-T
    - 150.005-T
    - 150.006-T
    - 150.007-T
    - 150.008-T
    - 150.009-T
    - 150.010-T
feature_pr: 423
additional_prs:
    - 425
    - 426
closure_pr: 427
merge_commit: 8b79de94e6705f4e950257073b263369a7e258a7
merged_at: "2026-08-30T10:29:32Z"
reviewed_head: 4353a7484458aeca04055d3ef5126eccb7a661b8
closure_merge_commit: 2661c1c82f82a22224c2f7df9309fe17f0745cf6
closure_reviewed_head: 9fbf3982040279ca269e3c510e02804064007a82
closure_status: READY
compaction_status: done
---

# 158-S / 150-F Post-Merge Closure -- v1.5.0 Release Preparation and Publish

Canonical machine-readable post-merge closure record for shipment `158-S`
(feature `150-F`, 10 tasks). This file exists solely to satisfy the
`docs/closure/{shipment_id}-*-post-merge-closure.md` discovery contract
used by `autoharness gate pipeline-topology`'s `closure_complete()` reader
(`src/autoharness/gates/topology.py`); the full release narrative already
exists in the authoritative evidence documents cited below and is
intentionally not duplicated here.

This artifact is itself a repair: `158-S` was already merged, safe-closed
(cascade path: `150-F` archived `done`, `158-S` archived `shipped`,
`commit: 8b79de94e6705f4e950257073b263369a7e258a7`), and its own post-merge
closure PR (#427) already merged before this file was authored. The gap was
that none of `158-S`'s closure documents were ever written under the
`{shipment_id}-*-post-merge-closure.md` filename shape the gate's discovery
glob requires, so `closure_complete('158-S')` returned `None` (no matching
file found) rather than `True`, which in turn blocked
`159-S`'s `pipeline-topology --phase pre_claim` readiness check with
`PREDECESSOR_CLOSURE_INCOMPLETE`. No release work is redone or re-verified
here; every fact below is drawn from already-existing, already-merged
evidence.

## Merge Confirmation

- Feature PR #423 (`chore(158-S): v1.5.0 release preparation and publish`)
  merged to `main` with merge commit `8b79de94e6705f4e950257073b263369a7e258a7`
  (parents `964f7aeaa5b6accfd9bee235aa11b561f43ad794` and
  `4353a7484458aeca04055d3ef5126eccb7a661b8` -- two parents, P-009
  merge-commit strategy preserved).
- Two additional post-merge follow-up PRs also merged to `main` before
  closure: #425 (`fix: clear ambient GITHUB_HEAD_REF before
  patched_environ() in topology tests`, merge commit
  `8922b62e4c548daaa0dc0c1c56be2c8817862af9`) -- an emergent finding
  outside `158-S`'s original manifest scope, captured as P-021 stash
  entry `E738A7D1` for Stage's retrospective review (see Stash
  Disposition below) -- and #426 (`fix: pin core-metadata-version to
  2.4 to fix v1.5.0 PyPI publish failure`, an in-scope publish-compatibility
  fix, merge commit `ca3232a8969b321f085eb4958d5e2f8f47259d2c`).
- Post-merge closure PR #427 (`chore: post-merge closure for 150-F -- v1.5.0
  release preparation and publish`) merged with merge commit
  `2661c1c82f82a22224c2f7df9309fe17f0745cf6` (parents
  `ca3232a8969b321f085eb4958d5e2f8f47259d2c` and
  `9fbf3982040279ca269e3c510e02804064007a82`).
- All four merge commits confirmed present on `origin/main` via
  `git merge-base --is-ancestor <sha> origin/main` (exit 0 for each).

## Authoritative Evidence (referenced, not duplicated)

- `docs/closure/2026-08-30-v1_5_0-release-preparation-and-publish-closure.md`
  -- the canonical operational-closure narrative: CI status across PRs
  #423/#425/#426, risky-action record (PA-1..PA-6), affected runtime
  surfaces, deployment/release path, pre-deploy audits, post-deploy checks,
  healthy/failure signals, monitoring plan, rollback trigger/procedure,
  validation window, and owner. Final releasability verdict recorded there:
  **READY** -- v1.5.0 published to PyPI, GitHub Release live, main
  confirmed green after all three merges, no open conditions.
- `docs/closure/2026-08-30-v1_5_0-release-preparation-runtime-verification.md`
  -- runtime validator evidence for the `cli` surface (source tree,
  isolated packaged-wheel install, and the published PyPI package).
  Verdict: **PASS**.
- `docs/closure/2026-08-30-v1_5_0-release-monitoring-and-publish-evidence.md`
  -- full monitoring signal log for both the rolled-back first tag attempt
  (safe, no version burned, confirmed via PyPI 404 probe) and the
  successful second attempt, published-package smoke evidence, and the
  PyPI/GitHub Release URLs.
- `docs/memory/compacted/2026-08-30-158-s-compacted.md` -- compacted P-020
  session memory: outcome, merge sequence, key learnings, executed
  rollback, and Stage follow-ups (verbose original archived under
  `docs/archive/memory/2026-08-30/`).

## Backlog Reconciliation (P-015)

`158-S` was safe-closed via the verified P-015 fully-covered-root cascade
exception: `150-F` (root feature) fully covered by all 10 manifest-member
task children, nothing beyond the qualifying root and its children in the
manifest. Archived state confirmed live in
`.backlogit/archive/158-S.md` (`archived_status: shipped`,
`commit: 8b79de94e6705f4e950257073b263369a7e258a7`) and
`.backlogit/archive/150-F.md` (`archived_status: done`).

## Stash Disposition (P-021)

One emergent finding outside `158-S`'s original scope (the
`GITHUB_HEAD_REF` push-context test fix underlying PR #425) was captured as
P-021 stash entry `E738A7D1` for Stage's retrospective review, per the
compacted memory above. It does not block this release's releasability
status.

## Compaction (P-020)

`compaction_status: done` -- `compact-context --target all` was invoked at
`158-S`'s original post-merge closure; the just-closed release unit's
session memory was compacted into
`docs/memory/compacted/2026-08-30-158-s-compacted.md`, with the verbose
original archived under `docs/archive/memory/2026-08-30/`.

## Releasability Evidence

**Closure verdict: READY.** Per
`docs/closure/2026-08-30-v1_5_0-release-preparation-and-publish-closure.md`'s
own recorded releasability evidence: `autoharness` v1.5.0 is published to
PyPI, the GitHub Release is live, the published-package smoke test passed,
and `main` was confirmed green after all three merges (#423, #425, #426).
No conditions remain outstanding for `158-S`/`150-F`. This file supplies no
new evidence beyond what is already recorded in the documents cited above;
it exists only to make that already-complete closure mechanically
discoverable by `autoharness gate pipeline-topology`'s predecessor-closure
readiness check ahead of `159-S`.
