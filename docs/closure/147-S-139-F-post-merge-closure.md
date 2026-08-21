---
shipment: 147-S
feature: 139-F
tasks:
    - 139.001-T
    - 139.002-T
feature_pr: 379
closure_pr: 380
merge_commit: f57d0f0c50f2ea005a688e91ebf42f4decda51cd
merged_at: "2026-08-21T11:37:53Z"
reviewed_head: 08607503edb076b4b36a54d69ce31a07b3412692
closure_merge_commit: 91afda32b5b1393ffa736e9e4d340c4b559d3bf6
closure_reviewed_head: c9968b41c202ef9513b72d4e4ae8fe7898547456
closure_status: READY
compaction_status: done
conditions: []
---

# 147-S / 139-F Post-Merge Closure -- Ship Execution Contract Excludes Pre-Archived Manifest Members

Shipment 147-S changed Ship's Task Execution Loop to derive its **executable
task set** from live task records (filter to task artifacts by the
configured task-ID suffix, then keep `queued`/`active`, skip-and-report
`archived` members as `pre_archived_skipped` distinct from `already_done`,
and fail-closed halt on any other/missing/unreadable status) instead of
iterating the shipment manifest unconditionally. The manifest remains the
closure-membership record only, byte-for-byte unchanged. This unblocks
`144-S`/`145-S`, whose manifests carry pre-archived, superseded children
alongside queued/active ones.

## Merge Confirmation

- Feature PR #379 merged to `main` at `2026-08-21T11:37:53Z` with merge
  commit `f57d0f0c50f2ea005a688e91ebf42f4decda51cd`.
- Merge commit parents: `e1a42a702d9a6ebd391a1c049e80d4fbcb3a605c` (prior
  `main`) and `08607503edb076b4b36a54d69ce31a07b3412692` (merged HEAD) -- two
  parents confirmed via `git show --no-patch --format='%H %P'`; P-009
  merge-commit strategy preserved.
- `git merge-base --is-ancestor f57d0f0c... origin/main` confirmed exit 0.
- Post-merge closure PR #380 merged to `main` at `2026-08-21T12:09:20Z` with
  merge commit `91afda32b5b1393ffa736e9e4d340c4b559d3bf6` (parents
  `f57d0f0c50f2ea005a688e91ebf42f4decda51cd` + `c9968b41c202ef9513b72d4e4ae8fe7898547456`,
  two parents confirmed).

## Pre-Merge Gate State (independently reverified)

| Gate | PR #379 (feature) | PR #380 (closure) |
| --- | --- | --- |
| CI (`gh pr checks`) | `ci gate` pass, `detect code changes` pass, `pipeline-topology (ambient)` pass, `test` pass | `ci gate` pass, `detect code changes` pass, `pipeline-topology (ambient)` pass, `test` skipped (docs-only, no code change detected) |
| P-018 Copilot review (`autoharness gate copilot-review`) | `SATISFIED: PASS` | `SATISFIED: PASS` |
| Copilot review threads | 3 threads, all `isResolved: true` | 2 threads, all `isResolved: true` |

## Review-Fix History

- Local review (code-review agent, pre-PR): returned READY on the first
  commit of PR #379 -- the contract text was internally coherent, but this
  scope did not catch the wiring/execution-semantics defects Copilot later
  found.
- Copilot review round 1 on PR #379 (2 P1s): (1) the template's new
  derivation was described but never wired into the actual queue Step 4
  iterates -- fixed by making the derived set explicitly replace the
  queued-only membership; (2) the new Step 0.5 item 6 intake-reconciliation
  reference mandated a single `expected_status` that `shipment-reconcile
  mode: pre` cannot satisfy for a legitimately mixed queued+active manifest
  -- fixed with a scope note limiting the check to uniform-status intake.
  Both fixed in commit `f065106b`.
