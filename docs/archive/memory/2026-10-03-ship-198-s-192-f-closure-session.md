# Ship session checkpoint: 198-S / 192-F resumed post-merge closure (2026-10-03)

## Context

* The first closure attempt halted before mutation. The details are in
  `docs/memory/2026-10-02-ship-198-s-192-f-closure-halt.md` and PR #483.
* The operator chose "Fix the cap first. Option 1." Stage added
  `192.023-T` .. `192.026-T` (PR #484). PR #485 merged as `829ab5e1`, raising
  the `cascade-close` `--timeout` range to 30–3600 s with a default of
  1800 s, and setting the supervision budget to `--timeout + 600 s`.
* This session ran under dark mode (P-017). Merges were pre-authorized, but
  this session stops after opening the closure PR.

## What ran (branch `chore/198-s-closure-2`, cut from `main` at `829ab5e1`)

1. The venv was refreshed with `pip install -e .`. `cascade-close --help`
   shows `30-3600` and `Default: 1800`.
2. Lifecycle topology gate: exit 0 (`BRANCH_OK`).
3. Lock `.backlogit/queue/198-S.md` acquired at `08:07:37Z`. Pre-mode
   returned `PROCEED` for 27 items.
4. `--classify-only --replace-pre-close` exited 0 (`CASCADE`, `VERIFIED`),
   replacing the stale `eb8b7811` record. Committed in `d820cb44`.
5. Sizing: N = 28, B = 1670 s, so the default 1800 s timeout applied. The
   mutating run was started in attached async mode and polled every 300 s.
   It exited 0 after 1006 s; the backlogit child took about 985 s. It
   archived 28 IDs, `returned_ids` was `[]`, and postconditions passed.
6. INV-12: `035-DL` and `038-DL` both `retained_shared_reference`, giving
   `DISPOSITION_COMPLETE`. Post-mode returned `PROCEED`. The lock was
   released at `08:25:52Z`. Committed in `d6aaf9ab`.
7. Stash `A5FA81C4` (task/low) records that the effective `--timeout` is
   missing from the evidence record. `backlogit sync` reported
   `Indexed 1696 artifacts`.
8. Closure artifact: `docs/closure/198-S-192-F-post-merge-closure.md`
   (`close_path: cascade`).

## Learnings

* The duration model (133 s fixed + 35 s per artifact) predicted 1113 s for
  28 artifacts. The actual time was 985 s, so the model is slightly
  pessimistic at this size, and the 1.5× margin is comfortable.
* The `.backlogit/queue/{S}.md` lock can be held across separate processes
  by persisting its token. Releasing it after the cascade moves the target
  prints a harmless "Target file does not exist" warning and still releases
  the lock.
* Do not change the stash between `--classify-only` and the mutating run.
  A new referrer can change the recorded disposition plan
  (`referrer_ids`) and risks a revalidation drift (exit 4). Capture
  follow-up stash entries after the disposition step.
