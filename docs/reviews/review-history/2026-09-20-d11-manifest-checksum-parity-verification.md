---
title: "Targeted verification — decision D11 manifest checksum-parity changes across the Push B portfolio"
description: "Immutable targeted-verification artifact recording the independent verification of the decision D11 manifest checksum-parity remediation applied across the bounded Push B portfolio of PR #457, against working-tree content on branch chore/stage-176-s-workflow-defects with committed base a192e50c. Six current-HEAD Copilot review threads (2, 3, 4, 5, 6 and 7) reported the same false contract in six different authoritative carriers: an activation that creates or modifies a manifest-tracked installed artifact while declaring an exact commit surface that omits the .autoharness/harness-manifest.yaml entry and checksum that edit requires. Rather than patching six carriers independently, the invariant is stated ONCE as decision D11 and bound at each affected activation with its own exactly-derived entry count. This artifact records the independent re-derivation of every entry count against the live 72-entry manifest, the confirmation that templates/ is not tracked at all (so a template-plus-mirror pair refreshes one entry and not two), the confirmation that .github/workflows/ci.yml and .mcp.json are not tracked, the confirmation that NO declared_surface_count anywhere in the portfolio moved, and the bounded sweep for equivalent live assertions left uncorrected in other authoritative carriers. RESULT: all counts correct, no surface arithmetic disturbed, no live manifest edit performed, and the deliberate non-coverage of 181-S and 185-S recorded as reasoned negative findings rather than oversights. Zero P0, zero P1, zero P2; one P3 observation."
doc_type: review
source: docs/reviews/review-history/2026-09-20-d11-manifest-checksum-parity-verification.md
date: 2026-09-20
review_artifact_role: targeted-verification
review_artifact_immutable: true
verification_scope: cross-cutting
review_terminal: true
terminal_designation: terminal-for-push-b
bounded_convergence_decision: docs/decisions/2026-09-20-pr457-bounded-review-convergence-deliberation.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 4
decision_clause: D11
reviewed_content_head: a192e50c
reviewed_content_state: working-tree-uncommitted-at-review-time
reviewed_branch: chore/stage-176-s-workflow-defects
addresses_review_threads: [2, 3, 4, 5, 6, 7]
manifest_path: .autoharness/harness-manifest.yaml
manifest_artifact_count: 72
manifest_written_this_session: false
gate_result: PASS
decision: PROCEED
verdict_is_pass: true
p0_open: 0
p1_open: 0
p2_open: 0
p3_open: 1
open_findings: [P1-OBS]
blocking_findings: []
dispatch_mode: single-agent-declared-degradation
backlogit_index_state: "INDEX_SYNC_OK — 1445 artifacts indexed at session start"
degraded_capabilities:
  - capability: agent-engram
    state: circuit-open
  - capability: agent-intercom
    state: unavailable
  - capability: graphtor-docs
    state: unavailable
tags:
  - "targeted-verification"
  - "manifest-parity"
  - "terminal"
  - "portfolio-2026-09-18"
---

# Targeted verification — decision `D11` manifest checksum-parity changes

## The defect class

Six of the eight current-HEAD Copilot threads on PR #457 are the same defect
wearing six different labels. Each names an activation that **creates or
modifies a manifest-tracked installed artifact** while declaring an exact commit
surface — "two files, nothing else", "four declared surfaces" — that **omits**
the `.autoharness/harness-manifest.yaml` entry and checksum the edit requires.

This is a **false contract**, not a missing nicety. An executor obeying such a
contract literally lands a commit whose manifest records a checksum for a file
that same commit just changed, and the workspace's own installed-state record
becomes wrong at the moment of activation. Worse, the rollback unit is torn: the
revert restores the artifact but not the record, or the record but not the
artifact.

## The remediation shape

The invariant is stated **once**, at the portfolio's governing decision, as
`D11`:

> Any activation that **creates or modifies** an artifact tracked in
> `.autoharness/harness-manifest.yaml` MUST, **in the same commit and the same
> rollback unit**, update or register that artifact's manifest entry (`path`,
> `primitive`, `template`, `checksum`) and then **verify checksum parity**.

Each affected activation then binds `D11` with **its own exactly-derived entry
count**. Stating the invariant once and binding it per-unit is what prevents six
independently drifting restatements — which is the failure mode that produced
six threads from one defect in the first place.

## Independent re-derivation against the live manifest

Every count below was derived by parsing `.autoharness/harness-manifest.yaml`
directly. **None was accepted from a plan's own claim.**

**Baseline facts established first:**

| Fact | Value | Why it matters |
|---|---|---|
| Total `artifacts:` entries | **72** | The denominator for every claim below |
| Tracked paths under `templates/` | **0** | A template-plus-mirror pair refreshes **one** entry, not two — this single fact corrects half the naive counts |
| `.github/workflows/ci.yml` tracked | **no** | CI edits trigger no `D11` obligation |
| `.mcp.json` tracked | **no** | Transport config edits trigger no `D11` obligation |
| `.github/skills/*/SKILL.md` entries | 18, none of them `harness-architect` | Confirms thread 5 is a **registration**, not a refresh |

**Per-carrier verification:**

| Thread | Carrier | Claimed entries | Tracked paths verified | Result |
|---|---|---|---|---|
| 2 | `169.015-T` / `169-F` / `177-S` / post-claim plan rev 8 | **2** | `.github/policies/workflow-policies.md` ✓, `.github/agents/_ship.agent.md` ✓ | **correct** — 4 surfaces are 2 authoritative/mirror pairs, 5 files in the commit |
| 3 | `180.010-T` / `180-F` / checkpoint-authority plan rev 2 | **2** | `.github/skills/harvest/SKILL.md` ✓, `.github/skills/plan-review/SKILL.md` ✓ | **correct** — 6 files, 4 consumers, 2 entries |
| 4 | `181.005-T` / `181-F` / `187-S` / lifecycle plan rev 7 | **1** | `.github/agents/_ship.agent.md` ✓ | **correct** — template untracked, so one entry not two; 3 files, 2 surfaces |
| 5 | `182.003-T` / `182-F` / `188-S` / bootstrap plan rev 4 | **1 (register)** | `.github/skills/harness-architect/SKILL.md` **absent from the manifest** | **correct** — this is a registration of a new entry, not a refresh of an existing one |
| 6 | operation-substrate-transport plan rev 2 | **2** | `.github/agents/_ship.agent.md` ✓, `.github/agents/_stage.agent.md` ✓ | **correct** — `.mcp.json` correctly excluded as untracked |
| 7 | p004-observation-gate plan rev 2 | **2** | `.github/policies/workflow-policies.md` ✓, `.github/agents/_ship.agent.md` ✓ | **correct** |
| — | branch-ensure-operation plan rev 2 | **1** | tracked ✓ | **correct** (swept, not threaded) |
| — | review-authority-foundation plan rev 2 | **2** | tracked ✓ | **correct** (swept, not threaded) |

Every claimed path is genuinely tracked; every claimed count matches the
manifest; no carrier over-claims a count that would license touching an entry
outside its own unit.

## The surface-arithmetic invariant (the check that mattered most)

The most dangerous way to remediate this class is to add the manifest as an
extra **declared surface**. That would silently change digest inputs and gate
arithmetic across the portfolio — a P1 in at least `177-S`, where
`declared_surface_count = 4` and `resolved_surface_count` (0 at readiness, 4 at
confirmation) are inputs to `169.017-T`'s CCD/v1 digest and the F1–F5 binding.

**Verified: no `declared_surface_count` anywhere in the portfolio moved.** The
mechanism that makes this sound is stated in every carrier rather than assumed:
the manifest refresh is a **commit member, not a declared surface**, and
`169-F`'s enumeration rule already excludes `.autoharness/` — so the exclusion
follows from a rule in force, not from an exception carved for this remediation.
Confirmed unchanged at revision 8: `declared_surface_count` 4, F2's seven digest
inputs, F3 = 0, and `169.016-T`'s enumeration of exactly four surfaces.

