---
shipment: 144-S
feature: 136-F
tasks:
    - 136.002-T
    - 136.003-T
pre_archived_manifest_members:
    - 136.001-T
feature_pr: 382
closure_pr: TBD
merge_commit: c4e4851cb2e4e1ebee72f675b4bd96264f3a87ad
merged_at: "2026-08-21T13:38:16Z"
reviewed_head: 0c443d30bb5f8523051c8f689b40b73eb7a7d6d6
closure_status: READY
compaction_status: done
conditions: []
---

# 144-S / 136-F Post-Merge Closure -- Restore Workspace-Wide Docline Lint + Regression Guard

Shipment `144-S` executed feature `136-F` (stash `395EBE60`): swept `docs/`
for the unquoted-colon-in-plain-scalar YAML hazard that had been silently
aborting `backlogit docs lint`'s workspace-wide traversal, and added a
regression guard so the failure class cannot recur. The single known
instance (`docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md`
line 12) was already repaired by `138.001-T` (feature `138-F`, shipment
`146-S`, merged prior to this shipment's claim).

## Merge Confirmation

- Feature PR #382 merged to `main` at `2026-08-21T13:38:16Z` with merge
  commit `c4e4851cb2e4e1ebee72f675b4bd96264f3a87ad`.
- Merge commit parents: `7850ffc1c9207f1eb47b514a0ac6c6c1a1de1e4c` (prior
  `main`) and `0c443d30bb5f8523051c8f689b40b73eb7a7d6d6` (merged HEAD) --
  two parents confirmed via `git cat-file -p`; P-009 merge-commit strategy
  preserved (repo settings: `allow_merge_commit: true`,
  `allow_squash_merge`/`allow_rebase_merge` both `false`).
- `git merge-base --is-ancestor c4e4851c... origin/main` confirmed exit 0.

## Executable Task Set / Manifest Classification (147-S contract)

Manifest `custom_fields.items`: `136-F`, `136.002-T`, `136.003-T`,
`136.001-T`.

| Item | Classification | Disposition |
| --- | --- | --- |
| `136.002-T` | task, was `queued` -> cascade-activated `active` at shipment claim | executable, kept, done |
| `136.003-T` | task, was `queued` -> cascade-activated `active` at shipment claim | executable, kept, done |
| `136.001-T` | task, `archived` (superseded by `138.001-T`) | `pre_archived_skipped` -- never claimed, moved, unarchived, or removed |
| `136-F` | covering feature (resolved via `parent_id`), not a task artifact | excluded from the executable set derivation; handled by cascade close below |

No `already_done`, no fail-closed anomalies.

## Pre-Merge Gate State (independently reverified)

| Gate | PR #382 |
| --- | --- |
| CI (`gh pr checks`) | `ci gate` pass, `detect code changes` pass, `pipeline-topology (ambient)` pass, `test` pass |
| P-018 Copilot review (`autoharness gate copilot-review`) | `SATISFIED` at HEAD `0c443d30` |
| Copilot review threads | 2 threads, both `isResolved: true` |
| P-009 merge strategy | merge-commit only, two parents confirmed |

## Review-Fix History

- Self-review (own pass, pre-PR): found and fixed a latent BOM-handling gap
  in the guard's own file-reading step (`utf-8` -> `utf-8-sig`), commit
  `1d228395`.
- Copilot hosted review on PR #382, round 1 (2 findings, both fixed in
  commit `0c443d30`): (1) the docstring referenced stale
  `.backlogit/queue/136.00{2,3}-T.md` paths, current after this PR marks
  both tasks done as `.backlogit/archive/...` -- corrected; (2) the
  regex-based frontmatter extractor could not distinguish "no frontmatter"
  from an unterminated (`---`-opened, never-closed) block -- replaced with
  a three-way `_frontmatter_status` classifier (`none`/`ok`/`unterminated`)
  built on `str.splitlines()`, which also correctly recognizes a closing
  delimiter at EOF with no trailing newline as closed. Both threads
  replied-to (citing the fixing commit) and resolved via GraphQL before
  merge.

