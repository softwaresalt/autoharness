---
title: "Reliable Copilot-Review Completion + Comment-Resolution Merge Gate"
description: "Decision for stash 0B278CEE: enforce wait-for-Copilot-review completion and iterative bot-thread resolution as a deterministic, fail-closed pre-merge gate that --admin cannot bypass when Copilot review is enabled."
topic: "How should the harness reliably block merge (including admin merge) until Copilot review completes and its threads are resolved across multiple rounds?"
depth: "hardened"
decision_status: "accepted"
doc_type: decision
source: docs/decisions/2026-07-09-copilot-review-merge-gate-deliberation.md
source_stash_ids:
  - "0B278CEE"
related_stash_ids:
  - "0B3F546C"
  - "027B60E8"
linked_artifacts:
  - "src/autoharness/gates/sizing.py"
  - "src/autoharness/cli.py"
  - "templates/instructions/github-pr-automation.instructions.md.tmpl"
  - ".github/instructions/github-pr-automation.instructions.md"
  - "templates/agents/.ship.agent.md.tmpl"
  - ".github/agents/.ship.agent.md"
  - "templates/policies/workflow-policies.md.tmpl"
tags:
  - "copilot-review"
  - "merge-gate"
  - "admin-merge"
  - "deterministic-gate"
  - "pr-readiness"
  - "P-018"
---

# Reliable Copilot-Review Completion + Comment-Resolution Merge Gate

## Context

Today the harness treats GitHub Copilot shadow review as **advisory / non-blocking
by default**:

* `github-pr-automation.instructions.md` §1.1 — "Shadow review is advisory by default."
* §1.2 — 15-minute poll timeout → "proceed without it."
* §1.8 — cycle limits "do not make shadow review merge-blocking by default."
* §1.9 — the pre-merge readiness gate keys on the **local** review record and
  explicitly treats shadow review as advisory.
* `.ship.agent.md` Step 4 merges with `gh pr merge --merge --admin`; the dark-mode
  admin fallback state machine allows `--admin` for branch-protection review/
  conversation blocks.

**Gap**: when Copilot review IS enabled for a repository, nothing deterministically
holds an (admin) merge until (a) Copilot has actually completed a review for the
**current HEAD** and (b) all resulting Copilot-authored review threads are
resolved — iterating across multiple Copilot rounds when PR rules re-trigger
review. The operator reports the current prose-based wait is unreliable, and
`--admin` can bypass it.

The operator explicitly wants a **reliable / deterministic** enforcement
mechanism, not stronger prose the agent may forget.

## Options Considered

### A. Prose-only reinforcement
Strengthen §1.1 / §1.8 / §1.9 so "wait + resolve" becomes a conditional HARD gate
when Copilot review is enabled.

* **Pro**: cheap; no code; ships fast.
* **Con**: relies entirely on agent compliance. This is exactly the failure mode
  the operator is reporting. Not reliable on its own.

### B. Deterministic gate check (RECOMMENDED core)
A small `autoharness` CLI gate (`autoharness gate copilot-review <pr>`), mirroring
the shipped pre-execution sizing gate (`src/autoharness/gates/sizing.py`). Given a
PR it queries GitHub (via `gh` GraphQL/REST) and classifies:

1. **Enablement** — is Copilot review in play for this PR?
2. **Completion for current HEAD** — has Copilot submitted a review whose
   `commit.oid == headRefOid`?
3. **Thread resolution** — are there any unresolved Copilot-authored review
   threads (`reviewThreads` where `isResolved == false` and the first comment
   author login matches the Copilot reviewer)?

It exits **non-zero (BLOCK)** when review is enabled and the wait/resolution is
incomplete, and **0 (PASS)** when review is satisfied or not-applicable.

* **Pro**: deterministic; code enforces the invariant regardless of agent memory.
  Reuses the proven sizing-gate safety shape (argv-array, `shell=False`, bounded
  timeout, injectable runner for testability).
* **Con**: needs `gh`/network; must be wired into the merge path to have effect.

### C. Workflow policy (RECOMMENDED companion)
Add **P-018** (next free ID after P-017): "Copilot-review completion + thread
resolution is a required pre-merge gate when Copilot review is enabled; admin
merge does not bypass it," with precondition / postcondition / gate-point /
violation-action, wired into the §1.9 terminal states.

* **Pro**: formalizes the invariant as first-class, auditable policy; gives the
  gate teeth and a violation path (P-005 telemetry).
* **Con**: policy alone is still prose; needs B to be reliable.

## Decision

Adopt **B + C + the §1.9 / instruction / agent wiring from A** — the strongest
reliable combination:

1. **B (deterministic gate)** is the reliability core. New module
   `src/autoharness/gates/copilot_review.py` + `autoharness gate copilot-review`
   subcommand, with tests. It is the single source of truth for "may this PR merge
   with respect to Copilot review?"
2. **C (P-018 policy)** formalizes the invariant and its admin-merge non-bypass.
3. **A-wiring** makes the instruction (§1.1 / §1.8 / §1.9) and the `.ship` agent
   merge path (Step 4 + dark-mode admin fallback state machine) **invoke the gate**
   and treat a BLOCK verdict as a hard stop that `--admin` cannot skip.

