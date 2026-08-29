---
shipment: 156-S
feature: 148-F
tasks:
    - 148.001-T
    - 148.002-T
    - 148.003-T
    - 148.004-T
    - 148.005-T
    - 148.006-T
    - 148.007-T
    - 148.008-T
feature_pr: 417
closure_pr: 418
merge_commit: ec894bf3a7c4c1ad91b97191f5f8a94177419c9f
merged_at: "2026-08-29T18:12:57Z"
reviewed_head: 8b7dae51b6d997aa324b414f4bb80e4d285ba5db
closure_merge_commit: null
closure_reviewed_head: null
closure_status: READY
compaction_status: done
---

# 156-S / 148-F Post-Merge Closure -- S0 Policy Registry and Review-Persona Layer Install/Restore

Shipment 156-S (`336F3AB7`) installed the policy registry (`workflow-policies.md`)
and the 13-artifact review-persona layer (`.github/agents/subagents/*.agent.md`,
rendered from their `.tmpl` sources) into the workspace, plus an end-to-end
verification suite (21 tests). Executed as the first shipment in a bounded
operator-authorized P-017 dark-factory sequence (156-S then 157-S; 157-S out
of scope for 156-S's own execution and untouched throughout).

**Repair disclosure**: this closure artifact was omitted from the original
post-merge closure PR #418 (which correctly performed the P-015 cascade-close,
compound learning, session memory, and P-020 compaction, but did not itself
create the `docs/closure/156-S-148-F-post-merge-closure.md` file the
`pipeline-topology` successor gate requires). The gap was surfaced when the
Orchestrator's `--phase pre_claim` check for 157-S correctly returned
`PREDECESSOR_CLOSURE_INCOMPLETE` (`closure_complete: null`, since
`docs/closure/` contained no matching artifact). This file is the repair,
created and merged via a dedicated `post-merge/156-s-closure-repair` branch
and PR under the existing P-017 dark-activation's merge pre-authorization
(scoped to this exact shipment's mandatory closure evidence). No other 156-S
fact changes as a result of this repair; all substantive closure work
(cascade-close, compaction, learnings) was already correctly completed and
merged in PR #418 -- only this evidentiary artifact was missing.

## Merge Confirmation

- Feature PR #417 merged to `main` at `2026-08-29T18:12:57Z` with merge
  commit `ec894bf3a7c4c1ad91b97191f5f8a94177419c9f`.
- Merge commit parents: `5f35c34b...` (prior `main`) and
  `8b7dae51b6d997aa324b414f4bb80e4d285ba5db` (merged feature HEAD) -- two
  parents confirmed via `git log --format="%H %P" -1`; P-009 merge-commit
  strategy preserved (repo settings confirmed pre-merge:
  `allow_squash_merge: false`, `allow_rebase_merge: false`).
- `git merge-base --is-ancestor ec894bf3... origin/main` confirmed exit 0.
- Post-merge closure PR #418 merged separately at `2026-08-29T18:52:43Z`
  with merge commit `4be87847631896a7eaf7a2daeb5069e0da3d3742` (2 parents:
  `ec894bf3...` and `3e31584c15916ee2a57082b9b75f58b8257af0d2`); this too
  was a normal merge-commit merge, no admin fallback, no squash/rebase.

## Pre-Merge Gate State (PR #417, independently reverified immediately before merge)

| Gate | PR #417 |
| --- | --- |
| CI | green at final HEAD `8b7dae51` (4/4 checks) |
| P-018 Copilot review (`autoharness gate copilot-review`) | `SATISFIED` at final HEAD `8b7dae51` (re-confirmed immediately before merge, unconditionally); `unresolved_thread_ids: []` after 2 review rounds (8 total findings: 4 fixed directly, 4 deferred per P-021) |
| `pipeline-topology --phase lifecycle` | PASS (branch/worktree ownership, single active shipment `156-S`, worktree topology OK) |
| P-014 local review readiness | `## Local Review Readiness` block present at reviewed HEAD `8b7dae51`, outcome `READY`, 0 unresolved P0/P1, full local build evidence (`uv run autoharness --help` PASS; full pytest suite 1925 passed / 20 skipped ambient via pre-push hook), all 4 deferred entry IDs recorded |
| Operator merge authorization | `DARK_MODE_ACTIVE` pre-authorization record (`merge_approval_pre_authorized: true`) for this exact scoped shipment's normal merge-commit PR; admin fallback not authorized and not used |

Closure PR #418 independently carried its own P-014/P-018 gates (SATISFIED
at final HEAD `3e31584c` after 2 Copilot doc-accuracy findings were fixed
directly and threads resolved) and its own `DARK_MODE_ACTIVE` pre-authorized
merge, per the Post-Merge Closure PR Local Review Gate.

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

