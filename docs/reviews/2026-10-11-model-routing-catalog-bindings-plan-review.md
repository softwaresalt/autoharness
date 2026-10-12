---
title: "Plan review: model routing catalog and bindings with schema 1.2.0 (R1-B)"
description: "Multi-persona plan review of docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md, run as a single-agent declared-degradation pass. Cycle 1 failed on a P1 (no render-time composition unit for bound subagents); the plan was revised with unit B6a and cycle 2 passes."
doc_type: review
review_target: docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md
dispatch_mode: single-agent-declared-degradation
decision: PASS
review_cycles: 2
reviewed_utc: 2026-10-12
---

# Plan review: model routing catalog and bindings with schema 1.2.0 (R1-B)

Review gate for `docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md`
(deliberation `040-DL`, stash `BF66F08B`). Dates are UTC.

dispatch_mode: single-agent-declared-degradation

decision: PASS

## Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch` — no reviewer subagent dispatch surface in
  this Stage session. Declared fallback: single-agent persona pass; every selected persona
  applied inline.
* `TOOL_DEGRADED: model-specific-review-routing` — `model_routing.anchor_review` is not
  dispatchable from this session. Declared fallback: same-model rubric pass for the
  cross-model personas.

## Persona coverage

| Persona | Mode | Triggered | Findings |
|---|---|---|---|
| Constitution Reviewer | inline pass | always-on | B-F5 (P3) |
| Python Reviewer | inline pass | always-on | B-F2 (P2, fixed) |
| Scope Boundary Auditor | inline pass | always-on | B-F4 (P2, fixed) |
| Learnings Researcher | inline pass | always-on | B-F3 (P2, fixed), B-F8 (P3) |
| Architecture Strategist | inline pass, same-model fallback | always | B-F1 (P1, fixed), B-F6 (P3) |
| Agent-Native Parity Reviewer | inline pass, same-model fallback | not triggered: no new agent-facing action in this release (the CLI is R1-A) | none |
| Security Lens Reviewer | inline pass, same-model fallback | judged not triggered: no auth, secrets, or new trust boundary; cross-provider exposure is operator data | B-F7 (P3, noted) |

## Findings

### Cycle 1 (decision before revision: FAIL)

* **B-F1 [P1] Architecture Strategist.** No unit made the render loop honor a binding.
  Subagent frontmatter renders from the global `TIER_<N>_*` variables, and the only
  per-artifact variable composition is the role overlay (`_resolve_artifact_role` and
  `_compose_artifact_variables`) for `_stage` and `_ship`. A bound agent would therefore
  render with its template tier values, so after a `tune` refresh its installed frontmatter
  would disagree with the render-parity check, and B7's fail-closed drift check and the
  render check could not both pass. This would also leave bindings declared in config but
  unable to be applied by install, the exact "accepted but inert" defect the release exists
  to remove. **Fixed:** new unit **B6a** adds a site overlay in the render loop (bound agent's
  four route variables come from the resolver; unbound and pipeline artifacts render
  byte-identically), new invariant **I9**, a ProposedAction row, a requirements-trace row
  (RB2a), a dependency-graph update (`B6 -> B6a -> B7`), and install-harness wording (B8).
* **B-F2 [P2] Python Reviewer.** B2 parsed template frontmatter with YAML, which can fail on
  unquoted `{{...}}` values (for example the `tools:` line in `_stage`). **Fixed:** B2 uses a
  targeted regex over the frontmatter block for the `{{TIER_<N>_FAMILY}}` variable.
* **B-F3 [P2] Learnings Researcher.** B8 and B9 edit global, non-rendered skills; per
  `docs/compound/096-S-template-vs-global-skill-placeholders.md` they must read values from
  the config at runtime and not rely on install-time placeholders. **Fixed:** both units
  state the rule.
* **B-F4 [P2] Scope Boundary Auditor.** `tests/test_context_tier_tune_guidance.py` pins
  prose in the install and tune skills that names `schema_version: "1.1.0"`; B8 could break
  those pins without budgeting for them. **Fixed:** B8 forbids editing pinned strings and
  budgets a meaning-preserving pin update only if the example config must change.
* **B-F5 [P3] Constitution Reviewer.** B4 is `harness-surface:none` (schemas and tests, no
  `src/` file), so the harness-architect imposes no RED roster; tests-first still applies.
  **Acknowledged:** the unit lists its tests and the implementer writes them first.
* **B-F6 [P3] Architecture Strategist.** Binding syntax is validated by the schema pattern
  and existence by the registry (two layers). **Acknowledged;** documented in B4 and B6.
* **B-F7 [P3] Security Lens Reviewer (noted, not triggered).** `routes` accepts any provider
  string by design (Core Rule 3). The release ships no routing data, so no data leaves the
  workspace because of it. Provider mix and egress remain `040-DL` OQ1, operator authority.
