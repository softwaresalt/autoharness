---
spike_id: 151.006-T
title: "De-risking prerequisite: verify_workspace assertion-table enumeration and source-of-truth resolution"
status: complete
recommendation: proceed
date: 2026-09-05
task: 151.006-T
parent_feature: 151-F
shipment: 159-S
plan: docs/plans/2026-08-31-ship1-v1_5_0-guardrail-contract-restoration-plan.md
source_stash: 053E2BD2
doc_type: spike
safety_mode: "careful + investigate-first"
---

# Verifier assertion-table enumeration and source-of-truth resolution

Recorded findings only. **No production edits, no harness code, no assertion
changes** were made by this task (SHIP-1 plan, task 0 scope bound). This
document supplies all four deliverables that `151.003-T` (the render harness)
consumes.

Measured at branch `feat/159-s-ship-1-v1-5-0-shipped-guardrail-contract-restoration`
on 2026-09-05 against `src/autoharness/verify_workspace.py`.

## Deliverable 1 — Enumeration and measured count

The plan (cycle 0) cited "~71". **Measured: exactly 71.** The number was
computed, not inherited:

| Table | Entries |
|---|---|
| `PACK_ASSERTIONS` (9 packs, flattened) | 23 |
| `FOUNDATION_ASSERTIONS` | 40 |
| `DARK_FACTORY_ASSERTIONS` | 8 |
| **Total** | **71** |

`PACK_ASSERTIONS` per pack: `backlogit` 12, `graphtor-docs` 3,
`agent-intercom` 2, and 1 each for `strict-safety`, `agent-engram`,
`adversarial-review`, `release-observability`, `browser-verification`,
`continuous-learning`.

All 71 `key` values are **distinct** (71 unique keys), so a sweep may be keyed
by assertion `key` with no collision handling. The 71 assertions address only
**29 distinct `path` values** — the render harness must therefore cache by
resolved source path, not by assertion, or it will re-render the same file up
to 13 times.

Assertion entry shape (all three tables share it): `key`, `path`,
`must_contain` (list of literal substrings), optional `must_precede` (list of
`[first, second]` ordering pairs). `DARK_FACTORY_ASSERTIONS` entries carry two
extra gating keys — `required` (bool) and `requires_pack` (pack name) — which
only affect *whether* verify runs the check in a given workspace, not how its
path resolves.

Evaluation entry point for all three tables is `_add_text_check`
(`verify_workspace.py:4041`), which reads `workspace_path / assertion["path"]`
— i.e. the **installed** copy. That is precisely the blindness H2 targets.

## Deliverable 2 — Source-of-truth resolution for every assertion

Rule applied (binding H2): resolve to the `.tmpl` when one exists; fall back to
the installed file **only** when no template exists.

**Result: 58 of 71 assertions resolve to a `.tmpl`; 13 resolve to an
installed-only file. Zero are unresolvable. Zero are ambiguous** (no assertion
path produced more than one existing candidate template).

### Resolution mechanism (important negative finding)

`_resolve_source_template()` (`verify_workspace.py:1982`) **cannot** be reused
for this mapping. It resolves from the manifest artifact's `template` field,
and for the highest-value assertion targets that field is a prose label, not a
path:

* `.github/agents/_ship.agent.md` → `template: "global agent definition"`
* `.github/agents/_stage.agent.md` → `template: "global agent definition"`
* `.github/skills/install-harness/SKILL.md` → `template: "global skill definition"`
* `.github/instructions/harness-architecture.instructions.md` → `template: "global instruction definition"`

None of those strings start with `templates/`, end with a known suffix, or
appear in `WORKSPACE_SOURCE_TEMPLATES`, so `_resolve_source_template` returns
`(None, None)` for them. Worse, 7 of the 29 assertion paths are **not present
in the dogfood manifest at all** (their packs are not installed here):
`adversarial-review`, `backlogit-sql-schema`, `backlogit-yaml-header-tooling`,
`browser-verification`, `continuous-learning`, `release-observability`,
`strict-safety` instruction files. A manifest-driven mapping would silently
skip them.

**Therefore the harness must use a deterministic convention mapping** from
installed path to template path, and fall back to the installed file only when
that template does not exist on disk:

