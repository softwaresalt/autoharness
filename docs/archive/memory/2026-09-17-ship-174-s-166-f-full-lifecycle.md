---
title: "Ship session — 174-S SHIP-16 flat-manifest shipment closure, full lifecycle through merge and cascade close (PR #454)"
date: 2026-09-17
doc_type: memory
agent: ship
shipment_id: 174-S
feature_id: 166-F
tasks: [166.001-T, 166.002-T, 166.003-T, 166.004-T, 166.005-T, 166.006-T]
pr: 454
merge_commit: d8615e9d5eb93a1d1616a735ca1433236868bee1
status: complete
---

# Ship session — 2026-09-16/17 — 174-S full lifecycle (build through post-merge closure)

## Scope

Implement feature `166-F` (P-015 rewrite from the withdrawn hierarchical
`TERMINAL_CLOSE` premise to a flat-manifest, engine-inertness shipment-closure
model) for shipment `174-S`, per the authoritative decision
`docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md`
and plan `docs/plans/2026-09-15-flat-manifest-shipment-closure-plan.md`.
6 tasks (`166.001-T`..`166.006-T`), classifier
`classify_shipment_close_path` in `src/autoharness/gates/shipment_closure.py`,
`.github/policies/workflow-policies.md` and
`.github/skills/shipment-reconcile/SKILL.md` (+ `.tmpl` mirrors) rewritten to
match.

## Build + Step 3 local review

11-persona local review found 15 out-of-scope findings (captured per P-021,
stash entries `AD0F128D`/`25B0D5F2`/`2E31C659`/`4E4C54DE`/`429E3F7F`/
`815830AB`/`A0FAE77A`/`CC2E9329`/`85BFB54C`/`9D8C4949`/`AF0CC40E`/
`46A985E5`/`F6330460`/`25E10837`/`AD01B943`) and fixed 2 P0/P1 findings
in-cycle (symlink-traversal fail-closed gap, `OSError` fail-closed gap).

## PR #454: 14 rounds of hosted Copilot review, 52 threads, all resolved

- **Rounds 1-6** (nominal 3-cycle limit exceeded because each round surfaced
  a new genuine, narrowly-scoped finding rather than an unresolved ping-pong):
  fail-closed fix for missing/non-string declared `id`; `required_ids(S)`
  formula reconciled across policy/skill/docstring; baseline-fingerprint
  capture/verification added to the Cascade Close Sub-Procedure;
  directory-symlink/junction containment guard; decision-doc
  `required_ids(S)` table reconciliation; a TOCTOU/symlink-race finding
  deferred (`92FC85DD`, new capability, not same-contract-surface); a
  `.tmpl`-mirror gap (round-1 content not actually mirrored) fixed with a new
  doc-contract test; `_scan_backlog`'s id-shape validation gap (malformed/
  path-traversal-shaped ids) fixed with a regression test, plus a stale
  "no protected set by construction" claim corrected.
