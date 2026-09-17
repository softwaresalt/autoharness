---
title: Compacted memory — 174-S SHIP-16 flat-manifest shipment closure, full lifecycle through merge and cascade close (PR #454)
doc_type: memory
memory_class: compacted
created: 2026-09-17
shipment: [174-S]
feature: [166-F]
tasks: [166.001-T, 166.002-T, 166.003-T, 166.004-T, 166.005-T, 166.006-T]
merge_commit: d8615e9d5eb93a1d1616a735ca1433236868bee1
pr: [454]
consolidates:
  - docs/archive/memory/2026-09-15-stage-166-f-planning-gates.md
  - docs/archive/memory/2026-09-17-ship-174-s-166-f-full-lifecycle.md
---

# Session Memory — 2026-09-17 — 174-S SHIP-16 full lifecycle (Stage planning through Ship merge and cascade close)

## Scope

Rewrite P-015 from the withdrawn hierarchical `TERMINAL_CLOSE` premise to a
flat-manifest, engine-inertness shipment-closure model
(`classify_shipment_close_path` in `src/autoharness/gates/shipment_closure.py`,
plus `.github/policies/workflow-policies.md` and
`.github/skills/shipment-reconcile/SKILL.md` + template mirrors). Feature
`166-F`, 6 tasks, shipment `174-S`.

## Stage planning (2026-09-15)

Ran the three planning gates (`impl-plan`, `plan-harden`, `plan-review`)
against an initial `TERMINAL_CLOSE`-based design, which was **superseded**
mid-session by an operator architectural correction to the flat-manifest
design recorded in
`docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md`
and `docs/plans/2026-09-15-flat-manifest-shipment-closure-plan.md`
(cycle-2 `PASS`). Key substantive corrections carried into the authoritative
design: `ClosePath` keeps exactly `SAFE_CLOSE` and `CASCADE` (no third
`TERMINAL_CLOSE` state); engine-inertness requires exact canonical
`status: archived` with no normalization/synonym acceptance; classifier
evaluation order preserves existing `CASCADE` verdicts bit-for-bit
unchanged. `174-S` was authorized as a `dag-root` (operator-authorized
label, no bootstrap grant, no dependency edge) once the prior `173-S`
shipment's P-001 overlap was discharged by state (administratively closed
2026-09-16).

## Build + Step 3 local review

11-persona local review: 15 out-of-scope findings captured per P-021 (stash
`AD0F128D`, `25B0D5F2`, `2E31C659`, `4E4C54DE`, `429E3F7F`, `815830AB`,
`A0FAE77A`, `CC2E9329`, `85BFB54C`, `9D8C4949`, `AF0CC40E`, `46A985E5`,
`F6330460`, `25E10837`, `AD01B943`); 2 P0/P1 findings (symlink-traversal,
`OSError` fail-closed gaps) fixed in-cycle.

## PR #454: 14 rounds of hosted Copilot review, 52 threads, all resolved

Rounds 1-6 (nominal 3-cycle limit exceeded because each round surfaced a new
genuine, narrowly-scoped finding, not an unresolved ping-pong): id-shape
validation hardening (missing/non-string, then malformed/path-traversal-
shaped, declared `id`s); `required_ids(S)` formula reconciliation across
policy/skill/docstring; baseline-fingerprint capture/verification added to
the Cascade Close Sub-Procedure; directory-symlink/junction containment
guard; a `.tmpl`-mirror gap (round-1 content not actually mirrored) fixed
with a new doc-contract test; a TOCTOU/symlink-race finding deferred
(`92FC85DD`, new capability, not same-contract-surface).

**Operator-authorized extension, rounds 7-14** (explicit operator direction
to continue past the 3-cycle limit for genuine same-contract-surface
findings, P-021 C1/C3):

- Round 7: `closure_scope(S)` baseline-invariance scope made path-specific
  (safe-close vs. CASCADE) rather than one universal scope that forced a
  fail-closed HALT even on legitimate CASCADE archival.
