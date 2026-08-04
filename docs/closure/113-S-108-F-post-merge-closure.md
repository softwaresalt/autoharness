---
shipment: 113-S
feature: 108-F
tasks: [108.001-T, 108.002-T, 108.003-T, 108.004-T]
feature_pr: 294
merge_commit: c2011114edd302968145e05bd164fc0bd3ad5f3c
merged_at: "2026-08-04T07:29:34Z"
reviewed_head: 6da2f55ba16b49404c4b813ef870ff09ddf0f34b
closure_status: READY
compaction_status: done
---

# 113-S / 108-F Post-Merge Closure — Backlogit Telemetry Evidence Mapping

Shipment `113-S` (feature `108-F`, the backlogit-only carve-out of `082-F`)
maps backlogit 1.8 telemetry evidence to the ratified
`ToolTelemetryEvent`/`ExecutionEpoch` contract (observed vs derived vs
unavailable/not_applicable), adds a structurally-separate task-level
`complexity` dimension to the event schema (non-conflated with `size`), and
documents sensitivity/redaction guardrails preventing raw-content
exfiltration. All 4 manifest tasks (`108.001-T`–`108.004-T`) executed.

## Merge Confirmation

- PR **#294** merged to `main` at `2026-08-04T07:29:34Z` with merge commit
  `c2011114edd302968145e05bd164fc0bd3ad5f3c`.
- The merge commit has **two parents**
  (`9607a13cd07617d795bcd584d8143ac6346241e6` base +
  `6da2f55ba16b49404c4b813ef870ff09ddf0f34b` feature HEAD), preserving the
  P-009 merge-commit strategy. Repo settings verified immediately before
  merge: `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false` — only "Create a merge commit" was possible.
- Merge SHA confirmed as ancestor of `origin/main`
  (`git merge-base --is-ancestor` exit 0); local `main` fast-forwarded from
  `9607a13` to `c201111`. Closure work was cut from synced `main` on branch
  `post-merge/108-f-backlogit-telemetry-evidence-mapping`.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Reviewed HEAD | `6da2f55ba16b49404c4b813ef870ff09ddf0f34b` (== PR HEAD at merge) |
| Local adversarial review (prior session) | READY, P0=0/P1=0, no unresolved findings; follow-ups: none. |
| Copilot review (round 2, prior session, HEAD progression → `6da2f55`) | 4 findings, all fixed in review-fix cycle 2. All 4 threads replied to and resolved via `gh api graphql` — re-verified resolved (4/4 `isResolved: true`) in this session immediately before merge. |
| P-018 copilot-review gate | **SATISFIED: PASS** at HEAD `6da2f55` — re-run in this session immediately before merge (`autoharness gate copilot-review 294 --repo softwaresalt/autoharness --enforcement auto --max-wait 0`). |
| §1.9 pre-merge readiness (Checks 1–5) | PASS at HEAD `6da2f55`; PR body's Local Review Readiness block matched this HEAD exactly (re-checked in this session, not assumed from prior state): outcome `READY`, P0=0/P1=0, follow-ups `none`. |
| CI (`detect code changes`, `test`, `ci gate`) | all **SUCCESS** at HEAD `6da2f55`; `mergeStateStatus: CLEAN`, `mergeable: MERGEABLE` — re-verified fresh in this session, not carried over from the prior pass. |
| Full-build applicability evidence | Full local build recorded in the PR body: `PYTHONPATH=src python -m unittest discover -s tests` — 1093 tests, OK (skipped=7); `uv run autoharness --help` smoke test passed. Targeted telemetry suite (147 tests) also passed. |
| Review-fix cycles | local: 0 additional cycles needed this session (already READY). Copilot review-comment cycles: 2/3 used (4 findings fixed in cycle 2, all resolved). Fix-CI cycles: 0/5. |
| Repo merge-strategy settings (P-009) | `allow_merge_commit: true`, `allow_squash_merge: false`, `allow_rebase_merge: false` — verified fresh via `gh api repos/softwaresalt/autoharness` immediately before merge. |
| Worktree/PR topology | single worktree (`git worktree list --porcelain` showed only the current worktree on `feat/108-f-backlogit-telemetry-evidence-mapping`), no parallel worktree violations (P-016). |

Operator merge approval was explicit and scoped to PR #294 only — recorded
as not transferring to any post-merge closure PR. This session performed
its own full defense-in-depth re-verification of every gate above from
scratch (not carried over from the prior Ship pass) immediately before
issuing `gh pr merge 294 --merge`. No admin fallback was authorized or
used; the normal merge path succeeded directly.

## Runtime Verification

**Surface**: `runtime_validation.validator_manifest` declares one surface,
`cli`, with a single required probe (`cli-help`). This shipment's scope
(docs, schema additions, telemetry event-composition module changes) does
not add new runtime/CLI surfaces beyond the pre-existing entrypoint, so the
CLI smoke probe is the applicable — and only required — baseline check.

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

No unsupported automation was fabricated.

## Backlog Reconciliation (single-artifact safe-close, P-015 / 097-S)

Safe-close used per-item / single-artifact operations only. The cascade
command `backlogit shipment ship 113-S` was **not** run.

