# Ship session — 204-S / 198-F post-merge closure (2026-10-01)

## Outcome

* 204-S (195-F slice 3 of 6; covering feature 198-F; manifest `198-F`,
  `198.002-T` … `198.009-T`) delivered by PR #472. The operator approved the
  merge, which landed as merge commit `2770128a` (`--merge`, P-009). Final
  reviewed HEAD `1b605e8a`, `READY_WITH_FOLLOWUPS`, P0=0/P1=0. 2573 tests OK.
  CI green. P-018 copilot-review `SATISFIED`. The 198-S sequencing guard was
  re-verified pre-merge (198-S `queued`, `198-S → 201-S` `blocks`).
* Delivered: the P-015 close-path gate vs INV-12 split (U2b policy triples,
  assertions, rendered-region parity) and the skill engine-semantics gate
  (U3a): all-member Step 0(b) snapshot, Step 0(c) probe plus
  `select_close_path` routing, and the re-probe drift HALT in the cascade
  revalidation.
* Closure ran on `chore/204-s-closure`. The `pipeline-topology` lifecycle
  gate returned exit 0 (predecessor `203-S`, explicit).

## Interim rule A (operator decision 2026-10-01, stash 26D90B0F)

The skill stays authoritative for closure execution until slice 4 (199-F,
205-S) merges. Where P-015 and the skill conflict, the skill wins. Ship
followed the skill and did not edit policy or skill files. A comment was
appended to `26D90B0F` (`{"ok": true}`); the closure record is the durable
copy because comment events live in the git-ignored `.backlogit/logs/`.

## Close

* First closure to run the slice-3 Step 0(c) gate as the authoritative
  selector (not advisory). Probe `backlogit version --no-update-check
  --format json` on the CLI: `1.11.0` / `131577c` → `VERIFIED`. Classifier
  `CASCADE` (root `198-F`, no descendants, no linked deliberations) →
  `select_close_path` `CASCADE`.
* Pre-invocation revalidation re-probed the engine fresh and compared raw
  `version`, `commit`, `probe_surface` and verdict by exact string: no drift.
* `backlogit shipment ship 204-S --sha 2770128a…` exit 0 in about 6.5 minutes
  under the `.backlogit/queue/204-S.md` lock (00:34:21Z–00:41:04Z).
  `archived_ids` = the 8 tasks + `198-F` + `204-S`; `returned_ids` `[]`;
  both set differences empty; `parent_id` preserved; no out-of-scope tree
  change; `204-S` `archived_status: shipped`.
* 198-F T4: `linked_deliberation_disposition: step-not-yet-on-main
  (transition window); all retained`. No deliberation mutation.
* No `source_stash_id` / `source_deliberation_id` to retire. `backlogit sync`
  exit 0, `Indexed 1659 artifacts` → `CLOSURE_INDEX_SYNC_OK`.

## Learnings

* The 203-S scripted run adapted cleanly: replace the advisory
  `backlogit --version` parse with the JSON probe, branch on
  `select_close_path` instead of the bare classifier, and add the
  exact-string engine re-probe to the revalidation drift check.
* backlogit had already moved the eight tasks to `archive/` with
  `status: done` at task completion, so pre-mode classifies them
  `pre-archived` and `required_ids` still includes them (not truly
  `archived`).

## Follow-ups (Stage-owned, left active)

26D90B0F, 0C3EDC57, 218DF163, 4661F6AA, 049094FC, B31435CF, 56566173,
D6CCDE2C, 3C09D9D0, 6F2C4BFD, 013363F5, 492FB413.
