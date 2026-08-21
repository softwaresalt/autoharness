---
title: "Plan hardening - verify-workspace template-variable derivation"
date: 2026-08-21
plan: docs/plans/2026-08-21-verify-workspace-variable-derivation-plan.md
stash_id: 8FA8FC22
deliberation: ".backlogit/queue/023-DL.md"
outcome: HARDENED
amendments: [B1, B2, B3, B4, B8]
---

# Plan Hardening - verify-workspace variable derivation

Date: 2026-08-21
Agent: Stage (P-006 hardening gate)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Why hardening applies

`requires_plan_hardening: yes`. Signals present: Python CLI / install-correctness
surface; config round-trip through `templates/harness-config.yaml.tmpl`; multiple
template families (agents, instructions, foundation, startup scripts); and a live
P-021/137-F byte-identity contract test that consumes the exact function being
changed.

## H1 - The change can break the parity contract that motivated its own discovery

**Risk.** `tests/test_scope_containment_policy_contract.py` imports
`_derive_template_variables` and `_render_template` at module level and asserts
BYTE IDENTITY for four clean template/dogfood pairs. Resolving a previously
unresolved variable that occurs in a clean pair changes that pair's render and
breaks the assertion. Discovering this mid-implementation invites the worst
available response: editing the dogfood copy to match, silently rewriting live
agent policy under cover of a refactor - the exact failure mode P-021 exists to
prevent and which the originating spike refused to enter.

**Hardening.** Task 0 AC0b already forces the intersection to be MEASURED FIRST.
Strengthen: **AMENDMENT B1** - if the intersection is NON-EMPTY, the affected
derivation task must STOP and return to Stage rather than proceeding, unless the
divergence is confined to a variable whose correct rendered value is provably
identical to the literal text currently in the dogfood copy (a pure
placeholder-to-same-literal substitution). Any other divergence is a normative
edit and re-enters P-021 capture.

## H2 - Raw escalation slots must derive to empty, and a test must prove it

**Risk.** The single highest-consequence error available in this work is
resolving `{{STAGE_ESCALATION_*}}` / `{{SHIP_ESCALATION_*}}` /
`{{LEGACY_ESCALATION_*}}` to the collapsed `{{ESCALATION_*}}` value. That copies
a nested-only override into the flat block on re-render and reproduces the H2
flat+nested ambiguity that PR #316 round 3 already fixed once. It would also
corrupt the escalation route THIS agent resolves at session start.

**Hardening.** Constraint C3 plus AC1b already require a test. Strengthen:
**AMENDMENT B2** - the test must be a NEGATIVE assertion as well as a positive
one: given a workspace with a nested `stage.escalation` override and an unset
flat `escalation`, assert the rendered flat block's three sub-fields are the
EMPTY STRING and specifically NOT equal to the nested override's values. A
positive-only test would pass under the defect in the common case where both
happen to match.

## H3 - Round-trip loss is silent and only manifests on the NEXT install

**Risk.** Per `docs/compound/2026-05-05-harness-config-round-trip-requirement.md`,
a variable that resolves but is not written back to `harness-config.yaml.tmpl`
reverts to a default on the next install/tune - a defect that is invisible in
this shipment's own verification and surfaces later as mysterious config drift.
45 of the 83 occurrences are in the staged `config.yaml`, so this is the dominant
surface, not an edge case.

**Hardening.** **AMENDMENT B3** - add an explicit round-trip acceptance test to
Task 2: render `.autoharness/config.yaml` from the template using the derived
variables, re-parse it, re-derive variables from the re-parsed config, and assert
the second derivation equals the first (idempotent round-trip). This catches
write-back gaps mechanically instead of by table inspection.

## H4 - Structural block rendering through pure string substitution

**Risk.** `*_YAML`, `*_SH`, `*_PS1` block variables are multi-line structured
values injected by a substitution engine that knows nothing about indentation.
A wrong indent produces a file that still "renders" but no longer parses -
and `_find_unresolved_placeholders` would report SUCCESS because no `{{...}}`
remains. The zero-unresolved headline metric can therefore be satisfied by a
broken render.

**Hardening.** AC2b/AC2c already require parse-level assertions. Confirmed
necessary and sufficient, and elevated: **the zero-unresolved criterion (AC3b)
MUST NOT be reported as met unless AC2b and AC2c also hold.** Zero-unresolved
alone is not evidence of a correct render.

## H5 - Scope creep into semantic prose drift

