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

**Acceptance** (self-contained - satisfied by the document alone; see
Amendment F3)
* Document exists under `docs/` and decodes as valid frontmatter.
* All five *must contain* items above are present.
* Every claim traceable to the spike; no new measurements invented.
* **Not** an acceptance criterion here: being *referenced from* the contract
  test. That reference is authored and verified exclusively by Task 2.

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
* The in-file rationale comment cites the Task 1 document by path. **Task 2 is
  the sole owner of this reference** (Amendment F3); it is made once, here.
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
---

## Amendment F3 (Stage bounded correction, 2026-08-20) - acceptance ownership

**Status: additive. Nothing above is deleted; F3 supersedes the specific
statements it names.**

### Finding - Task 1 required a successor-owned artifact

Task 1 (`137.002-T`) originally required its new document to be *"referenced
from the contract test"*. That test edit is owned by Task 2 (`137.001-T`),
and Task 2 **depends on** Task 1 (`137.001-T -> 137.002-T (blocks)`).

Task 1 therefore could not satisfy its own acceptance without either:

* waiting for its own successor - a circular completion condition; or
* making the test edit itself - **duplicating** work owned by Task 2, on a file
  Task 2 also edits, on the same lines.

Ship gates every task, so an unsatisfiable acceptance criterion blocks Task 1
and, transitively, the whole shipment.

### Resolution

**Task 1 is now independently complete on document creation, frontmatter
validity, and content.** Its acceptance is satisfied by the deliverable it
actually owns.

**Task 2 retains sole ownership of the reference.** Its requirement 3 (the
in-file pointer to the Task 1 document) is unchanged and is now also an explicit
Task 2 acceptance criterion, so the reference is still verified - once, in the
task that authors it. Covering feature `137-F` acceptance carries the end-state
guarantee that the document exists **and** is cited from the contract test.

### What was deliberately *not* done

* **No reverse dependency** was added. The edge stays one-way:
  `137.001-T -> 137.002-T (blocks)`. Adding `137.002-T -> 137.001-T` would be a
  literal cycle.
* **No duplication of the test edit.** Task 1 is explicitly instructed not to
  touch `tests/test_scope_containment_policy_contract.py` or any other test.
  Width isolation for Task 1 is docs-only.

### Net effect on sequencing

Unchanged: `137.002-T` -> `137.001-T` -> `137.003-T`, with `137.004-T`
order-independent. Task 1 still lands first; it simply can now *complete* when
it lands.
