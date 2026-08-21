---
title: "Plan review - verify-workspace template-variable derivation"
date: 2026-08-21
plan: docs/plans/2026-08-21-verify-workspace-variable-derivation-plan.md
hardening: docs/plans/2026-08-21-verify-workspace-variable-derivation-hardening.md
stash_id: 8FA8FC22
deliberation: "023-DL"
verdict: PASS
---

# Plan Review - verify-workspace variable derivation

Date: 2026-08-21
Agent: Stage (plan-review gate)
Plan hardening: HARDENED (B1-B4 applied pre-review)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Verdict

**PASS** - 3 P1 raised, all RESOLVED by amendments B5, B6, B7; 1 P2 raised and
folded into B6. **0 unresolved P0/P1.** Review-fix cycles used: 1 of 3.

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

**Resolution (B6).** Derivation MUST normalise both forms per route key: a scalar
value means "model identifier" and populates `*_FAMILY` (and `MODEL_ROUTING_*`)
with the provider/reasoning-effort sub-fields deriving to the empty string; a
mapping populates each sub-field independently. Contract tests must cover BOTH
shapes for at least one tier and the orchestrator route.

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

## P2-1 (FOLDED into B6) - STAGE_*/SHIP_* are config-storage-only and must be RAW

**Finding.** `templates/agents/_stage.agent.md.tmpl` frontmatter uses
`{{TIER_3_*}}`, not `{{STAGE_*}}`. So `{{STAGE_FAMILY}}`/`{{SHIP_FAMILY}}` and
siblings occur ONLY in `harness-config.yaml.tmpl` raw storage, whose comment
reads "Absent/empty sub-fields fall back to tier3 (stage) / tier2 (ship)."
Deriving these with the tier fallback APPLIED would materialise a role override
the operator never declared - the same defect class as the H2 escalation
ambiguity, one level up. By contrast `{{ORCHESTRATOR_*}}` IS dual-use (agent
frontmatter AND config storage), so it must resolve for frontmatter while
remaining faithful for storage.

**Resolution.** Folded into B6 as an explicit per-variable classification rule.

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
