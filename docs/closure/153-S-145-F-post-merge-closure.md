---
shipment: 153-S
feature: 145-F
tasks:
    - 145.001-T
    - 145.002-T
feature_pr: 401
closure_pr: 402
merge_commit: fed1319bac9e1ac3c2f2eeb448390fbfc192f155
merged_at: "2026-08-23T00:32:27Z"
reviewed_head: d33dc898181d97055d70908f7820854659ff34f9
closure_merge_commit: null
closure_reviewed_head: null
closure_status: READY
compaction_status: done
---

# 153-S / 145-F Post-Merge Closure -- Mechanism B: BranchOwnershipTests Intra-File Order Pollution (Re-Measure at Mechanism-A Head)

Shipment 153-S executed mechanism B of the E8158860/9DD9E323 remediation
chain: re-measuring the `BranchOwnershipTests` intra-file order dependence
(`141.004-T`'s original standalone finding) at mechanism A's fixed head
(152-S). Both planned tasks (`145.001-T`, `145.002-T`) were completed per
`docs/plans/2026-08-22-git-config-env-containment-plan.md` Tasks 8-9 and
binding Amendment A10. This was a **measurement/diagnosis shipment**: no
production source code was changed. The evidence conclusively proved the
order dependence was already **SUBSUMED** by mechanism A's fix, not a
separate live defect requiring remediation.

## Merge Confirmation

- Feature PR #401 merged to `main` at `2026-08-23T00:32:27Z` with merge
  commit `fed1319bac9e1ac3c2f2eeb448390fbfc192f155`.
- Merge commit parents: `bbaf327fbf376da7ef7ae3134fd51cacef32f33f` (prior
  `main`, the 152-S closure-correction merge) and
  `d33dc898181d97055d70908f7820854659ff34f9` (merged feature HEAD) -- two
  parents confirmed via `git log --pretty="%H %P" -1`; P-009 merge-commit
  strategy preserved (repo settings confirmed `allow_merge_commit: true`,
  `allow_squash_merge`/`allow_rebase_merge` both `false`).
- `git merge-base --is-ancestor fed1319b... origin/main` confirmed exit 0.

## Pre-Merge Gate State (independently reverified)

| Gate | PR #401 |
| --- | --- |
| CI | green at final HEAD `d33dc898` (`ci gate` pass, `detect code changes` pass, `pipeline-topology (ambient)` pass; `test` check correctly SKIPPED -- this PR is backlog-metadata-only, no source/template paths touched; the canonical Windows full suite was independently re-run as part of the measurement task itself and is green: 1830 tests, OK, skipped=20) |
| P-018 Copilot review (`autoharness gate copilot-review`) | `SATISFIED` at final HEAD `d33dc898` (re-confirmed immediately before merge, unconditionally) |
| Copilot review threads | 1 round, 2 findings, both fixed in commit `d33dc898` and resolved -- see Review-Fix History below |
| P-014 local review readiness | `## Local Review Readiness` block present at reviewed HEAD `d33dc898`, outcome `READY`, 0 residual findings |
| Operator merge authorization | Explicit: operator selected bug `E8158860`, directed autonomous end-to-end completion of shipment 153-S specifically, scoped to mechanism B only |

## Review-Fix History

Round 1 (2 findings, commit `d33dc898`), both classified P-021 C1 in-scope
(same-contract-surface completions of `145.001-T`'s own evidence-recording
deliverable) and fixed directly, well within the 3-cycle review-fix budget:

1. `PRRT_kwDORzpWpM6bcM8E`: the originally recorded evidence in
   `.backlogit/archive/145.001-T.md` synthesized one-line pass/fail
   summaries instead of verbatim command output. Fixed by adding the full
   captured transcript (or a verified-representative tail for the
   104-test standalone run) for every measurement: the standalone run,
   each of the five current-code polluter->victim pairings, and each of
   the five reverted-code (A10 negative-control) pairings including full
   tracebacks.
2. `PRRT_kwDORzpWpM6bcM8J`: the original causal statement misattributed
   the leaked state to the per-test `GITHUB_HEAD_REF`/`GITHUB_REF_NAME`/
   `GITHUB_REF_TYPE` overrides. Corrected to match the established
   mechanism-A record (`.backlogit/archive/144-F.md:45-61`,
   `.backlogit/queue/145-F.md:50-54` at time of measurement): the ambient,
   ephemeral-shell `GIT_CONFIG_VALUE_2` is destructively deleted from the
   real Win32 environment block by `patch.dict`'s clear-then-update
   restore path on context-exit; the victim's git subprocess then fails
   config parsing, and `_run_git`'s designed `check=False` swallow
   launders that into `BRANCH_MISMATCH` / `exit_code == 1`.

Both replies cite commit `d33dc898`; both threads were resolved only after
the reply was posted. No P-021 C2 deferred-scope-expansion capture was
needed -- both findings passed the C1 same-contract-surface test.

## Runtime Verification

**Surface**: `cli` -- the only workspace-configured runtime validator
surface for this repository
(`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`).
This shipment made no production source changes at all; its "surface" is
entirely the `tests/test_gates_topology.py` measurement evidence and the
backlog metadata recording the `SUBSUMED` disposition.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` (`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`) |
| Runtime probe | `uv run autoharness --help` |
| Result | **PASS** -- exit 0 |
| Canonical gate | `uv run python -m unittest discover -s tests` (Windows) |
| Result | `Ran 1830 tests, OK (skipped=20)` -- 0 failures, 0 errors, matching the pre-existing 152-S baseline exactly (no regression) |
| Standalone module | `python -m unittest discover -s tests -p test_gates_topology.py` -- `Ran 104 tests, OK` (independently reconfirmed after the A10 negative-control throwaway edit was restored to byte-identical HEAD) |
| Hosted CI | green at final HEAD `d33dc898`; `test` check correctly SKIPPED (docs/backlog-only) |
| Manual checkpoints | none required -- measurement/diagnosis-only shipment, zero production behavior change |
| Blocked prerequisites | none |
| Verdict | **PASS** for runtime-verification purposes; mechanism B of the E8158860 chain is fully measured, proven `SUBSUMED` by mechanism A, and closed with zero new source changes |

### Other Gates

- Full build: non-applicable -- this shipment's diff is backlog-metadata-
  only (task/feature/shipment queue+archive+log records); the canonical
  Windows test suite above is the relevant regression evidence, and it is
  green.
- Quality Gates 1-4: PASS (YAML frontmatter validated for all touched
  `.md` files both before and after edits; no `{{VAR}}` placeholders
  involved; all cross-referenced files -- the plan, hardening doc, and
  `tests/test_gates_topology.py` -- exist).

## Backlog Reconciliation (P-015)

`classify_shipment_close_path(['145-F', '145.001-T', '145.002-T'],
'.backlogit')` -> **CASCADE** (`145-F` is a root, fully covered by both
manifest-member children `145.001-T`/`145.002-T`; the manifest contains
nothing beyond the qualifying root feature and its children). Re-verified
independently both pre-merge and post-merge with an identical result.

`backlogit shipment ship 153-S --sha fed1319bac9e1ac3c2f2eeb448390fbfc192f155`
was used in place of manual safe-close, per the P-015 verified
fully-covered-root exception.

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` | exact match: `145.001-T`, `145.002-T`, `145-F`, `153-S` -- nothing more, nothing less |
| `parent_id` preservation | both tasks re-read with `parent_id: 145-F`, unchanged |
| Live status | `145-F` archived (`status: archived`); `153-S` archived (`archived_status: shipped`) |

No out-of-manifest linked-deliberation sweep was observed (see
`docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`
for the known quirk this shipment was watched for; it did not recur
here).

## Operational Closure

- **Invariants to preserve**: the `SUBSUMED` disposition depends entirely
  on mechanism A's fix (152-S) remaining in place -- if `patched_environ`'s
  restore-by-diff semantics or the L0/L1/L2 Windows process topology from
  152-S are ever reverted or regressed, this shipment's evidence and
  disposition should be treated as invalidated and mechanism B
  re-measured.
- **Pre-deploy audits**: not applicable -- no production source, test
  behavior, migration, feature flag, configuration, or access-control
  surface was changed. This shipment is a diagnostic evidence record.
- **Deployment / rollout path**: merge-only; no separate deploy, canary,
  or phased-rollout step. There is nothing to "roll out" beyond the
  backlog record itself.
- **Risky action record**: not applicable -- no `ProposedAction` entries
  requiring approval, containment, or rollback beyond the standard
  operator-approved merge-commit-only merge (P-009) were taken.
- **Post-deploy checks**: none beyond the canonical full-suite gate
  already reconfirmed above; there is no new behavior to monitor.
- **Healthy signals**: PR #401 merged with a verified 2-parent merge
  commit; P-018 `SATISFIED` at final HEAD; both review findings fixed and
  resolved in a single review-fix cycle (well within the 3-cycle budget);
  backlog cascade-close archived exactly the manifest's 2 tasks, the
  feature, and the shipment record, with no unintended archival; repo
  merge-strategy settings confirmed merge-commit-only.
- **Failure signals to watch**: any future regression of mechanism A
  (152-S) that reintroduces destructive Windows `os.environ` restore
  behavior would very likely resurrect this exact intra-file order
  dependence; if `test_gates_topology.py`'s `BranchOwnershipTests` ever
  again appears to leak state into a later-run victim, re-open a
  measurement task rather than assuming this shipment's `SUBSUMED`
  disposition still holds.
- **Monitoring plan**: none required beyond ordinary CI; this is a
  one-time diagnostic shipment producing no new runtime surface.
- **Validation window**: immediate, at this post-merge closure
  (2026-08-23).
- **Rollback trigger**: not applicable in the conventional sense (no
  production behavior changed); if the recorded evidence is later found
  to be inaccurate or non-reproducible, correct the archived task record
  via a dedicated correction PR (as was done for 152-S, PR #400) rather
  than reverting the merge.
- **Rollback procedure**: `git revert` the `153-S`/`145-F` feature merge
  commit (`fed1319b...`) on `main` through a new reviewed PR, if ever
  needed.
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for
  merge approval and release follow-up routing.
- **Releasability evidence**: **READY**
  (`.autoharness/workspace-profile.yaml` `runtime_validation.releasability`:
  `required: false`, `status_when_satisfied: READY`, `required_evidence: []`
  -- no additional evidence beyond the runtime verification above is
  required for this workspace). Verified merge commit (two parents), green
  CI, P-018 `SATISFIED`, P-015 cascade-close independently re-verified
  pre- and post-merge, and P-020 compaction (see below). No residual
  risk, no accepted conditions, no open follow-ups requiring a
  `conditions:` block.
- **Follow-ups**: none outstanding for 153-S itself. `closure_pr`,
  `closure_merge_commit`, and `closure_reviewed_head` above are recorded
  truthfully at each stage of authorship (see note below) rather than
  invented in advance.

### Note on self-referential closure fields

`closure_pr` is populated once this closure PR is created (a normal,
externally-assigned GitHub PR number -- not self-referential).
`closure_reviewed_head` is populated once the final pre-merge commit on
this branch is known (the commit that Copilot/local review actually
evaluates -- also not self-referential, since no further edits are made
after that point). `closure_merge_commit`, by contrast, genuinely cannot
be known before GitHub creates the merge commit for this exact PR at
merge time, and this document cannot embed its own future hash without a
literal self-reference paradox (embedding the SHA would change the
content, which would change the SHA). Per `_closure_artifact_complete` in
`src/autoharness/gates/topology.py`, `closure_complete` for predecessor-
gating purposes depends ONLY on `compaction_status` and
`closure_status`/`conditions` -- never on `closure_pr`/
`closure_merge_commit`/`closure_reviewed_head` -- so leaving
`closure_merge_commit: null` here does not block any future predecessor-
closure check. If a future shipment's closure record ever needs this
field populated for traceability, it should be corrected via a small,
dedicated correction PR, exactly per the precedent established for
152-S/144-F (PR #400,
`docs/closure/152-S-144-F-post-merge-closure.md`), rather than invented
here.

## Compaction (P-020)

`compact-context --target all` was invoked on this post-merge closure
branch (per `templates/skills/compact-context/SKILL.md.tmpl` -- not
installed as a resolved `.github/skills/` copy in this self-hosting
repo). Candidate selection is threshold-gated; the just-closed release
unit's own fresh session memory qualified under the completed-work rule
(Phase 2). A bounded Tier-1 consolidation was performed: the verbose
session-memory file was summarized into
`docs/memory/compacted/2026-08-23-153s-145f-compacted.md` and the verbose
original moved to
`docs/archive/memory/2026-08-23-ship-153-s-mechanism-b-shipped-closure-in-progress.md`.
No plan-with-appended-review or closure-record candidates exceeded the
age/count/size thresholds this cycle, so no additional compaction was
performed. `compaction_status: done` above reflects this outcome.

**Closure verdict: READY.** Runtime verification passed, all review
findings were fixed and resolved in a single review-fix cycle, backlog
cascade-close is complete and independently re-verified both pre- and
post-merge, and P-020 compaction is complete. No residual risk or
accepted conditions are outstanding. No successor shipment was claimed in
this invocation. `closure_pr` and `closure_reviewed_head` will be filled
in via a small follow-up commit on this same branch once this closure
PR's number and final pre-merge commit are known (see note above);
`closure_merge_commit` remains permanently `null` per the self-referential
rationale documented above.
