---
shipment: 149-S
feature: 141-F
tasks:
    - 141.001-T
    - 141.002-T
    - 141.003-T
    - 141.004-T
    - 141.005-T
feature_pr: 390
closure_pr: null
merge_commit: ca9059bf9c651b61c9d0a458568ffc798ff4cf91
merged_at: "2026-08-22T03:52:59Z"
reviewed_head: 2c81d136a8becdb69749b1dcd0435ba17525a70c
closure_merge_commit: null
closure_reviewed_head: null
closure_status: READY
compaction_status: done
conditions: []
---

# 149-S / 141-F Post-Merge Closure -- Full-Suite Test-Isolation Diagnosis and Ambient-CWD Decoupling

Shipment 149-S diagnosed the full-suite test-isolation pollution tracked as
stash `E8158860` and removed ambient-cwd coupling from all 58
`tempfile.TemporaryDirectory(dir=Path.cwd())` sites across 4 test modules.
Task `141.001-T` recorded a terminal `VERDICT: INCONCLUSIVE` (the prior
deliberation's own established fact -- that the three
`test_scope_containment_*` modules were the polluter -- was falsified by
this task's own mandatory re-check). `141.005-T` remains
pre-archived/superseded (split into `143.001-T`/`143.002-T`, shipment
151-S) and was not touched. Remediation of any confirmed polluter is out of
scope here -- that is 151-S's job (feature 143-F), gated on the recorded
diagnostic evidence.

## Merge Confirmation

- Feature PR #390 merged to `main` at `2026-08-22T03:52:59Z` with merge
  commit `ca9059bf9c651b61c9d0a458568ffc798ff4cf91`.
- Merge commit parents: `fb3e196a2c67b513be4637422b6c3658f9293744` (prior
  `main`) and `2c81d136a8becdb69749b1dcd0435ba17525a70c` (merged HEAD) --
  two parents confirmed via `git cat-file -p`; P-009 merge-commit strategy
  preserved (repo settings confirmed `allow_merge_commit: true`,
  `allow_squash_merge`/`allow_rebase_merge` both `false`).
- `git merge-base --is-ancestor ca9059bf... origin/main` confirmed exit 0.

## Pre-Merge Gate State (independently reverified)

| Gate | PR #390 |
| --- | --- |
| CI (`gh pr checks`) | `ci gate` pass, `detect code changes` pass, `pipeline-topology (ambient)` pass, `test` pass (reproduced at final HEAD `2c81d136`) |
| P-018 Copilot review (`autoharness gate copilot-review`) | `SATISFIED: PASS` (re-confirmed immediately before merge, unconditionally) |
| Copilot review threads | 1 thread, resolved |
| P-014 local review readiness | `## Local Review Readiness` block present at reviewed HEAD `2c81d136`, outcome `READY` |
| Operator merge authorization | Explicit: operator selected bugs `8FA8FC22`, `E8158860`, `F73BA065` and directed autonomous completion, explicitly authorizing normal merge-commit merges for this shipment and its closure PR |

## Review-Fix History

- Local review (code-review agent, pre-PR): READY. No P0/P1/P2 findings;
  two sub-P3 theoretical observations noted (no positional/variable
  `dir=` indirection site exists anywhere in `tests/` today; the guard
  scans `test_*.py` only, no non-`test_`-prefixed module currently exists).
- Copilot review on PR #390 (1 P1-equivalent thread): the isolation guard's
  scan used a non-recursive `test_*.py`-only glob, which would silently
  exempt a nested test package or non-`test_`-prefixed helper module from
  the guard's own stated "no module under tests/" invariant -- fixed by
  switching to `Path.rglob("*.py")` in commit `2c81d136`. Thread
  replied-to and resolved via GraphQL before merge.

## Runtime Verification

**Surface**: `cli` -- the only workspace-configured runtime validator
surface for this repository
(`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`).
This shipment touched only `tests/*.py` files (a new structural guard plus
mechanical `dir=` keyword edits across four existing test modules) and
official `.backlogit/` lifecycle metadata -- no `src/autoharness/` runtime,
API, or UI code changed.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` (`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`) |
| Runtime probe | `uv run autoharness --help` |
| Result | **PASS** -- exit 0 |
| Canonical gate | `uv run python -m unittest discover -s tests` |
| Result | `Ran 1722 tests, FAILED (failures=3, errors=2, skipped=20)` -- all 5 are the pre-existing, already-diagnosed (this shipment's own 141.001-T) `E8158860` full-suite test-isolation failures; identical failing test IDs reproduced before and after this shipment's work, confirmed by 141.001-T's own baseline capture and the feature-level AC-F1 re-measurement after 141.004-T |
| Hosted CI | `ci gate`, `detect code changes`, `pipeline-topology (ambient)`, `test` -- all green at final HEAD `2c81d136` |
| Manual checkpoints | none required -- test-suite-only artifact, no user-facing or operational behavior change |
| Blocked prerequisites | none |
| Verdict | **PASS** for runtime-verification purposes; the 5 pre-existing failures are tracked for remediation by 151-S (feature 143-F), gated on this shipment's `VERDICT: INCONCLUSIVE` diagnostic record |

### Other Gates

- Full build: non-applicable in the compiled-artifact sense; this
  shipment changed only test modules -- no compiled build step applies.
  The canonical test suite above is the full local build evidence.
- `tests/test_test_suite_isolation_contract.py`: GREEN with an EMPTY
  allowlist -- zero `dir=Path.cwd()` sites remain anywhere under `tests/`.
- Quality Gates 1-4: PASS (no YAML frontmatter or template surfaces
  touched; markdown structure intact for the compound learning doc edit;
  no `{{VAR}}` placeholders involved; all cross-referenced files exist).

## Backlog Reconciliation (P-015)

`classify_shipment_close_path(['141-F', '141.001-T', '141.002-T',
'141.003-T', '141.004-T', '141.005-T'], '.backlogit')` -> **CASCADE**
(`141-F` is a root, fully covered by all five manifest-member children,
including the pre-archived `141.005-T`).

`backlogit shipment ship 149-S --sha ca9059bf...` returned `archived_ids`
including an out-of-manifest deliberation (`024-DL`, linked to `141-F` only
via a plain `references` list entry, never a `parent_id` edge) -- the THIRD
observed occurrence of the same known engine-behavior surprise documented in
`docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`
(first: 143-S/134-F/019-DL; second: 148-S/140-F/025-DL, the immediately
preceding shipment in this same session). Applied the identical documented
remediation: reverted only `024-DL` (confirmed byte-identical to its
pre-cascade state via empty `git diff` and `backlogit get 024-DL` reporting
`status: queued` unchanged), then independently re-verified all remaining
post-conditions.

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` (after excluding the reverted `024-DL`) | exact match: `141.001-T`, `141.002-T`, `141.003-T`, `141.004-T`, `141-F`, `149-S` |
| `141.005-T` | untouched (already archived/pre-existing before this cascade; correctly absent from `archived_ids` since no action was required) |
| `parent_id` preservation | all four freshly-archived tasks' `parent_id` re-read as `141-F`, unchanged from the Step 0(b) pre-close snapshot |
| Live status | `141-F` archived (`archived_status: done`; `status: archived`); `149-S` archived (`archived_status: shipped`) |
| `024-DL` | restored to pre-cascade state, `status: queued`, byte-identical (`git diff` empty) |

`backlogit shipment ship 149-S --sha ca9059bf...` was used in place of
manual safe-close, per the P-015 verified fully-covered-root exception.
This is the third observed occurrence of the out-of-manifest linked-
deliberation surprise, spanning three shipments over two calendar days;
recorded as a new disposition section on the existing compound learning doc
rather than a duplicate entry.

## Operational Closure

- **Invariants to preserve**: `tests/test_test_suite_isolation_contract.py`
  continues to assert an EMPTY allowlist and zero `dir=Path.cwd()` sites
  anywhere under `tests/` (recursively); a future test author reintroducing
  the anti-pattern anywhere under `tests/` will fail this guard immediately.
- **Pre-deploy audits**: not applicable -- this shipment changed only test
  modules and official backlog metadata; no migration, feature flag,
  configuration, or access-control surface was touched.
- **Deployment / rollout path**: merge-only. The guard takes effect for any
  future contributor's next local or CI test run the moment `main` is
  synced; there is no separate deploy, canary, or phased-rollout step for
  this artifact class.
- **Risky action record**: not applicable -- no `ProposedAction` entries
  requiring approval, containment, or rollback beyond the standard
  operator-approved merge-commit-only merge (P-009) were taken.
- **Post-deploy checks**: re-run `uv run python -m unittest tests.test_test_suite_isolation_contract`
  after `main` sync and confirm 4/4 pass with an empty allowlist; re-run the
  canonical full-suite gate and confirm exactly the same 5 pre-existing
  `E8158860` failures (no new failures).
- **Healthy signals**: PR #390 merged with a verified 2-parent merge
  commit; P-018 `SATISFIED` at final HEAD; the 1 Copilot review thread
  resolved before merge; backlog cascade-close archived exactly the
  manifest's task, feature, and shipment records (after reverting the one
  out-of-manifest deliberation sweep) with no other unintended archival;
  repo merge-strategy settings confirmed merge-commit-only.
