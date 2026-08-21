---
title: "Plan review - verify-workspace template-variable derivation"
date: 2026-08-21
plan: docs/plans/2026-08-21-verify-workspace-variable-derivation-plan.md
hardening: docs/plans/2026-08-21-verify-workspace-variable-derivation-hardening.md
stash_id: 8FA8FC22
deliberation: "023-DL"
verdict: PASS
review_fix_cycle: 1
regated: 2026-08-21
---

# Plan Review - verify-workspace variable derivation

Date: 2026-08-21
Agent: Stage (plan-review gate)
Plan hardening: HARDENED (B1-B4 applied pre-review)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Verdict

**PASS (re-gated after review-fix cycle 1).**

*Original pass:* P1-1, P1-2, P1-3 RESOLVED by amendments B5, B6, B7; P2-1 folded
into B6.

*Review-fix cycle 1* (Copilot review on PR #386, 17 threads; 6 landed on this
plan/review pair): P2-1 was found FACTUALLY FALSE, **WITHDRAWN**, and replaced by
**P1-4** (role-route classification inverts the contract); the P1-1 resolution
was found to over-apply the tier-scalar empty-metadata rule to the ORCHESTRATOR
route and was corrected; and the sibling `GRAPHTOR_BINARY_PATH` criterion (AC3c)
was corrected from "derives to `\"\"`" to the documented PATH -> local-candidate
-> `graphtor` fallback chain. All three corrections are folded into the plan's
B6 clause and Task 3.

**0 unresolved P0/P1.** P1-4 RESOLVED. Review-fix cycles used: 1 of 3.

*Method note:* every corrected claim in this cycle was re-verified against the
authoritative source (`.github/skills/install-harness/SKILL.md` rows 414-453,
875, 881, 1088) and against a full-tree search for each variable's consumers,
rather than against a single template. The withdrawn P2-1 is a direct instance of
the failure mode that check exists to catch.

## P1-1 (RESOLVED by amendment B6) - `config.model_routing` is POLYMORPHIC and the plan assumes it is not

**Finding.** The plan (and the hardening) treat `config.model_routing` as a
uniform mapping of route -> {model_family, model_provider, reasoning_effort}. The
live `.autoharness/config.yaml` is not uniform:

```yaml
model_routing:
  tier1:                       # MAPPING
    model: "gpt-5.6-luna"
    model_family: "gpt-5.6-luna"
  tier2: "claude-sonnet-5"     # SCALAR STRING
  tier3: "claude-opus-5"       # SCALAR STRING
  orchestrator: "gpt-5.6-sol"  # SCALAR STRING
  stage: {...}                 # MAPPING
  ship: {...}                  # MAPPING
  escalation: {...}            # MAPPING
```

`tier2`, `tier3` and `orchestrator` are SCALAR SHORTHAND. A derivation written
against the mapping shape returns nothing for exactly
`{{TIER_2_FAMILY}}`, `{{TIER_3_FAMILY}}`, `{{TIER_2_PROVIDER}}`,
`{{TIER_3_PROVIDER}}`, `{{ORCHESTRATOR_FAMILY}}`, `{{ORCHESTRATOR_PROVIDER}}`,
`{{ORCHESTRATOR_REASONING_EFFORT}}` - which are precisely the variables in the
stash entry's own evidence. This shape polymorphism is very likely the actual
mechanism of the reported gap, and the plan does not mention it.

**Why it is P1.** A plan whose central task would reproduce the defect it is
fixing, for the specific variables cited as evidence, is not implementable as
written.

**Resolution (B6) - CORRECTED in review-fix cycle 1.** Derivation MUST normalise
both forms per route key, and the scalar rule is **NOT uniform across route
keys**:

* **TIER routes** (`tier1`/`tier2`/`tier3`), scalar form: the value populates
  `*_FAMILY` and `MODEL_ROUTING_*`; `*_PROVIDER` and `*_REASONING_EFFORT` derive
  to the empty string (SKILL.md rows 414-416).
