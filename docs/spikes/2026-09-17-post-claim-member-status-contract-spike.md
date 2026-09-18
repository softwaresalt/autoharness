---
title: "Spike — post-claim member-status contract: provenance of P-002.6 and the autoharness-owned remedy surface"
description: "Read-only, in-workspace spike resolving the ownership and remedy surface for stash 3EF5AAF2. Establishes by existence proof that P-002.6 and its WAVE_NO_PROGRESS/ready_k vocabulary exist nowhere in autoharness, that the canonical Ship contract already tolerates post-claim all-active members in both the template and the installed mirror, and that the actionable defect is the absence of a named, versioned, machine-checkable post-claim member-status contract that a consuming workspace could be validated against."
doc_type: spike
source: docs/spikes/2026-09-17-post-claim-member-status-contract-spike.md
date: 2026-09-17
status: complete
timebox: "in-session, read-only"
source_stash_id: 3EF5AAF2
stash_ids:
  - 3EF5AAF2
source_bug_report: docs/bugs/2026-09-17-autoharness-shipment-claim-wave-admission-contract-conflict.md
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
prior_learnings:
  - docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
linked_artifacts:
  - docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
tags:
  - "spike"
  - "shipment-claim"
  - "contract-drift"
  - "ownership-boundary"
---

# Spike — post-claim member-status contract

## Containment declaration

This spike is **read-only and in-workspace**. No external `%TEMP%` workspace
arm was created, no worktree was created, no file was mutated, and no backlog
record was written. This is a deliberate correction of the containment pattern
recorded as a P-005 violation in stash `7F9CB5E9`.

Engram search was unavailable (circuit open, `error-5001`). All evidence below
comes from `git grep`, `git log -S`, and exact-path reads — which for the
central question (does a token exist anywhere in this repository or its
history) is a stronger instrument than semantic search.

## Questions

* **Q1** — Does `P-002.6`, or any wave-admission policy, exist in autoharness?
* **Q2** — Does the canonical Ship contract tolerate post-claim all-active
  manifest members, and is that tolerance present in both the template and the
  installed mirror?
* **Q3** — Is any upstream backlogit change required?
* **Q4** — What is the actionable autoharness-owned remedy surface?

## Q1 — Does `P-002.6` exist in autoharness? **No.**

```text
git grep -l -E "WAVE_NO_PROGRESS|ready_k" -- '*.md' '*.tmpl'
  docs/bugs/2026-09-17-autoharness-shipment-claim-wave-admission-contract-conflict.md

git log --oneline -S "P-002.6" --all
  187526c0 chore: stage closure evidence contract fix

git log --oneline -S "WAVE_NO_PROGRESS" --all
  187526c0 chore: stage closure evidence contract fix
```

`187526c0` is the commit that added the bug report itself. The tokens have
never existed in this repository outside that document.

`.github/policies/workflow-policies.md` declares `P-002: TDD Gate
(Harness-Ready Precondition)` at line 36 with **no `.6` sub-clause**. A
repo-wide search for "wave" outside the bug report returns only unrelated
prose ("waved through", research-doc "Wave 1..4" headings) and a single
cross-reference to stash `3EF5AAF2` in
`docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md`.
There is no wave scheduler, no `ready_k` set, no `terminal_success` set, and no
`active residual` concept in the policy registry, the agent templates, the
installed agents, or any skill.

The report's own frontmatter confirms the provenance:
`external_provenance.origin_repository: softwaresalt/backlogit`, with a
transfer note stating it was authored in the backlogit workspace and describes
that workspace's installed harness.

**Finding**: `P-002.6` is a **downstream-authored policy in a consuming
workspace**. The report's ownership attribution to "the autoharness
integration/policy layer" is upheld, but the artifact it names is not present
here and cannot be edited here.

## Q2 — Does the canonical contract already tolerate the state? **Yes, in both copies.**

