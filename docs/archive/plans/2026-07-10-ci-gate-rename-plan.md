---
title: "Rename Dogfood CI Aggregation Gate to ci gate — Implementation Plan"
description: "Single-task, single-file plan to rename the build-named CI aggregation gate in .github/workflows/ci.yml to ci-gate / ci gate and rewrite its two justifying comment blocks. Trivial, near-zero-risk dogfood correction."
doc_type: plan
source: docs/plans/2026-07-10-ci-gate-rename-plan.md
decision_doc: docs/decisions/2026-07-10-ci-gate-rename-decision.md
source_stash_ids: []
requires_plan_hardening: "no"
plan_review_verdict: "approved"
backlog_items:
  - "071-F"
  - "071.001-T"
  - "083-S"
tags:
  - "ci"
  - "github-actions"
  - "dogfood-parity"
  - "cleanup"
---

# Rename Dogfood CI Aggregation Gate to ci gate — Implementation Plan

See `docs/decisions/2026-07-10-ci-gate-rename-decision.md` for the rationale.
This is a fully-specified, single-file, near-zero-risk chore. One
width-isolated task covers it; no decomposition beyond that is warranted.

## Task decomposition

```text
T1 (071.001-T): rename build job -> ci-gate in .github/workflows/ci.yml   -- no deps
```

## Task 071.001-T — rename job + rewrite comments

**File:** `.github/workflows/ci.yml` (single file)

**Changes:**

1. Job id `build:` → `ci-gate:` and `name: build` → `name: ci gate`.
2. Header comment (~lines 9-11): rewrite to describe the always-running
   `ci gate` aggregation gate; remove the deleted-ruleset rationale.
3. Inline comment above the job (~lines 90-92): rewrite the same way; remove the
   "named build to satisfy the main ruleset" wording.

**Acceptance criteria:**

1. Job id `build` → `ci-gate`; `name: build` → `name: ci gate`.
2. Both comment blocks rewritten to describe the `ci gate` aggregation gate,
   without the obsolete deleted-ruleset rationale.
3. No other job/`needs`/reference changes; `templates/ci/ci.yml.tmpl` unchanged;
   local-build-evidence gate wording in the ship agent and
   github-pr-automation instructions unchanged.
4. Workflow remains valid YAML and preserves behavior: aggregation gate still
   `if: always()`, `needs: [changes, test]`, same pass/fail logic (fail only on
   a needed job that is `failure`/`cancelled`; skipped `test` is OK).
5. Conditional (does not apply): `.autoharness/workspace-profile.yaml` has no
   `ci.required_check_name` field, so no profile edit is required.

## Risk assessment

* **Blast radius:** minimal. `build` is the last job in the workflow; nothing
  `needs:` it, so the job-id rename cannot break any dependency graph.
* **External impact:** none. The operator has removed the ruleset and will not
  require this check in branch protection, so no required-check name mismatch is
  introduced.
* **Hardening:** not required (P-006) — low blast radius, no cross-file coupling.

## Plan-review sanity pass

Self-review (trivial scope, no multi-persona ceremony):

* Correctness — matches the verified spec and the template default. OK.
* Completeness — job id, `name`, and both comment blocks all covered. OK.
* Safety — no `needs:` breakage; template and unrelated build-gate wording
  explicitly out of scope. OK.
* Behavior preservation — YAML validity and gate logic retained as acceptance
  criteria. OK.

Verdict: **approved** for harvest and shipment.