* **ORCHESTRATOR route**, scalar form: the value populates `ORCHESTRATOR_FAMILY`
  only; `ORCHESTRATOR_PROVIDER` and `ORCHESTRATOR_REASONING_EFFORT` **fall back
  to their Tier 2 equivalents**, not to the empty string (SKILL.md rows 426-427;
  line 452 states it verbatim for the string form). `ORCHESTRATOR_FAMILY` does
  not fall back to tier2 - its own default is `gpt-5.4` (row 428).
* **Mapping form**: each sub-field derives independently, with the same
  per-field fallbacks applied to absent or empty sub-fields.

Contract tests must cover BOTH shapes for at least one tier and the orchestrator
route, and must assert the orchestrator's tier2 provider/effort fallback
specifically.

**Correction note (why the original resolution was wrong).** As first written,
this resolution applied the tier-scalar "empty metadata" rule to the orchestrator
route as well. That would have emptied `ORCHESTRATOR_PROVIDER` and
`ORCHESTRATOR_REASONING_EFFORT` for exactly the live scalar
`orchestrator: "gpt-5.6-sol"` config cited in this finding's own evidence - and
those two variables render `_orchestrator.agent.md` frontmatter, so the
"resolution" would have preserved the reported defect for two of the seven
variables it named. An empty-string expectation in the orchestrator test would
have locked the defect in as intended behaviour.

## P1-2 (RESOLVED by amendment B7) - the round-trip test can pass while the config is reshaped

**Finding.** Amendment B3's round-trip test is derive -> render -> parse ->
re-derive -> compare derivations. Rendering `templates/harness-config.yaml.tmpl`
emits every route as a MAPPING. So a workspace whose live config uses scalar
shorthand gets NORMALISED on render. B3's test compares DERIVATIONS, which are
equal before and after normalisation - so it passes while the file's shape has
silently changed. If that staged output were ever written back over the live
config, it would rewrite an operator's hand-authored config shape as a side
effect of a bug fix.

**Why it is P1.** It is a silent-data-modification hazard on the workspace's own
configuration file, invisible to the acceptance test that was specifically added
to catch round-trip problems.

**Resolution (B7).** (i) The plan states explicitly that shape normalisation in
the STAGED tree is acceptable and expected, and that this shipment MUST NOT write
the staged `.autoharness/config.yaml` back over the live one. (ii) The round-trip
test is strengthened to assert SEMANTIC route equivalence (each route's resolved
family/provider/effort) before and after, not merely derivation-map equality.

## P1-3 (RESOLVED by amendment B5) - T0b is a standing red test across the shipment

**Finding.** Task 0 adds T0b (zero unresolved) as RED "at the start of this
shipment, GREEN only after the last derivation task." Tasks 1, 2 and 3 each gate
on a local build/test pass (P-018). A checked-in red test blocks every
intermediate task gate - the same defect raised as P1-1 on the sibling
test-isolation plan.

**Resolution (B5).** T0b becomes a MONOTONE RATCHET: the checked-in expected set
is the acceptance surface, and each task lowers it. The final task sets the
expected set to empty and T0b degenerates to the zero assertion. Every commit is
green; a NEW unresolved variable still fails immediately because the expected set
is exact, not an upper bound on count alone.

## P2-1 (WITHDRAWN in review-fix cycle 1) - superseded by P1-4

**Original finding (WITHDRAWN - factually false).** P2-1 asserted that because
`templates/agents/_stage.agent.md.tmpl` frontmatter uses `{{TIER_3_*}}` rather
than `{{STAGE_*}}`, the `{{STAGE_*}}`/`{{SHIP_*}}` variables "occur ONLY in
`harness-config.yaml.tmpl` raw storage" and must therefore be RAW pass-through
with the tier fallback NOT applied.

