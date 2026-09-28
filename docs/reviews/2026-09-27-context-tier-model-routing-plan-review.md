---
title: "Review record: context_tier routing, generic Ship default, durable dogfood Ship pin plan"
description: "Review record for docs/plans/2026-09-27-context-tier-model-routing-plan.md (stash 6EC29DD6). The five plan-2 downstream adjustments were applied, Hardening Pass 2 (H-C1 to H-C9) was added, and the plan went through three review-fix cycles and a bounded fix-verification pass confined to the cycle-3 fixes. The result is PASS with 0 open P0 and 0 open P1 under severity rule C4."
doc_type: review
status: complete
created: 2026-09-27
subject:
  plan_path: docs/plans/2026-09-27-context-tier-model-routing-plan.md
  base_commit: deb0564b
  reviewed_blob: d3d199382a7210d58beb14fc807fa92412eb4262
  note: "The plan is uncommitted. reviewed_blob is the plan content as reviewed, before the Plan Review pointer section and the status change were appended."
decision: PASS
dispatch_mode: single-agent-declared-degradation
severity_rule: C4
source_stash: 6EC29DD6
source_deliberation: docs/decisions/2026-09-27-close-evidence-frontmatter-context-tier-staging-deliberation.md
depends_on_plan: docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md
recorded_by: Stage
---

# Review Record: context_tier Routing and Durable Ship Pin Plan

## Verdict

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* **Decision: PASS.** All selected personas return PASS after cycle 3 and the
  bounded fix-verification pass.
* **Open blocking findings: 0 P0, 0 P1.** Under severity rule C4, only P0, P1, and
  matrix-critical P2 findings block harvest. No matrix-critical P2 is open.
* **Plan hardening was required** (the plan declares four signals), and it is
  satisfied. The original record is kept, and Hardening Pass 2 was added:
  * H-C1 to H-C9;
  * the downstream-adjustment table DA-1 to DA-5;
  * INV-C7 to INV-C9;
  * a corrected rollback.
* **The binding operator ruling holds** (INV-C1):
  * this repository's Ship route stays `claude-opus-5.5` / `anthropic` / `high`,
    with `context_tier: default`;
  * the pin is mechanical: role-variable binding (C4a), config-authoritative route
    precedence (C4b), the whole-route seed trigger that cannot fire here (C3b), the
    tune exemption (C8), and the C7 regression test;
  * the generic fresh-install Ship default is `openai` / `gpt-6-luna` / `xhigh` /
    `long_context`. It lives in the install-harness skill only, and no `.tmpl`
    hardcodes it.
* **Harvest is permitted** once shipment B (plan 2) is harvested ahead of it,
  through the `blocks` edge, and once the operator confirms the Stage-recommended
  decisions below. None of them blocks safe execution.
* Harvest, shipment assembly, and commit are out of scope for this invocation.

## Capability Declaration (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
  This Stage runtime has no reviewer subagent tool. Stage applied the inline
  personas itself, each with its own finding list.
* The cross-model personas (Architecture Strategist and Agent-Native Parity) ran as
  independent, read-only external passes:
  * they used the Copilot CLI on the anchor route `gpt-6-sol`
    (`--reasoning-effort high`), with `--deny-tool write --deny-tool shell`, so
    they could only view and search;
  * the reviewer model differs from Stage's `claude-opus-5.5`;
  * this follows the precedent in the two sibling 2026-09-27 plan reviews.
* **Security Lens Reviewer was not triggered:** the plan has no auth, secrets,
  sensitive store, API, or external-integration surface.
* Intercom, Engram, and graphtor were not probed in this bounded invocation.
  Knowledge came from `docs/compound/`, the plan's cited sources, and read-only
  inspection of the code.

## Persona Coverage

| Persona | Mode | Model | Raised | Final |
|---|---|---|---|---|
| Constitution Reviewer | inline pass | claude-opus-5.5 | 1 P2 | PASS |
| Python Reviewer | inline pass | claude-opus-5.5 | 1 P3 | PASS |
| Scope Boundary Auditor | inline pass | claude-opus-5.5 | 1 P3 | PASS |
| Learnings Researcher | inline pass | claude-opus-5.5 | 0 | PASS |
| Architecture Strategist | anchor external pass (cycles 1-3 + fix verification) | gpt-6-sol | 1 P0, 7 P1, 2 P2 | PASS (fix verification) |
| Agent-Native Parity Reviewer | anchor external pass (cycles 1-3 + fix verification) | gpt-6-sol | 5 P1, 6 P2 (AN-F6 raised P2, re-raised P1) | PASS (fix verification) |