**Risk.** The originating spike measured ~1,200 lines of bidirectional normative
drift and explicitly refused it. Anyone working in these files will see it.

**Hardening.** Already covered by Non-goals and 023-DL R6. Confirmed sufficient;
B1 additionally gives a concrete stop trigger rather than only a prohibition.

## H6 - "Never invent a value"

**Risk.** `LINT_COMMAND` derives to `""` and `FORMAT_CHECK_COMMAND` is absent,
while the installed dogfood copies contain real literals. The tempting fix is to
hardcode those observed literals into the derivation, which would make the
derivation lie about a workspace whose profile genuinely has no linter.

**Hardening.** **AMENDMENT B4** - Task 3 must record, per variable, whether the
value came from (i) a config/profile field, (ii) a SKILL.md documented default,
or (iii) the empty string. Category (iv) "observed in the current dogfood copy"
is FORBIDDEN as a source. The provenance table is an acceptance artifact.

## H7 - Manifest checksum atomicity

**Risk.** Regenerating artifacts without refreshing
`.autoharness/harness-manifest.yaml` leaves the workspace in a state where
`verify-workspace` reports checksum drift, converting a fix into a new warning
surface.

**Hardening.** C6 plus Task 4 AC4c already cover this. Confirmed sufficient.

## H8 - Sequencing

**Risk.** AC4a/AC4b depend on a clean full-suite signal; the current suite has
five known failures, and one of the implicated modules is the very module this
plan extends.

**Hardening.** Confirmed by the shipment dependency edges. Review-fix cycle 2 split
the test-isolation work across TWO shipments, so the chain is now
`148-S -> 149-S -> 151-S -> 150-S` and this shipment executes AFTER BOTH of them
(149-S diagnosis + decoupling, then 151-S remediation). Recorded in both plans.

## H9 - One global variable map cannot serve role-distinct consumers

*(RAISED in review-fix cycle 3, PR #386, thread `PRRT_kwDORzpWpM6bTZTM`.)*

**Risk.** The plan's whole derivation model assumes a SINGLE variable mapping is
sufficient for the entire render pass. Verified at the exact call sites, that
assumption is false in a way the plan could not have caught by variable-by-variable
review: `verify_workspace.py:4196` derives `variables` ONCE outside the artifact
loop, and `:4340` applies that same dict to EVERY artifact - yet
`_stage.agent.md.tmpl:946-947` and `_ship.agent.md.tmpl:898-899` consume the SAME
collapsed `{{ESCALATION_*}}` triple while the escalation route resolves PER ROLE.
Task 1 even names `{{ESCALATION_*}}` the "acting-role-collapsed" value - a collapse
that a role-less global map cannot perform.

The failure mode is especially dangerous because it is LATENT: today's config
declares only the flat `escalation` block, so both agents coincidentally render the
same correct value and every test would pass. It activates silently the first time
an operator uses the nested per-role override the Stage contract documents as
PREFERRED (F02FD596), at which point one of the two agents renders another role's
escalation route - a wrong-model routing defect with no local symptom.

A second, independent reason: the ESCALATION_DEGRADED same-route guard is
role-relative (Stage's route == `tier3`, Ship's == `tier2`), so a shared collapsed
value cannot express "degraded for Stage, genuine for Ship".

**Hardening.** **AMENDMENT B8** - add Task 1b: an artifact/role-aware SELECTION and
COMPOSITION step in front of the renderer. Binding constraints, all testable:
`_render_template` stays pure and byte-identical (C5, asserted by diff); role is
resolved from ARTIFACT IDENTITY via an explicit mapping table, never from ambient
state; only the COLLAPSED prose triple is role-scoped while the RAW
`LEGACY_`/`STAGE_`/`SHIP_ESCALATION_*` families stay global and raw (C3 preserved -
role-scoping a raw slot would reintroduce the PR #316 round-3 flat+nested
ambiguity); role-less artifacts get the base map unchanged. The acceptance surface
is a DISTINCT Stage-vs-Ship override test asserting the two rendered triples are
NOT EQUAL - an equality-only test would pass under the defect whenever the values
coincide, which is exactly today's situation.

## Outcome

**HARDENED.** Amendments B1, B2, B3, B4 applied to
`docs/plans/2026-08-21-verify-workspace-variable-derivation-plan.md` before
plan-review; **B8 added in review-fix cycle 3** after Copilot review surfaced the
single-global-map defect (H9), and applied to the plan as new Task 1b and harvested
as 142.007-T.
