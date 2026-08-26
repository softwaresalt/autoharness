---
title: "Copilot-Review Merge Gate — decided plan"
doc_type: decided-plan
status: reviewed
created: 2026-07-09
tasks: ["T1", "T2", "T3", "T4", "T5", "T6"]
supersedes:
  - docs/archive/plans/2026-07-09-copilot-review-merge-gate-plan.md
---

# Decided Plan: Copilot-Review Merge Gate

**Outcome:** Reviewed, not shipped. The source plan records an approved, hardened implementation for policy `P-018`: when Copilot review is enabled for a pull request, merge — including `--admin` — must block until Copilot has reviewed the current `headRefOid` and every Copilot-authored review thread is resolved. The plan spans CLI, instruction, agent, policy, schema, and documentation surfaces.

## Decisions

1. Add a deterministic `autoharness gate copilot-review <pr>` command that classifies PR state into explicit pass/block verdicts and fails closed whenever completion or thread resolution cannot be proven.
2. Treat stale-head reviews as insufficient: if Copilot reviewed an older HEAD, the gate must re-arm and wait for review on the current `headRefOid`.
3. Support `auto`, `required`, and `disabled` enforcement modes so repositories can distinguish between no-engagement PASS, required engagement BLOCK, and opt-out behavior.
4. Wire the gate into GitHub PR automation guidance and Ship's pre-merge state machine so a `COPILOT_REVIEW_BLOCK` can never be bypassed by `--admin`.
5. Codify the behavior as workflow policy `P-018`, with a bounded timeout path that still blocks by default and only yields under an audited `--force` override.

## Implementation (6 tasks)

- **T1** — add the deterministic gate module, CLI subcommand, GitHub GraphQL query path, and tests.
- **T2** — update the GitHub PR automation instruction template and installed mirror.
- **T3** — update the Ship template and installed mirror so the gate runs before any merge attempt.
- **T4** — add `P-018` to the workflow-policies template.
- **T5** — add the `copilot_review.enforcement` config/schema surface.
- **T6** — document the gate, verdicts, enforcement modes, and timeout/force behavior.

`T1` is foundational; `T2`, `T5`, and `T6` depend on it; `T3` depends on `T1` and `T2`; `T4` is policy work that can land independently.

## Key constraints preserved

- Enabled-but-incomplete or unverifiable Copilot review is always a BLOCK.
- GitHub queries must use an argv-array `gh api graphql` invocation with `shell=False`; the injection negative test is acceptance-blocking.
- Copilot review detection uses the GraphQL login form `copilot-pull-request-reviewer` and GraphQL thread node IDs so REST/GraphQL identity drift does not break the gate.
- Template behavior changes land with their installed mirrors to preserve dogfood parity.
- `REVIEW_TIMEOUT` is a distinct blocking outcome; only an audited `--force` record under `.autoharness/gates/` may override it.

## Rejected alternatives

- **Leave Copilot review advisory once engaged** — rejected; engagement turns review completion and Copilot-thread resolution into a deterministic merge gate.
- **Allow `--admin` to bypass the Copilot-review block** — rejected explicitly by the design.
- **Wait forever for Copilot review** — rejected; timeout is bounded, logged, and still fail-closed.
- **Build the GitHub command through shell interpolation** — rejected because injection resistance is an acceptance requirement.
- **Treat no Copilot engagement as a block in `auto` mode** — rejected because it would wedge PRs where Copilot never entered the review flow.

## Plan-hardening refinements folded in

- Fail-open regression risk became an explicit acceptance condition: no enabled-but-unproven path may return success.
- Wedge risk is handled by `auto` mode's not-applicable PASS and a bounded `--max-wait` path.
- Command-injection defense is reinforced by an acceptance-blocking negative test.
- Bot-login and ID-type drift are handled through a central login constant and GraphQL thread IDs.
- Admin-bypass and timeout cases are elevated into explicit blocking states instead of implicit fallthrough.