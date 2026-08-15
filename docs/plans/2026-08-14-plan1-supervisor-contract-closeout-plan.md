---
title: "Implementation Plan — Plan 1 supervisor contract and verification closeout"
date: "2026-08-14"
description: "Closes the two PR #325 findings that still have real remaining scope after Plan 1 shipped: undefined --session-id semantics in the CLI contract, and an under-powered negative control in the shipment-topology verifier. Two other findings were re-triaged this session and found already satisfied by shipped code."
doc_type: plan
source: docs/plans/2026-08-14-plan1-supervisor-contract-closeout-plan.md
plan_id: "PLAN-P1-CLOSEOUT"
stash_ids: ["024FDA20", "A5628E7E"]
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/reviews/2026-08-14-plan1-supervisor-contract-closeout-review.md"
  - "docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md"
---

# Implementation Plan — Plan 1 supervisor contract and verification closeout

## 1. Re-triage of the four PR #325 findings

All four were raised against backlog artifacts that have since shipped and been
archived (118-F/119-F/120-F, shipments 127-S/128-S/129-S). Each was re-evaluated
this session against the **shipped code**, not the archived task text.

| Stash | Finding | Re-triage result |
|---|---|---|
| `9863A6D6` | `CANCELLED` vs `EXITED` terminal-state disagreement | **Already satisfied.** `src/autoharness/supervise/session.py` defines BOTH as distinct absorbing terminal phases, with `TERMINAL_PHASES` exactly `{EXITED, FAILED, REFUSED, CANCELLED}`, `DRAINING` as the sole gateway, and an explicit legal-transition table that removes any `CANCELLING -> EXITED` / `CANCELLING -> CANCELLED` edge. This is precisely the "define both with an explicit transition" option the stash asked for. No remaining scope. |
| `F72AFF70` | `119-F` summary claims `PipeChildProcess` is the default backend, contradicting the F29 inherited-stdio ruling | **Already satisfied.** Every live surface states the correct contract: the plan at lines 160/265/600 records `InheritStdioChildProcess` as THE DEFAULT with `PipeChildProcess` "retained but demoted"; `process_pty.py` documents the F29 degrade-to-inherited-stdio hard requirement; `docs/design-docs/2026-08-12-supervisor-observability-rollout-rollback.md:360` states PTY falls back to inherited stdio and "never `PipeChildProcess`". The contradiction survived only in the now-archived `119-F` summary. No remaining scope. |
| `024FDA20` | `--session-id` semantics undefined | **Real remaining scope.** See T1. |
| `A5628E7E` | Verifier negative control proves less than it appears to | **Real remaining scope.** See T2. |

## 2. T1 — Define `--session-id` semantics in the CLI contract

`src/autoharness/cli.py:143` documents only `--session-id ID  Explicit session id
(default: generated)`. That answers *operator-supplied or generated* but leaves
the two questions the stash actually raised unanswered in the contract:

* **Uniqueness** — must it be unique per workspace?
* **Collision** — what happens when it collides with a live session?

The behaviour already exists in `src/autoharness/supervise/locking.py`:
`SessionLockRefused` is raised when guard-lock acquisition is refused due to live
contention. The gap is that this is implemented but not stated in the CLI
contract, so an operator cannot predict it. T1 documents the existing behaviour;
it does not change it.

## 3. T2 — Strengthen the shipment-topology verifier negative control

`docs/spikes/2026-08-09-plan1-shipment-topology-proof/verify-plan1-shipment-topology.ps1:584-585`:

```
$nonRoot = Test-CascadeEligible @('118.003-T')
Assert (-not $nonRoot.Ok) "NEGATIVE CONTROL: a manifest with no feature member -> REJECTED"
```

The variable is named `$nonRoot`, but the input is a bare task ID, so the case
exercised is *manifest contains no feature member at all* — not *manifest contains
a feature that is not a root*. The **non-root-feature rejection branch is
therefore never executed**, exactly as the stash claims.

**Ruling (Stage, under the operator's granted planning authority):** the verifier
is cited evidence for the F14 topology redesign, so its existing 196/196
assertions MUST NOT be modified, reordered, or weakened. The fix is **purely
additive**: add a genuine non-root-feature negative control alongside the existing
one. Assertion count increases; no existing assertion changes semantics.

**Correction (PR #339 Copilot review, comment 3788712405).** An earlier draft of
this ruling also asked for the existing assertion *message* to be corrected. That
instruction was wrong and is **withdrawn**: line 585 already reads
`"NEGATIVE CONTROL: a manifest with no feature member -> REJECTED ($($nonRoot.Reason))"`,
which already describes the no-feature-member case it actually tests — so there is
no message correction to make, and making one would have contradicted the
immediately preceding “MUST NOT be modified” constraint. The only misleading token
is the **identifier** `$nonRoot`. Existing predicates, messages, and ordering stay
**unchanged**; renaming `$nonRoot` to `$noFeatureMember` is **optional** and, if
done, is a pure local-variable rename that changes no assertion semantics and no
assertion count.

## 4. Sequencing

T1 and T2 are independent and may execute in either order.

## 5. Plan Hardening conclusion

**Requires plan hardening: no.** Both tasks are additive documentation and
additive test coverage over already-shipped, already-reviewed behaviour. Neither
changes runtime behaviour, schemas, CLI distribution, or more than one template
family. Blast radius is minimal.