| Installed path prefix | Template path |
|---|---|
| `.github/agents/<name>` | `templates/agents/<name>.tmpl` |
| `.github/instructions/<name>` | `templates/instructions/<name>.tmpl` |
| `.github/prompts/<name>` | `templates/prompts/<name>.tmpl` |
| `.github/policies/<name>` | `templates/policies/<name>.tmpl` |
| `.github/skills/<dir>/<name>` | `templates/skills/<dir>/<name>.tmpl` |
| `AGENTS.md` | `templates/foundation/AGENTS.md.tmpl` |
| `.github/copilot-instructions.md` | `templates/foundation/copilot-instructions.md.tmpl` |

This mapping covers all 29 distinct assertion paths with no residue.

### The 13 legitimately installed-only assertions

These 5 paths have **no** `.tmpl` because they are autoharness's *own engine*
artifacts (the installer/tuner/discovery surfaces), not generated harness
output. Reading the installed file for these is the H2-correct behaviour, not a
degradation:

| Path | Assertions |
|---|---|
| `.github/skills/install-harness/SKILL.md` | `install_harness_runtime_validation_contract`, `install_harness_two_agent_role_enforcement`, `install_harness_browser_skill_manifest`, `install_harness_browser_verification_overlay`, `pipeline_topology_gate_install_wiring` |
| `.github/skills/tune-harness/SKILL.md` | `tune_harness_runtime_validation_contract`, `tune_harness_learning_loop_contract`, `tune_harness_dynamic_policy_generation`, `pipeline_topology_gate_tune_wiring` |
| `.github/agents/auto-tune.agent.md` | `auto_tune_learning_loop_contract`, `auto_tune_dynamic_policy_phase` |
| `.github/skills/workspace-discovery/SKILL.md` | `workspace_discovery_runtime_validation_contract` |
| `.github/instructions/harness-architecture.instructions.md` | `harness_architecture_runtime_validation_contract` |

**No ambiguous or unresolvable entries were found.** The list of entries that
would "silently degrade the sweep back into reading dogfood copies" is exactly
the 13 above, and each is justified by the absence of a template — the harness
must record the resolution *kind* per assertion so this stays auditable rather
than accidental.

### Full per-assertion table

Columns: index, table, assertion key, verifier `path`, resolved
source-of-truth, resolution kind.

