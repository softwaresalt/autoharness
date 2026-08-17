---
title: "Ship halt on 137-S claim: dirty-worktree Branch Creation Gate blocked by excluded operator changes"
source: docs/memory/2026-08-16-ship-137-s-dark-factory-halt.md
doc_type: decision
description: "P-017 dark-factory session record: Ship published the 137-S staging artifacts to main via PR #351 (merged), then halted before claiming shipment 137-S because the Branch Creation Gate's clean-worktree check cannot pass while operator-excluded dirty changes remain in the working tree."
---

# Ship session halt — 137-S staging published, shipment claim blocked

* **Route**: Ship — `claude-sonnet-5` / `anthropic` / `high`
* **Mode**: P-017 dark factory, operator AFK, autonomous judgment authorized
* **Trigger scope**: queue artifacts `137-S`, `128-F`, `128.001-T`, `128.002-T`; later stash scope `BED0DDED`, `47971057`, `34AAF1C7`, `34D50F2D`, `84D8E6AB`, `936C68F3`. Excluded: `080-F`, `081-F`, unrelated dirty operator files.
* **Cursor**: `[137-S]`, last completed none, next `137-S` — **still next; not advanced**.

## What completed

### Staging publication (PR #351) — DONE, MERGED

1. Local main carried Stage's uncommitted (well, committed-but-unpushed) commit
   `92cfa934` ("chore(backlog): make 137-S docline-conformance staging artifacts
   durable") — direct `git push origin main` was rejected (GH013, PR required).
2. Published `92cfa934` to a new remote branch by explicit SHA
   (`git push origin 92cfa934:refs/heads/chore/stage-137-S`) — no local checkout,
   no working-tree mutation, per the operator's explicit dirty-worktree exception.
3. Opened PR #351 (`chore/stage-137-S` -> `main`), backlog/docs-only, full build N/A.
4. Local review: READY, 0 P0/P1. Diff independently re-verified: exactly 14 files,
   all under `.backlogit/` and `docs/`; no `src/`/`templates/`/`schemas/`/`tests/`.
5. Discovered the repo enforces Copilot review via a native ruleset
   (`copilot_code_review.review_on_push: true`) plus
   `pull_request.required_review_thread_resolution: true` —
   `allowed_merge_methods: ["merge"]` (P-009 enforced server-side).
6. Copilot auto-reviewed commit `92cfa934` and posted 2 actionable comments:
   * `docs/decisions/2026-08-16-observable-termination-record-spike.md`:
     `confidence: "medium-high"` is outside the spike contract's allowed
     `high`/`medium`/`low` values (this file is in the session's declared
     "later stash scope" via stash `34AAF1C7`, so fixing it was in scope).
   * `.backlogit/stash.jsonl`: two pre-existing em dashes in the `84D8E6AB`
     record (also in-scope, later-stash) had been corrupted into mojibake
     (`ΓÇö`) by Stage's rewrite of that JSONL line.
7. Fixed both in commit `94b49abb`, using a **pathspec-scoped `git commit --
   <paths>`** (not a bare `git commit`) specifically to avoid sweeping the
   pre-staged excluded operator changes (`.gitmodules`, `references/hve-core`,
   `references/tokenmasterx`) into the fix commit. (First attempt used a bare
   `git commit -m` and *did* accidentally include them; caught immediately,
   reverted with `git reset --soft HEAD~1` — which only moves the branch
   pointer and restores the index to its pre-commit state, touching no file
   content — then redone correctly with the pathspec. Excluded-file working
   state was verified byte-identical before and after.)
8. Also corrected the same `34AAF1C7` stash record's own freshly-appended
   confidence annotation (`medium-high` -> `high`) for internal consistency;
   left the unrelated, historical `34D50F2D` "medium-high" mentions untouched
   (out of scope, pre-existing, preserved append-only history).
9. Pushed `94b49abb` to `chore/stage-137-S` by SHA; replied to both Copilot
   comments referencing the fixing commit; resolved both review threads via
   GraphQL `resolveReviewThread`.
10. Copilot re-reviewed `94b49abb`: **no new comments** (2 low-confidence items
    suppressed by Copilot itself — never posted, no thread created, no
    reply/resolve obligation).
11. CI green (`detect code changes`, `pipeline-topology (ambient)`, `ci gate`
    all `SUCCESS`; `test` `SKIPPED` — no code paths touched).
12. `mergeStateStatus: CLEAN`. Merged via `gh pr merge --merge`
    (merge-commit strategy; repo only allows `merge`, so P-009 cannot be
    violated here). Merge commit `e6bccebf`, confirmed **2 parents**, confirmed
    ancestor of `origin/main`.
13. Verified `git show origin/main:.backlogit/queue/137-S.md` succeeds.
14. Fast-forwarded local `main` to `e6bccebf` (`git pull`) — fast-forward only,
    zero working-tree changes, excluded files verified unchanged before/after.
15. Reloaded current `main` — this PR did not touch `.github/agents/_ship.agent.md`
    or any skill, so the Ship contract in effect is unchanged.

## What did NOT happen — 137-S was NOT claimed

**Blocker**: the Ship pipeline's Branch Creation Gate (Step 3) requires, when on
`main`, that `git status --short` produce **no output** before a shipment/feature
branch may be created. This workspace has pre-existing, operator-owned dirty
changes that are **explicitly excluded from all Ship action** for this session
(never modify, stage, commit, stash, discard, reset, clean, or otherwise disturb):

```
 M .backlogit/archive/015-DL.md
 M .backlogit/memories.json
 D .backlogit/queue/077-F.md
M  .gitmodules
 M docs/reference-library.md
 M references/ai-skills
 M references/awesome-agent-skills
 M references/awesome-agents
 M references/awesome-claude-skills
 M references/awesome-copilot
A  references/hve-core
 M references/mattpocock-eng-skills
A  references/tokenmasterx
 M tests/test_verify_workspace.py
?? .backlogit/archive/077-F.md
?? .backlogit/logs/015-DL.jsonl
?? .backlogit/logs/077-F.jsonl
?? .backlogit/telemetry.jsonl
```

These changes will remain present after any future `git pull`/staging-branch
publication cycle too, since they are working-tree/index state, not commit
history — they cannot be resolved by advancing `main`. Per the explicit operator
directive for this session: **when the clean-main gate cannot be met without
touching excluded changes, halt after completing the staging publication PR
rather than stash/reset/commit them or create a second worktree (P-016).**

This halt is exactly that outcome. Shipment `137-S` (queued: `128-F`,
`128.001-T`, `128.002-T`) was **not claimed**, no `feat/`/`chore/` branch was
created for it, and no implementation work began.

## Resumption path for the operator

1. Decide disposition of the excluded dirty files (they are outside Ship's role
   boundary and outside this session's authorized scope to touch). Once the
   operator has committed, reverted, or otherwise resolved them through their
   own channel, `git status --short` on `main` should return empty.
2. Re-invoke Ship for shipment `137-S`. With a clean worktree, Ship will pass the
   Branch Creation Gate, claim `137-S`, create `feat/spike-template-docline-conformance`
   (or similar), and execute:
   * Task `128.001-T` (XS): correct
     `templates/skills/spike/SKILL.md.tmpl` Phase 5 frontmatter + Step 4.2
     `promoted_to`/`plan_artifact` references to the target `docline`-nested
     shape (see `docs/plans/2026-08-16-spike-template-docline-conformance-plan.md`).
   * Task `128.002-T` (S, blocked by `128.001-T`): add
     `tests/test_spike_template_docline_frontmatter.py` (new module — do
     **not** touch the excluded `tests/test_verify_workspace.py`).
3. No other setup is required — `137-S`, `128-F`, `128.001-T`, `128.002-T` are
   already durably queued on `origin/main`.

## P-020 / compaction note

This is not a shipment closure (nothing was claimed or shipped), so the
mandatory `compact-context` closure invocation does not apply here. No shipment
state was mutated beyond the already-`queued` `137-S`.
