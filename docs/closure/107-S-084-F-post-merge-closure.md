---
shipment: 107-S
feature: 084-F
tasks: [084.001-T, 084.002-T, 084.003-T, 084.004-T, 084.005-T, 084.006-T, 084.007-T, 084.008-T]
feature_pr: 273
merge_commit: 364f6b07abc2418ec9f696603d5da4b9cf879256
merged_at: "2026-08-01T19:25:34Z"
reviewed_head: 25ab0c8fcd3c60094890f48c590c8c7515397912
closure_status: READY
compaction_status: done
---

# 107-S / 084-F Post-Merge Closure — Token-efficiency telemetry event emission and deterministic epoch composition

Shipment `107-S` (feature `084-F`) added a bounded, per-tool `ToolTelemetryEvent`
JSONL journal and a deterministic event-to-epoch composer that folds observed
tool events into the close-time telemetry payload (`--compose-tool-events`),
wired through `autoharness telemetry event` / `telemetry record` and the Ship
agent task loop. All 8 tasks (`084.001-T`..`084.008-T`) were completed by the
prior Ship session; this session resumed ownership at PR review remediation
and carried the shipment through Copilot hardening, merge, and closure.

## Merge Confirmation

- PR **#273** merged to `main` at `2026-08-01T19:25:34Z` with merge commit
  `364f6b07abc2418ec9f696603d5da4b9cf879256`.
- The merge commit has **two parents** (`a837b7a3979089246a428ec3232de2d1878ddeee`
  base + `25ab0c8fcd3c60094890f48c590c8c7515397912` feature HEAD), preserving the
  P-009 merge-commit strategy. Repo settings verified pre-merge:
  `allow_merge_commit: true`, `allow_squash_merge: false`, `allow_rebase_merge: false`.
- Merge SHA confirmed as ancestor of `origin/main` (`merge-base --is-ancestor`
  exit 0); local `main` fast-forwarded to `364f6b0`. Closure work was cut from
  synced `main` on branch `post-merge/084-token-efficiency-telemetry-metrics`
  (an initial backlog-archival commit was mistakenly made directly on `main`
  before the branch was cut — caught immediately, `main` was hard-reset to the
  merge commit before it was pushed, and the archival was redone correctly on
  the post-merge branch; no bad state reached `origin/main`).

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Reviewed HEAD | `25ab0c8fcd3c60094890f48c590c8c7515397912` (== PR HEAD at merge) |
| Local review (adversarial, code-review subagent) | **READY** — P0=0, P1=0 |
| §1.9 pre-merge readiness (Checks 1–5) | **PASS** at HEAD `25ab0c8` |
| P-018 copilot-review gate | **SATISFIED** (exit 0, 0 unresolved threads; re-run unconditionally immediately before merge — still SATISFIED, HEAD unchanged) |
| Copilot shadow review | round 2 — 6 threads, all fixed via TDD + replied with fixing SHA + resolved via GraphQL; final review submitted `2026-08-01T19:22:25Z` against `25ab0c8` |
| CI (`ci gate`, `detect code changes`, `test`) | all **pass** on final HEAD; mergeState CLEAN / MERGEABLE |
| Full build (`uv build`) | succeeded |
| Full unittest gate (`PYTHONPATH=src uv run python -m unittest discover -s tests`) | **905 passed, 7 skipped, 0 failed** |
| Review-fix cycles | **2 / 3** — cycle 1 (prior session): parent_event_id P1 fix (`1c09212`); cycle 2 (this session): 6-thread Copilot hardening batch (`25ab0c8`). Fix-CI cycles: 0 / 5 |

## Copilot Review Round 2 (P-018 engaged, this session)

| # | Thread | File | Finding | Resolution |
| --- | --- | --- | --- | --- |
| 1 | `PRRT_kwDORzpWpM6Vnq_G` | `tool_event.py` | schema permits arbitrary non-whitespace `event_id`, parser forced UUID | preserve caller-supplied ID; generate UUID only when omitted |
| 2 | `PRRT_kwDORzpWpM6Vnq_M` | `tool_event.py` | `evidence_path`/`artifact_refs` accepted absolute/traversal paths | added `validate_event_workspace_references()` incl. symlink-escape checks, wired into CLI before journal append |
| 3 | `PRRT_kwDORzpWpM6Vnq_P` | `tool_event_jsonl.py` | segment I/O failure returned partial events; `record_epoch` composed an undercount | `read_events()` returns `status="unavailable", events=()` on any segment I/O failure; composition skipped |
| 4 | `PRRT_kwDORzpWpM6Vnq_V` | `tool_event_compose.py` | no diagnostics when cumulative token values decrease out of order | added `_non_monotonic_diagnostics()` for both cumulative streams; `max()` aggregation retained |
| 5 | `PRRT_kwDORzpWpM6Vnq_h` | `tool_event_compose.py` | zero metrics contributed to provenance quality | `_metric_contributes()` restricts aggregation to strictly-positive contributors |
| 6 | `PRRT_kwDORzpWpM6Vnq_l` | `tool_event.py` | non-object/non-null `work_sizing_snapshot` silently became `None` | `from_mapping()` now raises `ToolTelemetryEventError` for strict-ingestion violations |

