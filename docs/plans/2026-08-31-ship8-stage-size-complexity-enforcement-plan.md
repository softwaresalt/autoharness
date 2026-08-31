---
title: "SHIP-8 — Stage size/complexity decomposition enforcement"
date: 2026-08-31
slug: stage-size-complexity-enforcement
doc_type: plan
source_stash: "2E67938C (primary); 6A2D62DD (bounded, non-consuming)"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-8"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "no"
plan_review_verdict: "PASS"
---

# SHIP-8 — Stage size/complexity decomposition enforcement

## Problem

`2E67938C`: backlogit exposes `size` and `complexity` as first-class fields.
Stage must **actually use them, robustly and enforceably**, when decomposing
work, so that shipment and session growth is bounded and multiplicative AI
token/credit consumption is controlled. Today the fields exist; the requirement
is that Stage's decomposition consumes them as a gate rather than as decoration.

Two concrete gaps, both verified at `2661c1c8`:

1. **The mandate is authored but the enforcement is advisory.**
   `templates/agents/_stage.agent.md.tmpl` carries the two-axis rule (14
   occurrences of `complexity`) and `templates/skills/harvest/SKILL.md.tmpl`
   carries 22. But the documented failure path when the registry does not
   advertise sizing is to **degrade to prose in the description and flag it** —
   the agent continues. There is no point at which a missing or invalid
   `size`/`complexity` **stops** the harvest.
2. **The degradation path was silently live in this very workspace.** Because the
   installed registry omitted `features.sizing` (SHIP-7), the enforcement branch
   was unreachable here. This is the `029-DL` law again: the rule is produced by
   nothing and penalizes nothing, so it survives only by agent goodwill.

Evidence that the fields are usable once advertised: `backlogit_update_item`
declares `size` (with `size_source` and `size_ruleset_version`) and `complexity`
as **separate, mutually exclusive, body-preserving** mutation seams;
`backlogit_create_item` accepts no sizing params at all;
`backlogit_list_items` exposes a `complexity` filter and a computed
`size_composition` rollup on features and shipments. The write sequence is
therefore fixed at three calls per task (create → size → complexity), and the
rollup gives a shipment-level budget surface for free.

## Direction

Convert the two-axis rule from documentation into a gate at three points:

* **Harvest-time, per task.** A task without both a valid `size` and a valid
  `complexity` is not a harvested task. Enum-validate both before writing;
  reject and halt on an invalid value rather than coercing or defaulting.
* **Harvest-time, per split trigger.** `size` implying more than two hours of
  human-equivalent effort forces a split regardless of `complexity`;
  `complexity: high` forces a split or an explicit de-risking step (spike,
  further decomposition, or additional deliberation) regardless of `size`. Both
  triggers already exist in prose; they become checked conditions.
* **Shipment-assembly-time, per shipment.** Read the shipment's
  `size_composition` rollup back after assembly and fail the assembly if
  `unsized > 0`, or if the composition exceeds the declared budget.

**Fail-closed when advertised; degrade loudly when not.** If the active registry
advertises `features.sizing`, a missing or invalid value is a **halt**. If it
does not (for example a `backlog-md` install), the existing behaviour is
retained — enum-validated values preserved as clearly-labelled prose in the
description — but the degradation must be reported explicitly in the harvest
report, not merely noted. That preserves the documented multi-registry contract
while removing the silent path.

## Hardening (P-006)

Not triggered: confined to Stage/harvest template text plus tests. No schema, no
CLI distribution surface, no template family beyond the two documents already
carrying the rule. Two constraints are nonetheless recorded as binding.

* **H1 (binding).** The gate applies to **newly harvested output only**. Day-one
  blast radius against the existing corpus must be exactly zero — no retroactive
  validation sweep, no migration of existing unsized items. This mirrors the
  Authority Test v2 migration story that portfolio unit S2 relies on, and it is
  what makes the gate promotable at all.
* **H2 (binding).** The three-call write sequence must be respected exactly:
  create with no sizing params; then one update setting `size` together with
  `size_source: agent` and a non-empty `size_ruleset_version`; then a separate
  update setting `complexity`. These seams are mutually exclusive and cannot be
  combined with each other or with any other field update.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Make the harvest sizing gate fail closed when the registry advertises sizing, with explicit reported degradation when it does not | M | medium | `templates/skills/harvest/SKILL.md.tmpl`, `templates/agents/_stage.agent.md.tmpl` + mirrors |
