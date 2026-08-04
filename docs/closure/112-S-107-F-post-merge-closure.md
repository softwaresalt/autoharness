---
shipment: 112-S
feature: 107-F
tasks: [107.001-T, 107.002-T, 107.003-T, 107.004-T, 107.005-T]
feature_pr: 292
merge_commit: 5311a3127e247e11a9ab25b1bfc0bd4095393a77
merged_at: "2026-08-04T01:06:14Z"
reviewed_head: a8f96576e8939759948dc388de5fd2a0a6e3096a
closure_status: READY
compaction_status: done
---

# 112-S / 107-F Post-Merge Closure — Size+Complexity First-Class in Staging

Shipment `112-S` (feature `107-F`) makes task-level `size` (implementation
volume/effort) and `complexity` (implementation difficulty/uncertainty)
first-class, validated, non-conflated planning metadata across the Stage
decomposition workflow: native `complexity` enum enabled in
`.backlogit/header-def.yaml`, `docs/size-complexity-reference.md` adopting
backlogit's released non-conflation semantics verbatim, the harvest skill
and `_stage` agent template (plus its installed dogfood copy) mandating
both axes at task-creation time with fail-closed enum validation and a
P-003 granularity gate extended to both axes independently, and a reviewer
validation checklist. Docs/templates/backlogit-config only — no `src/`
source code, schema, or CLI change shipped. All 5 manifest tasks
(`107.001-T`–`107.005-T`) executed in dependency order.

## Merge Confirmation

- PR **#292** merged to `main` at `2026-08-04T01:06:14Z` with merge commit
  `5311a3127e247e11a9ab25b1bfc0bd4095393a77`.
- The merge commit has **two parents**
  (`439b8d574cf5c12ca3226e5a463bfae6dcc612b2` base +
  `a8f96576e8939759948dc388de5fd2a0a6e3096a` feature HEAD), preserving the
  P-009 merge-commit strategy. Repo settings verified immediately before
  merge: `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false` — only "Create a merge commit" was possible.
- Merge SHA confirmed as ancestor of `origin/main`
  (`git merge-base --is-ancestor` exit 0); local `main` fast-forwarded from
  `439b8d5` to `5311a31`. Closure work was cut from synced `main` on branch
  `post-merge/107-f-size-complexity-staging`.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Reviewed HEAD | `a8f96576e8939759948dc388de5fd2a0a6e3096a` (== PR HEAD at merge) |
| Local adversarial review (prior session) | READY, P0=0/P1=0, no unresolved findings; follow-ups: none. |
| Copilot review (3 rounds, prior sessions, HEAD progression 9959331 → 64b19d9 → 1486c5b → a8f9657) | 8 findings total across 3 rounds, all fixed; round 3 corrected backlogit 1.8.0's actual create/update call sequencing for size+complexity, verified against backlogit source. All 8 threads across 3 rounds replied to and resolved via `gh api graphql` (re-verified resolved in this session immediately before merge). Review-fix cycle limit (3) reached with no new findings in round 3. |
| P-018 copilot-review gate | **SATISFIED: PASS** at HEAD `a8f96576` — re-run in this session immediately before merge. 0 unresolved Copilot threads (verified via GraphQL: 8/8 `isResolved: true`). |
| §1.9 pre-merge readiness (Checks 1–5) | PASS at HEAD `a8f96576`; PR body's Local Review Readiness block matched this HEAD exactly (re-checked in this session, not assumed from prior state). |
| CI (`detect code changes`, `test`, `ci gate`) | all **SUCCESS** at HEAD `a8f96576`; `mergeStateStatus: CLEAN`, `mergeable: MERGEABLE` — re-verified fresh in this session, not carried over from the prior pass. |
| Full-build applicability evidence | Not applicable (docs/templates/backlogit-config-only; no `src/` touched). Verified instead via `PYTHONPATH=src python -m unittest discover -s tests` (1065 passed, 7 skipped, 0 failed) and `autoharness verify-workspace` (`checksum_scan: .github/agents/_stage.agent.md status=unchanged, blockers=[]`), per the PR body's own Local Review Readiness block. |
| Review-fix cycles | local: 0 additional cycles needed this session (already READY). Copilot review-comment cycles: 3/3 (limit reached, no new findings, all resolved). Fix-CI cycles: 0/5. |
| Repo merge-strategy settings (P-009) | `allow_merge_commit: true`, `allow_squash_merge: false`, `allow_rebase_merge: false` — verified fresh via `gh api repos/softwaresalt/autoharness` immediately before merge. |
| Worktree/PR topology | single worktree (`git worktree list --porcelain` showed only the current worktree on `feat/107-f-size-complexity-staging`), no parallel worktree violations (P-016). |

