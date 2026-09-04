---
title: "Are v1.5.0 verify-workspace guardrails internally inconsistent with the templates that generate the checked artifacts?"
source: "docs/decisions/2026-08-31-v1_5_0-guardrail-template-contract-mismatch-spike.md"
doc_type: decision
description: "Two shipped v1.5.0 guardrail assertions are unsatisfiable by the templates that generate the artifacts they check; the reported Source artifact cleanup mismatch is confirmed as a genuine template defect, and a second wording-drift defect was found that this repository's own verify run cannot surface."
docline:
  type: spike
  date: 2026-08-31
  time_box: "2h, single Stage session, read-only"
  conclusion: "proceed"
  confidence: "high"
  linked_parent_work_item: null
  promoted_to: ["queue"]
  tags:
    - "templates"
    - "verification"
    - "guardrails"
    - "release-quality"
---

## Goal

Are the shipped autoharness v1.5.0 verification/guardrail contracts internally
inconsistent with the templates that generate the checked artifacts — especially
the reported `Source artifact cleanup` mismatch — and what exact upstream changes
are needed?

### Operator report (provenance, preserved verbatim in meaning)

Reported after a merge-install of autoharness v1.5.0 into a separate Engram
target workspace:

> "Four v1.5.0 guardrail checks are unsatisfiable by the v1.5.0 templates
> themselves; each patched with semantically identical wording and documented for
> re-check on next upgrade. One is a genuine upstream bug: `_ship.agent.md.tmpl`
> tells Ship to write a `Source artifact cleanup` section that
> `operational-closure/SKILL.md.tmpl` never defines."

This investigation had **no access to the Engram target workspace**. Everything
below is derived from this repository at `main` HEAD `2661c1c8` and from the
published v1.5.0 wheel unpacked in `.venv/Lib/site-packages/autoharness/data/`.

## Success Criteria

1. Reproduce the `Source artifact cleanup` contract mismatch from repository files.
2. Locate the responsible guardrail verifier(s) and compare every expected token
   and ordering requirement against the source templates.
3. Determine whether exactly four checks are unsatisfiable in v1.5.0 sources; name
   each with files/lines, or state clearly that the remainder is not recoverable
   here and specify the target evidence needed.
4. Assess blast radius across templates, generated artifacts, tests, docs,
   manifests, install/tune behavior, and backward compatibility.
5. Produce a focused recommendation and capture the confirmed bug for later Stage
   planning.

## Scope Constraints

Read-only Stage investigation. No template, source, schema, test, or config
mutation. No branch, worktree, commit, PR, shipment, or Ship invocation. Only two
writes performed: this artifact and one consolidated backlogit stash entry.
`docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md`
(pre-existing untracked) was left untouched.

Degraded tool routing during this session:

* `agent-engram` — `ENGRAM_DEGRADED` (daemon did not reach Ready; no third
  attempt made per circuit-breaker rules). Structural discovery was performed by
  importing the verifier's own assertion tables in-process rather than by broad
  grep, so no structural query was answered by a raw file scan.
* `agent-intercom` — not exposed; operator visibility degraded, no broadcasts.
* `graphtor-docs` — not exposed; documentation lookups used exact known paths.

`[PACK-ROUTING] query="verify-workspace guardrail token contracts" classified=code routed=direct reason="agent-engram degraded; used exact-path reads and in-process import of PACK_ASSERTIONS/FOUNDATION_ASSERTIONS/DARK_FACTORY_ASSERTIONS rather than broad scanning" sensitivity=internal`

## Investigation Approach

1. Confirmed the reported mismatch by direct token comparison between
   `templates/agents/_ship.agent.md.tmpl`,
   `templates/skills/operational-closure/SKILL.md.tmpl`, and the verifier.
2. Imported the verifier's three assertion tables in-process
   (`PACK_ASSERTIONS`, `FOUNDATION_ASSERTIONS`, `DARK_FACTORY_ASSERTIONS`;
   71 assertions total) and resolved each checked artifact path to its
   source-of-truth (a `templates/**.tmpl` file, or a self-hosted global artifact
   shipped verbatim as package data).
