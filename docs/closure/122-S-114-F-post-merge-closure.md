---
shipment: 122-S
feature: 114-F
tasks: [114.001-T, 114.002-T, 114.003-T]
feature_pr: 318
merge_commit: d923820e29473cb24e0c4c7d76070b4d811d55a5
merged_at: "2026-08-08T20:23:52Z"
reviewed_head: b255143df7fb58ceae61a2d778fa74a31c5da6d3
closure_pr: null
closure_merge_commit: null
closure_reviewed_head: null
closure_status: READY
compaction_status: done
feature_terminal_status: done
feature_archived_status: done
---

# 122-S / 114-F Post-Merge Closure — Capability-Pack Runtime Detection + Pre-Merge-Install Checklist (Bounded, 47971057)

Shipment `122-S` implemented covering feature `114-F`: bounded per-pack
presence + version detection for the three optional capability packs
(`backlogit`, `engram`, `graphtor-docs`) in both `deploy-harness.ps1` and
`deploy-harness.sh` (and their `.tmpl` counterparts), plus a
pre-merge-install checklist report and supporting documentation. `114-F`
has exactly 3 children — `114.001-T`, `114.002-T`, `114.003-T` — all of
which are this shipment's task-only manifest, so `114-F` is fully covered
by `122-S` alone (no partial-feature sibling protection needed at
closure). This is the **final** shipment in the `120-S -> 121-S -> 122-S`
dark-mode sequence.

## Checkpoint Anomaly Disposition (operator-authoritative, this session)

Per the operator's explicit, expanded disposition at the start of this
session:

- Four specific historical checkpoint files —
  `checkpoint-20260802-192655.json`, `checkpoint-20260802-045420.json`,
  `checkpoint-20260725-233536.json`, `checkpoint-20260726-005804.json` —
  were already fully addressed **before** this session began, in a prior
  session's dirty worktree. The operator's own words: "We already
  addressed checkpoint issues before starting this session. Why are we
  having to do this again? This smells like a bug in the system
  somewhere."
- Root cause (per operator, corroborated by prior-session evidence): the
  first full checkpoint enumeration of the orchestrator session reported
  all four as valid `status: resolved`; shipment `093-S` is
  archived/shipped; the repaired dirty versions live in stash
  `ab16544a1636651d2368825d08cbd5e7c26ec755`. The apparent re-trigger
  happened only after Ship isolated those uncommitted repairs into that
  stash, which exposed the stale **committed** baselines underneath
  (malformed for the two 08-02 records, `status: active` for the two
  093-S records) as if they were a fresh unresolved anomaly. This is a
  persistence/worktree-isolation bug, **not** a new interrupted session.
- Per operator disposition, this session did **not** restore, resume,
  resolve, delete, or repair any of the four files, and did **not** touch,
  apply, pop, or drop stash `ab16544a...`.
- **Read-only re-verification this session** (non-mutating): raw
  `Get-Content` inspection of all four files' `"status"` field matched the
  operator's exact description — the two 08-02 files return no match for
  a simple `"status"` grep (malformed/shape-mismatched for this
  inspection method), and the two 093-S files (`checkpoint-20260725-233536.json`,
  `checkpoint-20260726-005804.json`) show `"status":"active"` in raw JSON.
  This confirms the disposition's factual basis without performing any
  mutation.
- **Stash `ab16544a1636651d2368825d08cbd5e7c26ec755`**: confirmed present
  at `stash@{0}`, byte-identical, via `git rev-parse "stash@{0}"` both
  before this session's work and again at this closure point. Never
  applied, popped, or dropped. ATV-Phoenix (referenced in the stash's own
  history) remains merged on `main`, untouched.
- Any checkpoint file **not** in this explicit four-file set continues to
  follow the standard fail-closed crash-resumption protocol; none were
  encountered this session.

## Merge Confirmation

