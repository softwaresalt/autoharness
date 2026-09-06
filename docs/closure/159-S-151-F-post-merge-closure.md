---
shipment: 159-S
feature: 151-F
tasks:
    - 151.001-T
    - 151.002-T
    - 151.003-T
    - 151.004-T
    - 151.005-T
    - 151.006-T
    - 151.007-T
feature_pr: 435
additional_prs:
    - 434
merge_commit: cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab
merged_at: "2026-09-06T05:24:43Z"
reviewed_head: 494089ab638a7d111618ff6f9fd30febbc635934
closure_status: READY_WITH_CONDITIONS
compaction_status: done
conditions:
    - description: "Operator authorizes removal/disposition of the stale, unowned .backlogit/queue/.159-S.md.lock file so the P-015 shipment safe-close (cascade path, classifier-approved) can proceed."
      satisfied: false
      evidence: "pending operator decision"
---

# 159-S / 151-F Post-Merge Closure -- SHIP-1 v1.5.0 Shipped-Guardrail Contract Restoration

Canonical machine-readable post-merge closure record for shipment `159-S`
(feature `151-F`, 7 tasks) satisfying the
`docs/closure/{shipment_id}-*-post-merge-closure.md` discovery contract
used by `autoharness gate pipeline-topology`'s `closure_complete()` reader
(`src/autoharness/gates/topology.py`).

## Merge Confirmation

- Feature PR #435 ("feat: SHIP-1 v1.5.0 shipped-guardrail contract
  restoration (159-S)") merged to `main` with merge commit
  `cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab` (parents `05bbfc2f` and
  `494089ab` -- two parents, P-009 merge-commit strategy preserved).
- Confirmed present on `origin/main` via
  `git merge-base --is-ancestor cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab origin/main`
  (exit 0).
- An earlier PR in this shipment's lifecycle, #434
  ("chore(backlog): publish 159-S checkpoint waiver"), merged first
  (`05bbfc2f`) and is a parent of #435's merge commit.

## Authoritative Evidence (referenced, not duplicated)

- `docs/closure/2026-09-06-159-s-151-f-closure.md` -- operational-closure
  narrative: CI status, affected runtime surface, risky-action record (none),
  deployment path (merge-only), pre/post-deploy checks, healthy/failure
  signals, monitoring plan, rollback trigger/procedure, validation window,
  owner, and the open lock-disposition condition. Releasability verdict:
  **READY_WITH_CONDITIONS**.
- `docs/closure/2026-09-06-159-s-151-f-runtime-verification.md` -- runtime
  validator evidence for the `cli` surface. Verdict: **PASS**.
- `docs/memory/compacted/2026-09-06-159s-151f-compacted.md` -- compacted
  P-020 session memory (verbose original archived under
  `docs/archive/memory/2026-09-05/`).

## Backlog Reconciliation (P-015) -- OPEN CONDITION

The classifier (`src/autoharness/gates/shipment_closure.py`
`classify_shipment_close_path`) was run against the live workspace for
manifest `["151-F", "151.001-T".."151.007-T"]` and returned
**`ClosePath.CASCADE`** ("every feature member is a verified fully-covered
root; cascade close is permitted", qualifying feature `151-F`). The cascade
close (`backlogit shipment ship 159-S`) has **not yet been executed**: the
`shipment-reconcile` skill's single-writer lock
(`.backlogit/queue/159-S.md`) could not be acquired --
`.backlogit/queue/.159-S.md.lock` already exists, is empty (does not carry
the expected agent/timestamp/pid fields), and is dated 2026-09-03 (over 2.5
days before this closure attempt, and this Ship session did not create it).
Per the file-lock skill's non-negotiable lock hygiene rule, only the
operator may force-break a lock they did not create; this agent halted the
safe-close step at that gate rather than override it. `159-S` and `151-F`
therefore remain `status: active` in `.backlogit/queue/` pending operator
disposition of the stale lock and a follow-up completion of the cascade
close.

## Stash Disposition (P-021)

`151-F` declares no `custom_fields.source_stash_id` /
`custom_fields.source_deliberation_id` -- outcome `none` for both (see the
Source Artifact Cleanup section of the operational-closure artifact for the
full informational cross-check of the informally-referenced stash IDs
`053E2BD2` and `B698F01B`, neither of which was retired).

One emergent out-of-scope finding was captured as P-021 stash entry
`24A85BF8` (unrelated flaky `test_graphtor_mcp_shim.py` test) for Stage's
retrospective review; it does not block this release's runtime
releasability.

## Compaction (P-020)

`compaction_status: done` -- `compact-context --target all` was invoked
during this post-merge closure; the fresh PR #434 circuit-breaker memory
(the guaranteed post-merge candidate) was compacted into
`docs/memory/compacted/2026-09-06-159s-151f-compacted.md`, verbose original
archived under `docs/archive/memory/2026-09-05/`.

## Releasability Evidence

**Closure verdict: READY_WITH_CONDITIONS.** The shipped code change is fully
released and verified (CLI surface `PASS`, no rollback trigger observed,
Copilot review `SATISFIED`, local review `READY`). The single open condition
is procedural backlog bookkeeping (P-015 cascade close blocked by a stale
lock file), not a defect in the shipped functionality. This condition must
be resolved (`satisfied: true` with evidence) and this frontmatter updated
before `closure_complete('159-S')` registers `True` for any successor
shipment's predecessor-closure readiness check.
