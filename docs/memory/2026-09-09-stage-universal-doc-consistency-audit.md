---
title: "Stage session — universal shipment documentation consistency audit (164-F / 172-S)"
date: 2026-09-09
agent: stage
session_id: stage-2026-09-09-8F2FD1F6-universal-doc-consistency-audit
doc_type: memory
shipment_id: 172-S
feature_id: 164-F
source_stash: 8F2FD1F6
status: complete
tags: [stage, staging, documentation-consistency, universality, compound-learning, handoff]
---

# Stage session — universal shipment documentation consistency audit

## Outcome

Staged operator intake `8F2FD1F6` end-to-end into feature **164-F** and queued
shipment **172-S** (SHIP-14, 11 items). Handoff token for Ship: **172-S**.
No source, template, or PR work performed (P-010 respected).

## Degraded-mode declaration (P-012)

`TOOL_OK: backlogit`. `TOOL_DEGRADED: agent-engram, graphtor-docs,
agent-intercom` — all three capability packs are declared in
`.autoharness/config.yaml` and have installed instruction surfaces, but none
exposed MCP tools this session. Fell back to documented file-based discovery
(grep/view over `templates/`, `docs/compound/`, `.backlogit/`). Operator
independently confirmed intercom unavailable; local CLI visibility only.
No silent ad-hoc fallback for a *configured-and-available* tool occurred.

## Startup recovery

Zero-candidate normal startup. Enumerated all 32 checkpoints unfiltered;
`needs_quarantine: 0`, no validation anomalies, all `agent: stage` /
`status: resolved`. No active candidate ⇒ proceeded to triage. Not a failure.

## The decisive finding

The operator asked for "a compound learning that gets applied by the harness on
every shipment regardless of workspace". Investigation showed those two
properties are **mutually unreachable by the compound library alone**:

* `templates/skills/compound/SKILL.md.tmpl` authors into the *target
  workspace's own* `docs/compound/`, which is empty at install time.
* Nothing under `templates/foundation/`, `templates/packs/`, or any install
  layer bundles or propagates learning content.

So a `docs/compound/` entry written here can never execute in a customer
workspace. Satisfying the request literally (author a compound entry) would have
met its letter and failed its intent. Resolution: **separate memory from
behaviour** — `docs/compound/` is the memory vector (this repo only), normative
**templates** are the behaviour vector (every workspace).

## Adjacency handled, not duplicated

`162-F` / `170-S` (queued, plan-reviewed PASS, 13 tasks) already builds a
**conditional** Evidence Consistency Reviewer persona with a 10-point rubric.
164-F is deliberately scoped as the **universalization + completion** layer over
that substrate, not a competing implementation:

* trigger: conditional + dogfood-path ⇒ every-shipment + technology-agnostic;
* adds the four categories 162-F lacks (5 quantitative, 6 ownership/role,
  8 scope/distribution wording, 9 neighbour-schema consistency);
* adds the PR-body concision contract and the anti-self-referential rule.

`docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md` is
**consolidated in place** (164.003-T), not duplicated, per operator instruction.

## Decisions (D1–D8)

D1 single normative surface, referenced never restated · D2 unconditional audit
obligation with recorded outcome · D3 technology-agnostic predicates only ·
D4 consolidate the compound learning · D5 PR bodies carry outcome only ·
D6 anti-self-referential readiness (mutable surfaces own current-HEAD;
committed evidence records immutable/named state) · D7 P-021 routing ·
D8 no new template variables, verified negatively.

## Gates

* Plan hardening (P-006): **required and applied** — 8 findings H1–H8.
* Plan review: **PASS**, cycle 1, zero P0/P1 (3 accepted P2/P3).
* Two-axis sizing: all 10 tasks carry `size` + `complexity`; `unsized: 0`.
  `164.004-T` is `complexity: high`, so the gate forced a de-risking step —
  `164.010-T` was added for that purpose and also discharges P2-1/H6.

## Artifacts

* `docs/decisions/2026-09-09-universal-shipment-documentation-consistency-audit-deliberation.md`
* `docs/plans/2026-09-09-universal-shipment-documentation-consistency-audit-plan.md`
* `.backlogit/queue/164-F.md`, `164.001-T`…`164.010-T`, `172-S.md`

## Next steps for Ship

**Do not claim 172-S until 170-S has shipped.** The sequencing edge
(`172-S blocks-depends 170-S`) exists because both modify the Ship agent, the
review persona, and pr-lifecycle. `164.010-T` is the mandatory first
substantive step after the RED/authoring tasks: it re-reads those surfaces as
170-S actually left them and must HALT if 170-S has not shipped.

## Known residual (reported, not silently resolved)

`.backlogit/archive/stash.jsonl` was **not committed** this session. It records
this session's archival of `8F2FD1F6` but *also* carries a pre-existing
uncommitted archival of `9E22BFC6` belonging to another Stage publication set
(tracked by stash `2B68F9D6` / `1CD92B69` / `6B627A50`). Committing the file
would have swept unrelated work into this publication, which the operator
explicitly prohibited. `.backlogit/stash.jsonl` has net-zero content change
(entry added then archived) and shows only line-ending noise.

Traceability is unaffected: `8F2FD1F6` is cited by 164-F's description, the
deliberation, and the plan, and its archived state is live in local backlogit
state.
