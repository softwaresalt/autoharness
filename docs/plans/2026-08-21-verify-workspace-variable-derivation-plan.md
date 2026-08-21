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

### Task 0 - Variable inventory, classification, and the unresolved-placeholder ratchet guard (BASELINE GREEN AT 62)

**This task must run first and it changes no derivation logic.**

**Test-first requirement.** Add `tests/test_template_variable_derivation_contract.py`:
* T0a: an INVENTORY test that renders the full staged tree through
  `_derive_template_variables` + `_render_template` and asserts the set of
  unresolved placeholders equals a **checked-in expected set**. Seed that set
  with the current 62. This test is GREEN on day one and becomes the ratchet:
  every later task removes entries from the expected set, and a NEW unresolved
  variable appearing is an immediate failure.
* T0b: the ZERO-UNRESOLVED assertion, expressed as a MONOTONE RATCHET over the
  same checked-in expected set rather than as a standing red assertion
  (amendment B5). It asserts that the expected set contains no more entries than
  the checked-in bound, and each later task LOWERS that bound. T0b is therefore
  GREEN from day one at 62 and stays green through every intermediate commit; the
  final derivation task sets the bound to zero, at which point T0b degenerates
  into the literal zero-unresolved assertion. A NEW unresolved variable still
  fails immediately because T0a's expected set is EXACT, not a count bound.
  (Rewritten in review-fix cycle 2: this bullet previously said T0b is "RED at the
  start of this shipment", which contradicted B5 and would have checked in a
  deliberately-red test that blocks the P-018 gate on every intermediate task.)

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
* AC0c. T0a is GREEN with exactly 62 entries in the expected set, and T0b is
  GREEN as a ratchet at bound 62. Neither test is checked in red. (Rewritten in
  review-fix cycle 2 to match amendment B5.)

### Task 1 - Derive the model-routing and escalation family (~30 variables)

Covers `MODEL_ROUTING_TIER1/2/3`, `TIER_1/2/3_{FAMILY,PROVIDER,REASONING_EFFORT}`,
`ORCHESTRATOR_*`, `STAGE_*`, `SHIP_*`, `ANCHOR_REVIEW_*`, `ESCALATION_*`, and the
raw `LEGACY_ESCALATION_*` / `STAGE_ESCALATION_*` / `SHIP_ESCALATION_*` blocks.

**Test-first.** Extend the contract test with per-family assertions BEFORE
implementing: resolved fields take their value from `config.model_routing`;
the RAW ESCALATION fields (`LEGACY_`/`STAGE_`/`SHIP_ESCALATION_*`) derive to `""`
when unset; the P-013.5 per-sub-field tier fallback holds for the ROLE ROUTES
themselves - an absent `stage`/`ship` route resolves each sub-field from
tier3/tier2 (never from a hardcoded default, never from the current session
model), and `{{STAGE_*}}`/`{{SHIP_*}}` are asserted specifically NOT `""`; and a
scalar `orchestrator` keeps its tier2 provider/effort fallback while
`ORCHESTRATOR_FAMILY` uses its own `gpt-5.4` default.

**Acceptance criteria.**
* AC1a. All ~30 variables removed from T0a's expected set.
* AC1b. A test proves that a workspace with a nested `stage.escalation` override
  and an empty flat `escalation` block renders the flat block INERT (all-empty) -
  i.e. C3 is enforced by a test, not by comment.
* AC1c. C4 round-trip: any of these stored in config render into
  `templates/harness-config.yaml.tmpl` at the documented slot.

### Task 1b - Artifact/role-aware variable selection and composition (render pipeline)

**Why this task exists (review-fix cycle 3, thread `PRRT_kwDORzpWpM6bTZTM`).**
Tasks 0-1 assume ONE global variable mapping is sufficient. It is not.
`verify_workspace.py:4196` derives `variables` ONCE, outside the artifact loop, and
`verify_workspace.py:4340` passes that SAME dict to `_render_template` for EVERY
artifact. But `templates/agents/_stage.agent.md.tmpl:946-947` and
`templates/agents/_ship.agent.md.tmpl:898-899` both consume the SAME collapsed
triple `{{ESCALATION_FAMILY}}` / `{{ESCALATION_PROVIDER}}` /
`{{ESCALATION_REASONING_EFFORT}}`, while the escalation route is resolved PER ROLE
(nested `model_routing.<role>.escalation` -> flat `model_routing.escalation` ->
`tier3` per-field). Task 1 calls `{{ESCALATION_*}}` the "acting-role-collapsed"
value, but a single global dict has no acting role, so that collapse is
unsatisfiable as currently plumbed.

