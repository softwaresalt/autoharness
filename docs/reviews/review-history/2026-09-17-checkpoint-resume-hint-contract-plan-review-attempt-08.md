---
title: "Plan review attempt 08 (terminal) — Checkpoint resume_hint contract"
description: "Immutable per-attempt plan-review artifact recording the independent attempt-08 review of docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md at revision 7, against reviewed content HEAD f142173c. Gate result FAIL; decision BLOCKED on one P0, seven P1 and three P2 deduplicated findings: raw checkpoint create remains reachable through Ship's backlogit/* wildcard allowance so the guarded path is optional, the executable records cite a source stash ID that does not exist, T2 invokes the scanner before the scanner is implemented, the guarded MCP create names no server, owner or registration, scanner input is not hardened, the producer inventory is unsatisfiable, the terminal-classification text contradicts itself, and activation parity between template and installed mirror is incomplete. The authorized remediation cycle is exhausted: no remediation was performed, no finding is closed, and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-08.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 8
attempt_range: "08"
attempt_conformance: conforming
review_terminal: true
verdict_manifest: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-07.md
plan_path: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
plan_id: checkpoint-resume-hint-contract
reviewed_revision: 7
reviewed_content_head: f142173c
reviewed_content_state: committed
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 71200CBB
source_stash_id_recorded_in_backlog: 2A7C48A8
source_stash_id_conflict: true
feature_id: 172-F
shipment_id: 180-S
review_cycle: 8
dispatch_mode: declared-degradation
anchor_route: absent
anchor_route_note: "No cross-model anchor was available. The cross-model rubrics ran under same-model declared degradation; this is recorded, not compensated for."
gate_result: FAIL
decision: BLOCKED
verdict_at_entry: REMEDIATED-PENDING-REVIEW
verdict_at_entry_plan_revision: 7
remediation_authorization: none-exhausted
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 1
p1_open: 7
p2_open: 3
severity_basis: "Severities are the dispatch-recorded severities. The raw-create exposure through the Ship wildcard was dispatched with an explicit P0 label; the remaining substantive findings dispatched for this plan are recorded P1. Findings dispatched on the portfolio P2 list are recorded P2 against the plan surface they land on."
persona_coverage:
  - persona: constitution
    status: complete
  - persona: python
    status: complete
  - persona: scope-boundary
    status: complete
    findings: provenance-p1
  - persona: learnings
    status: degraded
    note: "Not-ready/degraded: could not inspect the diff. Relevant prior lessons were retrieved and applied."
  - persona: architecture
    status: complete
  - persona: agent-native-parity
    status: complete
  - persona: security-lens
    status: complete
tags:
  - "plan-review"
  - "terminal-review"
  - "checkpoint"
  - "recovery-contract"
  - "provenance"
---

# Plan review attempt 08 (terminal) — Checkpoint `resume_hint` contract

