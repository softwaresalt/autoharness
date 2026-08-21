---
shipment: 145-S
feature: 137-F
tasks:
    - 137.001-T
    - 137.002-T
    - 137.003-T
    - 137.004-T
pre_archived_manifest_members:
    - 137.005-T
    - 137.006-T
feature_pr: 384
closure_pr: 385
merge_commit: a1bce32f5f0173d82d8ac1301c66876e6b177356
merged_at: "2026-08-21T15:26:51Z"
reviewed_head: 124fcdaaed31599b4806dc1a364d333a04c81a71
closure_status: READY
compaction_status: done
conditions: []
---

# 145-S / 137-F Post-Merge Closure -- Harness Consistency: Template/Dogfood Paired-Edit Contract + Stash-Archive Migration

Shipment `145-S` executed feature `137-F` (stash `6D62077C` + stash
`8D570CF8`): authored the formal template/dogfood paired-edit maintenance
contract, pinned the divergent pair set with a fail-closed membership
assertion, and migrated Ship's post-merge Step 7 stash-retirement operation
off the deprecated `backlogit_stash_remove` to the canonical
`backlogit_stash_archive` across the Ship agent contract, dogfood mirror,
verifier, contract tests, manifest checksum, P-021 C5 policy clause, and
backlog registry template.

## Merge Confirmation

- Feature PR #384 merged to `main` at `2026-08-21T15:26:51Z` with merge
  commit `a1bce32f5f0173d82d8ac1301c66876e6b177356`.
- Merge commit parents: `ee823a15f3efd486a5d25a10e54d08c8946ac5a6` (prior
  `main`, 144-S closure) and `124fcdaaed31599b4806dc1a364d333a04c81a71`
  (merged HEAD) -- two parents confirmed via `git cat-file -p`; P-009
  merge-commit strategy preserved (repo settings: `allow_merge_commit: true`,
  `allow_squash_merge`/`allow_rebase_merge` both `false`).
- `git merge-base --is-ancestor a1bce32f... origin/main` confirmed exit 0.

## Executable Task Set / Manifest Classification

Manifest `custom_fields.items`: `137-F`, `137.002-T`, `137.001-T`,
`137.003-T`, `137.004-T`, `137.005-T`, `137.006-T`.

| Item | Classification | Disposition |
| --- | --- | --- |
| `137.002-T` | task, `queued` at claim (execution order: first) | executable, kept, done |
| `137.001-T` | task, `queued` at claim (depends on 137.002-T) | executable, kept, done |
| `137.003-T` | task, `queued` at claim (depends on 137.002-T; atomic migration) | executable, kept, done |
| `137.004-T` | task, `queued` at claim (order-independent) | executable, kept, done |
| `137.005-T` | task, `archived` (`[SUPERSEDED by 137.003-T]`) | `pre_archived_skipped` -- never claimed, moved, unarchived, or removed |
| `137.006-T` | task, `archived` (`[SUPERSEDED by 137.003-T]`) | `pre_archived_skipped` -- never claimed, moved, unarchived, or removed |
| `137-F` | covering feature (resolved via `parent_id`), not a task artifact | excluded from the executable set derivation; handled by cascade close below |

No `already_done`, no fail-closed anomalies. Execution order followed the
feature-level directive: `137.002-T` -> `137.001-T` -> `137.003-T`, then
order-independent `137.004-T`.

## Pre-Merge Gate State (independently reverified)

| Gate | PR #384 |
| --- | --- |
| CI (`gh pr checks`) | `ci gate` pass, `detect code changes` pass, `pipeline-topology (ambient)` pass, `test` pass |
| P-018 Copilot review (`autoharness gate copilot-review`) | `SATISFIED` at HEAD `124fcdaa` |
| Copilot review threads | 1 thread, `isResolved: true` (reply posted citing fixing commit) |
| P-009 merge strategy | merge-commit only, two parents confirmed |
| P-014 local review readiness | PR body carries the Local Review Readiness block at reviewed HEAD `124fcdaa`, outcome `READY` |

## Review-Fix History