- Copilot review round 2 on PR #379, re-armed on push (1 P1): the round-1
  fix hard-coded the dogfood `-T` task-ID suffix into the **template**,
  breaking any installation with a different configured task suffix -- fixed
  by using the already-defined `{{SUFFIX_TASK}}` variable, in commit
  `08607503`. All 3 threads replied-to (citing the fixing commit) and
  resolved via GraphQL before merge.
- Copilot review on PR #380 (2 P1s): (1) the closure narrative hard-coded
  the dogfood suffix as if it were the portable contract, contradicting the
  portability fix it was documenting -- corrected to describe the
  configured/resolved task suffix instead; (2) the new compound-learning
  entry omitted required searchable frontmatter metadata
  (`problem_type`/`category`/`root_cause`/`tags`) -- corrected to match the
  compound workflow's frontmatter contract. Fixed in commit `c9968b41`. Both
  threads replied-to and resolved via GraphQL before merge.

## Runtime Verification

**Surface**: `cli` — the only workspace-configured runtime validator
surface for this repository
(`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`).
This shipment touched `.github/agents/_ship.agent.md`,
`templates/agents/_ship.agent.md.tmpl`, `.autoharness/harness-manifest.yaml`,
and a new test module only — no `src/autoharness/` runtime, API, or UI code
changed.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` (`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`) |
| Runtime probe | `uv run autoharness --help` |
| Result | **PASS** — exit 0 (reproduced at time of this correction, current `main`) |
| Canonical gate | `PYTHONPATH=src python -m unittest discover -s tests` |
| Result | `Ran 1687 tests ... FAILED (failures=3, errors=2, skipped=20)` — all 5 are the pre-existing, already-deferred (P-021 stash entry `E8158860`) full-suite test-isolation failures (`test_gate_pipeline_topology_cli`, `test_gates_topology`, `test_repo_root_artifacts`, `test_telemetry_gitignore_template` x2); confirmed unrelated (no `src/` change in either PR #379 or #380; each test passes in isolation; CI's Linux `test` job was green on PR #379) |
| Hosted CI | `ci gate`, `detect code changes`, `pipeline-topology (ambient)`, `test` — all green on PR #379; PR #380's `test` job correctly reported `skipping` (docs-only, no code change detected) |
| Manual checkpoints | none required — docs-only artifact, no user-facing or operational behavior change |
| Blocked prerequisites | none |
| Verdict | **PASS** for runtime-verification purposes; the 5 pre-existing failures are tracked as a follow-up (stash `E8158860`), not a blocker |

### Other Gates

- Full build: non-applicable in the CLI-tool/template sense beyond the
  canonical test suite above; this shipment changed only
  `.github/agents/_ship.agent.md`, `templates/agents/_ship.agent.md.tmpl`,
  `.autoharness/harness-manifest.yaml`, and a new discriminating regression
  test module (`tests/test_ship_pre_archived_manifest_members.py`) -- no
  compiled build step applies.
- Quality Gates 1-4: PASS (YAML frontmatter valid; markdown structure
  intact; zero `{{VAR}}` placeholders in resolved templates; all
  cross-referenced files/skills/agents exist).

## Backlog Reconciliation (P-015)

`classify_shipment_close_path(['139-F', '139.001-T', '139.002-T'],
'.backlogit')` -> **CASCADE** (`139-F` is a root, fully covered by both
manifest-member children; the manifest contains nothing beyond the
qualifying root + children).

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` | exact match: `139.001-T`, `139.002-T`, `139-F`, `147-S` |
| `parent_id` preservation | `139.001-T.parent_id` / `139.002-T.parent_id` re-read as `139-F`, unchanged |
| Live status | `139-F` archived (`archived_status: done`); `147-S` archived (`archived_status: shipped`) |
| Backlog queue | `144-S` confirmed still present in `.backlogit/queue/144-S.md`, untouched by this cascade |

`backlogit shipment ship 147-S --sha f57d0f0c...` was used in place of
manual safe-close, per the P-015 verified fully-covered-root exception.

## Operational Closure