Operator merge approval was explicit and scoped to PR #292 only — recorded
as not transferring to any post-merge closure PR. This session performed
its own full defense-in-depth re-verification of every gate above from
scratch (not carried over from the prior Ship pass) immediately before
issuing `gh pr merge 292 --merge`. No admin fallback was authorized or
used; the normal merge path succeeded directly.

## Runtime Verification

**Surface**: `runtime_validation.validator_manifest` declares one surface,
`cli`, with a single required probe (`cli-help`). This shipment touched no
CLI/runtime code path (docs, templates, `.backlogit/header-def.yaml`,
`schemas/backlog-tool-registry.schema.json` config-shape addition only), so
the CLI smoke probe is the applicable — and only required — baseline check.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | CLI (command) |
| Runtime probe | `uv run autoharness --help` (probe `cli-help`, required) |
| Result | **PASS** — exit 0, CLI help printed, re-run post-merge on the closure branch cut from synced `main` |
| Preserve-invariant | "The autoharness CLI starts without import, packaging, or option-parsing failures" — HELD |
| Manual checkpoints | none defined |
| Blocked prerequisites | none |
| Release blocker (`The CLI help smoke check fails`) | NOT triggered |
| Verdict | **PASS** (meets `minimum_verdict: PASS`; `surfaces_expected: [cli]`) |

No unsupported automation was fabricated. This shipment's own scope
(planning-metadata semantics, docs, template mandates) has no runtime
surface beyond the pre-existing CLI, which the probe above covers.

## Backlog Reconciliation (single-artifact safe-close, P-015 / 097-S)

Safe-close used per-item / single-artifact operations only. The cascade
command `backlogit shipment ship 112-S` was **not** run.

| Item | Final state |
| --- | --- |
| 5 manifest tasks (`107.001-T`–`107.005-T`) | explicitly archived one at a time via `backlogit archive <id>` — each now carries `status: archived` with `archived_status: done` / `archived_from: .backlogit/queue/<id>.md` metadata. |
| `112-S` (shipment record) | moved to `done` then explicitly archived as a single artifact via `backlogit archive 112-S` — carries `status: archived` / `archived_status: done` / `archived_from`. |
| `107-F` (covering feature) | moved to `done` then explicitly archived via `backlogit archive 107-F` — carries `status: archived` / `archived_status: done` / `archived_from`. Confirmed via enumeration of `.backlogit/queue/107*` and `.backlogit/archive/107*` that the shipment manifest is this feature's entire task set (no other siblings in queue or archive), so terminal closure of `107-F` alongside `112-S` is within this shipment's explicit scope. |

- Baseline gate: `git status --short -- .backlogit/` clean on the closure
  branch before any mutation; `107-F` present in `.backlogit/queue/` and the
  5 manifest tasks confirmed absent from `.backlogit/queue/107.*` (no
  residual siblings) before any archival step.
- **Process note — move-vs-archive gap caught proactively (third
  occurrence)**: this session found, before skipping any item as
  "pre-archived", that all 5 manifest tasks had already been physically
  relocated to `.backlogit/archive/` by the feature branch's own task-loop
  commits (`move --status done` side effect), but their `status` field
  still read `done` — not `archived`, and no `archived_status`/
  `archived_from` metadata was present. Per
  `docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md`
  (first surfaced in `110-S`, recurred in `111-S`), physical file location
  under `archive/` is never evidence of the explicit archive transition.
  This session ran the documented pre-flight check
  (`Select-String -Pattern "^status:"` against each candidate file) before
  treating any of the 5 tasks as already closed, found all 5 still `done`,
  and explicitly archived each one. The compound doc has been updated with
  this third occurrence and confirmation that the pre-flight check
  prevents the recurrence when actually applied.