- Feature PR **#318** ("feat(114-F): capability-pack runtime detection and
  pre-merge-install checklist (bounded)") merged to `main` at
  `2026-08-08T20:23:52Z` with merge commit
  `d923820e29473cb24e0c4c7d76070b4d811d55a5`. Confirmed via `git show
  --no-patch --format="%H %P" d923820e`: two parents
  (`9a3dc6a27724f57e58d858376e42c1042d83a574` prior `main` tip — itself
  the `121-S`/`113-F` post-merge closure merge — +
  `b255143df7fb58ceae61a2d778fa74a31c5da6d3` feature branch HEAD),
  preserving the P-009 merge-commit strategy. Confirmed ancestor of
  `origin/main` (`git fetch origin main` then `git merge-base
  --is-ancestor d923820e... origin/main` -> exit 0).
- Repo merge-strategy settings (P-009), verified before merge:
  `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false` — only "Create a merge commit" is possible.
  Post-merge, both parents confirmed present on the merge commit.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Reviewed HEAD, round 1 (feature implementation) | `498b5c6a` — local adversarial review across correctness/maintainability/security/constitution/template-integrity personas. Verdict `READY`, 0 P0/P1. |
| Reviewed HEAD, round 2 (post-Copilot-fix, final merged HEAD) | `b255143d` — PR body's Local Review Readiness block updated to this HEAD; Outcome `READY`. |
| Full local build / test evidence | `PYTHONPATH=src python -m unittest discover -s tests` (exact CI `test` job command) run at HEAD `498b5c6a`: 1412 tests, OK (12 skipped); re-run after the fix commit at HEAD `a1a9b9b3`/`b255143d`: 1414 tests, OK (13 skipped — 2 new detection tests added, 1 additional expected skip for the sh test class on native Windows). `uv run autoharness --help` smoke test PASS. |
| CI (PR #318) | `detect code changes`, `pipeline-topology (ambient)`, `test`, `ci gate` all **SUCCESS** at every polled HEAD. |
| Copilot review (PR #318) | **2 rounds**. Round 1 (HEAD `498b5c6a`): `COMMENTED`, 3 unresolved threads, all valid. Round 2 (HEAD `b255143d`, post-fix): `COMMENTED`, 0 new threads — clean. |
| P-018 copilot-review gate | `SATISFIED` at HEAD `b255143d` (`unresolved_thread_ids: []`), re-confirmed immediately before merge. |
| §1.9 pre-merge readiness (Checks 1–5) | PASS at HEAD `b255143d`: PR body Local Review Readiness block refreshed to this HEAD, outcome `READY`, P0=0/P1=0, full local build evidence recorded, zero unresolved follow-ups, Copilot/P-018 result explicitly recorded `SATISFIED`. |
| Review-fix cycles | 1 of 3 available cycles used (round 1 → fix → round 2 clean). |
| Fix-CI cycles | 0 — CI was green throughout every polled HEAD; no CI-remediation reruns required. |
| Dark-mode merge authorization | `DARK_MODE_MERGE_AUTHORIZED` for PR #318: PR in scope (`122-S`, final shipment in the `120-S -> 121-S -> 122-S` sequence), `merge_approval_pre_authorized: true` per the operator's bounded P-017 dark contract, §1.9 passed at HEAD, P-018 `SATISFIED` at HEAD (both re-verified immediately before merge, unconditionally), checks green, P-009/P-016 all passed. Admin fallback was pre-authorized but never invoked — the normal merge (`gh pr merge 318 --merge`) succeeded directly. |
| Worktree/PR topology (P-016) | Single worktree throughout; no parallel worktree created or used. `pipeline-topology` lifecycle gate PASS immediately before merge. |

### Round-1 Copilot review detail (3 threads, all fixed/replied/resolved)

1. **`scripts/deploy-harness.sh` line 194** — pipeline exit-status masking:
   `"$exe" --version 2>/dev/null | head -n1 || true` loses the version
   command's own exit code (the pipeline's status reflects `head`, further
   masked by `|| true`), so a broken runtime that prints output but exits
   nonzero is misreported `present`.
2. **`templates/scripts/deploy-harness.sh.tmpl` line 194** — identical bug,
   mirrored in the template source.
3. **`tests/test_deploy_harness_scripts.py` line 545** — the existing
   execution test (`test_checklist_report_prints_non_interactively`) was
   host-dependent/weak, only checking "some recommended-action category
   appears somewhere," never verifying specific per-pack status/version/
   action for all three runtimes across the present/undetectable branches.

**Fix** (commit `a1a9b9b3`): replaced the piped pattern in both sh files
with a plain command-substitution assignment
(`if raw_output="$("$exe" --version 2>/dev/null)"; then ...`) so the
command's own exit status gates detection directly, never a pipeline's.
Added two new fixture-driven test classes
(`DeployHarnessPs1ChecklistPackDetectionTests`,
`DeployHarnessShChecklistPackDetectionTests`) with controlled fake
executables reproducing the exact regression shape (exit nonzero, but
print output first) and asserting exact per-pack status/action mapping.
Full test suite re-run: 1414 tests, OK, 13 skipped.

**Reply**: posted to all 3 review comments via the shell-safe file-backed
`--field body=@file` pattern, each referencing fixing commit `a1a9b9b3`
with a detailed explanation.

**Resolution**: re-queried GraphQL `reviewThreads` to reconfirm each
thread ID, then resolved all 3 via `gh api graphql` `resolveReviewThread` —
all confirmed `isResolved: true`.

A new compound-learning doc,
`docs/compound/2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md`,
records the generalizable pattern: piping a version/health-check
invocation through a text filter (`head`/`grep`/`awk`/etc.) loses the
probed command's own exit status even under `pipefail`, because the
filter stage itself almost always exits `0`.

**Total this shipment: 3 Copilot review comments, all fixed -> committed
-> pushed -> replied -> GraphQL-resolved.** 1 of 3 authorized bounded-window
rounds used; round 2 was clean, no further thread surfaced.

## Runtime Verification

**Surface**: bounded detection-only logic added to `deploy-harness.ps1`/
`.sh` (and `.tmpl` counterparts) — reads real executable presence/version
via subprocess invocation, produces a non-interactive checklist report. No
new runtime/execution engine, no distribution/packaging change, no actual
install/provisioning execution (explicitly out of scope per the accepted
deliberation).

| Field | Evidence |
| --- | --- |
| Validator | Ship pre-merge/post-merge runtime verification |
| Surface adapter | CLI-help probe (`runtime_validation.validator_manifest` in `.autoharness/workspace-profile.yaml`) — the closest available automated surface for this template/script-level change; the detection logic itself was additionally exercised via the new fixture-driven unit tests (real subprocess invocation against controlled fake executables), which is the strongest available automated evidence for this bounded scope. |
| Runtime probe | `uv run autoharness --help` — exit 0, run both pre-merge (feature branch) and post-merge (fresh `origin/main` pull). `DeployHarnessPs1ChecklistPackDetectionTests` / `DeployHarnessShChecklistPackDetectionTests` — real subprocess execution against fixture executables covering `present` (exit 0 + version), the exact regression shape (exit 1 + stdout banner, now correctly classified `undetectable`/absent-of-valid-version rather than falsely `present`), and `absent` (no executable on PATH) branches for all three packs. |
| Preserve-invariant | "The autoharness CLI starts without import, packaging, or option-parsing failures" — HELD. "A runtime that exits nonzero after printing output is never misreported as `present`" — HELD (the exact bug this shipment's fix corrects; regression tests added). "The ps1 and sh detection scripts agree on classification for the same fixture shape" — HELD (both new test classes assert the same fixture shapes against both scripts; ps1 needed no fix, sh did). |
| Blocked prerequisites | Actual native package-manager provisioning/install execution across OS/pack combinations is explicitly deferred (Option C scope boundary) — no automation exists yet to probe that surface, and none was fabricated. |
| Verdict | **HELD** — the bounded detection surface was exercised pre-merge and post-merge with the evidence above; the deferred provisioning surface has no fabricated evidence and is explicitly called out as a blocked prerequisite, not silently skipped. |

## Backlog Reconciliation (single-artifact safe-close, P-015) + Feature Terminal-State Determination

### 122-S safe-close (this session, post-merge)

- **Manifest**: `custom_fields.items` = `114.001-T`, `114.002-T`,
  `114.003-T` (task-only shipment, 3 tasks, all `status: done` since the
  pre-merge task loop; verified again this session via
  `Get-ChildItem .backlogit/archive -Filter "114.*"` — all 3 present in
  archive, none remaining in queue).
- **Protected set**: covering feature `114-F` alone. Verified via
  `backlogit get 114-F --json` (`size_composition.members` = exactly the
  3 manifest tasks) and `Get-ChildItem .backlogit/{queue,archive} -Filter
  "114.*"` — the only `114.*` artifacts present are the 3 manifest tasks
  (archived) plus `114-F` itself (queue, `active`, pre-closure). No
  `114.*` siblings exist outside the manifest — `114-F` is genuinely fully
  covered by `122-S` alone.
- **Baseline integrity gate**: `git status --short -- .backlogit/` clean
  at closure-work start. `114-F` confirmed present in `.backlogit/queue/`
  (`Test-Path` -> `True`) before any archival mutation.
- **Manifest item archival**: all 3 manifest tasks were already in
  `.backlogit/archive/` at session-closure start (archived by the
  pre-merge task-completion loop, `status: done`) — classified
  `pre-archived` for all 3, no re-archival performed.
- **122-S shipment record**: moved live `status: shipped`
  (`backlogit move 122-S --status shipped`) -> verified live
  `status: shipped` -> `backlogit archive 122-S` -> verified
  `archived_status: shipped`. The cascade command `backlogit shipment
  ship` / `backlogit_ship_shipment` was **never** run.
- **Protected-set integrity**: `114-F` re-confirmed present in
  `.backlogit/queue/` (`Test-Path` -> `True`) immediately after the
  shipment-record close, and `git status --short` showed only the `122-S`
  record rename to archive plus log-file updates — no cascade.

### `114-F` covering-feature terminal-state determination (this session)

`114-F`'s only 3 children are exactly `122-S`'s manifest — confirmed via
`backlogit get 114-F --json` and `Get-ChildItem .backlogit/{queue,archive}
-Filter "114.*"`, which returns exactly `114.001-T` through `114.003-T`
(all `status: done`, all archived), and zero `114.*` matches remain
anywhere else. Per the established 121-S/119-S precedent for a
fully-covered feature, `114-F` was moved `status: active` -> `done`
(`backlogit move 114-F --status done`) -> verified live `status: done` ->
`backlogit archive 114-F` -> verified `archived_status: done`.

- **Provenance preserved**: `114-F`'s labels (`capability-packs`,
  `runtime-installer`, `"47971057"`, `deploy-preflight`, `bounded`) remain
  present and untouched in the archived record; `114-F` carries only the
  `harness_status: pending` custom field, unaffected by closure.
- **`47971057` tracker**: remains a label embedded in `114-F`'s own
  frontmatter, fully consumed by this shipment's bounded scope (Option C).
  Full provisioning-execution scope remains deferred and unchanged.
- **Remainder stash `ab16544a1636651d2368825d08cbd5e7c26ec755`**:
  confirmed present, untouched, byte-identical (`git rev-parse
  "stash@{0}"` matches exactly) both before and after this session's
  closure work — see "Checkpoint Anomaly Disposition" above.
- Closure index resync: **complete** — `backlogit sync` run after all
  archival mutations were committed, indexing 740 artifacts
  (`CLOSURE_INDEX_SYNC_OK`).

## Context Compaction (P-020)

- **Status: done** — mandatory per-merge `compact-context` invocation
  (`target: all`) performed this session. Candidate identified: this
  release unit's own just-written session memory (completed-work rule,
  Phase 2). Bounded Tier-1 consolidation performed: 1 file compacted, 0
  active checkpoints touched, 0 plans consolidated (none pending review
  consolidation for this release unit), 0 additional closure records
  compacted (none exceeded `threshold_days`).