`templates/agents/_ship.agent.md.tmpl` line 274 and its installed mirror
`.github/agents/_ship.agent.md` line 322 carry the same intake-reconciliation
scope note:

> every manifest task still shares one uniform status (all `{{STATUS_QUEUED}}`
> pre-claim, or all `{{STATUS_ACTIVE}}` immediately after this session's own
> claim in item 4 above)

The adjacent `SHIPMENT_STATE_INCONSISTENT` early-warning (template line 166,
installed line 214) is deliberately scoped to the **inverse** condition — a
shipment record still reading `queued` while a member reads `active` or `done`
— and explicitly does not fire on the post-claim all-active state.

This matches `docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`
(confidence **high**, direct hit), whose recorded conclusion is that the
contract's tolerance "is correct and was **not** missing", and that the gap was
the missing causal attribution, which that learning then supplied.

**Finding**: autoharness's canonical Ship contract and backlogit's
`ClaimShipment` contract **agree**. The deadlock described in the report arises
only in a workspace whose installed harness carries an admission rule that
contradicts the canonical tolerance.

## Q3 — Is an upstream change required? **No.**

backlogit's `ClaimShipment` behaves per its documented contract, its unit test
`TestClaimShipment_ActivatesIncludedScope`, and this repository's own
independently observed compound learning. The report's Option A ("autoharness-
only correction using governed status operations to keep members `queued`")
and Option B ("a shipment-only claim operation or activation-scope option")
both presuppose changing what claim does. Both are **out of scope for this
entry**, because the canonical contract does not need members to stay `queued`
— it already expects them not to.

This is a distinct conclusion from stash `7F9CB5E9`, whose remedy genuinely is
upstream. The two entries share only the escalation *question*, answered once
in decision **D7**.

## Q4 — Actionable autoharness-owned remedy surface

The canonical tolerance is correct but is **prose-only, unnamed, unversioned,
and unenforced**. Three consequences follow, each an autoharness-owned defect:

1. **Unnamed.** There is no policy ID, token, or contract clause a downstream
   harness author can cite when deciding what post-claim member status means.
   `P-002.6` was authored into that vacuum.
2. **Unattributed in the contract itself.** The causal attribution lives only
   in `docs/compound/`, which is not part of the installed harness, so a
   consuming workspace never receives it.
3. **Undetectable.** `src/autoharness/verify_workspace.py` is the deterministic
   installed-workspace verifier, but it has no check that would notice a
   locally authored policy contradicting a canonical agent-contract clause.

**Recommended remedy**, carried into the plan:

* State the post-claim member-status expectation as a **named, numbered
  canonical clause** in `templates/policies/workflow-policies.md.tmpl` and its
  installed mirror, with the backlogit claim-cascade attribution inline.
* Cross-reference that clause from the existing Ship-template tolerance note so
  the two cannot drift apart silently.
* Add a `verify-workspace` check that fails closed when an installed policy
  registry declares an admission rule treating post-claim member `active` as a
  blocking residual, naming `WAVE_NO_PROGRESS`-class contradictions explicitly.
* Add a composed state-machine regression test in the style of
  `docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`:
  for the claim→admission transition, name one concrete legitimate state that
  passes (fresh claim, all members `active`) and one that fails (record
  `queued` with an `active` member).

**Explicitly not recommended**: weakening any active-residual concept a
downstream workspace has legitimately authored for genuinely stalled prior-wave
members. The canonical clause must distinguish *post-claim* all-active from
*mid-execution* partial-active, which is exactly the distinction the report
correctly identifies as observationally ambiguous without a claim timestamp.

## Residual uncertainty

* Whether any other consuming workspace has authored a similar contradictory
  rule is **unknown** and unverifiable from this repository. The
  `verify-workspace` check is the mechanism that answers it per-workspace.
* The `149-S` and `140-S` halts cited by the report occurred in the backlogit
  workspace and are **not reproducible here**; they are accepted as reported
  and are not re-derived. No autoharness test asserts against them.
