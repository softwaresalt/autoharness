---
shipment: 162-S
feature: 154-F
pr: 446
merge_commit: null
last_code_affecting_head: 1bd7ac6f7c3be3880f17aac0549e215f257e1523
surface: cli
verdict: PASS
post_merge_reverification: null
---

# 162-S / 154-F Runtime Verification -- SHIP-4 Review-Persona, Policy, and Agent-Architecture Contract Integrity

## Scope

Feature `154-F` (4 tasks, `154.001-T`..`154.004-T`) amends review-persona
templates, workflow policy text, instruction artifacts, and the
install-harness skill to fix five previously-identified defects: the
security-reviewer's purpose-based finding suppression, P-007's ungated
`git restore` remediation, the constitution-reviewer's incomplete principle
checklist, a leaf-executor/skill-spawning architecture contradiction, and the
technology-reviewer's dangling language-instruction reference. Three
additional review-fix carriers (`templates/agents/_ship.agent.md.tmpl`,
`.github/skills/shipment-reconcile/SKILL.md` + template) were amended during
Ship's own local review pass to close the same P-007 defect where it was
independently restated. **No source code under `src/` was touched by this
shipment** (`git diff --stat main..HEAD -- src/` is empty) -- this is a
template/policy/instruction/skill/test content change only.

## Validator Contract

Per `.autoharness/workspace-profile.yaml` `runtime_validation`:

* `validator_manifest.surfaces`: `cli` only, adapter hint `command`, probe
  `cli-help` (`uv run autoharness --help`), required.
* `validation_expectations`: minimum verdict `PASS`, invariant "the
  autoharness CLI starts without import, packaging, or option-parsing
  failures".
* `releasability.required`: `false` for this workspace profile.

Because no runtime (`src/`) code changed, the CLI surface is not expected to
be affected by this shipment's diff; the probe below is run as confirmatory
evidence, not because a specific code path was touched.

## Execution

* `uv run autoharness --help` -- exit 0, CLI help text printed (ran
  repeatedly throughout this session, most recently at HEAD `1bd7ac6f`).
* `uv run autoharness verify-workspace --workspace .` -- run after every
  content edit in this shipment (9 times across 154.001-T..154.004-T and
  three review-fix rounds); 0 strict-schema blockers, 0 blockers, 0
  warnings on every run; every touched artifact's manifest checksum verified
  `status: unchanged` against its actual on-disk content.
* `PYTHONPATH=src python -m unittest discover -s tests` -- run to completion
  (full suite, no filters) after every task and every review-fix round; final
  clean run at HEAD `1bd7ac6f`: 2186 tests, `OK (skipped=51)`. The only
  observed intermittent failure across repeated local runs this session was
  `tests.test_graphtor_mcp_shim.GraphtorMcpShimHandshakeTests.test_child_stdin_write_error_fails_requests_without_crashing`,
  a pre-existing, environment-load-sensitive subprocess/pipe-timing test in a
  file untouched by this diff (last modified in unrelated PR #429); confirmed
  intermittently flaky in isolation (2 failures / 1 pass across 3 isolated
  reruns) and green on every GitHub Actions CI run for this PR, including the
  final HEAD.
* CI (`test`, `ci gate`, `pipeline-topology (ambient)`, `detect code changes`)
  -- green on every push to PR #446, including the final HEAD `1bd7ac6f`.
* New tests added by this shipment
  (`tests/test_p007_restore_approval_gate_contract.py`,
  `tests/test_subagent_depth_constraint_verifier.py`,
  `tests/test_technology_reviewer_coinstallation_contract.py`) each
  demonstrated RED (against the pre-amendment text, or against synthetic
  non-conforming fixtures) before GREEN (against the amended text / the live
  repository corpus), per the binding H7 requirement on 154.002-T/154.003-T.

## Invariants Preserved

* No `{{VARIABLE}}` placeholders remain unresolved in any installed mirror
  touched by this shipment (verified via `verify-workspace`'s
  `unresolved_placeholders` count: 0 across every run).
* Every amended template/mirror pair remains in agreement after variable
  resolution (asserted directly by the new contract tests for the
  P-007/constitution-reviewer, role-enforcement/harness-architecture, and
  install-harness/technology-reviewer pairs).
* No skill behavior changed (154.003-T's binding scope explicitly forbids
  this); only instruction text describing the exception was amended.
* `.github/instructions/python.instructions.md` remains absent in this
  repository (F2, not strategy (a) -- 154.004-T).

## Verdict

**PASS.** The CLI surface is unaffected and confirmed working; the full test
suite (2186 tests) is green; CI is green on the final reviewed HEAD; every
manifest checksum for a touched artifact matches its on-disk content with
zero blockers or warnings.

## Blocked Prerequisites

None. This shipment has no runtime rollout risk (documentation/policy/skill
text only) and no pending validator dependency.
