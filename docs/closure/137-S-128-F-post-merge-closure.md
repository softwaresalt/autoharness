---
shipment: 137-S
feature: 128-F
tasks: [128.001-T, 128.002-T]
feature_pr: 354
closure_pr: 355
merge_commit: aa460ccefc65dab03d03b6b745b60f30c50b5344
merged_at: "2026-08-17T21:53:20Z"
reviewed_head: b145578ca074a8bdb8129af963b7dda85071c4a2
closure_status: READY
compaction_status: degraded
feature_terminal_status: done
---

# 137-S / 128-F Post-Merge Closure — Spike Skill Template Docline Frontmatter Conformance

Shipment `137-S` implemented feature `128-F`: corrected the Phase 5
findings-artifact YAML example in `templates/skills/spike/SKILL.md.tmpl` to
nest spike-specific fields (`type`, `date`, `time_box`, `conclusion`,
`confidence`, `linked_parent_work_item`, `promoted_to`, `tags`) under a
`docline` mapping while keeping docline-required fields (`title`, `source`,
`doc_type: decision`, `description`) top-level (`128.001-T`); re-pointed
Step 4.2's promotion instructions to `docline.promoted_to` /
`docline.plan_artifact` accordingly; and added a new test module,
`tests/test_spike_template_docline_frontmatter.py`, proving both the
structural shape and (when `backlogit` is on PATH) real-linter acceptance
evidence (`128.002-T`).

`128-F` is a root feature (no `parent_id`) with exactly 2 children
(`128.001-T`, `128.002-T`), both of which are this shipment's manifest.

## Merge Confirmation

- PR **#354** ("fix(templates): spike skill template docline frontmatter
  conformance (128-F)") merged to `main` at `2026-08-17T21:53:20Z` with
  merge commit `aa460ccefc65dab03d03b6b745b60f30c50b5344`, verified an
  ancestor of `origin/main` via `git merge-base --is-ancestor` (exit 0).
  Merge commit confirmed to have exactly 2 parents
  (`0ec98ce4` = prior `main` tip, `b145578c` = feature branch HEAD).
- Repo merge-strategy settings (P-009), re-verified this session:
  `mergeCommitAllowed: true`, `squashMergeAllowed: false`,
  `rebaseMergeAllowed: false` — only "Create a merge commit" is possible.
  `gh pr merge 354 --merge` used; no `--admin`.

## PR Lifecycle Notes

- **Branch-rename mishap**: an earlier attempt to fix a `pipeline-topology`
  `BRANCH_MISMATCH` finding by renaming the open PR #353's branch
  server-side unexpectedly auto-closed #353 instead of retargeting it. PR
  #354 was opened from the renamed branch as recovery; #353 was annotated
  with a comment linking to #354. See
  `docs/compound/2026-08-17-branch-rename-after-pr-open-auto-closes-pr.md`.
- **Copilot review round 1** (HEAD `99a1408d`): 1 actionable P1 finding —
  `BacklogitLintAcceptanceTests` silently skip in CI (no `backlogit` binary
  there), leaving the PR's core external-contract claim CI-unverified.
  Remediated in `b145578c` by adding a pinned, SHA256-checksum-verified
  `backlogit v1.9.0` binary install step to `.github/workflows/ci.yml`'s
  `test` job. Replied to the comment (referencing the fixing commit) and
  resolved the thread via GraphQL `resolveReviewThread`. See
  `docs/compound/2026-08-17-ci-skip-coverage-gap-prefer-pinned-binary-over-reimplementation.md`.
- **Copilot review round 2** (HEAD `b145578c`, explicitly re-requested via
  `requested_reviewers` with login `Copilot`): reviewed 11/11 changed files,
  generated no new comments. 0 unresolved threads.
- `autoharness gate copilot-review 354 --enforcement auto` → `SATISFIED`
  (0 unresolved Copilot threads, review complete for final HEAD).
- P-014 §1.9 readiness: Local Review Readiness block in the PR body updated
  to the final HEAD (`b145578c`) with full CI + local build evidence before
  merge. `mergeStateStatus: CLEAN` at merge time.
