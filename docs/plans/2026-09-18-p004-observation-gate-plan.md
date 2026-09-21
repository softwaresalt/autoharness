---
title: "P-004 red-phase gate: three-channel observation over the declared harness set"
description: "Reduced current-state contract for the P-004 gate. Restores the compilation channel the gate had dropped, adds an explicit NO_OBSERVATION failed-precondition state distinct from PASS and from FAIL, and asserts exact set equality between declared and observed outcomes over the shipment's declared harness set. Consumes the installed harness-architect lifecycle from 187-S and the fixed-argv exec primitive from 185-S rather than assuming either. Bootstrap, schema, storage lifecycle, identity and MCP parity are no longer this unit's scope: they moved to the foundations that own them."
doc_type: plan
source: docs/plans/2026-09-18-p004-observation-gate-plan.md
date: 2026-09-18
plan_id: p004-observation-gate
plan_path: docs/plans/2026-09-18-p004-observation-gate-plan.md
plan_role: active
revision: 6
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 was a fresh document replacing the eight-attempt append history of p004-red-phase-precondition-scoping at architecture level. Revision 2 bound decision D11 - the two manifest checksum refreshes the ACTIVATE commit requires - into the Rollout section as commit members rather than activation surfaces. Revision 3 stated and enumerated the activation arithmetic explicitly and added an owned fail-closed checksum verification contract in place of the generic verify-workspace command. Revision 4 remediates the independent manifest-contract review: (a) the ACTIVATE commit now includes the AUTHORITATIVE policy template templates/policies/workflow-policies.md.tmpl alongside its installed mirror, because a commit touching only the mirror leaves the template that regenerates it asserting the old cross-reference and the next install silently reverts the activation - the arithmetic is therefore FIVE activation surfaces, SIX commit files, EXACTLY TWO refreshed manifest entries, and a rollback unit covering all six; and (b) the verification contract is now bound to the EXACT INDEX SNAPSHOT the commit records - it asserts the staged set equals exactly the six intended members, rejects any unstaged difference for them, hashes each installed artifact from :<path>, parses the manifest from :.autoharness/harness-manifest.yaml, rejects missing/extra/duplicate/metadata/checksum divergence, freezes the index between verification and commit (git write-tree recorded, no intervening index mutation, git commit -a and path arguments prohibited), and exits non-zero before the commit is created. Declared-surface and digest inputs are preserved: the manifest is a commit member, not an activation surface, and P-004's text remains unamended. No task is added and the live manifest is not edited: this is a future implementation contract. Revision 5 closes the terminal review finding that the post-commit tree comparison was described as preventing commit creation, which is impossible: the exact index prechecks (staged-set equality, no unstaged difference, index-read hashing, index-read manifest, total entry adjudication, recorded write-tree identity with re-staging prohibited) all run BEFORE the commit and are what fail closed and leave the commit uncreated; the commit is then created NORMALLY and git rev-parse HEAD^{tree} is compared against the recorded tree immediately afterwards as an ACCEPTANCE adjudication that claims no power to prevent local commit creation and makes no concurrency-proof claim - on mismatch the activation is NOT ACCEPTED and NOT PUBLISHABLE, it blocks the push and every downstream state token, verdict, manifest advance and handoff, and the local commit must be reverted or corrected and the whole contract re-run before proceeding. The arithmetic is unchanged at six commit members. Revision 5 also pins the literal repo-relative path of the future gate module as src/autoharness/gates/red_phase.py at every site enumerating the six commit members, matching the existing subject-named snake_case convention of the src/autoharness/gates/ package (shipment_closure.py, bootstrap_grant.py, copilot_review.py, sizing.py, topology.py); no vague 'gate module under src/' reference remains. It carries REMEDIATED-PENDING-REVIEW because it still awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review. Revision 6 corrects the actor-ownership attribution that attempt 07 of the lifecycle plan exposed (finding S14) and that this plan had inherited: the row previously read that 187-S 'installs the actual actor', which is no longer true in either direction. The actor was installed STRUCTURALLY by external commit 07b4be79, that installation is NOT behavioral P-004 satisfaction because the installed skill prescribes pytest while P-004 requires exactly PYTHONPATH=src python -m unittest discover -s tests, and the behavioral correction is now owned by the prerequisite release unit 191-S (feature 185-F). 187-S owns the Ship harness LIFECYCLE ONLY and now itself depends on 191-S. Revision 6 also binds this gate to FRESHNESS-SAFE DIRECT CONSUMPTION of the resolver: the gate calls the Python function resolve_harness_surfaces in src/autoharness/harness_surfaces.py DIRECTLY and RECOMPUTES the resolution at the moment of adjudication, rather than reading any persisted readiness state, cached token or caller-supplied claim - no token authorizes, and a resolution computed earlier in the session is treated as stale. The gate emits the resolution inputs_sha256 digest alongside its own observation record so the adjudication is reproducible. When the resolver returns NO_HARNESS, the gate records NO_OBSERVATION BEFORE ANY COMMAND IS EXECUTED. Revision 6 adds no task and edits no live manifest; it awaits its first independent plan-review attempt and Stage asserts no PASS."
resolver_module: src/autoharness/harness_surfaces.py
resolver_consumption: direct-python-call-recomputed-at-adjudication
resolver_state_is_persisted: false
no_harness_maps_to: NO_OBSERVATION-before-command-execution
actor_conformance_owner_shipment: 191-S
actor_installation_is_structural_only: true
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-p004-observation-gate-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 4
source_stash_ids:
  - 76EBDE6D