**Latent, not active.** `.autoharness/config.yaml` lines 57-80 declare only the FLAT
`escalation` block and no nested per-role override, so today both agents collapse to
the same value and render correctly by coincidence. The defect activates the moment
a nested per-role override is declared - the form the Stage contract documents as
preferred (F02FD596). It must be fixed while this surface is open.

**Design (C5 preserved - `_render_template` does NOT change).**
1. Add a PURE composition helper (e.g. `_compose_artifact_variables(base, role)`)
   returning a NEW mapping = base overlaid with the role-scoped collapsed triple.
   It must not mutate the base, which is reused across the loop.
2. Add role resolution from ARTIFACT IDENTITY (e.g. `_resolve_artifact_role`),
   driven by an explicit mapping table over the manifest artifact's `path`/`template`
   - never from ambient session state, the acting agent, or an env var.
3. Change ONLY the render call site (4340) to pass the composed mapping. Keep the
   single derivation at 4196 so cost stays O(1) in derivations.
4. Scope role-awareness to the COLLAPSED prose triple ONLY. The RAW families
   (`LEGACY_`/`STAGE_`/`SHIP_ESCALATION_*`) stay GLOBAL and RAW - C3 is preserved,
   not weakened. Role-scoping a raw slot would reintroduce the PR #316 round-3
   flat+nested ambiguity.
5. Artifacts with no role (instructions, config, start scripts, `AGENTS.md`) and the
   role-neutral `escalation-protocol.instructions.md` receive the BASE map unchanged.

**Acceptance criteria.**
* AC1b-a. A DISTINCT Stage-vs-Ship override test exists: given differing
  `model_routing.stage.escalation` and `model_routing.ship.escalation`, the staged
  `_stage.agent.md` and `_ship.agent.md` carry the respective role's values AND the
  two triples are asserted NOT EQUAL. An equality-only assertion would pass under
  the defect whenever the two happen to coincide.
