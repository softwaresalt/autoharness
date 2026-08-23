---
type: session-memory
date: 2026-08-23
agent: ship
shipment: 153-S
feature: 145-F
status: shipped-closure-in-progress
---

# Ship session memory — 153-S / 145-F (mechanism B measurement, E8158860)

## Summary

Executed shipment 153-S end-to-end: claimed, measured `BranchOwnershipTests`
intra-file order pollution at mechanism-A's fixed head (152-S), proved
`SUBSUMED` via the mandatory A10 reverted-checkout negative control, closed
both tasks with zero source changes, opened PR #401, addressed one
Copilot review-fix cycle (2 findings, both P-021 C1 in-scope, fixed
directly), passed P-018, merged with a verified 2-parent merge commit
(`fed1319bac9e1ac3c2f2eeb448390fbfc192f155`), cascade-closed the shipment
per the P-015 verified-fully-covered-root exception, and is completing
post-merge closure (this document, the closure PR, and P-020 compaction).

## Key facts for future reference

- **Disposition**: `SUBSUMED`. Mechanism B (the intra-file test-order
  dependence `141.004-T` first measured) is a downstream symptom of
  mechanism A (152-S's `GIT_CONFIG_VALUE_2` Windows destructive-restore
  fix), not an independent defect. No remediation code was needed or
  written.
- **Evidence**: standalone `test_gates_topology.py` 104/104 green; all 5
  named polluter->victim pairings green individually against current
  (mechanism-A-fixed) code; all 5 pairings reproduced the original failure
  when the 5 `BranchOwnershipTests` methods were surgically, temporarily
  reverted to their pre-`34d194a4` form (non-vacuity proof), then restored
  to byte-identical HEAD before any commit.
- **Canonical Windows full suite**: 1830 tests, OK, skipped=20 — matches
  the 152-S baseline exactly, no regression.
- **Review-fix cycle**: 1 of 3 budgeted cycles used. Both Copilot findings
  were about the evidence record's completeness/accuracy (missing verbatim
  transcripts; a causal misattribution to the wrong leaked environment
  variables), not about any source defect — see the compound learning doc
  `docs/compound/2026-08-23-153-s-145-f-measurement-task-review-scrutiny.md`.
- **Merge**: PR #401 merged as `fed1319bac9e1ac3c2f2eeb448390fbfc192f155`,
  two parents verified (`bbaf327f` + `d33dc898`), ancestor-verified in
  `origin/main`.
- **P-015 cascade-close**: `classify_shipment_close_path` confirmed CASCADE
  eligibility for 145-F/153-S both pre- and post-merge (145-F is a root,
  fully covered by its 2 manifest-member children). `backlogit shipment
  ship 153-S --sha fed1319b...` archived exactly `145.001-T`, `145.002-T`,
  `145-F`, `153-S` with zero `returned_ids`.
- **Post-merge closure**: branch `post-merge/145-f-mechanism-b-branchownershiptests-order-pollution`,
  cascade-close commit `1056ecd7`, closure doc
  `docs/closure/153-S-145-F-post-merge-closure.md`.

## Stop state / what's left

At the time of writing this memory: the cascade-close commit is made on
the post-merge closure branch; the closure doc, this session-memory file,
and the compound learning doc are being added to the same branch. Still
pending: run `compact-context --target all` (P-020, mandatory), populate
`closure_pr`/`closure_reviewed_head`/`compaction_status` in the closure
doc frontmatter once the closure PR exists and the final pre-merge commit
is known, push, create the closure PR, CI/local-review/P-018, merge
(normal merge commit, verify 2 parents), sync `main`, resolve the active
checkpoint, and return to `main`.

**Do not claim 153-S's successor** (if any) in this session — the operator
explicitly scoped this invocation to 153-S only and instructed stopping
after full closure without claiming any further shipment.

## Constraints preserved throughout

- Engram CLI circuit remained open the entire session — never retried; all
  codebase discovery used targeted/exact-path reads and literal searches
  only, never broad structural/dependency search substitutes.
- All 12 pre-existing stashes, including both `.mcp.json` stashes, were
  never touched, listed, applied, or dropped.
- No admin fallback was used or needed; P-009 (merge-commit-only) was
  verified and honored for the merge.
- No shipment beyond 153-S was claimed.