3. Eliminated false positives by **rendering** each template with the concrete
   operation/status/field variable map derived from
   `.autoharness/backlog-registry.yaml` using the verifier's own
   `OPERATION_VARIABLES` / `CLI_OPERATION_VARIABLES` / `STATUS_VARIABLES` /
   `FIELD_VARIABLES` tables, then re-testing every `must_contain` token and every
   `must_precede` ordering pair.
4. Cross-checked the same tokens against the **published v1.5.0 wheel** data to
   confirm the defects are shipped, not post-release drift.
5. Enumerated the 17 dynamically-computed checks not covered by the tables, and
   classified every failure in the existing `.autoharness/staging/` report.
6. Searched prior `docs/decisions`, `docs/compound`, and backlogit records for
   related prior art and for duplicate backlog items.

## Findings

### What Was Discovered

#### F1 — The reported `Source artifact cleanup` mismatch is CONFIRMED (genuine template defect)

The guardrail:

* `src/autoharness/verify_workspace.py:303-311` — assertion
  `closure_source_artifact_cleanup`, registered under
  `PACK_ASSERTIONS["backlogit"]`:
  * `"path"`: `.github/skills/operational-closure/SKILL.md` (line 305)
  * `"must_contain"`: `Source artifact cleanup`, `source_stash_id`,
    `source_deliberation_id` (lines 306-310)

The producer side, which is correct and complete:

* `templates/agents/_ship.agent.md.tmpl:856` — post-merge Step 7
  `**Source artifact cleanup** (backlogit only)`
* `templates/agents/_ship.agent.md.tmpl:857` — reads
  `custom_fields.source_stash_id`, calls `backlogit_stash_archive`
* `templates/agents/_ship.agent.md.tmpl:858` — reads
  `custom_fields.source_deliberation_id`, calls `backlogit_archive_item`
* `templates/agents/_ship.agent.md.tmpl:859` — instructs Ship to "record the
  archived and skipped source artifact IDs in the closure artifact's
  `Source artifact cleanup` section"

The consumer side, which never defines the section:

* `templates/skills/operational-closure/SKILL.md.tmpl` — 124 lines total. Zero
  occurrences of `Source artifact cleanup`, `source_stash_id`, or
  `source_deliberation_id`. Its closure-artifact contract is
  `### Step 2: Build the Closure Checklist` (lines 65-84), a MUST-include list of
  15 sections; none of them is source-artifact cleanup. Steps 1/3/4 (lines 52,
  85, 97) likewise do not define it.
* The generated dogfood copy `.github/skills/operational-closure/SKILL.md` is
  also 124 lines with the same zero occurrences, so this is not render loss.

Independent confirmation that the **template**, not the verifier, is the defect —
the shipped install documentation already declares operational-closure as a
carrier of this contract:

* `.github/skills/install-harness/SKILL.md:720` —
  `| Source artifact cleanup | `_ship.agent.md`, `operational-closure/SKILL.md`, and closure-facing traceability guidance |`
* `.github/skills/install-harness/SKILL.md:1082` — lists source-artifact-cleanup
  among the workflows the `backlogit` pack threads through installed artifacts.
* `docs/backlogit-operating-model.md:49` and
  `docs/backlogit-compatibility-matrix.md:55` both describe the cleanup contract
  as a supported, closure-recorded capability.

So three independent surfaces (verifier, install documentation, operating-model
docs) agree that `operational-closure/SKILL.md` must carry the section, and only
the template disagrees. **Ship is instructed to write into a section that the
closure-artifact contract never defines.**

This is shipped in v1.5.0, not a working-tree regression: the published wheel at
`.venv/Lib/site-packages/autoharness/data/templates/skills/operational-closure/SKILL.md.tmpl`
has the identical three misses, while
`.venv/.../templates/agents/_ship.agent.md.tmpl:856,859` has the identical hits.
Repo `pyproject.toml:7` is `version = "1.5.0"`; the installed distribution
reports `1.5.0`; tag `v1.5.0` exists.

#### F2 — A SECOND unsatisfiable guardrail, not in the operator report: `ship_release_closure_sequence`

* `src/autoharness/verify_workspace.py:566-575` — `FOUNDATION_ASSERTIONS` entry
  `ship_release_closure_sequence`, `"path"`: `.github/agents/_ship.agent.md`,
  requiring the literal phrase at line 573:
  `another top-level release unit may not begin yet`
