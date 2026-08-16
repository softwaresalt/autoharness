# Ship Session Memory — 2026-08-16 — PR #349 -> PR #348 Completion

## Context

Continuation session picking up a prior Ship session that could not receive
follow-up messages. Operator authorized: (1) merge PR #349 once gates pass,
(2) exactly one additional bounded review-fix cycle for PR #348's then-open
Copilot finding, (3) merge PR #348 once all gates pass. A second operator
message then authorized one *final* bounded cycle specifically for a new
Copilot finding at `templates/instructions/escalation-protocol.instructions.md.tmpl:150`
(missing `resolved_escalation_route`-style contract field), with explicit
scope bounding for any further genuinely-new finding: "apply only a
mechanical/directly-consequential correction in the same contract surface;
otherwise halt only for a non-overridable P0/P1 or external outage."

## What happened, in order

1. Re-verified PR #349 readiness (P-018 SATISFIED, CI green, CLEAN,
   merge-commit-only settings) and merged with `gh pr merge 349 --merge` ->
   `61ad9d53...` (two parents confirmed). Confirmed 136-S closure durable on
   `main`. Synced backlog index.
2. Switched to PR #348's branch, confirmed no parallel worktree existed,
   confirmed topology gate passed post-136-S-closure.
3. Investigated the authorized cycle-6 finding: the Escalation-Payload
   Contract table in `escalation-protocol.instructions.md(.tmpl)` had no
   route/model field, even though the Terminal Engram Handoff section said
   the agent "records the route in the payload." Decided on
   `resolved_escalation_route` as the field name (the
   `(model_family, model_provider, reasoning_effort)` tuple actually resolved
   for the handoff, present only when not `ESCALATION_DEGRADED`) — chosen to
   match existing repo terminology (`ESCALATION_FAMILY`/`PROVIDER`/
   `REASONING_EFFORT`, `resumption_checkpoint_ref` naming style).
4. **Red-first discipline**: added a focused contract test
   (`test_escalation_payload_contract_defines_resolved_route_field`) to
   `tests/test_circuit_breaker_policy_contract.py` before making any
   production edits. Confirmed it failed for the right reason first
   (assertion literal mismatch caught a line-wrap bug in the test itself,
   fixed by using the file's existing `_normalize()` whitespace-collapsing
   helper instead of literal substring matching against wrapped Markdown).
5. Edited the authoritative template + its dogfood counterpart
   (`escalation-protocol.instructions.md(.tmpl)`), and mirrored the same
   field-name reference into `_ship.agent.md.tmpl`/`_stage.agent.md.tmpl`
   item 4 ("Hand off and halt") plus their dogfood counterparts
   (`.github/agents/_ship.agent.md`, `_stage.agent.md`).
6. Refreshed manifest checksums for all three touched dogfood files in
   `.autoharness/harness-manifest.yaml`, computed via `Get-FileHash` on the
   raw working-tree file (confirmed byte-identical to the LF-normalized
   staged git blob via `git cat-file -p :<path>` piped to a temp file and
   re-hashed) — this matched the pre-existing test-asserted expected digests
   exactly (`test_crash_resumption_protocol.py`,
   `test_telemetry_ship_lifecycle.py`).
7. Full suite: 1500 passed / 0 failed. Committed as `5250dbe5`. Pushed (no
   force). Replied to the Copilot comment with the fixing commit, resolved
   the thread via GraphQL.
8. Refreshed the PR body's Local Review Readiness block for the new HEAD.
9. Waited for Copilot to re-review the new HEAD (~4 min observed). It
   surfaced 3 new threads, all in `verify_workspace.py`'s stale-retry
   checker: (a) a genuinely new "run ... again" object-separated-form gap,
   (b) a genuinely new "separate `**Escalation**` paragraph not scanned"
   coverage gap, (c) a **direct mechanical consequence** of step 5-6's own
   change — the shared-instruction verifier did not require the new
   `resolved_escalation_route` field.
10. **Scope-boundary judgment call**: fixed only (c) — added the token
    requirement, a red/green regression test (explicitly confirmed RED via
    `git stash` on the production file, then GREEN after restoring), full
    suite 1501/0 failed, committed `53e3cdcd`, pushed, replied, resolved.
    Findings (a) and (b) were judged out of the operator's "same contract
    surface" scope (they are stale-retry-matcher robustness gaps, not
    contract-field gaps) — replied to each with an explicit scope-boundary
    rationale and resolved the threads as disclosed-not-fixed residual risk,
    rather than silently ignoring them or leaving them unresolved (which
    would have blocked the P-018 gate).
11. Copilot's review of `53e3cdcd` surfaced one further new thread in
    `templates/policies/workflow-policies.md.tmpl` about whether
    `strict_safety`'s Tier 2->Tier 3 confirmation requirement should
    interact with the P-013.6 handoff — judged a substantive design
    question, not mechanical, and disclosed the same way.
12. Re-ran P-018: `SATISFIED`, all 12 threads resolved. Confirmed CI green,
    `mergeStateStatus: CLEAN`, merge-commit-only repo settings. Merged with
    `gh pr merge 348 --merge` -> `685fc255...` (two parents confirmed,
    ancestor-of-`origin/main` confirmed).
13. Post-merge: checked out and pulled `main` (confirmed the fix content is
    durable), created `post-merge/348-circuit-breaker-diagnostic-escalation-policy`
    from `main` for closure artifacts (no shipment authority exists for this
    PR, so no backlog archival step applies), wrote this memory doc, the
    closure doc, and a compound-learning entry, then recorded P-020 as
    `degraded` (compact-context skill not installed in this self-hosting
    repo's own `.github/skills/`, consistent with established precedent).

## Key decisions and why

- **Rebase-vs-merge audit**: an earlier report imprecisely said "rebased" for
  a `git merge origin/main` step. Verified via `git log --pretty=%P` that
  both branch-update commits are genuine two-parent merges. Corrected the
  language in this closure's artifacts; no rebase or force-push occurred at
  any point in this PR's history.
- **In-scope vs. out-of-scope findings**: the operator's directive drew a
  precise line — "same contract surface" — and the actual test was applied
  literally: does the new Copilot finding concern the
  `resolved_escalation_route` field/contract itself (in scope) or a
  different aspect of the same file/PR (out of scope)? This produced a
  defensible, auditable distinction rather than an unbounded "looks related
  enough" judgment.
- **Resolving disclosed-not-fixed threads rather than leaving them open**:
  P-018 requires zero *unresolved* Copilot threads at merge, not zero
  *unaddressed-by-code-change* threads. Resolving a thread via a substantive,
  honest disclosure reply (explaining why no fix was made and citing the
  scope boundary) is the correct mechanism for closing out-of-scope P2/P3
  findings without either fabricating unauthorized scope expansion or
  perpetually blocking merge on advisory-level suggestions — consistent with
  the Review Gate step's "Accept P2/P3 as follow-up backlog items" pattern,
  adapted here (no backlog authority exists for this PR) to a PR-body/
  closure-doc disclosure instead.
