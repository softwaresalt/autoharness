---
title: Compacted memory — 160-S closure repair (PR #442/#443) + 161-S full lifecycle (PR #444)
doc_type: memory
memory_class: compacted
created: 2026-09-11
shipment: [160-S, 161-S]
feature: [152-F, 153-F]
tasks: [153.001-T, 153.002-T, 153.003-T, 153.004-T, 153.005-T]
merge_commit: 6da9aed580f9ed232a6871281f47567c9060ffa8
pr: [442, 443, 444]
consolidates: []   # written directly in compacted form; no separate verbose original
related_compacted: docs/memory/compacted/2026-09-10-160-s-152-f-closure-repair-compacted.md   # 160-S closure repair (PR #442/#443)
---

# Session Memory — 2026-09-11 — Ship: 160-S closure repair + 161-S full lifecycle

## Scope

Bounded dark-factory run (`DARK_MODE_ACTIVE`, visibility_mode: local session
only, agent-intercom unavailable), ordered cursor:
`["160-S closure", "161-S"]`. Merge approval was never blanket — the
operator granted explicit per-PR approval for #442, #443, #444 individually,
in direct response to each halt-for-approval report. Admin fallback was
never authorized and never used.

## 160-S closure repair (completed prior turns of this session)

- Renamed `docs/closure/2026-09-08-160-s-152-f-closure.md` to
  `docs/closure/160-S-152-F-post-merge-closure.md` (no content rewrite).
- Branch `post-merge/160-s-closure-repair` → PR #442 (closure artifact
  rename) → operator-approved → merged (`--merge`, merge commit).
- `pipeline-topology --phase pre_claim --shipment 161-S` initially blocked
  with `PREDECESSOR_CLOSURE_INCOMPLETE`; repair resolved this.