* `templates/agents/_ship.agent.md.tmpl:709` says instead:
  `...Treat the shipment as still active for P-001 purposes, and do not allow another top-level release unit to begin yet.`

The two phrasings are semantically identical and lexically incompatible. A fresh
render of the v1.5.0 template can never produce the required substring, so **any
new merge-install of v1.5.0 into a target workspace fails this check**.

Critically, **this repository's own `verify-workspace` run reports it as PASS**
(`.autoharness/staging/verify-workspace-report.md:79`,
`ship_release_closure_sequence: PASS`). The reason is that the dogfood artifact
`.github/agents/_ship.agent.md:607` still carries the *older* wording
(`...and another top-level release unit may not begin yet.`) while the template
was reworded without the verifier or the dogfood copy following. This defect is
therefore **invisible from inside autoharness and only observable in a foreign
install target** — which is exactly the reporting context the operator described.

The published wheel confirms the same state: the v1.5.0
`templates/agents/_ship.agent.md.tmpl:709` carries the reworded phrase and does
not contain the verifier's required phrase.

#### F3 — Exactly TWO checks are unsatisfiable in v1.5.0 sources, not four

Render-aware sweep of all 71 table-driven assertions
(`PACK_ASSERTIONS` 207-433, `FOUNDATION_ASSERTIONS` 434-863,
`DARK_FACTORY_ASSERTIONS` 864-957), with each checked path resolved to its
source-of-truth and each template rendered with the concrete backlogit variable
map before token/order evaluation:

```text
TOTAL ASSERTIONS : 71
UNSATISFIABLE    : 2
  closure_source_artifact_cleanup  [PACK:backlogit]
  ship_release_closure_sequence    [FOUNDATION]
```

All 17 dynamically-computed (non-table) checks present in the current report
(`capability_pack_enforcement`, `copilot_code_review_frontmatter`,
`escalation_directive_present`, `escalation_route_resolution`,
`installed_role_enforcement_instruction`,
`orchestrator_invocation_routing_directive`, `orchestrator_model_routing_fields`,
`orchestrator_tier_fields`, `orchestrator_workspace_identity`,
`reload_propagation_directive`, `role_route_resolution`,
`runtime_validation_profile_contract`, `session_start_reload_directive`,
`ship_model_routing_fields`, `ship_workspace_identity`,
`stage_model_routing_fields`, `stage_workspace_identity`) evaluate `ok: true`.

**The other two of the operator's four cannot be identified from this repository
and are not guessed here.** See Remaining Unknowns for the exact target evidence
required.

#### F4 — Classification of every other current failure (none is a template defect)

The existing `.autoharness/staging/verify-workspace-report.md` shows 11 failing
targeted checks. Their correct classification:

| Check | Class | Why |
|---|---|---|
| `closure_source_artifact_cleanup` | **template defect** | F1 — template cannot satisfy it |
| `ship_release_closure_sequence` (reported PASS) | **template defect, masked** | F2 — only fails on fresh install |
| `backlogit_sql_schema_instruction` | generated-install drift | `templates/instructions/backlogit-sql-schema.instructions.md.tmpl` exists and install wiring exists (`.github/skills/install-harness/SKILL.md:628, 815, 1082`); the file is simply not installed in this repo's dogfood |
| `backlogit_yaml_header_instruction` | generated-install drift | same as above |
| `agents_metadata_catalog_guidance` | generated-install drift | `templates/foundation/AGENTS.md.tmpl` satisfies the tokens after render |
| `ship_source_artifact_cleanup` | generated-install drift | `templates/agents/_ship.agent.md.tmpl:857-858` has all four tokens; the stale dogfood `.github/agents/_ship.agent.md` has only `source_stash_id`/`backlogit_stash_archive` at line 47 |
| `copilot_durable_knowledge_layout` | generated-install drift | `templates/foundation/copilot-instructions.md.tmpl` satisfies |
| `copilot_session_memory_guidance` | generated-install drift | same |
| `copilot_remote_operator_guidance` | generated-install drift | same |
| `copilot_backlog_workflow_expectations` | generated-install drift | same |
| `stage_shipment_determinism` | generated-install drift | `templates/agents/_stage.agent.md.tmpl` satisfies |
| `ship_branch_management` | generated-install drift | `templates/agents/_ship.agent.md.tmpl` satisfies |