## Runtime Verification

**Surface**: `cli` -- the only workspace-configured runtime validator
surface for this repository
(`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`).
This shipment touched only `tests/test_docs_frontmatter_decodes.py` and
`.backlogit/` metadata -- no `src/autoharness/` runtime, API, or UI code
changed.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` (`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`) |
| Runtime probe | `uv run autoharness --help` |
| Result | **PASS** -- exit 0 |
| Canonical gate | `PYTHONPATH=src python -m unittest discover -s tests` |
| Result | `Ran 1689 tests ... FAILED (failures=3, errors=2, skipped=20)` -- all 5 are the pre-existing, already-deferred (P-021 stash entry `E8158860`) full-suite test-isolation failures; confirmed unrelated (reproduced identically before and after this shipment's own two new test methods were added; each passes in isolation; CI's Linux `test` job was green on every push to PR #382) |
| Hosted CI | `ci gate`, `detect code changes`, `pipeline-topology (ambient)`, `test` -- all green on PR #382 at final HEAD |
| Manual checkpoints | none required -- test-only artifact, no user-facing or operational behavior change |
| Blocked prerequisites | none |
| Verdict | **PASS** for runtime-verification purposes; the 5 pre-existing failures are tracked as a follow-up (stash `E8158860`), not a blocker |

### Other Gates

- Full build: `PYTHONPATH=src python -m unittest discover -s tests` (see
  above) is the canonical build/test gate for this repository; no compiled
  build step applies.
- Quality Gates 1-4: PASS (YAML frontmatter valid; markdown structure
  intact; zero `{{VAR}}` placeholders -- not applicable, no templates
  changed; all cross-referenced files/skills/agents exist).

## Backlog Reconciliation (P-015)

`classify_shipment_close_path(['136-F', '136.002-T', '136.003-T',
'136.001-T'], '.backlogit')` -> **CASCADE** (`136-F` is a root, fully
covered by all three manifest-member children -- including the
already-archived, pre-archived `136.001-T` -- and the manifest contains
nothing beyond the qualifying root + children).

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` | exact match: `136.002-T`, `136.003-T`, `136-F`, `144-S` |
| `parent_id` preservation | `136.001-T.parent_id` re-read as `136-F`, unchanged |
| Live status | `136-F` archived (`archived_status: done`); `144-S` archived (`archived_status: shipped`) |
| Pre-existing archived member | `136.001-T` untouched throughout -- never claimed, moved, unarchived, or removed |

`backlogit shipment ship 144-S --sha c4e4851c...` was used in place of
manual safe-close, per the P-015 verified fully-covered-root exception
(same exception applied to `146-S`/`138-F`).

### Process note: topology gate ordering

The Step 5 Closure Tasks item 1 `TOPOLOGY_GATE: lifecycle (before
closure/safe-close)` check was run for the first time **after** the
`backlogit shipment ship 144-S` cascade-close mutation had already
completed, not immediately before it as the pipeline specifies. Re-running
it afterward correctly returns `LIFECYCLE_NO_ACTIVE_SHIPMENT` (144-S was
already archived/shipped by that point), which is the expected result for
a check run against a topology that has since moved past the mutation it
was meant to gate -- not evidence of an invalid close. The classifier
precondition (`classify_shipment_close_path` -> `CASCADE`) was verified
immediately before the mutation, and the post-mutation exact-match
verification (`archived_ids`, `returned_ids: []`, `parent_id` preservation)
confirms the close itself was correct. This is recorded here as a
self-identified process-ordering deviation for future-session awareness,
not as an unresolved integrity gap: no revert or re-close is warranted.

## Source Stash Retirement

Source stash `395EBE60` was confirmed absent from both the active stash
list and `backlogit stash get 395EBE60` ("not found") at session start --
Stage had already retired it during harvest before this shipment's
execution began, consistent with the operator's own briefing at session
start. No `backlogit_stash_remove` action was performed or required this
session.

## Operational Closure