All 6 fixes landed in commit `25ab0c8` with 25 new focused TDD tests (red
confirmed before each fix, green after). All 6 threads replied to with the
fixing SHA before GraphQL resolution — reply-then-resolve ordering preserved.
Full narrative and reusable lessons captured in
`docs/compound/107-S-084-F-copilot-review-fix-patterns.md`.

## Runtime Verification

**Surface**: `runtime_validation.validator_manifest` declares one surface,
`cli`, with a single required probe (`cli-help`).

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | CLI (command) |
| Runtime probe | `uv run autoharness --help` (probe `cli-help`, required) |
| Result | **PASS** — exit 0, CLI help printed (stdout + exit-code evidence), run post-merge on the closure branch cut from synced `main` |
| Preserve-invariant | "The autoharness CLI starts without import, packaging, or option-parsing failures" — HELD |
| Manual checkpoints | none defined |
| Blocked prerequisites | none |
| Release blocker (`The CLI help smoke check fails`) | NOT triggered |
| Verdict | **PASS** (meets `minimum_verdict: PASS`; `surfaces_expected: [cli]`) |

No unsupported automation was fabricated. The new telemetry event CLI
subcommand (`autoharness telemetry event`) and the `--compose-tool-events` flag
on `telemetry record` are additive surfaces exercised extensively by the 905-test
unittest suite (including the 3 new CLI-layer tests added this session for path
validation); the declared validator manifest only requires the `cli-help` smoke
probe, which passed cleanly post-merge.

## Backlog Reconciliation (single-artifact safe-close, P-015 / 097-S)

Safe-close used per-item / single-artifact operations only. The cascade command
`backlogit shipment ship 107-S` was **not** run.

| Item | Final state |
| --- | --- |
| `084.001-T`–`084.008-T` (manifest tasks) | pre-archived by the prior Ship session (present in `.backlogit/archive/` at closure start); manifest-item skip applied; status `done` |
| `107-S` (shipment record) | archived as a single artifact (`backlogit archive 107-S`) |
| `084-F` (covering feature — **protected set**) | **preserved in `.backlogit/queue/` — NOT cascaded** |

- **Protected set = {`084-F`}**: all 8 tasks under `084-F` are exactly the
  manifest tasks; no unshipped sibling tasks exist under the feature (confirmed
  by enumerating `.backlogit/queue/084.*-T.md` and `.backlogit/archive/084.*-T.md`
  — the 8 archived tasks are the complete set). Baseline gate (`084-F` present in
  queue before mutation), verify-after-each (`git status -- .backlogit/`), and the
  P-007 post re-verify confirmed `084-F` stayed in queue throughout, with the only
  queue→archive relocation being `107-S.md` (the shipment, expected). Closure
  index resynced (`backlogit sync` → 620 artifacts indexed) both before and after
  the archival.
- **Correction note**: the archival + commit were first executed directly against
  `main` in error, immediately detected against the Post-Merge Branch Protocol,
  and remediated by hard-resetting the unpushed `main` commit and redoing the
  identical archival on `post-merge/084-token-efficiency-telemetry-metrics`. No
  corrupt or bypassing state was ever pushed to `origin/main`.

## Context Compaction (P-020)

- **Status: `done`** (bounded Tier-1 per-release-unit post-merge floor).
  Invoked `compact-context` (target: all). Assessment: `docs/memory` = 14 files
  (< 40 file-count threshold; 82.5 KB, < 500 KB) — no over-threshold date-bucket
  sweep due; `docs/plans` (29 files) and `docs/closure` (8 files) scanned.
- **Memory**: the just-closed release unit's session memory
  (`docs/memory/2026-08-01-ship-107-S-084-F-session.md`) qualified under the
  completed-work rule (Phase 2). Compacted to
  `docs/memory/compacted/2026-08-01-107S-084F-compacted.md`; verbose original
  moved to `docs/archive/memory/2026-08-01-ship-107-S-084-F-session.md`.
