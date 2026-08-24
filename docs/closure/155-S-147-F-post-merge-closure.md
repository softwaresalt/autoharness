---
shipment: 155-S
feature: 147-F
tasks:
    - 147.001-T
    - 147.002-T
    - 147.003-T
    - 147.004-T
feature_pr: 407
closure_pr: 408
merge_commit: a7aa820e3c7dbb96e95bb8376e3022a229b55cb1
merged_at: "2026-08-24T22:06:39Z"
reviewed_head: 4552a11369acc73ae49016a9db535fb61b33bfa2
closure_merge_commit: null
closure_reviewed_head: null
closure_status: READY
compaction_status: done
---

# 155-S / 147-F Post-Merge Closure -- P-015 / shipment-reconcile cascade-close `archived_ids` two-set gate

Shipment 155-S corrected a false "full-set equality" safety-invariant claim
in the P-015 policy and the `shipment-reconcile` skill's cascade-close
post-condition, replacing it with a two-set `allowed_ids` / `required_ids`
gate that matches actual Backlogit engine semantics (`archived_ids` is a
transition log of artifacts actually transitioned during the invocation,
not a manifest echo). Deliberation `027-DL`; plan
`docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-plan.md`
(hardened per the companion hardening doc); review
`docs/reviews/2026-08-24-cascade-close-archived-ids-postcondition-review.md`
(PASS at cycle 1 of 3, later extended through 13 review-fix cycles for
Copilot-raised findings, 0 unresolved P0/P1 at final HEAD). This closure
resolves deferred scope expansion `5CFA8198`, captured at 154-S/146-F
closure, per that entry's own explicit archive condition.

## Merge Confirmation

- Feature PR #407 merged to `main` at `2026-08-24T22:06:39Z` with merge
  commit `a7aa820e3c7dbb96e95bb8376e3022a229b55cb1`.
- Merge commit parents: `f983c78a406f55bf97d1d9a386364026516eb049` (prior
  `main`) and `4552a11369acc73ae49016a9db535fb61b33bfa2` (merged feature
  HEAD) -- two parents confirmed via `git log --format="%H %P" -1`; P-009
  merge-commit strategy preserved (repo settings independently reconfirmed
  before merge: `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false`).
- `git merge-base --is-ancestor a7aa820e... origin/main` confirmed exit 0.

## Pre-Merge Gate State (independently reverified immediately before merge)

| Gate | PR #407 |
| --- | --- |
| CI | green at final HEAD `4552a113` (`ci gate` pass, `detect code changes` pass, `pipeline-topology (ambient)` pass, `test` pass) |
| P-018 Copilot review (`autoharness gate copilot-review`) | `SATISFIED` at final HEAD `4552a113` (re-confirmed immediately before merge, unconditionally); `unresolved_thread_ids: []` |
| `pipeline-topology --phase lifecycle` | PASS (branch/worktree ownership, single active shipment `155-S`, worktree topology OK) |
| P-014 local review readiness | `## Local Review Readiness` block present at reviewed HEAD `4552a113`, outcome `READY_WITH_FOLLOWUPS`, 0 P0/P1 from local adversarial review (all 20 Copilot-raised findings across cycles 4-13 fixed/replied/resolved), full local build evidence (`uv run autoharness --help` PASS; `uv run python -m pytest tests` 1880 passed, 20 skipped, 1422 subtests passed, 1 pre-existing unrelated `.mcp.json`-driven failure documented and reconfirmed, not introduced by this branch) |
| Operator merge authorization | Explicit: "PR 407: Merge approved" authorized the NORMAL MERGE-COMMIT merge of PR #407 only; admin fallback not authorized (not used); a dedicated post-merge closure PR requires separate approval per the same instruction |

## Merge Execution

`gh pr merge 407 --merge --repo softwaresalt/autoharness` (no `--admin`,
normal merge path only). No admin fallback, no squash, no rebase.

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

- Full build: the PR's own Local Review Readiness record already carries
  full local build evidence at the merged HEAD (1880 passed, 20 skipped,
  1422 subtests passed); no additional full build run was required for
  this closure beyond the runtime probe above.