* AC1b-b. With only the FLAT block declared (today's live shape), both agents render
  the SAME value - proving a strict generalisation and a no-op for current config.
* AC1b-c. With neither declared, each role falls back to `tier3` per-field.
* AC1b-d. `_render_template` is byte-identical to its pre-change form (assert by diff).
* AC1b-e. RAW `*_ESCALATION_*` families render byte-identically across all artifacts.
* AC1b-f. Role-less artifacts render byte-identically to pre-change output.

**Dependency.** Task 1 (the escalation slots must exist before they can be composed).
Task 4 depends on this task, because composition changes rendered bytes.

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
`.autoharness/workspace-profile.yaml` - and `null`/absent is a
DOCUMENTED-DEFAULT case, **not** an empty-string case. Per SKILL.md row 875 and
the prose at line 1088 it resolves through an ORDERED CHAIN: (1) `graphtor` on
PATH; (2) `.graphtor/bin/graphtor-docs.exe` or `.graphtor/bin/graphtor-docs`;
(3) final default `graphtor`. The chain always yields a NON-EMPTY value, and
SKILL.md line 881 independently requires this variable to be fully resolved in
installed output. (Corrected in review-fix cycle 1.)

**Acceptance criteria.**
* AC3a. All remaining variables removed from T0a's expected set.
* AC3b. **T0b (zero unresolved) is GREEN** - this is the shipment's headline
  acceptance criterion.
* AC3c (CORRECTED, review-fix cycle 1). A test asserts
  `graphtor_docs.binary_path: null` derives through the documented fallback chain
  to a NON-EMPTY value - never `""`, never the literal string `"None"` -
  covering each rung: `graphtor` on PATH; a PATH miss with a
  `.graphtor/bin/graphtor-docs[.exe]` candidate present; and both absent yielding
  the final default `graphtor`. A declared non-null `binary_path` still wins over
  the whole chain (config-first, C2).

### Task 4 - Parity and manifest reconciliation

**Dependency.** Depends on Tasks 1, 1b, 2 and 3. Task 1b is included because
artifact/role-aware composition changes rendered bytes and therefore checksums.

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

* **B5 (P1-3; APPLIED to the operative Task 0 section in review-fix cycle 2 - it
  had previously been recorded here as an amendment while Task 0's heading, its
  T0b bullet and AC0c still described a standing-RED baseline)** - T0b becomes a
  MONOTONE RATCHET rather than a standing red assertion. The checked-in expected-unresolved SET is the acceptance surface and
  each task lowers it; the final task sets it to empty, at which point T0b is the
  zero assertion. Every intermediate commit is green, and a NEW unresolved
  variable still fails immediately because the expected set is exact.
* **B6 (P1-1, P2-1; the scalar-orchestrator and role-route clauses were
  CORRECTED in review-fix cycle 1)** - Derivation MUST normalise the POLYMORPHIC
  `config.model_routing` shape. In the live workspace `tier2`, `tier3` and
  `orchestrator` are SCALAR STRINGS while `tier1`, `stage`, `ship` and
  `escalation` are MAPPINGS. Rules:
  * Scalar form, TIER routes (`tier1`/`tier2`/`tier3`) -> the value is the model
    identifier; it populates `MODEL_ROUTING_*` and `*_FAMILY`; `*_PROVIDER` and
    `*_REASONING_EFFORT` derive to the empty string (SKILL.md rows 414-416, "all
    other tier sub-fields default to empty").
  * Scalar form, ORCHESTRATOR route -> the value populates `ORCHESTRATOR_FAMILY`
    ONLY. `ORCHESTRATOR_PROVIDER` and `ORCHESTRATOR_REASONING_EFFORT` **fall back
    to `{{TIER_2_PROVIDER}}` / `{{TIER_2_REASONING_EFFORT}}`**, NOT to the empty
    string - SKILL.md rows 426-427, and line 452 states it verbatim for the
    string form ("The `reasoning_effort` and `model_provider` fields fall back to
    their tier2 equivalents"). Asymmetry to preserve: `ORCHESTRATOR_FAMILY`
    itself does NOT fall back to tier2; its own default is `gpt-5.4` (row 428).
  * Mapping form -> each sub-field derives independently, with the same per-field
    fallbacks applied to any absent or empty sub-field.
  * Contract tests MUST cover BOTH shapes for at least one tier route and for the
    orchestrator route, including the orchestrator's tier2 provider/effort
    fallback and its distinct `gpt-5.4` family default.
  * Classification rule (CORRECTED): `{{STAGE_*}}` / `{{SHIP_*}}` are
    `RESOLVED-FROM-SOURCE` with the P-013.5 PER-SUB-FIELD tier fallback APPLIED
    (`stage.<field>` -> `{{TIER_3_<field>}}`, `ship.<field>` ->
    `{{TIER_2_<field>}}`; SKILL.md rows 429-434 and the role-route paragraph at
    line 453). The earlier claim that they occur ONLY in
    `harness-config.yaml.tmpl` raw storage is FALSE and is WITHDRAWN:
    `templates/agents/_orchestrator.agent.md.tmpl` lines 527-533 consume all six
    directly, and its prose requires concrete resolved values. Unlike escalation
    - where SKILL.md defines a SECOND, raw-only family
    (`LEGACY_`/`STAGE_`/`SHIP_ESCALATION_*`) precisely to keep resolved values
    out of raw storage - there is exactly ONE variable per role sub-field,
    defined WITH its fallback. `{{ORCHESTRATOR_*}}` is likewise DUAL-USE (agent
    frontmatter and config storage) and must resolve for frontmatter while
    remaining faithful to the stored value.
  * Round-trip consequence (RESIDUAL RISK - record, do not silently resolve):
    storing a resolved role-route value in `harness-config.yaml.tmpl`
    materialises a concrete value where the operator declared none, so later
    `tier3`/`tier2` changes stop propagating through that stored file. The
    harness-config comment "falls back to tier3 (stage) / tier2 (ship) when
    empty" describes CONSUMER behaviour on an empty field, not a derivation
    instruction, so contract and comment are consistent. Implement per contract
    and surface the consequence; changing it is a SKILL.md contract change and
    re-enters P-021 capture.
* **B7 (P1-2)** - (i) Shape normalisation in the STAGED tree is acceptable and
  expected; this shipment MUST NOT write the staged `.autoharness/config.yaml`
  back over the live workspace config. (ii) B3's round-trip test is strengthened
  to assert SEMANTIC route equivalence (each route's resolved
  family/provider/effort) before and after rendering - not merely equality of the
  derived variable map, which is invariant under normalisation and would mask the
  reshape.

## Amendments applied in review-fix cycle 3 (PR #386)

Thread: `PRRT_kwDORzpWpM6bTZTM`.

* **B8** - **NEW Task 1b.** One global variable mapping cannot serve two artifacts
  that consume the same placeholder with role-distinct correct values. Verified at
  the exact call sites (`verify_workspace.py:4196` single derivation, `:4340` same
  dict per artifact) and the exact consumers (`_stage.agent.md.tmpl:946-947`,
  `_ship.agent.md.tmpl:898-899`). Resolved by an artifact/role-aware
  SELECTION/COMPOSITION step in front of a still-pure `_render_template` (C5 intact),
  scoped strictly to the collapsed `{{ESCALATION_*}}` prose triple so the raw
  storage families and C3 are untouched. Harvested as **142.007-T** (M / high) into
  150-S, gated `142.007-T -> 142.003-T` and `142.006-T -> 142.007-T`.

P-021 C1: SAME CONTRACT SURFACE - `src/autoharness/verify_workspace.py` plus its
contract tests, already this feature's declared surface. No SKILL.md edit, no
`_render_template` behavioural change. No new deferred capture required.