| # | Table | Key | Verifier `path` | Source-of-truth | Kind |
|---|---|---|---|---|---|
| 1 | PACK_ASSERTIONS[`backlogit`] | `backlogit_instruction_guidance` | `.github/instructions/backlogit.instructions.md` | `templates/instructions/backlogit.instructions.md.tmpl` | `.tmpl` |
| 2 | PACK_ASSERTIONS[`backlogit`] | `backlogit_checkpoint_recovery_protocol` | `.github/instructions/backlogit.instructions.md` | `templates/instructions/backlogit.instructions.md.tmpl` | `.tmpl` |
| 3 | PACK_ASSERTIONS[`backlogit`] | `orchestrator_crash_resumption_protocol` | `.github/agents/_orchestrator.agent.md` | `templates/agents/_orchestrator.agent.md.tmpl` | `.tmpl` |
| 4 | PACK_ASSERTIONS[`backlogit`] | `stage_crash_resumption_protocol` | `.github/agents/_stage.agent.md` | `templates/agents/_stage.agent.md.tmpl` | `.tmpl` |
| 5 | PACK_ASSERTIONS[`backlogit`] | `ship_crash_resumption_protocol` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 6 | PACK_ASSERTIONS[`backlogit`] | `backlogit_sql_schema_instruction` | `.github/instructions/backlogit-sql-schema.instructions.md` | `templates/instructions/backlogit-sql-schema.instructions.md.tmpl` | `.tmpl` |
| 7 | PACK_ASSERTIONS[`backlogit`] | `backlogit_yaml_header_instruction` | `.github/instructions/backlogit-yaml-header-tooling.instructions.md` | `templates/instructions/backlogit-yaml-header-tooling.instructions.md.tmpl` | `.tmpl` |
| 8 | PACK_ASSERTIONS[`backlogit`] | `agents_metadata_catalog_guidance` | `AGENTS.md` | `templates/foundation/AGENTS.md.tmpl` | `.tmpl` |
| 9 | PACK_ASSERTIONS[`backlogit`] | `ship_source_artifact_cleanup` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 10 | PACK_ASSERTIONS[`backlogit`] | `closure_source_artifact_cleanup` | `.github/skills/operational-closure/SKILL.md` | `templates/skills/operational-closure/SKILL.md.tmpl` | `.tmpl` |
| 11 | PACK_ASSERTIONS[`backlogit`] | `stage_index_sync_gate` | `.github/agents/_stage.agent.md` | `templates/agents/_stage.agent.md.tmpl` | `.tmpl` |
| 12 | PACK_ASSERTIONS[`backlogit`] | `ship_index_sync_gate` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 13 | PACK_ASSERTIONS[`strict-safety`] | `strict_safety_instruction` | `.github/instructions/strict-safety.instructions.md` | `templates/instructions/strict-safety.instructions.md.tmpl` | `.tmpl` |
| 14 | PACK_ASSERTIONS[`agent-intercom`] | `agent_intercom_instruction` | `.github/instructions/agent-intercom.instructions.md` | `templates/instructions/agent-intercom.instructions.md.tmpl` | `.tmpl` |
| 15 | PACK_ASSERTIONS[`agent-intercom`] | `review_intercom_workflow` | `.github/skills/review/SKILL.md` | `templates/skills/review/SKILL.md.tmpl` | `.tmpl` |
| 16 | PACK_ASSERTIONS[`agent-engram`] | `agent_engram_instruction` | `.github/instructions/agent-engram.instructions.md` | `templates/instructions/agent-engram.instructions.md.tmpl` | `.tmpl` |
| 17 | PACK_ASSERTIONS[`adversarial-review`] | `adversarial_review_instruction` | `.github/instructions/adversarial-review.instructions.md` | `templates/instructions/adversarial-review.instructions.md.tmpl` | `.tmpl` |
| 18 | PACK_ASSERTIONS[`release-observability`] | `release_observability_instruction` | `.github/instructions/release-observability.instructions.md` | `templates/instructions/release-observability.instructions.md.tmpl` | `.tmpl` |
| 19 | PACK_ASSERTIONS[`browser-verification`] | `browser_verification_instruction` | `.github/instructions/browser-verification.instructions.md` | `templates/instructions/browser-verification.instructions.md.tmpl` | `.tmpl` |
| 20 | PACK_ASSERTIONS[`continuous-learning`] | `continuous_learning_instruction` | `.github/instructions/continuous-learning.instructions.md` | `templates/instructions/continuous-learning.instructions.md.tmpl` | `.tmpl` |
| 21 | PACK_ASSERTIONS[`graphtor-docs`] | `graphtor_docs_instruction` | `.github/instructions/graphtor-docs.instructions.md` | `templates/instructions/graphtor-docs.instructions.md.tmpl` | `.tmpl` |
| 22 | PACK_ASSERTIONS[`graphtor-docs`] | `graphtor_docs_stage_weaving` | `.github/agents/_stage.agent.md` | `templates/agents/_stage.agent.md.tmpl` | `.tmpl` |
| 23 | PACK_ASSERTIONS[`graphtor-docs`] | `graphtor_docs_ship_weaving` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 24 | FOUNDATION_ASSERTIONS | `copilot_durable_knowledge_layout` | `.github/copilot-instructions.md` | `templates/foundation/copilot-instructions.md.tmpl` | `.tmpl` |
| 25 | FOUNDATION_ASSERTIONS | `copilot_session_memory_guidance` | `.github/copilot-instructions.md` | `templates/foundation/copilot-instructions.md.tmpl` | `.tmpl` |
| 26 | FOUNDATION_ASSERTIONS | `copilot_remote_operator_guidance` | `.github/copilot-instructions.md` | `templates/foundation/copilot-instructions.md.tmpl` | `.tmpl` |
| 27 | FOUNDATION_ASSERTIONS | `copilot_backlog_workflow_expectations` | `.github/copilot-instructions.md` | `templates/foundation/copilot-instructions.md.tmpl` | `.tmpl` |
| 28 | FOUNDATION_ASSERTIONS | `copilot_code_review_focus_instruction` | `.github/instructions/copilot-code-review.instructions.md` | `templates/instructions/copilot-code-review.instructions.md.tmpl` | `.tmpl` |
| 29 | FOUNDATION_ASSERTIONS | `workspace_discovery_runtime_validation_contract` | `.github/skills/workspace-discovery/SKILL.md` | `.github/skills/workspace-discovery/SKILL.md` | installed |
| 30 | FOUNDATION_ASSERTIONS | `install_harness_runtime_validation_contract` | `.github/skills/install-harness/SKILL.md` | `.github/skills/install-harness/SKILL.md` | installed |
| 31 | FOUNDATION_ASSERTIONS | `tune_harness_runtime_validation_contract` | `.github/skills/tune-harness/SKILL.md` | `.github/skills/tune-harness/SKILL.md` | installed |
| 32 | FOUNDATION_ASSERTIONS | `ship_runtime_validation_contract` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 33 | FOUNDATION_ASSERTIONS | `harness_architecture_runtime_validation_contract` | `.github/instructions/harness-architecture.instructions.md` | `.github/instructions/harness-architecture.instructions.md` | installed |
| 34 | FOUNDATION_ASSERTIONS | `stage_shipment_determinism` | `.github/agents/_stage.agent.md` | `templates/agents/_stage.agent.md.tmpl` | `.tmpl` |
| 35 | FOUNDATION_ASSERTIONS | `stage_role_boundary` | `.github/agents/_stage.agent.md` | `templates/agents/_stage.agent.md.tmpl` | `.tmpl` |
| 36 | FOUNDATION_ASSERTIONS | `ship_role_boundary` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 37 | FOUNDATION_ASSERTIONS | `ship_release_closure_sequence` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 38 | FOUNDATION_ASSERTIONS | `orchestrator_release_closure_sequence` | `.github/agents/_orchestrator.agent.md` | `templates/agents/_orchestrator.agent.md.tmpl` | `.tmpl` |
| 39 | FOUNDATION_ASSERTIONS | `install_harness_two_agent_role_enforcement` | `.github/skills/install-harness/SKILL.md` | `.github/skills/install-harness/SKILL.md` | installed |
| 40 | FOUNDATION_ASSERTIONS | `stage_tool_availability_gate` | `.github/agents/_stage.agent.md` | `templates/agents/_stage.agent.md.tmpl` | `.tmpl` |
| 41 | FOUNDATION_ASSERTIONS | `ship_branch_management` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 42 | FOUNDATION_ASSERTIONS | `ship_branch_creation_gate` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 43 | FOUNDATION_ASSERTIONS | `ship_tool_availability_gate` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 44 | FOUNDATION_ASSERTIONS | `ship_merge_confirmation_gate` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 45 | FOUNDATION_ASSERTIONS | `ship_post_merge_compaction_gate` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 46 | FOUNDATION_ASSERTIONS | `pr_lifecycle_branch_retention` | `.github/skills/pr-lifecycle/SKILL.md` | `templates/skills/pr-lifecycle/SKILL.md.tmpl` | `.tmpl` |
| 47 | FOUNDATION_ASSERTIONS | `auto_tune_learning_loop_contract` | `.github/agents/auto-tune.agent.md` | `.github/agents/auto-tune.agent.md` | installed |
| 48 | FOUNDATION_ASSERTIONS | `tune_harness_learning_loop_contract` | `.github/skills/tune-harness/SKILL.md` | `.github/skills/tune-harness/SKILL.md` | installed |
| 49 | FOUNDATION_ASSERTIONS | `security_review_persona_routing` | `.github/skills/review/SKILL.md` | `templates/skills/review/SKILL.md.tmpl` | `.tmpl` |
| 50 | FOUNDATION_ASSERTIONS | `local_review_readiness_contract` | `.github/skills/review/SKILL.md` | `templates/skills/review/SKILL.md.tmpl` | `.tmpl` |
| 51 | FOUNDATION_ASSERTIONS | `template_integrity_reviewer_routing` | `.github/skills/review/SKILL.md` | `templates/skills/review/SKILL.md.tmpl` | `.tmpl` |
| 52 | FOUNDATION_ASSERTIONS | `schema_cli_docs_reviewer_routing` | `.github/skills/review/SKILL.md` | `templates/skills/review/SKILL.md.tmpl` | `.tmpl` |
| 53 | FOUNDATION_ASSERTIONS | `security_plan_review_persona_routing` | `.github/skills/plan-review/SKILL.md` | `templates/skills/plan-review/SKILL.md.tmpl` | `.tmpl` |
| 54 | FOUNDATION_ASSERTIONS | `install_harness_browser_skill_manifest` | `.github/skills/install-harness/SKILL.md` | `.github/skills/install-harness/SKILL.md` | installed |
| 55 | FOUNDATION_ASSERTIONS | `install_harness_browser_verification_overlay` | `.github/skills/install-harness/SKILL.md` | `.github/skills/install-harness/SKILL.md` | installed |
| 56 | FOUNDATION_ASSERTIONS | `tune_harness_dynamic_policy_generation` | `.github/skills/tune-harness/SKILL.md` | `.github/skills/tune-harness/SKILL.md` | installed |
| 57 | FOUNDATION_ASSERTIONS | `auto_tune_dynamic_policy_phase` | `.github/agents/auto-tune.agent.md` | `.github/agents/auto-tune.agent.md` | installed |
| 58 | FOUNDATION_ASSERTIONS | `p013_policy_in_workflow_policies` | `.github/policies/workflow-policies.md` | `templates/policies/workflow-policies.md.tmpl` | `.tmpl` |
| 59 | FOUNDATION_ASSERTIONS | `p014_local_review_policy` | `.github/policies/workflow-policies.md` | `templates/policies/workflow-policies.md.tmpl` | `.tmpl` |
| 60 | FOUNDATION_ASSERTIONS | `pipeline_topology_gate_install_wiring` | `.github/skills/install-harness/SKILL.md` | `.github/skills/install-harness/SKILL.md` | installed |
| 61 | FOUNDATION_ASSERTIONS | `pipeline_topology_gate_tune_wiring` | `.github/skills/tune-harness/SKILL.md` | `.github/skills/tune-harness/SKILL.md` | installed |
| 62 | FOUNDATION_ASSERTIONS | `pipeline_topology_gate_ship_agent_wiring` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 63 | FOUNDATION_ASSERTIONS | `pipeline_topology_gate_orchestrator_agent_wiring` | `.github/agents/_orchestrator.agent.md` | `templates/agents/_orchestrator.agent.md.tmpl` | `.tmpl` |
| 64 | DARK_FACTORY_ASSERTIONS | `dark_factory_policy_contract` | `.github/policies/workflow-policies.md` | `templates/policies/workflow-policies.md.tmpl` | `.tmpl` |
| 65 | DARK_FACTORY_ASSERTIONS | `dark_factory_orchestrator_contract` | `.github/agents/_orchestrator.agent.md` | `templates/agents/_orchestrator.agent.md.tmpl` | `.tmpl` |
| 66 | DARK_FACTORY_ASSERTIONS | `dark_factory_ship_contract` | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | `.tmpl` |
| 67 | DARK_FACTORY_ASSERTIONS | `dark_factory_pr_lifecycle_contract` | `.github/skills/pr-lifecycle/SKILL.md` | `templates/skills/pr-lifecycle/SKILL.md.tmpl` | `.tmpl` |
| 68 | DARK_FACTORY_ASSERTIONS | `dark_factory_intercom_contract` | `.github/instructions/agent-intercom.instructions.md` | `templates/instructions/agent-intercom.instructions.md.tmpl` | `.tmpl` |
| 69 | DARK_FACTORY_ASSERTIONS | `dark_factory_prompt_contract` | `.github/prompts/feature-flow-dark.prompt.md` | `templates/prompts/feature-flow-dark.prompt.md.tmpl` | `.tmpl` |
| 70 | DARK_FACTORY_ASSERTIONS | `dark_factory_github_pr_automation_contract` | `.github/instructions/github-pr-automation.instructions.md` | `templates/instructions/github-pr-automation.instructions.md.tmpl` | `.tmpl` |
| 71 | DARK_FACTORY_ASSERTIONS | `dark_factory_foundation_contract` | `AGENTS.md` | `templates/foundation/AGENTS.md.tmpl` | `.tmpl` |

