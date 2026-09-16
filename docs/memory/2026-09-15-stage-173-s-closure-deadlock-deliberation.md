# Stage session — 2026-09-15 — coupled deliberation of FBD2F6BE + 2B42392E (173-S closure deadlock)

## Scope

Operator-requested bounded deliberation of exactly two active stash entries.
No implementation, no source/template/schema mutation, no shipment
claim/close, no PR, no unrelated triage.

## Outcome

One coupled decision, recorded at
`docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md`.

**Root cause (shared by both findings):** the shipment-closure contract models
closure over a LIVE backlog — live covering feature, live unshipped siblings,
live shipment record transitioning `active → shipped`. It has no model for a
**fully-terminal closure**, where the whole closure scope was already archived
before closure began. FBD2F6BE is that assumption failing on the protected set;
2B42392E is the same assumption failing on the record transition.

**Decision:** adopt `TERMINAL_CLOSE`, a third machine-checkable close
classification (fail-closed; defaults to `SAFE_CLOSE` on any ambiguity, never to
`CASCADE`), plus a generalized terminal-descope protected-set exemption.
Implementation is REQUIRED before 173-S can be safely closed.

**Post-condition deviation handling (Constitution Principle VII):** a
`TERMINAL_CLOSE` post-condition deviation NEVER triggers an automatic or
immediate `git restore`. The mandated sequence is fail-closed: capture evidence
(observed `archived_ids`, git diff vs. the Step 3 baseline, affected IDs) →
HALT with no further mutation → emit P-005 → request explicit operator approval
→ perform a repository-approved rollback ONLY after approval. Silent
auto-restore is prohibited.

## Key evidence gathered

* Safe-close Step 2/3 confirmed: descoped siblings `165.007-T`/`165.010-T`
  (archived, `archived_status: blocked`, `parent_id: 165-F`, descoped in commits
  `2744359a`/`730c3fc5` predating Ship's claim) land in the protected set; the
  existing sequence-aware exclusion requires `shipped`/`done` provenance and so
  does not apply. Step 3 halts.
* `classify_shipment_close_path` walks the full descendant graph across
  `queue/`+`archive/`, so `165-F` is not fully covered → forced `SAFE_CLOSE`,
  which forbids the cascade. Deadlock confirmed on both sides.
* **Spike (isolated `%TEMP%` workspace, destroyed afterwards; no branch, no
  worktree, repo untouched):** `move --status shipped` and `update --status
  shipped` both refused with exit 9; `archive` of an active shipment stamps
  `archived_status: active` (fails Step 8's provenance gate); `shipment ship` is
  the ONLY path to `archived_status: shipped`, with no `--no-cascade` flag.
* **Blast-radius measurement on a 173-S-shaped mirror:** the out-of-manifest
  descoped sibling was left byte-identical; the already-archived manifest task
  untouched; the feature gained only `commit:` traceability; `archived_ids` was
  `[feature, shipment]`. P-015 protects LIVE artifacts, and 173-S has none.
* **Archive-provenance survey (1029 records):** `done`-without-provenance is
  366 records, including all 11 of 173-S's manifest members. Terminality checks
  must accept `done|archived|shipped`, never "declares `status: archived`".

## Backlog mutations

* Created feature `166-F`; tasks `166.001-T`..`166.006-T` (all sized on both
  axes: 2×M, 4×S; complexity high×3, medium×2, low×1).
* Dependencies: `166.002-T`→`166.001-T`→`166.005-T` (also gated by
  `166.003-T`); `166.006-T` gated by `166.004-T` and `166.005-T`.
* Created shipment `174-S` (queued, high) with all 7 harvested IDs, covering
  feature first. Manifest verified: `unsized: 0`, nothing skipped. `174-S` is a
  PLANNING HANDOFF RECORD ONLY — not executable, not claimable (see Next steps).
* Stash `FBD2F6BE` and `2B42392E` reconciled in place (P-021 C5: clean duplicate
  scans recorded; PR #451 added as recovered late identifier; `task`/
  `review-thread` `N/A` verified structurally truthful and left standing), then
  archived as consumed with forward references.
* `3CA122AC` deliberately LEFT ACTIVE — separate occurrence of the same class,
  not the same expansion; linked as co-beneficiary via `166.002-T`/`166.006-T`.

## Untouched (deliberately)

`173-S` (still `active`), `165-F`, all 11 manifest members, `165.007-T`,
`165.010-T`. No `parent_id` cleared. Step 5 verify-after-each invariant not
weakened. Pre-existing dirty working-tree files preserved; nothing committed.

## Next steps

1. Operator decision on the P-001 sequencing overlap: Ship must execute `174-S`
   while `173-S` remains `active`-but-blocked (173-S is a closure-record remnant;
   all its work is merged).
2. **`174-S` IS NOT EXECUTABLE OR CLAIMABLE.** Its `queued` status is a planning
   handoff record only, and its fail-closed unsequenced state (no `dag_root`, no
   declared dependencies, no bootstrap grant) is intentional and preserved
   as-is. Ship MUST NOT claim it until ALL of the following hold: (a) `impl-plan`
   has produced a plan for `166-F`; (b) MANDATORY `plan-harden` has run (P-006 —
   policy + skill + classifier + template-mirror blast radius; not optional
   here); (c) `plan-review` has returned a passing verdict on the hardened plan;
   (d) a valid DAG declaration exists, OR an operator-authored bootstrap grant
   has been issued; (e) explicit P-001 authority has been granted for the
   sequencing overlap in item 1. Stage grants none of these; (d) and (e) are
   operator-owned.
3. After `174-S` ships, Ship RE-RUNS `shipment-reconcile` safe-close for `173-S`
   from Step 0/1 in full — not resuming at Step 8.
4. Follow-up: classify `168-S` (3CA122AC) once the new path exists; optional
   upstream backlogit request for a genuine non-cascading close.