* **B-F8 [P3] Learnings Researcher.** Schema-mirror immutability
  (`docs/compound/2026-08-08-*`, `2026-08-30-*`) is respected: B4 forbids editing 1.1.0 and
  B5 pins it. **Acknowledged.**

### Cycle 2 (re-review after the fixes)

Re-checked B6a against the render-loop pattern it extends (file budget 2; depends on B6;
acceptance requires existing render-parity tests unchanged and byte-identical unbound
renders). Re-checked the graph: `B1 -> B2`; `B3a -> B3b -> B4 -> B5`;
`{B1, B2, B5} -> B6 -> B6a -> B7`; `B5 -> B8`; `{B7, B8} -> B9 -> B10 -> B11`. It is acyclic
and serial on the three shared files. No new findings.

## Hardening and verification gaps

Plan hardening was required (`Requires plan hardening: yes`) and is present: invariants I1
to I9, `ProposedAction`/`ActionRisk` table including the operator-owned config edit, added
verification, closure and rollback detail, operator checkpoints, and the review-gate
capability-risk declaration. Runtime verification and closure are specified for B4/B5,
B6/B7, B8, and B9. The one decision that blocks safe execution (`040-DL` OQ9, the dogfood
`schema_version` marker) is explicit, scoped to B5, and has a recommended default.

## Gate decision

Cycle 1 had one P1 and therefore failed. The plan was revised and re-reviewed; no P0 or P1
findings remain and the P2 findings were fixed. Decision: **PASS**. P3 items are
acknowledged for awareness.

## Addendum: PR #513 review-fix cycle 1 (2026-10-12 UTC)