## Deliverable 3 — Variable tables the render harness must reuse

H2 forbids inventing a parallel substitution path. The harness reuses these
`autoharness.verify_workspace` members verbatim:

| Member | Role |
|---|---|
| `_derive_template_variables(workspace_path, manifest, config, profile, registry)` | The single variable table. Produced **194 variables** against the live `.autoharness/` fixtures. |
| `_render_template(content, variables)` | The substitution engine — a plain `str.replace` loop over `{{KEY}}`. No `eval`, no shell, no network (plan review finding 6 is satisfied by reuse alone). |
| `_resolve_artifact_role(relative_path)` | Maps `.github/agents/_stage.agent.md` → `stage`, `.github/agents/_ship.agent.md` → `ship`, else `None`. |
| `_compose_artifact_variables(base, model_routing, role)` | Overlays the role-scoped `{{ESCALATION_FAMILY/PROVIDER/REASONING_EFFORT}}` triple for those two agent artifacts. Without it, `_ship`/`_stage` renders carry the wrong escalation prose. |
| `PACK_ASSERTIONS`, `FOUNDATION_ASSERTIONS`, `DARK_FACTORY_ASSERTIONS` | Imported directly; the sweep must have **no** local copy and **no** exemption list. |
| `_add_text_check` semantics | The sweep must reproduce `must_contain` (literal substring) and `must_precede` (`find(first) < find(second)`, both present) exactly, against rendered text. |

