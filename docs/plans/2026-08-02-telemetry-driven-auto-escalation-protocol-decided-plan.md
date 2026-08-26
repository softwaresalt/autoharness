---
title: "Telemetry-driven Auto-escalation Protocol"
doc_type: decided-plan
status: planned
created: 2026-08-02
feature: "106-F"
supersedes:
  - docs/archive/plans/2026-08-02-telemetry-driven-auto-escalation-protocol-plan.md
---

# Decided Plan: Telemetry-driven Auto-escalation Protocol

**Outcome:** Planned as feature `106-F` / capability `011-DL(b)` and recorded in the source plan as policy **P-013.6** with P-006 hardening applied. No PR or merge evidence appears in the source plan, so status remains `planned`. The decided scope formalizes the autoharness-side protocol and verification surface only: agents can compile an escalation payload, resolve a stronger reasoning route, and hand off terminally to engram, while the telemetry emitter/store and automated threshold-evaluation engine remain explicitly routed out.

## Decisions

- Extend the existing halt-and-prompt seam into a product-level **auto-escalation protocol** using the named-route pattern proven by P-013.5. The protocol lives in schemas, instructions, agent templates, policy text, verification, and tests.
- Treat escalation as **reasoning escalation, never authority escalation**. Escalation must not self-authorize shipment claims, merges, source mutation, or policy bypasses; it preserves P-001, P-009, P-014, P-017, and P-020.
- Add an optional `model_routing.escalation` route with **per-field fallback to `tier3`**. Configured routes win; literal spec examples do not override the resolved configuration.
- Install a dedicated `escalation-protocol.instructions.md` whenever **either** `_stage.agent.md` or `_ship.agent.md` is present. The contract is not two-agent-only.
- Define `ESCALATION_DEGRADED` as a first-class fail-closed outcome. It applies when the resolved route is unavailable, the engram handoff surface is unavailable, or the fully resolved escalation tuple equals the acting agent's already-resolved role route and would therefore be a no-op.
- Keep the runtime telemetry emitter, queryable store, and automated threshold evaluator **outside** this increment under the external-guard pattern. The current delivery is a protocol contract, not the whole runtime automation stack.

## Implementation (9 tasks)

- **T1 — Schema route:** add optional `model_routing.escalation` to both harness-config schema files without regressing current config validation.
- **T2 — Installer/skill contract:** document `ESCALATION_PROVIDER`, `ESCALATION_FAMILY`, and `ESCALATION_REASONING_EFFORT` with tier3 fallback semantics and install the new instruction whenever either primary agent exists.
- **T3 — Escalation-protocol instruction:** author the payload contract, authority-preservation invariant, and single canonical `ESCALATION_DEGRADED` definition.
- **T4 — Stage template:** add compile → resolve → engram handoff → halt behavior, with degraded fallback to the existing operator-halt path.
- **T5 — Ship template:** mirror the same protocol and degraded behavior for Ship.
- **T6 — Policy text:** add **P-013.6** to the workflow-policy template and amendment log.
- **T7 — Verification:** add fail-closed checks for route resolution, same-route no-op detection, directive presence, and either-agent instruction installation.
- **T8 — Tests:** cover positive and negative verification cases, including tier3 fallback and same-route degradation.
- **T9 — Boundary decision doc:** record what stays external and the conditions for later re-entry.

## Key constraints preserved

- Per 097-S, the eventual shipment manifest is task-only: the covering feature 106-F is derived from task parentage and is not itself a manifest item.
- The schema change is **additive and optional**; existing `.autoharness/config.yaml` must remain valid unchanged.
- Verification is **existence-gated** and fallback-aware: legacy/default installs do not false-fail, but missing directives, missing instruction installs, unresolvable routes, or same-route no-ops fail closed.
- The instruction install condition is **either-agent**, not tied to the two-agent role-enforcement gate.
- No change reaches backlogit or engram binaries, and no live telemetry emitter/store or runtime MAX_ITERATIONS engine is implemented here.
- Escalation ends in **halt + handoff**, not retry loop continuation or authority expansion.

## Rejected alternatives

- **Implementing the live telemetry emitter/store and threshold evaluator in this increment** — rejected via the external-guard boundary. This plan formalizes the autoharness contract only.
- **Hanging the protocol off the two-agent role-enforcement instruction** — rejected because Stage-only or Ship-only installs would then reference an uninstalled contract.
- **Using literal spec model names as the protocol authority** — rejected in favor of the config-resolved route with explicit per-field fallback.
- **Allowing a same-model "escalation" to count as success** — rejected because it is not a real escalation and must fail closed as `ESCALATION_DEGRADED`.

## Review findings that changed the plan

- A Copilot review finding forced the **same-route guard** into the protocol: Stage currently resolves to the same tuple as `tier3`, so silent fallback would otherwise pretend to escalate while staying on the same model.
- The verification surface was tightened to prove both **route resolution** and **directive presence**, plus the new either-agent installation rule.
- The plan explicitly carried forward the 104-F lesson that fallback-aware, existence-gated verification is required to avoid false failures on legacy/default installs.

## Rollback

The change set is additive. Safe rollback order is reverse-topological: tests, verification, policy/instructions, agent-template references, installer variables, then schema route. No data migration is involved.