- Full build: PR #417's own Local Review Readiness record carries full
  local build evidence at the merged HEAD (1925 passed, 20 skipped); no
  additional full build run was required for this closure beyond the
  runtime probe above. PR #418's push-time pre-push hook independently
  reconfirmed the identical full suite green (docs/backlog-only diff).
- Quality Gates 1-4: PASS -- YAML frontmatter validated for all touched
  `.md`/`.tmpl` files; no `{{VAR}}` placeholders left unresolved in template
  output (the D8-B misdiagnosis-and-correction below is precisely the
  finding that ensures this); all cross-referenced files exist.

## Material Transparency Disclosure -- D8-B Ratchet Misdiagnosis

Mid-execution, a `RatchetContractTests` regression on 4 D8-B variables
(`LANGUAGE_SAFETY_CHECKS`/`LANGUAGE_IDIOM_CHECKS`/
`LANGUAGE_ERROR_HANDLING_CHECKS`/`LANGUAGE_PERFORMANCE_CHECKS`) was initially
misdiagnosed as an acceptable RK-J residual and "fixed" by widening the
tolerated-unresolved-variable baseline. This was wrong: it would have masked
a genuine production regression (`autoharness verify-workspace` would exit 1
on any real Python-primary workspace, since the general variable-derivation
function never bound these 4 D8-B variables). The error was caught by
Copilot's PR #417 review, not by local review or the original diagnosis. The
real fix -- 4 pinned constants plus a binding block in `verify_workspace.py`,
gated on `primary_language == python` -- was applied and verified (commit
`3450837f`). Full account:
`docs/compound/2026-08-29-156-s-148-f-d8b-ratchet-misdiagnosis-and-copilot-catch.md`.

## Backlog Reconciliation (P-015)

`classify_shipment_close_path(['148-F','148.001-T'..'148.008-T'], '.backlogit')`
-> **CASCADE** (`148-F` is a root feature, fully covered at every depth by
its 8 manifest-member children; the manifest contains nothing beyond the
qualifying root feature and its children).