- Session memory: written to
  `docs/memory/2026-08-08-ship-122-S-114-F-session.md`, then moved
  verbatim to `docs/archive/memory/2026-08-08-ship-122-S-114-F-session.md`
  as part of this compaction pass.
- Compacted memory: `docs/memory/compacted/2026-08-08-122S-114F-compacted.md`
  (decisions, files modified, key learnings/cross-references to the new
  compound doc, outcomes, provenance chain) — written during this
  compaction pass.

## Operational Closure

- **Healthy signals**:
  - Feature PR #318 merged with a merge commit (two parents; P-009
    preserved).
  - Local review `READY` (0/0/0/0) at final HEAD `b255143d`; 3 Copilot
    review comments across 2 rounds, all fixed, replied, and resolved —
    zero unresolved threads, re-confirmed via the P-018 gate immediately
    before merge.
  - CI green at every required check on every polled HEAD.
  - Backlog safe-close for `122-S` reconciled all 3 manifest tasks
    (already `pre-archived` by the merge commit's own pre-merge
    task-completion loop, so no re-archival action was needed for the
    tasks themselves) and then explicitly archived the `122-S` shipment
    record (`status: shipped` -> `archived_status: shipped`), without the
    forbidden cascade command; `114-F` was then archived as a separate,
    subsequent step (`status: done` -> `archived_status: done`) only after
    independently verifying all 3 children are archived and zero `114.*`
    descendants remain in queue.
  - Remainder stash `ab16544a1636651d2368825d08cbd5e7c26ec755` (historical
    checkpoint repairs + BED0DDED deliberation) confirmed present, ACTIVE,
    and byte-for-byte untouched throughout this session, per the
    operator's explicit expanded disposition.
  - This is the **final** shipment in sequence `120-S -> 121-S -> 122-S` —
    all three now shipped/closed. Dark-mode sequence complete.