| 2 | Add a shipment-assembly size-composition budget check and a regression test for both gates | M | high | `templates/agents/_stage.agent.md.tmpl`, `tests/` |

## Non-goals

* **N1.** No backlogit schema change and no new sizing field.
* **N2.** No derivation of a range-deterministic per-session token/complexity
  threshold. `6A2D62DD` states plainly that "the threshold value is YET TO BE
  DETERMINED — establishing it is part of what the spike should explore". This
  shipment enforces against the thresholds that **already exist** (the 2-hour
  rule and the two enum axes). `6A2D62DD` stays active and is unconsumed.
* **N3.** No one-shipment-per-session execution policy. That is the second,
  coupled half of `6A2D62DD` and is Ship-side session lifecycle, not Stage
  decomposition.
* **N4.** No auto-splitting of oversized tasks. The gate **halts and reports**;
  a human or a subsequent Stage pass decides the split. Auto-splitting is
  explicitly a non-goal of portfolio unit S2 as well, and the two must not
  disagree.
* **N5.** No retroactive validation of the 612 existing tasks (**H1**).

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `verify-harness`; a
negative test per gate (harvest a task with no `complexity` → must halt; assemble
a shipment with `unsized > 0` → must fail); and a positive test confirming a
`backlog-md`-shaped registry without `features.sizing` still completes with a
reported degradation rather than a halt.

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Correctness | **P1** | A fail-closed harvest gate can **strand a partially written task**: `create_item` succeeds, the `size` update succeeds, the `complexity` update fails, and the halt leaves a half-sized orphan in the backlog. | **Resolved.** Task 1's acceptance requires the gate to validate **both** enum values *before* the create call, so a rejection happens before any write. If a write nonetheless fails mid-sequence, the halt message must name the item ID and the exact remaining call, so the state is recoverable rather than mysterious. The three seams are ordered so that the item is never left in a state a subsequent run cannot complete idempotently. |
| 2 | Scope/Maintainability | **P1** | This overlaps portfolio unit **S2**, whose `ART-03` detector checks exactly "`size` **and** `complexity` present". Building both is duplicated effort or, worse, two disagreeing rules. | **Resolved.** They are the **producer** and the **detector** of the same invariant and are deliberately complementary: SHIP-8 makes Stage *emit* conforming items; S2 *verifies* that anything in the backlog conforms, including items Stage did not produce. To guarantee they cannot disagree, this plan adopts S2's own constraints verbatim — enforce-on-new-only (**H1**), no auto-split (**N4**), no schema change (**N1**) — and records that S2 is the authority if they ever diverge. |
| 3 | Architecture | **P1** | Enforcement lives in **template prose** read by an agent. Prose is not a machine gate, so this reproduces the `029-DL` failure it claims to fix. | **Accepted, honestly bounded.** Task 2's shipment-assembly check is a genuine machine check — it reads the `size_composition` rollup back from the tool and fails on `unsized > 0`, which no amount of agent goodwill can fake. The harvest-time gate is prose plus a regression test asserting the documented behaviour. This is a **partial** mechanisation and is labelled as such rather than overclaimed; full mechanisation of harvest-time validation is precisely what S2's `ART-03` delivers, and duplicating it here would violate finding 2's resolution. |
| 4 | Constitution | P2 | Halting a dark-factory session on a sizing violation could strand an AFK operator. | The halt is a **decomposition** halt, not a session halt: it rejects one malformed task and reports it. Other independent scoped items continue, consistent with this run's own operating rules. |
| 5 | Schema/CLI/docs coupling | P2 | The `size_ruleset_version` value must be non-empty and meaningful; an arbitrary string makes provenance useless. | Task 1's acceptance requires a single declared ruleset identifier recorded in the harvest documentation, written with `size_source: agent`, and used consistently. |
| 6 | Security | P3 | No security surface. | Confirmed: no credentials, no network, no path handling, no destructive command. |
| 7 | Maintainability | P3 | The gate depends on SHIP-7 having installed `features.sizing`. | Encoded as a real `blocks` edge (SHIP-7 → SHIP-8), not as a comment. |

**Verdict: PASS.** 3 P1 raised, all 3 resolved. Zero unresolved P0/P1. Two
review-fix cycles of three.