- **Invariants to preserve**: the manifest (`custom_fields.items`) remains
  the closure-membership record only and is never mutated by the executable
  task set derivation; an `archived` manifest member is always
  skip-and-reported, never reactivated.
- **Pre-deploy audits**: not applicable — this shipment changed only Ship
  agent instruction files and a test module; no migration, feature flag,
  configuration, or access-control surface was touched.
- **Deployment / rollout path**: merge-only. Ship's instruction files take
  effect the moment `main` is synced by a future Ship session; there is no
  separate deploy, canary, or phased-rollout step for this artifact class.
- **Risky action record**: not applicable — no `ProposedAction` entries
  requiring approval, containment, or rollback beyond the standard
  operator-approved merge-commit-only merge (P-009) were taken by either
  PR #379 or PR #380.
- **Post-deploy checks**: re-run
  `autoharness gate pipeline-topology --mode agent --shipment 144-S --phase
  pre_claim --json` after `main` sync and confirm `exit_code: 0` (see
  Verification under Correction Provenance below for the first observation
  of this check against the working-tree copy of this file).
- **Healthy signals**: both PR #379 and PR #380 merged with verified
  2-parent merge commits; P-018 `SATISFIED` on both PRs at final HEAD; all
  Copilot review threads (5 total across both PRs) resolved before merge;
  backlog cascade-close archived exactly the manifest's task, feature, and
  shipment records with no unintended archival; repo merge-strategy settings
  confirmed merge-commit-only (`allow_merge_commit: true`,
  `allow_squash_merge`/`allow_rebase_merge` both `false`).
- **Failure signals to watch**: a future contract change to Ship's Task
  Execution Loop must preserve the "derived set replaces the consumed queue,
  not sits beside it" wiring -- `tests/test_ship_pre_archived_manifest_members.py`
  should catch a regression here; and any new agent-template literal must
  use the existing `{{SUFFIX_*}}` variable family rather than a hardcoded
  dogfood-installation token (see the compound learning below).
- **Monitoring plan**: none required beyond the one-time post-deploy check
  above; this is a retroactive documentation artifact for an
  already-archived shipment, not an ongoing runtime rollout requiring
  dashboards, alerts, or SLI monitoring.
- **Validation window**: immediate post-merge closure was intended for
  2026-08-21 after PR #380 merged at `2026-08-21T12:09:20Z`; this specific
  closure artifact's validation window is the correction below, performed
  the same day once the gap was discovered by the `144-S` pre-claim topology
  gate.
- **Rollback trigger**: revert merge commit `f57d0f0c...` if the executable
  task set derivation causes Ship to skip a legitimately `queued`/`active`
  task, or reactivate an `archived` one, in a future shipment execution.
- **Rollback procedure**: `git revert` the `147-S`/`139-F` feature merge
  commit (`f57d0f0c...`) on `main` through a new reviewed PR; the executable
  task set derivation would revert to unconditional manifest iteration.
  Separately, if only *this correction* needs to be undone (e.g. a future
  audit finds a factual error in this artifact), revert this correction's
  own merge commit — that action alone re-triggers
  `PREDECESSOR_CLOSURE_INCOMPLETE` on `144-S`'s pre-claim gate without
  touching `147-S`'s underlying shipped state.
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for
  merge approval and release follow-up routing.
- **Releasability evidence**: **READY**. All required evidence for this
  docs-only retroactive closure-artifact correction is present: verified
  merge commits (both PRs, two parents each), green CI, P-018 `SATISFIED`
  on both PRs, P-015 cascade-close independently re-verified, and P-020
  compaction evidence (`compaction_status: done`) backed by durable
  compacted/archived memory files. No condition is outstanding.
- **Residual follow-up (non-blocking)**:
  1. P-021 deferred stash entry `E8158860` (full-suite test-isolation
     pollution, Windows-only) remains open; requires Stage deliberation
     (C6), not actioned by Ship per the role boundary.
  2. Compound learning: `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md`
     -- a described derivation is not a wired derivation; local review can
     confirm internal textual coherence without simulating execution
     against the specific variable a later, unedited step consumes by name.

