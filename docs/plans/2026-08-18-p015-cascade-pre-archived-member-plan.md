# Implementation Plan — P-015 cascade close: explicit pre-archived manifest-member handling

Date: 2026-08-18
Agent: Stage (planning only — Ship executes)
Stash source: `EDE3CC2D`
Evidence: `docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md`
Spike: `docs/spikes/2026-08-18-cascade-close-pre-archived-member-behavior.md`
Deliberation: `docs/decisions/2026-08-18-p015-cascade-pre-archived-member-deliberation.md`
Classification: **reliability / contract-correctness (P-015 close-path authority)**
Feature: `132-F` · Tasks: `132.001-T`, `132.002-T`, `132.003-T` · Shipment: `141-S`

## Goal

Give the Cascade Close Sub-Procedure an explicit, machine-checkable
pre-archived-member branch so a clean `CASCADE` classifier verdict can never
again be silently overridden by an ad hoc manual safe-close, as happened during
140-S closure.

## Non-goals

* **No change to `src/autoharness/gates/shipment_closure.py`.** The spike proves
  the classifier already returns clean `CASCADE` for fully and partially
  pre-archived manifests. Evidence does not prove code behaviour needs to change.
* **No relaxation of step 3's `archived_ids` exact-match post-condition.** The
  compound doc recommends this; the spike disproves the premise. `archived_ids`
  already includes pre-archived members. Relaxing it would weaken a live P-005
  out-of-scope-mutation detector for no benefit. This is an explicit correction
  of the proposed remedy, not an oversight.
* No halt-and-escalate rule for pre-archived members — that would institutionalise
  the 140-S failure and fire on the ordinary case.
* No change to `templates/agents/_ship.agent.md.tmpl` or its checksum-tracked
  mirror; its close-path section already carries the classifier-authority rule.
  Avoids `harness-manifest.yaml` checksum churn (width isolation).
* No change to safe-close steps 1–10, the protected-set rules, or the
  no-pre-archived-exemption-for-the-protected-set invariant.
* No touching of stash entry `1EFDA8EE` or any other stash/queue work.

## Verified behaviour this plan encodes

From the spike, `backlogit v1.9.0`, three arms (control / partial / full pre-archive):

| Property | Result (identical in all three arms) |
|---|---|
| classifier verdict | `CASCADE`, clean |
| `archived_ids` | exactly {task items} + {feature members} + {shipment record} |
| `returned_ids` | `[]` |
| `parent_id` | preserved |
| exit code | `0` |

## Task decomposition

### `132.001-T` — Cascade Close Sub-Procedure: explicit pre-archived-member branch

**Surface (single template family):** `templates/skills/shipment-reconcile/SKILL.md.tmpl`

Add to the Cascade Close Sub-Procedure (currently lines ~516-561) a new numbered
step, placed **before** the existing step 1 (`{{OP_SHIP_SHIPMENT_MCP}}` invocation),
that:

1. Classifies each manifest member as `queued` or `pre-archived` by presence in
   `{{BACKLOG_DIRECTORY}}/queue/` vs `{{BACKLOG_DIRECTORY}}/archive/`, recording
   the `pre-archived` set for the step 5 report.
2. States that a `pre-archived` manifest member is **expected and tolerated**: it
   does **not** disqualify the `CASCADE` verdict, does **not** constitute a
   classifier ambiguity or unresolved precondition, and does **not** authorise a
   fallback to safe-close. Cite that the classifier's own record lookup reads
   both `queue/` and `archive/`, so archived inputs were already accounted for
   in the verdict.
3. States that the cascade operation is idempotent over pre-archived members and
   still returns them in `archived_ids` — therefore **step 3's exact-match
   post-condition applies unchanged**, and is evaluated against the full manifest,
   not against "members newly archived by this call".
4. Adds an explicit no-substitution rule: after Step 0 selects `CASCADE`,
   substituting manual safe-close is a **P-005 process deviation**, not a
   permitted fallback, regardless of manifest archival state. If a genuine
   unhandled cascade error occurs, halt and disclose — never silently switch paths.