| Item | Final state |
| --- | --- |
| 4 manifest tasks (`108.001-T`–`108.004-T`) | explicitly archived one at a time via `backlogit archive <id>` — each now carries `status: archived` with `archived_status: done` / `archived_from: .backlogit/queue/<id>.md` metadata. |
| `113-S` (shipment record) | moved to `done` then explicitly archived as a single artifact via `backlogit archive 113-S` — carries `status: archived` / `archived_status: done` / `archived_from`. |
| `108-F` (covering feature) | moved to `done` then explicitly archived via `backlogit archive 108-F` — carries `status: archived` / `archived_status: done` / `archived_from`. Confirmed via enumeration of `.backlogit/queue/108*` and `.backlogit/archive/108*` that the shipment manifest is this feature's entire task set (no other siblings in queue or archive), so terminal closure of `108-F` alongside `113-S` is within this shipment's explicit scope. |
| `082-F` (linked feature, NOT part of this shipment) | left **untouched**: `status: blocked`, queue-resident. `108-F` is a backlogit-only carve-out that `informs` `082-F` via a link, not a parent/child relationship; `082-F`'s remaining engram/graphtor-docs/agent-intercom scope is out of scope for `113-S` and was verified unchanged before and after every archival mutation in this closure. |

- Baseline gate: `git status --short -- .backlogit/` clean on the closure
  branch before any mutation; `108-F` present in `.backlogit/queue/` and no
  other tasks with `parent_id: 108-F` existed in queue or archive before
  any archival step.
- **Process note — move-vs-archive gap caught mid-procedure (fourth
  occurrence)**: this session's first pass reflexively treated the 4
  manifest tasks as "pre-archived" because their files already lived under
  `.backlogit/archive/` (relocated there by the feature branch's own
  task-loop `move --status done` commits pre-merge). Reading each file's
  `status:` field during the shipment/feature archival pre-flight surfaced
  `status: done` (not `archived`) on all 4 — the same gap recorded in
  `docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md`
  (occurrences 1–3 in `109-S`, `111-S`, `112-S`). All 4 tasks were then
  explicitly archived via `backlogit archive <id>`, verified to now carry
  `status: archived` + `archived_status: done` + `archived_from`. The
  compound doc has been updated with this fourth occurrence.
- Verify-after-each: `git status --short -- .backlogit/` checked after
  every single archival call (each of the 4 tasks, `113-S`, `108-F`) — no
  unexpected match in any pass; `082-F` (`status: blocked`, queue-resident)
  re-confirmed unchanged after every mutation.
- Closure index resync: `backlogit sync` run after all archival mutations —
  `Indexed 659 artifacts` (`CLOSURE_INDEX_SYNC_OK`).

## Context Compaction (P-020)

- **Status: `done`** (mandatory per-merge invocation; bounded Tier-1
  per-release-unit post-merge floor).
- **Memory**: wrote `docs/memory/2026-08-04-ship-113-S-108-F-session.md`,
  then compacted it to
  `docs/memory/compacted/2026-08-04-113S-108F-compacted.md` and moved the
  verbose original to
  `docs/archive/memory/2026-08-04-ship-113-S-108-F-session.md`.
- **Docs**: updated the existing compound learning
  `docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md`
  with a fourth-occurrence entry.

## Operational Closure

- **Healthy signals**:
  - PR #294 merged with a merge commit (two parents; P-009 preserved).
  - Local review READY (P0=0/P1=0, no follow-ups); Copilot review round 2
    (4 findings, all fixed, all 4 threads resolved); §1.9 and P-018 both
    PASS/SATISFIED at final HEAD, re-verified unconditionally immediately
    before merge in this session (not carried over from the prior Ship
    pass).
  - CI green at every merge gate; CLI smoke probe PASS.
  - Backlog safe-close explicitly archived all 4 manifest tasks, the
    shipment, and the covering feature individually without the forbidden
    cascade command; all now carry proper `archived_status`/`archived_from`
    metadata; `082-F` remains untouched (`status: blocked`), correctly
    preserving its own remaining non-backlogit blocked scope.
- **Failure signals to watch**:
  - The move-vs-archive gap (physically-relocated-but-not-archived tasks)
    recurred a fourth time (after `109-S`, `111-S`, `112-S`). This session
    caught it during the shipment/feature pre-flight check rather than via
    a Copilot review thread — no corruption occurred — but the recurrence
    itself reinforces the still-open follow-up (add an explicit/scripted
    pre-flight `status:` check as a hard, unconditional step in the Step 5
    Closure Tasks procedure, first recorded in the `111-S` closure).
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): monitoring — no new runtime surface
  introduced beyond the pre-existing CLI/schema; rollback = revert merge
  commit `c201111` (safe, additive schema mirror + docs, no destructive
  migration); validation window = immediate post-merge on 2026-08-04 after
  `main` synced to `c201111`; owner = Ship agent (closure evidence),
  operator (merge approval for PR #294, explicit and separately required
  for this post-merge closure PR per P-014).
  **Releasability: READY.**
- **Follow-ups**: none carried from the PR's own Local Review Readiness
  block (explicitly `none`). The open cross-shipment follow-up (stronger
  move-vs-archive pre-flight enforcement, recorded since `111-S`) remains
  outstanding and is not specific to this shipment's scope.

**Closure verdict: READY.** Merge confirmed (P-009 preserved, two-parent
commit `c201111`), local review READY + Copilot review round 2 (4/4
findings fixed, 4/4 threads resolved) + §1.9 + P-018 gates re-verified from
scratch at final HEAD `6da2f55` immediately before merge, runtime CLI probe
PASS, single-artifact safe-close complete for the shipment, the covering
feature, and all 4 manifest tasks (each explicitly archived with correct
`archived_status`/`archived_from` metadata after this session caught the
recurring move-vs-archive gap mid-procedure; no cascade corruption, no
scope leakage into `082-F`), and P-020 context compaction is recorded
`done` (see Context Compaction section above).

**Remaining approval blocker**: this post-merge closure PR requires its own
**separate, explicit operator approval** before merge (P-014 — the PR #294
approval does not carry over). No merge of the closure PR will be attempted
without it. `113-S`/`108-F` are already safe-closed and archived; the sole
outstanding item is operator sign-off on this closure PR itself.
