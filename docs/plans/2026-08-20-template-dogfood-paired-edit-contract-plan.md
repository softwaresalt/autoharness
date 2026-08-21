---
title: "Formally define the paired-edit maintenance contract for divergent template/dogfood pairs"
date: 2026-08-20
stash_id: 6D62077C
spike: docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md
requires_plan_hardening: no
blast_radius: "low (one new document, one contract-test strengthening; no agent behaviour change)"
---

# Implementation Plan - Template/dogfood paired-edit maintenance contract

Date: 2026-08-20
Agent: Stage (planning only - Ship executes)
Stash source: `6D62077C`
Spike: `docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md`
Classification: **maintenance contract / verification hygiene**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Goal

Replace an undocumented de-facto practice with a stated, enforced contract:
declare which template/dogfood pairs are **paired-edit maintained** rather than
mechanically rendered, record **why** per pair, and make an unreviewed addition
to that set fail a test.

## Non-goals

* **No change to `_render_template`.** The spike rejects extending it.
* **No reconciliation of the semantic prose drift** found in spike F3/F4(2).
* **No fix for the `_derive_template_variables` coverage gap** (spike F5) -
  captured as a separate deferred stash entry.
* **No content back-porting** between any template and its mirror.

## Task 1 - Author the maintenance-contract document

**Deliverable**: a new document under `docs/` stating the contract.

**Must contain**
1. The two categories: **mechanically rendered** (byte-identical through
   `_render_template`) and **paired-edit maintained**.
2. The current inventory, explicitly listing all eight pairs:
   * *Mechanically rendered (4)*: role-enforcement, circuit-breaker,
     copilot-code-review, feature-flow-dark.
   * *Paired-edit maintained (4)*: `_ship`, `_stage`, `_orchestrator` agents and
     `github-pr-automation.instructions`.
3. The **per-pair cause taxonomy** from spike F4: install-time conditional
   content; semantic prose drift; variable-derivation coverage gap - with the
   measured evidence (spike F2/F3/F5 tables) cited, not restated from memory.
4. The **author obligation**: editing either side of a paired-edit pair obliges
   the author to consider the other side in the same change and to refresh the
   `harness-manifest.yaml` checksum.
5. An explicit statement that paired-edit status is a **recorded exception, not
   a goal** - the drift it tolerates is technical debt with an owner, not a
   design choice to be extended casually.

**Acceptance**
* Document exists, decodes as valid frontmatter, and is referenced from the
  contract test.
* Every claim traceable to the spike; no new measurements invented.

## Task 2 - Pin the divergent set in the contract test

**File**: `tests/test_scope_containment_policy_contract.py`

That file already splits `_CLEAN_BYTE_IDENTICAL_PAIRS` (asserted byte-identical)
from `_DIVERGENT_MARKER_ONLY_PAIRS` (asserted by marker presence plus manifest
checksum). Keep both mechanisms. Add:

1. A per-pair **cause annotation** on each divergent entry, matching the Task 1
   taxonomy.
2. An assertion that the divergent set has **exactly the expected membership** -
   so a fifth pair silently becoming non-renderable is a test failure naming the
   new pair, not an unnoticed shrug.
3. A pointer to the Task 1 document in the in-file rationale comment, replacing
   the current inline-only explanation.

**Acceptance**
* Existing byte-identity assertions for the four clean pairs still pass unchanged.
* Membership assertion fails with a clear message if a pair is added or removed.
* No production code changes.

## Verification (Ship)

1. Full test suite green.
2. Removing one entry from the divergent inventory makes Task 2's membership
   assertion fail (verify locally; do not commit).
3. No file under `templates/` or `.github/` is modified by this plan.

## Sequencing

**Lands before** the `backlogit_stash_archive` migration in the same shipment.
That migration is itself a paired edit on the `_ship` pair, so the rule must
exist before the edit is made under it.

## Plan Review (plan-review gate)

**Verdict: PASS.** Reviewed 2026-08-20 by Stage.

| Check | Result |
|---|---|
| Conclusion supported by evidence | PASS - spike is quantitative and bidirectional; premise falsification is demonstrated, not asserted |
| Scope matches the spike's chosen direction | PASS |
| Each task within the 2-hour rule | PASS |
| Width isolation | PASS - Task 1 docs-only, Task 2 tests-only |
| Acceptance criteria falsifiable | PASS - both tasks include a negative check |
| Incidental discovery handled per P-021 C1 | PASS - F5 deferred to a new stash entry, not absorbed |
| Hardening required (P-006) | NO - additive documentation plus a test-only assertion; no policy, contract, or runtime behaviour changes; fully reversible |

No blocking findings. Advisory: Task 2's membership assertion must fail
**closed** (unknown pair present -> fail), not merely warn.
