---
title: "Stage session 2026-08-24 - three-bug resolution (5CFA8198 / B57F9E24 / 84D8E6AB)"
date: 2026-08-24
source: "docs/memory/2026-08-24-stage-three-bug-resolution.md"
doc_type: "memory"
agent: stage
session_id: stage-2026-08-24-three-bug-resolution
route: claude-opus-5 / anthropic / high
dark_mode: INACTIVE
---

# Stage session - 2026-08-24

Scope: exactly three active stash bug IDs - `5CFA8198`, `B57F9E24`, `84D8E6AB`.

`DARK_MODE_ACTIVE` **INACTIVE** (no P-017 activation phrase given). Normal
sequential pipeline. No merge approval, no admin authority, no admin fallback.

## Capability status

| Gate | Result |
|---|---|
| Step 0.0 tool availability | `ALL_TOOLS_OK` - backlogit MCP + CLI 1.10.1 (`b0772938`) |
| Step 0.1 index sync | `INDEX_SYNC_OK` (958 indexed) |
| Step 0.1b engram | `ENGRAM_OK` - external backlogit workspace bound (640 files, 4489 edges, 100% embedding coverage) |
| Step 0.1c intercom | `INTERCOM_DEGRADED` - pack installed, no tool surface in runtime. Operator visibility reduced; only safe non-destructive work performed |
| Crash recovery | Zero active `stage` candidates (1 resolved checkpoint, 0 quarantined). Normal startup |

## Dispositions

### 5CFA8198 - RESOLVED INTO WORK (stays ACTIVE by its own contract)

`DEFERRED SCOPE EXPANSION` marker forced the deliberate route (P-021 C6).
Deliberation `027-DL` created before any planning.

Deliberated -> planned -> hardened -> reviewed -> harvested -> shipped-assembly:

* `027-DL` - Option C (two-set allowed/required gate) selected over A (subset
  only - would let a no-op cascade pass), B (re-archive to satisfy the checker -
  fights the engine to preserve a false claim), D (directory location - rebuilds
  the original defect).
* Plan `docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-plan.md`
* Hardening (P-006, required and performed) - amendments A1-A4 BINDING, applied
  in place.
* Review `docs/reviews/2026-08-24-cascade-close-archived-ids-postcondition-review.md`
  - **PASS**, cycle 1 of 3. Three MINOR findings, all addressed.
* Feature `147-F`; tasks `147.001-T` .. `147.004-T`; shipment `155-S` (queued).

**NOT archived** - work contract item 5 says archive only after the corrections
have shipped. Ship has not executed `155-S`.

**Key evidence upgrade**: the corrected diagnosis was verified against backlogit
ENGINE SOURCE, not by re-running the behavioral spike the entry names as a
non-goal. `internal/core/shipment_lifecycle.go` `archiveItems()` L1130 skips a
truly `status: archived` item AND does not append it to the slice that becomes
`ArchivedIDs` (L670, L709); same exclusion at L799/L808. So `archived_ids` is a
TRANSITION LOG, not a manifest echo. Corroborated by 154-S / 153-S logs.

The 2026-08-18 spike built its "pre-archived" arms with `move --status done`,
which leaves declared `status: done`; against the L1130 guard `done != archived`,
so all three arms were the control arm at the guard that mattered.

### B57F9E24 - STILL OPEN (ACTIVE, high) - upstream linkage added

Upstream HEAD unchanged at `b0772938` (no intervening commits), so no fix could
have landed. Re-read directly: `internal/events/memory.go:69` still discards the
unmarshal error and falls through to the unguarded verbatim write at `:112`. No
truncated-V1 regression test exists.

New this session: the defect is now tracked in the owning repo as backlogit
stash **`3A33E404`** (verified present and active, read-only). Entry updated with
that linkage. No local implementation work fabricated; NOT combined into `155-S`.

### 84D8E6AB - RESOLVED, VERIFIED, ARCHIVED

Both recorded preconditions met: upstream `143-F` (raised from this very entry -
its `custom_fields` name `84D8E6AB`) and `144-F` are archived/done, and the
installed binary (`b0772938`, 2026-08-22) post-dates both.

Ordering verified EMPIRICALLY as the deferred note required:

| Shipment | Sequence | Intermediate `shipped` |
|---|---|---|
| 114-S (2026-08-05, pre-fix) | active -> archived | **ABSENT** |
| 153-S (2026-08-22, post-fix) | active -> shipped -> archived | PRESENT |
| 154-S (2026-08-23, post-fix) | active -> shipped -> archived | PRESENT |

Disposition appended; tracker archived via `backlogit stash archive`
(non-destructive). No synthetic log entry authored - the historical 114-S gap is
permanent and correctly left alone.

## Duplicate scan (P-021 C5, unconditional)

