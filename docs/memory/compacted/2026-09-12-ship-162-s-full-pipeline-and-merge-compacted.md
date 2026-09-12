---
title: Compacted memory — 162-S SHIP-4 full pipeline execution and merge (PR #446)
doc_type: memory
memory_class: compacted
created: 2026-09-12
shipment: [162-S]
feature: [154-F]
tasks: [154.001-T, 154.002-T, 154.003-T, 154.004-T]
merge_commit: 1b2312273c1570c7557d367429c24e7e8905c0de
pr: [446]
consolidates: docs/archive/memory/2026-09-12-ship-162-s-full-pipeline-and-merge.md
---

# Session Memory — 2026-09-12 — Ship: 162-S SHIP-4 full pipeline (PR #446)

## Scope

Full pipeline execution: claim, build 4 tasks (154.001-T..154.004-T), local
review, PR #446, 9-round Copilot review-fix loop, operator-authorized
dark-mode merge, post-merge closure. Branch carried pre-existing
operator-authorized uncommitted files throughout, preserved untouched.

## What shipped (5 defects, 4 tasks)

- **154.001-T**: security-reviewer purpose-based suppression removed;
  report-first/classify-scope-afterwards + P-021 disposition channel added.
- **154.002-T**: P-007 unconditional `git restore` replaced with Decisions
  G1-G9 (live approval, evidence-only comment, fail-closed no-channel halt,
  pathspec scoping, pre-restore revalidation against TOCTOU); constitution
  checklist completed (Principle X/XI). Self-found P1 (fixed same cycle):
  the same defect independently restated in `_ship.agent.md.tmpl` and
  `shipment-reconcile/SKILL.md` — both brought into the G1 contract.
- **154.003-T**: Bounded One-Hop Review-Family Exception added to
  harness-architecture/role-enforcement instructions; static verifier
  shipped.
- **154.004-T**: Decision F co-installation invariant added to
  install-harness/SKILL.md; technology-reviewer dangling reference closed
  via F2.

## PR #446 — 9 rounds, 24 threads, all resolved same-round

Rounds 1-6: substantive fixes (correctness bugs in own new code/tests,
TOCTOU gap, test-scoping precision). Rounds 7-9: dominated by the
**current-HEAD evidence-drift** pattern (closure docs' anchor SHA/test-count
chasing a moving HEAD) — see
`docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md`
for the fix that broke the loop: split code-affecting fix commits from
evidence-anchor-refresh commits, so the anchor commit never needs to
reference its own not-yet-known SHA.

**Not fixed in-cycle** (P-021 deferred, `72676271`, high priority): the
installed dogfood `.github/agents/_ship.agent.md` never invokes
`shipment-reconcile mode: post`, so this repo's own Ship workflow never runs
the P-007 guard regardless of this shipment's fix. Also deferred: `CE6749C9`
(operator-authorized out-of-scope `check_eraser_diagrams.py`), `4C0126A5`
(P-015 cascade-revert lacks equivalent gate), `CEB6555A` (verifier vocabulary
gap), `206ED296` (test hardening opportunity).

## Operator authorization sequence

Initial dark-mode: `merge_approval_pre_authorized=false`. Ship built/reviewed/
PR'd, hit P-018 BLOCK at round 7, reported and asked for disposition instead
of continuing indefinitely (circuit breaker). Operator: "Merge approval is
implicit with dark factory mode" → `merge_approval_pre_authorized=true` for
bounded 162-S scope, `admin_fallback_pre_authorized` stayed `false`, all
gates still required. Ship resumed rounds 7-9, reached P-018 SATISFIED + CI
green + P-009 confirmed + topology pass, merged via `gh pr merge --merge`
(two-parent commit `1b231227`, confirmed ancestor of `origin/main`). No
admin fallback used.

## Post-merge closure

Created `post-merge/162-s-closure`. Cleared a stale pre-session zero-byte
advisory lock (`.162-S.md.lock`, dated 2026-09-03, no owner info) via
`-Force`, justified as provably abandoned and blocking mandatory closure.
Ran shipment-reconcile manually (no MCP surface available): pre-mode
confirmed all 5 manifest items pre-archived; `classify_shipment_close_path`
confirmed verified-fully-covered-root CASCADE (154-F root, exactly its 4
children, nothing else in manifest); ran cascade
`backlogit shipment ship 162-S --sha 1b231227...`; independently verified
`archived_ids` == computed `allowed_ids`/`required_ids` exactly, zero
`returned_ids`; post-mode P-007 check found no deletions. Lock released.

## Follow-ups

P-021 entries `4C0126A5`, `CEB6555A`, `206ED296`, `72676271`, `CE6749C9`
need Stage triage. `72676271` blocks this repo's own P-007 protection from
being live end-to-end until the installed Ship agent gets its missing
`mode: post` invocation step.
