---
title: Full-Preset Harness Sync — Remediation Plan
doc_type: plan
date: 2026-07-09
stash_id: 4EEB1131
kind: chore
status: reviewed
owner: Stage
spike: docs/spikes/2026-07-09-full-preset-sync-drift-detection.md
---

# Full-Preset Harness Sync — Remediation Plan

Remediation plan for the drift catalogued in the companion spike. This plan is
produced by Stage (planning only). **Ship** owns all edits below — Stage must not
perform remediation, edit source/templates/config, or touch branches.

Mode: **sequential (NOT dark factory)** — no P-017 trigger given. Single worktree
(P-016). Blast radius touches multiple artifact families (agents, instructions,
prompts, foundation docs, manifest) → plan-harden applied; gated through
plan-review before harvest.

## Task decomposition (2-hour rule, width-isolated, ≤3 files each)

| Task | Concern | Files | Remediates |
|---|---|---|---|
| T1 | Install agent-intercom `ping-loop.prompt.md` from template | `.github/prompts/ping-loop.prompt.md` | D7 |
| T2 | Restore capability-pack overlay weave in foundation docs (intercom/backlogit/graphtor blocks in copilot-instructions; brief enabled-pack pointer in AGENTS.md — keep it a map) | `.github/copilot-instructions.md`, `AGENTS.md` | D5, D6 |
| T3 | Fix graphtor-docs `.mcp.json` canonical registration precedence + fallback rule | `.github/instructions/graphtor-docs.instructions.md` | D8 |
| T4 | Install github-pr-automation base deps (`pull-request`, `ci-security`) from templates | `.github/instructions/pull-request.instructions.md`, `ci-security.instructions.md` | D10 |
| T5 | Install two-agent / circuit-breaker base deps (`role-enforcement`, `concurrency`) from templates | `.github/instructions/role-enforcement.instructions.md`, `concurrency.instructions.md` | D10 |
| T6 | Resolve constitution cross-reference (install condensed `constitution.instructions.md` from template; if AGENTS.md already fully covers Principles III–V, instead fix the harness-architecture reference) | `.github/instructions/constitution.instructions.md` | D9 |
| T7 | Sync `.stage.agent.md` — Step Sequence Contract, Contextual Grouping + Learnings Retrieval, P-006 Gate Bypass Guard, shipment handoff safety | `.github/agents/.stage.agent.md` | D4 |
| T8 | Sync `.ship.agent.md` — Role Boundary + P-010 self-check, merge-commit-only/P-009 dark gate, Post-Merge Branch Protocol, circuit breakers/escalation | `.github/agents/.ship.agent.md` | D2 |
| T9 | Sync `_orchestrator.agent.md` — Staging Artifact Merge Gate, Elective Agents/install-tune routing (E1), trigger surface | `.github/agents/_orchestrator.agent.md` | D3 |
| T10 | Refresh `harness-manifest.yaml` — record all unrecorded + newly installed artifacts with checksums, bump version, refresh `tuned_at` | `.autoharness/harness-manifest.yaml` | D1 |

**T10 depends on T1–T9** (manifest checksums must reflect final file state).

## Harvest / condensation rule for Ship

Installed agents are intentionally condensed self-install variants. Ship must
restore only the **behavioral contract** the template mandates (gates, tables,
protocols, weave hooks) — not verbatim template bulk. Match the existing
condensed house style. AGENTS.md stays a short map (harness-architecture rule);
add a pointer, not full overlay sections.

## Plan-review notes (gate before harvest)

- **Scope discipline:** every task maps to a concrete evidence-backed finding; no
  busywork. Areas with only intentional condensation/omission produced no tasks.
- **Width isolation:** agent edits, instruction installs, foundation-doc weave,
  prompt install, and manifest refresh are separated. No task mixes families.
- **P-010 safety:** Ship performs edits; Stage stays in planning boundary.
- **Dark-mode gap (D2 / P-009)** is the highest-signal item — a genuine shipped
  behavior missing from the installed Ship agent. Prioritize T8.
- **T6 latitude:** default is to install the condensed constitution; the fallback
  (fix the cross-ref) is explicitly allowed so Ship does not create a redundant
  doc if AGENTS.md already carries Principles III–V. Not unsafe either way.
- **No deferrals:** nothing removes a shipped policy without replacement.

## Verification expectations handed to Ship

After remediation, verify-harness / tune-harness should confirm: zero unresolved
`{{VARIABLE}}`; all cross-references resolve (constitution, pull-request,
ci-security, concurrency, role-enforcement, ping-loop now present); each enabled
pack woven per its overlay contract; feature-flow-dark complete across
Orchestrator + Ship (P-009 gate) + PR automation; manifest `artifacts[]` matches
the installed `.github` tree.