This drift is **expected and previously ratified**, not a new finding:
`docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md` concluded
"adopt paired-edit contract; do not extend the renderer" for the `_ship`,
`_stage`, `_orchestrator`, and `github-pr-automation` template/dogfood pairs, and
`tests/test_scope_containment_policy_contract.py:870-881` explicitly documents the
`Source artifact cleanup` template/dogfood divergence as pre-existing and
deliberately out of scope for that feature.

#### F5 — Wording-brittleness class exists but is NOT a defect

Four checks initially appeared unsatisfiable against raw template text and were
cleared once rendering was applied. They depend on registry-driven substitution
and are correct by design:

* `stage_index_sync_gate` / `ship_index_sync_gate` — require `backlogit_sync_index`;
  templates emit `{{OP_SYNC_INDEX_MCP}}`
  (`templates/agents/_stage.agent.md.tmpl:184,726`,
  `templates/agents/_ship.agent.md.tmpl:122,862`), which resolves to
  `backlogit_sync_index` from `.autoharness/backlog-registry.yaml`.
* `pipeline_topology_gate_ship_agent_wiring`
  (`src/autoharness/verify_workspace.py:800-842`) — its `must_precede` anchors
  include `backlogit_claim_shipment`, emitted as `{{OP_CLAIM_SHIPMENT_MCP}}`
  (`templates/agents/_ship.agent.md.tmpl:202`).
* `ship_source_artifact_cleanup` (`verify_workspace.py:302-312` block above the
  closure one) — all four literals are present in the ship template.

These are genuinely brittle (any registry without the operation, or any reword,
silently breaks them) but they are *satisfiable*, so they belong in a hardening
backlog rather than a bug.

#### F6 — Root cause: no test ever validates a guardrail against a rendered template

Both defects share one cause. The guardrail test suite validates the **verifier**,
never the **template contract**:

* `tests/test_verify_workspace.py:1925-1932` writes *synthetic* fixture files
  containing exactly the required tokens —
  `(workspace/".github"/"skills"/"operational-closure"/"SKILL.md").write_text("Source artifact cleanup\nsource_stash_id\nsource_deliberation_id\n")`
  — then asserts `targeted_checks["closure_source_artifact_cleanup"]["ok"]` at
  line 1945. The assertion passes forever regardless of what the real template
  contains.
* The single test that runs assertions against real artifacts,
  `tests/test_verify_workspace.py:2179-2203`
  (`test_pipeline_topology_gate_assertion_passes_on_dogfood_repo`), reads
  `repo_root / assertion["path"]` — i.e. this repo's **installed dogfood copies**,
  not the rendered templates — and covers only 2 of the 71 keys.

Because the dogfood copies are paired-edit maintained (F4) and can legitimately
lag the templates, checking them cannot detect template-side drift. No test in
`tests/` renders `templates/**.tmpl` and evaluates the assertion tables against
the result. That is the exact missing guard, and it explains why both defects
reached a published release.

### What Was Tried and Failed / Ruled Out

* **Hypothesis: the verifier is wrong and should be relaxed to match the template.**
  *Ruled out for F1.* Three independent surfaces
  (`install-harness/SKILL.md:720,1082`, `docs/backlogit-operating-model.md:49`,
  `docs/backlogit-compatibility-matrix.md:55`) plus the producer template
  (`_ship.agent.md.tmpl:859`) all state that the closure artifact carries the
  section. Relaxing the verifier would delete a real, documented traceability
  contract and leave Ship writing into an undefined section.
* **Hypothesis: the mismatch is a rendering/variable-substitution artifact.**
  *Ruled out.* Re-ran the full sweep after substituting the concrete backlogit
  operation/status/field variables; the three closure tokens and the release-closure
  phrase remain absent, while four other apparent misses (F5) were cleared. The
  generated dogfood `operational-closure/SKILL.md` is byte-for-byte the same 124
  lines with the same zero occurrences.
