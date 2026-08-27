---
title: "plan-review — Telemetry-driven Auto-escalation Protocol (106-F)"
type: plan-review
date: 2026-08-02
route: claude-opus-4.8 / anthropic / high (P-013.5)
plan: docs/archive/plans/2026-08-02-telemetry-driven-auto-escalation-protocol-plan.md
spike: docs/spikes/2026-08-02-telemetry-driven-auto-escalation-protocol-spike.md
source_stash: 34D50F2D
deliberation: 011-DL
verdict: PASS
p0_count: 0
p1_count: 0
p2_count: 2
review_fix_cycles: 2
requires_plan_hardening: yes
hardening_present: yes
---

## Verdict: PASS

The plan is bounded, grounded in real repository structure (the existing Ship
"Escalation Protocol" seam and the shipped P-013.5 named-route pattern), and
draws a defensible product boundary that routes the runtime trigger engine and
telemetry emitter/store OUT via the external-guard pattern. Plan hardening is
present and commensurate with the elevated (schema + multi-family) blast radius.

## Findings

### P0 — Blocking (0)
None.

### P1 — Must-fix before harvest (0)
None. Specifically checked and cleared:
- **P-003 speculative-task risk — CLEARED.** Every task has a concrete,
  independently verifiable acceptance criterion (schema validates the unchanged
  config; verify checks pass/fail deterministically; directive text is present).
  The protocol prose is a real, testable product artifact even though its runtime
  *trigger* is external — directly analogous to 079-F shipping `ToolTelemetryEvent`
  as a forward-contract schema with no emitter. Not speculative.
- **Model-routing regression — CLEARED.** `escalation` route is optional, no
  required fields, tier3 per-field fallback; T1 acceptance pins the unchanged
  `.autoharness/config.yaml` as a regression guard; T8 negative test covers the
  no-route install. Mirrors the 104-F fail-closed-without-false-fail lesson.
- **Authority-escalation drift — CLEARED.** Reasoning-not-authority invariant is
  encoded in T3/T4/T5/T6; terminal state is halt + engram handoff, preserving
  P-001/P-009/P-014/P-017/P-020.

### P2 — Advisory (2, non-blocking; folded into acceptance)
- **P2-1 "Inert until runtime" must be operator-explicit.** Because the runtime
  trigger evaluator is OUT of scope (residual risk 1), the protocol is dormant
  until a telemetry emitter/store exists. Fold into **T6 (policy)** and **T9
  (external-guard doc)** acceptance: both must state plainly that P-013.6 defines
  the protocol contract and that automated firing is gated on a future runtime
  substrate, so operators are not misled into believing auto-escalation is live.
- **P2-2 `ESCALATION_DEGRADED` token must be defined once, reused.** T4/T5 both
  introduce `ESCALATION_DEGRADED`. Fold into **T3** acceptance: define the
  `ESCALATION_DEGRADED` state (route unavailable OR engram unavailable → fall back
  to existing operator-halt) once in the instruction contract; T4/T5 reference it
  rather than re-defining, preventing drift between the two agent templates.

## Scope / Policy Checks
- Single capability (011-DL(b) only); candidates (a)/(c)/(d) explicitly deferred. ✔
- Width isolation: schema (T1) / installer (T2) / instruction (T3) / agent-Stage
  (T4) / agent-Ship (T5) / policy (T6) / verify (T7) / tests (T8) / docs (T9) —
  no task crosses families. ✔
- 2h rule respected per task; T1's two-schema edit is one additive route object. ✔
- Global-tool/local-output boundary respected; runtime engine + telemetry
  emitter/store + external binaries routed OUT (external-guard). ✔
- P-006 hardening present and required (schema + multi-family blast radius). ✔
- P-017 dark-mode posture preserved (policy-preserving, authority-non-escalating). ✔
- Stage role boundary respected: no source/template mutation performed by staging;
  plan only. ✔

## Disposition
PASS — proceed to harvest. Two P2 advisories folded into T3/T6/T9 acceptance
criteria; no re-plan cycle required (1 review cycle, within the 3-cycle limit).

## Review-fix pass — Copilot PR #283 (2026-08-02, cycle 2)

Deterministic P-018 gate reported `UNRESOLVED_THREADS: BLOCK` with three
Copilot-authored threads on PR #283. All three verified **valid** against their
cited sources and corrected in-scope (planning/backlog only; no source/template
mutation). Verdict **remains PASS** after correction — the fixes tighten
acceptance criteria and the shipment manifest without altering the reviewed
executable scope (nine tasks, dependency order preserved).

- **C1 (valid) — Stage same-route escalation is a no-op.**
  `docs/plans/...-plan.md:48`. Stage role route (`config.yaml:65-68` =
  `claude-opus-4.8/anthropic/high`) already equals tier3 (`config.yaml:62`), so
  an unset `model_routing.escalation` resolves Stage to the identical model —
  no escalation to deeper reasoning. Fixed: Model reconciliation section now
  defines a same-route guard; `ESCALATION_DEGRADED` (T3) gains a same-route
  trigger; T7 detects a same-route resolution (fail-closed) and T8 pins the
  Stage-case negative test. New failure-mode + mitigation added to plan
  hardening.
- **C2 (valid) — shipment manifest listed the covering feature.**
  `.backlogit/queue/110-S.md:6`. Violated the durable 097-S task-only safe-close
  contract (`docs/compound/097-S-shipment-task-only-safe-close.md:25-40`). Fixed:
  removed `106-F` from `custom_fields.items` (now a nine-task manifest); covering
  feature is derived via task `parent_id`. Checkpoint `add_order` and the shipment
  log updated (correction event appended); plan "Add order" note rewritten to
  reflect the task-only manifest.
- **C3 (valid) — escalation contract placed in a two-agent-only instruction.**
  `docs/plans/...-plan.md:58`. `role-enforcement.instructions.md` installs only
  when both agents are present and is skipped for one-agent installs
  (`install-harness/SKILL.md:1032`), leaving a Stage-only/Ship-only install
  referencing an uninstalled contract. Fixed: T3 now targets a new
  `escalation-protocol.instructions.md.tmpl` installed whenever **either** agent
  exists; T2 adds the either-agent installer gating; T7 verifies the either-agent
  install (fail-closed) and T8 covers the one-agent negative case.

Cycle 2 of 3 (within limit). No P0/P1 introduced; original P2-1/P2-2 unchanged.