- Quality Gates 1-4: PASS -- YAML frontmatter validated for all touched
  `.md`/`.tmpl` files; no `{{VAR}}` placeholders left unresolved in
  template output; all cross-referenced files (plans, review, deliberation
  027-DL, prior closure 154-S-146-F) exist.

## Backlog Reconciliation (P-015)

`classify_shipment_close_path(['147-F','147.001-T','147.002-T','147.003-T','147.004-T'],
'.backlogit')` -> **CASCADE** (`147-F` is a root, fully covered at every
depth by its four manifest-member children; the manifest contains nothing
beyond the qualifying root feature and its children).

`backlogit shipment ship 155-S --sha a7aa820e3c7dbb96e95bb8376e3022a229b55cb1`
was used in place of manual safe-close, per the P-015 verified
fully-covered-root exception -- this shipment's own newly-shipped
`shipment-reconcile` two-set gate governs this closure.

**Pre-close declared-status snapshot** (captured before the cascade
invocation, per Step 0(b)/(c) of the shipment-reconcile skill): `147-F`
`status: active`; `147.001-T`/`147.002-T`/`147.003-T`/`147.004-T` were each
**already relocated to `.backlogit/archive/`** by PR #407's own
task-completion commits, but each declared `status: done` -- **not**
`status: archived` -- i.e. directory-archived but not truly (hard-)
archived, the identical "relocated via `move --status done`, never stamped
`archived`" pattern the 154-S/146-F closure and this shipment's own
corrected contract both describe. Linked deliberation `027-DL` (referenced
by `147-F`) was the only member already truly `status: archived`
pre-close.

| Check | Result |
| --- | --- |
| `returned_ids` | `[]` |
| `archived_ids` (raw response) | `["147.001-T","147.002-T","147.003-T","147.004-T","147-F","155-S"]` -- ALL SIX manifest+shipment artifacts |
| Live workspace archive presence | ALL SIX artifacts confirmed archived: `147-F`, `147.001-T`, `147.002-T`, `147.003-T`, `147.004-T`, `155-S`; none remain in `.backlogit/queue/` |
| `parent_id` preservation | all four tasks re-read with `parent_id: 147-F`, unchanged from the pre-close snapshot |
| Archived provenance | `147-F`/`147.001-T`/`147.002-T`/`147.003-T`/`147.004-T`: `status: archived`, `archived_status: done`; `155-S`: `status: archived`, `archived_status: shipped`, `commit: a7aa820e3c7d...` |
| Linked deliberation `027-DL` | already truly `status: archived` pre-close (`archived_status: queued`); correctly NOT re-added to `archived_ids` (no transition to report) |

**Note on the corrected `archived_ids` behavior**: `147.001-T` through
`147.004-T` were **not** truly pre-archived pre-close (declared
`status: done`, only directory-relocated) -- under the corrected two-set
gate, `required_ids` therefore **mandatorily** includes all four of them,
the qualifying feature `147-F`, and the shipment record `155-S` itself.
Their appearance in `archived_ids` is not the optional pre-archived-omission
behavior tolerated by the gate; it is the **required** transition the gate
demands, and the engine correctly delivered it. Only the linked
deliberation `027-DL` was truly pre-archived pre-close, and it is the one
member here that correctly exercises the gate's optional
included-or-omitted tolerance (by being omitted, having no transition to
report). `returned_ids: []` confirms no unexpected substitution. No
discrepancy between the raw response and the required/allowed sets, no
condition, no follow-up required for this check.

All backlog reconciliation and closure-document commits were made on a
dedicated `post-merge/155-s-p015-cascade-close-archived-ids-postcondition`
branch created from `main`, never committed directly to `main`, per the
Post-Merge Branch Protocol.

