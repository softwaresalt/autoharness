---
title: "Workspace-authoritative branch resolution as a safe operation"
description: "Reduced current-state contract for the branch-resolution defect. Replaces the agent-composed git command with a registered safe operation, autoharness op git ensure-branch --shipment ID, which resolves the branch name inside Python from the shipment record and never returns it to the agent. Eliminates the interpolation P0 structurally rather than by escaping, and replaces the invalid git checkout -b -- NAME form with check-ref-format validation plus git switch --create under fixed argv, asserting the postcondition after the attempt rather than checking before it."
doc_type: plan
source: docs/plans/2026-09-18-branch-ensure-operation-plan.md
date: 2026-09-18
plan_id: branch-ensure-operation
plan_path: docs/plans/2026-09-18-branch-ensure-operation-plan.md
plan_role: active
revision: 2
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document replacing the eight-attempt append history of workspace-authoritative-branch-resolution at architecture level. It awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review. Revision 2 remediates one finding of the PR #457 current-HEAD Copilot review of Push A, a P-021 C1 in-scope completion of this already-published plan: the ACTIVATE commit modifies manifest-tracked installed artifacts and the Rollout section omitted the atomic .autoharness/harness-manifest.yaml checksum refresh those edits require. The Rollout section now binds decision D11 - the affected manifest entries refreshed in the same commit and the same rollback unit, followed by a checksum-parity re-digest - and states that the refreshes are commit members rather than activation surfaces, so no surface, consumer or gate count in this plan moves. No task is added and the live manifest is not edited: this is a future implementation contract. It still carries REMEDIATED-PENDING-REVIEW because it awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-branch-ensure-operation-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 4
source_stash_ids:
  - 86498B64
  - 14F4D6F3
merged_stash_ids:
  - 14F4D6F3
feature_id: 170-F
shipment_id: 178-S
unit_role: reduced-defect-unit
supersedes_plan: docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md
depends_on_shipments:
  - 185-S
task_reharvest_gate: 185-S
requires_plan_hardening: true
hardening_rationale: "Executes git against the working repository from an agent-reachable surface. A defect creates or switches branches in a live workspace."
tags:
  - defect-unit
  - branch-resolution
  - safe-operation
  - reduced-scope
---

# Workspace-authoritative branch resolution as a safe operation

## The P0 and why escaping could not fix it

Attempt-08 `A1` (P0): the plan's branch-ensure procedure interpolates a
resolved branch name into a git command written in an agent document.

The previous revisions tried to close this inside the agent surface — argument
separators, quoting rules, a promise of `shell=False`. None can work, because:

> **A Markdown agent does not execute an argument vector.** A model reads prose
> and composes a shell string. `--` cannot terminate an argv that does not
> exist, and a document cannot promise `shell=False` about an execution it does
> not perform.

Two further defects followed from the same frame:

* **Invalid argv.** `git checkout -b -- <branch>` was specified as the safe
  form. It is not safe; it is **wrong**. In `git checkout -b`, `--` separates
  revisions from **pathspecs**, so the branch name after it parses as a
  pathspec and the command does not mean what the plan says.
* **TOCTOU.** A compare-then-create pair (`rev-parse`, then decide, then
  create) has a window between the check and the act.

## Contract

The agent calls one registered operation:

```text
autoharness op git ensure-branch --shipment <SHIPMENT_ID>
```

The agent passes **a shipment identifier**. It never receives, holds, or
interpolates the branch name. The operation:

1. reads the shipment record and resolves the workspace-authoritative branch
   name **inside Python**;
2. validates it with `git check-ref-format --branch <name>` — git's own
   authority on what a legal branch name is, rather than a hand-written regex;
3. executes `git switch --create <name>` or `git switch <name>` with the name
   as a **plain argv element** under the `185-S` fixed-argv primitive, with
   `git` on the per-operation allowlist and no shell anywhere;
4. **asserts the postcondition after the attempt** — `git rev-parse
   --abbrev-ref HEAD` equals the resolved name — rather than checking
   beforehand, which closes the TOCTOU window;
5. returns a typed outcome token.

A name beginning with a hyphen is carried as a plain list element and is not
reinterpreted, because there is no shell to reinterpret it.

This is the reframe the architecture decision records as D1: **a value the
agent never holds is a value the agent cannot mis-escape.**

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `BRANCH_ENSURED` — postcondition asserted: `HEAD` is on the resolved branch |
| Fail state | `BRANCH_REFUSED` — name rejected by `check-ref-format`, executable not on the allowlist, or postcondition assertion failed after the attempt |
| Producer | `185-S` PR-3 fixed-argv exec; `184-S` operation registry |
| Consumer | the `pipeline-topology` gate; Ship's branch-ensure step |
| Activation commit | one task, one commit: operation registered, agent template and installed mirror switched to the operation call together |

