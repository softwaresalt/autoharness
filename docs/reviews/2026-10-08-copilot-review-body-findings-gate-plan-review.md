---
title: "Plan review: Copilot review-body findings gate (stash 38D29192)"
description: "Plan-review record for docs/plans/2026-10-08-copilot-review-body-findings-gate-plan.md. Round 1 FAIL (1 P1, 3 P2, 2 P3), remediated in the same session; round 2 PASS (P3 advisories only)."
doc_type: review
plan: docs/plans/2026-10-08-copilot-review-body-findings-gate-plan.md
source_stash: 38D29192
created: 2026-10-08
reviewer: stage (inline persona pass)
---

# Plan review: Copilot review-body findings gate

dispatch_mode: single-agent-declared-degradation
decision: PASS

## Capability declaration (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
  This Stage session has no subagent dispatch surface. Every selected persona
  rubric below was applied inline, with one finding list per persona.
* `TOOL_DEGRADED: model-specific-review-routing`. The anchor-review route was
  not dispatchable. Architecture Strategist and Security Lens ran on the
  caller's model.
* `INTERCOM_DEGRADED`. Agent-intercom is unreachable this session, so no
  broadcasts were sent.
* Engram and graphtor-docs are not installed in this workspace. File-based
  search was used.

## Hardening check

The plan declares `Requires plan hardening: yes`, with contract,
trust-sensitive gate, and external-format signals. A `## Plan Hardening`
section is present. It covers:

* invariants I1 to I7;
* the `ProposedAction` / `ActionRisk` table;
* added verification, rollback, closure, and review-gate capability risk.

The hardening requirement is **satisfied**. The `strict-safety` pack is not
installed, and risky actions are classified anyway.

## Persona coverage

| Persona | Mode | Round 1 findings | Round 2 findings |
|---|---|---|---|
| Constitution Reviewer | inline | PR-2 (P2) | none |
| Python Reviewer | inline | PR-2 (P2, merged), PR-3 (P2) | PR-4 (P3) |
| Scope Boundary Auditor | inline | PR-5 (P3), scenario-count overrun (merged into PR-4) | PR-5 (P3) |
| Learnings Researcher | inline | none. Four learnings are cited, and the plan honours the 157-S timeout lesson through I7. | none |
| Architecture Strategist | inline (same model; anchor route unavailable) | PR-8 (P3) | PR-8 (P3) |
| Agent-Native Parity Reviewer (triggered: agent-facing clearance action) | inline | PR-7 (P2) | none |
| Security Lens Reviewer (triggered: merge-gate trust boundary, external API) | inline | **PR-1 (P1)** | none |

## Round 1: FAIL

### PR-1 (P1, Security Lens): any commenter could clear a P-018 BLOCK

**Finding.** The draft accepted a disposition marker from any non-Copilot
comment author. On a public repository, any GitHub user can post a PR
conversation comment, but resolving a review thread requires write access. The
claimed parity with thread resolution was therefore false. An outside
contributor could clear a fail-closed merge gate.

**Remediation (applied).** U2 fetches `authorAssociation` and honours markers
only from `OWNER`, `MEMBER`, or `COLLABORATOR` authors
(`TRUSTED_DISPOSITION_ASSOCIATIONS`). Any other or missing association is
ignored, which is the fail-closed direction. The change also covers:

* U2 tests;
* U5 doc and U7 policy text;
* the U6 instruction (the operator account posts the comment);
* invariant I6;
* deliberation D4, which records the amendment.

### PR-2 (P2, Constitution and Python): parse logic split across U2 and U3

**Finding.** `overview_version` was parsed in U3, which crossed unit
boundaries.

**Remediation (applied).** All three `ReviewRecord` fields are set in U2 from
one detector call. U3 is classification only.

### PR-3 (P2, Python): open-findings span fragile under nested `<details>`

**Finding.** The span ran to the next `</details>`, and `ccr-overview-v2`
nests per-finding `<details>`. Under-counting anchors would cause a false
BLOCK.

**Remediation (applied).** The span now ends at the next section header
(`<summary>\s*<strong>` or `### `). U1 adds a nested-details fixture row.

### PR-7 (P2, Agent-Native Parity): agents had no defined source for the review ID

**Remediation (applied).** U6 §1.6.1 states that the ID is the GraphQL
`databaseId`, which equals the REST review `id` from
`mcp_github_pull_request_read` and the number in the `#pullrequestreview-<id>`
URL. It also states that a review whose findings were fixed by later pushes
still needs its marker.

### PR-4 (P3, Python and Scope): unit size and scenario count

**Finding.** U1 to U3 listed 4 or 5 scenarios, against the fewer-than-4
heuristic. U2 sits at the upper end of the 2-hour envelope.

**Remediation (applied).** The scenarios were regrouped into 3 table-driven
groups per unit (`subTest` rows over pure functions and fixtures).

**Residual (advisory).** If U2's fixture-builder update grows beyond its two
builders, Ship may split it into U2a (builders plus query) and U2b (marker
parsing).

### PR-5 (P3, Scope): the OQ-1 `advisory` field is optional surface

**Accepted.** It is small, it makes format drift visible, and it has no verdict
effect.

## Round 2: PASS

The revised plan was re-read in full against every persona rubric.

* No P0, P1, or P2 findings remain.
* The requirements trace R1 to R11 maps to the units.
* The dependency graph is acyclic.
* Width isolation holds: code units pair one production file with its test
  file, docs are separate, and rendered surfaces are the accepted triple.
* Runtime verification (the PR #506 reproduction and the no-false-block check)
  and the closure expectations are present.

### Advisory (P3) items carried to harvest

* **PR-4 residual:** the U2 split allowance (above).
* **PR-5:** the advisory field (accepted).
* **PR-8 (Architecture):** U9 could also pin the trusted-association literals
  (`OWNER`, `MEMBER`, `COLLABORATOR`) in the doc and the policy. This is
  optional, and Ship may include it in U9 without re-review.
* **PR-9 (Scope, report-only):** the pre-existing template/mirror drift in
  `github-pr-automation` (about 146 differing lines) is out of scope here. U6
  must edit by section, not by whole-file copy. It is reported to the
  Orchestrator, and no stash entry was created this session.

## Gate

* Round 1: `FAIL`, remediated (review-fix cycle 1 of 3).
* Round 2: `PASS`. The plan may proceed to harvest.
