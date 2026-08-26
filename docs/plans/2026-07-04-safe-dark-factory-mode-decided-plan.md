---
title: "Safe Dark Factory Mode — decided plan"
doc_type: decided-plan
status: reviewed
created: 2026-07-04
feature: "061-F"
shipment: "064-S"
tasks: ["061.001-T", "061.002-T", "061.003-T", "061.004-T", "061.005-T", "061.006-T", "061.007-T"]
supersedes:
  - docs/archive/plans/2026-07-04-safe-dark-factory-mode-plan.md
---

# Decided Plan: Safe Dark Factory Mode

**Outcome:** Reviewed, not shipped. Stage produced an execution-ready plan for feature `061-F` / shipment `064-S` that groups the two high-priority dark-factory stashes and sequences implementation behind a contract-first opening shipment (`061.001-T`). No implementation, build, test, lint, branch, worktree, or PR action occurred in the source session.

## Decisions

1. Define the dark-factory autonomy contract before any trigger, merge, or fallback behavior is implemented.
2. Activate dark mode only through the exact trigger `Run pipeline in dark mode` or the explicit alias `Run pipeline in dark factory mode`; ambiguous autonomy language must not enable it.
3. Keep `P-001`, `P-014`, `P-016`, `P-009`, and `P-005` non-negotiable inside dark mode.
4. Make local review readiness for the current HEAD the authoritative merge gate; hosted Copilot/GitHub review stays advisory by default unless explicitly elevated.
5. Model branch-protection and admin fallback as explicit, fail-closed states: normal merge first, fallback only when pre-authorized and unambiguous.
6. Weave operator visibility and safety telemetry across Orchestrator, Ship, PR lifecycle, and closure.
7. Put brainstorm-led requirements capture in front of `impl-plan`, `plan-review`, and `harvest` so dark-mode handoff begins from a stable requirements artifact.

## Implementation (7 tasks)

- **061.001-T** — define the autonomy policy contract.
- **061.002-T** — design the brainstorm-led research intake and its handoff artifact.
- **061.003-T** — implement Orchestrator trigger semantics and `DARK_MODE_ACTIVE` state recording.
- **061.004-T** — define local-review-first dark-mode readiness.
- **061.005-T** — implement merge approval and admin fallback semantics.
- **061.006-T** — add dark-mode safety telemetry and remote-operator visibility.
- **061.007-T** — update docs and verification surfaces after the behavior is woven together.

Dependency order matters: `061.001-T` blocks all downstream work; `061.005-T` depends on both the contract and the readiness workflow; `061.006-T` depends on contract + trigger + merge behavior; `061.007-T` closes after the rest.

## Key constraints preserved

- The first shipment is intentionally `064-S` with **only** `061.001-T`; later shipments stay queued until the contract exists.
- The parent feature `061-F` stays out of the shipment manifest to avoid partial-feature closure cascade risk.
- Dark mode remains bounded to one release unit at a time and cannot expand scope silently.
- Any implementation slice must verify frontmatter, markdown hierarchy, unresolved-variable scans, cross-references, dark-mode non-bypass of `P-014` / `P-016` / `P-009`, admin-fallback state handling, and local review readiness evidence on produced PRs.
- The unrelated CI build-minute optimization stash `8DBD43A1` remains separate.

## Rejected alternatives

- **Trigger-first autonomy without a policy contract** — rejected because it would leave merge authority, topology safety, and review gates undefined.
- **Ambiguous autonomy language as activation** — rejected; only the canonical trigger and explicit alias may enable dark mode.
- **Hosted review as the default authoritative merge gate** — rejected in favor of local-review-first readiness.
- **Silent or loosely-defined admin bypass** — rejected; fallback must be explicit, pre-authorized, and fail closed.
- **Bundling unrelated CI optimization work into dark-factory mode** — rejected; stash `8DBD43A1` stays out of scope.

## Plan-review refinements folded in

- The two high-priority dark-factory stashes stay grouped because the trigger is unsafe without the accompanying brainstorm, review, merge/fallback, and visibility design.
- Each child task remains single-domain and roughly two hours of human work.
- The first shipment stays limited to the policy/contract slice so later behavior never outruns the governance.