Append-only. The cycle 1 and cycle 2 records and the verdict above are unchanged. After the
staging PR (#513) received a Copilot review (review 5487147517, HEAD `cc06f41e`), Stage fixed
the findings that touch this plan and re-checked only the changed units as a single-agent
delta pass (same `TOOL_DEGRADED` declarations as above).

| Review thread | Change to this plan or its tasks | Commit |
|---|---|---|
| `PRRT_kwDORzpWpM6rWUWn` (missing B3b to B4 edge) | No plan change: the graph and the `208.005-T` note already declared `B3b -> B4`. The backlog edge `208.005-T` depends on `208.004-T` was added; an audit of every `207.*` and `208.*` task against both plan graphs and all task notes found no other missing edge | `d12a3979` |
| `PRRT_kwDORzpWpM6rWUXL` (empty `model_provider`) | B1 gains a no-`model_provider` vector; the error was in deliberation D4, now corrected (only `model_family` is mandatory) | `82c8308c` |
| `PRRT_kwDORzpWpM6rWUXr` (registry cannot see workspace-authored agents) | B2 is disk-first with a manifest left-join, adds manifest-orphan and conflict cases and three fixtures; B6, B6a, B7 text updated; B2 resized `S` to `M` | `78f88268` |
| `PRRT_kwDORzpWpM6rWUYJ` (purity not enforced) | B1 runs through the R1-A `forbid_io()` guard; B2's read-only claim is asserted by a tree-snapshot test | `b62cb4d1` |
| Operator answer to `040-DL` OQ1 to OQ9 | OQ9 (the B5 marker bump) confirmed 2026-10-12: the B5 checkpoint text now says Ship cites the recorded confirmation; no B5 scope change | `96a4503b` |

Delta persona pass over the changed units:

* **Architecture Strategist.** Disk-first enumeration then a left-join to the manifest is the
  same shape `frontmatter_conformity` already uses (`_fc_enumerate_targets` plus
  `_fc_classify`), so the unmanaged branch is now reachable. The registry return type
  became `SiteRegistry(sites, orphans, conflicts)`; B6 and B7 were updated in the same
  revision. The plan dependency graph is unchanged and acyclic, and the backlog now encodes
  every plan edge.
* **Python Reviewer.** The `verify_workspace` import cycle (it imports this module) is
  handled by function-local import or injection plus a standalone-import test.
  Containment and symlink checks precede every read.
* **Scope Boundary Auditor.** Still one concern and two files in B2; no new config key or
  routing value. The resize to `M` reflects volume only (complexity unchanged).
* **Learnings Researcher.** The managed versus workspace-authored provenance split from
  `037-DL` is reused, not reinvented.

New findings: **B-F9 [P3]** the registry return type changed shape; consumers were updated
together, acknowledged. **B-F10 [P3]** a workspace-authored agent has no default tier, so B7
compares it only when it is bound (an unbound one is skipped); this is now stated in B7 and
tested, acknowledged. No P0, P1, or P2 findings. The delta check supports the existing
verdict: the plan remains **PASS**. The statement above that OQ9 "blocks safe execution"
describes the plan as reviewed; OQ9 was confirmed afterwards (see the plan's "Unresolved
operator decisions" paragraph).

## Addendum: PR #513 review-fix cycle 2 (2026-10-12 UTC)

Append-only. The cycle 1 and cycle 2 records, the cycle 1 addendum, and the verdict above are
unchanged. The staging PR (#513) received a second Copilot review (review 5494415746, HEAD
`e0051e68`) with three findings, all touching this plan. Stage verified each against the
repository, fixed it, and re-checked only the changed units as a single-agent delta pass
(same `TOOL_DEGRADED` declarations as above). The graph statement in the cycle 1 addendum
("the backlog encodes the `B3b -> B4` edge") described that state; the edge now reads
`B3b -> B5`, as below.

| Review thread | Verification and change | Commit |
|---|---|---|
| `PRRT_kwDORzpWpM6rkjC9` (`model_routing` still open to arbitrary keys) | Confirmed: `model_routing` has no `additionalProperties` in the root schema or the 1.1.0 mirror (the dogfood config carries no unknown key). Decision: B4 closes `model_routing` with an allowlist in the **1.2.0 schema only** (1.1.0 untouched, so I1 and I2 hold); B1 exports `MODEL_ROUTING_KNOWN_KEYS`; B6 adds `routing_unknown_keys` (fails at 1.2.0 with `ROUTING_UNKNOWN_KEY`, one advisory per key below 1.2.0, the same gate as the anchor check); regression cases for `routez` and an inert `subagents` block at the schema and verify layers, and a 1.1.0 stays-valid case | `e21a9502` |
| `PRRT_kwDORzpWpM6rkjDk` (a deliberately red boundary between B4 and B5) | Confirmed: the four B3 modules validate current-version fixtures and the dogfood config against both the root and the current mirror, which read the contract version (1.1.0 until B5), so the root const at 1.2.0 in B4 made them red. B4 now only publishes the unreferenced 1.2.0 mirror (2 files); B5 is the single atomic cut-over (root schema content, `current_version`, `known_versions`, migration entry, byte pin, lockstep test, dogfood marker, manifest hash), resized `S` / `low` to `M` / `medium`; edges: `208.005-T` no longer depends on `208.004-T`, `208.006-T` now does; invariant I10 | `789f5748` |
| `PRRT_kwDORzpWpM6rkjEC` (alias check only in `verify-workspace`) | Confirmed (see the R1-A review addendum). B6's alias check now delegates to the shared R1-A function `model_routing_yaml.check_model_routing_yaml` (`207.006-T`); B6 defines no scanner and tests delegation | `7ba1193a` |

Audit for the same "intermediate red" pattern across all of R1-B: B1, B2, B3a, B3b, B4 (now),
B6, B6a, B7, B8, B9, B10, and B11 each leave the suite green by their acceptance criteria;
B5 is the only unit that changes the root const, the contract version, the current-mirror
pairing, and the marker, and it does so together. The shipment manifest order of `215-S`
already honored every edge and is unchanged.

Delta persona pass over the changed units:

* **Architecture Strategist.** Closing `model_routing` only in 1.2.0 keeps every published
  mirror immutable; the unknown-key severity follows the same fail-at-1.2.0 / advisory-below
  gate as anchors (040-DL D2), so one rule covers every accepted-but-inert routing key.
  Publishing the mirror unreferenced and adopting it atomically in B5 keeps the
  contract-version-coupled tests green at every boundary. The graph is
  `B3a -> B3b -> B5`, `B4 -> B5`, `{B1, B2, B5} -> B6`; acyclic; `autoharness gate
  dag-readiness` reports `cycle_detected: false` and `ready_set: [209-S]`.
* **Python Reviewer.** `MODEL_ROUTING_KNOWN_KEYS` is a plain frozenset in the pure module (no
  I/O, so the A2 import allowlist still passes) and a B6 sync test ties it to the 1.2.0
  mirror's `model_routing.properties`, so the schema and the check cannot drift.
* **Scope Boundary Auditor.** B4 shrinks to two new files; B5 grows to three files plus the
  marker pair (within budget, resized for volume and integration risk); B6's net size is
  unchanged (the event scan left, a set-difference check arrived). No routing value, config
  key beyond the documented twelve, or policy text changes.
* **Learnings Researcher.** The seven-step mirror-immutability fix and the existence-gated
  verify-check pattern from the two compound learnings still govern; no conflict.

New findings: **B-F11 [P3]** B5 resized `S` / `low` to `M` / `medium`; both axes re-estimated
under `ah-stage-sizing-v1`, `215-S` histogram now `M:8`, `S:5`, acknowledged. **B-F12 [P3]**
between B5 and B8 the config template still renders `schema_version: "1.1.0"` while a global
skill still says to validate against the root schema file; no test gate observes it and B8,
B9, and R1-A A5 close the install, tune, and Orchestrator wording within the same shipment.
The one consumer none of them covers, `workspace-discovery` Phase 0, is out of scope here
(P-021 C1) and captured as `DEFERRED SCOPE EXPANSION` stash `44CB5AE1`, which must route
through `deliberate` (C6) before `215-S` is claimed, acknowledged. **B-F13 [P3]** B6 now
carries four checks, but the raw-YAML scan moved to R1-A, so its size and complexity are
unchanged, acknowledged. No P0, P1, or P2 findings. The delta check supports the existing
verdict: the plan remains **PASS**.

## Addendum: PR #513 review-fix cycle 3 (2026-10-12 UTC)

Append-only. The cycle 1 and cycle 2 records, both earlier addenda, and the verdict above are
unchanged. The staging PR (#513) received a third Copilot review (review 5494859553) with one
finding, touching this plan's shipment. Stage verified it against the repository, fixed it,
and re-checked only the changed units as a single-agent delta pass (same `TOOL_DEGRADED`
declarations as above). The repository test suite was not run (Stage boundary).

| Review thread | Verification and change | Commit |
|---|---|---|
| `PRRT_kwDORzpWpM6rlcW8` (comment 4251365219, `.backlogit/queue/215-S.md` line 21: the `workspace-discovery` correction was a prose-only hold, so `215-S` could be claimed after `214-S` ships without it) | Confirmed. `.github/skills/workspace-discovery/SKILL.md` Phase 0 item 1 validates an operator config against `schemas/harness-config.schema.json`, whose `schema_version` const is the current version only. A scratch probe (not committed) showed a `{schema_version: 1.0.0}` document passes its own mirror and fails the root with `'1.1.0' was expected`; B5 makes the same true of 1.1.0, the version every installed workspace declares. `verify-workspace` is unaffected (it uses `resolve_contract_schema_path`). The other consumers are owned: `install-harness` by B8, `tune-harness` by B9, the Orchestrator template by R1-A A5. The cause is B5's own authorized cut-over on the same contract surface, so it is completed here (P-021 C1), not deferred again. New task **B4a** (`208.014-T`, `S` / `low`) rewrites the Phase 0 wording to select the mirror matching the document's own `schema_version` and adds a version-agnostic regression test (reads the version only through the B3a helper); edges `208.006-T` -> `208.014-T` and `208.014-T` -> `208.003-T`; manifest order `... 208.005-T, 208.014-T, 208.006-T ...`; B9 gains an end-of-shipment sweep over the three global skills; invariant I11; stash `44CB5AE1` archived with a forward reference | `2f851bc2` |

Audit for other prose-only gates in the staged artifacts (greps for "before ... is claimed",
"must be decided before", "do not claim", "decide before", "hold"): the only claim hold that
lived solely in free text was `44CB5AE1`, now materialized. Not gates on `214-S` or `215-S`:
`207-S` is a hold gate that already exists as a backlog item (the 168-S distribution
re-plan) and is not a predecessor; the follow-up stash entries `C2EA31FA` (R2), `C5801D7B`
(R3), `507B2139` (R4, gated on `9B582824` component A, which gates its own future staging)
and `56654C18` (post-ship tune chore) gate nothing claimable; the "do not claim P-013.7" text
in B10 reserves a policy number, not a shipment.

Delta persona pass over the changed units:

* **Architecture Strategist.** The root schema tracks only the current version, so every
  agent-executed consumer must select the schema by the document's own `schema_version`, the
  rule `resolve_contract_schema_path` already applies for `verify-workspace`. B4a follows the
  same migration-first pattern as B3a/B3b: its wording is correct before and after the
  cut-over, so it lands first and B5 depends on it. The graph is `B3a -> B3b -> B5`,
  `B3a -> B4a -> B5`, `B4 -> B5`, `{B1, B2, B5} -> B6`; acyclic. The `215-S` manifest
  (15 items) honors every task edge; no shipment-level edge changed, and
  `autoharness gate dag-readiness` still reports `cycle_detected: false` and
  `ready_set: [209-S]`.
* **Python Reviewer.** No `src/` file changes. B4a's test is version-agnostic: the current
  version and mirror come only from the B3a helper, the legacy set is every non-current
  mirror on disk, and both directions of the hazard are asserted (selected mirror accepts,
  root rejects a non-current version), so it stays green before and after B5 and B5's gate
  re-runs it unmodified.
* **Scope Boundary Auditor.** B4a is three files and one concern (skill prose, its manifest
  checksum, its test); no template, CLI, schema, config, policy, or routing value is touched
  and width isolation holds. B5 changes only by an added prerequisite and a fifth acceptance
  criterion; B8 and B9 gain notes, and B9 gains one read-only sweep scenario inside its own
  new test file (still `S` / `low`). The runtime-validation tokens that
  `workspace_discovery_runtime_validation_contract` pins stay untouched.
* **Constitution Reviewer and Learnings Researcher.** The reclassification (P-021 C1) is
  recorded in `040-DL` D11 and supersedes the cycle 2 deferral, so no separate deliberation
  artifact is required under C6. The compound learning on reading full stash text for holds
  applies: a hold must be a backlog edge, not prose. No conflict.

New findings: **B-F14 [P3]** the cycle 2 addendum's B-F12 text (the `workspace-discovery` gap
"is out of scope ... must route through `deliberate` before `215-S` is claimed") described
that state and is superseded by this addendum; the earlier record is left unaltered,
acknowledged. **B-F15 [P3]** B8 and B9 still land after B5 (B8 depends on B5, B9 on B7 and
B8), so `install-harness` and `tune-harness` keep a prose window inside the one unreleased
shipment where the suite stays green (I10); it is closed by the B9 sweep (I11) rather than by
reordering, acknowledged. **B-F16 [P3]** `215-S` now holds 15 manifest members (14 tasks,
histogram `M:8`, `S:6`), acknowledged. No P0, P1, or P2 findings. The delta check supports
the existing verdict: the plan remains **PASS**.

## Addendum: PR #513 review-fix cycle 4 (2026-10-12 UTC)

Append-only. The cycle 1 to cycle 3 records, all earlier addenda, and the verdict above are
unchanged. This is review-fix cycle **4**: the three-cycle limit was reached in cycle 3 and
the operator explicitly authorized one more cycle (disposition recorded: "Option 1: extend
the cycle limit by one"). The staging PR (#513) received a fourth Copilot review (review
5495212123) with one finding on this plan. Stage verified it against the repository, fixed
it, and re-checked only the changed units as a single-agent delta pass (same
`TOOL_DEGRADED` declarations as above). The repository test suite was not run (Stage
boundary).

| Review thread | Verification and change | Commit |
|---|---|---|
| `PRRT_kwDORzpWpM6rmKbh` (comment 4251665186, plan line 213: `FC_MANAGED_CLASSES` also includes `managed-community`, but B2 derives `default_tier` only for `managed-rendered`, so a community agent registers `managed=True, default_tier=None` and cannot resolve its template default) | Confirmed. `_fc_build_provenance_index` assigns `managed-community` from a manifest `community_templates[]` entry alone and carries its `template_path`; `_fc_evaluate_target` sets `managed = artifact_class in FC_MANAGED_CLASSES`, and `frontmatter_conformity` fails managed community files closed exactly like rendered ones. The shipped community template (`templates/community/agents/adr-generator.agent.md.tmpl`, also the `template_path` its `templates/community/registry.yaml` entry exposes) declares `max_subagent_tier: 2` and `model_family: "{{TIER_2_FAMILY}}"` and is rendered by the same `_render_template` (plain `{{KEY}}` replacement); `_fc_rendered_candidate` already resolves a community `template_path` through `_fc_contained_community_source` (relative, existing file inside `autoharness_home/templates/`). So an unbound community agent resolved no route: B7 would skip it or fail it as `ROUTING_UNRESOLVED`, and B6a gave it no overlay. Fix: B2 derives `default_tier` for both template-backed classes through **one** `{{TIER_<N>_FAMILY}}` frontmatter parse (community from the manifest `template_path`, the existing containment rule reused), `SiteRegistry` gains `unresolved` (id to reason: `template-path-unusable`, `template-unreadable`, `no-tier-placeholder`, `ambiguous-tier`; `SiteSpec` keeps three fields), the sync test covers community agent templates, and fixtures cover managed-community, missing and escaping `template_path`, no placeholder, ambiguous, and unreadable; B6a overlays both render seams; B7 compares an unbound community agent against its template default and surfaces an unresolved default (fail closed with bindings via `ROUTING_SITE_DEFAULT_UNRESOLVED`, `info` without); B6 gains a known-site test; invariant I12 | `6dffa98c` |

The drift-verification unit is B7 (`208.009-T`); B9 (`208.011-T`) is the tune-harness unit and
is unchanged (it only proposes, and the verify output already names an unresolved default).
Other managed classes in `FC_MANAGED_CLASSES`: `managed-rendered` (already derived),
`managed-community` (the finding), and `managed-source` (`auto-tune`, `auto-mergeinstall`:
manifest label "global agent definition", no template, listed in `plugin.json`, frontmatter
carries tier keys only and no route-value keys), so it correctly has no tier default and
stays dropped. This workspace's manifest has no `community_templates` entry and no community
agent is installed, so its registry and verify output are unchanged (invariant I4); community
coverage is by fixture and by the added scratch-workspace runtime check.

Delta persona pass over the changed units:

* **Architecture Strategist.** The registry now mirrors `_fc_build_provenance_index`'s
  classification on both of its manifest sources instead of one, so the disk-first join is
  complete. The class is taken from the manifest, never from template health, so an
  unusable community template stays managed (fail-closed) rather than being demoted to an
  advisory workspace-authored site. The plan dependency graph is unchanged and acyclic.
* **Python Reviewer.** The tier parse is one targeted regex over the frontmatter block (no
  YAML parse of `{{...}}` values); community resolution reuses
  `_fc_contained_community_source`, so containment precedes every read and an escaping path
  is never read (asserted at the read seam). `SiteSpec` is untouched, so the R1-A resolver
  contract and the B1 vectors do not change.
* **Scope Boundary Auditor.** No new task, file, edge, or concern: B2, B6, B6a, and B7 each
  keep their two files and `M` / `medium`; the increments are one more template source for
  the same parse (B2), a second render seam in the same file (B6a), one more drift state
  (B7), and one known-site scenario (B6). The `215-S` manifest is unchanged (15 members,
  histogram `M:8`, `S:6`).
* **Constitution Reviewer and Learnings Researcher.** The fix completes the same
  contract surface the finding named (P-021 C1), so nothing is deferred and no
  `DEFERRED SCOPE EXPANSION` entry was created. The provenance split (`037-DL`) and the
  fail-closed-managed rule are reused, not reinvented.

New findings: **B-F17 [P3]** B2's manifest-orphan rule covered `artifacts[]` only, the same
root cause as the finding (community entries invisible to the manifest side of the join);
extended to `community_templates[]` with a fixture, acknowledged. **B-F18 [P3]**
`SiteRegistry` gained a fourth field (`unresolved`), the same shape change as B-F9; B6 and B7
were updated in the same revision, acknowledged. **B-F19 [P3]** `ROUTING_SITE_DEFAULT_UNRESOLVED`
is a verify-level code defined in B7, not a resolver code, and fails only under the bindings
opt-in, so I4 holds, acknowledged. **B-F20 [P3]** a managed-rendered file with a missing
template source is demoted by the classifier to unknown-provenance (workspace-authored) while
a community file with an unusable template stays managed with an unresolved default; the
asymmetry follows the existing classifier and is recorded in B2, acknowledged. No P0, P1, or
P2 findings. The delta check supports the existing verdict: the plan remains **PASS**.

Graph checks: `autoharness gate dag-readiness --json` reports `cycle_detected: false` and
`ready_set: [209-S]`; the `214-S` (7 items) and `215-S` (15 items) manifests honor every
task edge and no edge leaves either manifest; no edge changed.

## Addendum: PR #513 review-fix cycle 5 (2026-10-12 UTC)

Append-only. The cycle 1 to cycle 4 records, all earlier addenda, and the verdict above are
unchanged. This is review-fix cycle **5**: the operator explicitly authorized a further
extension of the review-fix cycle limit by one (disposition recorded: "Extend by one more
cycle"), and this is the **last** extension; if more findings remain after it, the
Orchestrator escalates. The staging PR (#513) received a fifth Copilot review on HEAD
`790e28c0` with three threads that are one design cluster: how a **bound** managed agent is
rendered and then verified. Stage verified each against the repository, fixed them together
as one coherent correction (one commit, `9fa41513`), and re-checked the changed units as a
single-agent delta pass (same `TOOL_DEGRADED` declarations as above). The repository test
suite and linters were not run (Stage boundary).

| Review thread | Verification and change | Commit |
|---|---|---|
| `PRRT_kwDORzpWpM6rmyoO` (comment 4251926657, `.backlogit/queue/208.009-T.md` line 28: B6a skips the binding overlay when a managed site's `default_tier` is unresolved, but the same bound site could resolve and pass B7, so reinstall or community rendering could restore a different route) | Confirmed. Before the fix B6a said a managed site with an unresolved tier "receives no overlay", B7 said "with a binding it resolves from the binding and is compared normally", and B6 said a binding on a managed-community agent "including one whose default tier is unresolved, is a known site and passes". The renderer is plain `{{KEY}}` replacement (`_render_template`, `verify_workspace.py` ~1152) fed by a variable map at both seams (the staged loop ~6049; `_fc_rendered_candidate` ~3857, where an unusable community `template_path` is `unproducible`), so a binding can reach an installed agent only by overlaying the four `TIER_<N>_*` variables of one resolved tier. All four unresolved reasons (`template-path-unusable`, `template-unreadable`, `no-tier-placeholder`, `ambiguous-tier`) leave no such target: a missing or unreadable template has nothing to render and a template with no or several tier placeholders has no single `N`. A bound unresolved site whose installed frontmatter coincidentally equaled the binding therefore passed B7 while a reinstall rendered the base route. Fix (rejected, not rendered around): `ROUTING_BINDING_UNRESOLVED_SITE: <id>: <reason>` (a verify-level code) in B6 (up front, at config validation) and in B7 (so B7 cannot pass such a site even run alone), B6a applies no overlay, and D3 states the rule once; B6 gains a parametrized scenario over the four reasons and both template-backed classes (including frontmatter equal to the binding), B7 a bound-unresolved scenario with no refresh proposal, and B6a and B7 a reinstall regression (the render output installed passes, one changed field fails). A render path that needs no `TIER_<N>_*` was evaluated and rejected: it would require a per-site placeholder family in every agent template or a post-render frontmatter rewrite, a second rendering mechanism that the prose install and tune skills and a future port would have to reproduce, only for templates that are already defective | `9fa41513` |
| `PRRT_kwDORzpWpM6rmyoz` (comment 4251926715, same file and line: the bound-agent renderer requires `config.overrides` to win, but the drift check compares frontmatter with resolver output that has no override layer, so a correctly rendered agent using an explicit `TIER_<N>_*` override is reported as drift) | Confirmed, and broader than the thread: it also affects an **unbound** agent whenever bindings are declared anywhere (the opt-in). `_derive_template_variables` assigns `_authoritative_route_variables(config)` into the base map, and that function applies `config.overrides[<VAR>]` over the config-derived value for every route-family variable, `TIER_<N>_*` included (~2864 to ~2879, ~2976); `_compose_artifact_variables` applies it again on the role overlay (~2805); the R1-A contract and 040-DL D4 give the resolver no override layer, and B7 compared raw resolver output. Fix: ONE shared composition function, `verify_workspace._compose_site_route_variables` plus the companion `_expected_site_route`, defined by B6a next to `_compose_artifact_variables` (the module that already owns `_render_template`, the override layer, and both render seams; `model_routing.py` cannot host it because its import allowlist excludes `verify_workspace`, and `model_routing_sites.py` must not import `verify_workspace` at module level). Both render seams render with its composed map, and B7 reads its expected frontmatter through the same two functions, so renderer and drift check cannot diverge by construction. Overrides apply per variable on top of the bound route exactly as on the unbound base, are keyed to the agent's own `TIER_<N>_*` names, an invalid `*_CONTEXT_TIER` override is skipped as in the existing compose paths, and `config_authoritative` has no default. B6a gains override, no-overlay, equivalence (rendered bytes parsed back equal `_expected_site_route`, plus a source assertion that no other composition exists), and reinstall scenarios; B7 gains bound and unbound override, non-authoritative, and round-trip scenarios | `9fa41513` |
| `PRRT_kwDORzpWpM6rmypP` (comment 4251926758, plan line 145: the B1/B2 precedence falls through to `site.default_tier` after a binding, conflicting with the governing D4 decision, which applies the template default tier only when a subagent has no binding, and can mix tiers) | Confirmed. D4 listed "for subagent sites with no binding, the agent's template default tier" while the plan and B1 listed `the site's default_tier` after the binding for every `agent:<id>` site. The existing per-field fallback (`_resolve_role_route_field`) runs only from a route to its own tier, never across tiers, so the plan's fall-through would let a bound tier that intentionally leaves `model_provider`, `reasoning_effort`, or `context_tier` empty inherit them from the agent's old template tier instead of keeping the runtime default or `default`. Fix: D4 and the plan now state two explicit, never-mixed branches chosen once by whether `bindings` has an entry for the site. **Unbound**: `site.default_tier` is the base. **Bound**: the binding's route is the base (binding override, catalog-delta field, the route's tier field, terminal `default` for `context_tier` only) and `site.default_tier` is never consulted, not even as a field-level fallback. B1 (`208.001-T`) adds five branch vectors (a bound tier that leaves a field empty while the site default tier would supply it, the unbound contrast, a partial catalog delta, an override-only binding, and a generic assertion that no bound `resolution_chain` names the site default tier) and an overrides-ignored vector; B6a renders the same (its overlay assigns all four variables, empty strings included); B7 fails frontmatter that carries the default tier's values | `9fa41513` |

Where the rule is stated, identically: 040-DL D3 and D4 (plus the D10 and risk rows), R1-B
plan Outcome, Requirements Trace (RB2a, RB3, RB5), Planned Contract Extensions, B1, B2, B6,
B6a, B7, B8, B9, B10, B11, Decisions, Risks, invariants I13 and I14, and Runtime
Verification, and tasks `208.001-T`, `208.002-T`, `208.007-T`, `208.008-T`, `208.009-T`,
`208.010-T` to `208.013-T`, and the `208-F` summary. The managed-community text from cycle 4
holds under the same two branches (an unbound community agent resolves its template default
tier exactly as a rendered one; a bound one resolves from its binding and must have a resolvable
default tier). R1-A was checked for the same gap: it has no agent sites (so no bound/unbound
issue) but its contract never said the resolver excludes `config.overrides`; that is now
explicit in the R1-A plan, A2 (one vector), and A3 (the override layer is not delegated), see
the R1-A record's cycle 5 addendum.

Delta persona pass over the changed units (B1, B2, B6, B6a, B7, B8 to B11, D3, D4, D10, and
R1-A A2 and A3):

* **Architecture Strategist.** The composition lives where the renderer and the override
  layer already live, so the resolver stays pure (its import allowlist and the standalone
  import of `model_routing_sites` are untouched) and the renderer and the drift check share
  one function instead of two derivations. The branch statement is identical across D4, B1,
  B6a, and B7 (a grep for the old fall-through and "resolves from the binding and is
  compared" phrases finds none outside the append-only earlier addenda). The dependency graph
  is unchanged and acyclic.
* **Python Reviewer.** The overlay assigns empty strings rather than skipping them (a
  skip-empty overlay would re-create the cross-tier inheritance at render time);
  `config_authoritative` is a required keyword (the older compose helpers' `True` default is
  the residual recorded in stash `09DFC9F9` item 3, left as is); the registry is built once
  per verify run and passed to both seams; no new import cycle.
* **Scope Boundary Auditor.** No new task, file, edge, or manifest change: B6a and B7 keep two
  files and one concern each (render composition; the drift verdict), B6 gains one failing
  branch, and R1-A gains one vector and one statement. The one thing that is genuinely out of
  scope, whether R3's invocation-time route and `routing resolve` should include the
  render-time overrides layer that R1 keeps outside the resolver, is captured as `DEFERRED
  SCOPE EXPANSION` stash `EB56281C` (P-021 C2; duplicate scan clean; all source refs populated,
  so no late-identifier reconciliation applies). Rejecting a binding on an unresolved-default
  site completes the same contract surface the finding named (P-021 C1), so it is not a
  deferral.
* **Constitution Reviewer and Learnings Researcher.** No source, template, schema, config, or
  policy file was touched. The fix reuses two precedents rather than inventing a scheme: the
  fail-closed managed rule (`037-DL`) and the single-shared-function rule the repo already
  follows for escalation (`_effective_escalation_context_tier_for_role` serves both the
  render and its check "so the render and the check cannot diverge"). No prose-only gate was
  added: the rejection is a named verify token with tests, and the equivalence is a test plus
  a source assertion.

New findings: **B-F21 [P2, fixed]** a bound site on an unresolved default tier could pass B7
while B6a could not apply its binding (thread `PRRT_kwDORzpWpM6rmyoO`). **B-F22 [P2, fixed]**
the drift check compared raw resolver output, so an explicit `TIER_<N>_*` override was
reported as drift for bound and unbound agents (thread `PRRT_kwDORzpWpM6rmyoz`). **B-F23 [P2,
fixed]** the B1/B2 precedence fell through to the site default tier after a binding,
contradicting D4 and mixing tiers (thread `PRRT_kwDORzpWpM6rmypP`). **B-F24 [P3]**
overrides are keyed to the variable names the agent's template renders, so an override on the
bound route's own tier variables (`TIER_<T>_*`, `T` different from the agent's `N`) does not
reach a bound agent; the rule is stated in D4, the plan, and B6a, and tested, acknowledged.
**B-F25 [P3]** the overlay must assign empty strings, stated and tested in B6a, acknowledged.
**B-F26 [P3]** the R1-A contract did not state that the resolver excludes `config.overrides`
(fixed in R1-A; the CLI-versus-overrides question is `EB56281C`), acknowledged. **B-F27 [P3]**
B7's scenarios are restated as one parametrized matrix plus seven targeted scenarios (and
B6a's grow from five to eight) in the same files, acknowledged. No P0 or P1 findings; the
three P2 findings are fixed in this revision. The delta check supports the existing verdict:
the plan remains **PASS**.

Sizes and the 2-hour rule (`ah-stage-sizing-v1`, no value changed): B1, B2, B6, B6a, and B7
stay `M` / `medium`. B1 adds five rows to one parametrized fixture; B2 changes no code or
test; B6 adds one failing branch and one parametrized scenario; B6a is the overlay it already
owned plus a small accessor and the empty-overwrite rule (five to eight scenarios, one fixture
helper, two files); B7 gets thinner and class-agnostic because it reads the expectation from
B6a's function instead of deriving one. Nothing needed a split, so no task, edge, or manifest
order changed.

Graph checks: `autoharness gate dag-readiness --json` reports `cycle_detected: false` and
`ready_set: [209-S]`; the `214-S` (7 items; 6 tasks, `M:4`, `S:2`) and `215-S` (15 items; 14
tasks, `M:8`, `S:6`) manifests honor every task edge and no edge leaves either manifest; no
edge, manifest order, size, or complexity value changed.