- **Failure signals to watch**: a future PR reintroducing
  `tempfile.TemporaryDirectory(dir=Path.cwd())` anywhere under `tests/`
  would regress `tests/test_test_suite_isolation_contract.py` immediately.
  151-S's remediation work should watch for the supplementary
  `BranchOwnershipTests`-order pollution finding recorded on `141.004-T` --
  a distinct, pre-existing, unrelated-to-ambient-cwd defect discovered
  incidentally, not yet root-caused.
- **Monitoring plan**: none required beyond the post-deploy checks above;
  this is a one-time diagnostic-plus-hygiene shipment, not an ongoing
  runtime rollout requiring dashboards, alerts, or SLI monitoring.
- **Validation window**: immediate, at this post-merge closure (2026-08-21).
- **Rollback trigger**: revert merge commit `ca9059bf...` if any of the 58
  anchored/converted `TemporaryDirectory` sites is later found to have
  altered its own test's observed behavior (contradicting the AIG's
  isolation-pass-count-parity guarantee).
- **Rollback procedure**: `git revert` the `149-S`/`141-F` feature merge
  commit (`ca9059bf...`) on `main` through a new reviewed PR.
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for
  merge approval and release follow-up routing.
- **Releasability evidence**: **READY**
  (`.autoharness/workspace-profile.yaml` `runtime_validation.releasability`:
  `required: false`, `status_when_satisfied: READY`, `required_evidence: []`
  -- no additional evidence beyond the runtime verification above is
  required for this workspace). Verified merge commit (two parents), green
  CI, P-018 `SATISFIED`, P-015 cascade-close independently re-verified
  (including the `024-DL` revert), and P-020 compaction pending completion
  below. No condition is outstanding beyond compaction.
