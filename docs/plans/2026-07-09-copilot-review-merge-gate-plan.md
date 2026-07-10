---
title: "Copilot-Review Merge Gate — Implementation Plan"
description: "Impl-plan, hardening, and review verdict for stash 0B278CEE: a deterministic fail-closed pre-merge gate enforcing Copilot-review completion and iterative bot-thread resolution, non-bypassable by --admin."
doc_type: plan
source: docs/plans/2026-07-09-copilot-review-merge-gate-plan.md
source_stash_ids:
  - "0B278CEE"
decision: docs/decisions/2026-07-09-copilot-review-merge-gate-deliberation.md
requires_plan_hardening: "yes"
plan_review_verdict: "approved"
tags:
  - "copilot-review"
  - "merge-gate"
  - "deterministic-gate"
  - "P-018"
---

# Copilot-Review Merge Gate — Implementation Plan

Decision of record:
`docs/decisions/2026-07-09-copilot-review-merge-gate-deliberation.md`
(B + C + A-wiring: deterministic gate + P-018 policy + instruction/agent wiring).

## Objective

When Copilot review is enabled for a PR, deterministically block merge (including
`--admin`) until (1) Copilot has completed a review for the current `headRefOid`
and (2) all Copilot-authored review threads are resolved — iterating across
multiple rounds — with a bounded, logged, fail-safe timeout escape.

## Work Breakdown (width-isolated, ≤2h each)

### T1 — Deterministic gate module + CLI subcommand + tests (CLI/gate code)
* New `src/autoharness/gates/copilot_review.py`:
  * Pure classification core over an injected GitHub query result → verdict enum
    (`SATISFIED`, `NOT_APPLICABLE`, `WAITING_FOR_REVIEW`, `UNRESOLVED_THREADS`,
    `REVIEW_TIMEOUT`, `DETECTION_AMBIGUOUS`, `VERIFY_FAILED`).
  * Default GitHub query via `gh api graphql` as an **argv array**, `shell=False`,
    bounded `_COMMAND_TIMEOUT_SECONDS` (mirror sizing.py); injectable `run_fn` for
    tests.
  * Reads: `headRefOid`, `reviewRequests` (Copilot requested?), `reviews`
    (Copilot review + `commit.oid`), `reviewThreads { id isResolved
    comments(first:1){ nodes{ author{ login } } } }`.
  * Copilot login match: `copilot-pull-request-reviewer` (GraphQL, no `[bot]`).
  * `enforcement` mode input: `auto` | `required` | `disabled`.
  * Fail-closed on enabled-but-incomplete/unverifiable; PASS on not-applicable.
* `autoharness gate copilot-review <pr>` in `cli.py`:
  `--repo owner/name`, `--enforcement`, `--max-wait`, `--json`, `--force`
  (audited), `--workspace`. Exit 0 = PASS/not-applicable; non-zero = BLOCK.
  `--force` writes an audit record under gitignored `.autoharness/gates/`.
* `tests/test_gates_copilot_review.py` (+ CLI test): each verdict branch,
  multi-round re-arming (review for stale HEAD ⇒ WAITING), unresolved-thread
  detection, timeout ⇒ BLOCK, `required` forcing before request, and an
  **argv-injection negative test** (acceptance-blocking).
* **Depends on**: none (foundation).

### T2 — github-pr-automation instruction: template + installed mirror (instruction)
* Edit `templates/instructions/github-pr-automation.instructions.md.tmpl` AND
  mirror `.github/instructions/github-pr-automation.instructions.md`:
  * §1.1 — when Copilot review is **enabled**, shadow review is a conditional
    **hard gate**, not advisory.
  * §1.8 — cycle limits still bound iterations, but when enabled, exhausting them
    with unresolved bot threads is a **BLOCK**, not "accept as follow-up."
  * §1.9 — new gate check invoking `autoharness gate copilot-review` and a new
    terminal state (`Copilot review incomplete/unresolved ⇒ Halt`), plus the
    bounded-timeout `REVIEW_TIMEOUT` fail-safe.
* Dogfood-parity pair (template + mirror in this one task).
* **Depends on**: T1 (references the CLI command).