* **Hypothesis: this is post-v1.5.0 working-tree drift, not a shipped defect.**
  *Ruled out.* The published wheel data under
  `.venv/Lib/site-packages/autoharness/data/` reproduces both defects exactly.
* **Hypothesis: the four failures are the two "missing file" checks plus two others,
  totalling the operator's four.** *Ruled out as the explanation.*
  `backlogit-sql-schema` and `backlogit-yaml-header-tooling` templates exist and
  install-harness wires them (`SKILL.md:628, 815, 1082`), so a fresh v1.5.0
  merge-install installs them; their absence here is local dogfood drift. They are
  also inconsistent with the operator's description of wording patches.
* **Attempted: running `autoharness verify-workspace` to reproduce end-to-end.**
  *Deliberately not done.* It rewrites tool-managed `.autoharness/staging/` state
  and would only re-test this repo's stale dogfood artifacts — which, per F2, is
  precisely the surface that masks the second defect. The in-process
  assertion-table sweep is strictly more informative and fully read-only.
* **Attempted: `engram workspace-status`.** Failed twice (daemon not Ready within
  30s). No third attempt was made, per the universal circuit-breaker
  same-operation rule. `engram index --direct` was not run because this
  investigation does not authorize rebuilding tool-managed state.

### Remaining Unknowns

1. **The identity of the operator's other two unsatisfiable checks.** Only two are
   recoverable from v1.5.0 sources. The remaining two are most plausibly explained
   by one of: (a) checks failing in the target for reasons other than template
   unsatisfiability (missing-file / pack-composition / stale prior install), which
   the operator's summary may have grouped together; (b) an assertion path whose
   artifact is not installed under that target's specific capability-pack
   composition; or (c) a target-local prior patch that shifted wording. None of
   these can be discriminated without target evidence.

   **Target evidence required to close this:** the target workspace's
   `.autoharness/staging/verify-workspace-report.json` (or `.md`) from the failing
   merge-install — specifically the `targeted_checks` map with each failing `key`,
   its `missing` token list and/or `reason` — plus the target's
   `.autoharness/workspace-profile.yaml` (enabled capability packs), its
   `.autoharness/backlog-registry.yaml`, and the diff of the "semantically
   identical wording" patches the operator applied. Four check keys plus their
   missing-token lists are sufficient to classify all four deterministically.
2. **Whether the target's patches were applied to installed artifacts or to
   templates.** If installed artifacts only, the patches are target-only and will
   be reverted by the next merge-install unless the upstream fix lands —
   consistent with the operator's "documented for re-check on next upgrade".
3. **Whether other guardrails are brittle-but-currently-satisfied under non-backlogit
   registries.** The F5 class was cleared using the backlogit registry only; a
   registry lacking `sync_index` or `claim_shipment` would leave those literals
   unresolved. Not investigated — out of the reported scope.

## Blast Radius Assessment

| Surface | Impact |
|---|---|
| **Templates** | `templates/skills/operational-closure/SKILL.md.tmpl` needs a new closure-artifact section (additive, ~1 checklist bullet + supporting prose). `templates/agents/_ship.agent.md.tmpl:709` OR `verify_workspace.py:573` needs a one-phrase alignment. Both are low-risk, additive/lexical edits. |
| **Generated artifacts** | `.github/skills/operational-closure/SKILL.md` must be updated in the same paired edit (the operational-closure pair is a straight render pair, not one of the four divergent pairs). `.github/agents/_ship.agent.md` already carries the F2 phrase; per the ratified paired-edit contract, whichever side is changed must be reconciled deliberately. |
| **Validation tests** | `tests/test_verify_workspace.py:1925-1932` synthetic fixtures should stay (they test the verifier), but a **new** render-aware contract test is required — render every `templates/**.tmpl`, resolve each assertion path to its source-of-truth, and assert all 71 table-driven assertions hold. Without it the same class of defect recurs. `tests/test_scope_containment_policy_contract.py:870-881` is unaffected (it asserts against the ship template, which is correct). |
| **Docs** | `.github/skills/install-harness/SKILL.md:720,1082`, `docs/backlogit-operating-model.md:49`, `docs/backlogit-compatibility-matrix.md:55` already describe the intended contract and need no change if the template is fixed. They WOULD all need correction if the verifier were relaxed instead — further evidence the template fix is the right direction. |
| **Manifests / schemas** | None. No schema, `harness-manifest.yaml`, or registry change is implied. `.autoharness/backlog-registry.yaml` is unaffected. |
| **Install / tune behavior** | `install-harness` and `tune-harness` wiring already reference the contract; no wiring change needed. After the fix, fresh installs stop failing 2 checks. Existing installs pick the fix up on the next merge-install/tune, at which point target-only patches are superseded. |
| **Backward compatibility** | Non-breaking. F1 is purely additive to a skill template. F2 is a lexical alignment. No agent behavior, tool contract, or artifact schema changes. Existing closure artifacts remain valid; the new section is written going forward. |
| **Risk of NOT fixing** | Every fresh v1.5.0+ merge-install into any backlogit workspace fails 2 guardrails, pushing each operator toward local unauditable patches (as already happened). Ship's post-merge Step 7 traceability record has no defined home, so archived/skipped source-artifact IDs are recorded inconsistently or not at all. |