## Compaction (P-020)

`compact-context --target all` was invoked per the mandatory per-merge
trigger during the original PR #380 closure work. This shipment's own
session memory qualified under the completed-work rule; compacted summary
written to `docs/memory/compacted/2026-08-21-147S-139F-compacted.md`,
consolidating the verbose original at
`docs/archive/memory/2026-08-21-ship-147-s-execution-and-closure-session.md`.
Neither artifact records a compact-context degradation or failure signal --
the compacted summary's reference to pre-existing P-021 stash entry
`E8158860` is a residual-follow-up citation, not a compaction-run defect.

**Closure verdict: READY.** Runtime verification passed, all 5 Copilot
review threads (3 on PR #379, 2 on PR #380) were resolved before their
respective merges, backlog cascade-close is complete and independently
re-verified, and the P-021 full-suite test-isolation follow-up remains
tracked as stash entry `E8158860` under Stage/Ship role separation.

## Correction Provenance

**This artifact was authored retroactively, in a dedicated correction
session, not as part of the original PR #380 closure work.** PR #380
correctly performed the P-015 cascade close, wrote the compound-learning
entry, and wrote the compacted/archived P-020 memory files, but never wrote
the mandatory `docs/closure/147-S-139-F-post-merge-closure.md` artifact
itself -- the file was simply absent from `docs/closure/` after PR #380
merged, with no partial or malformed record to repair (unlike the
`146-S`/`138-F` precedent correction, PR #377/#378, which had an existing
file missing only its `compaction_status` field).

### How the gap was discovered

The successor-shipment pre-claim topology gate
(`autoharness gate pipeline-topology --mode agent --shipment 144-S --phase
pre_claim --json`) returned:

```
PREDECESSOR_CLOSURE_INCOMPLETE: predecessor 147-S is terminal but missing
required closure evidence
```

with `"closure_complete": null` -- the `null` (rather than `false`) value
confirms `closure_complete()`'s glob
(`docs/closure/147-S-*-post-merge-closure.md`) found **zero** matching
files, per `src/autoharness/gates/topology.py`'s `closure_complete` reader
implementation, distinct from a `false` result (a matching file existing but
failing `_closure_artifact_complete`).

### Fix

This correction adds the missing file with `closure_status: READY` and
`compaction_status: done`, both supported by pre-existing durable evidence
cited throughout this document (PR #379/#380 CI/review records, the P-015
cascade verification, and the P-020 compacted/archived memory files) -- no
field is fabricated. No backlog shipment or task was reopened, claimed, or
touched (`147-S`/`139-F`/`139.001-T`/`139.002-T` remain archived exactly as
PR #380 left them); no source, test, template, or config change was made.
Delivered as a standalone post-merge correction PR under Ship's post-merge
correction authority (precedent: 129-S/120-F correction PR #334; 146-S/138-F
correction PR #377/#378).

### Verification

- `autoharness gate pipeline-topology --mode agent --shipment 144-S --phase
  pre_claim --json` reproduced `PREDECESSOR_CLOSURE_INCOMPLETE` with
  `closure_complete: null` against the pre-correction state (this file
  absent), and is expected to return a passing verdict once this file is
  merged to `main` -- see the correction PR's readiness evidence for the
  exact before/after output.
- This correction does not claim, execute, or otherwise act on `144-S`; it
  only supplies the missing closure-evidence artifact so a future,
  separately authorized pre-claim of `144-S` can proceed on its own merits.

### Follow-ups / deferred

None new. `147-S`'s existing residual follow-up (P-021 deferred stash entry
`E8158860`) is unaffected by this correction. No systemic defect in the
closure-artifact-writing step of the post-merge closure workflow was
identified beyond this single missed write; if a pattern of missed
`docs/closure/` writes emerges across future shipments, that would be a
separate, out-of-scope process defect for Stage deliberation (P-021 C1),
not something this single-artifact correction expands into.
