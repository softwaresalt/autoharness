# Ship session checkpoint: 199-S / 193-F post-merge closure (2026-10-03)

## Context

* PR #487 (`feat(193-F): agent and skill frontmatter conformity contract
  (199-S)`) merged as `30095385` at `2026-10-04T06:07:24Z`, with reviewed HEAD
  `1c5c379e`.
* This session ran under dark mode (P-017), with the scope chain
  `... -> 199-S -> 200-S`. Merges were pre-authorized, but this session stops
  after opening the closure PR.

## What ran (branch `chore/199-s-closure`, cut from `main` at `30095385`)

1. The venv was refreshed with `pip install -e .`.
2. Lifecycle topology gate: exit 0 (`BRANCH_OK`, sole active `199-S`,
   predecessor `198-S` explicit).
3. Lock `.backlogit/queue/199-S.md` acquired at `06:10:56Z`. Pre-mode
   returned `PROCEED` for 11 items (`193-F` active in the queue; 8 tasks and
   2 subtasks `done` in the archive).
4. `--classify-only` exited 0 (`CASCADE`, `VERIFIED` `1.11.0` / cli). No
   earlier `pre_close` record existed. Committed in `f210c191`.
5. Sizing: N = 12 and B = 830 s, so the default 1800 s timeout applied. The
   mutating run was started in attached async mode and polled. It exited 0
   after 563 s; the backlogit child took about 540 s. It archived 12 IDs,
   `returned_ids` was `[]`, and postconditions passed. The whole-tree guard
   found only the 14 closure-scope paths changed.
6. INV-12: `037-DL` was `retained_shared_reference` (referrers `4F7B8BA7`
   and `692727D7`), giving `DISPOSITION_COMPLETE`. Post-mode returned
   `PROCEED`. The lock was released at `06:21:47Z`. Committed in
   `1010fa17`.
7. `backlogit sync` reported `Indexed 1698 artifacts`. Source stash
   `EF96B695` was already archived.
8. Follow-up stash entries (task/low): `4C6CBA75`, `A6CF06E6`, `2568A99A`,
   `24BA1B8F`, `BE6C7DF8`, and `3E60149D`.
9. Closure artifact: `docs/closure/199-S-193-F-post-merge-closure.md`
   (`close_path: cascade`).

## Learnings

* The duration model (133 s + 35 s per artifact) predicted 553 s for 12
  artifacts. The actual time was 540 s, so it is close at this size. The
  engine spent about 122 s before its first status change, then about 25 s
  per artifact.
* The 198-S scratch scripts (`run_a.py` for lock, pre-mode, and
  classify-only; `run_c.py` for disposition, post-mode, and lock release)
  were reused with only the IDs changed. Drop `--replace-pre-close` when no
  earlier `pre_close` record exists.
* The `--author` value follows the skill's `<merge_commit_author>`: the
  merge commit's recorded author.
