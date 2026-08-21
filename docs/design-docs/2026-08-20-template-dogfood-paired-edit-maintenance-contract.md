---
title: "Template/Dogfood Paired-Edit Maintenance Contract (137-F / 145-S)"
feature: 137-F
shipment: 145-S
tasks:
  - 137.002-T
  - 137.001-T
status: implemented
spike: docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md
stash_id: 6D62077C
---

# Template/Dogfood Paired-Edit Maintenance Contract

## Purpose

State, as a durable and enforced contract, a maintenance practice that
previously existed only informally: which `templates/` <-> `.github/` pairs
are reproduced mechanically by `autoharness.verify_workspace._render_template`,
and which pairs are instead **paired-edit maintained** — kept consistent by a
human/agent author editing both sides in the same change, not by rendering.

This document does not change any agent behaviour. It records and enforces
the status quo that the spike below measured.

Source of truth for every measurement cited here:
`docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md` (stash
`6D62077C`). No new measurements are invented in this document; every claim
below is traceable to that spike's findings F1-F5.

## The two categories

1. **Mechanically rendered.** `_render_template` performs pure `{{VAR}}`
   string substitution (spike F1) and, for these pairs, that substitution
   alone reproduces the dogfood file byte-for-byte once LF-normalized. No
   paired-edit discipline is required: editing the template and re-rendering
   is sufficient to keep the dogfood copy correct.
2. **Paired-edit maintained.** For these pairs, `_render_template` output does
   NOT achieve byte identity with the dogfood copy — not because rendering is
   broken, but because the two files are substantially independently-authored
   documents sharing a common ancestor and section structure (spike F3). Their
   consistency is instead maintained by an editorial obligation (see below),
   verified by marker-presence-plus-manifest-checksum contract tests rather
   than whole-file byte comparison.

## Current inventory (eight pairs)

### Mechanically rendered (4)

| # | Pair | Template | Dogfood |
|---|---|---|---|
| 1 | role-enforcement | `templates/instructions/role-enforcement.instructions.md.tmpl` | `.github/instructions/role-enforcement.instructions.md` |
| 2 | circuit-breaker | `templates/instructions/circuit-breaker.instructions.md.tmpl` | `.github/instructions/circuit-breaker.instructions.md` |
| 3 | copilot-code-review | `templates/instructions/copilot-code-review.instructions.md.tmpl` | `.github/instructions/copilot-code-review.instructions.md` |
| 4 | feature-flow-dark | `templates/prompts/feature-flow-dark.prompt.md.tmpl` | `.github/prompts/feature-flow-dark.prompt.md` |

These four are asserted at full byte granularity in
`tests/test_scope_containment_policy_contract.py::test_clean_pairs_are_byte_identical_via_render_template`.

### Paired-edit maintained (4)

| # | Pair | Template | Dogfood |
|---|---|---|---|
| 5 | `_ship` agent | `templates/agents/_ship.agent.md.tmpl` | `.github/agents/_ship.agent.md` |
| 6 | `_stage` agent | `templates/agents/_stage.agent.md.tmpl` | `.github/agents/_stage.agent.md` |
| 7 | `_orchestrator` agent | `templates/agents/_orchestrator.agent.md.tmpl` | `.github/agents/_orchestrator.agent.md` |
| 8 | `github-pr-automation` instructions | `templates/instructions/github-pr-automation.instructions.md.tmpl` | `.github/instructions/github-pr-automation.instructions.md` |

These four are asserted by marker presence (both sides) plus a
`harness-manifest.yaml` checksum match against the actual committed dogfood
bytes, in the same test module (`_DIVERGENT_MARKER_ONLY_PAIRS`), and their
membership is pinned by
`tests/test_scope_containment_policy_contract.py::test_divergent_pair_membership_is_pinned_and_annotated`
(137.001-T) so a fifth pair silently joining this set fails the test by name
rather than passing unnoticed.

## Per-pair cause taxonomy (spike F4, measured evidence)

Three distinct, non-exclusive causes explain the divergence. Citing the
measured evidence rather than restating it from memory:

