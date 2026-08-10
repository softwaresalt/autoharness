---
title: "Plan Review — Local Copilot CLI Supervisor / Control Plane (Plan 1, FAST-TRACK)"
date: "2026-08-09"
description: "Adversarial plan review of the Plan 1 local Copilot CLI supervisor/control-plane plan and its P-006 hardening, gating harvest."
doc_type: review
source: docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md
review_id: "PLAN-1-R"
verdict: "PASS"
stash_ids: ["34D50F2D"]
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md"
  - "docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md"
  - ".backlogit/archive/004-SP.md"
  - "docs/decisions/2026-08-09-composability-single-source-of-truth-spike.md"
tags: ["plan-review", "34D50F2D", "candidate-a", "supervisor", "P-006"]
---

# Plan Review (PLAN-1-R)

## Verdict: PASS — 0 unresolved P0, 0 unresolved P1

Review cycles used: **1 of 3**. All findings resolved in-cycle by amending the
plan and hardening documents before harvest.

## Scope reviewed

The Plan 1 implementation plan and its P-006 hardening, against: the operator's
authoritative product decision, the `004-SP` spike evidence, the preserved
product boundaries (Copilot CLI as reasoning engine; Engram read-only;
backlogit authoritative for backlog/checkpoints; graphtor for docs;
`.autoharness/config.yaml` as routing authority), the candidate (c) boundary,
the Stage role boundary (P-010), and the 2-hour task rule.

## Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| **F1** | **P0** | The spike's recorded verdict was CONDITIONAL PROCEED with an explicit **NO-GO** for "process supervision"-adjacent scope, because the only reading available was spec §3 as an in-process action/observation executor. Harvesting a supervisor plan against an un-reconciled NO-GO would leave PR #325 contradicting the shipped backlog. | **RESOLVED** — Plan §2 reconciles the disposition to evidence-backed **PROCEED** under the clarified scope, drawing the bright line *supervising an external engine is in scope; implementing a new agent runtime is not*. The literal-§3 NO-GO is preserved verbatim as a still-standing non-goal. The same reconciliation is appended (append-only) to `004-SP`, the decision doc, the session memory, and the completion checkpoint. |
| **F2** | **P0** | Nothing structurally prevented "control plane" from acquiring a network listener, which would silently pull deferred Plan 2 scope (remote UI/auth/approvals/tunnel) into Plan 1. | **RESOLVED** — H7.2 adds a test-level invariant: no `bind`/`listen` in `supervise/`, and an import ban on `gradio`/`fastapi`/`flask`/`uvicorn`/`aiohttp`/devtunnel clients. Plan §3.6 constrains approvals to console/TTY only. Plan §11.1 states the exclusion. Enforced in Shipment 1, before any supervision code exists. |
| **F3** | **P1** | `start.ps1`'s semantics are subtle (no-clobber `.env.local` precedence, single-pair quote stripping, `--remote` double-add guard, non-fatal sidecars). A "port then test" ordering would have baked in drift. | **RESOLVED** — H1 makes characterize-before-migrate a hard ordering constraint enforced by `blocks` edges (S1 → S2 → S3), and T18's acceptance criterion requires the T1/T2 suites to be re-run **byte-identical**. Changing a characterization assertion is escalated to an operator product decision. |
| **F4** | **P1** | The session journal (checkpoints + resume cursor) risked becoming a second checkpoint/backlog authority competing with backlogit. | **RESOLVED** — H6.1 and Plan §3.7 declare the journal gitignored local operational state, explicitly not readable by any agent-recovery protocol and not a checkpoint. backlogit remains sole authority. |
| **F5** | **P1** | The typed event bus is exactly the hook candidate (c) needs; incremental "just one subscriber" additions would silently implement candidate (c) and could drift Engram toward authority. | **RESOLVED** — H7.1 permits only the journal and console renderer as subscribers; no background verification/summarization/compaction thread. H6.2 forbids any supervisor decision from reading Engram. Plan §8 and §11.6 restate it. `34D50F2D` stays ACTIVE as candidate (c)'s tracker. |
| **F6** | **P1** | Exit-code masking is a *known, already-realized* defect class in this repository's shell scripts (compound learning, trailing `|| true`). A new shim layer reintroduces the exact surface. | **RESOLVED** — H3 makes verbatim exit-status propagation a hard invariant with a dedicated round-trip test over `{0,1,2,42,130}` across both process backends and both shims, and explicitly prohibits `|| true` / `-ErrorAction SilentlyContinue` around the child launch. |
| **F7** | **P1** | Three tasks carry `complexity: high`; without de-risking controls they would likely exceed the 2-hour box. | **RESOLVED** — H8 assigns a specific control to each: T7 is off the default path with a documented pipe-only degradation escape; T11's restart budget defaults to 0 so the complex path is opt-in; T15 is pure composition over already-tested dependencies and *must be split* if it grows an algorithm. T18 is gated by T1/T2 plus an escape hatch. |
| **F8** | **P2** | "Control plane" invites daemon/database/framework overreach (scheduler, SQLite session store, asyncio rewrite, TUI library). | **RESOLVED** — Plan §6 lists these as explicitly rejected; §11.4 makes daemon/scheduler/database/web-framework/plugin-registry non-goals; §7 confines any Go re-evaluation to a hypothetical future persistent multi-workspace daemon with no work item now. |
| **F9** | **P2** | Secret redaction implemented per-writer would eventually be forgotten by one writer. | **RESOLVED** — H5 makes redaction a single choke point with no raw-write API, registers resolved secret *values* (not just regex patterns), and adds a ≥8-character no-substring-survival property test. |
| **F10** | **P2** | Sidecar degradation (e.g. Engram unavailable) could be mapped onto the supervisor call's own `status`, repeating a documented telemetry defect. | **RESOLVED** — Plan §8 cites compound learning `2026-08-08-state-vs-call-outcome-conflation-in-telemetry-mapping` and requires a sidecar's reported state to stay a per-sidecar typed outcome, never the supervisor's `status`. Telemetry, if emitted, is emitted by the service with `tool_surface` supplied by the adapter. |
| **F11** | **P2** | Templates under `templates/` carry copies of the start scripts; migrating only the repository-root scripts would leave generated workspaces with orphaned inline policy. | **RESOLVED** — T18 scope explicitly includes the `templates/` copies; H9.5 states the guarantee. |
| **F12** | **P2** | A native autoharness MCP server could be re-argued as "the control-plane API". | **RESOLVED** — Plan §11.3 keeps it an explicit non-goal absent a concrete consumer; §2 preserves the three distinct MCP vocabularies (server-framework absence vs. registry-validation vs. telemetry) so the absence claim stays precisely scoped and is not overstated. |

