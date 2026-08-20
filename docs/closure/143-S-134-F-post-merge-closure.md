---
shipment: 143-S
feature: 134-F
auxiliary_feature: 135-F
auxiliary_task: 135.001-T
feature_pr: 373
merge_commit: e2af4dfe1b403b85cab7f237a4f7f9b621370d70
merged_at: "2026-08-20T11:09:47Z"
reviewed_head: 10c266bec7fba69b8f27d134068f2fcded531e5a
closure_status: READY
compaction_status: done
conditions: []
---

# 143-S / 134-F Post-Merge Closure — P-021 Bounded Fix-Cycle Scope Containment and Deferred Expansion Capture

Shipment 143-S authored workflow policy **P-021** (bounded fix-cycle scope
containment and deferred expansion capture) and carried it coherently across
the Ship/Stage agent templates, circuit-breaker instruction, PR-automation
instruction, role-enforcement instruction, and `fix-ci`/`pr-lifecycle` skill
templates, backed by three new contract test suites
(`test_scope_containment_boundary_contract.py`,
`test_scope_containment_policy_contract.py`,
`test_scope_containment_semantics_contract.py`).

A separately-authorized **auxiliary CI-unblocker** unit rode the same branch
and PR: feature `135-F` / task `135.001-T` (forward-authorized under P-021 C4
via deliberation `020-DL` from deferred stash `D71F6283`), fixing a
pre-existing, unrelated PowerShell checklist-rendering truncation defect that
was blocking PR #373's required `test`/`ci gate` checks. Deliberately
excluded from 143-S's manifest and P-015 protected set per its own task
instructions.

## Merge Confirmation

- PR #373 merged to `main` at `2026-08-20T11:09:47Z` with merge commit
  `e2af4dfe1b403b85cab7f237a4f7f9b621370d70`.
- Merge commit parents: `94898dc7f05d394350427b732b1269ce38dee36b` (prior
  `main`) and `10c266bec7fba69b8f27d134068f2fcded531e5a` (merged HEAD) — two
  parents confirmed via `git log -1 --format=%P`; P-009 merge-commit strategy
  preserved.
- `git merge-base --is-ancestor e2af4dfe... origin/main` confirmed exit 0.
- Closure began from synced `main` at `e2af4dfe...` (fast-forward
  `94898dc7..e2af4dfe`, 66 files changed).

## Pre-Merge Gate State (independently reverified)

| Gate | Result |
| --- | --- |
| CI (`gh pr checks 373`) | all 4 required checks `pass` (`ci gate`, `detect code changes`, `pipeline-topology (ambient)`, `test`) |
| P-018 Copilot review | `SATISFIED` |
| P-014 local review readiness | `READY_WITH_FOLLOWUPS`, P0=0 / P1=0 |
| `mergeStateStatus` | `CLEAN` |

## Implementation Summary

**134-F / 143-S** — 13 tasks (`134.001-T`..`134.013-T`) implementing P-021
across policy text, Ship/Stage agent instructions, circuit-breaker and
PR-automation instructions, role-enforcement, and the `fix-ci`/`pr-lifecycle`
skill templates, plus three new contract test suites totaling ~2,400 lines.
Review-fix cycle 1 resolved 8 Copilot findings in commit `10c266be` (the
merged HEAD).

**135-F / 135.001-T** (auxiliary, P-021 C4 forward-authorized) — preserved
full `RecommendedAction` literals in the pre-merge-install checklist report
under redirected/non-TTY stdout in `scripts/deploy-harness.ps1` (and its
template mirror `templates/scripts/deploy-harness.ps1.tmpl`), unblocking the
required `test`/`ci gate` checks. Fix commit `a19dd072`. `scripts/deploy-harness.sh`
left byte-unchanged (already correct; the sh renderer uses fixed-width
`printf` and was never defective).

## Validation

- Canonical gate: `PYTHONPATH=src python -m unittest discover -s tests` →
  **1677 passed, 20 skipped** (0 failures).
- Runtime smoke: `uv run autoharness --help` → exit 0.
- Full build: non-applicable in the CLI-tool/template sense beyond the
  canonical test suite above (no compiled build step for this stack pack);
  the canonical suite is this workspace's full-build equivalent and is
  recorded as such.
- Quality Gates 1-4: PASS (YAML frontmatter valid across all `.tmpl`/`.md`
  changes; markdown structure intact; zero `{{VAR}}` placeholders in resolved
  templates; all cross-referenced files/skills/agents exist).

## Backlog Reconciliation

`classify_shipment_close_path(["134-F", "134.001-T".."134.013-T"], ".backlogit")`
returned **CASCADE** (134-F verified fully-covered root).

1. Topology gate (`autoharness gate pipeline-topology --phase lifecycle`)
   → `exit_code: 0` immediately before the cascade mutation.
2. `backlogit shipment ship 143-S --sha e2af4dfe...` → `returned_ids: []`;
   `archived_ids` unexpectedly also included `019-DL` (a deliberation linked
   via `134-F.custom_fields.source_deliberation_id`, not a `parent_id` child
   — the classifier's coverage check only walks `parent_id` hierarchy and
   could not have predicted this engine-side reference-link cascade
   behavior).
