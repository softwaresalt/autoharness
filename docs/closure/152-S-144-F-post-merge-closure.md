---
shipment: 152-S
feature: 144-F
tasks:
    - 144.001-T
    - 144.002-T
    - 144.003-T
    - 144.004-T
    - 144.005-T
    - 144.006-T
    - 144.007-T
feature_pr: 398
closure_pr: null
merge_commit: f0cad43c04ad98809685db0fb247db1e9a287bb6
merged_at: "2026-08-22T23:05:49Z"
reviewed_head: ef96eb72f88e529f4212ed4b02b5a532ad8fc977
closure_merge_commit: null
closure_reviewed_head: null
closure_status: READY_WITH_CONDITIONS
compaction_status: done
conditions:
    - "PRRT_kwDORzpWpM6bb2je: control-flow-insensitive alias tracking in _EnvMutationVisitor (P2, accepted operator-directed residual risk, not a P-021 C2 capture)"
---

# 152-S / 144-F Post-Merge Closure -- Contain Ambient GIT_CONFIG_* Environment Destruction on Windows (Mechanism A)

Shipment 152-S implemented mechanism A of the E8158860 remediation chain:
containing ambient `GIT_CONFIG_*` Windows environment-variable destruction
that could corrupt the test-suite's own subprocess environment. All 7
planned tasks (`144.001-T`-`144.007-T`) were completed per
`docs/plans/2026-08-22-git-config-env-containment-plan.md` and its
hardening amendments: explicit L0/L1/L2 Windows process topology with
blank-sentinel seeding, `tests/_env_patch.py` restore-by-diff helper,
migration of all 13 planned bulk `os.environ` mutation sites, an empty
structural-guard allowlist (including the helper itself), a narrowly-shaped
`GIT_CONFIG` normalizer, and canonical unittest discovery in-process under
a controller with before/after child probes, a mandatory negative control,
byte/per-key equality, and canonical subprocess count equivalence.

## Merge Confirmation

- Feature PR #398 merged to `main` at `2026-08-22T23:05:49Z` with merge
  commit `f0cad43c04ad98809685db0fb247db1e9a287bb6`.
