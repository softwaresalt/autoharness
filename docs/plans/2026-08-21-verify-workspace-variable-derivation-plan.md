---
title: "verify-workspace template-variable derivation must conform to the install-harness resolution contract"
date: 2026-08-21
stash_id: 8FA8FC22
deliberation: ".backlogit/queue/023-DL.md"
hardening: docs/plans/2026-08-21-verify-workspace-variable-derivation-hardening.md
requires_plan_hardening: yes
hardening_present: yes
blast_radius: "elevated (install correctness in the Python CLI, config round-trip through harness-config.yaml.tmpl, multiple template families, and a live P-021/137-F byte-identity contract test)"
---

# Implementation Plan - verify-workspace variable derivation

Date: 2026-08-21
Agent: Stage (planning only - Ship executes)
Stash source: `8FA8FC22`
Deliberation: `023-DL`
Classification: **bug / install-correctness defect in the Python CLI**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Goal

Make `autoharness.verify_workspace._derive_template_variables` conform to the
`.github/skills/install-harness/SKILL.md` resolution tables, so that
`autoharness verify-workspace --workspace .` stages a tree with **zero**
unresolved `{{...}}` placeholders.

## Non-goals

* No change to `_render_template` (stays pure `{{VAR}}` substitution).
* No conditional-block template engine.
* **No reconciliation of the F3/F4(2) semantic prose drift** identified in
  `docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md` (~1,200
  lines of bidirectional normative drift). If implementation finds itself
  editing normative agent prose it has left scope and must re-enter P-021
  capture (023-DL R6).
* No backfill of `.autoharness/workspace-profile.yaml` (different surface).
* No reinterpretation of the 137-F paired-edit parity contract.

## Baseline (measured by Stage, read-only, from `.autoharness/staging/verify-workspace-report.json`)

**83 unresolved occurrences / 62 distinct variables / 10 staged files.**

| staged file | occurrences |
|---|---:|
| `.autoharness/config.yaml` | 45 |
| `.github/agents/_orchestrator.agent.md` | 15 |
| `.github/instructions/escalation-protocol.instructions.md` | 6 |
| `.github/copilot-instructions.md` | 4 |
| `.github/instructions/constitution.instructions.md` | 4 |
| `.github/instructions/graphtor-docs.instructions.md` | 2 |
| `AGENTS.md` | 2 |
| `start.ps1` | 2 |
| `start.sh` | 2 |
| `.github/instructions/github-pr-automation.instructions.md` | 1 |

`{{DEFAULT_BRANCH}}` alone accounts for 12. This is materially larger than the
stash entry's own 4-pair / 21-occurrence measurement.

## Binding constraints (from 023-DL)

* **C1.** `.github/skills/install-harness/SKILL.md` resolution tables are the
  single source of truth. Do not invent resolution sources.
* **C2.** Config-first, detection-as-fallback
  (`docs/compound/2026-05-05-resolution-order-config-first-not-detection-first.md`).
