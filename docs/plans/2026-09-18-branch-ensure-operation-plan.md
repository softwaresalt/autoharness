---
title: "Workspace-authoritative branch resolution as a safe operation"
description: "Reduced current-state contract for the branch-resolution defect. Replaces the agent-composed git command with a registered safe operation, autoharness op git ensure-branch --shipment ID, which resolves the branch name inside Python from the shipment record and never returns it to the agent. Eliminates the interpolation P0 structurally rather than by escaping, and replaces the invalid git checkout -b -- NAME form with check-ref-format validation plus git switch --create under fixed argv, asserting the postcondition after the attempt rather than checking before it."
doc_type: plan
source: docs/plans/2026-09-18-branch-ensure-operation-plan.md
date: 2026-09-18
plan_id: branch-ensure-operation
plan_path: docs/plans/2026-09-18-branch-ensure-operation-plan.md
plan_role: active
revision: 5
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document replacing the eight-attempt append history of workspace-authoritative-branch-resolution at architecture level. Revision 2 bound decision D11 - the single manifest checksum refresh the ACTIVATE commit requires - into the Rollout section as a commit member rather than an activation surface. Revision 3 stated and enumerated the activation arithmetic exactly - TWO activation surfaces (the Ship agent template and the installed Ship mirror), EXACTLY ONE refreshed manifest entry (.github/agents/_ship.agent.md), and THREE commit files once the single manifest file is counted - carried it into the composed-state activation row, extended the rollback unit to all three members, and added an owned fail-closed checksum verification contract in place of the generic verify-workspace command. Revision 4 remediates the independent manifest-contract review by binding that verification to the EXACT INDEX SNAPSHOT the commit records: it asserts the staged set equals exactly the three intended commit members, rejects any unstaged difference for them, hashes the installed Ship mirror from :.github/agents/_ship.agent.md, parses the manifest from :.autoharness/harness-manifest.yaml, rejects missing/extra/duplicate/metadata/checksum divergence, freezes the index between verification and commit (git write-tree recorded, no intervening index mutation, git commit -a and path arguments prohibited), and exits non-zero before the commit is created. The arithmetic is unchanged at two activation surfaces, three commit files, exactly one refreshed Ship entry, rollback across all three. Declared-surface and digest inputs are preserved: the manifest is a commit member, not a third surface, so no surface, consumer or gate count in this plan moves. No task is added and the live manifest is not edited: this is a future implementation contract. Revision 5 closes the terminal review finding that the post-commit tree comparison was described as preventing commit creation, which is impossible: the exact index prechecks (staged-set equality, no unstaged difference, index-read hashing, index-read manifest, total entry adjudication, recorded write-tree identity with re-staging prohibited) all run BEFORE the commit and are what fail closed and leave the commit uncreated; the commit is then created NORMALLY and git rev-parse HEAD^{tree} is compared against the recorded tree immediately afterwards as an ACCEPTANCE adjudication that claims no power to prevent local commit creation and makes no concurrency-proof claim - on mismatch the activation is NOT ACCEPTED and NOT PUBLISHABLE, it blocks the push and every downstream state token, verdict, manifest advance and handoff, and the local commit must be reverted or corrected and the whole contract re-run before proceeding. The arithmetic is unchanged at three commit members. It still carries REMEDIATED-PENDING-REVIEW because it awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
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
| Activation commit | one task, one commit: operation registered, agent template and installed mirror switched to the operation call together — two activation surfaces, three commit members with the single manifest refresh |

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

**ACTIVATE.** One task, one commit across **two activation surfaces**:
removing the interpolated command from the Ship agent template
`templates/agents/_ship.agent.md.tmpl` and the installed mirror
`.github/agents/_ship.agent.md` and replacing it with the operation call.
Leaving the prose form in either file while the operation exists is the P0
unfixed.

**Manifest parity is part of that same atomic unit (decision `D11`).**
`.github/agents/_ship.agent.md` is a **manifest-tracked installed artifact**
with an `artifacts:` entry in `.autoharness/harness-manifest.yaml` recording a
`sha256` of its pre-activation content; `templates/agents/_ship.agent.md.tmpl`
is not tracked — the manifest tracks no template — so the ACTIVATE commit
refreshes **exactly one** manifest entry and contains **exactly three files
while updating two activation surfaces** —
`templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md` and
`.autoharness/harness-manifest.yaml`. In the **same commit** and the **same
rollback unit**, rewrite that checksum to the `sha256` of the installed mirror
*as written by this commit*, then **verify checksum parity** under the
index-bound fail-closed contract below. A commit that replaces the interpolated
command in the mirror without its manifest refresh
leaves the manifest asserting a digest of a file the same commit has already
rewritten — an installed-artifact parity hole in a unit whose whole purpose is
removing an interpolation hazard from that file — and is an **immediate
revert**, not a fixup commit. The refresh is a **commit member, not a third
surface**: it registers no operation, leaves the activation-surface count at
**two**, and changes no surface count stated anywhere in this plan. This binds
a **future implementation commit**; it authorizes no staging-time edit to the
live manifest, and none has occurred.