Run over all 11 active entries. **CLEAN.** Nearest neighbour to `5CFA8198` is
archived feature `132-F` / `132.001-T`, which INSTALLED the now-falsified
invariant - predecessor, not duplicate. Late-identifier reconciliation NOT
triggered (no `N/A` source ref on `5CFA8198`).

## External workspace preservation

`C:\Source\GitHub\backlogit` inspected READ-ONLY throughout (git log, file reads,
grep, engram CLI, backlogit read-only queries). No write, build, test run,
branch, or backlog/stash mutation. Its pre-existing dirty state left exactly as
found.

## Next steps (Ship)

**PARTLY SUPERSEDED 2026-08-24** - see "Post-handoff corrections" below.
`155-S` is NOT claimable yet; a Ship-owned predecessor-closure evidence repair
for `154-S` must land first.

Claim `155-S`. Execute `147.001-T -> 147.002-T -> 147.003-T -> 147.004-T` in
dependency order. After merge, archive stash `5CFA8198`.

Stage did NOT stage, commit, branch, push, build, or create a PR.

## Post-handoff corrections (narrow Stage follow-up, 2026-08-24)

A follow-up Stage session (planning/backlog scope only; normal non-dark mode)
corrected two post-handoff findings. No source, template, schema, or CLI file
was touched; no git commit, branch, push, build, test run, or PR.

### 1. `027-DL` archived (deliberation lifecycle)

`027-DL` was fully deliberated (all four sections complete) and harvested into
`147-F` / `147.001-T`-`147.004-T` / `155-S`, but remained `status: queued` in
`.backlogit/queue/027-DL.md`. Repository precedent archives a completed
deliberation after harvest (`023-DL`, archived from `queued` while its
consuming feature `142-F` was still open).

Archived via the supported Backlogit lifecycle operation
(`backlogit_archive_item`), not by hand-editing markdown. Final state:
`status: archived`, `archived_from: .backlogit/queue/027-DL.md`,
`archived_status: queued`, now at `.backlogit/archive/027-DL.md`. A traceability
comment recording the harvest destinations was appended to the item log before
the move.

Path pointers to `.backlogit/queue/027-DL.md` in the plan, hardening, review,
and `147-F`'s `references` were deliberately left as-is, matching the `023-DL` /
`142-F` precedent (`142-F` still references `.backlogit/queue/023-DL.md`). The
deliberation now resolves at `.backlogit/archive/027-DL.md`.

### 2. `155-S` is BLOCKED pre-claim by a `154-S` closure-evidence gap

The installed pre-claim topology gate returns
`PREDECESSOR_CLOSURE_INCOMPLETE: predecessor 154-S is terminal but missing
required closure evidence`.

Read-only cause: `docs/closure/154-S-146-F-post-merge-closure.md` declares
`closure_status: READY_WITH_CONDITIONS` and `compaction_status: done` but has
no machine-readable `conditions:` frontmatter list.
`_closure_artifact_complete` (`src/autoharness/gates/topology.py:294`) accepts
`READY_WITH_CONDITIONS` only when every entry of a non-empty `conditions:` list
carries `satisfied: true` plus non-empty `evidence:`. Reproduced directly:
`conditions=None`, `complete=False`. The artifact BODY does record the captured
follow-up `5CFA8198`, so this is an evidence-FORM gap, not an unmet condition.

Stage did NOT modify the Ship-owned closure artifact and did NOT bypass or
weaken the gate. The prerequisite is now recorded in the plan
(`execution_prerequisite` frontmatter key + "Execution prerequisite" section +
a Sequencing line) and mirrored as a comment on `155-S`.

**The repair was deliberately NOT added to `147.001-T`-`147.004-T` or to the
`155-S` manifest**: the gate blocks the CLAIM of `155-S`, so any item inside
`155-S` could never unblock it - that would be a circular prerequisite. It must
land as separate, narrow, pre-claim Ship work.

### Corrected handoff

1. **Ship** - narrow predecessor-closure evidence repair on
   `docs/closure/154-S-146-F-post-merge-closure.md`: add the machine-readable
   `conditions:` list (one entry per condition the existing
   `READY_WITH_CONDITIONS` prose already asserts, each `satisfied: true` with
   concrete `evidence:`; the `5CFA8198` -> `027-DL` -> `147-F` / `155-S` chain
   is the evidence for the captured-follow-up condition). Verdict value
   unchanged; historical narrative not rewritten.
2. Re-run the pre-claim topology gate and confirm `shipment_readiness` passes
   for `155-S`.
3. **Orchestrator** - claim `155-S`.
4. **Ship** - execute `147.001-T -> 147.002-T -> 147.003-T -> 147.004-T` in
   dependency order; `T4`'s append-only cross-reference to `027-DL` stays a
   body-only addition and does not overlap step 1.
5. After merge, archive stash `5CFA8198` (work-contract item 5).