## Downstream Adjustments Applied (from the plan-2 review)

Each adjustment was verified against the text of plan 2 (units B1, B2b, B3, and B7,
and its `## Plan Review` downstream list) before it was applied.

| # | Adjustment | Applied in |
|---|---|---|
| DA-1 | `context_tier` goes into `ROUTE_VALUE_KEYS` only, not `AGENT_OPTIONAL`. It is optional on tier-routed agents and forbidden on plugin-global agents and skills, and its validator goes through `VALIDATORS` | C5a |
| DA-2 | `adr-generator.agent.md.tmpl` is added with `{{TIER_2_CONTEXT_TIER}}`. The test covers tier-routed agents only | C5b |
| DA-3 | No `context_tier` on `auto-tune` / `auto-mergeinstall` | C5b, C5c (INV-C8) |
| DA-4 | Rendered-candidate validation in installed mode, as in B2b | C4a, C5b |
| DA-5 | C6 and B7 edit disjoint policy sections, so they need only a rebase. The wording excludes plugin agents | C6a, C6b |

## Findings and Dispositions

Severity reflects the finding as raised. Duplicates are cross-referenced and
counted once.

| ID | Sev | Cycle | Unit | Finding | Disposition |
|---|---|---|---|---|---|
| AS-F1 | P0 | 1 | Rollback | Reverting C4 would restore `{{TIER_2_*}}` and break the Ship pin on re-install | Fixed: the binding is never reverted alone; fix forward; C7 must stay green |
| AS-F2 / AN-F2 | P1 | 1 | C3 | The seed ran after Step 3.3 had already created the manifest, and after derivation | Fixed (C3b): first-install snapshot before Step 1.2; seed applied in Step 1.2 |
| AS-F3 | P1 | 1 | C3 | The whole-route-empty trigger also matched an explicit empty operator Ship block | Fixed (C3b): trigger is "no `ship` key"; an explicit empty block is honored |
| AS-F4 / AN-F4 | P1 | 1 | C3, C8 | The install-harness and tune-harness manifest checksums were not refreshed | Fixed: refresh plus an `unchanged` assertion |
| AS-F5 / AN-F5 | P2 | 1 | C7 | `role_route_resolution` emits only `ok` / `errors` | Fixed: assert `ok` plus the derived `SHIP_FAMILY` |
| AN-F1 | P1 | 1 | C2, C6 | The resolved escalation `context_tier` had no consumer in the handoff | Fixed (new C6b): a separate `resolved_escalation_context_tier`; the 3-field tuple is unchanged |
| AN-F3 / AS-F6 | P1 | 1-2 | C4 | Manifest `variables_used` beats config, so stale route variables are rendered | Fixed (C4b): route family is config-authoritative, plus the `ROUTE_VARIABLE_STALE` warning; the rendered value is tested |
| AN-F6 / AS-F7 | P2→P1 | 1-2 | C6a | The Ship-site check ran to EOF, so the P-013.5 summary could satisfy it | Fixed: the Ship window is bounded at the next heading; regression test keeps the summary |
| AN-F7 | P2 | 1 | C5 | C5 mixed the contract, templates, and render gate | Fixed: split into C5a, C5b, and C5c |
| AS-F8 | P2 | 2 | C3a | Write-back materializes the resolved `context_tier` | Fixed: documented as the existing one-time pattern, with a round-trip test; escalation stays raw |
| AN-F8 | P2 | 2 | C5b | Tier parity did not cover `ORCHESTRATOR_*`, and the placeholder rule was too broad | Fixed: route-prefix parity; frontmatter-only installed-mode check |
| AN-F9 | P2 | 2 | C6b | The per-role escalation overlay was untested | Fixed: nested Stage/Ship fixture with distinct tiers |
| AN-F10 | P2 | 2 | C3, C4 | Units were over-sized | Fixed: split into C3a/C3b and C4a/C4b |
| AS-F9 | P1 | 3 | C3b, C4b | `config.overrides` `SHIP_*` was ignored by the seed and by the precedence | Fixed: overrides suppress the seed and take top precedence; tested |
| AS-F10 | P1 | 3 | C4b | A manifest-only install would replace recorded routes with generic defaults | Fixed: config-authoritative only when an authoritative config is loaded; tested |
| AN-F11 | P1 | 3 | Rollback | An independent C4b revert would reintroduce stale renders | Fixed: C4b is fixed forward, never reverted alone |
| CR-F1 | P2 | inline | C3 | The Core Rule 3 proxy only checked for the `gpt-6-luna` literal | Fixed: every `context_tier:` line in a `.tmpl` must be a placeholder |
| PY-F1 | P3 | inline | C2 | `resolved_context_tier` could diverge from the derivation | Fixed: the check and the render share one helper |
| SB-F1 | P3 | inline | — | Pre-existing mirror staleness: tier-1 subagents record `gpt-5.6-luna`, but config has `gpt-6-luna` | Accepted residual. Out of scope and recorded in the plan as a stash candidate. C5c does not re-resolve `model_*` |

