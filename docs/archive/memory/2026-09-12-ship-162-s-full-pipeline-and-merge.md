# Session Memory: 162-S / SHIP-4 — Full Pipeline Execution and Merge

**Agent**: Ship
**Date**: 2026-09-12 (local)
**Session scope**: Full end-to-end execution of shipment 162-S (feature
154-F, tasks 154.001-T..154.004-T) — claim, build, review, PR, extended
review-fix loop, operator-authorized dark-mode merge, and post-merge
closure. The branch was created carrying pre-existing operator-authorized
uncommitted changes (`.backlogit/stash.jsonl`, `.gitignore`, a checkpoint
file, two design docs, `docs/diagrams/`, `scripts/check_eraser_diagrams.py`);
these were preserved untouched throughout and remain uncommitted after merge.

## What shipped

Five defects fixed across four tasks:

- **154.001-T** (BA035180): removed the security-reviewer's purpose-based
  finding-suppression rule; added a report-first/classify-scope-afterwards
  discipline naming P-021 as the disposition channel.
- **154.002-T** (C0EA1175/701073F9): replaced P-007's unconditional
  `git restore` remediation with Decisions G1-G9 (live operator approval,
  evidence-only backlog comment, fail-closed no-channel halt, pathspec
  scoping, and — added during review-fix — immediate pre-restore
  revalidation against a fresh status read to close a TOCTOU gap); completed
  the constitution-reviewer's principle checklist (Principle X/XI).
- **154.003-T** (7628C291): added a Bounded One-Hop Review-Family Exception
  to `harness-architecture.instructions.md`/`role-enforcement.instructions.md`,
  resolving the contradiction with `review`/`plan-review`'s declared
  one-hop persona spawning; shipped a static document-layer verifier.
- **154.004-T** (F0ADCC03): added Decision F (co-installation invariant) to
  `install-harness/SKILL.md`; closed the technology-reviewer's dangling
  `python.instructions.md` reference via F2 graceful degradation.

During Ship's own local review, a self-found P1 identified the same P-007
defect independently restated in two more carriers
(`templates/agents/_ship.agent.md.tmpl`, `.github/skills/shipment-reconcile/SKILL.md`
+ template) — both fixed in the same cycle.

## PR #446 — 9 rounds of Copilot review

Hosted review ran 9 rounds (24 threads total, all replied-to and resolved
in the same round each was found), well beyond the nominal 3-round
circuit-breaker. Findings converged on decreasing severity/count per round:
3, 2, 1, 2, 2, 2, 5, 4, 2. The last three rounds were dominated by the
**current-HEAD evidence-drift** pattern already documented in
`docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md` — see
the new `docs/compound/2026-09-12-breaking-the-current-head-drift-review-loop.md`
for the fix (split code-affecting fix commits from evidence-anchor-refresh
commits) that finally broke the loop.

One finding was deliberately **not** fixed in-cycle: the installed dogfood
Ship agent (`.github/agents/_ship.agent.md`) never invokes
`shipment-reconcile`'s `mode: post`, so this repository's own Ship workflow
never runs the P-007 deleted-file guard regardless of this shipment's fix.
This is a real, pre-existing, high-priority gap, captured as P-021 deferred
stash entry `72676271` for Stage deliberation rather than expanded into —
fixing it required restructuring the installed agent's closure-tasks
contract, outside 154.002-T's authorized surface.

Five P-021 deferred entries captured this session: `CE6749C9` (the
operator-authorized but out-of-scope `check_eraser_diagrams.py`),
`4C0126A5` (P-015's own cascade-revert lacks an equivalent approval gate),
`CEB6555A` (verifier vocabulary gap for `verify-harness`), `206ED296` (test
hardening opportunity), `72676271` (high — see above).

## Operator authorization sequence

1. Initial dark-mode activation: `merge_approval_pre_authorized=false`,
   `admin_fallback_pre_authorized=false` — Ship prepared the PR through all
   gates and halted before merge as instructed.
2. Ship reported a P-018 BLOCK (round-7 findings still open) and asked for
   disposition rather than continuing indefinitely per the circuit breaker.
3. Operator responded: "Merge approval is implicit with dark factory mode,"
   authorizing `merge_approval_pre_authorized=true` for the bounded 162-S
   scope, with `admin_fallback_pre_authorized` remaining `false` and an
   explicit instruction that all gates (P-014, P-018, CI, P-009, P-016) must
   still pass — merge is conditioned on gates, not unconditional.
4. Ship resumed the review-fix loop (rounds 7-9), reached P-018 `SATISFIED`
   with CI green, P-009 confirmed (`allow_merge_commit: true`, squash/rebase
   disabled), and topology gate passing, then merged via
   `gh pr merge 446 --merge` (two-parent merge commit
   `1b2312273c1570c7557d367429c24e7e8905c0de`, confirmed ancestor of
   `origin/main`). No admin fallback was used or needed at any point.

## Post-merge closure

- Fast-forwarded local `main` to the merge commit; created
  `post-merge/162-s-closure` per the Post-Merge Branch Protocol.
- Cleared a stale, pre-session, zero-byte, no-owner-info advisory lock on
  `.backlogit/queue/162-S.md` (`.162-S.md.lock`, dated 2026-09-03, predating
  this entire session) via `release_lock.ps1 -Force`, justified as a
  provably abandoned artifact blocking mandatory closure, per the operator's
  standing authorization to continue through required post-merge closure.
- Ran the shipment-reconcile procedure manually (no MCP skill-invocation
  surface available in this session): pre-mode confirmed all 5 manifest
  items already pre-archived, shipment record `active` (consistent);
  `classify_shipment_close_path` confirmed the **verified fully-covered-root
  CASCADE exception** (154-F root, fully covered by its exact 4 children,
  manifest contains nothing beyond that); ran the cascade
  `backlogit shipment ship 162-S --sha 1b231227...`; independently verified
  `archived_ids` exactly matched the computed `allowed_ids`/`required_ids`
  set (`154.001-T, 154.002-T, 154.003-T, 154.004-T, 154-F, 162-S`), zero
  `returned_ids`; post-mode P-007 check found no working-tree deletions
  (no restore needed); released the lock.
- Compound learning written (see above).
- `compact-context --target all` invoked (P-020 mandatory).
- Carried files preserved exactly throughout (confirmed via `git status`
  at every stage); the mid-session external `docs/bugs/...` artifact
  (appeared from an apparent concurrent Stage-side process in this same
  checkout) was left untouched and unreported to git.

## Follow-ups for the operator / Stage

- P-021 entries `4C0126A5`, `CEB6555A`, `206ED296`, `72676271`, `CE6749C9`
  need Stage triage and deliberation.
- `72676271` in particular: the installed Ship agent's closure-tasks thin
  pointer needs an explicit `mode: post` invocation step added, with a
  manifest checksum refresh, before this repository's own P-007 protection
  is actually live end-to-end.
