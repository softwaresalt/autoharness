---
shipment: 142-S
feature: 133-F
feature_pr: 368
merge_commit: 093e09966696f1e753193105427acd9bd1c3a1dc
merged_at: "2026-08-18T23:01:49Z"
reviewed_head: 0e8cfab85059ee020b904f0956136273648cbb4e
staging_pr: 367
staging_merge_commit: ebe5c2d4900ffe729a664835c85636aa5a7974b5
staging_reviewed_head: bdd11713
closure_pr: 369
closure_reviewed_head: null
closure_status: READY
compaction_status: done
conditions: []
---

# 142-S / 133-F Post-Merge Closure — Repository Hygiene: Remove Stale Tracked Root Scratch Artifacts

Shipment 142-S removed three stale tracked scratch artifacts (`out.json`,
`res.json`, `results.json`) from the autoharness repository root -- accidental
`autoharness verify-workspace --format json` outputs for the *external*
`D:\Source\GitHub\backlogit` workspace, committed in `24777b44` with no
functional dependents -- and added a deterministic regression test
(`tests/test_repo_root_artifacts.py`) preventing recurrence via a tracked
root-level `*.json` allowlist (`{.mcp.json, plugin.json}`), rather than a
`.gitignore` rule (which cannot untrack already-tracked files and fails
silently).

Stash source: **1EFDA8EE** (harvested/published via staging PR #367).

Executed under **P-017 DARK_MODE_ACTIVE** as the final shipment in the
141-S -> 142-S global sequence, operator AFK, local-only visibility, intercom
unavailable.

## Staging Publication

Stage's harvested planning artifacts (task spec, plan, review, memory --
commit `5a499b62`) were not yet on `origin/main` when this session began.
Published via staging PR #367 (`chore/stage-142-S` -> `main`), merged with a
verified 2-parent merge commit `ebe5c2d4900ffe729a664835c85636aa5a7974b5`
(parents `957947ab...` + `bdd11713`).

Copilot review on the staging PR returned **3 valid threads**, all on the
same root cause: an unscoped `git diff --cached --stat` acceptance/assertion
command in the Stage-authored task spec and plan (`.backlogit/queue/133.001-T.md`
criterion 5; `docs/plans/2026-08-18-root-scratch-artifact-removal-plan.md`
Section 5.1 assertion 5 and Section 6 step 2) that would have incorrectly
included the pre-existing operator-staged `.gitmodules`/`references/*`
gitlink entries in its diff-stat count, causing Ship to falsely fail-closed
on an otherwise-correct deletion. All three were valid P1-equivalent
findings. Fixed by scoping the diff command to the three literal pathspecs
(`git diff --cached --stat -- out.json res.json results.json`) in commit
`bdd11713`; replied to each thread individually referencing the fixing
commit; resolved all three via GraphQL `resolveReviewThread`. Copilot's
follow-up re-review after resolution reported **1 suppressed comment**
(not a new open thread) on the plan document, unrelated to the resolved
findings -- concerning a missing machine-readable `## Plan Review` gate
marker block per the `plan-review`/`harvest` skill contract. This is a
Stage-owned planning-artifact concern outside Ship's role boundary (P-010:
Ship cannot edit deliberation/plan/review artifacts) and did not block
merge (suppressed, no open thread, 0 unresolved at merge time). P-018 gate
`SATISFIED` at HEAD `bdd11713` after resolution, 0 unresolved threads.

## Merge Confirmation

- PR #368 merged to `main` at `2026-08-18T23:01:49Z` with merge commit
  `093e09966696f1e753193105427acd9bd1c3a1dc`.
- Merge commit parents: `ebe5c2d4900ffe729a664835c85636aa5a7974b5` (staging
  publication) and `0e8cfab85059ee020b904f0956136273648cbb4e` (implementation
  HEAD) -- two parents, P-009 merge-commit strategy preserved and verified
  via `git cat-file -p`.
- `git merge-base --is-ancestor 093e0996... origin/main` confirmed exit 0.
- Closure began from synced `main` at `093e0996...`.

## Implementation Summary

**133.001-T** (delete stale tracked root scratch artifacts):
- Pre-deletion hash/size/line-count re-verification (immediately before
  `git rm`) matched the corrected Stage-provided evidence exactly:
  `out.json` SHA-256 `12F53D59...C525843` (26390 bytes, 588 lines);
  `res.json` and `results.json` both SHA-256 `8D6948EA...8635395` (26388
  bytes, 587 lines each) -- confirming the stash/F7 claim that all three
  were identical was false (`out.json` differs by one line), as Stage's
  correction stated.
- `git rm out.json res.json results.json` (three explicit literal
  pathspecs only; no wildcard, no broad cleanup).
- Scoped acceptance command
  `git diff --cached --stat -- out.json res.json results.json`: **3 files
  changed, 0 insertions(+), 1762 deletions(-)** = 588+587+587, matching
  exactly.
- Implementation commit `b2af432100128b420556be4ef42552e1f11a829e`; task-done
  archive-move commit `69094ecc`.