Also update the Safe-Close-Mode contract summary bullets (~lines 736-740) so the
cascade bullet names the pre-archived tolerance alongside its existing
`returned_ids`/`archived_ids`/`parent_id` verification summary.

**Acceptance**: no unresolved `{{...}}` beyond the template's own legitimate
variables; the four numbered guarantees above are present; step 3's exact-match
wording is unchanged; the protected-set no-exemption rule is unchanged.

*Size `S` · Complexity `medium`* — single file, prose-only, but must be worded so
it cannot be read as licensing a safe-close substitution.

---

### `132.002-T` — Mirror pre-archived tolerance into P-015 policy text

**Surface (single template family):** `templates/policies/workflow-policies.md.tmpl`

In the **VERIFIED FULLY-COVERED-ROOT EXCEPTION** block (~lines 436-447), add a
precondition-clarifying item stating that manifest members already archived
before closure runs do **not** disqualify the exception, and that once the
classification returns `CASCADE` the close path is fixed — a subsequent manual
substitution of safe-close is a P-005 deviation.

Add a version-history row to the table at ~line 713 recording the clarification.

**Acceptance**: existing preconditions 1-6 semantically unchanged; new text does
not weaken the all-or-nothing qualification rule; version-history row present.

*Size `XS` · Complexity `low`* — small, additive, single file.

**Depends on `132.001-T`** — policy mirrors the contract wording settled there.

---

### `132.003-T` — Regression tests: CASCADE classification with pre-archived members

**Surface (single test module):** `tests/test_shipment_closure_classification.py`

Add cases proving the classifier returns `CASCADE` when:

1. **every** manifest member is pre-archived (the 140-S shape);
2. **some** members are pre-archived and some are queued;
3. the covering feature is pre-archived while its child is queued, and vice versa.

Plus negative/invariant-preservation cases proving pre-archival does **not**
create a false cascade grant:

4. a pre-archived feature with an **out-of-manifest child** (in either `queue/`
   or `archive/`) still yields `SAFE_CLOSE`;
5. a pre-archived **non-root** feature member still yields `SAFE_CLOSE`;
6. existing cascade and safe-close cases in the module continue to pass unchanged.

**Acceptance**: tests are hermetic (tmp fixtures, never live `.backlogit/`);
all existing tests in the module still pass; no change to the module's helpers
that would alter existing case semantics.

*Size `S` · Complexity `low`* — additive tests against an unchanged pure function.

**Depends on `132.001-T`** — the tests encode the contract settled there.

## Dependency graph

```text
132.001-T  (skill contract)
   |-- blocks --> 132.002-T  (policy mirror)
   |-- blocks --> 132.003-T  (regression tests)
```

`132.002-T` and `132.003-T` are independent of each other.

## Risk assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Wording read as licensing safe-close substitution | High | Explicit no-substitution clause in `132.001-T`; review gate checks for it |
| Weakening the `archived_ids` exact-match invariant | High | Named as an explicit non-goal; acceptance requires the wording be unchanged |
| Scope creep into gate code | Medium | Non-goal, backed by spike evidence |
| Agent-template/checksum churn | Medium | Out of scope; ship agent already carries the rule |

## Requires plan hardening

**yes** — the change edits a P-015 safety policy and its implementing skill
contract across two template families, and a mis-worded clause could authorise
the exact class of unsafe close this policy exists to prevent.

## Post-merge obligation (Ship, compound-refresh)

The evidence source
`docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md`
recommends a remedy this plan **rejects on evidence** (relaxing step 3's
`archived_ids` exact-match post-condition — see Non-goals). Leaving that
recommendation uncorrected would let a future Stage or Ship session re-derive
and implement the disproven Option A.

Ship MUST therefore invoke **compound-refresh** on that entry as part of Step 6
post-merge closure, updating its "Follow-up" and "The rule (corrected)" sections
to record: (a) the engine is idempotent over pre-archived manifest members,
(b) `archived_ids` already includes them, (c) the exact-match post-condition must
**not** be relaxed, and (d) the shipped contract change closes the gap. Cite this
plan, the spike, and shipment `141-S`.

This is an update to an existing learning entry, not a new one, and is covered by
Ship's existing compound-refresh obligation — it does not add a task to this
shipment.