- **Round 8** (the two findings named in the continuation instruction that
  triggered this closure session): (1) INV-6's engine-inertness containment-
  gate statement was broader than round-7's new path-specific rule,
  incorrectly forcing SAFE_CLOSE for live/required
  `validated_linked_deliberations(S)` members legitimately archived by
  CASCADE — narrowed to defer to the classifier's CASCADE verdict,
  reconciled across the installed skill, template mirror, and
  workflow-policies. (2) `ClosePathDecision` computed
  `out_of_manifest_descendant_ids` internally but never exposed it, forcing
  callers toward a forbidden re-derivation (an INV-7/INV-10 risk) — exposed
  as a public field via classifier-first TDD, with regression coverage for
  CASCADE-with-descendants, CASCADE-with-empty-set (174-S's own live case),
  and SAFE_CLOSE shapes.
- Rounds 9-11: doc-only cross-reference/vocabulary-numbering corrections;
  one finding (a stale INV-6 restatement inside the deliberation artifact
  itself) deferred as `7667738E` — genuine but outside Ship's Role Boundary
  (editing a deliberation document); `topology._frontmatter()` fixed to
  catch `UnicodeDecodeError` instead of crashing (classifier suite → 53
  tests); Amendment Log and test-count reconciliation fixes.
- Round 12-13: pre-invocation classifier revalidation added (closing a
  TOCTOU gap between Step 0(c) classification and cascade invocation), then
  extended to also re-collect/compare the linked-deliberation snapshot
  (since the classifier alone never inspects
  `validated_linked_deliberations(S)`).
- Round 14: `last_code_affecting_head` anchor-currency rule clarified —
  `SKILL.md` procedure-text changes DO count as code-affecting, same as
  `.py` source, correcting a false assumption held through rounds 12-13.
- Round 15: `SATISFIED`, zero new threads. P-018 gate cleared (14 total
  review rounds, 52 threads, all resolved).

## Operational pitfalls (durable lessons, see also
`docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md`)

1. PowerShell **double-quoted** here-strings still process backtick escapes
   — an inline-code backtick immediately followed by a letter forming a
   known escape (`` `v ``/`` `n ``/`` `t ``) silently corrupts GitHub API
   comment bodies. Always use single-quoted here-strings (`@'...'@`) for
   comment/PR bodies containing inline code.
2. `classify_shipment_close_path` returns `CASCADE` for an **empty**
   out-of-manifest descendant set (vacuous truth) — confirmed intentional,
   not a bug; this was `166-F`'s own live case.
3. The installed `.github/skills/file-lock/` mirror in this workspace is
   missing its `scripts/` subdirectory — use
   `templates/skills/file-lock/scripts/{acquire,release}_lock.ps1
   -WorkspaceRoot ...` directly as a workaround (pre-existing gap, out of
   scope here).
4. `backlogit shipment ship` (cascade close) is slow (~3 min wall-clock for
   an 8-artifact shipment) — expect multiple polling reads.

## Merge (2026-09-17)

Pre-merge gate re-verification (`pipeline-topology --phase lifecycle` exit
0; `MERGEABLE`/`CLEAN`; P-009 merge-commit-only confirmed; final
unconditional P-018 re-check `SATISFIED` at HEAD `91519498`). Merged via
`gh pr merge 454 --merge`. Merge SHA
`d8615e9d5eb93a1d1616a735ca1433236868bee1`, two parents confirmed, confirmed
ancestor of `origin/main`.

## Post-merge closure: shipment cascade-close SUCCEEDED (contrast with 173-S's blocked SAFE_CLOSE)

`post-merge/174-s-flat-manifest-shipment-closure` branch created from `main`.
Single-writer lock acquired; pre-invocation classifier + linked-deliberation
revalidation identical to the original: `CASCADE`, qualifying feature
`166-F`, empty out-of-manifest descendant set, empty linked-deliberation
set. `backlogit shipment ship 174-S --sha ...` archived 8 artifacts
(`166.001-T`..`166.006-T`, `166-F`, `174-S`), `returned_ids: []`, all
postcondition checks passed (two-set gate, `parent_id` preservation,
baseline invariance). Full report:
`.backlogit/reconcile/174-S-safe-close-20260917-062522.md`, recommendation
`CLOSED`. `mode: post` reconciliation confirmed all 8 artifacts archived;
unrelated pre-existing queued shipment `166-S` (coincidental numeric-prefix
collision) confirmed untouched. Backlog index resynced (1255 artifacts).

This is the **inverse outcome** of the immediately-prior `173-S` closure
(see
`docs/memory/compacted/2026-09-14-ship-173-s-165-f-full-lifecycle-compacted.md`):
`165-F` had out-of-manifest descendants blocking CASCADE and forcing a
SAFE_CLOSE that was itself CLI-blocked; `166-F` had zero out-of-manifest
descendants, so CASCADE applied cleanly and closed the same session as the
merge, with no Stage deliberation blocker.

## Follow-ups (Stage deliberation required)

17 deferred stash entries: `AD0F128D`, `25B0D5F2`, `2E31C659`, `4E4C54DE`,
`429E3F7F`, `815830AB`, `A0FAE77A`, `CC2E9329`, `85BFB54C`, `9D8C4949`,
`AF0CC40E`, `46A985E5`, `F6330460`, `25E10837`, `AD01B943`, `92FC85DD`,
`7667738E`. Plus carried-forward, out-of-scope, pre-existing high-priority
bug entry `14F4D6F3` (untouched, deferred per explicit operator
instruction). Two untracked bug-report docs preserved without modification:
`docs/bugs/2026-09-13-autoharness-append-only-plan-review-loop-bug-report.md`,
`docs/bugs/2026-09-16-autoharness-pipeline-topology-explicit-branch-contract-bug.md`.