**Why it was wrong.** The premise does not survive a full-tree search. It
generalised from one template to the whole repository.
`templates/agents/_orchestrator.agent.md.tmpl` lines 527-533 consume all six
role-route variables directly, and the prose immediately below requires them to
resolve concretely ("An installed workspace resolves each placeholder to concrete
values ... resolves `stage` to `claude-opus-5`/`anthropic` and `ship` to
`claude-sonnet-5`/`anthropic`"). That `_stage.agent.md.tmpl` uses `{{TIER_3_*}}`
in its OWN frontmatter never implied `{{STAGE_*}}` was unused elsewhere.

## P1-4 (RAISED in review-fix cycle 1; RESOLVED by the corrected B6 clause) - the role-route classification inverts the contract

**Finding.** The plan classified `{{STAGE_*}}`/`{{SHIP_*}}` as RAW
pass-through, deriving to `""` when unset. SKILL.md rows 429-434 define each of
these variables **with** its fallback (`{{STAGE_FAMILY}}` =
`config.model_routing.stage.model_family`, fallback `{{TIER_3_FAMILY}}`, default
`claude-opus-5`; mirrored for ship -> tier2). The P-013.5 paragraph at line 453
requires resolution "**per sub-field**, not as an all-or-nothing block ... never
from a hardcoded default and never silently from the current session model", and
requires the installer to resolve `{{STAGE_*}}`/`{{SHIP_*}}` "so the installed
frontmatter never carries an unresolved `{{...}}` placeholder".

**Why it is P1.** Deriving these to `""` would render `.github/agents/_orchestrator.agent.md`
with empty role-route values that contradict that file's own prose, and would do
so while T0b reports "zero unresolved" - the shipment's headline acceptance
criterion would be GREEN over a wrong render. A classification error that the
headline gate cannot see is exactly the class that ships.

**Why the escalation analogy does not transfer.** For escalation, SKILL.md
deliberately defines TWO families - resolved `{{ESCALATION_*}}` (prose-only) and
raw `{{LEGACY_ESCALATION_*}}`/`{{STAGE_ESCALATION_*}}`/`{{SHIP_ESCALATION_*}}`
(storage-only) - so a resolved value is never round-tripped into raw storage. No
such second raw-only family exists for the role routes; there is exactly one
variable per role sub-field. "Empty when unset" for `{{STAGE_*}}` would not
preserve a contract distinction, it would fabricate one.

**Resolution (corrected B6 classification clause).** `{{STAGE_*}}`/`{{SHIP_*}}`
are `RESOLVED-FROM-SOURCE` with the per-sub-field tier fallback APPLIED. The
raw/empty-when-unset classification remains correct for, and only for,
`{{LEGACY_ESCALATION_*}}`, `{{STAGE_ESCALATION_*}}` and
`{{SHIP_ESCALATION_*}}` - constraint C3 is unchanged and was never in error.

**Residual risk carried forward (ACCEPTED, recorded).** Storing a resolved
role-route value in `harness-config.yaml.tmpl` materialises a concrete value
where the operator declared none, so later `tier3`/`tier2` changes stop
propagating through that stored file. This is a genuine consequence of the
contract as written. The harness-config comment "falls back to tier3 (stage) /
tier2 (ship) when empty" describes CONSUMER behaviour on an empty field, not a
derivation instruction, so contract and comment are consistent. Changing it is a
SKILL.md contract change and re-enters P-021 capture; it does not block this
plan.

## Confirmed strengths (no action)

* Measuring the real blast radius (83 occurrences / 62 variables / 10 files)
  rather than inheriting the entry's 21-occurrence figure is the difference
  between a plan that fits and one that silently overruns.
* Task 0 as a measurement-and-guard task with a BLOCKING clean-pair intersection
  check (AC0b) is the correct way to defuse the parity-contract landmine before
  any code changes.
* B4's forbidden-provenance rule ("observed in the current dogfood copy" is not a
  source) closes the most tempting shortcut in the whole shipment.
* Decomposing by RESOLUTION SOURCE rather than by file keeps each task owning one
  coherent rule set, which is what makes the 2-hour bound achievable at all.
