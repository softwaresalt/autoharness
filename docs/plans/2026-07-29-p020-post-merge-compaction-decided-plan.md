---
title: P-020 Post-Merge Context Compaction — decided plan
doc_type: decided-plan
status: shipped
created: 2026-07-29
feature: 098-F
shipment: 103-S
supersedes: docs/archive/plans/2026-07-29-p020-post-merge-compaction-plan.md
---

# Decided Plan: P-020 Post-Merge Context Compaction

**Outcome:** Shipped as feature `098-F` / shipment `103-S` (PR #259, merge commit
`1c72dbf`). Plan-review verdict: READY, P0 = 0, P1 = 0. This decided-plan replaces
the verbose original (full deliberation, plan-harden, five-persona review), which is
archived for traceability at
`docs/archive/plans/2026-07-29-p020-post-merge-compaction-plan.md`.

## Decision

Formalize mandatory post-merge context compaction as first-class policy **P-020**.
Decouple mandatory **invocation** (guaranteed at Ship Step 6 post-merge closure =
per-merge) from threshold-based **candidate selection** (skill-internal, unchanged).
The enforcement mechanism is the environment-agnostic **compact-context skill** —
never a literal `/compact` command (Copilot-CLI-specific; forbidden by the
environment-agnostic core rule). Mandating invocation is not mandating heavy
compaction: the Tier-1 skill is a cheap idempotent no-op when nothing qualifies.

## P-020 definition (authored in `templates/policies/workflow-policies.md.tmpl`)

- **Applies To:** `ship`, `orchestrator`, `compact-context`.
- **Gate Point:** Ship post-merge closure (Step 6).
- **Statement:** at every post-merge closure, invoke compact-context (`target: all`).
  No `/compact` literal.
- **Precondition:** PR merged and Ship Step 6 entered.
- **Postcondition:** compact-context invoked before the shipment is declared closed;
  the operational-closure artifact carries a compaction-status field
  (`pending` → `done` / `degraded`).
- **Violation-Action:** SKIPPING invocation is a P-020 violation recorded via P-005
  telemetry, and closure is treated as incomplete (the shipment stays active under
  P-001 so it is caught/retried) — it does not hard-halt or strand the merged PR.
  A FAILED compact-context run is NON-BLOCKING (warn + continue; the merge landed and
  the skill is non-destructive).
- **Relationship to P-001:** required post-merge compaction is part of the closure set
  that keeps a merged shipment in-flight until complete (composes with, does not
  duplicate, P-001).
- **Relationship to P-017:** in dark mode, closure must report compaction status before
  `DARK_MODE_COMPLETE`.

## Implementation (8 tasks, dependency-ordered — all done)

| Task | Scope |
|---|---|
| 098.001-T | P-020 in `workflow-policies.md.tmpl` (the only definition site; no installed policy file) + amendment log 1.15.0 |
| 098.002-T | Ship template closure wiring (`templates/agents/_ship.agent.md.tmpl` Step 6 + dark-mode summary) |
| 098.003-T | Orchestrator template closure sequencing (`_orchestrator.agent.md.tmpl` + `DARK_MODE_COMPLETE`) |
| 098.004-T | compact-context skill + Primitive 1/10 + context-efficiency instruction references |
| 098.005-T | Foundation templates (AGENTS + constitution) enumeration |
| 098.006-T | Dogfood drift fix: installed `.github/agents/_ship.agent.md` Step 5 compact-context step restored + `_orchestrator.agent.md` closure sequencing |
| 098.007-T | Installed instruction/foundation sweep (harness-architecture Primitive 1/10 note — global artifact, edited directly + `AGENTS.md`) |
| 098.008-T | `ship_post_merge_compaction_gate` verify assertion + tests + CRLF-safe manifest checksums |

## Key constraints preserved

- **H1 — Env-agnostic fidelity:** zero `/compact` command literals introduced;
  grep-guarded in 098.008-T.
- **H2 — Skip vs failure semantics:** skip = incomplete closure (P-001), not a hard
  halt; failed run = non-blocking. Finalized via the operational-closure
  compaction-status field.
- **H3 — Verify/drift coupling:** the gate checks the installed `_ship.agent.md`, so it
  fails until the drift fix lands (dependency 008 → 006 makes the fix non-optional).
- **H4 — CRLF-safe manifest:** normalize → assert no CRLF → raw-byte hash; only installed
  copies re-hashed; templates are not manifest-tracked.
- **H5 — Composition, not duplication:** P-020 references P-001/P-017 rather than
  restating them.

## Rejected alternatives

- **(B) Human-decision escalation** — rejected: low-risk, environment-agnostic design
  with no unresolved product judgment.
- **Hard-wired `/compact` command** — rejected: Copilot-CLI-specific; violates the
  environment-agnostic core rule.
- **Block-merge gate (Option 4)** — rejected: P-020 is a post-merge closure gate, not a
  merge gate.

## Post-review refinements folded in

Two coupled Copilot review threads on PR #259 refined the status mechanism: the
operational-closure skill now **defines and initializes** the compaction-status field
(`pending` → `done` / `degraded`), and the Orchestrator next-shipment routing
**deterministically reads** the prior shipment's operational-closure artifact and gates
on `done`/`degraded` (`pending`/unset/missing blocks routing).