- **Plan consolidation**: `docs/plans/2026-07-31-token-efficiency-telemetry-emission-plan.md`
  was a candidate — feature `084-F` complete **and** the plan carried two
  appended review-cycle sections (Phase 2 criterion). Converted to a
  decided-plan at
  `docs/plans/2026-07-31-token-efficiency-telemetry-emission-decided-plan.md`
  (surviving implementation units, key decisions, post-harvest PR hardening,
  protected invariants, rollback, r1–r3 revision log), and the verbose original
  moved to
  `docs/archive/plans/2026-07-31-token-efficiency-telemetry-emission-plan.md`
  (`superseded_by` lineage recorded in its frontmatter). Because the move
  changed the plan's path, every reference was repointed to a resolving
  target: the **live** source files
  (`src/autoharness/telemetry/tool_event.py`,
  `src/autoharness/telemetry/tool_event_compose.py` — 4 docstring references)
  now point at the **decided-plan**, while **historical** records (the 8
  archived task snapshots `.backlogit/archive/084.001-T.md`–`084.008-T.md` and
  the historical Stage session memory
  `docs/memory/2026-07-31-stage-group-and-stage-next.md`) point at the
  **archived** path. The append-only audit log
  `.backlogit/logs/084-F.jsonl` was left untouched (immutable historical
  record, same treatment as git history). No dangling reference to the old
  `docs/plans/...` path remains. Targeted tests
  (`test_telemetry_tool_event`, `test_telemetry_tool_event_compose` — 80 tests)
  re-run green after the docstring edits.
- **Closure records**: the only 084-F closure artifact is this document,
  authored in this same pass; not over `threshold_days` old — no closure-record
  compaction.

## Operational Closure

- **Healthy signals**:
  - Feature PR #273 merged with a merge commit (two parents; P-009 preserved).
  - Local review READY (P0=0/P1=0); §1.9 all-checks PASS; P-018 SATISFIED across
    both Copilot rounds (6 threads round 2, all resolved).
  - CI green at every merge gate; CLI smoke probe PASS; full unittest suite
    905 passed / 7 skipped / 0 failed; `uv build` succeeded.
  - Backlog safe-close archived the shipment without the forbidden cascade;
    covering feature `084-F` preserved throughout, including through the
    main-branch mis-commit correction.
  - Reusable review-fix lessons captured in
    `docs/compound/107-S-084-F-copilot-review-fix-patterns.md`.
- **Failure signals to watch**:
  - Any future `ToolTelemetryEvent.from_mapping()` change that reintroduces
    fail-open coercion for `work_sizing_snapshot` or re-normalizes a
    caller-supplied `event_id` to a UUID unconditionally.
  - Any `record_epoch` path that composes against a `read_events()` result
    without checking for `status == "unavailable"` first.
  - Divergence between `validate_event_workspace_references()`'s containment
    logic and `context.py`'s `_is_within` convention (should stay aligned).
  - Recurrence of the main-branch-mis-commit pattern: always cut
    `post-merge/{slug}` from synced `main` **before** running any backlog
    archival or other closure mutation.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): monitoring — the tool-event journal is
  bounded/segmented and additive-only (no destructive migration); rollback =
  revert merge commit `364f6b0` (all changes are additive CLI/telemetry code +
  tests + docs, no schema/data migration); validation window = immediate
  post-merge on 2026-08-01 after `main` synced to `364f6b0`; owner = Ship agent
  (closure evidence), operator (merge approval, dark-contract pre-authorized for
  scope `107-S`). **Releasability: READY.**
- **Follow-ups**: none blocking. No P2/P3 findings were raised in the final
  Copilot round requiring separate backlog tracking (all 6 findings were fixed
  inline as P1-equivalent hardening items in this pass). Per the Ship role
  boundary (P-010), no new backlog/stash items were created by this session;
  any future refinement ideas would route through Stage.

**Closure verdict: READY.** Merge confirmed (P-009 preserved, two-parent commit
`364f6b0`), local review + §1.9 + P-018 gates passed across both Copilot rounds,
runtime CLI probe PASS + full suite 905 passed/7 skipped/0 failed, single-artifact
safe-close complete with the protected feature `084-F` intact throughout
(including recovery from an in-session main-branch mis-commit), and P-020 context
compaction is being invoked as the immediate next step in this closure pass.
