---
shipment: 121-S
feature: 113-F
tasks: [113.001-T, 113.002-T, 113.003-T, 113.004-T, 113.005-T]
feature_pr: 316
merge_commit: db8630b6ce7b83bebf9a0006940fcccf01bf3ee0
merged_at: "2026-08-08T18:49:15Z"
reviewed_head: c355d3784e9866b3fd4c69d92199f5cb6c5c39cb
closure_pr: 317
closure_merge_commit: 9a3dc6a27724f57e58d858376e42c1042d83a574
closure_reviewed_head: a0f67581d8e6b9098b008325b8b6aface838a717
closure_status: READY
compaction_status: done
feature_terminal_status: done
feature_archived_status: done
---

# 121-S / 113-F Post-Merge Closure — Model-Routing Hierarchy Correctness + Dynamic Session-Start Reload (F02FD596 + E8B5B3C5)

Shipment `121-S` implemented covering feature `113-F`: the nested per-role
`stage.escalation`/`ship.escalation` model-routing hierarchy fix (F02FD596)
plus the session-start dynamic config reload contract (E8B5B3C5). `113-F` has
exactly 5 children — `113.001-T` .. `113.005-T` — all of which are this
shipment's task-only manifest, so `113-F` is fully covered by `121-S` alone
(no partial-feature sibling protection needed at closure).