- **Residual follow-up (non-blocking)**:
  1. `141.001-T`'s `VERDICT: INCONCLUSIVE` (P-021/`E8158860` tracked) --
     remediation is 151-S's scope (feature 143-F), gated on this recorded
     verdict; not actioned by Ship per the role boundary.
  2. Compound learning:
     `docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`
     third-occurrence disposition added -- the Stage-owned follow-up to add
     a bounded, documented tolerance to the Cascade Close Sub-Procedure's
     step 3 exact-match check remains open, now reinforced by three
     independent observations.
  3. The supplementary `BranchOwnershipTests`-order intra-file pollution
     finding recorded on `141.004-T` (distinct from the ambient-cwd work;
     unrelated root cause, not identified within this shipment's scope) --
     informational for 151-S.

## Compaction (P-020)

`compact-context --target all` was invoked as part of this closure session.
This shipment's own session memory qualified under the completed-work rule
(the guaranteed Tier-1 consolidation floor). Compacted summary written to
`docs/memory/compacted/2026-08-21-149s-141f-compacted.md`, consolidating
the verbose original now at
`docs/archive/memory/2026-08-21-ship-149-s-execution-and-closure-session.md`.
No compaction degradation or failure signal.

**Closure verdict: READY.** Runtime verification passed, the 1 Copilot
review thread was resolved before merge, backlog cascade-close is complete
and independently re-verified (including the `024-DL` revert), and P-020
compaction is `done`. The residual follow-ups (`141.001-T`'s
`VERDICT: INCONCLUSIVE`, the supplementary `BranchOwnershipTests`-order
finding, and the third cascade recurrence) are tracked under Stage/Ship
role separation and do not block this READY verdict.
