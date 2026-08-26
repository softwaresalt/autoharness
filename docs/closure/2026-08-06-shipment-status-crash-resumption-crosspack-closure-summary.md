---
doc_type: closure-compaction-summary
compaction_phase: phase-3-closure-compaction
compacted_on: "2026-08-26"
period_start: "2026-08-06"
period_end: "2026-08-08"
shipments: [118-S, 119-S, 120-S]
features: [112-F, 111-F, 082-F]
source_artifacts:
  - docs/archive/closure/118-S-112-F-post-merge-closure.md
  - docs/archive/closure/119-S-111-F-post-merge-closure.md
  - docs/archive/closure/120-S-082-F-post-merge-closure.md
---

# Closure Summary — 118-S through 120-S: Shipment-Record-Status Diagnostics, Crash-Resumption Protocol & Cross-Pack Measurability Docs (2026-08-06 to 08-08)

Consolidates three post-merge closure records: read-only shipment-record-
status inconsistency detection (`112-F`, 936C68F3 part 2), the
operator-confirmed crash-resumption + prune-on-restore protocol (`111-F`,
34D50F2D candidate d), and cross-pack (Engram + graphtor-docs) measurability
documentation (`082-F`, first shipment of the dark-mode sequence
`120-S → 121-S → 122-S`). `118-S → 119-S` is the final pair of the serial
chain `117-S → 118-S → 119-S` derived from spike `001-SP`. Source artifacts
are preserved verbatim at `docs/archive/closure/`.

## Shipments & Features Covered

| Shipment | Feature | Tasks | PR (+ closure PR) | Merge commit (+ closure) | Merged at | `closure_status` | `feature_terminal_status` |
|---|---|---|---|---|---|---|---|
| 118-S | 112-F | 4 | #308 (+ #309) | `f4f517c678676e64215a433f7561438137098f71` | 2026-08-07T03:45:09Z | READY | done |
| 119-S | 111-F | 7 | #310 (+ #311) | `8262bd29da750e76397723f10209ee14f692f184` (+ `90dacd6cd16dfdb42c7552676f55703ceb2dacff`) | 2026-08-07T15:01:13Z | READY | done |
| 120-S | 082-F | 3 | #314 (+ #315) | `ca066a053c891fa2152c85c2f2936f6507e81fa3` (+ `55bfb3454641fe0a68d03ef6736e8456297f6fc1`) | 2026-08-08T06:17:22Z | READY | done |

All entries carry `compaction_status: done` (verbatim from source
frontmatter). All merges verified as genuine two-parent merge commits
(P-009).

## What Was Verified, and Verdict per Shipment

- **118-S / 112-F** — READ-ONLY `detect-mixed-role` diagnostics (936C68F3
  part 2). 3 Copilot threads, all fixed. **Baseline Integrity Gate
  deviation**: this session proceeded past a no-exemption halt condition for
  protected feature `112-F` (already archived at baseline) based on explicit
  contemporaneous operator instruction — **documented as a genuine
  template-contract gap, not a sanctioned default exception**; a follow-up
  was raised for Stage to formalize an exemption. **6th occurrence** of the
  move-vs-archive gap (all 4 tasks + `112-F` had only been `move --status
  done`'d, never explicitly archived — fixed in this closure). **Verdict:
  READY.**
- **119-S / 111-F** — operator-confirmed crash-resumption + prune-on-restore
  protocol (candidate d of tracker `34D50F2D`; candidates a/c remain
  deferred/ACTIVE). **Final shipment of chain `117-S → 118-S → 119-S`.**
  **3 rounds of Copilot review, 16 total comments** — unusually, each
  round's own fix introduced a new, subtler filter/gate bug (documented in
  `docs/compound/2026-08-07-copilot-review-fix-introduces-new-filter-bug.md`):
  Bug A (unsafe age filter), Bug B (prune/resume ordering), Bug C (empty
  agent/status fields silently dropped), Bug D (backlogit-only install
  false-halt), Bug E/F (`cleanup_checkpoints` disposition-guard gaps) — all
  eventually fixed. A provenance-repair correction to
  `closure_merge_commit`/`closure_reviewed_head` frontmatter is documented in
  the source's own Closure Tasks section (an intermediate HEAD was
  originally recorded, corrected to PR #311's true values). **Verdict:
  READY.**
