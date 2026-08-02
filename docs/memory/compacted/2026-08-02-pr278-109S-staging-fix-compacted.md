---
type: compacted-memory
compacted_at: 2026-08-02
source: docs/archive/memory/2026-08-01-stage-dark-factory-staging.md
pr: 278
shipment: 109-S
feature: 105-F
reviewed_head: 620fec664f42d0ebdaade2219284d5792b22e509
merge_commit: 7f301d202e00374a81f621bd68c8aaeadc7c4c79
status: closed
tags: [ship, dark-mode, copilot-review, backlog-integrity, closure]
---

# Compacted Memory — PR #278 Copilot-review remediation → merge (109-S staging, not executed)

**Scope**: Ship dark-mode invocation bounded to PR #278 / `chore/stage-109-S` /
shipment `109-S` staging artifacts only. This session did NOT claim or execute
`109-S` — the shipment remains `queued` on `main` for the next serial Ship
handoff. What merged was Stage's staging PR itself, corrected per Copilot
review feedback.

## What happened

- Stage's staging PR #278 ("chore: stage serial dark pipeline") had 3
  unresolved Copilot review threads at HEAD `9bc594e`:
  1. `109-S`'s manifest `custom_fields.items` wrongly included the covering
     feature `105-F` alongside its two tasks — shipment membership must be
     task-only, with feature derivation via each task's `parent_id`.
  2. The `shipment-record-status` classification matrix drafted in task
     `105.002-T` (for future `shipment-reconcile` work) was not mutually
     exclusive: `record-queued-with-active-work` was worded to also match a
     `blocked` record, overlapping with `record-blocked-with-done-work` for
     the blocked+done case, and blocked+active had no explicit classification.
  3. The implementation plan mirrored the same ambiguous matrix.
- Fix: removed `105-F` from `109-S`'s manifest items (synced the same
  membership fact in the handoff checkpoint's `shipment_items` field and the
  Stage memory doc's "Items:" line — both repeated the pre-fix membership
  list); split the classification matrix into 4 mutually-exclusive cases,
  scoping `record-queued-with-active-work` to `queued`-only and splitting the
  blocked case into `record-blocked-with-active-work` /
  `record-blocked-with-done-work` with an explicit precedence rule (active
  takes precedence over done when a blocked record has both). Mirrored
  identically in the task, the feature's acceptance criteria, and the plan.
  Left the append-only `.backlogit/logs/109-S.jsonl` shipment_created event
  untouched (historical audit record of what literally happened, not a
  restatement of current truth).
- Validated: YAML/JSON frontmatter for all changed files, `backlogit sync` +
  `shipment get 109-S` confirmed the corrected task-only manifest with
  `covering_feature: 105-F` still resolving via `parent_id`, doctor findings
  confirmed pre-existing/unrelated. Full local build recorded
  not-applicable (docs/backlog-only fix, no source/template/schema files
  touched).
- Committed `620fec6` with required Copilot trailers, pushed, replied to all
  3 review comments individually with commit SHA + exact fix, resolved all 3
  threads via GraphQL only after replying. Verified via GraphQL that exactly
  3 threads existed and all were resolved (no drift, no phantom threads).
- `autoharness gate copilot-review 278 --enforcement auto --max-wait 900`
  returned `SATISFIED: PASS` after a fresh non-pending Copilot review landed
  at HEAD `620fec6` with zero new comments. Re-ran the same gate
  unconditionally immediately before merge (HEAD unchanged) — still PASS.
- Repo settings confirmed merge-commit-only (`allow_merge_commit: true`,
  squash/rebase both `false`) — no P-009 ambiguity. `main` had no branch
  protection rule requiring review, so the normal `gh pr merge --merge`
  succeeded directly; **no admin fallback was needed** despite being
  pre-authorized for this turn.
- Merge commit `7f301d2` confirmed two parents; merge-base ancestor check
  against `origin/main` passed. Updated PR body's Local Review Readiness
  block to the final HEAD before merge, per P-014.

## Key learnings (durable)

1. **The backlogit CLI's `shipment get`/`queue view` can read a stale index**
   after a direct file edit — `backlogit sync` must run before trusting CLI
   output as evidence that a manifest fix took effect. Observed here: editing
   `109-S.md`'s `items` array directly did not change `shipment get`'s JSON
   output until `backlogit sync` re-indexed.
2. **A "mutually exclusive" classification fix must partition by the record's
   own status first, then add an explicit precedence rule for any state that
   can co-occur with more than one task-state signal** (here: a `blocked`
   record with both an `active` and a `done` task). Simply adding a new
   category without removing the overlap from the old one reintroduces
   ambiguity.
3. **Not every artifact that repeats a fact is a sync target.** Append-only
   event logs (`.backlogit/logs/*.jsonl`) recording what literally happened
   at a point in time are historical audit trail, not current-state
   assertions — they should not be rewritten when a later fix corrects the
   state they recorded. Checkpoints and memory docs describing *current*
   handoff state are sync targets; timestamped event logs are not.
4. **Branch protection absence changes the merge path, not the gate
   discipline.** With no branch-protection rule on `main`, the normal merge
   succeeded without needing the pre-authorized admin fallback — but every
   gate (P-009 strategy check, P-014 readiness, P-018 unconditional
   pre-merge re-check) still ran in full before attempting it.

## Follow-ups

None blocking. Shipment `109-S` remains `queued` on `main`, task-only
manifest confirmed present at the merge commit, ready for the next serial
Ship handoff to claim and execute `105.002-T` → `105.001-T`. No new
backlog/stash items created (Ship role boundary, P-010).

**Verbose original**: `docs/archive/memory/2026-08-01-stage-dark-factory-staging.md`.