`backlogit shipment ship 156-S --sha ec894bf3a7c4c1ad91b97191f5f8a94177419c9f`
was used in place of manual safe-close, per the P-015 verified
fully-covered-root exception.

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` (raw response) | 11 items -- `148-F`, all 8 `148.00N-T` tasks, `031-DL` (linked deliberation, resolved via description-embedded reference), `156-S` |
| Two-set gate | `archived_ids - allowed_ids = {}` and `required_ids - archived_ids = {}` -- both empty, no discrepancy |
| `parent_id` preservation | all 8 tasks re-read with `parent_id: 148-F`, unchanged from the pre-close snapshot |
| Archived provenance | `148-F`/`031-DL`: `archived_status: done`; `156-S`: `archived_status: shipped`, `commit: ec894bf3a7c4c1ad91b97191f5f8a94177419c9f`; all 8 tasks: `archived_status: done` |

All backlog reconciliation, compound learning, session memory, and P-020
compaction commits were made on the dedicated
`post-merge/148-f-s0-policy-registry-and-persona-layer-install-restore`
branch, never committed directly to `main`, per the Post-Merge Branch
Protocol, and merged via PR #418.

**Operational observation (non-blocking)**: the `backlogit shipment ship`
cascade invocation took approximately 11 minutes wall time (vs. an expected
few seconds), traced to 8 orphaned `backlogit.exe mcp` background server
processes from prior sessions contending for lock/index files. This is a
host-process-hygiene issue, not a code defect in the P-015 cascade path;
recorded here as an operator follow-up recommendation (clean up orphaned
`backlogit.exe mcp` processes between sessions), not a P-021 capture.

## Stash Disposition (P-021 C5)

Four deferred scope-expansion entries were captured during 156-S's review
cycles, all pre-existing out-of-scope template gaps under the D4/R4
render-only discipline; none were resolved or archived by this shipment
(all `requires deliberation: true`, provisional priority/kind only, Stage
disposition pending):

- `C0EA1175` -- P-007 workflow-policies.md automatic-remediation approval-gate
  gap (local review, threadless capture).
- `701073F9` -- constitution-reviewer template missing Principle X/XI
  (PR #417 Copilot round 1, thread `PRRT_kwDORzpWpM6dbaC4`).
- `BA035180` -- security-reviewer purpose-based suppression rule can hide
  findings (PR #417 Copilot round 1, thread `PRRT_kwDORzpWpM6dbfbw`).
- `F0ADCC03` -- dangling `python.instructions.md` cross-reference in
  `python-reviewer.agent.md` (PR #417 Copilot round 2, thread
  `PRRT_kwDORzpWpM6dbrOF`).

All four remain active in `.backlogit/stash.jsonl`, correctly outside this
closure's disposition authority (P-010: reprioritization/archival is
Stage-only).

## Operational Closure

- **Invariants to preserve**: the D8-B binding block in
  `verify_workspace.py` must not regress back to an unbound/tolerated state;
  the ratchet-contract test's `EXPECTED_UNRESOLVED_VARIABLES` must remain
  `frozenset()` for this workspace's Python-primary profile.
- **Pre-deploy audits**: not applicable -- no distribution/schema/CLI
  surface changed beyond the D8-B binding fix and the manifest
  `primitive` field corrections, already covered by the runtime `cli` probe
  and the PR's own full-suite run.
- **Deployment / rollout path**: merge-only; no separate deploy, canary, or
  phased-rollout step.
- **Risky action record**: not applicable -- no `ProposedAction` entries
  requiring approval, containment, or rollback beyond the standard
  operator-pre-authorized merge-commit-only merges (P-009) were taken.
- **Post-deploy checks**: none beyond the runtime `cli` probe and the
  existing full-suite evidence already recorded on PR #417/#418.
- **Healthy signals**: PR #417 merged with a verified 2-parent merge commit;
  P-018 `SATISFIED` at final HEAD; backlog cascade-close archived exactly
  the manifest's 8 tasks, the feature, the linked deliberation, and the
  shipment record (verified via live workspace state AND the raw
  `archived_ids` response, no discrepancy); repo merge-strategy settings
  confirmed merge-commit-only; closure PR #418 and this repair both merged
  cleanly under the same pre-authorization.
- **Failure signals to watch**: any future rendering of
  `technology-reviewer.agent.md.tmpl` for a non-Python primary language
  should be checked against an equivalent binding-completeness audit,
  since the D8-B gap here was specific to the Python profile path.
- **Monitoring plan**: none required beyond ordinary CI; the shipped
  `test_template_variable_derivation_contract.py` ratchet test is the
  durable regression guard going forward.
- **Validation window**: immediate, at this post-merge closure repair
  (2026-08-29).
- **Rollback trigger**: not applicable in the conventional sense; if the
  D8-B binding fix is later found incorrect, correct it via a dedicated
  correction PR rather than reverting the merge.
- **Rollback procedure**: `git revert` the `156-S`/`148-F` feature merge
  commit (`ec894bf3...`) on `main` through a new reviewed PR, if ever
  needed.
- **Owner**: Ship agent for closure evidence; operator for merge approval
  and release follow-up routing.
- **Releasability evidence**: **READY**
  (`.autoharness/workspace-profile.yaml` `runtime_validation.releasability`:
  no additional evidence beyond the runtime verification above is required
  for this workspace). Verified merge commit (two parents, both PR #417 and
  #418), green CI, P-018 `SATISFIED` on both PRs, P-015 cascade-close fully
  verified with no discrepancy, and P-020 compaction (see below) are all
  satisfied. No open conditions.
- **Follow-ups**: none outstanding for 156-S itself beyond the 4 active
  P-021 deferred entries listed above (Stage-owned disposition, not a 156-S
  closure blocker). `157-S` remains queued and was not claimed, mutated, or
  implemented at any point during 156-S's execution or this closure repair.

## Compaction (P-020)

`compact-context --target all` performed manually as part of PR #418
(`templates/skills/compact-context/SKILL.md.tmpl` -- not installed as a
resolved `.github/skills/` copy in this self-hosting repo at time of
execution). Two pre-existing, now-superseded 156-S-only memory checkpoints
(`docs/memory/2026-08-28-ship-156s-u8-blocked-tool-outage.md`,
`docs/memory/2026-08-28-stage-156s-review-fix-cycle-3.md`) were consolidated
into `docs/memory/compacted/2026-08-29-156-s-compacted.md`; the verbose
originals were moved to `docs/archive/memory/`. Two other 156-S-referencing
memory files (`2026-08-28-stage-156s-blocked-review-repair.md`,
`2026-08-29-ship-staging-publication-156-s-157-s.md`) were deliberately left
uncompacted because they carry mixed scope with the still-queued,
still-active `157-S`/`149-F`. `compaction_status: done` above reflects this
outcome.

### Note on self-referential closure fields

Consistent with the adopted convention (see
`docs/closure/154-S-146-F-post-merge-closure.md` and
`docs/closure/155-S-147-F-post-merge-closure.md`), `closure_merge_commit`
and `closure_reviewed_head` are left permanently `null` in this file. This
closure repair's own reviewed HEAD and merge commit are recorded in its own
PR body's `## Local Review Readiness` section instead.

**Closure verdict: READY.** Runtime verification passed, P-015 cascade-close
is complete and fully verified with no discrepancy, P-020 compaction is
complete, and all 4 active P-021 deferred entries are correctly recorded
and outside this closure's disposition authority. No residual risk or open
follow-up is outstanding for 156-S. No successor shipment (`157-S`) was
claimed, mutated, or implemented at any point. This repair closes the sole
gap (`closure_complete: null`) that blocked the `pipeline-topology`
successor-readiness check for `157-S`.