- **120-S / 082-F** — documentation-only cross-pack (Engram/graphtor-docs)
  telemetry evidence-mapping; `082-F` is the backlogit-portion carved from
  `108-F` (see the 2026-08-03 group summary for `108-F`'s own carve-out
  closure). 1 round of Copilot review, 5 findings (a state-vs-call-outcome
  conflation pattern; compound doc:
  `docs/compound/2026-08-08-state-vs-call-outcome-conflation-in-telemetry-mapping.md`).
  **Dirty-worktree handoff**: out-of-scope 121-S-relevant changes
  (model-route rename, checkpoints, a rename-deliberation doc) were isolated
  into a **labeled** stash ("120-S: preserve out-of-scope dirty state...") —
  explicitly 121-S's own responsibility to restore, with a caution that
  stash indices are positional, not stable. Also carried forward an
  operator-owned `.gitmodules`/`references/atv-phoenix` gitlink addition (no
  backlog item). **Verdict: READY.**

## Healthy Signals

- All three merges are genuine two-parent commits; P-009 preserved.
- `118-S → 119-S` closes out the `117-S/118-S/119-S` chain cleanly, with
  every Copilot-review-introduced regression across 119-S's 3 rounds
  eventually caught and fixed rather than merged silently.
- `120-S` correctly isolated out-of-scope dirty-worktree changes into a
  clearly labeled stash rather than discarding or force-committing them.

## Failure Signals Observed

- **118-S**: Baseline Integrity Gate deviation — proceeding past a
  no-exemption halt for an already-archived protected feature, on explicit
  operator instruction. This is recorded as a template-contract gap
  requiring Stage follow-up, not routine behavior.
- **118-S — 6th occurrence of the move-vs-archive gap** (after 109-S, 111-S,
  112-S, 113-S, 117-S). Fixed in this closure; the cross-shipment
  enforcement follow-up remains open.
- **119-S**: a recurring pattern where each Copilot review round's fix
  introduced a new, distinct filter/gate bug (Bugs A–F across 3 rounds) —
  all fixed, but the pattern itself is captured as a compound learning for
  future review-fix work to watch for regressions introduced by fixes
  themselves, not just by the original code.
- **119-S**: a provenance-repair correction was needed for
  `closure_merge_commit`/`closure_reviewed_head` (an intermediate HEAD was
  initially recorded) — self-corrected within the same document, not an
  open issue.

## Monitoring, Validation Windows & Rollback Triggers

- **118-S**: rollback = revert `f4f517c6...`. READ-ONLY diagnostics, no
  destructive migration. Validation window: immediate post-merge
  2026-08-07.
- **119-S**: rollback = revert `8262bd29...`. Crash-resumption/prune-on-
  restore protocol is additive; candidates a/c remain deferred/ACTIVE for a
  future shipment. Validation window: immediate post-merge 2026-08-07.
- **120-S**: rollback = revert `ca066a05...`. Documentation-only change, no
  runtime surface. Validation window: immediate post-merge 2026-08-08.

## Unresolved Follow-Ups Carried Forward

1. **Move-vs-archive enforcement** — still open after its 6th occurrence at
   118-S; no scripted pre-flight check has been added as of this closure.
2. **118-S Baseline Integrity Gate exemption gap** — Stage follow-up raised
   to formalize an exemption path for already-archived protected features
   under explicit operator instruction; not yet formalized.
3. **119-S — tracker `34D50F2D`**: candidates **a and c remain deferred and
   ACTIVE** (only candidate d was resolved by this shipment). Not closed by
   any shipment in this group.
4. **120-S — two distinct stash situations, do not conflate**:
   - (a) The **120-S-created labeled stash** ("120-S: preserve out-of-scope
     dirty state...") holding the model-route-rename/checkpoints/rename-
     deliberation-doc changes — **121-S's explicit responsibility to
     restore**. Caution: stash indices are positional, not stable, across
     intervening stash operations.
   - (b) A **separate, pre-existing debris stash**
     (`ab16544a1636651d2368825d08cbd5e7c26ec755`) is a **different** stash
     not created by 120-S and not addressed in this group — see the
     2026-08-08 group summary (121-S/122-S) for its "Checkpoint Anomaly
     Disposition."
   These two are distinct stash objects and must not be conflated when
   tracing 121-S's or 122-S's own closure records.
5. **120-S**: an operator-owned `.gitmodules`/`references/atv-phoenix`
   gitlink addition was carried forward with no backlog item — informational
   only, not a defect.
6. No new follow-ups were recorded from 118-S or 119-S beyond the items
   above.
