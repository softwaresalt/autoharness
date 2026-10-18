---
title: "Ship session memory: 218-S / 211-F post-merge closure and PR #536 delivery"
date: 2026-10-18
agent: ship
shipment: 218-S
feature: 211-F
---

# Ship session memory: 218-S / 211-F post-merge closure

## Outcome

* PR #536 merged as `03216ce0` (merge commit, two parents, ancestor of `origin/main`). 211-F delivered cascade-close durable journaling, `--detach` / `--poll` supervision (exits 9 and 10), safe stale-lock takeover only for a provably dead owner, and a provenance-marked, evidence-only `--recover`. It answers the 214-S incident (a killed wrapper left an `invoking` record and a stale pair lock).
* Closure executed under the just-merged shipment-reconcile contract (re-read before closing). Lifecycle topology gate exit 0; pre-mode PROCEED; Step 0(d) `agreed`; `--classify-only` exit 0 (CASCADE, engine VERIFIED on backlogit 1.11.0); the mutating `cascade-close` ran attached (`--timeout 2415` from N = 18 and the F = 800 / P = 45 formula, `--caller-wait 3015`) and exited 0 after about 16 minutes with postcondition `pass`. No `--recover`, no direct `backlogit shipment ship`.
* Linked-deliberation disposition: 041-DL `retained_description_mention`, nothing archived; post-mode PROCEED. The lifecycle lock was released right after post-mode.
* Closure record: `docs/closure/218-S-211-F-post-merge-closure.md` (READY). Evidence: `docs/closure/evidence/218-S-211-F-close-evidence.json` (phase `post_close`). Source stash retirement: none (neither 218-S nor 211-F declares `source_stash_id`).
* P-021 deferred captures from the PR: `967F9DC1`, `F0EF3FC2`, `50548692`, `B6D2B6FE`, `7CDE1693`, `E99F6EC9`, `F1AEC34D`, `EB8888A2`, `A22A7FD5`, `C3FBB38D`.

## PR delivery highlights

* Review: six local personas at `62f5c176` plus delta Correctness/Concurrency passes (`814971dc`, `71907548`); no P0/P1. P2 hardening fixed in the PR: hostile-JSON TypeError, attached shim child-pid journaling and spawn-window group kill, supervisor pre-spawn failure semantics, poll trust-walk and exit-0 corroboration.
* Copilot review ran four rounds; threaded findings were fixed or answered and resolved; P-018 gate `SATISFIED`.
* Design note kept in the PR: `recovery.supersedes_run_id` carries the original run id while the recovery record's own `run_id` is the recovery run id; the plan text equating them is stale.

## Linux CI port

* The first CI run failed on Linux in the process-liveness and open-writer logic. Fix: the Linux open-writer probe tolerates hidden same-uid helper processes that predate the journal, and foreign-uid fd tables no longer make the writer scan fail.
* Verification technique: re-run the cascade-close tests on Linux under WSL Ubuntu before pushing, instead of paying a CI round trip per attempt.
* A synthetic launcher test is skipped inside a venv, and the supervisor accepts a venv launcher between the foreground process and the real child.

## Flake fixes

* The live-supervisor poll test was made race-free; process-race tests were made deterministic under load (hold barrier, no timing assumptions).
* Detach exit assertions accept the finished-in-window outcome (`--detach` returns the final exit code when the supervised run finished inside the acknowledgement window) instead of asserting exit 9 only.
* Exit 9 (running) is exempt from the retry counter.

## Lessons

* Run the mutating `cascade-close` only attached under async with a declared `--caller-wait` of at least `--timeout` + 600 s, or `--detach` plus `--poll`; never abandon it early. This closure took about 16 minutes at N = 18.
* Expect pre-archived manifest members (211.011-T through 211.016-T): they are tolerated and absent from the engine's transition-log `archived_ids`.
* Write the Pre-Mode report before `--classify-only` so the Step 0(d) agreement check is meaningful.
* Date-named memory folders use the UTC date: this session's local date was 2026-10-17 but the UTC date was already 2026-10-18.
