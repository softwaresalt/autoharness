---
title: "Full-Preset Harness Sync Remediation — decided plan"
doc_type: decided-plan
status: reviewed
created: 2026-07-09
tasks: ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]
supersedes:
  - docs/archive/plans/2026-07-09-full-preset-sync-remediation-plan.md
---

# Decided Plan: Full-Preset Harness Sync Remediation

**Outcome:** Reviewed, not shipped. The source plan turns stash `4EEB1131` and spike `docs/spikes/2026-07-09-full-preset-sync-drift-detection.md` into a sequential, Ship-owned remediation program for full-preset drift. Dark factory mode is explicitly inactive, single-worktree `P-016` discipline remains in force, and the multi-family blast radius is handled through plan-hardening and plan-review before harvest.

## Decisions

1. Remediate only the concrete drift catalogued in the companion spike, using ten width-isolated tasks across prompts, foundation docs, instructions, agent mirrors, and manifest state.
2. Keep execution sequential rather than dark-factory: no `P-017` trigger was given, so the work stays in normal Ship flow.
3. Keep Stage inside the planning boundary; Ship owns every remediation edit, source/template/config change, and branch action.
4. Restore condensed installed artifacts to the template-mandated **behavioral contract**, not to full template bulk; `AGENTS.md` remains a short map.
5. Refresh `harness-manifest.yaml` only after the other nine tasks so checksums and artifact inventory reflect final file state.
6. Leave room for the constitution cross-reference fix to be either a condensed constitution install or a harness-architecture reference repair, depending on whether `AGENTS.md` already covers Principles III–V.

## Implementation (10 tasks)

- **T1** — install the agent-intercom `ping-loop.prompt.md` prompt.
- **T2** — restore capability-pack overlay weave in `.github/copilot-instructions.md` and the brief enabled-pack pointer in `AGENTS.md`.
- **T3** — fix graphtor-docs canonical `.mcp.json` registration precedence and fallback guidance.
- **T4** — install the GitHub PR automation base dependencies (`pull-request`, `ci-security`).
- **T5** — install the two-agent / circuit-breaker base dependencies (`role-enforcement`, `concurrency`).
- **T6** — resolve the constitution cross-reference by installing the condensed constitution or, if already redundant, fixing the harness-architecture reference instead.
- **T7** — sync `.stage.agent.md` behavioral guidance.
- **T8** — sync `.ship.agent.md` role-boundary, merge-gate, post-merge, and escalation/circuit-breaker behavior.
- **T9** — sync `_orchestrator.agent.md` merge-gate, elective-agent routing, and trigger guidance.
- **T10** — refresh `.autoharness/harness-manifest.yaml` with the final artifact set, checksums, version, and `tuned_at` value.

## Key constraints preserved

- Every task is evidence-backed, width-isolated, and limited to a small file set.
- `T10` depends on `T1`–`T9`; manifest repair is intentionally last.
- The installed agents remain condensed self-install variants; remediation restores behavior, not template bulk.
- `T8` is the highest-signal priority because it fixes the dark-mode / `P-009` gap in the installed Ship agent.
- Verification after remediation must confirm zero unresolved `{{VARIABLE}}`, resolved cross-references, coherent enabled-pack weave, intact `feature-flow-dark` behavior across Orchestrator + Ship + PR automation, and a manifest that matches the installed `.github` tree.

## Rejected alternatives

- **Let Stage perform the remediation** — rejected by the Stage role boundary; Stage plans only.
- **Restore every installed artifact verbatim from template bulk** — rejected in favor of the repository's condensed house style.
- **Refresh the manifest before syncing files** — rejected because the checksums would immediately drift.
- **Always add a new constitution document even if it would be redundant** — rejected; `T6` keeps a narrower reference-fix path available.

## Plan-review refinements folded in

- Scope discipline was retained: each task maps directly to a concrete drift finding, with no busywork.
- Width isolation across prompts, foundation docs, instructions, agents, and manifest work stayed intact.
- `T8` was explicitly called out as the highest-signal behavioral gap to prioritize.
- `T6` remained flexible so remediation can fix the cross-reference without creating redundant documentation.
- No plan step removes a shipped policy or behavior without a replacement landing in the same remediation sequence.