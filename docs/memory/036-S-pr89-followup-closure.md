# Session Memory — Shipment 036-S: PR #89 Follow-up Closure

**Shipment**: 036-S  
**Title**: PR #89 follow-up: reconcile 035-S post-merge closure artifacts  
**PR**: #91 (`chore/036-S-pr89-copilot-followup` → `main`)  
**Merge SHA**: `77fd377e7eb2390c05c0a7916e92ea9c5cb3fefa`  
**Merged At**: 2026-05-18T04:53:38Z  
**Status**: Shipped and archived

---

## Summary

Shipment 036-S resolved three unresolved Copilot review threads from PR #89
(`chore(backlog): post-merge closure for 035-S`). All three defects were
documentation/backlog-hygiene issues — no schema changes, no template changes,
no CLI changes.

All tasks 040.001-T through 040.003-T were delivered. Shipment 036-S is now
shipped.

---

## Scope

| Task | Title | Status |
|------|-------|--------|
| 040.001-T | Fix session-memory summary: reconcile task list in docs/memory/035-S-release-1.4.3.md | Done |
| 040.002-T | Fix archived shipment record: add archived_from and set correct status in .backlogit/archive/035-S.md | Done |
| 040.003-T | Remove stale queue copy: delete .backlogit/queue/035-S.md | Done |

Parent feature: **040-F** (`chore(backlog): PR #89 follow-up — reconcile 035-S post-merge closure artifacts`)

---

## Key Changes Delivered (in PR #91)

1. **`docs/memory/035-S-release-1.4.3.md`** — Extended summary paragraph to
   include `039.007-T` and state "seven tasks total". Previously read "039.001-T
   through 039.006-T" (omitting the late-added seventh task).

2. **`.backlogit/archive/035-S.md`** — Added `archived_from` provenance field;
   corrected `commit:` to align with the actual v1.4.3 merge SHA
   (`38a6c77c0fa682fea640794f253d9d26c10a5b80`) rather than the post-merge
   closure PR merge SHA; kept `status: shipped` (not `archived` — shipments
   only allow queued/active/shipped/abandoned per schema).

3. **`.backlogit/queue/035-S.md`** — Deleted stale queue copy; archive is now
   the sole canonical record for 035-S.

---

## Copilot Review Gate

- PR #91 received two Copilot reviews.
- Both review threads were resolved before merge (`isResolved: true`).
- §1.9 Pre-Merge Readiness Verification passed at HEAD `f89bed548ce500e1ee69120b2e28beeeeb3dcd97`.
- `current_user_can_bypass: pull_requests_only` (ruleset `PR-Required`, id 14577755).
- Merged via admin bypass (operator-explicit approval; `REVIEW_REQUIRED` state
  due to no APPROVED review — all reviews were COMMENTED).

---

## Compound Learnings

### L1: Copilot COMMENTED ≠ APPROVED — Ruleset bypass required

A Copilot review with `state: COMMENTED` does not satisfy `required_approving_review_count: 1`.
Even when all Copilot threads are resolved and the §1.9 gate passes, the
`reviewDecision` remains `REVIEW_REQUIRED`. Admin bypass (available when
`current_user_can_bypass: pull_requests_only`) is the correct path when the
operator has explicitly approved the merge.

### L2: archive/035-S.md status should remain `shipped`, not `archived`

The backlogit header-def schema for shipments only allows:
`queued | active | shipped | abandoned`. Using `status: archived` in an archive
file violates the schema even though the file lives in `.backlogit/archive/`.
The archive *location* plus the `archived_from` field are the canonical signals
of archival; the `status` field should reflect the last valid lifecycle state
(`shipped`).

### L3: Post-merge closure can span two sessions when sequencing conflicts arise

When a second PR is already open (PR #92 / 037-S) and the operator must resolve
PR #91 first, the Ship agent should:
1. Merge the blocking PR first (with explicit operator approval).
2. Create a separate closure branch off the freshly updated `origin/main`.
3. Stash tracked modifications from the current branch to allow clean branch
   switch; untracked files follow the worktree automatically.
4. Present the closure PR separately from the already-open PR.

---

## Backlog Closure

- 036-S: archived at commit `77fd377e7eb2390c05c0a7916e92ea9c5cb3fefa`
- 040-F: archived
- 040.001-T, 040.002-T, 040.003-T: archived