- Verify-after-each: `git status --short -- .backlogit/` (filtered for
  `113` and `108`) checked after every single archival call (each of the 5
  tasks, `112-S`, `107-F`) — no match in any pass, confirming `113-S` and
  `108-F` were never touched. A final full `git status --short -- .backlogit/`
  confirmed only `107-F`, `112-S`, and the 5 manifest tasks' files (plus
  their logs) changed.
- Closure index resync: `backlogit sync` run after all archival mutations —
  `Indexed 659 artifacts` (`CLOSURE_INDEX_SYNC_OK`).

## Context Compaction (P-020)

- **Status: `done`** (mandatory per-merge invocation; bounded Tier-1
  per-release-unit post-merge floor).
- **Memory**: wrote
  `docs/memory/2026-08-03-ship-112-S-107-F-session.md`, then compacted it
  to `docs/memory/compacted/2026-08-03-112S-107F-compacted.md` and moved the
  verbose original to `docs/archive/memory/2026-08-03-ship-112-S-107-F-session.md`.
- **Docs**: updated the existing compound learning
  `docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md`
  with a third-occurrence entry confirming the documented pre-flight check
  (grep/read the `status` field before treating any archive-folder file as
  already closed) is effective when actually applied.

## Operational Closure

- **Healthy signals**:
  - PR #292 merged with a merge commit (two parents; P-009 preserved).
  - Local review READY (P0=0/P1=0, no follow-ups); 3 rounds of Copilot
    review, all 8 findings fixed and all 8 threads resolved; §1.9 and P-018
    both PASS/SATISFIED at final HEAD, re-verified unconditionally
    immediately before merge in this session (not carried over from the
    prior Ship pass).
  - CI green at every merge gate; CLI smoke probe PASS.
  - Backlog safe-close explicitly archived all 5 manifest tasks, the
    shipment, and the covering feature individually without the forbidden
    cascade command; all now carry proper `archived_status`/`archived_from`
    metadata; `113-S` and `108-F` remain untouched (`status: queued`),
    correctly blocked pending this closure.
- **Failure signals to watch**:
  - The move-vs-archive gap (physically-relocated-but-not-archived tasks)
    recurred a third time (after `110-S`, `111-S`). This session caught it
    proactively via the documented pre-flight status check before any skip
    decision, so no corruption occurred and no Copilot review thread was
    needed to catch it this time — but the recurrence itself confirms the
    compound-doc reminder alone is still insufficient without an
    enforced/scripted pre-flight step; see the `111-S` closure's recorded
    follow-up (add an explicit pre-flight `backlogit get <id>` status check
    as a hard step in the Step 5 Closure Tasks procedure) — still open.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): monitoring — the change is
  docs/templates/backlogit-config only (no `src/` source, no shipped CLI
  behavior, no schema/data migration beyond an additive registry field);
  rollback = revert merge commit `5311a31` (safe, no migration in either
  direction); validation window = immediate post-merge on 2026-08-04 after
  `main` synced to `5311a31`; owner = Ship agent (closure evidence),
  operator (merge approval for PR #292, explicit and separately required
  for this post-merge closure PR per P-014).
  **Releasability: READY.**
- **Follow-ups**: none carried from the PR's own Local Review Readiness
  block (explicitly `none`). The open cross-shipment follow-up (stronger
  move-vs-archive pre-flight enforcement, recorded in the `111-S` closure)
  remains outstanding and is not specific to this shipment's scope.

**Closure verdict: READY.** Merge confirmed (P-009 preserved, two-parent
commit `5311a31`), local review READY + 3 rounds of Copilot review (8/8
findings fixed, 8/8 threads resolved) + §1.9 + P-018 gates re-verified from
scratch at final HEAD `a8f96576` immediately before merge, runtime CLI
probe PASS, single-artifact safe-close complete for the shipment, the
covering feature, and all 5 manifest tasks (each explicitly archived with
correct `archived_status`/`archived_from` metadata after this session
proactively caught the recurring move-vs-archive gap via the documented
pre-flight check; no cascade corruption, no scope leakage into `113-S` or
`108-F`), and P-020 context compaction is recorded `done` (see Context
Compaction section above).

**Remaining approval blocker**: this post-merge closure PR requires its own
**separate, explicit operator approval** before merge (P-014 — the PR #292
approval does not carry over). No merge of the closure PR will be attempted
without it. `113-S` remains blocked/unclaimed pending this closure PR's
merge.
