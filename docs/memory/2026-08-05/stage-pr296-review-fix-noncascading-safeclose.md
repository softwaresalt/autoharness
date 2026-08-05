---
type: session-memory
agent: stage
date: 2026-08-05
session_id: stage-2026-08-05-pr296-review-fix
feature: 109-F
pr: 296
reviewed_head: 28e5c3069533e73031b6b90ad23c3743e673e0f5
review_artifact: 109.006-R
checkpoint: checkpoint-20260805-032712.json (resolved)
verdict: PASS (ready for Orchestrator independent review)
---

# Stage session — PR #296 review-fix: non-cascading safe-close + phase/readiness reconciliation

Operator removed the 3-cycle review-fix limit for this session. Stage boundary
respected: only `.backlogit/**`, `docs/memory/**`, and scoped planning/review
artifacts were modified. No source/template/config mutation, no build, no
branch/worktree, no shipment claim, no commit/push, no PR/GitHub actions.
`C:\Source\GitHub\backlogit` used read-only as evidence.

## Scope

Resolve the 8 currently-unresolved Copilot review threads on PR #296 plus the
local readiness blocker (109.005-T / 109.010-T stale worktree-phase language).

## Backlogit semantics verified (read-only, C:/Source/GitHub/backlogit)

- `internal/core/shipment_lifecycle.go` **`ShipShipment`** (= `backlogit_ship_shipment`
  / `backlogit shipment ship`, HEAD `fd8d2c9`) is the **cascade**: `completeReleaseScope`
  (marks the member release-scope items `done`) + `returnUnreleasedFeatureItems`
  (each unshipped non-release descendant -> `queued` with `parent_id` cleared —
  REQUEUED and DETACHED to unparented backlog, **not** archived) + `archiveItems`
  over the release scope and — ONLY for an explicit-member covering feature — that
  feature + its terminal descendants + linked deliberations; a NON-MEMBER covering
  feature is snapshotted and restored via `restoreRolledUpNonMemberFeatures`
  (**never** archived), then the shipment is moved to `shipped` and archived.
  **P-015-forbidden** for a partial-feature shipment: for 114-S (`109-F` already a
  non-member) it would NOT archive `109-F`, but it WOULD requeue/detach the
  downstream 115-S/116-S descendant tasks (orphaning them from `109-F`) and archive
  the release-scope members outside the safe-close terminal-marker ordering.
- `internal/core/shipment.go` **`MoveShipmentStatus`** (`active->shipped`) enforces
  `isValidShipmentTransition` and mutates ONLY the shipment record, BUT it is
  **not exposed by any CLI/MCP surface** (only `ClaimShipment` queued->active and
  the cascade `ShipShipment` are wired).
- Therefore the supported **non-cascading** transition is the GENERIC
  **`backlogit move <shipment_id> --status shipped`** (`internal/cli/move.go` ->
  `handleMoveItem`/`UpdateArtifactWithGate`), which sets only the shipment
  record's `status` field (no release-scope cascade). `shipped` is a recognized
  status; the shipment has no `parent_id` children so the cascade-terminal
  children check passes trivially.
- `internal/core/archive.go` **`ArchiveItem`** stamps `archived_status = <pre-archive
  status>` (archive.go:215) and single-item archive does **not** cascade. So
  **move-to-`shipped` THEN `backlogit archive <shipment_id>`** yields
  `archived_status: shipped`. `archived_status` does not exist until the archive
  step, so the pre-archive marker to verify is the live `status: shipped`.
- Corroborated by compound docs `2026-08-02-backlogit-done-move-vs-explicit-archive.md`
  (`move --status done` relocates the file but only `archive` stamps provenance)
  and `097-S-shipment-task-only-safe-close.md` (task-only manifests, per-item
  move+archive, never `shipment ship`). No contradiction found.

## The canonical non-cascading close sequence (now encoded in the plan)

After manifest-scoped per-item closure, close the shipment record by:
1. `backlogit move <shipment_id> --status shipped` (non-cascading; shipment record only)
2. verify live `status: shipped` (re-read)
3. `backlogit archive <shipment_id>` (single artifact -> `archived_status: shipped`)
4. verify archived `archived_status: shipped`

Never `backlogit_ship_shipment` for a partial-feature shipment. The covering
feature and unshipped siblings are never moved/archived by this path.

## Thread dispositions (8 hosted + local blocker)

| Thread | Artifact | Disposition |
|---|---|---|
| PRRT_kwDORzpWpM6WhDtm | 109.016-T | FIXED — non-cascading move->verify->archive->verify |
| PRRT_kwDORzpWpM6WhUnU | 109.016-T | FIXED — ship_shipment forbidden; manifest-scoped closure kept |
| PRRT_kwDORzpWpM6WhDt0 | 109.016-T | FIXED — rescoped to canonical skill; split off 109.020-T |
| PRRT_kwDORzpWpM6WhDtt | 109.019-T | FIXED — pre-self-close merged-main reload before 114-S close |
| PRRT_kwDORzpWpM6WhDt8 | 109.017-T | Already compliant at HEAD — verified, reply only |
| PRRT_kwDORzpWpM6WhUnQ | 109.017-T | Already compliant at HEAD — verified, reply only |
| PRRT_kwDORzpWpM6WhDuD | 109.004-T | Already compliant at HEAD — verified, reply only |
| PRRT_kwDORzpWpM6WhDuO | 109-F DoD | FIXED — DoD requires non-cascading sequence |
| (local blocker) | 109.005-T, 109.010-T | FIXED — branch/worktree = pre_claim |

## A7 split (thread C)

- `109.016-T` (A7) rescoped to the **canonical** `templates/skills/shipment-reconcile/SKILL.md.tmpl`
  (+ installed `.github/skills/shipment-reconcile/SKILL.md` where present) + skill
  tests/verify surfaces. Note: this repo has only the `.tmpl` (template-only
  skill; no installed copy here).
- New `109.020-T` (A7b, size S / complexity low, depends_on 109.016-T) owns the
  **Ship agent** safe-close summary pointer in `templates/agents/_ship.agent.md.tmpl`
  + installed `.github/agents/_ship.agent.md`. Width-isolates the agent family
  from the skill family; both under 2h.
- `114-S` manifest updated **exactly once** (9 -> 10) with a traceable
  `shipment_item_added` log event naming thread PRRT_kwDORzpWpM6WhDt0.

## Manifests / dependencies (unchanged except sanctioned split)

- Task-only manifests: **114-S = 10**, 115-S = 7, 116-S = 3.
- Dependency chain 114-S -> 115-S -> 116-S intact; `109.020-T` blocks-depends-on
  `109.016-T`.
- Handoff token: **114-S**.
- Doctor: no duplicate IDs; only pre-existing unrelated `048.x` orphans.

## Evidence

- Review artifact: `109.006-R` (plan-harden + plan-review PASS).
- Checkpoint: `checkpoint-20260805-032712.json` (valid v1, **resolved** at
  2026-08-05T03:47:03Z — primary session handoff, carries `context.feature_id: 109-F`).
  The thin `checkpoint-20260805-032654.json` (also resolved, empty context) is a
  secondary marker only, not the handoff.

## Handoff to Orchestrator

Stage does not commit/push/claim/PR. Orchestrator: run an independent
current-HEAD review, then reply + resolve the 8 threads via gh API, commit and
push the backlog/planning changes. Reply bodies are provided in the session
summary (one per thread ID).
