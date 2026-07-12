---
type: closure-memo
date: 2026-07-12
shipment: none (single chore)
chore: 001-C
stash: 3459B819
pr: 210
merge_commit: e1dda8f27d7afaec32d1b93e096dadde1087f749
mode: dark-factory (P-017)
tags: [agent-intercom, acp, prompts, cleanup, ping-loop]
---

# Ping-loop prompt removal — agent-intercom ACP consolidation (chore 001-C)

## What shipped

Fully removed the `ping-loop.prompt` artifact and all live references from the
`agent-intercom` capability pack. agent-intercom is consolidating strictly on
ACP mode; the MCP-mode sustained-heartbeat prompt is retired. Heartbeat
*behavior* is preserved via the intercom `ping`/heartbeat tool surface documented
in `agent-intercom.instructions.md` — only the standalone prompt artifact and its
wiring were removed.

PR #210 (feature/shipping) merged via merge commit `e1dda8f` (2 parents
`da44830` + `53682b2`, P-009 verified). Backlog archival and this closure memo
land in the separate closure PR #211.

## Changes

- Deleted `templates/prompts/ping-loop.prompt.md.tmpl`.
- `src/autoharness/verify_workspace.py`: removed ping-loop from
  `PROMPT_INSTALL_RULES` (it was the only `universal` prompt) and from the
  `copilot_remote_operator_guidance` check's `must_contain` (check relaxed).
- Removed ping-loop / heartbeat-prompt references from
  `templates/foundation/copilot-instructions.md.tmpl`,
  `.github/skills/install-harness/SKILL.md` (3 refs),
  `.github/agents/auto-mergeinstall.agent.md`,
  `.github/copilot-review-instructions.md`, `docs/getting-started.md`,
  and `docs/capability-packs.md` (overlay-target example + generic
  "Heartbeat or orchestration prompts" → "Orchestration prompts").
- Refreshed manifest checksums for the two manifest-tracked dogfood artifacts
  touched (`auto-mergeinstall.agent.md`, `install-harness/SKILL.md`), using the
  repo's LF-normalized sha256 convention.
- TDD regression tests: ping-loop absent from `PROMPT_INSTALL_RULES` and all
  live files; gap-aware `heartbeat[\w/ ]{0,40}prompts?` doc assertion; repointed
  uninstalled-prompt test to `feature-flow`.

## Adversarial review (dark-factory requirement)

- code-review + rubber-duck subagents ran on the staged diff before the PR.
- rubber-duck caught two by-description "heartbeat prompt" doc references that
  the name-only grep missed (fixed pre-PR).
- Copilot review: 3 rounds. Round 1 (2 threads) — valid: stale manifest
  checksums for the two touched artifacts (fixed). Round 2 (1 thread) — valid:
  `docs/capability-packs.md:73` "Heartbeat or orchestration prompts" still
  advertised the retired prompt AND the regression test's substring check missed
  the gap-separated phrasing (both fixed, test made regex/gap-aware). Round 3 —
  clean. P-018 gate SATISFIED.

## Gates

- Full suite: 510 passed, 138 subtests.
- Dogfood `verify_workspace(Path("."), Path("."))`: 0 blockers, 0 strict-schema
  blockers, 0 unresolved placeholders.
- §1.9 readiness: READY_WITH_FOLLOWUPS; Reviewed HEAD == headRefOid; CI 3/3 green.
- P-009 merge commit; P-016 single worktree (foreign CI-ruleset WIP parked in
  `git stash@{0}`, untouched).

## Residual-risk follow-ups (deferred — need separate work)

1. **Retired-artifact migration.** External workspaces that previously installed
   `ping-loop.prompt.md` and track it in their manifest will surface a
   `missing-template-source` blocker on verify against this autoharness version.
   No retired-artifact migration subsystem exists; building one is a separate
   feature. Dogfood is unaffected (ping-loop was never installed here).
2. **Full agent-intercom MCP→ACP transport consolidation.** The registry,
   workspace-discovery, and install-harness still declare agent-intercom MCP
   requirements/detection. This chore removed only the ping-loop prompt (stash
   3459B819); the broader transport consolidation is distinct, larger work.
3. **Pre-existing dogfood `copilot_remote_operator_guidance` = False.** The
   condensed dogfood `.github/copilot-instructions.md` uses pack-overlay blocks,
   not a "Remote Operator Integration" section. This PR only relaxes that check;
   not CI-gated.

## Backlog

- Chore `001-C` moved queued → active → done (archived).
- Stash `3459B819` archived (operator-confirmed direction).
- No shipment involved; single-chore lifecycle.
