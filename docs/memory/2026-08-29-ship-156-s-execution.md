# 2026-08-29 — Ship: 156-S End-to-End Execution (S0 — Policy Registry and Review-Persona Layer)

## Scope

First shipment in a bounded operator-authorized P-017 dark-factory sequence
(`156-S` then `157-S`; `157-S` explicitly out of scope for this turn). Full
Ship pipeline: startup/tool/checkpoint gates -> branch/claim with topology
gates -> sequential execution of 8 tasks (U1-U8) -> local adversarial review
-> PR creation/CI/Copilot review remediation -> merge-approval-pre-authorized
normal merge -> post-merge runtime verification, closure, and compaction.

## What happened

1. Claimed shipment `156-S` (feature `148-F`, 8 tasks) on branch
   `feat/156-s-s0-policy-registry-and-review-persona-layer-install-restore`.
   All pipeline-topology pre_claim/post_claim gates passed.
2. Executed all 8 tasks (148.001-T..148.008-T, U1-U8): policy registry
   resolution, `workflow-policies.md` install wiring, 13 review-persona
   template installs, manifest registration, and an end-to-end verification
   suite (21 tests). Survived a transient environment-wide PowerShell tool
   outage (self-resolved) and fixed a real `.gitattributes` `eol=lf` autocrlf
   defect discovered during verification.
3. **Misdiagnosed, then corrected, a real production regression** (D8-B
   pinned persona-checklist variables never bound by the general
   variable-derivation function). Full account in
   `docs/compound/2026-08-29-156-s-148-f-d8b-ratchet-misdiagnosis-and-copilot-catch.md`
   — flagged by Copilot's PR review, not caught by local review or the
   original test suite. This is the single most important finding from this
   session and is called out explicitly for operator visibility.
4. Local review (Constitution Reviewer + Python Reviewer personas): 1 direct
   fix (bare-assert / regex-parsing cleanups in the new U8 test file) plus 1
   genuine out-of-scope P-021 finding (pre-existing P-007 policy-prose
   approval-gate gap) captured as deferred entry `C0EA1175`.
5. Created PR #417. Copilot's automatic review (2 rounds, across 3 pushes)
   raised 8 total findings:
   - **4 direct in-scope fixes** (commit `3450837f`): the D8-B binding
     regression (#1), a `set()`-dedup test-logic gap in the U8 fenced-JSON
     exemption check that could miss a token leaking into prose (#3), and 2
     manifest `primitive` misclassifications (`workflow-policies.md` 5->8,
     13 persona entries 4->7) (#5, #6).
   - **3 out-of-scope P-021 deferred captures**, all pre-existing
     `.tmpl` content 156-S did not author (render-only D4/R4 discipline):
     constitution-reviewer principle-checklist gap (`701073F9`),
     security-reviewer purpose-based suppression rule (`BA035180`), and a
     dangling `python.instructions.md` cross-reference in
     `python-reviewer.agent.md` (`F0ADCC03`).
   - **1 in-scope process fix**: a stale PR readiness block (reviewed HEAD
     had not been updated after the fix commits) — corrected directly.
   All 6 review threads across both rounds replied-to (citing fix commits or
   deferred-entry IDs) and resolved via GraphQL. `autoharness gate
   copilot-review 417` returned `SATISFIED` at final HEAD `8b7dae51`.
6. All 4 required CI checks green; `mergeStateStatus: CLEAN`; repository
   `allow_merge_commit: true` / `allow_squash_merge: false` /
   `allow_rebase_merge: false` (P-009 structurally enforced). Runtime
   verification: `uv run autoharness --help` smoke probe passed (exit 0),
   satisfying the workspace's `runtime_validation.validation_expectations`
   (single required `cli` surface, `minimum_verdict: PASS`).
7. Merged PR #417 via `gh pr merge --merge` under `DARK_MODE_ACTIVE`'s
   `merge_approval_pre_authorized: true` (scope-matched to 156-S only, §1.9
   and P-018 both passing at the merged HEAD, no branch advance since the
   last gate pass). Merge commit `ec894bf3`, two parents (`5f35c34b` feature
   branch base advance, `8b7dae51` PR head) — verified merge-commit shape and
   `origin/main` ancestry.
8. **Post-merge closure**: the P-015 classifier
   (`classify_shipment_close_path`) confirmed 148-F is a verified
   fully-covered root (all 8 children present in the manifest, no
   descendants outside it), so the **cascade close path** was used instead
   of manual safe-close. `backlogit shipment ship 156-S --sha ec894bf3...`
   archived exactly the expected 11 artifacts (8 tasks + `148-F` + its
   linked deliberation `031-DL`, description-referenced, matched by
   `deliberationIDPattern` + `156-S` itself); `returned_ids: []`; two-set
   gate (`archived_ids` vs `allowed_ids`/`required_ids`) verified exactly
   matching; `parent_id: 148-F` preserved on all 8 archived tasks; shipment
   record shows `archived_status: shipped`. All closure work (this
   commit, compound learnings, this memory file) committed on
   `post-merge/148-f-s0-policy-registry-and-persona-layer-install-restore`,
   never on `main` directly.

## Operational observations (non-blocking)

- **`backlogit shipment ship` took ~11 minutes wall time** (vs. an expected
  few seconds for 9-11 metadata mutations), consuming continuously-growing
  CPU the whole time. Investigation found **8 orphaned `backlogit.exe mcp`
  background server processes** from prior sessions/incidents still running
  concurrently, almost certainly contending for the same lock/index files
  and causing retry/poll overhead. The command did complete correctly and
  all invariants verified clean, so this was **not** treated as a hang and
  was allowed to run to completion rather than interrupted mid-cascade
  (interrupting a partially-applied cascade mutation would have been far
  riskier than waiting). **Follow-up recommendation**: an operator should
  periodically audit and terminate stale `backlogit.exe mcp` processes
  outside of active agent sessions; no code or template change is implicated,
  so no P-021 capture was made for this — it is pure host-process hygiene.
- A same-named, same-task-description sibling background agent ("Ship
  156-S", owner not this session) was visible via `list_agents` earlier in
  this session, unreadable via `read_agent` ("No agent found"). Elapsed-time
  correlation and a fully clean git history (zero foreign commits/conflicts
  throughout this session) indicate this was a benign bookkeeping artifact
  of the same overarching session/context-compaction boundary, not a genuine
  concurrent P-001/P-016 conflict. No corrective action was taken or needed.

## Outcome

- Shipment `156-S`: **shipped and archived** (`archived_status: shipped`).
- Feature `148-F` and all 8 tasks: archived, `done`.
- 4 deferred P-021 stash entries created this session: `C0EA1175`,
  `701073F9`, `BA035180`, `F0ADCC03` — all out-of-scope pre-existing template
  content, all with source refs, all requiring Stage deliberation.
- PR #417 merged (`ec894bf3`), post-merge closure branch/commit prepared;
  closure PR to be opened next (per Post-Merge Branch Protocol) and requires
  its own local review + §1.9/P-018 gates + explicit operator approval before
  merge.
- `157-S` was not claimed, mutated, or implemented at any point in this
  session, per the operator's explicit scope boundary.

## Follow-ups

- Stage should triage all 4 new deferred stash entries (`C0EA1175`,
  `701073F9`, `BA035180`, `F0ADCC03`) in its next triage cycle.
- Consider a future task to generalize the D8-B pinned constants into
  `_language_defaults()`-derived values for non-Python primary languages
  (the RK-J residual that remains genuinely open and out of S0 scope).
- Consider periodic cleanup of orphaned `backlogit.exe mcp` processes as a
  standing operational hygiene item (not a code defect).
