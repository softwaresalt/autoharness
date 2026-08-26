---
title: "Agent Output Timestamps for Phase Transitions — decided plan"
doc_type: decided-plan
status: planned
created: 2026-07-02
feature: "059-F"
tasks:
  - "059.001-T"
  - "059.002-T"
supersedes: docs/archive/plans/2026-07-02-agent-output-timestamps-plan.md
---

# Decided Plan: Agent Output Timestamps for Phase Transitions

**Outcome:** Feature `059-F` is queued and plan-ready as a template/instruction
change. The source artifact records operator clarification of the required
surfaces, trigger scope, and timestamp format, but it records no plan-review
verdict, shipment, PR, or merge commit, so this decided-plan remains **planned**.
P-001 sequencing also kept shipment assembly out of scope while `057-S` was the
active release unit. This replaces the verbose original, archived for traceability
at `docs/archive/plans/2026-07-02-agent-output-timestamps-plan.md`.

## Decisions

1. **Land the behavior on both surfaces.** A new universal output-timestamps
   instruction handles pack-less installs, and the `agent-intercom` Progress
   Protocol carries the same requirement for broadcast-capable installs.
2. **Stamp only meaningful phase transitions and long-running operations.** The
   rule applies to planning, build, review, runtime-verification, operational-
   closure, and other long-running boundaries, not every trivial line of output.
3. **Use one canonical format.** Emit ISO-8601 UTC plus the delta since the
   previous stamp; the first stamp may use `(+0s)` or omit the parenthetical.
4. **Treat templates as the product.** Primary edits land in the template files,
   install-harness registration, and matching dogfood mirrors.
5. **Avoid needless churn.** No new template variable is introduced, and the agent
   broadcast literal tables inherit the rule by reference rather than by mass
   string rewrites.

## Implementation (2 tasks)

| Task | Scope |
|---|---|
| 059.001-T | Author the universal `output-timestamps` instruction template, register it in install-harness, map it to Primitives 6 and 7, and add the rendered dogfood mirror |
| 059.002-T | Weave the timestamp requirement into the `agent-intercom` Progress Protocol and update the installed mirror to match |

## Key constraints preserved

- The rule stays environment-agnostic and applies whether or not the
  `agent-intercom` capability pack is enabled.
- The universal instruction is the single format authority; the intercom overlay
  references it instead of defining a divergent format.
- Install-harness registration is required, but no variable-resolution-table
  change is needed because the timestamp format is fixed text, not a template
  variable.
- Verification stays documentation-oriented: frontmatter validity, markdown
  structure, unresolved-variable checks, cross-reference integrity, and the
  existing `verify_workspace` coverage if it enumerates base instruction mirrors.
- Out of scope by design: agent broadcast literal tables, foundation docs,
  schemas, and CLI stdout formatting.

## Rejected alternatives

- **Intercom-only implementation** — rejected because pack-less installs would
  miss the behavior entirely.
- **Stamp every trivial output line** — rejected as noise that obscures the
  meaningful elapsed-time signal.
- **Rewrite every literal broadcast string in agent tables** — rejected as
  unnecessary churn once the universal rule and intercom Progress Protocol carry
  the requirement.
- **Extend `autoharness` CLI stdout formatting** — rejected because the operator
  scoped the change to agent output / instruction surfaces.

## Post-clarification refinements folded in

- The surface ambiguity was resolved to **both** the universal instruction and the
  `agent-intercom` overlay.
- The trigger ambiguity was resolved to **phase transitions and long-running
  operations only**, explicitly excluding trivial lines.
- The format ambiguity was resolved to **ISO-8601 UTC + delta**, with an explicit
  first-stamp rule.