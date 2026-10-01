# Ship session — 202-S / 196-F post-merge closure (2026-09-30)

## Outcome

* 202-S (195-F slice 1 of 6; covering feature 196-F; manifest `196-F`,
  `196.001-T` … `196.008-T`) delivered by PR #468, merged by operator approval
  as merge commit `f45086f2` (`--merge`, P-009). Final reviewed HEAD
  `a287ab9f`, `READY_WITH_FOLLOWUPS`, P0=0/P1=0. 2527 tests OK (54 skipped).
  CI green. P-018 copilot-review `SATISFIED` at `a287ab9f`.
* Delivered code (inert on main, no runtime caller): U1a
  `assess_cascade_engine_semantics` + `select_close_path` (CASCADE only when
  the classifier says CASCADE AND the engine is a released 1.11.x probed on
  the invocation surface); U1b read-only INV-12
  `compute_linked_deliberation_disposition` planner core.
* Closure ran on `chore/202-s-closure` (direct pushes to `main` are rejected
  by rulesets).

## Close path

* `classify_shipment_close_path` → `CASCADE` (qualifying `196-F`, no
  out-of-manifest descendants, no validated linked deliberations — 196-F is
  T2 deliberation-clean). Pre-invocation revalidation: no drift.
* `backlogit shipment ship 202-S --sha f45086f2…` (backlogit 1.11.0) exit 0;
  `archived_ids` = all 9 manifest items + `202-S`; `returned_ids: []`. Both
  two-set checks PASS, `parent_id` preserved, whole-tree diff shows no
  out-of-scope change, record `archived_status: shipped`. Post-mode PROCEED.
* All of pre-mode → cascade → post-mode ran in one scripted pass under the
  `.backlogit/queue/202-S.md` file lock (token held in-process only).
* Observation: the cascade took ~8 minutes of CPU-bound engine time for 10
  artifacts (per-item "index may be stale after mutation" logs). Not a
  failure; budget for it in future closes.

## Learnings

* The globally installed `autoharness.exe` (`C:\Python\Python314\Scripts`) is
  stale: it lacks the `gate closure-evidence` subcommand that `src/` registers.
  Run that gate as `uv run autoharness gate closure-evidence …` from the repo.
* With the 195-F alignment work still in flight, the pre-195 contract remains
  authoritative for closes; the slice's new gate/planner have no runtime
  caller, so they did not participate.

## Follow-ups (untouched, Stage-owned)

* P-021 deferred entries `D6CCDE2C`, `3C09D9D0`, `6F2C4BFD`, `013363F5`,
  `492FB413` remain active.
* Next: 203-S (195-F slice 2 of 6, 197-F), `queued`, blocked-on 202-S (now
  shipped). Not touched in this session.