- Merge commit parents: `d6c9568c1c28da88f86ce482e9e397afd24e7514` (prior
  `main`, itself the merge of staging PR #397) and
  `ef96eb72f88e529f4212ed4b02b5a532ad8fc977` (merged feature HEAD) -- two
  parents confirmed via `git cat-file -p`; P-009 merge-commit strategy
  preserved (repo settings confirmed `allow_merge_commit: true`,
  `allow_squash_merge`/`allow_rebase_merge` both `false`).
- `git merge-base --is-ancestor f0cad43c... origin/main` confirmed exit 0.

## Pre-Merge Gate State (independently reverified)

| Gate | PR #398 |
| --- | --- |
| CI | green at final HEAD `ef96eb72` (Windows canonical suite: 1830 tests, failures=0, errors=0, skipped=20; Linux CI parity confirmed) |
| P-018 Copilot review (`autoharness gate copilot-review`) | `SATISFIED` (re-confirmed immediately before merge, unconditionally) |
| Copilot review threads | 4 rounds, 9 total findings: 8 fixed across rounds 1-3 (5+2+1 -- see below), 1 round-4 finding (the 9th) accepted as residual risk rather than fixed; all threads replied-to and resolved |
| P-014 local review readiness | `## Local Review Readiness` block present at reviewed HEAD `ef96eb72`, outcome `READY_WITH_FOLLOWUPS` (1 P2 residual finding) |
| Operator merge authorization | Explicit: operator selected bug `E8158860`, directed autonomous end-to-end completion, and explicitly delegated the round-4 disposition (accept as residual risk, do not perform a 4th fix cycle) |

## Review-Fix History

- Round 1 (5 findings, commit `b35d5d74`): fixed and resolved (threads
  `PRRT_kwDORzpWpM6bBC`/`BN`/`BZ`/`Bi`/`B1`, abbreviated).
- Round 2 (2 findings, commit `18d4619f`): a class-scope LEGB bug in the
  `_EnvMutationVisitor` AST guard (class bodies incorrectly treated as
  enclosing scopes for their own methods) plus a stale PR-body HEAD.
  Threads `PRRT_kwDORzpWpM6bbvrW`/`bbvro` resolved.
- Round 3 (1 finding, commit `ef96eb72`): a decorator/header scope-
  ordering bug in the same visitor (decorators visited inside the
  function's own new scope, and after the body, due to AST field order).
  Thread `PRRT_kwDORzpWpM6bbykS` resolved.
- Round 4 (1 finding, `PRRT_kwDORzpWpM6bb2je`, control-flow-insensitive
  alias tracking): the 3-cycle review-fix budget (Stop Conditions table)
  was already exhausted. Classified P-021 C1 in-scope but P2 severity
  (no live exploit in the repo today; guard remains fully sound for every
  existing offending shape). Ship halted and escalated per protocol;
  operator explicitly directed acceptance as documented residual risk
  rather than authorizing a 4th fix cycle. Replied-to (citing the
  disposition rationale) and resolved without a code change.
- Full technical detail of the three fixed LEGB-scoping bugs and the
  round-4 residual-risk rationale:
  `docs/compound/2026-08-22-ast-scope-aware-alias-resolution-legb-pitfalls.md`.

## Runtime Verification

**Surface**: `cli` -- the only workspace-configured runtime validator
surface for this repository
(`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`).
This shipment's primary surface is `tests/*.py` modules (env-mutation
containment, the AST structural guard, and the restore-by-diff helper).
One task (`144.006-T`) also made a production fix in
`src/autoharness/gates/topology.py`, stopping the `_run_git` git-
infrastructure-failure path from being laundered into a false domain
diagnosis (assertion-integrity hardening for the existing
`pipeline-topology` gate's `check-ignore` invocation) -- this is a
defensive diagnostics correction to existing gate code, not a new runtime
surface or behavior change to the gate's pass/fail semantics.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` (`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`) |
| Runtime probe | `uv run autoharness --help` |
| Result | **PASS** -- exit 0 |
| Canonical gate | `uv run python -m unittest discover -s tests` (Windows) |
| Result | `Ran 1830 tests, OK (skipped=20)` -- 0 failures, 0 errors, at final reviewed HEAD `ef96eb72` |
| Hosted CI | green at final HEAD `ef96eb72`; Linux CI parity independently confirmed |
| Manual checkpoints | none required -- primarily a test-tooling artifact with one defensive diagnostics fix in existing gate code; no user-facing or operational behavior change |
| Blocked prerequisites | none |
| Verdict | **PASS** for runtime-verification purposes; mechanism A of the E8158860 chain is fully implemented and proven green on the canonical Windows suite |

### Other Gates

- Full build: non-applicable in the compiled-artifact sense; this
  shipment's changes are Python source (test-suite tooling plus one small
  gate-code diagnostics fix) with no separate compiled build step. The
  canonical test suite above is the full local build evidence.
- Quality Gates 1-4: PASS (no YAML frontmatter or template surfaces
  touched by the feature change itself; markdown structure intact for
  the compound learning doc; no `{{VAR}}` placeholders involved; all
  cross-referenced files exist).

## Backlog Reconciliation (P-015)

`classify_shipment_close_path(['144-F', '144.001-T', ..., '144.007-T'],
'.backlogit')` -> **CASCADE** (`144-F` is a root, fully covered by all 7
manifest-member children; manifest contains nothing beyond the qualifying
root feature and its children).

`backlogit shipment ship 152-S --sha f0cad43c...` was used in place of
manual safe-close, per the P-015 verified fully-covered-root exception.

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` | exact match: `144.001-T`..`144.007-T`, `144-F`, `152-S` -- nothing more, nothing less |
| `parent_id` preservation | all 7 tasks re-read with `parent_id: 144-F`, unchanged from the Step 0 pre-close snapshot |
| Live status | `144-F` archived (`archived_status: done`; `status: archived`); `152-S` archived (`archived_status: shipped`) |

No out-of-manifest linked-deliberation sweep was observed this time (the
recurring surprise documented in
`docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`
did not recur for this shipment's manifest).

## Operational Closure

- **Invariants to preserve**: the L0/L1/L2 Windows process topology and
  the `tests/_env_patch.py` restore-by-diff helper must continue to fully
  restore `os.environ` byte-for-byte after every mutating test; the
  `_EnvMutationVisitor` structural guard's empty allowlist must remain
  empty (any future addition requires an explicit, reviewed exemption);
  the accepted round-4 residual risk (control-flow-insensitive alias
  tracking) means a conditional/branch-dependent import alias could still
  theoretically bypass the guard -- no such pattern exists in the repo
  today, but this should be re-assessed if one is ever introduced.
- **Pre-deploy audits**: not applicable -- this shipment's changes are
  test-suite tooling, one defensive diagnostics fix in existing gate code
  (`src/autoharness/gates/topology.py`, `144.006-T`), and official backlog
  metadata; no migration, feature flag, configuration, or access-control
  surface was touched.
- **Deployment / rollout path**: merge-only. The containment mechanism
  takes effect for any future contributor's next local or CI test run the
  moment `main` is synced; no separate deploy, canary, or phased-rollout
  step.
- **Risky action record**: not applicable -- no `ProposedAction` entries
  requiring approval, containment, or rollback beyond the standard
  operator-approved merge-commit-only merge (P-009) were taken.
- **Post-deploy checks**: re-run the canonical full-suite gate
  (`uv run python -m unittest discover -s tests`) after `main` sync and
  confirm `1830 tests, OK (skipped=20)` persists with no regressions.
- **Healthy signals**: PR #398 merged with a verified 2-parent merge
  commit; P-018 `SATISFIED` at final HEAD; all resolvable review threads
  fixed and resolved across 3 cycles, with the 4th accepted as documented
  residual risk per explicit operator disposition; backlog cascade-close
  archived exactly the manifest's 7 tasks, the feature, and the shipment
  record, with no unintended archival; repo merge-strategy settings
  confirmed merge-commit-only.
- **Failure signals to watch**: any future report of an `os.environ`
  mutation escaping containment on Windows, or any conditional-import
  pattern near `os.environ` mutation code that could exploit the accepted
  round-4 control-flow-insensitivity gap.
- **Monitoring plan**: none required beyond the post-deploy checks above;
  this is a one-time test-tooling hardening shipment, not an ongoing
  runtime rollout requiring dashboards, alerts, or SLI monitoring.
- **Validation window**: immediate, at this post-merge closure
  (2026-08-22).
- **Rollback trigger**: revert merge commit `f0cad43c...` if the
  containment mechanism is later found to alter test behavior outside its
  intended scope (contradicting the assertion-integrity gate's isolation
  guarantee), or if it fails to actually contain a reproduction of the
  original E8158860 ambient-corruption pattern.
- **Rollback procedure**: `git revert` the `152-S`/`144-F` feature merge
  commit (`f0cad43c...`) on `main` through a new reviewed PR.
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt`
  for merge approval and release follow-up routing.
- **Releasability evidence**: **READY_WITH_CONDITIONS**
  (`.autoharness/workspace-profile.yaml` `runtime_validation.releasability`:
  `required: false`, `status_when_satisfied: READY`, `required_evidence: []`
  -- no additional evidence beyond the runtime verification above is
  required for this workspace). Verified merge commit (two parents),
  green CI, P-018 `SATISFIED`, P-015 cascade-close independently
  re-verified, and P-020 compaction `done` (see below). The single
  outstanding condition is the accepted round-4 residual-risk finding
  (`PRRT_kwDORzpWpM6bb2je`), which is non-blocking and does not gate
  release.
- **Residual follow-up (non-blocking)**:
  1. `PRRT_kwDORzpWpM6bb2je`: the `_EnvMutationVisitor` structural guard's
     alias tracking is not control-flow-aware (both branches of an
     `if`/`else` are visited into the same mutable scope dict). No
     current test file exploits this shape and the guard fully covers
     every existing offending pattern; recommended future hardening is to
     make the tracker treat an ambiguously-bound name (bound differently
     across reachable branches) as its most permissive/forbidden
     candidate origin. Accepted as documented residual risk by explicit
     operator disposition; not a P-021 C2 capture (the finding passed C1).
  2. Shipment 153-S (mechanism B, `BranchOwnershipTests` intra-file order
     pollution) remains `queued`, blocked on 152-S's own completion per
     its dependency declaration, and was explicitly NOT claimed in this
     invocation. It is now eligible for the Orchestrator to reload `main`
     and re-check.
  3. The Ship resume checkpoint for this session
     (`checkpoint-20260822-232506.json`) is resolved as part of this
     closure PR -- no active recovery candidate is left for this
     completed work.

## Compaction (P-020)

`compact-context --target all` was invoked as part of this closure
session. This shipment's own session memory qualified under the
completed-work rule (the guaranteed Tier-1 consolidation floor).
Compacted summary written to
`docs/memory/compacted/2026-08-22-152s-144f-compacted.md`, consolidating
the verbose original now at
`docs/archive/memory/2026-08-22-ship-152-s-mechanism-a-shipped-closed.md`.
No compaction degradation or failure signal.

**Closure verdict: READY_WITH_CONDITIONS.** Runtime verification passed,
all resolvable review threads were fixed and resolved across 3 review-fix
cycles, the 4th finding was accepted as documented residual risk per
explicit operator disposition, backlog cascade-close is complete and
independently re-verified, and P-020 compaction is `done`. The single
outstanding condition (round-4 residual risk) is non-blocking and does not
gate release. Shipment 153-S remains queued and unclaimed.