`187-S` states the same distinction in its own vocabulary — *"EXACTLY TWO
SURFACES … AND, AS A COMMIT MEMBER RATHER THAN A THIRD SURFACE, THE SINGLE
entry"* — and concludes *"THE COMMIT THEREFORE CONTAINS THREE FILES AND CHANGES
TWO SURFACES."*

## Rollback and verification semantics

Checked in every carrier, uniformly present:

1. The entry is refreshed **in the same commit**.
2. The entry is restored **in the same rollback unit** — a single-commit revert
   restores artifact and record together, never one without the other.
3. Parity is **verified by re-digesting the file as written by that commit**,
   not by trusting the value written.
4. Where a separate confirmation task exists (`182.004-T`, `169.016-T`), it
   **re-derives** parity independently and never writes; mismatch is fail-closed.

`169.016-T` was checked specifically for the emitter-that-mutates hazard: it
re-derives and never writes, mismatch yields `STATUS_CONTRACT_DIVERGENT`, and an
unreadable input yields `NOT_OBSERVED` / `digest_input_unreadable`.

## Bounded sweep for equivalent live assertions

The changed portfolio (merge-base `363a5f34` → working tree, ~280 changed files,
119 changed `.backlogit/queue/*.md`) was swept for activations declaring exact
commit surfaces over manifest-tracked artifacts. Eighteen plan frontmatters were
read for `plan_role`; the six superseded `2026-09-17-*` plans were excluded as
out of bounds per the operator's instruction not to expand into
historical/superseded artifacts.

**Deliberate non-coverage, recorded as reasoned negative findings rather than
oversights** — this distinction is the point of recording them at all:

| Unit | Why `D11` is not bound | Verified |
|---|---|---|
| `181-S` (safe-close-conformance) | Its activation touches CI and documentation only; `.github/workflows/ci.yml` is **not** a tracked artifact, so no `D11` obligation arises | yes — absent from the 72 entries |
| `185-S` (safe-operation-primitives) | Has **no** ACTIVATE step at all; there is no activation to bind | yes |
| `168-F` / `170-F` / `172-F` pre-reslice task records | Superseded by the reslice; editing them would expand into historical artifacts the bounding decision excludes | yes — deliberately not edited |

The decision's `D11` carries an explicit coverage/inheritance clause naming
which units state `D11` at plan level (`188-S` 1 registration, `177-S` 2,
`187-S` 1, `186-S` 2, `180-S` 2, `184-S` 2, `176-S` 2) and why the rest are
uncovered, so a future reader cannot mistake absence for omission.

## No live manifest edit

`D11` binds **future implementation contracts**. `.autoharness/harness-manifest.yaml`
was read repeatedly during this verification and **never written**. Every carrier
states this explicitly. Confirmed against the working tree: the manifest is not
among the modified files.

## Findings

### P1-OBS — P3: `D11`'s coverage clause is prose, not a mechanical check

The coverage/inheritance clause enumerating which units bind `D11` is
authoritative prose in the decision. Nothing mechanically verifies that a future
activation touching a tracked artifact has bound it — a new plan could omit the
binding and no validator would notice. This is the same class of gap `D11`
itself exists to close one level down. Recorded as a non-blocking observation
for a future hardening pass; **no remediation proposed**, because introducing a
validator here would exceed the bounded Push B surface.

## Result

**PASS — PROCEED.** Zero P0, zero P1, zero P2; one P3 observation (P1-OBS).

All six threaded carriers and two additional swept carriers bind `D11` with
correctly derived entry counts; no surface arithmetic was disturbed; rollback
units are whole; and the live manifest is untouched.

## Scope statement

This verification mutated no plan, task, feature, shipment or stash record, read
`.autoharness/harness-manifest.yaml` without writing it, and performed no GitHub
interaction.