feature_id: 168-F
shipment_id: 176-S
unit_role: reduced-defect-unit
supersedes_plan: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
depends_on_shipments:
  - 191-S
  - 185-S
  - 187-S
depends_on_shipments_note: "191-S is a TRANSITIVE prerequisite reached through 187-S, which now declares an explicit dependency on it. Shipment record 176-S records DIRECT edges only (185-S, 187-S) and is deliberately NOT given a redundant 176-S -> 191-S edge; the ordering is already enforced. This plan lists 191-S because the plan-level statement is about what must be true before this unit is buildable, not about the shape of the shipment graph."
task_reharvest_gate: 187-S
requires_plan_hardening: true
hardening_rationale: "Changes a policy gate that governs every shipment execution, and depends on two foundations whose surfaces are not yet built."
tags:
  - defect-unit
  - p004
  - gate
  - reduced-scope
---

# P-004 red-phase gate: three-channel observation

## Reduction

The previous revision of this unit carried its own bootstrap, its own schema,
its own storage lifecycle, its own identity model and its own MCP parity
surface. Attempt 08 recorded one P0 and eleven P1 findings across those
families, most of which were the same missing producers four units were each
inventing separately.

This revision keeps **one contract** and moves the rest to the foundations that
own them:

| Previously in scope | Now owned by |
|---|---|
| harness-architect bootstrap / assumed skill | `191-S` (feature `185-F`) - corrects the actor to P-004 BEHAVIOURAL conformance; the actor itself was already installed structurally by external commit `07b4be79` |
| Ship pre-task harness lifecycle and the surface resolver | `187-S` (feature `181-F`) - lifecycle only; it does NOT install or correct the actor |
| fixed-argv command execution | `185-S` — PR-3 exec primitive |
| MCP parity for the gate | `184-S` — one registry, two transports |
| atomic record write | `185-S` — PR-1 |
| result identity and correlation | folded into the operation result model in `184-S` |

What remains is the defect that opened stash `76EBDE6D`.

## The defect

Live policy P-004's precondition already requires both:

```text
python -m py_compile src/autoharness/cli.py   → exit 0
python -m unittest discover                    → exit non-zero
```

and its postcondition records `Compilation: PASS` and `Red Phase: CONFIRMED`.

The implemented gate observes only the test-run channel. A file that fails to
compile produces a non-zero test run, which the gate reads as a satisfied red
phase. **A compilation failure is indistinguishable from a red test.** That is
a regression against live policy text, not a gap in the policy — so the remedy
restores an observation, and P-004's text is not amended.

## Contract

The gate observes **three channels** and classifies **totally**:

| Channel | Observation |
|---|---|
| Compilation | `py_compile` over the declared harness set exits 0 |
| Collection | every declared test module imports with zero loader errors and zero `_FailedTest` placeholders |
| Outcomes | observed outcome set equals declared outcome set, by exact set equality |

Declared outcomes admit two disjoint classes: **expected-red** and
**expected-green-characterization**. A test may be in exactly one.

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `RED_CONFIRMED` — compilation clean, collection clean, observed set equals declared set |
| Fail state | `RED_NOT_CONFIRMED` — all three channels observed, sets unequal |
| Third state | `NO_OBSERVATION` — a channel could not be observed (compilation failed, a module failed to import, or `HARNESS_READY` was not reached). **A failed precondition, never a pass and never a red.** |
| Producer | `187-S`'s `HARNESS_READY` state; `185-S`'s PR-3 exec primitive |
| Consumer | Ship's task-start sequence |
| Activation commit | one task, one commit: `src/autoharness/gates/red_phase.py`, the policy template and its installed mirror, the Ship template and its installed mirror — five activation surfaces, six commit members with the manifest refresh |

`RED_CONFIRMED` is reachable: a shipment declaring a harness set of expected-red
tests that compile and import satisfies all three channels.

The load-bearing distinction is that `NO_OBSERVATION` is **not** `RED_CONFIRMED`.
The current defect is exactly the collapse of these two states.

## Rollout