### Counts

| Severity | Found (unique) | Open |
|---|---|---|
| P0 | 1 | 0 |
| P1 | 9 | 0 |
| P2 | 7 | 0 |
| P3 | 2 | 1 (SB-F1, accepted residual, out of scope) |

## Cycle Log

* **Cycle 1:**
  * Architecture Strategist: FAIL, with 1 P0, 3 P1, and 1 P2;
  * Agent-Native Parity: FAIL, with 4 P1 and 3 P2;
  * all findings were fixed.
* **Cycle 2:**
  * both personas: FAIL;
  * 7 of the 9 cycle-1 findings were verified fixed;
  * AN-F3 / AN-F6 were not fixed, and were re-raised as AS-F6 / AS-F7;
  * new findings: AS-F8, AN-F8, AN-F9, and AN-F10;
  * all were fixed.
* **Cycle 3:**
  * all cycle-1/2 items were verified fixed;
  * new findings: AS-F9, AS-F10 (P1), and AN-F11 (P1);
  * all were fixed. The 3-cycle limit was not used to defer any in-scope P1.
* **Bounded fix-verification pass** (gpt-6-sol, both lenses, confined to AS-F9,
  AS-F10, and AN-F11): all three FIXED, no new P0/P1, VERDICT PASS.

## Stage-Recommended Decisions (pending operator confirmation)

* **D-C1 to D-C5 and D-C7**, from the deliberation. D-C6 is binding.
* **H-C2:** a nested `<role>.escalation` block that declares only `context_tier`
  changes only the escalation `context_tier`. It never selects the nested source,
  and never triggers the H2 ambiguity.
* **H-C3 / AS-F3 / AS-F9:** the fresh-install seed fires only when all of these
  hold:
  * it is a first install;
  * there is no `model_routing.ship` key;
  * there is no `SHIP_*` override.
  An explicit empty Ship block, and any `SHIP_*` override, are honored instead.
* **H-C4:** because the write-back materializes the resolved Ship family, tune's
  new-default proposal is normally inert for existing workspaces. Adopting the new
  default is a manual config edit.
* **H-C5:** `""` is legal in config only, meaning unset or inherit. It is rejected
  in rendered frontmatter.
* **C4b:** route-family variables are config-authoritative in verify's staged
  render, subject to override precedence and an authoritative-config gate. This is
  a small behavior change for workspaces whose manifest records stale route
  variables.
* **C6b:** the escalation payload gains a separate `resolved_escalation_context_tier`
  field.
* **This repository's Ship `context_tier` is `default`**, per the operator
  instruction, unless the operator says otherwise.

## Harvest Notes

* Linear harvest order: C1, C2, C3a, C3b, C4a, C4b, C5a, C5b, C5c, C6a, C6b, C7, C8.
  Each unit declares its size and complexity.
* The whole shipment is blocked by shipment B (plan 2).
* Carry the out-of-scope SB-F1 observation to the operator as a stash candidate.