Fixture inputs are the live repository files, loaded the same way
`tests/test_template_variable_derivation_contract.py::_load_live_fixtures`
already loads them: `.autoharness/harness-manifest.yaml`, `config.yaml`,
`workspace-profile.yaml`, `backlog-registry.yaml`. Reusing that established
pattern keeps one loading convention in the suite.

**Second (non-backlogit) variable set.** `151.001-T` acceptance requires a
zero-unresolved-`{{` render under a non-backlogit variable set as well.
`BACKLOG_DIRECTORY` is derived at `verify_workspace.py:3018` from
`registry["directory"] → config["backlog"]["directory"] →
variables["BACKLOG_DIRECTORY"]`, and `BACKLOG_TOOL_NAME` at `:3014` from
`registry["tool_name"] → config["backlog"]["tool"]`. A non-backlogit set is
therefore produced by deriving with a registry/config whose `directory` is
`backlog` and `tool_name` is `backlog-md`, and with the manifest's
`variables_used` backlog entries removed so they cannot shadow the override
(`_derive_template_variables` seeds from `variables_used` first and every later
assignment is a `setdefault`).

## Deliverable 4 — Measured wall-clock cost of a full-corpus render

Measured on the development host (Windows, CPython via `uv run`), warm cache:

| Operation | Measurement |
|---|---|
| `_derive_template_variables` (one call) | **0.095 s** |
| Full-corpus render: read + substitute **128** `templates/**/*.tmpl` files | **1.77 s** (≈ 1.16 M rendered characters) |
| Combined worst case per variable set | **< 2 s** |

Only **24 of the 128** templates are actually needed by the 71 assertions, so a
demand-driven render of just the assertion targets is well under 1 s; the 1.77 s
figure is the pessimistic upper bound if the harness renders everything.

**Decision this measurement supports (cycle-0 finding 5 mitigation):** the
budget is not exceeded. `151.004-T` may express the sweep as **one test case per
assertion** (71 cases) rather than collapsing to a single test over a prebuilt
render, provided the harness **renders once per test class and caches** — which
`151.003-T` is required to do anyway. Two variable sets (backlogit and
non-backlogit) still cost under 4 s combined, which is negligible against the
existing suite runtime.

## Consumption checklist for 151.003-T

1. Convention path map (Deliverable 2) — not `_resolve_source_template`.
2. Installed-file fallback restricted to the 5 engine paths / 13 assertions
   listed above, recorded per assertion as an explicit resolution kind.
3. Reuse `_derive_template_variables` / `_render_template` /
   `_resolve_artifact_role` / `_compose_artifact_variables` (Deliverable 3).
4. Cache the render per test class; per-assertion cases are affordable
   (Deliverable 4).