**PREPARE (inert).** Three-channel observer and total classifier built and
tested while the live gate continues its single-channel behaviour.

**VERIFY.** Each of the three states observed reachable, including a compilation
failure yielding `NO_OBSERVATION` rather than `RED_CONFIRMED`.

**ACTIVATE.** One task, one commit across **five activation surfaces**: the
the gate module **`src/autoharness/gates/red_phase.py`**, the **authoritative**
policy template
`templates/policies/workflow-policies.md.tmpl` and its installed mirror
`.github/policies/workflow-policies.md`, which together carry the policy
cross-reference, and the Ship agent template
`templates/agents/_ship.agent.md.tmpl` with its installed mirror
`.github/agents/_ship.agent.md` — all move together. The policy template is
the authoritative surface: editing the installed policy mirror without it
would leave the template that regenerates that mirror asserting the old
cross-reference, so the next install would silently revert the activation.

**Manifest parity is part of that same atomic unit (decision `D11`).** Two of
the activation surfaces are **manifest-tracked installed artifacts** —
`.github/policies/workflow-policies.md`, which carries the policy
cross-reference, and `.github/agents/_ship.agent.md`, the installed mirror.
Each has an `artifacts:` entry in `.autoharness/harness-manifest.yaml`
recording a `sha256` of its pre-activation content. The gate module
`src/autoharness/gates/red_phase.py` is not manifest-tracked, and the
manifest tracks no template — neither
`templates/policies/workflow-policies.md.tmpl` nor
`templates/agents/_ship.agent.md.tmpl` — so the ACTIVATE commit refreshes
**exactly two** manifest entries and contains
**exactly six files while updating five activation surfaces** —
`src/autoharness/gates/red_phase.py`,
`templates/policies/workflow-policies.md.tmpl`,
`.github/policies/workflow-policies.md`,
`templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md` and
`.autoharness/harness-manifest.yaml`. In the **same commit** and the **same
rollback unit**, rewrite each of those two checksums to
the `sha256` of the installed file *as written by this commit*, then **verify
checksum parity** under the index-bound fail-closed contract below. A commit
that edits
either installed surface without its manifest refresh leaves the manifest
asserting a digest of a file the same commit has already rewritten — an
installed-artifact parity hole — and is an **immediate revert**, not a fixup
commit. The manifest refreshes are **commit members, not activation
surfaces**: they add no channel, no state, no gate behaviour and no policy
text, the activation-surface count stays **five**, and they change no surface
count stated anywhere in this plan. This is a **future implementation
contract**; it authorizes no staging-time edit to the live manifest, and none
has occurred. It is also not an amendment of P-004's text, which remains out
of scope below: refreshing a checksum records what a permitted edit did, it
does not add a permitted edit, and transcribing the same cross-reference into
the policy template and its mirror is the one permitted edit, applied to both
halves of an authoritative/mirror pair rather than to one.

**Fail-closed verification bound to the exact index snapshot, not generic
`verify-workspace`.** Parity is adjudicated by a verification step this unit
owns, run **after all commit members are staged and before the commit is
created**, and bound to the **exact index snapshot the commit will record**.
The generic `verify-workspace` command is **not** that gate: it reports
whole-workspace install state read from the working tree, it does not
adjudicate a named staged digest against a named `artifacts:` entry, and its
exit status is therefore not a checksum assertion. The owned step:

1. **Asserts the staged set is exactly the intended commit members.**
   `git diff --cached --name-only` equals, as a set, the six members
   enumerated above — `src/autoharness/gates/red_phase.py`, the two templates,
   the two installed
   surfaces and `.autoharness/harness-manifest.yaml`. A **missing** member,
   an **extra** staged path, or a **duplicate** entry each fails.
2. **Rejects any unstaged difference for those members.** `git diff
   --name-only --` restricted to the six members must be empty, and none may
   be untracked. If the working tree differs from the index for any commit
   member, the bytes verified are not the bytes committed, and the step fails
   rather than verifying the wrong content.
3. **Hashes the installed artifacts from the index.** For each of the two
   touched installed artifacts, recompute SHA-256 over the **staged blob read
   as `:<path>`** (`git cat-file -p :.github/policies/workflow-policies.md`,
   `git cat-file -p :.github/agents/_ship.agent.md`) — never a working-tree
   read.
4. **Parses the manifest from the index too**, as
   `:.autoharness/harness-manifest.yaml`, so the entries compared against are
   the entries this commit records rather than any the working tree may hold.