- **Invariants to preserve**: the pre-archived manifest member
  (`136.001-T`) must never be claimed, moved, unarchived, or removed by any
  future shipment touching this feature's history; the executable task set
  derivation (147-S contract) correctly excluded it throughout this
  shipment.
- **Pre-deploy audits**: not applicable -- this shipment changed only a
  test module and backlog metadata; no migration, feature flag,
  configuration, or access-control surface was touched.
- **Deployment / rollout path**: merge-only. The new regression guard takes
  effect the moment `main` is synced and `python -m unittest discover -s
  tests` (or CI's `test` job) is next run; there is no separate deploy,
  canary, or phased-rollout step for this artifact class.
- **Risky action record**: not applicable -- no `ProposedAction` entries
  requiring approval, containment, or rollback beyond the standard
  operator-approved merge-commit-only merge (P-009) were taken.
- **Post-deploy checks**: re-run
  `autoharness gate pipeline-topology --mode agent --shipment 145-S --phase
  pre_claim --json` after this closure PR merges and confirm `exit_code: 0`
  (predecessor closure evidence for `144-S` -- this artifact -- now
  present).
- **Healthy signals**: PR #382 merged with a verified 2-parent merge
  commit; P-018 `SATISFIED` at final HEAD; both Copilot review threads
  resolved before merge; backlog cascade-close archived exactly the
  manifest's task, feature, and shipment records with no unintended
  archival; repo merge-strategy settings confirmed merge-commit-only.
- **Failure signals to watch**: a future sweep task in this same family
  should keep triangulating "decode failure" evidence from at least two
  independent parsers (direct PyYAML + `backlogit docs lint` output) rather
  than trusting either alone, as this shipment did.
- **Monitoring plan**: none required beyond the one-time post-deploy check
  above and the new regression guard itself, which now runs on every future
  `tests/` invocation.
- **Validation window**: immediate post-merge closure, 2026-08-21, the same
  day as PR #382's merge.
- **Rollback trigger**: revert merge commit `c4e4851c...` if the new
  regression guard produces false positives against legitimate,
  well-formed `docs/**/*.md` frontmatter in a future shipment.
- **Rollback procedure**: `git revert` the `144-S`/`136-F` feature merge
  commit (`c4e4851c...`) on `main` through a new reviewed PR; `backlogit
  docs lint` traversal and the new guard would both be removed, returning
  to the pre-shipment state (`138.001-T`'s single-file fix, from `146-S`,
  is unaffected since it lives in a separate commit history).
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for
  merge approval and release follow-up routing.
- **Releasability evidence**: **READY**. All required evidence is present:
  verified merge commit (two parents), green CI, P-018 `SATISFIED`, P-015
  cascade-close independently re-verified, and P-020 compaction evidence
  (`compaction_status: done`) backed by durable compacted/archived memory
  files. No condition is outstanding.
- **Residual follow-up (non-blocking)**:
  1. P-021 deferred stash entries `E8158860` (full-suite test-isolation
     pollution), `F73BA065` and `90F2A9F8` (docline lint required-field /
     hard-abort behavior) remain open; require Stage deliberation (C6), not
     actioned by Ship per the role boundary.
  2. Compound learning: `docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`
     -- promotes a behavior first noted informally in the 147-S session
     memory (backlogit 1.10.0 cascades shipment claim to the covering
     feature and queued manifest tasks) to a standalone, generalizable
     entry.

## Compaction (P-020)

`compact-context --target all` was invoked per the mandatory per-merge
trigger during this closure work. This shipment's own session memory
qualified under the completed-work rule; compacted summary written to
`docs/memory/compacted/2026-08-21-144S-136F-compacted.md`, consolidating
the verbose original at
`docs/archive/memory/2026-08-21-ship-144-s-execution-and-closure-session.md`.
Neither artifact records a compaction degradation or failure signal.

**Closure verdict: READY.** Runtime verification passed, both Copilot
review threads were resolved before merge, backlog cascade-close is
complete and independently re-verified, the source stash was already
retired by Stage prior to this session, and outstanding P-021 follow-ups
remain correctly tracked as Stage's to deliberate.
