---
shipment: 157-S
feature: 149-F
tasks:
    - 149.001-T
    - 149.002-T
    - 149.003-T
    - 149.004-T
    - 149.005-T
    - 149.006-T
    - 149.007-T
    - 149.008-T
    - 149.009-T
    - 149.010-T
    - 149.011-T
    - 149.012-T
    - 149.013-T
    - 149.014-T
    - 149.015-T
feature_pr: 420
closure_pr: 421
merge_commit: f93afa0eee8d228ff4a7ac54cf3b2b3b4ec5eeb9
merged_at: "2026-08-30T01:12:57Z"
reviewed_head: f5e19bea37cdfe656f5e13e194e950608fe39ac4
closure_merge_commit: null
closure_reviewed_head: null
closure_status: READY
compaction_status: done
---

# 157-S / 149-F Post-Merge Closure -- S1 Detector SDK, Evidence-Node Contract, and Gate Pre-Review Reader

Shipment 157-S (feature 149-F, 15 tasks) implemented a report-only, non-blocking
pre-review detector SDK: the node/evidence/outcome contract (D1-D8, canonical
8-value `status`), a schema-validated `detectors` registry block (both the
pointer and versioned `validation-gates` schema documents), a fail-closed
applicability engine (FC1/FC2), a DAG assembler with cycle detection, an
epoch-keyed append-only report emitter, the `autoharness gate pre-review`
CLI reader, and the first registered node (ART-01, a backlogit
section-marker conformance detector) with an RK1 falsification-gate
re-detection of a historical PR #202-style defect. Executed as the second
and final shipment in a bounded operator-authorized P-017 dark-factory
sequence (156-S then 157-S; 156-S was already merged, closed, and closure-
repaired at the time this shipment began).

## Merge Confirmation

- Feature PR #420 merged to `main` at `2026-08-30T01:12:57Z` with merge
  commit `f93afa0eee8d228ff4a7ac54cf3b2b3b4ec5eeb9`.
- Merge commit parents: `7674ca48362a358bd917d8c973a5325b5ff7ecd0` (prior
  `main`, the 156-S closure-repair merge) and
  `f5e19bea37cdfe656f5e13e194e950608fe39ac4` (merged feature HEAD) -- two
  parents confirmed via `git log --format="%H %P" -1`; P-009 merge-commit
  strategy preserved (repo settings confirmed pre-merge:
  `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false`).
- `git merge-base --is-ancestor f93afa0e... origin/main` confirmed exit 0.

## Pre-Merge Gate State (PR #420, independently reverified immediately before merge)

| Gate | PR #420 |
| --- | --- |
| CI | green at final HEAD `f5e19bea` (4/4 checks: `ci gate`, `detect code changes`, `pipeline-topology (ambient)`, `test`) |
| P-018 Copilot review (`autoharness gate copilot-review`) | `SATISFIED` at final HEAD `f5e19bea` (re-confirmed immediately before merge, unconditionally); `unresolved_thread_ids: []` after 8 review rounds |
| `pipeline-topology --phase lifecycle` | PASS (branch/worktree ownership, single active shipment `157-S`, worktree topology OK, shipment readiness with predecessor `156-S`) |
| P-014 local review readiness | `## Local Review Readiness` block present at reviewed HEAD `f5e19bea`, outcome `READY`, 0 unresolved P0/P1, full local build evidence (2018 tests, 0 failures/errors, 20 skipped) |
| Operator merge authorization | `DARK_MODE_ACTIVE` pre-authorization record (`merge_approval_pre_authorized: true`) for this exact scoped shipment's normal merge-commit PR; admin fallback not authorized and not used |

## Copilot Hosted Review -- 8 Rounds, All In-Scope P-021 C1 Fixes

Every finding across all 8 review rounds touched code/config/schema newly
introduced or mutated by this shipment's own commits (verified via
`git log main..HEAD -- <file>` before classifying each finding), so every
finding was a P-021 C1 same-contract-surface completion, never an
expansion. **Zero deferred stash entries were created for 157-S.**

| Round | Commit | Findings fixed |
| --- | --- | --- |
| 1 | `70500e87` | 6 findings (initial pass) |
| 2 | `75355f56` | 3 additional findings |
| 3 | `2e9425b5` | Report writer / ART-01 SHA/dirty-worktree/symlink-escape hardening |
| 4 | `78f79f07` | Producer `Evidence` contract enforcement (node_id + type) |
| 5 | `8438d3f8` | Remaining validator/producer SDK contract gaps |
| 6 | `a084a073` | D3 evidence-reference (`#evidence`) normalization + self-reference exemption; `waived`-status rejection (S10 reserved); ART-01 `applies_when` `.backlog/**` gap; `harness-manifest.yaml` checksum refresh |
| 7 | `9cd58458` | `applicability.py` uncaught `BacklogUnavailableError`; `assembler.py` non-JSON-serializable `details`/`provenance` |
| 8 | `f5e19bea` | Schema-mirror-mutated-in-place (`1.0.0.schema.json` restored, `1.1.0.schema.json` published); `tool_version_dims` required for `ast`/`coverage`/`api` producer kinds (schema + runtime backstop); strengthened `NodeResult` payload serializability check (mapping-type + full `to_dict()`); ART-01 `path.exists()` pathspec filter missed working-tree directory deletions |