- **Failure signals to watch**: none specific to this shipment's own
  closure. The bounded review window (max 3 additional rounds) was used
  for only 1 round; 2 rounds remain unused headroom, not a risk.
- **Follow-ups** (non-blocking; `closure_status: READY`):
  1. See
     `docs/compound/2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md`
     for the generalizable "shell pipeline exit-status masking in
     version-probe detection logic" pattern — a forward-looking lesson for
     any future shell-script detection/health-check logic, not an open
     defect in this shipment.
  2. Full native capability-pack runtime provisioning/install execution
     and supply-chain/OS-matrix design remain **deferred** per
     `docs/decisions/2026-08-07-capability-pack-runtime-installer-deliberation.md`
     Option C, tracked under label `47971057` — explicitly out of scope
     for this bounded shipment, unchanged.
  3. This is the final shipment in the dark-mode sequence — no successor
     shipment is queued as a direct continuation.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): the shipped capability is
  detection-only script/checklist/doc logic — no external binary changes
  beyond the bug fix itself, no new runtime/execution engine, no new
  distribution/packaging change, no actual provisioning executed. Rollback
  = revert merge commit `d923820e` (additive detection-script + checklist
  + doc changes only, plus the exit-status-masking bug fix which is itself
  a correctness improvement, not new behavior surface). **Verdict:
  READY.**