- **Operator-authorized extension, rounds 7-14** (explicit operator direction
  to continue past the 3-cycle limit for genuine same-contract-surface
  findings, P-021 C1/C3):
  - Round 7: `closure_scope(S)` baseline-invariance scope made path-specific
    (safe-close vs. CASCADE) instead of one universal scope forcing a
    fail-closed HALT even on legitimate CASCADE archival.
  - **Round 8 (the two findings named in the current continuation
    instruction)**: (1) INV-6's engine-inertness containment-gate statement
    was broader than round-7's new path-specific rule, incorrectly forcing
    SAFE_CLOSE for live/required `validated_linked_deliberations(S)` members
    legitimately archived by CASCADE — narrowed to defer to the classifier's
    CASCADE verdict, reconciled across installed skill + template mirror +
    workflow-policies. (2) `ClosePathDecision` computed
    `out_of_manifest_descendant_ids` internally but never exposed it, forcing
    callers to re-derive it (itself an INV-7/INV-10 violation risk) — added
    as a public field via classifier-first TDD, with regression coverage for
    CASCADE-with-descendants, CASCADE-with-empty-set (174-S's own case), and
    SAFE_CLOSE shapes.
  - Rounds 9-10: stale Step-4/Step-5 cross-reference corrections (doc-only);
    a stale Step 0(b)/Step 0(c) cross-reference and an INV-1..INV-11
    vocabulary-numbering drift in `SKILL.md` corrected. One finding
    (`docs/decisions/...deliberation.md`'s own stale INV-6 restatement)
    deferred as `7667738E` — genuine but requires editing a deliberation
    artifact, outside Ship's Role Boundary.
  - Round 11: Step 5 SAFE_CLOSE bullet rewritten to separate per-item
    archival from shipment-record closing; `topology._frontmatter()` fixed
    to catch `UnicodeDecodeError` instead of crashing (TDD, classifier suite
    now 53 tests); Amendment Log accuracy fix; closure/runtime-verification
    evidence refreshed.
  - Round 12: pre-invocation classifier revalidation added (TOCTOU gap — the
    original classification could go stale between Step 0(c) and invocation).
  - Round 13: revalidation extended to also re-collect/compare the
    linked-deliberation snapshot (classifier alone never inspects
    `validated_linked_deliberations(S)`); stale "protected set has no
    pre-archived exemption" sentence corrected; test-count reconciliation
    (2342 → 2344, a round-11 arithmetic slip).
  - Round 14: `last_code_affecting_head` anchor bump — established that
    `SKILL.md` procedure-text changes DO count as code-affecting (not just
    `.py` source), correcting a false assumption held through rounds 12-13.
- **Round 15**: `SATISFIED`, zero new threads. P-018 gate cleared.

## Operational pitfalls hit and resolved this session

1. **PowerShell double-quoted here-string backtick-escaping**: a markdown
   inline-code backtick immediately followed by a letter forming a known
   escape sequence (`` `v ``, `` `n ``, `` `t ``) silently corrupts GitHub API
   comment bodies. Fixed via `gh api ... -X PATCH`; rule going forward:
   always use single-quoted here-strings (`@'...'@`) for comment/PR bodies
   containing inline code.
2. **`classify_shipment_close_path` returns CASCADE for an empty
   out-of-manifest descendant set** (vacuous truth) — confirmed intentional,
   not a bug, and this was 174-S's own live case (`166-F`'s only descendants
   were its 6 manifest tasks).
3. **`file-lock` skill install gap**: `.github/skills/file-lock/` has only
   `SKILL.md`, missing the `scripts/` subdirectory in this workspace; used
   `templates/skills/file-lock/scripts/{acquire,release}_lock.ps1
   -WorkspaceRoot ...` directly as a workaround (pre-existing gap, out of
   scope for 174-S).
4. **`backlogit shipment ship` (cascade close) is slow**: ~3 minutes
   wall-clock for an 8-artifact shipment; required multiple polling reads.

## Merge (2026-09-17)

Pre-merge gate re-verification: `pipeline-topology --phase lifecycle` exit 0;
PR mergeability `MERGEABLE`/`CLEAN`; repo settings merge-commit-only
confirmed (P-009); final unconditional P-018 re-check `SATISFIED` again at
the same HEAD `91519498`. Merged via `gh pr merge 454 --merge`. Merge SHA
`d8615e9d5eb93a1d1616a735ca1433236868bee1`, two parents confirmed, confirmed
ancestor of `origin/main` via `git merge-base --is-ancestor`.

## Post-merge closure: shipment cascade-close SUCCEEDED (contrast with 173-S's blocked SAFE_CLOSE)

Checked out `main`, pulled (fast-forward 30 commits), created
`post-merge/174-s-flat-manifest-shipment-closure`. Acquired single-writer
lock on `.backlogit/queue/174-S.md`. Pre-invocation classifier + linked-
deliberation revalidation: identical to original — `CASCADE`, qualifying
feature `166-F`, empty out-of-manifest descendant set, empty linked-
deliberation set. Invoked `backlogit shipment ship 174-S --sha ... `.
Result: `shipment_status: shipped`, 8 artifacts archived
(`166.001-T`..`166.006-T`, `166-F`, `174-S`), `returned_ids: []`. All
postcondition checks passed (two-set `allowed_ids`/`required_ids` gate,
`parent_id` preservation, out-of-manifest baseline invariance — trivially,
for the empty observation set). Full report:
`.backlogit/reconcile/174-S-safe-close-20260917-062522.md`. Recommendation
`CLOSED`. Lock released. `mode: post` reconciliation confirmed all 8
artifacts archived; unrelated pre-existing queued shipment `166-S`
(coincidental numeric-prefix collision, unrelated `references`) confirmed
untouched. Backlog index resynced (1255 artifacts).

This is the **inverse outcome** of the immediately-prior `173-S` closure
(recorded in
`docs/memory/compacted/2026-09-14-ship-173-s-165-f-full-lifecycle-compacted.md`),
where `165-F` had out-of-manifest descendants (`165.007-T`/`165.010-T`)
blocking CASCADE and forcing SAFE_CLOSE, which was itself then blocked by a
backlogit CLI limitation. `166-F` had zero out-of-manifest descendants, so
CASCADE applied cleanly and the shipment closed the same session as the
merge, with no Stage deliberation blocker.

## Follow-ups (Stage deliberation required)

17 deferred stash entries from Step 3 local review + P-018 rounds 1-10:
`AD0F128D`, `25B0D5F2`, `2E31C659`, `4E4C54DE`, `429E3F7F`, `815830AB`,
`A0FAE77A`, `CC2E9329`, `85BFB54C`, `9D8C4949`, `AF0CC40E`, `46A985E5`,
`F6330460`, `25E10837`, `AD01B943`, `92FC85DD`, `7667738E`. Plus carried-
forward, out-of-scope, pre-existing high-priority bug entry `14F4D6F3`
(untouched by this shipment, deferred per explicit operator instruction).
Two untracked bug-report docs preserved throughout without modification:
`docs/bugs/2026-09-13-autoharness-append-only-plan-review-loop-bug-report.md`
and `docs/bugs/2026-09-16-autoharness-pipeline-topology-explicit-branch-contract-bug.md`.

Compound learnings captured in
`docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md`.