## Decomposition check (2-hour rule, width isolation)

* **19 tasks**, each scoped to a single module or a single script surface.
* **No task mixes** template work with CLI work with schema work. T18 is the only
  cross-surface task and it is deliberately a *mechanical* deletion-plus-delegation
  with a pre-existing test gate.
* **No schema changes** anywhere in the plan — `schemas/` is untouched.
* Every task is independently testable; the fake-`ChildProcess` seam removes the
  Copilot dependency from all but one opt-in smoke test.
* Sizes and complexities are assigned on two independent axes; every
  `complexity: high` task has an H8 control.

## Priority assignment

* **P0** — Shipment 1 (T1–T5) and Shipment 2 (T6–T11): process safety,
  contracts, characterization, containment. These are the correctness and
  security substrate.
* **P1** — Shipment 3 (T12–T19): application services, the CLI adapter, the local
  approval path, migration, and documentation. Convenience and UX ride at the
  back, per the operator's fast-track ordering directive.
* No P2-only tasks were harvested.

## Boundary confirmations (explicitly re-verified)

1. Copilot CLI remains the external reasoning/tool-execution runtime; autoharness
   implements **no** action/observation loop. ✅
2. Engram is read-only, non-authoritative, and no supervisor decision depends on
   it. ✅
3. backlogit owns backlog and checkpoints; the session journal is not a
   checkpoint. ✅
4. graphtor owns docs retrieval; untouched. ✅
5. `.autoharness/config.yaml` remains model-routing authority; no model names
   hardcoded; the supervisor does not read model routing at all. ✅
6. Candidate (c) is not implemented; only hook surfaces are exposed. ✅
7. Native autoharness MCP server remains an explicit non-goal. ✅
8. Gradio / devtunnel / remote UI / remote auth / remote approvals / browser
   terminal streaming / remote services are wholly absent and deferred to
   Plan 2. ✅
9. Python-first with a replaceable `ChildProcess` Protocol; no Python+Go split. ✅

## Gate outcome

`PASS`. Harvest authorized for Plan 1 only. Plan 2 is design/tracker-only and
must not be harvested into implementation work.