**Process-deviation disclosure**: the Ship Step 5 Closure Tasks item 1
`pipeline-topology --phase lifecycle` re-check ("before closure/safe-close")
was inadvertently run *after*, not before, the `backlogit shipment ship`
cascade invocation above. Run post-hoc for the record, it correctly returns
`LIFECYCLE_NO_ACTIVE_SHIPMENT` (exit 1) because, by that point, `155-S` had
already reached `archived`/`shipped` -- an expected consequence of having
already closed, not a topology fault. The equivalent branch/worktree/
single-active-shipment invariants this checkpoint exists to re-verify were
already independently confirmed twice pre-merge (Step 4, both immediately
before build and immediately before PR creation) and once more immediately
before the merge itself (all three `PASS`, `active_shipment_ids: ["155-S"]`,
single worktree, correct branch); no branch or worktree change occurred
between the merge and the cascade invocation other than the intended
`main` -> `post-merge/155-s-...` switch, and the cascade's own outcome was
independently verified against live workspace state above with no
discrepancy. This ordering slip is recorded here transparently as a P-005
process-deviation note rather than omitted; it did not cause or mask any
actual topology violation.

### Unrelated pre-existing housekeeping carried forward

Two categories of pre-existing dirty working-tree state predated this
merge and were adjudicated per the operator's instruction to include only
legitimate, traceable state:

1. **023-DL archival (committed)**: a fully-implemented deliberation
   (verify-workspace template-variable derivation, stash `8FA8FC22`,
   shipped as feature `142-F` / shipment `150-S`, commit `927272da2c...`)
   had already been reconciled and archived by Stage on 2026-08-23, but the
   archival was never committed to git. Committed on this branch as a
   distinct housekeeping commit, unrelated to 155-S/147-F's own scope.
2. **`.mcp.json` and `.backlogit/runtime/` (left untouched, uncommitted)**:
   pre-existing local workspace state, explicitly documented in PR #407's
   own Local Review Readiness record as out of this shipment's scope
   (`.mcp.json`'s divergence drives one pre-existing, unrelated local test
   failure; `.backlogit/runtime/hooks/orchestrator.checkpoint.json` is a
   local ambient runtime sequence file with no repository history or
   references). Neither was discarded, overwritten, nor committed.

A line-ending-only, no-semantic-diff delta on `.backlogit/stash.jsonl`
(observed pre-merge) resolved itself once the working tree moved through
the post-merge branch's checkout/stash-pop sequence and required no action,
consistent with the PR's own session-housekeeping note that this same delta
was deliberately left uncommitted during the PR's own review cycles.

## Stash Disposition (P-021 C5)

Deferred scope expansion `5CFA8198` (the source of this shipment,
deliberated as `027-DL`) was archived via `backlogit stash archive
5CFA8198`, satisfying its own explicit archive condition recorded at
capture time -- "archive this entry once 155-S has shipped and the four
corrections are merged." Both conditions are now true: 155-S is `shipped`
(archived_status confirmed above) and PR #407 (containing all four
corrections: P-015 policy text, `shipment-reconcile` skill two-set gate,
regression tests, evidence-trail correction) is merged. Stash entry
`B57F9E24` remains active/external and untouched (unrelated scope); `84D8E6AB`
was already archived prior to this shipment (no action).

## Operational Closure

- **Invariants to preserve**: the two-set `allowed_ids`/`required_ids` gate
  in `templates/skills/shipment-reconcile/SKILL.md.tmpl` and the
  corresponding P-015 policy text in
  `templates/policies/workflow-policies.md.tmpl` must not regress back to a
  full-set-equality claim; `classify_shipment_close_path`'s full-depth
  descendant-coverage check (cycle 13 fix) must continue to walk the
  complete `parent_id` graph, not just direct children, before permitting a
  `CASCADE` close.
- **Pre-deploy audits**: not applicable -- no distribution/schema/CLI
  surface changed beyond the `autoharness` gates package's shipment-closure
  classifier (already covered by the runtime `cli` probe and the PR's own
  1880-test full suite run).
- **Deployment / rollout path**: merge-only; no separate deploy, canary, or
  phased-rollout step.
- **Risky action record**: not applicable -- no `ProposedAction` entries
  requiring approval, containment, or rollback beyond the standard
  operator-approved merge-commit-only merge (P-009) were taken. This
  closure's own cascade-close invocation was itself the first live exercise
  of the corrected two-set gate, and its outcome was independently verified
  against live workspace state (see Backlog Reconciliation above) rather
  than trusted on the raw response alone.
