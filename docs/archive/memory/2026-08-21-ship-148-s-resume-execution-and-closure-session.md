---
title: "Ship 148-S resume, execution, and closure session (docs/compound docline conformance)"
date: 2026-08-21
agent: ship
route: "claude-sonnet-5 / anthropic / high"
shipment: 148-S
feature: 140-F
tasks:
  - 140.001-T
  - 140.002-T
pr: 387
merge_commit: 291dafd8cd5c1ff937c6499476161ae450fb2f0a
---

# Ship 148-S: Resume, Execution, and Closure Session

## Why this session started as a resume

A prior synchronous `_Ship` invocation for shipment 148-S was interrupted at
the tool transport after substantial work: both tasks 140.001-T and
140.002-T were already committed (`19890739`, `4fff68a2`) on branch
`feat/148-s-docs-compound-docline-conformance-backfill-source-doc-type-and-align-the-authoring-contract`,
but no checkpoint had survived, no PR existed, and a pending official
backlogit archival move for 140.002-T (`.backlogit/queue/140.002-T.md` ->
`.backlogit/archive/140.002-T.md`) remained uncommitted. The operator
explicitly directed diagnosis-and-continue, with two `.mcp.json`-removal
stashes preserved and untouched throughout (Orchestrator restores the
newest after the full shipment sequence).

## Session sequence

1. **Diagnosis**: confirmed branch/HEAD/shipment/feature/task state matched
   the operator's exact cursor. Enumerated ALL backlogit checkpoints
   (zero-candidate normal startup -- no active `ship`-owned checkpoint
   existed, no quarantine anomalies) before proceeding. Created a fresh
   active Ship checkpoint capturing the resume cursor immediately, per the
   operator's explicit resilience directive.
2. **Committed the pending archival**: staged and committed the
   queue->archive move for 140.002-T plus the new checkpoint, with proper
   trailers.
3. **Validation**: ran the two targeted test modules (15/15 passed), the
   full canonical test suite (`uv run python -m pytest tests/ -q`: 1692
   passed, 20 skipped, 5 failed -- the 5 failures exactly matched the known
   pre-existing `E8158860` test-isolation defect, confirmed not a
   regression), `backlogit docs lint --path docs/compound` (0 violations),
   and the `docs migrate --dry-run` re-run (`body_bytes_changed: false` for
   all 73 files).
4. **Local review**: delegated to the `code-review` custom agent
   (report-only mode) against the full branch diff. Verdict:
   `READY_WITH_FOLLOWUPS` with one P2 finding (a pre-existing file's
   `source:` value carries shipment/PR provenance text rather than a
   self-referential path -- correctly left untouched by 140.001-T's AC3
   verbatim-preservation rule). Captured as P-021 C2 deferred scope
   expansion stash entry `FAE1E7B7` after a full duplicate scan (active +
   archived stash) found no reusable entry -- threadless capture path (no
   PR/thread existed yet).
5. **PR lifecycle**: pushed the branch, created PR #387 with the required
   `## Local Review Readiness` block, requested Copilot review via the
   REST `requested_reviewers` endpoint (no MCP tool or configured CLI
   wrapper was available in this session's toolset, so this was a direct,
   one-off API call rather than the documented `gh pr edit --add-reviewer`
   anti-pattern or a configured wrapper).