3. Per the Cascade Close Sub-Procedure's step 3 exact-match verification,
   halted on the extra ID, reverted **only** the unintended `019-DL`
   archival (confirmed restored to its exact pre-cascade `status: queued`
   state via `git diff` producing no output), and retained the legitimate
   archival of the 13 tasks + `134-F` + `143-S` (independently re-verified
   exact-match, `parent_id: 134-F` preserved on all tasks, `returned_ids: []`).
   See `docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`
   for the full analysis and Stage-owned follow-up recommendation.
4. Gate decision: **CLOSED** (post-remediation).

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` (post-remediation) | exact match: 13 tasks + `134-F` + `143-S` |
| Out-of-scope archive caught and reverted | `019-DL` |
| `parent_id` preservation | confirmed unchanged (`134-F`) on all 13 tasks |
| Live status | `143-S` → `shipped` → archived (`archived_status: shipped`); `134-F` archived (`archived_status: done`) |
| Protected set | none — verified fully-covered root has no protected set by construction |
| `135-F` / `135.001-T` | closed on their own path (queued/active → done → commit-tracked → archived), never touched by 143-S's cascade mutation |
| `020-DL` (auxiliary deliberation), stashes `6D62077C`/`3C7AAC71` | untouched throughout |
| Protected git stash `operator-work-before-ship-143-S` | untouched throughout — safe for the Orchestrator to restore now that all Ship-owned closure work is complete |

## Source Artifact Cleanup (post-merge Step 7)

Per the Ship Role Boundary ("retire the source stash entry that fed the
shipped scope via `backlogit_stash_remove` on `custom_fields.source_stash_id`
at post-merge Step 7") and `templates/agents/_ship.agent.md.tmpl`'s
"Source artifact cleanup" step, processed for the sole shipped top-level item
in 143-S's scope, `134-F`:

* `custom_fields.source_stash_id: B48A482A` — checked `backlogit stash list`:
  **already removed** (not present in the active stash list; its record
  carries a `[CONSUMED 2026-08-18 by Stage: ... harvested]` annotation from
  prior Stage triage). Skipped, logged here.
* `custom_fields.source_deliberation_id: 019-DL` — verified it exists
  (`status: queued`, i.e. not yet archived at the time of this check — its
  earlier out-of-scope cascade archival, see above, had already been
  reverted back to `queued` before this explicit Step 7 check ran). Archived
  via `backlogit archive 019-DL` → confirmed `status: archived`,
  `archived_status: queued`.

Auxiliary top-level item `135-F` carries no `custom_fields.source_stash_id`
or `custom_fields.source_deliberation_id` (its stash/deliberation provenance
— `D71F6283` / `020-DL` — is recorded only in description prose, not
structured custom fields); no Step 7 action applies to it.

Committed on
`post-merge/134-f-p-021-bounded-fix-cycle-scope-containment-and-deferred-expansion-capture`
per the Post-Merge Branch Protocol (closure mutations never land directly on
`main`).

## Operational Closure

- **Healthy signals**: PR #373 merged with a verified 2-parent merge commit;
  full canonical test suite green (1677 passed, 20 skipped, 0 failures);
  all 4 required CI checks green; P-018 `SATISFIED`; P-014
  `READY_WITH_FOLLOWUPS` (P0=0/P1=0); backlog reconciliation completed via
  the classifier-selected CASCADE path with an out-of-scope archival anomaly
  caught, reverted, and disclosed rather than silently accepted or
  overreacted to.
- **Failure signals to watch**: none identified specific to this shipment's
  functional scope. The cascade-close engine-behavior surprise (see compound
  doc) is a process/tooling residual, not a functional regression.
- **Validation window**: immediate post-merge closure on 2026-08-20 after
  `main` synced to merge commit `e2af4dfe...`, merged at
  `2026-08-20T11:09:47Z`.
- **Rollback trigger**: revert merge commit `e2af4dfe...` if a P-021
  contract test proves incorrect against real fix-cycle behavior in a future
  session, or if the auxiliary checklist-rendering fix (`135.001-T`)
  regresses the sh renderer or template/instance parity.
- **Owner**: Ship agent for closure evidence; operator for merge approval and
  release follow-up routing (autonomous completion pre-authorized for this
  session per explicit operator direction, applied to the closure PR only
  after all mandatory gates below passed).
- **Residual follow-up (non-blocking)**:
  1. Stash `6D62077C` remains open for Stage triage.
  2. External stash `3C7AAC71` remains open.
  3. New residual: extend `classify_shipment_close_path` and/or the Cascade
     Close Sub-Procedure to account for `custom_fields`-only reference links
     (e.g. `source_deliberation_id`), not just `parent_id` hierarchy edges,
     when determining the `archived_ids` exact-match post-condition — see
     the compound doc above. Stage-owned; no backlog item opened by Ship
     (P-010).

## Compaction (P-020)

`compact-context --target all` invoked per the mandatory per-merge trigger.
This shipment's own session memory
(`docs/memory/2026-08-20-ship-143-s-full-lifecycle-closure.md`) qualifies
under the completed-work rule regardless of age; compacted summary written to
`docs/memory/compacted/2026-08-20-143S-134F-compacted.md`.

**Closure verdict: READY.** Runtime verification passed; backlog
reconciliation completed via the classifier-selected CASCADE path with the
one out-of-scope-artifact anomaly independently caught, reverted, and fully
disclosed; source artifact cleanup (post-merge Step 7) completed —
`019-DL` properly archived and `B48A482A` confirmed already removed; the
auxiliary 135-F/135.001-T unit closed cleanly on its own path outside the
143-S manifest/protected set; the protected operator git stash was never
touched.