- **Post-deploy checks**: none beyond the runtime `cli` probe and the
  existing local full-suite evidence already recorded on the PR.
- **Healthy signals**: PR #407 merged with a verified 2-parent merge
  commit; P-018 `SATISFIED` at final HEAD; backlog cascade-close archived
  exactly the manifest's four tasks, the feature, and the shipment record
  (verified via live workspace state AND the raw `archived_ids` response,
  which now agree -- no discrepancy, unlike 154-S/146-F); repo
  merge-strategy settings confirmed merge-commit-only; source stash
  `5CFA8198` retired per its own recorded condition.
- **Failure signals to watch**: any future cascade-close invocation whose
  `archived_ids` response omits a required member (the shipment record or a
  qualifying feature member) should now correctly halt under the shipped
  `required_ids` gate; watch for a regression that silently reintroduces
  the withdrawn full-set-equality claim in either contract surface.
- **Monitoring plan**: none required beyond ordinary CI; the shipped
  contract tests (`tests/test_cascade_close_archived_ids_postcondition.py`)
  are the durable regression guard going forward.
- **Validation window**: immediate, at this post-merge closure (2026-08-24).
- **Rollback trigger**: not applicable in the conventional sense (no
  production runtime behavior changed beyond the shipment-closure
  classifier's fully-covered-root descendant check and the
  shipment-reconcile contract text); if the two-set gate is later found
  incorrect or overly permissive, correct it via a dedicated correction PR
  rather than reverting the merge.
- **Rollback procedure**: `git revert` the `155-S`/`147-F` feature merge
  commit (`a7aa820e3c...`) on `main` through a new reviewed PR, if ever
  needed.
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for
  merge approval and release follow-up routing.
- **Releasability evidence**: **READY**
  (`.autoharness/workspace-profile.yaml` `runtime_validation.releasability`:
  `required: false`, `status_when_satisfied: READY`, `required_evidence: []`
  -- no additional evidence beyond the runtime verification above is
  required for this workspace). Verified merge commit (two parents), green
  CI, P-018 `SATISFIED`, P-015 cascade-close fully verified against BOTH
  the raw engine response and live workspace state (no discrepancy), and
  P-020 compaction (see below) are all satisfied. No open conditions.
- **Follow-ups**: none outstanding for 155-S itself. External backlogit
  stash entry `B57F9E24` remains active and is unrelated to this
  shipment's scope -- it was neither touched nor implemented here.

## Compaction (P-020)

`compact-context --target all` performed manually
(`templates/skills/compact-context/SKILL.md.tmpl` -- not installed as a
resolved `.github/skills/` copy in this self-hosting repo). Candidate
selection is threshold-gated; the just-closed release unit's own fresh
session memory qualified under the completed-work rule: Ship's closure
session memory
(`docs/memory/2026-08-24-ship-155-s-147-f-shipped-closure.md`) was
consolidated into `docs/memory/compacted/2026-08-24-155s-147f-compacted.md`;
the verbose original was moved to `docs/archive/memory/`.
`compaction_status: done` above reflects this outcome.

### Note on self-referential closure fields

Consistent with the adopted convention (see
`docs/closure/153-S-145-F-post-merge-closure.md` and
`docs/closure/154-S-146-F-post-merge-closure.md`), `closure_merge_commit`
and `closure_reviewed_head` are left permanently `null` in this file. The
authoritative, always-current reviewed-HEAD record for the closure PR
itself lives in that PR's own body (`## Local Review Readiness` section),
which can be edited without shifting the branch HEAD. `closure_pr` is now
populated (`408`), reflecting this closure PR's actual number.

**Closure verdict: READY.** Runtime verification passed, P-015 cascade-close
is complete and fully verified with no discrepancy, source stash `5CFA8198`
is retired per its own recorded condition, and P-020 compaction is
complete. No residual risk or open follow-up is outstanding for this
shipment. No successor shipment was claimed in this invocation. This
closure PR requires a separate, explicit operator merge approval; it is
NOT authorized by the "PR 407: Merge approved" instruction, which was
scoped to PR #407 only.