1. **Install-time conditional content** (the three agent pairs: `_ship`,
   `_stage`, `_orchestrator`). Templates carry `backlog-md` and "no backlog
   tool" conditional branches that the backlogit-installed dogfood copies
   correctly omit (spike F4(1) counts: `_ship` 2 and 2 branches; `_stage` 2
   and 1; `_orchestrator` 0 and 1). This is real, by design, and not
   reproducible by plain substitution — `_render_template` has no
   conditional-block handling (spike F1).
2. **Semantic prose drift** (present in all four pairs; the *dominant* cause
   for `github-pr-automation`, which spike F2/F4(2) measured with **zero**
   `backlog-md` / "no backlog tool" markers on either side yet still a 725-byte
   (1.9%) delta — conditional content cannot explain it). Diffing shows
   genuine normative drift where the dogfood copy is the stale side (spike
   F4(2) examples: "operator-visible review data" vs "blocking data";
   "fresh" local review readiness vs merely "one").
3. **Variable-derivation coverage gap** (spike F5). `_derive_template_variables`
   does not cover every variable a template uses, so rendering leaves
   unresolved `{{...}}` placeholders (e.g. `{{ESCALATION_FAMILY}}`,
   `{{DEFAULT_BRANCH}}`, `{{FORMAT_CHECK_COMMAND}}` — spike F5 table). This
   cause is a genuine, separate installation-correctness defect, captured as
   its own deferred stash entry per P-021 C1, and is **not** fixed by this
   contract or this shipment.

Measured magnitude, per spike F2/F3 (bidirectional, not a subset relationship
— pure conditional stripping would yield ~0 dogfood lines absent from the
rendered template; instead, for `_ship`, 73% of the dogfood file's non-empty
lines are absent from the rendered template **and** 79% of the rendered
template's non-empty lines are absent from the dogfood file):

| Pair | template bytes | dogfood bytes | delta % | dogfood lines absent from rendered |
|---|---:|---:|---:|---:|
| `_ship` | 95,669 | 68,360 | 28.5% | 508/692 (73%) |
| `_stage` | 64,859 | 41,420 | 36.1% | 319/467 (68%) |
| `_orchestrator` | 53,147 | 35,954 | 32.4% | 87/216 (40%) |
| `github-pr-automation` | 38,396 | 37,671 | 1.9% | 54/635 (8.5%) |

## Author obligation

Editing either side of a paired-edit maintained pair obliges the author to:

1. **Consider the other side in the same change.** A change to the template
   side does not automatically propagate; a change to the dogfood side is not
   automatically reflected upstream. The author must decide, explicitly, per
   change, whether the other side needs a corresponding edit — not assume
   either silence or automatic sync.
2. **Refresh the `harness-manifest.yaml` checksum** for the mirrored dogfood
   file whenever its committed bytes change, computed from the LF-normalized
   committed git blob (never a raw working-tree read) — because the bytes
   legitimately changed, not to silence an unrelated drift finding (see
   `docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`).

This obligation applies regardless of which side (template or dogfood) is
edited first, and regardless of task/shipment boundaries.

## Recorded exception, not a goal

Paired-edit-maintained status is a **recorded exception**, not a design goal.
The drift it tolerates — install-time conditional content aside — is
**technical debt with an owner**, specifically the semantic prose drift (cause
2) and the variable-coverage gap (cause 3). It is not a design choice to be
extended casually: a new pair should default to mechanically rendered unless
a change of this same rigor (spike-then-plan) demonstrates it cannot be.
Reconciling the existing drift is explicitly out of scope for this contract
document and is not authorized by its existence; see the spike's own
"Explicitly out of scope" section.

## Traceability

* Spike: `docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md`
  (stash `6D62077C`).
* Plan: `docs/plans/2026-08-20-template-dogfood-paired-edit-contract-plan.md`.
* Pinning test: `tests/test_scope_containment_policy_contract.py` (137.001-T).
* Every measurement in this document reproduces a spike finding (F1-F5); none
  is a new measurement.