**133.002-T** (regression test, depends on 133.001-T):
- TDD: wrote `tests/test_repo_root_artifacts.py` while the three stale
  files were still present -> **RED** (test correctly named all three
  unexpected files). Deleted the files -> re-ran -> **GREEN**.
- Acceptance-criterion 3 (control-fires proof): temporarily restored
  `out.json` via `git show 24777b44:out.json` and staged it -> test
  **FAILED again**, correctly naming `out.json` as the sole unexpected
  entry -> reverted the restoration -> test **GREEN** again.
- Test uses `git ls-files` tracked-file semantics (not filesystem
  globbing/`.gitignore`), `skipTest`s if git is unavailable or the
  workspace is not a git checkout -- deterministic and cross-platform.
- Implementation commit `75de0399ccc02d974230815c151802d4f3309f21`;
  task-done archive-move commit `0e8cfab85059ee020b904f0956136273648cbb4e`.

Both tasks followed the established two-commit-per-task convention
(implementation commit bundling claim-cascade `.backlogit` state, then a
separate `chore(<task-id>): mark task done and track <x> commit`).

## Validation

- Targeted: `PYTHONPATH=src python -m unittest discover -s tests -p
  "test_repo_root_artifacts.py"` -> OK (1 test), both pre- and
  post-deletion, and during the criterion-3 restore/revert cycle.
- Full canonical suite (local): `PYTHONPATH=src python -m unittest discover
  -s tests` -> **1580/1581 pass, 20 skipped**. The single failure
  (`test_deploy_harness_scripts...test_checklist_report_prints_non_interactively`)
  is a pre-existing, deterministic (reproduced twice in isolation),
  environment-local-build artifact -- the file is byte-identical to `main`
  (zero diff introduced by this shipment) and the failure is caused by this
  workstation's locally-built `backlogit` CLI version string
  (`v1.9.0-39-g17530fe3-dirty ... update available`) not matching the
  test's expected "recommended-action category" text. **CI's own `test` job
  on PR #368 passed fully** (1m5s, all green), confirming this is a local
  build-environment artifact and not a real defect.
- Full build: non-applicable (no application/template/schema/CLI source
  changes; only tracked-artifact deletion, a new test file, and `.backlogit`
  bookkeeping).
- Quality Gates 1/3/4: PASS on all changed files (YAML frontmatter valid;
  zero `{{VAR}}` placeholders; `py_compile` clean).
- Repo-wide grep: zero functional/code/CI references to the three deleted
  filenames remain; only historical documentation (memory/review/stash
  archive) references them.

## Local Adversarial Review (multi-persona, report-only)

| Persona | Verdict |
| --- | --- |
| Correctness | PASS -- exact 3-file deletion matches pre-verified provenance |
| Test quality / anti-flake | PASS -- tracked-file semantics, skip-safe, RED->GREEN + control-fire proof |
| Security / content | PASS -- no secrets in deleted diagnostic output |
| Backward compatibility | PASS -- zero functional references remain |
| Process compliance | PASS -- two-commit convention, correct SHA tracking, protected state preserved, explicit-pathspec commits only |
| Scope adherence | PASS -- diff touches exactly the manifest members, zero unrelated stash/queue items touched |

Zero unresolved P0/P1 findings on either PR.

## Copilot Review (implementation PR #368)

Copilot reviewed all 12 changed files and **generated zero comments**
(confirmed via direct GraphQL query of `reviews`/`reviewThreads` -- a
genuinely clean review, not merely a no-request). P-018 gate `SATISFIED` at
HEAD `0e8cfab8`, 0 unresolved threads, re-confirmed unconditionally
immediately before merge (still `SATISFIED`, HEAD unchanged).

## CI

All required checks green on both PRs: `detect code changes`,
`pipeline-topology (ambient)`, `test`, `ci gate`.

## Runtime Verification