Both states are reachable and observable from the returned outcome token; there
is no state in which the operation reports success without having asserted the
postcondition.

## Rollout

**PREPARE (inert).** The operation is implemented and registered while no agent
surface calls it; the existing prose procedure remains in place, so live
behaviour is unchanged.

**VERIFY.** `BRANCH_ENSURED` and `BRANCH_REFUSED` both observed; a
hyphen-leading and a `check-ref-format`-rejected name both observed refused;
the invalid `checkout -b --` form asserted absent from every normative
procedure.

**ACTIVATE.** One task, one commit removing the interpolated command from the
Ship agent template and installed mirror and replacing it with the operation
call. Leaving the prose form in either file while the operation exists is the
P0 unfixed.

**Manifest parity is part of that same atomic unit (decision `D11`).**
`.github/agents/_ship.agent.md` is a **manifest-tracked installed artifact**
with an `artifacts:` entry in `.autoharness/harness-manifest.yaml` recording a
`sha256` of its pre-activation content; `templates/agents/_ship.agent.md.tmpl`
is not tracked — the manifest tracks no template — so the ACTIVATE commit
refreshes **exactly one** manifest entry. In the **same commit** and the **same
rollback unit**, rewrite that checksum to the `sha256` of the installed mirror
*as written by this commit*, then **verify checksum parity** by re-digesting
the installed file and comparing it against the recorded value. A commit that
replaces the interpolated command in the mirror without its manifest refresh
leaves the manifest asserting a digest of a file the same commit has already
rewritten — an installed-artifact parity hole in a unit whose whole purpose is
removing an interpolation hazard from that file — and is an **immediate
revert**, not a fixup commit. The refresh is a **commit member, not a third
surface**: it registers no operation and changes no surface count stated
anywhere in this plan. This binds a **future implementation commit**; it
authorizes no staging-time edit to the live manifest, and none has occurred.

## Task re-harvest gate

Task decomposition waits on `185-S`, because the operation's signature is the
exec primitive's signature. The existing tasks under `170-F` remain queued and
are re-sliced once PR-3 is fixed.

## Out of scope

* The operation substrate, registry and transports — `184-S`.
* The exec, path-containment and atomic-write primitives — `185-S`.
* Any change to what the workspace-authoritative branch *is*. This unit changes
  how it is resolved and applied, not the naming policy.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | `git switch` availability on older git | `check-ref-format` and `switch` are both long-established; the VERIFY step records the observed git version with the evidence. |
| R2 | The operation runs against a dirty worktree | The operation reports the refusal as a typed token rather than forcing a switch; recovery is the operator's, not the agent's. |
| R3 | An agent surface retains the old prose form after activation | The activation task's assertion is that the invalid form appears in **no** normative procedure, checked across both template and mirror. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Could better escaping have fixed the P0 in the agent surface? | No. The agent composes a shell string from prose; there is no argv to separate and no execution to promise `shell=False` about. The fix is structural — the agent passes a shipment ID and never holds the branch name. |
| H2 | Is `git checkout -b -- <branch>` safe? | It is **wrong**. After `-b`, `--` separates revisions from pathspecs, so the name parses as a pathspec. The activation task asserts this form appears in no normative procedure. |
| H3 | Why assert the postcondition instead of checking first? | A compare-then-create pair opens a TOCTOU window. Asserting `git rev-parse --abbrev-ref HEAD` equals the resolved name **after** the attempt has no window: either HEAD is on the branch or the operation reports `BRANCH_REFUSED`. |
| H4 | What about a branch name beginning with a hyphen? | It is carried as a plain argv element under `shell=False`, and it must additionally pass `git check-ref-format --branch`. Two independent defences, neither relying on quoting. |
| H5 | Why use `check-ref-format` rather than a regex? | Git's rules for legal ref names are intricate and version-dependent. A hand-written regex is a second, divergent specification; `check-ref-format` is the authority. |
| H6 | Can the operation force a switch on a dirty worktree? | No. It reports refusal as a typed token. Forcing would put an agent in a position to discard operator work. |

### Blast radius

Git branch state in a live working repository, reached from an agent surface.
A defect creates or switches branches under the operator.

### Rollback

PREPARE is inert; the prose procedure remains authoritative until activation.
The ACTIVATE commit reverts as a unit across template and mirror. Note that
rollback restores the interpolated prose form, so a revert re-opens the P0 and
must be treated as a temporary state.

### Verification floor

Both outcome states observed, plus a hyphen-leading name and a
`check-ref-format`-rejected name both observed refused, plus the invalid
`checkout -b --` form asserted absent from every normative procedure.
