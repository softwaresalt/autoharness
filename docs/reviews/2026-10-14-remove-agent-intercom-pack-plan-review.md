---
title: "Plan review: remove the agent-intercom capability pack"
description: "Multi-persona plan review of docs/plans/2026-10-14-remove-agent-intercom-pack-plan.md, run as a single-agent declared-degradation pass. Cycle 1 produced one P1 (constitution amendment protocol) and four P2 findings that were fixed in the plan; cycle 2 verified PASS."
doc_type: review
review_target: docs/plans/2026-10-14-remove-agent-intercom-pack-plan.md
dispatch_mode: single-agent-declared-degradation
decision: PASS
review_cycles: 2
reviewed_utc: 2026-10-14
---

# Plan review: remove the agent-intercom capability pack

Review gate for `docs/plans/2026-10-14-remove-agent-intercom-pack-plan.md` (stash `0FD06900`,
feature `209-F`, shipment `216-S`). Dates are UTC. The authoritative, machine-readable copy of this
review is the `## Plan Review` section appended to the plan; this file is the standalone record.

dispatch_mode: single-agent-declared-degradation

decision: PASS

## Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch` - this Stage session exposes no reviewer subagent
  dispatch surface. Declared fallback: single-agent persona pass; every persona below was applied
  inline against its rubric with one finding list per persona.
* `TOOL_DEGRADED: model-specific-review-routing` - `model_routing.anchor_review` is not dispatchable
  here. Declared fallback: same-model rubric pass for the cross-model personas. No persona skipped.

## Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Constitution Reviewer | inline (always-on) | F1 P1 resolved |
| Python Reviewer | inline (always-on) | F2 P2 resolved, F3 P3, F4 P2 resolved |
| Scope Boundary Auditor | inline (always-on) | F5 P3, F6 P3 (re-triaged from P2) |
| Learnings Researcher | inline (always-on) | F12 P3 |
| Architecture Strategist | inline, same-model | F7 P3 (re-triaged from P2), F8 P3 |
| Agent-Native Parity Reviewer | inline (triggered) | F9 P2 resolved |
| Security Lens Reviewer | inline (triggered) | F10 P3 |
| Schema-CLI-Docs Coupling Reviewer | inline (extra, repo-specific) | F11 P2 resolved |

## Cycle history

* **Cycle 1: FAIL** - one P1: F1, the constitution's Governance section requires a version bump,
  rationale and sync-impact report for any amendment, and the draft removed the `agent-intercom`
  Capability Overlays bullet without them. Plan revised (U10 now bumps the constitution to 1.1.0
  in template and mirror and adds a dated sync-impact report).
* **Cycle 2: PASS** - all revised sections re-verified; no open P0/P1.

## Findings

| ID | Sev | Persona | Finding | Disposition |
|---|---|---|---|---|
| F1 | P1 | Constitution | Amendment protocol missing for removing a constitutional overlay bullet | Resolved in U10 |
| F2 | P2 | Python | Legacy-pack error matcher misses `recommendation_reasons...item` and the `agent_intercom` additional-properties error | Resolved in U6 |
| F3 | P3 | Python | Type `REMOVED_CAPABILITY_PACKS` as an immutable mapping | Advisory |
| F4 | P2 | Python | Guard-test scan must be encoding/CRLF-robust | Resolved in U1 |
| F5 | P3 | Scope | 23 tasks is large for a removal but each is family-scoped | Advisory |
| F6 | P3 | Scope | U21 wrapper tolerance goes slightly beyond pure deletion | Advisory; re-triaged from P2 - required by R5, not scope growth; separable |
| F7 | P3 | Architecture | `verify_workspace.py` edited by three sequential tasks | Advisory; re-triaged from P2 - linear chain keeps each step green, no concurrent-edit risk |
| F8 | P3 | Architecture | `215-S blocks` edge puts this shipment at the chain tail | Advisory; reasons in D-11 |
| F9 | P2 | Agent-Native | Operator clarification/wait behavior undefined after transmit/standby removal | Resolved in D-4 |
| F10 | P3 | Security | Do not imply destructive approval can be skipped without a remote channel | Advisory; checked in U10/U12 |
| F11 | P2 | Schema-CLI-Docs | Cross-check pack registration touchpoints | Resolved; all 10 covered |
| F12 | P3 | Learnings | Reuses the schema-mirror versioning and LF-blob checksum procedures | Advisory |

## Gate decision

**PASS.** No open P0/P1 and no open or accepted P2 findings: every P2 is resolved in the plan, and
F6/F7 were re-triaged to P3 advisory after a hosted review of the staging PR (PR 518) showed the
earlier "P2 accepted" label conflicted with the plan-review gate table (an accepted P2 would
require `decision: ADVISORY` plus recorded authorization). Re-triage basis: F6 is traceable to
requirement R5 (existing automation passing `-Packs agent-intercom` must not hard-fail), so U21 is
requirement-driven rather than scope growth; F7 is an ordering observation whose risk is already
removed by the linear task chain. Plan hardening was required (`Requires plan hardening: yes`) and is
satisfied by the plan's `## Plan Hardening` section. The plan is harvest-ready; harvest produced
`209-F` with 23 tasks (`209.001-T` to `209.023-T`) in shipment `216-S`.

## Hosted review of the staging PR (PR 518)

Round 1 (3 findings, all resolved): the profile schema root is open so the legacy block is detected
directly (U2/U6); F6/F7 re-triaged to P3 (above); the stage checkpoint now truthfully records
publication via the PR. Round 2 (3 findings, resolved): U2-U4 now retarget the current-version
proposals (`backfill-*`/`review-unknown-*` rules and their action text) to the new current
contract with payload tests (new F13, P2, resolved in U2-U4); U18 and task 209.018-T now also pin the
workspace-discovery generated-profile `schema_version` to `1.1.0` with a generated-profile
validation test (new F14, P2, resolved in U18); the PR readiness record was refreshed for the
current HEAD. These are plan refinements, not verdict changes: no open P0/P1 or P2 remains.
Round 3 and the round-2 body finding added four more plan refinements, all resolved: the D-14
checksum procedure now reads the INDEX blob (`git add --renormalize` then `:<path>`) for files edited
in the task and reserves `HEAD:<path>` for unchanged baselines; U17 and task 209.017-T pin the
install-harness Step 3.3 manifest skeleton to manifest `1.1.0` with a render-and-validate test; D-9
and U1 (task 209.001-T) no longer blanket-exclude `tests/**` and allowlist only the exact test
files that intentionally name the retired value; U21 and task 209.021-T make all four deploy
wrapper/template copies scaffold the config at U4's new current version with a generated-config
validation test. Round 4 added: U1/209.001-T classify tests per exact path (no `tests/` allowlist,
downstream units add or move their own tombstone entries); U9/209.009-T scope strict-safety to its
template only (9 files, 4 mirror checksums; no installed strict-safety mirror exists); U10/209.010-T
exempt the new sync-impact report from the zero-reference criterion; the plan's config-ownership row
says U8 changes only the pack entry, never the config `schema_version` (D-10). Round 5 added: U8/209.008-T
also refresh the manifest `profile_hash` and the profile artifact checksum, because the dogfood
profile is edited in that task.