* **C3.** Preserve the PROSE-ONLY vs RAW-STORAGE split. `{{ESCALATION_*}}` is the
  acting-role-collapsed resolved value used for prose only.
  `{{LEGACY_ESCALATION_*}}`, `{{STAGE_ESCALATION_*}}` and `{{SHIP_ESCALATION_*}}`
  are RAW pass-through and MUST derive to the empty string when unset. Collapsing
  these reproduces the H2 flat+nested ambiguity (Copilot review round 3, PR #316).
* **C4.** Every newly derived variable must round-trip through
  `templates/harness-config.yaml.tmpl` where the SKILL.md table says it is stored
  (`docs/compound/2026-05-05-harness-config-round-trip-requirement.md`).
* **C5.** No behavioural change to `_render_template`.
* **C6.** `.autoharness/harness-manifest.yaml` checksums refreshed atomically
  with any regenerated artifact.

## Task breakdown

### Task 0 - Variable inventory, classification, and the zero-unresolved guard (BASELINE RED)

**This task must run first and it changes no derivation logic.**

**Test-first requirement.** Add `tests/test_template_variable_derivation_contract.py`:
* T0a: an INVENTORY test that renders the full staged tree through
  `_derive_template_variables` + `_render_template` and asserts the set of
  unresolved placeholders equals a **checked-in expected set**. Seed that set
  with the current 62. This test is GREEN on day one and becomes the ratchet:
  every later task removes entries from the expected set, and a NEW unresolved
  variable appearing is an immediate failure.
* T0b: a ZERO-UNRESOLVED test asserting the expected set is empty. RED at the
  start of this shipment, GREEN only after the last derivation task.

**Steps.**
1. Produce a per-variable classification table (checked into the plan's task
   record) with, for each of the 62: variable name, the SKILL.md resolution
   source, and one of `RESOLVED-FROM-SOURCE` or `DERIVE-TO-EMPTY-STRING`.
   Every `*_ESCALATION_*` raw variable must be classified
   `DERIVE-TO-EMPTY-STRING` per C3.
2. **BLOCKING MEASUREMENT (023-DL R1).** For each of the 62, determine whether
   it appears in any of the FOUR CLEAN template/dogfood pairs asserted
   byte-identical by
   `tests/test_scope_containment_policy_contract.py::test_clean_pairs_are_byte_identical_via_render_template`.
   Record the intersection. If ANY newly derived variable appears in a clean
   pair, its derivation task MUST update both sides of the pair plus the
   manifest checksum in the same change - or STOP and return to Stage.

**Acceptance criteria.**
* AC0a. Classification table covers all 62 variables with a cited SKILL.md row.
* AC0b. The clean-pair intersection is recorded explicitly (including "empty" if
  empty) - an unrecorded result is not acceptable.
* AC0c. T0a green; T0b red with exactly 62 remaining.

### Task 1 - Derive the model-routing and escalation family (~30 variables)

Covers `MODEL_ROUTING_TIER1/2/3`, `TIER_1/2/3_{FAMILY,PROVIDER,REASONING_EFFORT}`,
`ORCHESTRATOR_*`, `STAGE_*`, `SHIP_*`, `ANCHOR_REVIEW_*`, `ESCALATION_*`, and the
raw `LEGACY_ESCALATION_*` / `STAGE_ESCALATION_*` / `SHIP_ESCALATION_*` blocks.

**Test-first.** Extend the contract test with per-family assertions BEFORE
implementing: resolved fields take their value from `config.model_routing`;
raw escalation fields derive to `""` when unset; the P-013.5 per-sub-field tier
fallback holds (an absent `stage`/`ship` route resolves each sub-field from
tier3/tier2, never from a hardcoded default).

**Acceptance criteria.**
* AC1a. All ~30 variables removed from T0a's expected set.
* AC1b. A test proves that a workspace with a nested `stage.escalation` override
  and an empty flat `escalation` block renders the flat block INERT (all-empty) -
  i.e. C3 is enforced by a test, not by comment.
* AC1c. C4 round-trip: any of these stored in config render into
  `templates/harness-config.yaml.tmpl` at the documented slot.

### Task 2 - Derive the install-shape family (~10 variables)

`INSTALL_PRESET`, `PRIMARY_STACK_PACK`, `STACK_PACKS_YAML`, `INSTALL_LAYERS_YAML`,
`CAPABILITY_PACKS_YAML`, `HARNESS_OVERRIDES_YAML`, `ENABLED_SIDECARS_{YAML,SH,PS1}`,
`COPILOT_CLI_ARGS_{YAML,SH,PS1}`.

**Structural-rendering hazard (023-DL R4).** These are BLOCK values (YAML array,
sh array, PowerShell array) rendered through pure string substitution.
Indentation and quoting correctness is the primary failure mode.

**Test-first.** Assert the rendered `.autoharness/config.yaml` **parses as YAML**
and that the parsed values round-trip equal to the source config; assert
`start.sh` and `start.ps1` render syntactically valid array literals.

**Acceptance criteria.**
* AC2a. All install-shape variables removed from T0a's expected set.
* AC2b. Staged `.autoharness/config.yaml` parses and round-trips.
* AC2c. Staged `start.sh` / `start.ps1` array literals are syntactically valid
  (assert by parse/shape, not by eyeball).

### Task 3 - Derive the profile-derived and misc-config families (~15 variables)

`DEFAULT_BRANCH` (12 occurrences), `STRICT_SAFETY_ENABLED`,
`CONTINUOUS_LEARNING_{CAPTURE_HOOKS,ENVIRONMENT_ADAPTER,PROMOTION_THRESHOLD}`,
`GRAPHTOR_SOURCES_PATH`, `GRAPHTOR_BINARY_PATH`, `LANGUAGE_VERSION`,
`LANGUAGE_NOTES`, `LINTER`, `FORMATTER`, `FORMAT_CHECK_COMMAND`, `ERROR_PATTERN`,
`DOC_COMMENT_STYLE`.

**Rule for empty profile fields (023-DL R3).** Use the SKILL.md documented
default where one exists; otherwise derive to `""`. **Never invent a value.**
`GRAPHTOR_BINARY_PATH` must tolerate the `null` currently recorded in
`.autoharness/workspace-profile.yaml`.

**Acceptance criteria.**
* AC3a. All remaining variables removed from T0a's expected set.
* AC3b. **T0b (zero unresolved) is GREEN** - this is the shipment's headline
  acceptance criterion.
* AC3c. A test asserts `GRAPHTOR_BINARY_PATH: null` derives to `""` and not to
  the literal string `"None"`.

### Task 4 - Parity and manifest reconciliation

**Dependency.** Depends on Tasks 1-3.

**Steps.**
1. Re-run the byte-identity contract test for the four clean pairs. If any
   diverged as predicted by AC0b, update BOTH sides of the pair and refresh the
   manifest checksum atomically (C6).
2. Refresh `.autoharness/harness-manifest.yaml` checksums for every regenerated
   artifact.

**Acceptance criteria.**
* AC4a. `tests/test_scope_containment_policy_contract.py` fully green,
  including `test_clean_pairs_are_byte_identical_via_render_template`.
* AC4b. `autoharness verify-workspace --workspace .` reports 0 unresolved and no
  NEW blockers or warnings versus the pre-change baseline (which had 0 blockers,
  0 warnings per the 145-S closure record).
* AC4c. No manifest entry left stale (checksum scan clean).

## Width isolation (P-003)

Task 0 is measurement + guard. Tasks 1-3 are each ONE resolution-source family
inside `src/autoharness/verify_workspace.py` plus its contract test. Task 4 is
manifest/parity reconciliation. Template-family edits are confined to Task 1's
C4 round-trip slot in `templates/harness-config.yaml.tmpl` and to Task 4.

## Sequencing dependency on E8158860

This shipment's acceptance depends on a trustworthy full-suite signal
(AC4a/AC4b). It is therefore sequenced AFTER the test-isolation shipment, so its
verification evidence is not contaminated by the five pre-existing failures -
and because the same module implicated in that pollution
(`test_scope_containment_policy_contract.py`) is the module this plan extends.

## Amendments applied from hardening (P-006)

Source: `docs/plans/2026-08-21-verify-workspace-variable-derivation-hardening.md` (HARDENED).

* **B1 (H1)** - If Task 0's clean-pair intersection (AC0b) is NON-EMPTY, the
  affected derivation task STOPS and returns to Stage, UNLESS the divergence is a
  pure placeholder-to-same-literal substitution (the correct rendered value is
  provably identical to the literal already present in the dogfood copy). Any
  other divergence is a normative edit and re-enters P-021 capture.
* **B2 (H2)** - AC1b's test must be NEGATIVE as well as positive: given a nested
  `stage.escalation` override with the flat `escalation` unset, assert the
  rendered flat sub-fields are the empty string and specifically **not equal to**
  the nested override values.
* **B3 (H3)** - Task 2 gains an idempotent round-trip acceptance test: render
  `.autoharness/config.yaml` from template using the derived variables, re-parse,
  re-derive from the re-parsed config, and assert the second derivation equals
  the first.
* **B4 (H6)** - Task 3 must record per-variable value provenance as an acceptance
  artifact, restricted to (i) config/profile field, (ii) SKILL.md documented
  default, or (iii) empty string. "Observed in the current dogfood copy" is a
  FORBIDDEN source.
* **H4 elevation** - AC3b (zero unresolved) MUST NOT be reported as met unless
  AC2b and AC2c (parse-level validity of the rendered YAML and shell/PowerShell
  arrays) also hold. Zero-unresolved alone is not evidence of a correct render.

## Amendments applied from plan review

Source: `docs/reviews/2026-08-21-verify-workspace-variable-derivation-review.md` (PASS).

* **B5 (P1-3)** - T0b becomes a MONOTONE RATCHET rather than a standing red
  assertion. The checked-in expected-unresolved SET is the acceptance surface and
  each task lowers it; the final task sets it to empty, at which point T0b is the
  zero assertion. Every intermediate commit is green, and a NEW unresolved
  variable still fails immediately because the expected set is exact.
* **B6 (P1-1, P2-1)** - Derivation MUST normalise the POLYMORPHIC
  `config.model_routing` shape. In the live workspace `tier2`, `tier3` and
  `orchestrator` are SCALAR STRINGS while `tier1`, `stage`, `ship` and
  `escalation` are MAPPINGS. Rules:
  * Scalar form -> the value is the model identifier; it populates
    `MODEL_ROUTING_*` and `*_FAMILY`; `*_PROVIDER` and `*_REASONING_EFFORT`
    derive to the empty string.
  * Mapping form -> each sub-field derives independently.
  * Contract tests MUST cover BOTH shapes for at least one tier route and for the
    orchestrator route.
  * Classification rule: `{{STAGE_*}}` / `{{SHIP_*}}` occur ONLY in
    `harness-config.yaml.tmpl` raw storage (the agent templates' frontmatter uses
    `{{TIER_3_*}}`), so they are RAW pass-through - empty when unset, tier
    fallback NOT applied. `{{ORCHESTRATOR_*}}` is DUAL-USE (agent frontmatter and
    config storage) and must resolve for frontmatter while remaining faithful to
    the stored value.
* **B7 (P1-2)** - (i) Shape normalisation in the STAGED tree is acceptable and
  expected; this shipment MUST NOT write the staged `.autoharness/config.yaml`
  back over the live workspace config. (ii) B3's round-trip test is strengthened
  to assert SEMANTIC route equivalence (each route's resolved
  family/provider/effort) before and after rendering - not merely equality of the
  derived variable map, which is invariant under normalisation and would mask the
  reshape.
