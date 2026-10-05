# Ship session checkpoint: 200-S / 194-F post-merge closure (2026-10-04)

## Context

* PR #490 (`feat(routing): context_tier on model_routing routes and agent
  frontmatter, fresh-install Ship seed, dogfood Ship pin (200-S / 194-F)`)
  merged as `b264efd5` at `2026-10-04T21:36:18Z`, with reviewed HEAD
  `d7721b00`.
* This session ran under dark mode (P-017), with the operator AFK. Merges
  were pre-authorized, but this part of the closure stops before push and PR.
* The closure ran in two parts. Part 1 (with the Orchestrator) ran the
  lifecycle gate, the runtime proofs, pre-mode, `--classify-only`, and the
  mutating `cascade-close`. Part 2 (this session) ran the guard, the INV-12
  disposition, post-mode, source cleanup, follow-ups, sync, the suite, and
  this record.

## What ran (branch `chore/200-s-closure`, cut from `main` at `b264efd5`)

1. Lifecycle topology gate: exit 0 (`BRANCH_OK`, `WORKTREE_TOPOLOGY_OK`, sole
   active `200-S`, predecessor `199-S` explicit).
2. Runtime proofs 1 to 3 from the plan: all met
   (`.proof-scratch/200-closure-proofs/results.md`).
3. Lock `.backlogit/queue/200-S.md` acquired at `21:46:29Z`. Pre-mode
   returned `PROCEED` for 15 items (`194-F` active in the queue; 14 tasks
   `done` in the archive).
4. `--classify-only` exited 0 (`CASCADE`, `VERIFIED` `1.11.0` / cli).
   Committed in `bd610aa8`.
5. Sizing: N = 16 and B = 1040 s, so the default 1800 s timeout applied. The
   Orchestrator ran the mutating command attached. It exited 0 after 737 s;
   the backlogit child took about 710 s. It archived 16 IDs, `returned_ids`
   was `[]`, and postconditions passed.
6. Whole-tree guard: 1895 files before and after; 18 changed, all in
   `closure_scope(200-S)`; 0 out of scope.
7. INV-12: `036-DL` was `retained_shared_reference` (referrer `BAF15C62`),
   giving `DISPOSITION_COMPLETE`. Post-mode returned `PROCEED`. The lock was
   released at `00:00:09Z`. Committed in `1a570ef9`.
8. Source cleanup: stash `6EC29DD6` was already archived; `036-DL` was
   retained.
9. Follow-up stash entries: `09DFC9F9`, `EFC48191`, `D6FE4677`, `8447F9EB`,
   `9039DA3F`, and `7A3E1AD7`. Existing entries were reused for the dogfood
   verify failures (`50434138`, `97B28746`, `BCD87392`), MD001 (`24BA1B8F`),
   and subagent drift (`BAF15C62`). `backlogit sync` reported
   `Indexed 1711 artifacts`. Committed in `acb57265`.
10. Full suite on `acb57265`: `Ran 3143 tests`, `OK (skipped=54)`.
11. Closure artifact: `docs/closure/200-S-194-F-post-merge-closure.md`
    (`close_path: cascade`).

## Learnings

* The duration model (133 s + 35 s per artifact) predicted 693 s for 16
  artifacts, and the child took about 710 s. The engine spent about 176 s
  before the shipment status change and about 150 s more before the first
  task rewrite, then about 25 s per task.
* The 199-S `run_c.py` script was reused by changing only the IDs.
* A `git add` with a pathspec that no longer exists fails the whole add. The
  chained commit then recorded only the already staged rename. Amend the
  commit, and use `git add -A` on directories for queue-to-archive moves.
* `scripts/release_lock.ps1` warns that the target file does not exist after
  the queue-to-archive move. That warning is expected, and the release
  succeeds.