## Recommendation

**Conclusion**: proceed
**Confidence**: high

**Fix the templates; do not relax the verifiers.** Both defects are one-directional
contract breaks where the verifier and the documentation agree and the template is
the outlier.

1. **F1 — `closure_source_artifact_cleanup` (P1).** Add a
   `Source artifact cleanup` section to
   `templates/skills/operational-closure/SKILL.md.tmpl`, defined as part of the
   `### Step 2: Build the Closure Checklist` MUST-include list, naming
   `custom_fields.source_stash_id` and `custom_fields.source_deliberation_id` and
   the archived/skipped ID record that `_ship.agent.md.tmpl:859` writes. Mirror
   into `.github/skills/operational-closure/SKILL.md`. Gate it on the `backlogit`
   pack, matching the assertion's `PACK_ASSERTIONS["backlogit"]` registration, so
   non-backlogit installs are unaffected.
2. **F2 — `ship_release_closure_sequence` (P1).** Align the phrasing. Preferred
   direction: change `verify_workspace.py:573` to match the current template
   wording at `templates/agents/_ship.agent.md.tmpl:709`, because the template's
   phrasing is the newer, more prescriptive one and the dogfood copy is the
   knowingly-lagging side. Whichever direction is chosen, the template, the
   verifier, and the dogfood `_ship.agent.md:607` must end up mutually consistent.
3. **F6 — Root-cause guard (P1, ships with the fix).** Add a render-aware
   template/verifier contract test. It must render `templates/**.tmpl` with the
   verifier's own variable tables, resolve every assertion `path` to its
   source-of-truth (template, or self-hosted global artifact), and assert all
   table-driven assertions hold. This test fails today on exactly the two defects
   above and would have blocked the v1.5.0 release.
4. **F5 — Brittleness hardening (P3, separate work).** Guardrails matching literal
   tool names produced by registry substitution are fragile. Consider asserting on
   the template variable or a stable anchor rather than the rendered literal. Not
   a defect; do not bundle with the P1 fix.

Do **not** attempt to explain the operator's remaining two checks by inference.
Request the target report and classify them deterministically.

## Next Steps

1. Consolidated bug captured in the backlogit stash as entry **`053E2BD2`**
   (kind `bug`, priority `high`), referencing this artifact and the exact files
   and lines. Not harvested and not planned — Stage planning is a separate
   session.
2. Request from the operator: the target workspace's
   `.autoharness/staging/verify-workspace-report.json` `targeted_checks` failures
   (keys + `missing` lists + `reason`), the target
   `.autoharness/workspace-profile.yaml` and `.autoharness/backlog-registry.yaml`,
   and the applied wording patches. Attach to the stash entry when received so the
   remaining two checks can be classified without guessing.
3. On a later Stage session, route the captured bug through `impl-plan`. The scope
   spans three surfaces (skill template + agent/verifier phrase + new contract
   test) and must be decomposed into separate 2-hour, width-isolated tasks —
   template authoring, verifier/agent alignment, and test infrastructure must not
   be combined into one task.
4. Treat the operator's target-side patches as temporary. They are target-only and
   will be overwritten by the next merge-install; the upstream fix is what makes
   them unnecessary.