- Self-review (code-review subagent, pre-PR, at HEAD `a337e47e`): found and
  fixed **P0** -- a stray corrupted trailing line
  (`++ .github/agents/_ship.agent.md`) accidentally appended to
  `.github/agents/_ship.agent.md` by a patch-tool artifact during
  `137.003-T`'s edit, and baked into that commit's manifest-checksum
  refresh. Removed the stray line, recomputed the checksum from the
  corrected LF-normalized staged git blob, re-reviewed clean.
- Copilot hosted review on PR #384, round 1 (1 finding, fixed in commit
  `124fcdaa`): Copilot correctly identified that
  `_EXPECTED_DIVERGENT_PAIR_MANIFEST_PATHS` in
  `tests/test_scope_containment_policy_contract.py` was derived from
  `_DIVERGENT_MARKER_ONLY_PAIRS` itself, making the fail-closed membership
  assertion vacuous (both sides changed together on any mutation). Fixed by
  hardcoding the expected set as an independent literal; verified locally
  that the guard now correctly fails on both a simulated removal and a
  simulated addition. Thread replied-to (citing the fixing commit) and
  resolved via GraphQL before merge.

## Runtime Verification

**Surface**: `cli` -- the only workspace-configured runtime validator
surface for this repository
(`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`).
This shipment touched `src/autoharness/verify_workspace.py` (a single
`must_contain` marker string), templates, tests, and documentation -- no new
CLI command, API, or UI behavior.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` (`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`) |
| Runtime probe | `uv run autoharness --help` |
| Result | **PASS** -- exit 0 |
| Canonical gate | `uv run python -m pytest tests/ -q` |
| Result | `1677 passed, 20 skipped, 1116 subtests passed` -- 5 pre-existing failures, all the already-deferred (P-021 stash entry `E8158860`) full-suite test-isolation-pollution finding; confirmed unrelated (all 5 pass individually/in isolation on both `main` and this branch; reproduces identically before and after this shipment's own new test module was added) |
| `uv run autoharness verify-workspace --workspace .` | 0 blockers, 0 warnings -- identical to the pre-existing baseline on `main` before this shipment (verified via `git stash`/isolated re-run); the pre-existing `unresolved: 83` placeholder count and handful of missing-file targeted-check failures are unchanged baseline noise (spike F5, explicitly deferred), not introduced here |
| Hosted CI | `ci gate`, `detect code changes`, `pipeline-topology (ambient)`, `test` -- all green on PR #384 at final HEAD |
| Manual checkpoints | none required -- no user-facing or operational runtime behavior change |
| Blocked prerequisites | none |
| Verdict | **PASS** for runtime-verification purposes; the 5 pre-existing failures are tracked as a follow-up (stash `E8158860`), not a blocker |

### Other Gates

- Full build: `uv run python -m pytest tests/ -q` (see above) is the
  canonical build/test gate for this repository.
- Quality Gates 1-4: PASS (YAML frontmatter valid for the new design doc;
  markdown structure intact; zero unresolved `{{VAR}}` placeholders in the
  changed templates -- no new template variables introduced by this change,
  so the install-harness variable-resolution table required no update;
  all cross-referenced files/skills/agents exist).

## Bookkeeping Anomaly and Repair (session-local)

During execution, a `git stash`/`git stash pop` cycle used to establish the
pre-existing full-suite test-isolation baseline (E8158860) reverted the
on-disk `.backlogit/queue/*.md` files for this shipment and its four
executable tasks back to their pre-claim state, even though the actual
deliverables were already correctly committed to git. Detected via the Step
4 lifecycle `pipeline-topology` gate reporting `LIFECYCLE_NO_ACTIVE_SHIPMENT`
despite `backlogit`'s own claim command refusing a reclaim (`active to
active: shipment status conflict`), confirming the desync was file-only, not
a real competing claim. Repaired by re-running the `queued -> active -> done`
transitions for all four tasks (correctly re-archived with `status: done`)
and correcting the shipment record's status field directly, followed by a
full `backlogit sync`; verified via the lifecycle gate (exit 0) and
`backlogit get`/`shipment get` returning consistent status for all seven
manifest members before proceeding. Committed separately
(`54c41b14`, "chore(145-S): repair backlogit bookkeeping state desync") with
no task deliverable, test, or template file touched. Recorded here as a
process learning; see the compound learning below.

## Backlog Reconciliation (P-015)

`classify_shipment_close_path(['137-F', '137.002-T', '137.001-T',
'137.003-T', '137.004-T', '137.005-T', '137.006-T'], '.backlogit')` ->
**CASCADE** (`137-F` is a root, fully covered by all six manifest-member
children -- including the two already-archived, pre-archived
`137.005-T`/`137.006-T` -- and the manifest contains nothing beyond the
qualifying root + children).

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` | exact match: `137.001-T`, `137.002-T`, `137.003-T`, `137.004-T`, `137-F`, `145-S` |
| `parent_id` preservation | all four executable tasks' `parent_id` re-read as `137-F`, unchanged |
| Live status | `137-F` archived (`archived_status: done`); `145-S` archived (`archived_status: shipped`) |
| Pre-existing archived members | `137.005-T`/`137.006-T` untouched throughout (`archived_status: queued`, unchanged from their pre-shipment frozen state) -- never claimed, moved, unarchived, or removed |

`backlogit shipment ship 145-S --sha a1bce32f...` was used in place of
manual safe-close, per the P-015 verified fully-covered-root exception
(same exception applied to `144-S`/`146-S`).

`backlogit doctor` (62 pre-existing findings, none touching `137-*`,
`145-S`, or any ID from this session's predecessor chain `136-*`, `138-*`,
`144-S`, `146-S`, `147-S`) and `backlogit queue view --type shipment`
(empty -- no claimable shipment remains) confirm a clean post-close state.

## Source Stash Retirement

Both source stashes `6D62077C` and `8D570CF8` were confirmed absent
(`backlogit stash get` returns "not found" for both) at session start --
Stage had already reconciled them in place during harvest before this
shipment's execution began, per the traceability sections of the spike
(`docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md`) and
deliberation
(`docs/decisions/2026-08-20-ship-stash-archive-operation-migration-deliberation.md`)
documents. No `backlogit_stash_archive` action was performed or required
this session for either source stash.

## Operational Closure

- **Invariants to preserve**: the pre-archived manifest members
  (`137.005-T`, `137.006-T`) must never be claimed, moved, unarchived, or
  removed by any future work touching this feature's history; the
  divergent-pair membership assertion in
  `tests/test_scope_containment_policy_contract.py` must remain an
  independent literal, never re-derived from `_DIVERGENT_MARKER_ONLY_PAIRS`
  (the exact Copilot-caught regression this shipment fixed); Ship's
  post-merge Step 7 must continue to name `backlogit_stash_archive`, never
  the deprecated `backlogit_stash_remove`, as a prescriptive execution path.
- **Pre-deploy audits**: not applicable -- this shipment changed templates,
  a verifier marker string, test modules, a policy clause, a registry
  mapping, and one new design document; no migration, feature flag,
  configuration, or access-control surface was touched.
- **Deployment / rollout path**: merge-only. The renamed stash-retirement
  operation and the pinned divergent-pair inventory take effect the moment
  `main` is synced; there is no separate deploy, canary, or phased-rollout
  step for this artifact class.
- **Risky action record**: not applicable -- no `ProposedAction` entries
  requiring approval, containment, or rollback beyond the standard
  operator-approved merge-commit-only merge (P-009) were taken.
- **Post-deploy checks**: re-run
  `autoharness gate pipeline-topology --mode agent --shipment <next-shipment-id>
  --phase pre_claim --json` for the next queued shipment and confirm
  `exit_code: 0` (predecessor closure evidence for `145-S` -- this artifact
  -- now present).
- **Healthy signals**: PR #384 merged with a verified 2-parent merge
  commit; P-018 `SATISFIED` at final HEAD; the one Copilot review thread
  resolved before merge; backlog cascade-close archived exactly the
  manifest's tasks, feature, and shipment records with no unintended
  archival or requeue; repo merge-strategy settings confirmed
  merge-commit-only.
- **Failure signals to watch**: any future template/dogfood paired-edit
  should re-check the divergent-pair membership test after editing
  `_DIVERGENT_MARKER_ONLY_PAIRS` -- the Copilot-caught vacuous-assertion
  pattern (deriving both sides of a fail-closed check from the same source)
  is a general hazard worth watching for in other contract tests.
- **Monitoring plan**: none required beyond the one-time post-deploy check
  above; the pinned membership test and the verifier marker now run on every
  future `tests/` invocation.
- **Validation window**: immediate post-merge closure, 2026-08-21, the same
  day as PR #384's merge.
- **Rollback trigger**: revert merge commit `a1bce32f...` if the
  `backlogit_stash_archive` rename produces an operational failure (e.g. if
  `backlogit_stash_archive` is later found not to be reachable in some
  installed workspace configuration) or if the divergent-pair membership
  assertion produces false positives against a legitimate future
  eighth-plus paired-edit pair.
- **Rollback procedure**: `git revert` the `145-S`/`137-F` feature merge
  commit (`a1bce32f...`) on `main` through a new reviewed PR; this reverts
  the Ship contract, dogfood mirror, verifier marker, contract tests,
  manifest checksum, policy clause, and registry mapping back to naming
  `backlogit_stash_remove`, and removes the new maintenance-contract
  document and the divergent-pair membership pin. `backlogit_stash_remove`
  remains reachable as a deprecated MCP tool / CLI alias, so a revert would
  not itself break anything -- it would simply re-expose the deprecated
  surface this shipment retired.
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for
  merge approval and release follow-up routing.
- **Releasability evidence**: **READY**. All required evidence is present:
  verified merge commit (two parents), green CI, P-018 `SATISFIED`, P-015
  cascade-close independently re-verified, and P-020 compaction evidence
  (`compaction_status: done`) backed by durable compacted/archived memory
  files. No condition is outstanding.
- **Residual follow-up (non-blocking)**:
  1. P-021 deferred stash entries `E8158860` (full-suite test-isolation
     pollution), `F73BA065`, `90F2A9F8`, and `8FA8FC22` remain open; require
     Stage deliberation (C6), not actioned by Ship per the role boundary.
  2. A new deferred stash entry, captured by Stage during the `6D62077C`
     spike (spike finding F5): `autoharness.verify_workspace._derive_template_variables`
     does not cover every `{{VAR}}` the shipped templates use, leaving
     unresolved placeholders after rendering. This is a genuine,
     separate installation-correctness defect already captured before this
     Ship session began; explicitly out of scope per the spike's own
     "Explicitly out of scope" section and per this shipment's manifest.
     Not actioned here; requires Stage deliberation.
  3. Compound learning:
     `docs/compound/2026-08-21-backlogit-shipment-status-file-desync-after-git-stash.md`
     -- documents the bookkeeping-anomaly finding and repair procedure above
     as a durable, generalizable pattern for future sessions that need to
     `git stash`/`git stash pop` mid-shipment.

## Compaction (P-020)

`compact-context --target all` was invoked per the mandatory per-merge
trigger during this closure work (the `templates/skills/compact-context/SKILL.md.tmpl`
authored contract, since this self-hosting repository has no resolved
`.github/skills/compact-context/` copy). This shipment's own session
memory qualified under the completed-work rule; compacted summary written
to `docs/memory/compacted/2026-08-21-145S-137F-compacted.md`, consolidating
the verbose original at
`docs/archive/memory/2026-08-21-ship-145-s-execution-and-closure-session.md`.
Neither artifact records a compaction degradation or failure signal.

**Closure verdict: READY.** Runtime verification passed, the one Copilot
review thread was resolved before merge, backlog cascade-close is complete
and independently re-verified, both source stashes were already retired by
Stage prior to this session, and outstanding P-021 follow-ups remain
correctly tracked as Stage's to deliberate.