- Operator pre-authorization ("previously granted permission to open PRs
  and approve normal merges for this scoped pipeline... treat that as the
  P-014 approval signal for the 137-S PR only after all readiness gates
  pass") was treated as satisfying the operator-approval gate only after
  CI, §1.9 readiness, and the P-018 Copilot-review gate all independently
  passed at the final HEAD — never before.

## Backlog State Inspection (this closure session)

- Classifier run (`classify_shipment_close_path`, reused directly from
  `src/autoharness/gates/shipment_closure.py` in this self-hosting repo)
  against manifest `[128-F, 128.001-T, 128.002-T]`: verdict `CASCADE` —
  `128-F` is a verified fully-covered root (both children are manifest
  members, both terminal, `128-F` itself has no `parent_id`).
- Pre-close `parent_id` snapshot taken before the cascade call:
  `128.001-T.parent_id = 128-F`, `128.002-T.parent_id = 128-F`.
- Ran `backlogit shipment ship 137-S --sha aa460cce... --message ... --author ...`
  per the P-015 verified fully-covered-root exception (cascade path used
  in place of safe-close steps 1–10).
- Verified per the Cascade Close Sub-Procedure:
  - `returned_ids: []` (no classifier/engine mismatch).
  - `archived_ids: [128.001-T, 128.002-T, 128-F, 137-S]` — exactly the
    manifest task items, the one qualifying feature, and the shipment
    record; nothing extra.
  - `parent_id` on both tasks re-read post-cascade and confirmed unchanged
    (`128-F`) against the pre-close snapshot.
  - Shipment record: `archived_status: shipped`. Feature/tasks:
    `archived_status: done`.
- Gate decision: **CLOSED**.

## Local Review

Adversarial local review of the closure delta (backlog cascade-close state
+ this closure's own new docs) performed this session, multi-persona
(correctness/provenance, role-boundary, security/secrets):

- **P0/P1**: none found.
- **P2/P3**: none raised requiring separate follow-up.
- No secrets, credentials, or raw operator content present in any new file
  in this closure delta.

## Validator Evidence

This closure changes only `.backlogit/*` backlog-state files and `docs/*`
(closure artifact, 3 compound-learning documents, session memory) — no
source code, schema, or template changed by the closure itself (those
changes shipped in PR #354). Full local build/test suite is **not
applicable** to this closure delta; recorded per the docs/backlog-only
exemption. A CLI smoke check was still run for baseline confidence:

| Area | Verdict | Evidence |
|---|---|---|
| CLI smoke test | PASS | `.venv\Scripts\autoharness.exe --help` — exit 0 (`uv run` unavailable in this environment: no PyPI network access) |
| Cascade close invariant (manual, see above) | PASS | `returned_ids` empty, `archived_ids` exact match, `parent_id` preserved on both tasks |
| Full local build/test suite | N/A | Docs/backlog-only closure delta; no source changed by the closure itself |

## Runtime Verification

No runtime surface is touched by this closure delta (backlog-state files
and documentation only). Per `.autoharness/workspace-profile.yaml`
`runtime_validation.validator_manifest`, the only declared surface is `cli`;
the CLI smoke check above satisfies that surface's probe. The feature PR
(#354) itself touched CI workflow (`.github/workflows/ci.yml`) and a
template file, both already validated by CI's own green run at the merged
HEAD (see PR Lifecycle Notes above) — no additional runtime surface beyond
`cli` is introduced.

## Invariants Preserved

- No commit in this closure targets `main` directly; all closure commits
  land on `post-merge/spike-skill-template-docline-frontmatter-conformance`.
- No protected-set violation: this shipment's manifest fully covered its
  root feature, so the cascade path (not safe-close's protected-set logic)
  applied; the Cascade Close Sub-Procedure's own equivalent verification
  (parent_id preservation, exact `archived_ids` match) passed.

## Pre-Deploy Audits and Deployment Path

Docs/backlog-only closure delta; released by merge-only deployment to
`main`. No runtime service, background job, deployment surface, or public
API is introduced or altered by the closure itself. No pre-deploy audit
beyond the CLI smoke check above is applicable.

## Monitoring and Healthy Signals

No dedicated monitoring is required for a backlog-cascade-closure +
documentation closure. Healthy state is `137-S` showing
`archived_status: shipped` with `128-F`/`128.001-T`/`128.002-T` all
`archived_status: done` under `.backlogit/archive/` and no residual
`queue/128*` or `queue/137-S.md` entries.

## Failure Signals and Rollback

Rollback for this closure is a plain revert of the closure merge commit
(additive backlog-state + docs only, no destructive migration). Rollback
for the feature itself (PR #354) would be a revert of merge commit
`aa460cce`, which would restore the pre-fix (non-docline-conformant)
spike-template frontmatter and CI workflow — not expected to be needed, but
noted for completeness.

## Releasability Evidence

`closure_status: READY`. Merge, review (PR #354's two Copilot review
rounds plus this session's own closure-delta review), the P-018
Copilot-review gate, and the cascade-close invariant evidence are all
complete. No runtime surface beyond the already-validated `cli` surface is
introduced or altered. No P0/P1/P2/P3 follow-ups are outstanding.

## P-020 Compaction

`compaction_status: degraded`. The mandatory `compact-context` invocation
was attempted at post-merge closure; no installed/executable runtime skill
exists in this environment for it — only the repository's own authored
template at `templates/skills/compact-context/SKILL.md.tmpl` (this
self-hosting repo does not resolve `.github/skills/compact-context/SKILL.md`),
consistent with the `130-S`/`121-F`, `134-S`/`125-F`, `135-S`/`126-F`, and
`136-S`/`127-F` closure precedents. This session's own manual consolidation
— three compound-learning documents and one session-memory document, all
written during this same closure — constitutes the bounded, cheap Tier-1
consolidation of this shipment's fresh memory that a working
`compact-context` tool would otherwise perform. Recorded as
attempted-and-degraded, non-blocking, per P-020.

## Backlog Archival

- Feature `128-F` and its 2 tasks (`128.001-T`, `128.002-T`) archived this
  session via the cascade close path, each `archived_status: done`.
- Shipment `137-S` archived this session via the same cascade call,
  `archived_status: shipped`.

## Follow-Ups

None outstanding. All Copilot review findings were resolved (fixed or
disposed with a substantive reply + thread resolution) before merge; no
P2/P3 residual risk was deferred.