## Closure Tasks (this branch)

1. Compound-learning doc:
   `docs/compound/2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md`
   — **done** (this branch).
2. This canonical closure artifact (this file) — **done**.
3. Session memory write + compaction to
   `docs/memory/compacted/2026-08-08-122S-114F-compacted.md`
   (verbose original archived to
   `docs/archive/memory/2026-08-08-ship-122-S-114-F-session.md`) —
   **done** (this branch).
4. Mandatory P-020 `compact-context` (`target: all`) invocation —
   **done** (this branch): 1 memory file compacted (this release unit's
   own session memory, completed-work rule), 0 active checkpoints
   touched, 0 plans consolidated, 0 additional closure records compacted.
5. Closure index resync (`backlogit sync` CLI, 740 artifacts indexed) —
   **done** (this branch, after all archival mutations were committed).
6. Closure PR — to be opened from
   `post-merge/114-f-capability-pack-runtime-detection-pre-merge-install-checklist-122-s`
   -> `main`. Its own current-HEAD local review, CI, P-018 gate (if
   Copilot engages), and merge-commit-only merge are tracked on that PR
   directly, per the same provenance-repair convention used for prior
   closure PRs (values above will be corrected to the final merged
   HEAD/merge-commit once it merges).
7. **No follow-ups actioned by Ship in code this session** beyond the
   compound-learning doc above — the deferred provisioning-execution scope
   remains unchanged, per the accepted deliberation's Option C boundary.