This gives determinism (code, not just prose), policy backing, and enforcement at
the exact merge decision points including admin fallback.

### Fail-closed vs. fail-open (the critical divergence from the sizing gate)

The sizing gate fails **open** (advisory: config failure → exit 0). This gate is
the opposite where it matters: when Copilot review **is enabled** and the
wait/resolution is **incomplete or unverifiable**, it fails **closed** (BLOCK).
"Green but unverifiable" must never resolve to "merge."

### Enablement detection (false-positive / false-negative handling)

Detection is conservative on the "wait forever" axis and strict on the "already
engaged" axis:

| PR signal | Interpretation | Verdict axis |
|---|---|---|
| Copilot is a **requested reviewer** (`reviewRequests`) | Engaged | Hold until completed-for-HEAD + threads resolved |
| A **Copilot review exists** in `reviews` (any round) | Engaged | Hold until completed-for-HEAD + threads resolved |
| Neither signal present, API reachable | Not-applicable for this PR | PASS (do not wedge waiting for a reviewer that will never come) |
| Workspace config `enforcement: required` | Forced-on | Hold even before Copilot is requested (fail closed until requested + completed) |
| API unreachable / `gh` missing **and** enablement unknown | Cannot verify | BLOCK with actionable message (fail safe) |

* **False positive** (Copilot enabled org-wide but not requested on this PR):
  with no per-PR engagement signal, the gate is not-applicable → PASS, so the
  harness is never wedged. This is the deliberate, documented boundary.
* **False negative** (Copilot should review but wasn't requested): resolved
  **deterministically by explicit config**, not by guessing — a workspace that
  knows Copilot review is required sets `copilot_review.enforcement: required`,
  and the gate then holds merge until Copilot is requested, completes for HEAD,
  and threads resolve.

### Multiple-rounds handling (inherent, not special-cased)

Because the gate requires a completed Copilot review **for the current
`headRefOid`** plus **zero unresolved Copilot threads**, every new push (new HEAD)
that re-triggers Copilot naturally re-arms the gate: it only passes when the
**latest** HEAD has a completed Copilot review with no open bot threads. N rounds
are handled by construction — no round counter needed.

### Bounded timeout escape (logged, still fails safe)

A bounded `--max-wait` window governs how long the harness waits for an engaged
Copilot reviewer to submit a review for the current HEAD. On expiry the gate emits
a distinct `REVIEW_TIMEOUT` outcome that is **logged** and **still BLOCKS by
default** — it never silently passes to merge. An operator may override only via
an explicit, audited `--force` flag (mirroring `gate check --force`), recorded to a
gitignored audit log under `.autoharness/gates/` (same pattern as the existing
`gate-force-audit.log`). Timeout never equals silent merge.

### Admin non-bypass

`--admin` addresses branch-protection blocks; it does **not** satisfy this gate.
Ship must run `autoharness gate copilot-review` (BLOCK ⇒ halt) **before** any
merge, including the dark-mode admin fallback path. P-018 names admin-merge
non-bypass explicitly and is referenced by the §1.9 terminal states and the Ship
merge/admin fallback state machine.

## Scope

Scoped to stash **0B278CEE**. Relationships noted but **not** pulled in:

* `0B3F546C` — fail-closed denylist CI primitive (required-check aggregation). The
  Copilot-review gate is a *merge-readiness* gate; the CI primitive is a *checks*
  gate. They compose but are separate shipments.
* `027B60E8` — deterministic PR-gating hooks catalog. This work is one concrete
  instance of such a hook; the catalog effort remains separate.

## Consequences

* New deterministic gate + CLI subcommand + tests (width: CLI/gate code).
* github-pr-automation instruction template + installed mirror updated so the
  conditional hard gate replaces "advisory by default" **when review is enabled**.
* `.ship` agent template + mirror invoke the gate on the (admin) merge path.
* P-018 added to the policy template (no installed `.github/policies/` mirror
  exists — policy touches only the template).
* Workspace-profile schema gains a `copilot_review.enforcement` toggle
  (`auto` | `required` | `disabled`, default `auto`).
* Docs describe the gate + P-018 for operators.

## Reused Learnings (compound library)

* `docs/compound/2026-05-06-github-review-comment-id-types.md` — thread resolution
  uses the GraphQL **thread** node ID (`PRRT_…`); the gate reads
  `reviewThreads { id isResolved comments(first:1){ nodes{ author{ login } } } }`
  and matches the Copilot login (`copilot-pull-request-reviewer`, no `[bot]`
  suffix in GraphQL).
* `docs/compound/2026-07-01-subprocess-validation-gating.md` — argv-array +
  `shell=False`, per-token substitution, an **injection negative test as an
  acceptance-blocking criterion**, and gitignored runtime/audit artifacts under
  `.autoharness/gates/`. This gate inherits those patterns but inverts the
  fail-open default to fail-closed where review is enabled.

## Verification

Reviewed the sizing gate + CLI wiring, the Ship merge path and dark-mode admin
fallback state machine, the github-pr-automation instruction (§1.1/§1.8/§1.9), and
the P-014/P-017 policy structure. The decision composes with existing P-014
(local readiness) and P-017 (dark factory) without redefining them: P-018 adds an
independent, conditional, fail-closed dependency on Copilot-review completion when
Copilot review is enabled.