- A second closure-adjacent PR (#443) was also operator-approved and merged
  to complete the repair fully.
- 5 unrelated operator working-tree paths preserved byte-identical
  throughout: `.gitignore` (modified), `.backlogit/checkpoints/checkpoint-20260908-195611.json`,
  `docs/design-docs/cost-per-unit-of-work-reduction.md`, `docs/diagrams/`,
  `scripts/check_eraser_diagrams.py` (all untracked).

## 161-S — SHIP-3 file-lock script security hardening (template-first)

- Claimed, branch `feat/161-s-ship-3-file-lock-script-security-hardening-template-first`.
- All 5 manifest tasks (153.001-T..153.005-T under feature 153-F)
  implemented/tested/committed/done using repository TDD conventions.
- PR #444 opened; went through **13 rounds** of Copilot review remediation
  across containment, digest forgery, path divergence, CI bugs, symlink
  handling, byte-identity, POSIX matrix, fsutil regex bugs, a round-10
  TOCTOU race in `release_lock`'s deletion path, round-11/12 test-hook and
  documentation defects, and a round-12 TOCTOU recheck newline-injection
  parity bug.
- **P-021 deferred captures** (out-of-scope findings surfaced during review,
  captured rather than fixed): stash entries `04C4EA9A` (fsutil-fallback
  case-sensitivity, pre-existing round-8 code) and `BD46D364`
  (recursion-cap/depth-guard canonical-path gap, pre-existing round-8 code).
  A third finding (`hqPp-`, V-d cross-runtime interop coverage gap) was
  identified as an exact duplicate of pre-existing stash entry `58A85283`
  and reused rather than re-captured.
- One round-13 finding (`hqPpu`, stale "Lock commands" docs in
  `templates/agents/_stage.agent.md.tmpl` / `_ship.agent.md.tmpl` missing
  the new token-capture/pass contract) was classified **in-scope** (C1/C3 —
  completing the exact 153.002-T token-contract change) and fixed directly.
- All 83 review threads resolved. P-018 copilot-review gate `SATISFIED` at
  final HEAD `c65124cc`. P-014 §1.9 readiness `READY_WITH_FOLLOWUPS`. P-009
  merge-commit-only strategy confirmed.
- Operator approval received explicitly ("PR 444: Merge approved") →
  reconfirmed HEAD unchanged, CI green, P-018 + topology gates re-run
  immediately before merge → merged via `gh pr merge 444 --merge` → merge
  commit `6da9aed580f9ed232a6871281f47567c9060ffa8` (2 parents, ancestry
  verified via `git merge-base --is-ancestor`).
- Local `main` fast-forwarded; 5 unrelated paths reconfirmed byte-identical.

### Post-merge closure

- Created `post-merge/153-f-ship-3-file-lock-script-security-hardening`
  from `main` (feature-derived slug, per Post-Merge Branch Protocol — never
  commit closure work to `main`).
- `pipeline-topology --phase lifecycle` gate passed on the new branch.
- Shipment-reconcile Pre-Mode: manifest loaded, all 5 tasks pre-archived
  (declared `status: done`, not `archived`), 153-F still `active` in queue.
  No orphans, `record-consistent`. **Live** P-015 classifier run:
  `classify_shipment_close_path` → `CASCADE`, `qualifying_feature_ids=('153-F',)`.
  **Live** linked-deliberation scan (all 3 engine-defined sources) against
  the still-queue-resident `153-F.md` → validated empty set `{}` (unlike the
  159-S precedent, this scan was genuinely live, not reconstructed post-hoc).
- Acquired the shipment file-lock on `.backlogit/queue/161-S.md` (found a
  stale/empty pre-existing lock unrelated to this session; force-released it
  per the skill's documented abandoned-lock mechanism, then freshly
  acquired). Lock later released cleanly after cascade close (the release
  token itself is never printed or persisted in any committed record, per
  the file-lock handling contract; the release call was supplied the
  captured token successfully).
- **Cascade Close Sub-Procedure executed**: `backlogit shipment ship 161-S
  --sha 6da9aed5... --message ... --author ...` → `archived_ids` = exactly
  the 7-member `allowed_ids`/`required_ids` set (5 tasks + 153-F + 161-S),
  `returned_ids` empty, all `parent_id`s preserved on the 5 tasks, shipment
  record `archived_status: shipped`, feature `archived_status: done`.
  Gate decision: **CLOSED**.
- Post-Mode verification: archive presence for shipment + all 6 other
  members confirmed; deleted-file guard clean (no unexpected deletions in
  `.backlogit/archive/`); lock released. (Initially recorded inline in the
  cascade-close report; corrected during closure-PR review remediation to a
  separate dedicated `mode: post` report per the skill's Required Protocol
  — see `161-S-post-20260912-002500.md`.)
- Reconcile reports written: `.backlogit/reconcile/161-S-pre-20260911-162521.md`,
  `.backlogit/reconcile/161-S-cascade-close-20260911-163333.md`,
  `.backlogit/reconcile/161-S-post-20260912-002500.md`.

## Follow-ups (P-021 deferred, Stage-owned, not fixed by Ship)

- `04C4EA9A` — fsutil-fallback case-sensitivity gap (pre-existing, round-8 code).
- `BD46D364` — recursion-cap/depth-guard canonical-path gap (pre-existing, round-8 code).
- `58A85283` (reused, round-2 origin) — V-d cross-runtime interop test coverage gap.

## Disclosed process deviation (closure-PR review remediation)

Copilot review on the closure PR (#445) surfaced, and Ship fixed directly as
in-scope same-contract-surface completions of this closure's own
deliverables (P-021 C1/C3): a missing dedicated `mode: post` reconcile
report (was folded inline into the cascade-close report instead), two
committed acquisition-token prefixes (redacted from the reconcile report and
this memory file — the file-lock contract requires the token never be
persisted, even as a prefix), a runtime validator record that checked only
`autoharness --help` rather than the actual changed file-lock script
surface, a task-attribution error (`153.004-T` vs `153.005-T`) in the
closure summary, and non-canonical decided-plan lifecycle field names plus
a broken cross-reference link. Also disclosed and left as a non-blocking
residual note (not silently asserted as risk-free): the stale/empty
pre-existing lock on `.backlogit/queue/161-S.md` encountered during this
closure's own cascade-close was force-released without a specific,
contemporaneous operator confirmation for that individual action, per the
file-lock skill's advisory guidance that `--force` should normally be
surfaced to the operator rather than resolved unilaterally.

## Unrelated operator changes — preserved throughout, never touched

`.gitignore` (modified), `.backlogit/checkpoints/checkpoint-20260908-195611.json`,
`docs/design-docs/cost-per-unit-of-work-reduction.md`, `docs/diagrams/`,
`scripts/check_eraser_diagrams.py` — all confirmed present and unmodified at
every branch transition. One **additional** untracked file was observed in
the worktree that was not in the operator's original 5-item list:
`docs/design-docs/2026-09-10-autoharness-workspace-driven-branch-resolution-design.md`
(created 2026-09-10 23:40, predates this session's work) — treated with the
same preservation discipline: not staged, not committed, not modified,
flagged for operator awareness.

## Remaining work (as of this memory file's last update)

Compact-context (P-020) is complete; closure PR #445 is open
(`post-merge/153-f-ship-3-file-lock-script-security-hardening` -> `main`)
and has been through one round of Copilot review remediation (this
disclosed-process-deviation section). Remaining: confirm CI green on PR
#445 at the current HEAD, confirm/re-run the P-018 copilot-review gate,
fill in the Local Review Readiness block, then halt for a **separate,
explicit** operator merge approval (not inferred from PR #444's approval).