### T3 — .ship agent: template + installed mirror (agent)
* Edit `templates/agents/.ship.agent.md.tmpl` AND mirror
  `.github/agents/.ship.agent.md`:
  * Step 4: run `autoharness gate copilot-review` as a mandatory pre-merge gate
    before any `gh pr merge` (BLOCK ⇒ halt), including `--admin`.
  * Dark-mode merge/admin fallback state machine: add a
    `COPILOT_REVIEW_BLOCK` classification that admin fallback may **never** bypass.
* Dogfood-parity pair (template + mirror in this one task).
* **Depends on**: T1 (gate exists), T2 (references §1.9 wording).

### T4 — P-018 policy in workflow-policies template (policy)
* Add `## P-018: Copilot Review Completion & Thread Resolution Merge Gate` to
  `templates/policies/workflow-policies.md.tmpl` after P-017, with Field table,
  Statement (admin non-bypass, multi-round, fail-closed, bounded-timeout escape),
  Precondition, Postcondition, Relationship to P-014/P-017, Violation Action; add
  the amendment-log row (`1.13.0 … Added P-018`).
* **No installed mirror** — policy touches only the template.
* **Depends on**: none (independent).

### T5 — Config/schema surface: `copilot_review.enforcement` toggle (schema)
* Add `copilot_review.enforcement` (`auto` | `required` | `disabled`, default
  `auto`) to the workspace-profile schema and any registry/config the gate reads;
  update the variable/field documentation.
* **Depends on**: T1 (config contract shaped by the gate).

### T6 — Docs (docs)
* Operator-facing doc describing the gate, its verdicts, the enforcement modes,
  the timeout/force audit behavior, and P-018.
* **Depends on**: T1, T2, T4 (documents the assembled behavior).

## Dependency Graph

```text
T1 (gate+tests) ──> T2 (instruction) ──> T3 (ship agent)
      │       └────> T5 (schema)
      └────────────> T6 (docs) <── T2, T4
T4 (policy) : independent
```

## Plan Hardening (P-006) — elevated blast radius

This plan touches the merge gate, CLI distribution, an agent, a policy, and a
schema across multiple template families → **hardening required**.

Hardened risks and mitigations:

1. **Fail-open regression risk** — a bug that silently exits 0 when review is
   enabled but incomplete would re-open the exact hole. *Mitigation*: verdict enum
   is explicit; default is fail-closed; tests assert BLOCK for every
   enabled-but-incomplete branch and for `VERIFY_FAILED`. T1 acceptance criterion:
   "no code path returns exit 0 when enablement is true and completion/resolution
   is not proven."
2. **Wedge risk** (waiting forever for a reviewer that never comes) — *Mitigation*:
   `auto` mode treats no-engagement-signal as not-applicable → PASS; bounded
   `--max-wait`; `required` mode is opt-in and explicitly documented as
   fail-closed.
3. **Command injection** (PR number / repo interpolation) — *Mitigation*: argv
   array, `shell=False`, per-token substitution; injection negative test is
   acceptance-blocking (reuses `subprocess-validation-gating` learning).
4. **Bot-login / ID-type drift** — *Mitigation*: centralize the Copilot login
   constant and use the GraphQL thread node ID for resolution checks (reuses
   `github-review-comment-id-types` learning). A REST-vs-GraphQL login-suffix note
   is captured in T1.
5. **Dogfood drift** — behavioral instruction/agent changes must land template +
   installed mirror together; T2 and T3 each pair template + mirror in one task.
6. **Admin-bypass reintroduction** — *Mitigation*: P-018 names admin non-bypass;
   Ship dark-mode fallback gains an explicit `COPILOT_REVIEW_BLOCK` that fallback
   cannot clear; §1.9 terminal state halts.
7. **Timeout ≠ silent merge** — *Mitigation*: `REVIEW_TIMEOUT` is a distinct BLOCK
   outcome; only an audited `--force` overrides, logged to gitignored
   `.autoharness/gates/`.

## Plan Review Verdict

**APPROVED.** The plan is decomposed into six width-isolated, ≤2h tasks with a
clean dependency graph (CLI/tests before wiring; policy independent; docs last).
Dogfood parity is preserved by pairing each behavioral template with its installed
mirror inside a single task. The fail-closed invariant, multi-round handling,
enablement detection, and bounded-timeout escape from the decision are all mapped
to concrete acceptance criteria. No P-003 decomposition-chain issues (every task
references parent feature). No unsafe design (fails safe, never silently merges).
Ready for harvest.