This session **resumed** shipment `121-S` / feature PR `#316` after a prior
session's startup-checkpoint anomaly. The operator explicitly disposed of
that anomaly as a known, already-resolved historical artifact (see "Checkpoint
Anomaly Disposition" below) and authorized a bounded review-remediation window
to fix one additional Copilot review comment, then complete the shipment
end-to-end under the active `DARK_MODE_ACTIVE` contract (`120-S` completed,
`121-S` current, `122-S` next; merge/admin pre-authorized within all mandatory
gates).

## Checkpoint Anomaly Disposition (operator-authoritative, this session)

Per the operator's explicit resume instruction:

- `checkpoint-20260802-192655.json` and `checkpoint-20260802-045420.json` are
  known historical records whose repairs were already made **before** this
  session, in a prior session's dirty worktree.
- The confirmed root cause of the apparent re-trigger: those repairs existed
  only as **dirty worktree edits**, and were moved into remainder stash
  `ab16544a1636651d2368825d08cbd5e7c26ec755` during `120-S` isolation —
  exposing the old malformed **committed** snapshots underneath as if they
  were a fresh unresolved anomaly. This is **not** an unresolved recovery
  candidate and **not** a new interrupted session.
- Per operator disposition, this session did **not** repair, delete, or
  restore those two files, and did **not** touch, pop, apply, or drop stash
  `ab16544a...`. Verified via `git rev-parse "stash@{0}"` ==
  `ab16544a1636651d2368825d08cbd5e7c26ec755` (exact match) both at session
  start and again at this closure point — the stash is byte-identical
  throughout this session's lifetime.
- **Stash content (verified, untouched)**: a merge-style stash commit with
  two extra parents. Tracked-file diff: 5 checkpoint JSON files
  (`checkpoint-20260725-233536.json`, `checkpoint-20260726-005804.json`,
  `checkpoint-20260802-045420.json`, `checkpoint-20260802-192655.json`,
  `checkpoint-20260806-150505.json`). Untracked-file tree: 3 additional
  checkpoint JSON files (`checkpoint-20260808-042718.json`,
  `checkpoint-20260808-043446.json`, `checkpoint-20260808-044644.json`) plus
  `docs/decisions/2026-08-07-backlogit-directory-rename-feasibility-deliberation.md`
  (the "BED0DDED deliberation" referenced by the operator). Stash message:
  "On feat/model-routing-hierarchy-dynamic-reload-113-f: 121-S: preserve
  out-of-scope debris (historical checkpoints, backlogit-rename
  deliberation) - config/stage rename already applied via 121-S fresh
  commits 7e9682c2+4baebe48; gitmodules ATV-Phoenix hunk already merged on
  main, deliberately dropped." ATV-Phoenix confirmed already merged on
  `main` (untouched by this session). Successor `122-S` remains out of
  scope for this session.

## Merge Confirmation

- Feature PR **#316** ("feat: model-routing hierarchy correctness + dynamic
  session-start reload") merged to `main` at `2026-08-08T18:49:15Z` with
  merge commit `db8630b6ce7b83bebf9a0006940fcccf01bf3ee0`. Confirmed via
  `git show --no-patch --format="%H %P" db8630b6`: two parents
  (`55bfb3454641fe0a68d03ef6736e8456297f6fc1` prior `main` tip +
  `c355d3784e9866b3fd4c69d92199f5cb6c5c39cb` feature branch HEAD),
  preserving the P-009 merge-commit strategy. Confirmed ancestor of
  `origin/main` (`git merge-base --is-ancestor db8630b6... origin/main` ->
  exit 0).
- Repo merge-strategy settings (P-009), verified before merge:
  `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false` (`gh api repos/softwaresalt/autoharness`) —
  only "Create a merge commit" is possible. Post-merge, both parents
  confirmed present on the merge commit.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Reviewed HEAD (feature PR #316, merged) | `c355d378` (== PR HEAD at merge) |
| Local adversarial review (this session, round 5) | Direct diff review of the 11-file, 1021-insertion/153-deletion round-5 fix commit (`c355d378`) against `src/autoharness/schema_contracts.py`'s versioned-contract discipline and the established tool-telemetry-event precedent. Confirmed the restored 1.0.0 mirror is byte-identical to pre-PR `main`, the new 1.1.0 mirror differs from root only by `$id`, all coupled surfaces (template default, dogfood config, manifest checksum, tests, docs, changelog) updated coherently, and no `CONTRACT_MIGRATIONS` entry was needed. Verdict `READY`, 0 P0/P1. |
| Full local build / test evidence (at HEAD `c355d378`) | `PYTHONPATH=src uv run python -m unittest discover -s tests` (exact CI `test` job command) — 1402 tests, OK (skipped=11); `uv run python -m pytest tests -q` — 1391 passed, 11 skipped, 545 subtests passed; `uv run autoharness --help` smoke test PASS; `uv run autoharness verify-workspace --workspace . --autoharness-home . --json` — zero `blockers`, zero `strict_schema_blockers`, zero unexpected `migration_proposals`; `schema_contracts.config` status `current` at `observed_version: "1.1.0"`. |
| CI (PR #316, at HEAD `c355d378`) | `ci gate`, `detect code changes`, `pipeline-topology (ambient)`, `test` all **SUCCESS**. |
| Copilot review (PR #316) | **5 rounds total across the PR's lifetime** (4 prior to this session's resume + 1 this session). This session's round 5 addressed 1 thread. |
| P-018 copilot-review gate (this session) | `WAITING_FOR_REVIEW` immediately after push (round 5 HEAD not yet reviewed) -> re-requested Copilot review (`gh api .../requested_reviewers`, best-effort — GitHub CLI/REST reviewer-add for the Copilot bot identity is not guaranteed to register as a formal request, and did not appear in `reviewRequests` afterward) -> polled 2 minutes -> **`SATISFIED`** (0 unresolved threads) at HEAD `c355d378`, re-confirmed immediately before merge (exit 0, `forced: false`, 1 round). |
| §1.9 pre-merge readiness (Checks 1-5) | PASS at HEAD `c355d378`: PR body Local Review Readiness block refreshed to this HEAD, outcome `READY`, P0=0/P1=0, full local build evidence recorded, zero unresolved follow-ups, Copilot/P-018 result explicitly recorded `SATISFIED`. |
| Review-fix cycles (this session) | 1 of the operator's bounded 3-round authorization used (round 1 of the new window). 2 rounds remained unused — no further Copilot threads surfaced after round 5's fix. |
| Fix-CI cycles | 0 — CI was green throughout every HEAD checked this session; no code-remediation reruns required. |
| Dark-mode merge authorization | `DARK_MODE_MERGE_AUTHORIZED` for PR #316: PR in scope (`121-S`, current shipment in the `120-S -> 121-S -> 122-S` sequence), `merge_approval_pre_authorized: true` per the operator's bounded P-017 dark contract, §1.9 passed at HEAD, P-018 `SATISFIED` at HEAD (both re-verified immediately before merge, unconditionally), checks green, P-009/P-016 all passed. Admin fallback was pre-authorized but never invoked — the normal merge (`gh pr merge 316 --merge`) succeeded directly. |
| Worktree/PR topology (P-016) | Single worktree (`C:/Source/GitHub/autoharness`) throughout; no parallel worktree created or used. `pipeline-topology` lifecycle gate PASS (`branch_ownership: BRANCH_OK`, `worktree_topology: WORKTREE_TOPOLOGY_OK`, `active_shipment_invariant` — sole active shipment `121-S`) immediately before merge. |

### Round-5 Copilot review detail (this session's resume)

**Round 5** (HEAD `1610df56` -> fix `c355d378`, 1 comment):

- **Thread** `PRRT_kwDORzpWpM6XdaR_` (comment `databaseId 3740410056`,
  `schemas/harness-config.schema.json:608`): PR #316 added nested
  `stage.escalation`/`ship.escalation` properties (each
  `additionalProperties: false`) plus the H2 `not` ambiguity constraint
  directly into both `schemas/harness-config.schema.json` AND the published
  `schemas/harness-config/1.0.0.schema.json` mirror, while leaving
  `schema_version.const` / `SCHEMA_CONTRACTS["config"].current_version` at
  `1.0.0` — making the version string `1.0.0` describe two different
  validation contracts. Forbidden per the versioned-contract discipline in
  `src/autoharness/schema_contracts.py:42-54`.
- **Fix** (commit `c355d378`, mirrors the tool-telemetry-event v1.0->v1.1
  precedent, commit `6da2f55b`, PR #294 cycle 2): restored
  `schemas/harness-config/1.0.0.schema.json` to byte-identical pre-PR
  `main` content; published the additive change under a new
  `schemas/harness-config/1.1.0.schema.json` mirror; bumped
  `schema_version.const` and `SCHEMA_CONTRACTS["config"].current_version`/
  `known_versions` to `1.1.0` (no `CONTRACT_MIGRATIONS` entry — purely
  additive bump, matching precedent and preserving
  `tests/test_verify_workspace.py`'s `migration_proposals == []` contract);
  bumped `templates/harness-config.yaml.tmpl` and this repo's own dogfood
  `.autoharness/config.yaml` to `1.1.0`; refreshed `harness-manifest.yaml`
  checksum/note; updated `tests/test_escalation_hierarchy_schema.py` and
  `tests/test_anchor_review_routing.py`; added
  `test_legacy_1_0_0_mirror_preserved_unchanged`; documented in
  `CHANGELOG.md` and the design doc.
- **Reply**: posted via
  `gh api repos/softwaresalt/autoharness/pulls/316/comments/3740410056/replies`
  (new comment `3741340615`), identifying the fixing commit and summarizing
  the fix.
- **Resolution**: re-queried GraphQL `reviewThreads` to reconfirm the thread
  ID matched, then resolved programmatically via `gh api graphql`
  `resolveReviewThread` (thread ID `PRRT_kwDORzpWpM6XdaR_`). Re-queried again
  after resolution: 0 of 10 threads unresolved at HEAD `c355d378`.
- A new compound-learning doc,
  `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`,
  records the generalizable pattern: a schema-behavior change applied
  uniformly across "the schema files" for a contract with published
  versioned mirrors silently redefines an already-published version unless
  the old mirror is deliberately excluded and the version is bumped instead.

**Total this session: 1 Copilot review comment, fixed -> committed -> pushed
-> replied -> GraphQL-resolved.** 1 of the 3 authorized bounded-window
rounds used; no further thread surfaced.

## Runtime Verification

**Surface**: this shipment is agent-instruction/template/schema/CLI
verification logic only (schema versioning contract, `verify_workspace.py`
compatibility resolution, agent template/instruction prose) — no user-facing
runtime service surface, no external binary, no new runtime/execution engine,
and no distribution/packaging change.

| Field | Evidence |
| --- | --- |
| Validator | Ship pre-merge runtime verification |
| Surface adapter | `verify_workspace.py` schema-contract resolution (`resolve_contract_schema_path` / `SCHEMA_CONTRACTS`) — the CLI validation surface this shipment's round-5 fix directly touches |
| Runtime probe | `uv run autoharness verify-workspace --workspace . --autoharness-home . --json` (run pre-merge, at HEAD `c355d378`): zero `blockers`, zero `strict_schema_blockers`, zero unexpected `migration_proposals`; `schema_contracts.config` reports `status: "current"` at `observed_version: "1.1.0"`, `known_versions: ["0.9.0", "1.0.0", "1.1.0"]`. `uv run autoharness --help` — exit 0. |
| Preserve-invariant | "The autoharness CLI starts without import, packaging, or option-parsing failures" — HELD. "An installed config with `schema_version: 1.0.0` continues to validate against the untouched, restored 1.0.0 contract" — HELD (regression test `test_legacy_1_0_0_mirror_preserved_unchanged` added and passing). "The same `schema_version` string never means two different byte-level contracts" — HELD (the bug this shipment's round-5 fix corrects). |
| Blocked prerequisites | none |
| Verdict | **HELD** — the schema-contract validation surface was exercised pre-merge with the evidence above; no separate runtime engine, external binary, or distribution/packaging surface was touched by this shipment. |

## Backlog Reconciliation (single-artifact safe-close, P-015) + Feature Terminal-State Determination

### 121-S safe-close (this session, post-merge)

- **Manifest**: `custom_fields.items` = `113.001-T`, `113.002-T`,
  `113.003-T`, `113.004-T`, `113.005-T` (task-only shipment, 5 tasks, all
  `status: done` since the pre-merge task loop of a prior session; verified
  `done` again this session via `backlogit get` on each).
- **Protected set**: covering feature `113-F` alone. Verified via
  `Get-ChildItem .backlogit/{queue,archive} -Filter "113.*"` — the ONLY
  `113.*` artifacts present are the 5 manifest tasks (all archived,
  `status: done`). No `113.*` siblings exist outside the manifest —
  `113-F` is genuinely fully covered by `121-S` alone.
- **Baseline integrity gate**: `git status --short -- .backlogit/` was
  clean at the start of this session's closure work. Protected-set member
  `113-F` confirmed present in `.backlogit/queue/` (`Test-Path` -> `True`,
  not pre-archived) before any archival mutation.
- **Manifest item archival**: all 5 manifest tasks were already in
  `.backlogit/archive/` at session-closure start (archived by the merge
  commit's own pre-merge task-completion loop, `status: done`) —
  classified `pre-archived` for all 5, no re-archival performed.
- **121-S shipment record**: moved live `status: shipped`
  (`backlogit move 121-S --status shipped`) -> verified live
  `status: shipped` -> `backlogit archive 121-S` -> verified
  `archived_status: shipped`. The cascade command
  `backlogit shipment ship` / `backlogit_ship_shipment` was **never**
  run.
- **Protected-set integrity**: `113-F` re-confirmed present in
  `.backlogit/queue/` (`Test-Path` -> `True`) immediately after the
  shipment-record close, and `git status --short` showed only the `121-S`
  record rename to archive plus log-file updates — no cascade.

### `113-F` covering-feature terminal-state determination (this session)

`113-F`'s only 5 children are exactly `121-S`'s manifest — confirmed via
`Get-ChildItem .backlogit/{queue,archive} -Filter "113.*"`, which returns
exactly `113.001-T` through `113.005-T` (all `status: done`, all archived),
and zero `113.*` matches remain anywhere else. Per the established 119-S
precedent for a fully-covered feature, `113-F` was moved `status: active` ->
`done` (`backlogit move 113-F --status done`) -> verified live
`status: done` -> `backlogit archive 113-F` -> verified
`archived_status: done`.

- **Provenance preserved**: `113-F`'s labels (`model-routing`, `P-013.5`,
  `P-013.6`, `escalation`, `F02FD596`, `E8B5B3C5`) remain present and
  untouched in the archived record; `113-F` carries only the
  `harness_status: pending` custom field, unaffected by closure.
- **F02FD596 / E8B5B3C5 tracker verification**: neither identifier appears
  as a `backlogit stash list` tracker entry — both were labels embedded
  directly in `113-F`/`121-S`'s own frontmatter/description from original
  intake, fully consumed by this shipment with no separate living-tracker
  record requiring disposition update.
- **Remainder stash `ab16544a1636651d2368825d08cbd5e7c26ec755`**: confirmed
  present, untouched, and byte-identical (`git rev-parse "stash@{0}"`
  matches exactly) both before and after this session's closure work — see
  "Checkpoint Anomaly Disposition" above for full content/hash/message
  detail.
- Closure index resync: **complete** — `backlogit sync` run after all
  archival mutations were committed, indexing 740 artifacts
  (`CLOSURE_INDEX_SYNC_OK`).

## Context Compaction (P-020)

- **Status: recorded below** (mandatory per-merge invocation, performed this
  session; see the compact-context invocation output captured at the time
  this file was finalized).
- Session memory: `docs/archive/memory/2026-08-08-ship-121-S-113-F-session.md`
  (written this session, archived as part of the same compaction pass — the
  completed-work rule applies directly since this is the just-closed release
  unit's own memory).
- Compacted memory: `docs/memory/compacted/2026-08-08-121S-113F-compacted.md`
  (decisions, files modified, key learnings/cross-references to the new
  compound doc, outcomes, provenance chain).

## Operational Closure

- **Healthy signals**:
  - Feature PR #316 merged with a merge commit (two parents; P-009
    preserved).
  - Local review `READY` (0/0/0/0) at final HEAD `c355d378`; 1 Copilot
    review thread this session (round 5 of the PR's overall lifetime), fixed,
    replied, and resolved — zero unresolved threads, re-confirmed via the
    P-018 gate immediately before merge.
  - CI green at every required check on the final HEAD.
  - Backlog safe-close for `121-S` reconciled all 5 manifest tasks (already
    `pre-archived` by the merge commit's own pre-merge task-completion loop,
    so no re-archival action was needed for the tasks themselves) and then
    explicitly archived the `121-S` shipment record (`status: shipped` ->
    `archived_status: shipped`), without the forbidden cascade command;
    `113-F` was then archived as a separate, subsequent step
    (`status: done` -> `archived_status: done`) only after independently
    verifying all 5 children are archived and zero `113.*` descendants
    remain in queue.
  - Remainder stash `ab16544a1636651d2368825d08cbd5e7c26ec755` (historical
    checkpoint repairs + BED0DDED deliberation) confirmed present, ACTIVE,
    and byte-for-byte untouched throughout this session, per the operator's
    explicit disposition.
  - This is the **current** shipment in sequence `120-S -> 121-S -> 122-S`
    (`120-S` already completed; `122-S` remains out of scope for this
    session, per the operator's directive).
- **Failure signals to watch**: none specific to this shipment's own
  closure. The bounded review window (max 3 additional rounds) was used for
  only 1 round; 2 rounds remain unused headroom, not a risk.
- **Follow-ups** (non-blocking; `closure_status: READY`):
  1. See
     `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`
     for the generalizable "schema mirror mutated in place without a version
     bump" pattern — a forward-looking lesson for any future schema-contract
     change, not an open defect in this shipment.
  2. Judgment call (not explicitly confirmed by a Copilot comment or operator
     instruction, inferred from convention): this repo's own dogfood
     `.autoharness/config.yaml` was bumped to `schema_version: "1.1.0"`
     alongside the template default, consistent with `harness-manifest.yaml`
     already tracking its own contract at current version. This is a
     structural-only change (no escalation data values altered) and is
     covered by the same `verify-workspace` validation evidence above; flagged
     here for operator awareness, not as an open risk.
  3. Successor shipment `122-S` remains queued and out of scope for this
     session per the operator's explicit directive.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): the shipped capability is
  autoharness product-template schema/CLI/verification-logic orchestration —
  no external binary changes, no new runtime/execution engine, no new
  distribution/packaging change. Rollback = revert merge commit `db8630b6`
  (additive schema-mirror/template/test/doc changes only; the restored
  1.0.0 mirror is itself a revert of the prior in-place mutation, not new
  behavior). **Verdict: READY.**

## Closure Tasks (this branch)

1. Compound-learning doc:
   `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`
   — **done** (this branch).
2. This canonical closure artifact (this file) — **done**.
3. Session memory write + compaction to
   `docs/memory/compacted/2026-08-08-121S-113F-compacted.md`
   (verbose original archived to
   `docs/archive/memory/2026-08-08-ship-121-S-113-F-session.md`) —
   **done** (this branch).
4. Mandatory P-020 `compact-context` (`target: all`) invocation —
   **done** (this branch).
5. Closure index resync (`backlogit sync` CLI, 740 artifacts indexed) —
   **done** (this branch, after all archival mutations were committed).
6. Closure PR — **done**: PR #317 merged to `main` with merge commit
   `9a3dc6a27724f57e58d858376e42c1042d83a574` at final reviewed HEAD
   `a0f67581d8e6b9098b008325b8b6aface838a717` (own local review + P-018
   gate + operator approval all satisfied pre-merge). *Correction
   (provenance-repair, post-#317): this file's `closure_merge_commit`/
   `closure_reviewed_head` frontmatter originally recorded `null` /
   `b0ebc5c3edd3a6b76c0f08858e68d59be2691d49` (an intermediate
   pre-final-push HEAD) instead of the actual #317 merge commit and true
   final reviewed HEAD; corrected here to the values above. The repair
   branch's own merge commit is never self-referenced in these fields —
   they record #317's stable, already-merged provenance only, per the
   same convention used for 119-S's closure PR #311.
7. **No follow-ups actioned by Ship in code this session** beyond the
   compound-learning doc above — successor `122-S` is unchanged and out of
   scope, per the operator's explicit directive.
