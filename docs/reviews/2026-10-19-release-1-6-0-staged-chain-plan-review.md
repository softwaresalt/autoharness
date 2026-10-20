---
title: "Plan review: autoharness v1.6.0 release chain (six linearly ordered shipments)"
description: "Multi-persona plan review of docs/plans/2026-10-19-release-1-6-0-staged-chain-plan.md, run as a single-agent declared-degradation pass. Cycle 1 found no P0/P1 and three P2 findings, all fixed in the plan; cycle 2 passed."
doc_type: review
review_target: docs/plans/2026-10-19-release-1-6-0-staged-chain-plan.md
dispatch_mode: single-agent-declared-degradation
decision: PASS
review_cycles: 5
reviewed_utc: 2026-10-20
---

# Plan review: v1.6.0 release chain

Review gate for the umbrella plan (stash 29D0ACB7, 3DB3AE91, 9CC3C661, 9AF294A4, E89674F1, 03427861; deliberation for
G3 at `docs/decisions/2026-10-19-docs-only-verification-gated-disposition-deliberation.md`). Dates UTC. The
machine-readable copy is the `## Plan Review` section of the plan.

dispatch_mode: single-agent-declared-degradation

decision: PASS

## Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch` - this Stage session exposes no reviewer subagent dispatch surface.
  Declared fallback: single-agent persona pass, each persona applied inline against its rubric.
* `TOOL_DEGRADED: model-specific-review-routing` - cross-model routing is not dispatchable here. Declared fallback:
  same-model rubric pass. No selected persona was skipped.

## Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Constitution Reviewer | inline (always-on) | F1 P2 resolved |
| Scope Boundary Auditor | inline (always-on) | F5 P3 |
| Learnings Researcher | inline (always-on) | F6 P3 (cascade-close and checksum conventions reused) |
| Template Integrity Reviewer | inline (triggered: mirrors, checksums, policy text) | F1, F3 |
| Schema-CLI-Docs Coupling Reviewer | inline (triggered: new CLI, schema, registry) | F2 P2 resolved |
| Security Lens Reviewer | inline (triggered: path normalization, release/tag authority) | F4 P3 |
| Architecture Strategist | inline, same-model | none |

## Cycle 1 findings (no P0/P1)

* **F1 (P2, fixed)** Shared Conventions and hardening H3 said "no manual checksum edits" while every prior shipment
  refreshes manifest checksums by computing them from the LF-normalized git blob. Reworded to the blob-derived
  convention and no hand-typed values.
* **F2 (P2, fixed)** S3-U1 (registry plus ten verified CLI forms across two files) was sized S; raised to M, low.
* **F3 (P2, fixed)** S6-U1 did not say how `uv.lock` is bumped; added `uv lock` or minimal edit confirmed with
  `uv lock --check`.
* **F4 (P3, accepted)** The docs-only checker and path normalization are the security-relevant surface; the plan
  puts the rules in one function used by all three call sites (H1) and fails closed on invalid input.
* **F5 (P3, accepted)** 207-S and 217-S are untouched; 217-S is a `dag-root` with no edge to the chain, so there is
  no ordering conflict. The pipeline-topology result for the first shipment is recorded in the staging summary.
* **F6 (P3, accepted)** Stash 5C870EB2 (high, safety-adjacent wording) is left as a post-release candidate per the
  operator brief; the plan flags it so the operator may reorder.

## Cycle 2

Revised sections re-verified against the facts table: every file and line citation was re-read, `backlogit_dispose_shipment`
absence was re-confirmed in the CLI help, the MCP tool list and a source search, the version-site list was re-checked
against `git grep`, and the policy version sequence (1.37.0 current, 1.38.0 for S3, 1.39.0 for S5) was re-checked against
the registry. No open P0/P1.

## Cycle 3 (post-publication, Copilot review of PR 543): two findings accepted and fixed

* **(P1) Start-SHA and lifecycle writes.** P-011 guarantees a clean worktree only before the claim; after claim and
  activation Ship's own writes change tracked backlog files, so a changed-path union would reject a valid docs-only
  task. The item-log comment is git-ignored and adds no tracked change, but the status and marker writes do. Fixed in
  deliberation D-3 and assumption AS-7, plan S5-U1/U2/U4/U7 and hardening H1, and tasks 216.001-T, 216.002-T,
  216.004-T and 216.007-T: a two-class partition (strict implementation class; exact lifecycle files of the task,
  feature and shipment admitted only through a structurally validated frontmatter allowlist with byte-identical body,
  plus new checkpoint files), and a required end-to-end claim, comment, docs edit, completion test that still
  rejects unrelated edits.
* **(P2) Config contract target.** `src/autoharness/schema_contracts.py` sets the current harness-config contract to
  `1.3.0` (the retired agent-intercom pack leaves `capability_packs`); the plan and task 217.003-T stopped at
  `1.2.0`. Fixed to the path `1.1.0` to `1.2.0` to `1.3.0` in plan S6-U3 and R6, task 217.003-T and the rollout entry
  B60A27EC.

## Cycle 4 (post-publication, Copilot review of PR 543 round 2): one finding accepted and fixed

* **(P1) Shipment-wide claim writes.** `ClaimShipment` activates and stamps every queued manifest member (P-002.7 and
  P-002.8), so after the claim the start-SHA diff contains sibling-task claim writes that the three-ID lifecycle
  allowlist rejected, and the acceptance sequence modeled only one task. Fixed in deliberation D-3 and AS-7, plan
  S5-U1/U1b/U1c/U2/U4/U7 and hardening H1, and tasks 216.001-T, 216.002-T, 216.004-T, 216.007-T, 216.008-T and new
  216.009-T: a baseline phase validates a claim-only delta over the whole live manifest and records a SHA-256
  lifecycle baseline; the completion phase requires siblings byte-identical to baseline and allows only allowlisted
  deltas on the task, feature and shipment; a two-task shipment test must pass and still reject an item outside the
  manifest, a stash edit, a body edit, a non-allowlisted key, a sibling edited during the task and a `src/` edit.
  (Superseded in design by cycle 5: the claim-only judgment of the pre-state was replaced by a recorded snapshot.)

## Cycle 5 (post-publication, Copilot review of PR 543 round 3): one finding accepted; design simplified

* **(P1) Pre-baseline lifecycle writes.** The claim-only baseline rejected legitimate writes made before Step 4.1: the
  route label that harness-architect adds during preparation (S5-U5) and, at a task boundary, the preceding task's
  close-out (commit, commit tracking, done, session memory per the Ship template). Enumerating or judging Ship's own
  lifecycle writes cannot be made safe (three rounds of review show the allowlist keeps missing legitimate writes), so
  the design changed class: the baseline is now a recorded pre-implementation snapshot (head SHA, changed paths with
  content hashes, self-digest) that is not judged, except that owned paths must be clean at baseline; only the task's
  own delta after the baseline is judged (implementation class strict, siblings unchanged, task/feature/shipment
  allowlisted keys, byte-identical bodies). The accepted residual risk is recorded (deliberation D-3, AS-8).
  Synchronized in deliberation D-3/AS-4/AS-7/AS-8, plan S5-U1/U1b/U1c/U2/U4/U7 and H1, and tasks 216.001-T, 216.002-T,
  216.004-T, 216.007-T, 216.008-T and 216.009-T. The required integration test now runs a two-task shipment through
  both tasks to completion, including the close-out of task 1 with a dirty session-memory file.

decision: PASS