**Fail-closed verification bound to the exact index snapshot, not generic
`verify-workspace`.** Parity is adjudicated by a verification step this unit
owns, run **after all commit members are staged and before the commit is
created**, and bound to the **exact index snapshot the commit will record**.
The generic `verify-workspace` command is **not** that gate: it reports
whole-workspace install state read from the working tree, it does not
adjudicate a named staged digest against a named `artifacts:` entry, and its
exit status is therefore not a checksum assertion. The owned step:

1. **Asserts the staged set is exactly the intended commit members.**
   `git diff --cached --name-only` equals, as a set, the three members
   enumerated above — `templates/agents/_ship.agent.md.tmpl`,
   `.github/agents/_ship.agent.md` and
   `.autoharness/harness-manifest.yaml`. A **missing** member, an **extra**
   staged path, or a **duplicate** entry each fails.
2. **Rejects any unstaged difference for those members.** `git diff
   --name-only --` restricted to the three members must be empty, and none
   may be untracked. If the working tree differs from the index for any
   commit member, the bytes verified are not the bytes committed, and the
   step fails rather than verifying the wrong content.
3. **Hashes the installed artifact from the index.** Recompute SHA-256 over
   the **staged blob read as `:.github/agents/_ship.agent.md`**
   (`git cat-file -p :.github/agents/_ship.agent.md`) — never a working-tree
   read.
4. **Parses the manifest from the index too**, as
   `:.autoharness/harness-manifest.yaml`, so the entry compared against is
   the entry this commit records rather than any the working tree may hold.
5. **Adjudicates the entry set totally.** There is **exactly one**
   `artifacts:` entry whose literal `path` is
   `.github/agents/_ship.agent.md`; its `primitive` and `template` metadata
   are exactly as required and unchanged by this commit; and its `checksum`
   equals the digest from (3) byte-for-byte. A **missing** entry, an
   **extra** entry — any `artifacts:` entry this commit adds or removes — a
   **duplicate** `path`, a **metadata** divergence, or a **checksum**
   mismatch each fails. This activation installs no new artifact — the
   template stays untracked — so **no new entry is required here**; where a
   future activation does install one, the same step asserts the new entry
   exists with exact `path`, `template` and `primitive` values before
   comparing its checksum.
6. **Records the index identity and forbids re-staging.** Record the index
   identity with `git write-tree` immediately after (5) passes, then create the
   commit with **no intervening index mutation** — no `git add`, `git rm`,
   `git stash`, checkout or restore. `git commit -a` and path arguments to
   `git commit` are **prohibited**, because both re-stage content after
   verification and would commit bytes the gate never adjudicated.
7. **Fails closed before the commit exists.** Steps (1)-(6) all run *before*
   the commit is created, so any failure among them, any unreadable input, or
   any digest mismatch **exits non-zero and the commit is not created**. This
   is the whole of the pre-commit gate.
8. **Adjudicates acceptance after the commit is created.** The commit is then
   created normally; this step does **not** prevent its creation and claims no
   such power. Immediately afterwards, compare `git rev-parse HEAD^{tree}`
   against the tree recorded in (6). On a match the activation is accepted. On
   a **mismatch** the commit records a tree the gate never adjudicated, so the
   activation is **NOT ACCEPTED and NOT PUBLISHABLE**: it **blocks the push**,
   blocks every downstream state token, verdict, manifest advance and handoff
   that would otherwise depend on this activation, and the local commit **must
   be reverted or corrected, and the whole contract re-run, before any further
   step proceeds**.

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
The ACTIVATE commit reverts as a unit across **all three commit members** —
template, installed mirror, and the single refreshed Ship manifest checksum.
Note that rollback restores the interpolated prose form, so a revert re-opens
the P0 and must be treated as a temporary state.

### Verification floor

Both outcome states observed, plus a hyphen-leading name and a
`check-ref-format`-rejected name both observed refused, plus the invalid
`checkout -b --` form asserted absent from every normative procedure.