5. **Adjudicates the entry set totally.** For each touched installed artifact
   there is **exactly one** `artifacts:` entry whose literal `path` matches;
   its `primitive` and `template` metadata are exactly as required and
   unchanged by this commit; and its `checksum` equals the digest from (3)
   byte-for-byte. A **missing** entry, an **extra** entry — any `artifacts:`
   entry this commit adds or removes — a **duplicate** `path`, a **metadata**
   divergence, or a **checksum** mismatch each fails. This activation installs
   no new artifact — `src/autoharness/gates/red_phase.py` and both templates
   stay untracked — so
   **no new entry is required here**; where a future activation does install
   one, the same step asserts the new entry exists with exact `path`,
   `template` and `primitive` values before comparing its checksum.
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

Task-level decomposition of this unit is **deliberately deferred** until
`187-S` has installed the harness lifecycle and `185-S` has fixed the exec
primitive's signature. Naming a producer before it exists is the precise defect
this redesign eliminates; harvesting tasks against an assumed exec signature
would reintroduce it. The existing tasks under `168-F` remain queued and are
re-sliced against the delivered foundation surfaces, not against this document.

## Out of scope

* Amending policy P-004's text.
* Any waiver, force flag or operator policy edit as a bootstrap path — all
  three were evaluated and rejected in the architecture decision.
* Building or correcting the harness-architect skill. The actor is already installed structurally by external commit `07b4be79`; making it BEHAVIOURALLY P-004 conformant is owned by `191-S` (feature `185-F`), and the Ship harness lifecycle is owned by `187-S` (feature `181-F`). Neither is this unit's work.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Restoring the compilation channel blocks shipments that pass today | Intended: those shipments are passing on an unobserved precondition. The transition surfaces as `NO_OBSERVATION` with a named channel rather than a silent failure. |
| R2 | Collection cleanliness is stricter than current practice | It is the same rule the foundation plans apply to their own RED modules, so the portfolio is internally consistent. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Can a compilation failure still read as a red phase? | Not after this change. Compilation is observed as its own channel, and a failure yields `NO_OBSERVATION`. The current defect is precisely the collapse of that state into `RED_CONFIRMED`. |
| H2 | Is a non-zero test-run exit sufficient evidence of a red phase? | No. It is satisfied by an import error, a collection error, a compilation failure, or a genuine red test. Only exact set equality between declared and observed outcomes distinguishes them. |
| H3 | Can a test be in both declared outcome classes? | No. Expected-red and expected-green-characterization are disjoint, and a test in both would make set equality unfalsifiable. |
| H4 | What if `HARNESS_READY` is never reached? | `NO_OBSERVATION`. The gate has not observed a pass, so it does not report one. This is why `187-S` is a hard predecessor rather than an assumption. |
| H5 | Does this unit need to change P-004's text? | No. The live precondition already requires both channels; the implementation regressed against it. Editing the policy to match the implementation would ratify the defect. |
| H6 | Why is task harvest deferred? | Because the exec primitive's signature is the gate's calling convention, and the harness lifecycle's state is its precondition. Harvesting against assumed shapes is the exact defect this redesign removes. |
| H7 | Can the policy cross-reference be activated in the installed mirror alone? | No, and treating the mirror as the whole surface was a defect. `templates/policies/workflow-policies.md.tmpl` is the **authoritative** half: it regenerates the installed policy, so a commit touching only the mirror leaves the template asserting the old cross-reference and the next install silently reverts the activation. Both halves of both authoritative/mirror pairs move in the one commit — five activation surfaces, six commit members. |
| H8 | Could the verification pass on bytes the commit does not record? | No, and this is why the gate is bound to the index rather than the working tree. It asserts the staged set is exactly the six intended members, rejects any unstaged difference for them, hashes each installed artifact from `:<path>`, parses the manifest from `:.autoharness/harness-manifest.yaml`, then records the index identity — `git write-tree`, no intervening `git add`/`git rm`/`git stash`/checkout, `git commit -a` and path arguments prohibited. Those prechecks run before the commit exists and are what make it fail closed. The post-commit `HEAD^{tree}` comparison is an **acceptance** check, not a prevention one: it cannot stop a local commit being created, so on mismatch the activation is simply not accepted or publishable and must be reverted or corrected. A working-tree-read gate would adjudicate content the commit never records. |

### Blast radius

A policy gate on every shipment execution, plus **two** authoritative/mirror
pairs — the policy template with its installed mirror and the Ship agent
template with its installed mirror — and two refreshed manifest checksums
carried as commit members of the same activation. Restoring the compilation
channel will block shipments that currently pass, which is intended — they are
passing on an unobserved precondition.

### Rollback

PREPARE is inert; the live single-channel gate continues until activation. The
ACTIVATE commit reverts as a unit across **all six commit members** —
`src/autoharness/gates/red_phase.py`, the policy template, the installed
policy mirror, the Ship template, the installed Ship mirror, and both
manifest checksums in the single manifest file.

### Verification floor

All three states observed reachable, including a compilation failure yielding
`NO_OBSERVATION` rather than `RED_CONFIRMED`. A suite that never observes
`NO_OBSERVATION` has not verified the fix.
