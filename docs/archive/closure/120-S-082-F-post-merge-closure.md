---
shipment: 120-S
feature: 082-F
tasks: [082.001-T, 082.002-T, 082.003-T]
feature_pr: 314
merge_commit: ca066a053c891fa2152c85c2f2936f6507e81fa3
merged_at: "2026-08-08T06:17:22Z"
reviewed_head: d8ef5e5dddf65a2ef835566ef4d5bc2fd4895ac5
closure_pr: 315
closure_merge_commit: 55bfb3454641fe0a68d03ef6736e8456297f6fc1
closure_reviewed_head: 52032a5a57ee1038fbd20a076037a62917dbf06a
closure_status: READY
compaction_status: done
feature_terminal_status: done
feature_archived_status: done
---

# 120-S / 082-F Post-Merge Closure — Cross-Pack Measurability Documentation (Engram + graphtor-docs Evidence Mapping)

Shipment `120-S` — first shipment in the dark-mode ordered scope
`120-S -> 121-S -> 122-S` — implemented feature `082-F`: a documentation-only
mapping of Engram's `UsageEvent` v2 telemetry surface and graphtor-docs's
`SyncMetrics`/`SyncStatus` telemetry surface onto the ratified
`ToolTelemetryEvent` v1.0 contract (079-F), consolidated into a cross-pack
adapter-gap report that also carries forward the binding sensitivity/redaction
acceptance criterion (AC1, review F1) established for a future 084-F-scoped
adapter. `082-F`'s only 3 children are exactly this shipment's task-only
manifest — fully covered by `120-S` alone, no partial-feature sibling
protection needed at closure.

Executed under an **operator-authorized P-017 dark-factory contract** scoped
to the ordered sequence `120-S -> 121-S -> 122-S` (current cursor: `120-S`),
with `merge_approval_pre_authorized: true`, `admin_fallback_pre_authorized: true`
(never invoked — normal merge succeeded directly), local-only/degraded
visibility (agent-intercom unavailable), and P-001/P-009/P-014/P-016/P-018/CI/P-020
held mandatory throughout.

## Dirty-Worktree Handoff (operator-directed, pre-session)

At session start the worktree carried operator-staged content plus unrelated
in-flight changes for successor shipment `121-S`. Both were handled exactly per
the operator's explicit directive:

- **`.gitmodules` + gitlink `references/atv-phoenix`** (pinned at
  `e99b918139fbd73011b1270516a2cf7a013fb417`): operator-owned reference content,
  **no backlog feature/task**, carried forward into the `120-S` implementation
  PR as a standalone, clearly-labeled commit (`cf1be492`, "chore(references):
  add atv-phoenix submodule (operator-provided reference content, no backlog
  item)") verified via `git diff-tree --raw` to confirm the exact gitlink mode
  `160000` at the pinned SHA, unaltered.
- **Out-of-scope changes excluded from `120-S`**: `.autoharness/config.yaml` and
  `.github/agents/_stage.agent.md` (a pre-existing 121-S-relevant model-route
  rename), 5 modified + 3 new-resolved checkpoint files, and the untracked
  `docs/decisions/2026-08-07-backlogit-directory-rename-feasibility-deliberation.md`
  were isolated via `git stash push -u` with precise pathspecs into a labeled
  stash entry (`120-S: preserve out-of-scope dirty state (121-S model-route
  rename, checkpoints, rename deliberation)`) **before** branch creation, matching
  the established Ship precedent pattern (117-S/114-S/098-S/059-S all used the
  same isolation technique). The stash was **not** popped, applied, or dropped
  at any point during `120-S`'s implementation, review, or merge — it remains
  present (at whatever positional index `git stash list` currently reports —
  see the caution below) for the operator/121-S to restore to `main`, now that
  `main` has fast-forwarded past `120-S`'s merge commit.

## Merge Confirmation

- Feature PR **#314** ("feat(082-F): cross-pack measurability documentation —
  Engram + graphtor-docs evidence mapping (120-S)") merged to `main` at
  `2026-08-08T06:17:22Z` with merge commit
  `ca066a053c891fa2152c85c2f2936f6507e81fa3`. Confirmed via
  `git log --pretty=%P -n 1 ca066a05...`: two parents (`cdf8913d436d...` prior
  `main` tip, i.e. the Stage publication PR #313 merge + `d8ef5e5ddd...`
  feature branch HEAD), preserving the P-009 merge-commit strategy. Confirmed
  ancestor of `origin/main` (`git merge-base --is-ancestor ca066a05...
  origin/main` -> exit 0).
- Repo merge-strategy settings (P-009), re-verified before merge:
  `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false` (`gh api repos/softwaresalt/autoharness`) — only
  "Create a merge commit" is possible.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Reviewed HEAD (feature PR #314, merged) | `d8ef5e5d` (== PR HEAD at merge) |
| Local adversarial review | Self-applied local review pass (report-only), performed twice: once at initial HEAD `be30b35f` (466 lines, READY, 0 P0/P1) and re-confirmed at the fix HEAD `d8ef5e5d` after the Copilot review-fix commit (34 lines changed across 3 files, all substantive corrections, no new defects introduced). Verdict `READY`, 0 P0/P1 at final HEAD. |
| Full local build / test evidence | `uv run autoharness --help` smoke test PASS (re-verified at `d8ef5e5d`). `uv run python -m pytest tests -q` — **1362 passed, 11 skipped, 545 subtests passed**, re-run clean at both `be30b35f` (117.07s) and `d8ef5e5d` (216.65s) — supplemental evidence, not the canonical gate. The repository's actual **canonical** CI gate is `PYTHONPATH=src python -m unittest discover -s tests` (`.github/workflows/ci.yml:95`; see `docs/compound/097-S-canonical-unittest-gate.md`) — this is what the `test` CI job below actually runs, not the scoped `pytest` invocation. (Bare `pytest` from repo root surfaces 29 pre-existing collection errors under `references/*` submodule test files, including the newly-added `atv-phoenix` — pre-existing behavior identical to prior submodules, unrelated to this PR's scope.) `autoharness gate check` — no validation gates configured for this doc-only diff. |
| CI (PR #314) | `detect code changes`, `pipeline-topology (ambient)` green throughout. `test`/`ci gate` failed once at `d8ef5e5d` on a pre-existing, unrelated concurrency test (`test_two_writers_interleaved_seal_preserve_every_distinct_segment`, `tests/test_telemetry_jsonl_sink.py`) — confirmed the PR's diff touched zero Python files before re-running the failed jobs (`gh run rerun --failed`), which then passed clean. See the new compound-learning doc for this session-process note. |
| Copilot review (PR #314) | **1 round, 5 inline comments**, all genuine mapping-accuracy/redaction-wording findings, all fixed at HEAD `d8ef5e5d`, individually replied to (referencing the fixing commit SHA), and resolved via GraphQL `resolveReviewThread`. See "Copilot review detail" below. |
| P-018 copilot-review gate | Progression: `WAITING_FOR_REVIEW` (initial) -> `UNRESOLVED_THREADS` (5 findings, after `--max-wait 180`) -> **`SATISFIED`** (0 unresolved threads) at HEAD `d8ef5e5d`, re-confirmed immediately before merge (`--max-wait 30`, exit 0, `forced: false`, 1 round). |
| §1.9 pre-merge readiness (Checks 1-5) | PASS at HEAD `d8ef5e5d`: PR body Local Review Readiness block updated to the fix-cycle HEAD, outcome `READY`, P0=0/P1=0, full local build evidence recorded (re-verified at the new HEAD), zero unresolved follow-ups, shadow-review (Copilot) result explicitly recorded as `SATISFIED`. |
| Review-fix cycles | Local: 1 round (0 findings requiring fixes at either HEAD checked). Copilot review-comment cycles: 1 round of 5 findings, all fixed to closure (well within the 3-cycle cap). Fix-CI cycles: 1 transient rerun (pre-existing flaky concurrency test, unrelated to the diff; not a code-remediation cycle). |
| Dark-mode merge authorization | `DARK_MODE_MERGE_AUTHORIZED` for PR #314: PR in scope (`120-S`, first shipment of ordered scope `120-S -> 121-S -> 122-S`), `merge_approval_pre_authorized: true` per the operator's P-017 dark contract, §1.9 passed at HEAD, P-018 `SATISFIED` at HEAD (both re-verified immediately before merge, unconditionally), checks green, P-009/P-016 all passed. Admin fallback was pre-authorized but never invoked — the normal merge (`gh pr merge 314 --merge`) succeeded directly. |
| Worktree/PR topology (P-016) | Single worktree (`C:/Source/GitHub/autoharness`) throughout; no parallel worktree created or used; `pipeline-topology` gate re-run and passed at every required checkpoint (pre_claim ×2, post_claim, lifecycle ×4). |

### Copilot review detail (all 5 comments fixed to closure)

**Round 1** (HEAD `be30b35f` -> fix `d8ef5e5d`, 5 comments, 1 defect class:
state/metadata vs. actual protocol outcome conflation):

- **Finding 1** (`engram-evidence-map.md`): `UsageEvent.timestamp` is set via
  `Utc::now()` **after** the response is fully computed (source-verified against
  `engram/src/cli/direct.rs` and `engram/src/tools/mod.rs`), so mapping it
  directly onto `started_at` silently reports a completion time as a start time.
  Fixed by splitting the row: `timestamp` remains `observed` (with a completion-
  time caution), and `started_at` is now `unavailable` (or `derived` as
  `timestamp - latency_ms`), never directly mapped.
- **Finding 2** (`graphtor-docs-evidence-map.md`): `SyncStatus::Error` was mapped
  directly to event `status: failed`, conflating the background sync state with
  the outcome of the `get_status` call itself — a successful `get_status` call
  reporting `SyncStatus::Error` is itself a successful call. Fixed by deriving
  `status` strictly from the MCP call's own success/error result; `SyncStatus`
  may only be mapped onto a separately-wrapped sync-cycle event's status.
- **Finding 3** (`graphtor-docs-evidence-map.md`): graphtor search tools return
  an unstructured markdown `CallToolResult` (source-verified against
  `graphtor/src/mcp/server.rs` — no structured `result_count` field on the
  wire), so `result_count` was overstated as `host_reported`/`observed`. Fixed
  by reclassifying `result_count` as `derived` (adapter-computed from returned
  result blocks).
- **Finding 4** (`cross-pack-adapter-gap-report.md`): AC1 required only
  `redaction_applied: true` before emission — but the flag alone is metadata,
  not the redaction; an emitter could set it without actually transforming or
  omitting the sensitive value. Fixed by requiring actual omission/transformation
  to happen first, with the flag only attesting to a transformation that has
  already occurred, and requiring verification to check the emitted value
  itself.
- **Finding 5** (`cross-pack-adapter-gap-report.md`): the consolidated summary
  table repeated Finding 2's `SyncStatus`/`status` conflation. Fixed by mirroring
  the graphtor-docs correction in the summary.

A new compound-learning doc,
`docs/compound/2026-08-08-state-vs-call-outcome-conflation-in-telemetry-mapping.md`,
records the generalizable pattern: a subsystem's reported state (or a
completion-time field, or a field that doesn't exist on the wire at all) is not
the same axis as the call's own outcome, and each mapping must be checked against
all three before being labeled `host_reported`/`observed`.

**Total: 5 Copilot review comments in 1 round, all individually fixed ->
committed -> pushed -> replied -> GraphQL-resolved.** No findings were dropped,
capped, or left as follow-ups.

## Runtime Verification

**Surface**: this shipment adds three new documentation files
(`docs/telemetry/engram-evidence-map.md`, `docs/telemetry/graphtor-docs-evidence-map.md`,
`docs/telemetry/cross-pack-adapter-gap-report.md`), cross-link updates to two
existing telemetry docs, and one operator-owned submodule gitlink
(`references/atv-phoenix`, unaltered). **No source code, schema, CLI, or runtime
engine surface was touched.** No new checkpoint-schema field, no new
runtime/execution engine, no new gate surface.

| Field | Evidence |
| --- | --- |
| Validator | Ship pre-merge runtime verification |
| Surface adapter | N/A — no runtime/CLI/gate surface changed by this shipment |
| Runtime probe | `uv run autoharness --help` — exit 0 (smoke test, re-verified at both HEADs). `uv run python -m pytest tests -q` — 1362 passed, 11 skipped, 545 subtests passed (re-verified at both HEADs; supplemental evidence — the repository's canonical CI gate is `PYTHONPATH=src python -m unittest discover -s tests`, `.github/workflows/ci.yml:95`). |
| Preserve-invariant | "The autoharness CLI starts without import, packaging, or option-parsing failures" — HELD. "No documentation-only change introduces an unresolved `{{VARIABLE}}` placeholder, broken cross-reference, or invalid YAML frontmatter" — HELD (verified via link-checker script, frontmatter parse, and placeholder scan, both at reviewed HEAD and after the fix commit). |
| Blocked prerequisites | none |
| Verdict | **HELD** — no runtime/CLI/execution surface was touched by this shipment; the documentation-only claim is source-verified (`git diff --name-only main...HEAD` shows zero `.py` files). |

## Backlog Reconciliation (single-artifact safe-close, P-015) + Feature Terminal-State Determination

### 120-S safe-close (this session, post-merge)

- **Manifest**: `custom_fields.items` = `082.001-T`, `082.002-T`, `082.003-T`
  (task-only shipment, 3 tasks, all `status: done` since the pre-merge task
  loop).
- **Protected set**: covering feature `082-F` alone. Verified via
  `Get-ChildItem .backlogit/{queue,archive} -Filter "082.*"` (and `082-F.md`
  itself) — the ONLY `082.*` artifacts present are the 3 manifest tasks (all
  archived, `status: done`). No `082.*` siblings exist outside the manifest —
  `082-F` is genuinely fully covered by `120-S` alone.
- **Baseline integrity gate**: `git status --short -- .backlogit/` was clean at
  session start on the post-merge closure branch (the merge commit itself
  already carried the 3 manifest tasks' `queue -> archive` renames and
  `status: done` transitions from the pre-merge task-completion loop).
  Protected-set member `082-F` confirmed present in `.backlogit/queue/` (not
  pre-archived) — no baseline-gate exemption needed.
- **Manifest item archival**: all 3 manifest tasks were already in
  `.backlogit/archive/` at session start (archived by the merge commit's
  pre-merge task-completion loop, `status: done`) — classified `pre-archived`
  for all 3, no re-archival performed.
- **120-S shipment record**: moved live `status: shipped`
  (`backlogit move 120-S --status shipped`) -> verified live
  `status: shipped` -> `backlogit archive 120-S` -> verified
  `archived_status: shipped`. The cascade command
  `backlogit shipment ship` / `backlogit_ship_shipment` was **never** run.
- **Protected-set integrity**: `082-F` re-confirmed present in
  `.backlogit/queue/` before its own terminal-state determination below, and
  `git status --short` showed only the `120-S` record rename to archive — no
  cascade.

### `082-F` covering-feature terminal-state determination (this session)

`082-F`'s only 3 children are exactly `120-S`'s manifest — confirmed via
`Get-ChildItem .backlogit/{queue,archive} -Filter "082.*"`, which returns
exactly `082.001-T` through `082.003-T` (all `status: done`, all archived) and
zero `082.*` matches remain in `.backlogit/queue/`. `082-F`'s own DoD
(operator-provided read-only pack access; evidence mapping of observed/
estimated/derived/unavailable/unsafe-to-emit metrics per pack; adapter-gap
report before broad pack-adapter implementation) is fully satisfied by this
shipment's three deliverables. `082-F` was moved `status: active` -> `done`
(`backlogit move 082-F --status done`) -> verified live `status: done` ->
`backlogit archive 082-F` -> verified `archived_status: done`.

- **Provenance preserved**: `082-F`'s label
  (`backlogit-portion-carved-108F`) remains present and untouched in the
  archived record; `082-F` carries `source_stash_id: 83854CD2` and related
  `source_stash_*` custom fields, unaffected by closure (no cleanup required —
  this is historical provenance, not a live stash reference to reconcile).
- **83854CD2 stash-tracker note**: `082-F`'s `source_stash_id: 83854CD2` is
  historical intake provenance; not independently re-verified via
  `backlogit stash list` in this closure session since it records the
  feature's origin, not an active/unresolved tracker requiring disposition
  confirmation (unlike `34D50F2D` in the 119-S precedent, which was itself a
  still-active living tracker for deferred candidates).
- Closure index resync: **complete** — `backlogit sync` run after all archival
  mutations were committed, indexing 740 artifacts (`CLOSURE_INDEX_SYNC_OK`).

## Context Compaction (P-020)

- **Status: `done`** (mandatory per-merge invocation, performed this session).
- Session memory: `docs/archive/memory/2026-08-08-ship-120-S-082-F-session.md`
  (written fresh this session, then immediately archived as part of the same
  compaction pass — the completed-work rule applies directly since this is the
  just-closed release unit's own memory).
- Compacted memory: `docs/memory/compacted/2026-08-08-120S-082F-compacted.md`
  (decisions, files modified, key learnings/cross-references to the new
  compound doc, outcomes, provenance chain).
- The Stage-authored plan `docs/archive/plans/2026-08-07-082F-cross-pack-measurability-plan.md`
  was **not** consolidated this pass — it has no appended review section
  (the review is a separate artifact, `082.001-R`), so it does not meet the
  "plan has appended review content ready for consolidation" candidate
  criterion; also out of Ship's role boundary to modify planning artifacts.
  No other plan or closure-record candidates met the compaction thresholds
  (`threshold_days: 14`, `max_files: 40`, `max_size_kb: 500`) during this
  pass — this was a bounded, cheap Tier-1 consolidation of the one intended
  candidate (this shipment's own fresh memory), per the compact-context
  skill's per-merge floor contract.

## Operational Closure

- **Healthy signals**:
  - Feature PR #314 merged with a merge commit (two parents; P-009 preserved).
  - Local review `READY` (0 P0/0 P1) at final HEAD; **5** Copilot review
    threads in 1 round, all genuine findings, all fixed, replied, and
    resolved — zero unresolved threads, re-confirmed via the P-018 gate
    immediately before merge.
  - CI green at every required check at the final HEAD (one transient,
    unrelated flaky-test rerun, resolved by re-running the job — see the
    compound-learning doc).
  - Backlog safe-close for `120-S` reconciled all 3 manifest tasks (already
    `pre-archived` by the merge commit's own pre-merge task-completion loop)
    and then explicitly archived the `120-S` shipment record
    (`status: shipped` -> `archived_status: shipped`), without the forbidden
    cascade command; `082-F` was then archived as a separate, subsequent step
    (`status: done` -> `archived_status: done`) only after independently
    verifying all 3 children are archived and zero `082.*` descendants remain
    in queue.
  - Operator-owned `.gitmodules`/`references/atv-phoenix` gitlink carried
    forward exactly as directed, in a standalone labeled commit, unaltered
    submodule revision, no backlog item created for it.
  - The 9 out-of-scope dirty-worktree files (121-S model-route rename,
    checkpoints, rename-deliberation doc) remained isolated in the labeled
    stash throughout `120-S`'s full lifecycle — never popped, applied, or
    included in any `120-S` commit or PR.
  - This is the **first** shipment in the dark-mode ordered scope
    `120-S -> 121-S -> 122-S`; cursor now advances to `121-S`.
- **Failure signals to watch**: none specific to this shipment's own content.
  The single transient CI flake (`test_two_writers_interleaved_seal_preserve_every_distinct_segment`)
  is a pre-existing concurrency test unrelated to this PR's docs-only diff;
  recorded in the compound-learning doc as a session-process note, not an open
  defect.
- **Follow-ups** (non-blocking; `closure_status: READY`):
  1. See `docs/compound/2026-08-08-state-vs-call-outcome-conflation-in-telemetry-mapping.md`
     for the generalizable state-vs-call-outcome / completion-vs-start-time /
     wire-shape-provenance pattern observed across all 5 Copilot findings — a
     forward-looking lesson for any future 084-F-scoped adapter, not an open
     defect in this shipment.
  2. The isolated stash (`120-S: preserve out-of-scope dirty state (121-S
     model-route rename, checkpoints, rename deliberation)`) remains stashed
     and must be restored to `main` before or during `121-S` execution — this
     is explicitly **121-S's** responsibility, not part of `120-S`'s own
     closure. **Safety note**: stash indices (`stash@{0}`, `stash@{1}`, ...)
     are positional, not stable identifiers — any new stash created between
     now and 121-S's restore would shift this entry away from index 0. 121-S
     MUST resolve the labeled entry's *current* index explicitly (e.g.
     `git stash list | Select-String "120-S: preserve out-of-scope"`) and pop
     that specific resolved ref — never assume a fixed index or run a bare
     `git stash pop`.
  3. `docs/decisions/2026-08-07-backlogit-directory-rename-feasibility-deliberation.md`
     remains untracked inside the same stash; also 121-S's concern.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): the shipped capability is documentation-only
  (three new evidence-mapping docs plus cross-link updates) plus an unaltered,
  operator-provided submodule gitlink — no external binary changes, no new
  runtime/execution engine, no new checkpoint-schema field, no
  distribution/packaging change, and no new CLI/gate surface. Rollback = revert
  merge commit `ca066a05` (additive documentation + gitlink changes only).
  **Verdict: READY.**

## Closure Tasks (this branch)

1. Compound-learning doc:
   `docs/compound/2026-08-08-state-vs-call-outcome-conflation-in-telemetry-mapping.md`
   — **done** (this branch).
2. This canonical closure artifact (this file) — **done**: `closure_pr`/
   `closure_merge_commit`/`closure_reviewed_head` populated below. *Correction
   (provenance-repair, post-#315): this file's `closure_merge_commit`/
   `closure_reviewed_head` frontmatter originally recorded `null` /
   `807016997feb24ed01f62825b48c6222339c812b` (an intermediate
   pre-final-push HEAD) instead of the actual PR #315 merge commit and true
   final reviewed HEAD; corrected here to `55bfb3454641fe0a68d03ef6736e8456297f6fc1`
   and `52032a5a57ee1038fbd20a076037a62917dbf06a` respectively. The repair
   branch's own merge commit is never self-referenced in these fields —
   they record #315's stable, already-merged provenance only.*
3. Session memory write + compaction to
   `docs/memory/compacted/2026-08-08-120S-082F-compacted.md` (verbose original
   archived to `docs/archive/memory/2026-08-08-ship-120-S-082-F-session.md`)
   — **done** (this branch).