6. **Copilot review cycle 1** (5 threads on HEAD `41ba96df`): classified
   every finding against P-021 C1 before fixing. Four passed C1 (same
   contract surface -- the task's own newly-authored test files and
   checkpoint) and were fixed directly: a YAML-semantic emptiness check
   replacing raw regex, a recursive corpus scan, a genuinely non-vacuous
   new-template-variable check (the naive "exclude the whole example"
   fix Copilot suggested would have falsely flagged ~16 legitimately
   example-only placeholders -- had to derive the correct fix by diffing
   against the template's pre-140.002-T git history instead), and a
   checkpoint schema correction (`resume_hint` belongs at the TOP LEVEL,
   not nested under `context` -- confirmed against
   `.github/instructions/backlogit.instructions.md`'s Checkpoint Payload
   Contract). The fifth finding was a PR-description accuracy issue (my
   own earlier draft claimed `backlogit docs migrate --apply` was used,
   contradicting 140.001-T's own execution record, which documented an
   additive-only manual equivalent after `--apply` was found to corrupt
   pre-existing frontmatter) -- corrected in the PR description, not code.
7. **Copilot review cycle 2** (2 threads on HEAD `598c7303`): the refreshed
   checkpoint from cycle 1 was itself flagged as still `active` pre-merge.
   Declined the literal "resolve before merge" ask -- the operator's
   explicit resumption directive required the checkpoint to stay active
   until the full merge+closure sequence completed, and resolving it
   prematurely would have removed the crash-recoverability safety net
   this whole session existed to establish. Addressed the underlying
   staleness concern instead (refreshed content, explicit note that it
   must be resolved as the final closure step). A follow-on finding (the
   refreshed checkpoint's resume_hint cited a stale intermediate HEAD) was
   fixed by editing the PR description only (`gh pr edit`, no new commit),
   which avoided re-arming another Copilot review round.
8. **Merge**: `autoharness gate copilot-review` returned `SATISFIED`;
   P-014 §1.9 gate passed at HEAD `598c7303`; repo merge-strategy settings
   confirmed merge-commit-only; last-mile headRefOid + P-018 re-check
   confirmed no drift; merged with `gh pr merge --merge`. Verified 2-parent
   merge commit and `git merge-base --is-ancestor` against `origin/main`.
9. **Post-merge closure**: created `post-merge/148-s-docs-compound-docline-conformance`
   from `main`. Ran the P-015 classifier
   (`classify_shipment_close_path`), which correctly returned `CASCADE`
   (140-F is a verified fully-covered root). Invoked
   `backlogit shipment ship 148-S --sha 291dafd8...`. The cascade swept in
   an out-of-manifest deliberation (`025-DL`, linked to `140-F` only via a
   plain `references` list entry) -- the exact known engine-behavior
   surprise already documented in
   `docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`
   (first observed on 143-S/134-F/019-DL). Applied the identical
   documented remediation: reverted only `025-DL`, independently
   re-verified every other post-condition (`returned_ids: []`, exact
   `archived_ids` match after excluding `025-DL`, `parent_id` preservation,
   shipment `archived_status: shipped`), and recorded this second
   occurrence as a new disposition section on the existing compound
   learning doc.

## Hard-won lessons (compound-worthy, captured separately)

* A "no new variable" structural test that computes its "pre-existing"
  baseline from text that trivially includes the example being checked is
  vacuous by construction -- the fix must scope "pre-existing" to what
  existed **before this diff**, not to "everything outside a naive text
  exclusion", because the latter can accidentally flag every intentionally
  example-scoped placeholder as new.
* The Checkpoint Payload Contract's `resume_hint` is a top-level field,
  not a `context` sub-field -- an easy mistake when reflexively nesting
  all state under `context` for a payload that also happens to need a
  human-readable resume note.
* Editing a PR description via `gh pr edit` does not advance git HEAD and
  therefore does not re-arm a Copilot review cycle -- this is the correct
  tool for correcting PR-body accuracy findings (documentation-only
  findings) without extending the review-fix cycle count.
* The out-of-manifest linked-deliberation cascade surprise is not a
  one-off: it recurred with a different feature/deliberation pair and a
  different reference mechanism (plain `references` list vs
  `custom_fields.source_deliberation_id`), reinforcing that the
  Stage-owned follow-up should target the engine's reference-link-walking
  behavior generally, not one specific field name.

## Deferred / follow-up

* P-021 stash entry `FAE1E7B7` (source-value semantic mismatch, one file) --
  Stage deliberation required.
* Existing P-021 stash entry `E8158860` (full-suite test-isolation
  pollution) -- unaffected, tracked separately.
* Cascade close out-of-manifest reference-link sweep -- Stage-owned
  template/classifier hardening follow-up remains open (recorded in the
  compound learning doc's recurrence section).

## Session state at close

Shipment 148-S archived (`archived_status: shipped`). Feature 140-F
archived. Both tasks archived with preserved `parent_id`. No successor
shipment (149-S) claimed. Two `.mcp.json` stashes left untouched for
Orchestrator restoration. Post-merge closure branch/PR still in progress
at the time this memory file was written (see
`docs/closure/148-S-140-F-post-merge-closure.md` for the authoritative
structured closure record, finalized once compact-context completes).
