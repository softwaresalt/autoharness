---
doc_type: session-memory
agent: stage
date: 2026-09-07
session_topic: "15A02E21 decision close, parked/hold contract surface, plan -> harvest -> queued shipment"
stash_entries: [15A02E21, 4D3826FE]
feature: 161-F
shipment: 169-S
plan: docs/plans/2026-09-07-shipment-reconcile-cascade-premode-member-class-contract-plan.md
outcome: "decision decided; plan hardened + reviewed PASS; 161-F/7 tasks harvested; 169-S queued and BLOCKED"
---

# Stage session — 2026-09-07

## What was decided

The operator recorded three authoritative decisions for stash bug `15A02E21`, plus a new
lifecycle-status requirement.

* **D-1** — the prior 159-S close is an **accepted-with-remediation P-005 deviation** (not a
  retroactive ratification; ratifying would erase the P-005 retrieval key). Nothing reopened.
* **D-2** — **Option A**: classifier-aware, member-class-scoped Pre-Mode.
* **D-3** — qualifying feature `active|done` PASS, `archived` tolerate-and-report, `queued` hard
  HALT, declared frontmatter status read regardless of `queue/` vs `archive/` location.

Binding refinements **R-1..R-5** (R-5 added at revalidation: unrecognised status ⇒ explicit HALT).

## Outputs

| Item | Value |
|---|---|
| Decision status | `decided` |
| Plan | `docs/plans/2026-09-07-shipment-reconcile-cascade-premode-member-class-contract-plan.md` |
| plan-harden | completed (required — fail-closed gate on an irreversible close path) |
| plan-review | **PASS**, cycle 2 of 3 (cycle 1 FAIL, four P1s) |
| Feature | `161-F` |
| Tasks | `161.001-T` .. `161.007-T` |
| Shipment | `169-S` — **queued, not routed to Ship** |
| New stash | `4D3826FE` (parked/hold lifecycle status, requires deliberation) |

## Findings worth carrying forward

1. **No Python change is needed.** `classify_shipment_close_path` already exposes `close_path`,
   `reason`, and `qualifying_feature_ids`. The fix is Markdown + tests only — materially smaller
   than the decision artifact originally scoped.

2. **The "byte-identical skill/template" claim was false.** They are identical *modulo*
   `{{BACKLOG_DIRECTORY}}` — exactly three lines differ (268, 272, 277). The parity guard must be
   **two-sided**.

3. **R-1 consolidates an existing rule.** Safe-Close Step 0(b) already says location alone is never
   sufficient. Pre-Mode failed to *apply* a rule the same file states. Consequence: U2 must also
   cover Step 0(b), or the fix leaves the rule in three places instead of one and defeats its own
   single-source acceptance criterion.

4. **A declared enum is not an enforced enum.** `header-def.yaml` declares shipment `blocked`, but
   the Go binary hard-codes the transition matrix and has no `blocked` `ShipmentStatus` constant —
   and `backlogit move` does not validate, so invalid writes are silently accepted. Real `blocked`
   shipment records exist as permanent dead ends. This resolved an open question in the
   `parked`/`hold` record and **raises its stakes**: adding a status to `header-def.yaml` alone
   would reproduce that exact failure mode.

5. **The stale test docstring.** `tests/test_shipment_reconcile_record_status.py` claims no
   installed dogfood mirror exists. It does (1082 lines) and is therefore **untested**.

## Blockers and hazards

* **169-S must not be routed to Ship** — PR #436 / the 159-S post-merge closure release unit is
  still open. 169-S is also the named P-005 remediation for D-1.
* **All documentation edits are UNCOMMITTED.** HEAD is checked out on PR #436's head branch
  (`post-merge/151-f-ship-1-v1-5-0-shipped-guardrail-contract-restoration`), in sync with origin.
  Committing there would inject these artifacts into PR #436. The operator should create a separate
  docs branch off the default branch, or explicitly authorize one.
* **backlogit MCP transport is down** (`Transport closed`); the whole session ran on the
  registry-declared CLI fallback.
* **Registry drift (report-only):** `.autoharness/backlog-registry.yaml` has no `features.sizing`
  key and its `create_task`/`update_task` params omit size/complexity, although
  `schemas/backlog-tool-registry.schema.json` defines them and the CLI supports them. Stage may not
  edit config files, so this is recorded, not fixed.
* `backlogit get --json` does not project `custom_fields`, so size/complexity are invisible to that
  view even when correctly written. Verify against the artifact file.

## Next session

1. Close PR #436 / the 159-S release unit.
2. Then route `169-S` to Ship. Enforce at execution: `161.003-T` is **indivisible** (R-4), and the
   test tasks are **red-first**.
3. Deliberate `4D3826FE` (parked/hold) as a separate contract surface — do **not** fold it into
   `169-S`.