All threads across rounds replied to (citing the fixing commit and
regression test names) and resolved via GraphQL. Round 8's schema-mutation
fix followed the repeatable procedure documented in
`docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`
(this repository's third occurrence of that bug class).

## Runtime Verification

**Surface**: `cli` -- the only workspace-configured runtime validator
surface (`.autoharness/workspace-profile.yaml`
`runtime_validation.validator_manifest`).

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` |
| Runtime probe | `uv run autoharness --help` |
| Result | **PASS** -- exit 0, CLI help printed |
| Manual checkpoints | none configured/required |
| Blocked prerequisites | none |
| Verdict | **PASS** -- satisfies `validation_expectations.minimum_verdict: PASS` for the single `required: true` surface `cli` |

### Other Gates

- Full build: PR #420's own Local Review Readiness record carries full
  local build evidence at the merged HEAD (2018 passed, 20 skipped); no
  additional full build run was required for this closure beyond the
  runtime probe above.
- Quality Gates 1-4: PASS -- YAML frontmatter validated for all touched
  `.md`/`.tmpl`/schema files; no `{{VAR}}` placeholders left unresolved in
  template output; all cross-referenced files exist (including the new
  `schemas/validation-gates/1.1.0.schema.json` mirror and its coupled
  test/doc references).

## Backlog Reconciliation (P-015)

`classify_shipment_close_path(['149-F','149.001-T'..'149.015-T'], '.backlogit')`
-> **CASCADE** (`149-F` is a root feature, fully covered at every depth by
its 15 manifest-member children; the manifest contains nothing beyond the
qualifying root feature and its children).

`backlogit shipment ship 157-S --sha f93afa0eee8d228ff4a7ac54cf3b2b3b4ec5eeb9`
was used in place of manual safe-close, per the P-015 verified
fully-covered-root exception.

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` (raw response) | 17 items -- `149-F`, all 15 `149.0NN-T` tasks, `157-S` |
| Two-set gate | `archived_ids - allowed_ids = {}` and `required_ids - archived_ids = {}` -- both empty, no discrepancy |
| `parent_id` preservation | all 15 tasks re-read with `parent_id: 149-F`, unchanged from the pre-close snapshot |
| Archived provenance | `149-F`: `archived_status: done`; `157-S`: `archived_status: shipped`, `commit: f93afa0eee8d228ff4a7ac54cf3b2b3b4ec5eeb9`; all 15 tasks: `archived_status: done` |

Index resynced via `backlogit sync` after all archival mutations (1026
artifacts indexed). All backlog reconciliation, compound learning, session
memory, and P-020 compaction commits were made on the dedicated
`post-merge/149-f-s1-detector-sdk-evidence-node-contract-and-gate-pre-review-reader`
branch, never committed directly to `main`, per the Post-Merge Branch
Protocol.

## Stash Disposition (P-021 C5)

**Zero** deferred scope-expansion entries were captured during 157-S's
execution or its 8 Copilot review rounds -- every finding across the entire
shipment lifecycle touched code/config/schema newly introduced or mutated
by this shipment's own commits and was fixed directly as an in-scope P-021
C1 completion. `.backlogit/stash.jsonl` carries no entry referencing
`157-S`/`149-F`/any `149.0NN-T` task (verified by direct grep before writing
this closure).

## Operational Closure

- **Invariants to preserve**: the D-9 canonical single-`status`-field
  contract on `NodeResult`; the D-10 pointer/versioned schema parity
  (`schemas/validation-gates.schema.json` and
  `schemas/validation-gates/1.1.0.schema.json` must remain structurally
  identical except `$id`); the immutable-versioned-snapshot convention for
  every published `schemas/{contract}/{version}.schema.json` mirror
  (`schemas/validation-gates/1.0.0.schema.json` must never be mutated again
  -- any future schema change under this contract must publish a new
  version); the INV-1/INV-2/INV-6/INV-7 no-persisted-graph / report-not-
  authoritative / single-detector / zero-backlogit-mutation invariants for
  `gate pre-review`.
- **Pre-deploy audits**: not applicable -- no distribution/packaging surface
  changed; the schema/CLI surface changes are covered by the runtime `cli`
  probe and the PR's own full-suite run (2018 tests).
- **Deployment / rollout path**: merge-only; no separate deploy, canary, or
  phased-rollout step. `gate pre-review` is report-only (exit 0/2 only,
  never blocking) so this shipment introduces no new blocking behavior for
  existing workspaces; a workspace with no `detectors` block continues to
  validate with zero nodes (back-compat preserved and tested).
- **Risky action record**: not applicable -- no `ProposedAction` entries
  requiring approval, containment, or rollback beyond the standard
  operator-pre-authorized merge-commit-only merge (P-009).
- **Post-deploy checks**: none beyond the runtime `cli` probe and the
  existing full-suite evidence already recorded on PR #420.
- **Healthy signals**: PR #420 merged with a verified 2-parent merge commit;
  P-018 `SATISFIED` at final HEAD after 8 rounds with zero unresolved
  threads; backlog cascade-close archived exactly the manifest's 15 tasks,
  the feature, and the shipment record (verified via live workspace state
  AND the raw `archived_ids` response, no discrepancy); repo merge-strategy
  settings confirmed merge-commit-only; zero P-021 deferred entries for the
  entire shipment lifecycle.
- **Failure signals to watch**: any future producer implementation for
  `kind: ast`/`coverage`/`api` must supply `tool_version_dims` (now enforced
  at both schema and runtime-loader level as of this shipment); any future
  edit to `schemas/validation-gates/1.1.0.schema.json` must be version-
  bumped again rather than mutated in place, per the same convention this
  shipment's round-8 fix restored.
- **Monitoring plan**: none required beyond ordinary CI; the shipped
  `test_legacy_1_0_0_mirror_preserved_unchanged` and
  `test_pointer_schema_mirrors_versioned_schema_except_id` tests are the
  durable regression guards for the schema-immutability and pointer/mirror-
  parity invariants going forward.
- **Validation window**: immediate, at this post-merge closure (2026-08-30).
- **Rollback trigger**: not applicable in the conventional sense; `gate
  pre-review` is report-only and additive. If a future defect is found in
  the detector SDK, correct it via a dedicated correction PR rather than
  reverting the merge.
- **Rollback procedure**: `git revert` the `157-S`/`149-F` feature merge
  commit (`f93afa0e...`) on `main` through a new reviewed PR, if ever
  needed.
- **Owner**: Ship agent for closure evidence; operator for merge approval
  and release follow-up routing.
- **Releasability evidence**: **READY**
  (`.autoharness/workspace-profile.yaml` `runtime_validation.releasability`:
  no additional evidence beyond the runtime verification above is required
  for this workspace). Verified merge commit (two parents), green CI,
  P-018 `SATISFIED`, P-015 cascade-close fully verified with no
  discrepancy, and P-020 compaction (see below) are all satisfied. No open
  conditions.
- **Follow-ups**: none outstanding for 157-S. This was the final shipment in
  the bounded P-017 dark-factory sequence (156-S -> 157-S); no successor
  shipment scope remains in this activation.

## Compaction (P-020)

`compact-context --target all` invoked as part of this closure. Per the
skill's mandatory-invocation/threshold-gated-selection contract, the bounded
Tier-1 consolidation candidate was this release unit's own just-closed
pre-execution planning memory:

- Compacted `docs/archive/memory/2026-08-28-stage-157s-pr414-review-fix-cycle-1.md`
  and `docs/archive/memory/2026-08-28-stage-157s-pr414-review-fix-cycle-2.md`
  (both superseded by the final execution record) into
  `docs/memory/compacted/2026-08-30-157-s-compacted.md`. Verbose originals
  moved to `docs/archive/memory/` (never deleted).
- `docs/memory/2026-08-30-ship-157-s-execution.md` (this session's own
  execution summary) was preserved uncompacted as the authoritative final
  record, consistent with the 156-S convention.
- `docs/memory/` file count: 43 -> 41 after this pass (still 1 file above the
  40-file manual-trigger threshold; total size ~467 KB, under the 500 KB
  threshold). No active-task checkpoints were touched. The residual
  above-threshold file count is noted for a future dedicated compaction pass
  and is not, by itself, a P-020 gap for this closure -- the mandate is
  invocation plus a bounded per-merge consolidation, both satisfied here.

`compaction_status: done` above reflects this actually-executed outcome.

### Note on self-referential closure fields

Consistent with the adopted convention (see
`docs/closure/154-S-146-F-post-merge-closure.md`,
`docs/closure/155-S-147-F-post-merge-closure.md`, and
`docs/closure/156-S-148-F-post-merge-closure.md`), `closure_merge_commit`
and `closure_reviewed_head` are left permanently `null` in this file. This
closure's own reviewed HEAD and merge commit (once merged) are recorded in
its own PR body's `## Local Review Readiness` section instead. `closure_pr`
is populated once the closure PR is opened.

**Closure verdict: READY.** Runtime verification passed, P-015 cascade-close
is complete and fully verified with no discrepancy, P-020 compaction is
complete, and zero P-021 deferred entries exist for this shipment's entire
lifecycle. No residual risk or open follow-up is outstanding for 157-S.
This closes the final shipment in the bounded P-017 dark-factory sequence
(156-S -> 157-S).