**Surface**: `cli` (per `.autoharness/workspace-profile.yaml`
`runtime_validation.validator_manifest.surfaces`) -- this shipment is a
tracked-artifact-deletion + test-only change with no CLI-observable
behavior change, so the `cli-help` smoke probe is the applicable and
sufficient surface.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` (CLI) |
| Runtime probe | `uv run autoharness --help` -- exit 0, prints CLI help text |
| Canonical gate | Full repo suite `PYTHONPATH=src python -m unittest discover -s tests` |
| Result | 1580/1581 pass, 1 pre-existing unrelated local-build flake (see Validation above), 20 skipped |
| Live gate exercise | `pipeline-topology --phase lifecycle` returned `exit_code: 0` at every invocation (pre-build, pre-PR-creation, pre-closure) |
| Verdict | **PASS** |

`releasability.required` is `false` in the workspace profile with
`required_evidence: []`, so `status_when_satisfied: READY` applies without
additional structured releasability artifact.

## Backlog Reconciliation

`classify_shipment_close_path(["133-F", "133.001-T", "133.002-T"],
".backlogit")` returned **CASCADE**: `133-F` is a root feature member (no
`parent_id`) whose only children (`133.001-T`, `133.002-T`) are both
manifest members -- a verified fully-covered root per the P-015 exception.

1. Snapshotted pre-close `parent_id: 133-F` on both tasks (already
   individually archived via ordinary Step 2 task-completion routing during
   implementation).
2. Invoked `backlogit shipment ship 142-S --sha 093e0996...`.
3. Result: `archived_ids: ["133.001-T", "133.002-T", "133-F", "142-S"]`
   (exact manifest + shipment record match), `returned_ids: []`,
   `shipment_status: "shipped"`.
4. Verified: `parent_id: 133-F` unchanged on both tasks post-cascade.
5. Gate decision: **CLOSED**.

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` | exact match: manifest + shipment record |
| `parent_id` preservation | confirmed unchanged (`133-F`) on both tasks |
| Live status | `142-S` -> `shipped` -> archived (`archived_status: shipped`); `133-F` archived (`archived_status: done`) |
| Protected set | none -- verified fully-covered root has no protected set by construction |
| `1EFDA8EE` stash entry | untouched |
| Unrelated stash/queue | untouched (git diff scoped exactly to manifest artifacts) |
| Protected operator state | `.gitmodules` + 3 reference gitlinks byte-identical throughout (verified before/after every checkout, commit, and the cascade mutation) |

Committed on `post-merge/133-f-repository-hygiene-remove-stale-tracked-root-scratch-artifacts`
per the Post-Merge Branch Protocol (closure mutations never land directly on
`main`).

## Operational Closure

- **Healthy signals**: staging PR #367 and implementation PR #368 both
  merged with verified 2-parent merge commits; full local test suite green
  apart from one confirmed pre-existing unrelated local-build flake; CI
  fully green on both PRs (including a clean `test` job pass on #368); P-018
  gate `SATISFIED` on both PRs after full thread resolution (3 threads on
  #367, 0 on #368); multi-persona adversarial review 0 P0/P1 on both;
  cascade close post-conditions independently verified.
- **Failure signals to watch**: none identified specific to this shipment.
- **Validation window**: immediate post-merge closure on 2026-08-18 after
  `main` synced to merge commit `093e0996...`, merged at
  `2026-08-18T23:01:49Z`.
- **Rollback trigger**: revert merge commit `093e0996...` if the new
  `tests/test_repo_root_artifacts.py` allowlist test is found to produce
  false positives against a legitimately-tracked new root-level JSON file
  not accounted for in `ALLOWED_ROOT_JSON` -- no such conflict observed;
  the allowlist is intentionally narrow (`.mcp.json`, `plugin.json`) and any
  future legitimate addition requires an explicit, reviewed allowlist
  update rather than a broad ignore rule.
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for
  merge approval and release follow-up routing.
- **Residual follow-up (non-blocking)**:
  1. During 133.001-T's commit-tracking step, a fabricated/incorrect commit
     SHA (`b2af43219cbf46d8a186b6bfd2b6b2a1f9a1b6c5`) was transiently tracked
     via `backlogit update --commit` before being caught and corrected to
     the real SHA (`b2af432100128b420556be4ef42552e1f11a829e`). At the time
     of implementation, the authoritative frontmatter `commit:` field in the
     archived record was single-valued and correctly held only the real
     implementation SHA; the erroneous value persisted only as a harmless
     historical entry in the append-only commit-links audit log (no CLI
     removal capability exists for this log; file-level surgery on an
     append-only audit trail was judged riskier than leaving the artifact).
     **Post-closure update**: the subsequent P-015 cascade `backlogit
     shipment ship` call (see Backlog Reconciliation above) itself rewrote
     the frontmatter `commit:` field on both `133.001-T` and `133.002-T` to
     the shipment merge SHA `093e09966696f1e753193105427acd9bd1c3a1dc` (the
     cascade operation stamps its own tracked SHA onto every archived
     manifest member it touches). The originally-tracked implementation SHAs
     (`b2af4321...` for 133.001-T, `75de0399...` for 133.002-T) remain
     accurate and traceable via git commit history and this closure
     document, but are no longer the live frontmatter value as of the
     cascade close -- this is expected cascade behavior, not a defect, and
     is recorded here so the evidentiary chain (implementation SHA ->
     cascade-overwritten merge SHA) is explicit rather than assumed static.
     No functional or provenance impact -- disclosed here for transparency.
     Process note: verify `git rev-parse HEAD` output length (40 hex
     chars) immediately before any `backlogit update --commit` call, as was
     done successfully for 133.002-T's tracking.

## Compaction (P-020)

`compact-context --target all` invoked per the mandatory per-merge trigger
(see closure PR for the recorded outcome). This shipment's own session
memory (`docs/memory/2026-08-18-ship-142-s-full-lifecycle-closure.md`)
qualifies under the completed-work rule regardless of age.

**Closure verdict: READY.** Runtime verification passed; backlog
reconciliation completed via the classifier-selected CASCADE path with all
post-conditions independently verified; protected operator-staged state
(`.gitmodules` + 3 reference gitlinks) preserved byte-for-byte throughout
the entire session with zero drift.