This artifact records **one thing**: the independent reviewer's verdict on plan
revision 7 as it stands at content HEAD `f142173c`. It has no Part 2. The
authorized remediation budget is **exhausted**, so no remediation followed this
review, no finding below is closed, and Stage asserts no `PASS`.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md` |
| Reviewed revision | 7 |
| Reviewed content HEAD | `f142173c` (committed) |
| Verdict at entry | `REMEDIATED-PENDING-REVIEW` at plan revision 7 |
| Covering feature / shipment | `172-F` / `180-S` |
| Source stash (plan frontmatter) | `71200CBB` — exists |
| Source stash (executable records) | `2A7C48A8` — **does not exist** |
| Dispatch mode | `declared-degradation` |
| Gate result | **FAIL** |
| Decision | **BLOCKED** |

## Dispatch and coverage

All **seven** required personas ran: Constitution, Python, Scope Boundary,
Learnings, Architecture, Agent-Native Parity, Security Lens.

* **Anchor route absent.** No cross-model anchor was reachable; the cross-model
  rubrics executed under *same-model declared degradation*.
* **Learnings degraded / not-ready.** Could not inspect the diff; prior lessons
  were retrieved and applied, diff-grounded checks did not run.
* **Scope Boundary raised a provenance P1** on this plan — finding B1 below.

## P0 findings (1)

**A1 — raw checkpoint create remains exposed through Ship's `backlogit/*`
wildcard.**
The plan introduces a guarded create path, but Ship's tool allowance still
includes a **`backlogit/*` wildcard** that matches the raw create operation. A
guard that an agent can decline to use by calling the unguarded operation that is
still permitted is **advisory, not a gate**. Every producer guarantee in this
plan — `resume_hint` presence, shape, and validation — is defeated by one call to
the raw operation the wildcard continues to admit. The wildcard must be narrowed
to exclude raw create, or the raw operation must be removed from the surface;
neither is specified.

## P1 findings (7, deduplicated)

**B1 — the executable records cite a source stash ID that does not exist.**
The plan's frontmatter names `source_stash_id: 71200CBB`, which is present in the
stash record. The executable backlog records — `172-F` and `180-S` and the
`172.x` tasks — instead cite `2A7C48A8`, which **appears in no stash file, live
or archived**. This is an **exact source provenance violation** and is recorded
P1. It is recorded and **not corrected**: the executable backlog is outside the
authorized mutation scope of this evidence-only cycle.

**B2 — `T2` invokes the scanner before the scanner exists.**
`T2` is sequenced to run the producer scan, but the scan implementation lands in
a later task. A task that invokes a not-yet-implemented component produces a
**missing observation, not a result** — the same failure mode this portfolio's
P-004 work exists to close, reproduced inside this plan's own ordering.

**B3 — the guarded MCP create has no server, owner, or registration.**
The guarded operation is specified as an MCP tool but the plan names **no MCP
server that exposes it, no owner that implements it, and no registration step**
that makes it callable. As written, the guarded path is unreachable, which leaves
the raw path (A1) as the only working path.

**B4 — scanner input is not hardened.**
The scanner consumes checkpoint JSON without a stated input-hardening contract:
no bound on size or nesting depth, no behaviour for malformed or partially
written files, and no quarantine path. The live checkpoint directory already
contains records that fail a naive parse, so this is an observed condition, not a
hypothetical one.

**B5 — the producer inventory is unsatisfiable.**
The plan requires a complete inventory of `resume_hint` producers, but producers
include agent documents whose call sites are **prose instructions**, not
statically enumerable call graphs. The inventory as specified cannot be completed
by any procedure the plan defines, so the task that depends on it cannot be
declared done.

**B6 — the terminal-classification text contradicts itself.**
The plan classifies terminal checkpoint states in two places with **incompatible
wording**: one treats a resolved checkpoint as terminal regardless of its
`resume_hint`, the other requires a terminal record to carry a specific hint
shape. A validator implementing either is conformant with the text and
inconsistent with the other.

**B7 — activation parity between template and installed mirror is incomplete.**
The activation path is specified for one of the two surfaces. The template and
its installed mirror must activate the contract identically, and the plan does
not require the mirror to be checked, so a mirror that never activates the
validation passes every gate this plan defines.

## P2 findings (3)

**C1 — the verdict manifest's `description` asserts a falsehood.**
The mutable verdict manifest's `description` claims `No PASS exists anywhere in
this record` while its own roster carries `verdict: PASS` at attempts 2 and 3.
The truthful statement is narrower: no `PASS` exists at or after attempt 4, and
none exists against the governing revision. Recorded against the manifest
wording **as observed at `f142173c`**; one defect class, six instances across the
portfolio, counted once per manifest surface.

**C2 — inline checkpoint argv is exposed in prose.**
The plan reproduces checkpoint CLI invocations inline in agent-facing prose.
Inline argv in a Markdown surface is composed by a model rather than executed as
an argument vector, and it invites the same substitution defect recorded as P0
on `178-S`. Recorded P2 here because this plan's guarded path is the MCP
operation, not the CLI.

**C3 — registry links parity is incomplete.**
The backlog-registry `operations` entries for the checkpoint surface are not
updated in step with the guarded operation the plan introduces, so registry
consumers resolve the raw operation while the plan's prose names the guarded one.

## Disposition

**No remediation.** The authorized remediation budget is exhausted.
`remediation_revision` is `null`, `disposition` is `null`, and the governing
revision remains 7 — the revision that was reviewed and found BLOCKED.

This plan is **not harvest-ready and not Ship-ready**. No backlog executable
record, source file, test or configuration was changed on the strength of this
review.
