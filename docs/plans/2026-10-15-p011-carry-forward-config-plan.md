---
title: "Operator-editable P-011 carry-forward configuration"
description: "Implementation plan for .autoharness/carry-forward.yaml: schema, HEAD-blob loader, gate wiring, default template/install/manifest, wording mirrors, docs. Stash D2F399C9, feature 210-F, shipment 217-S."
date: 2026-10-15
status: reviewed
deliberation: "docs/decisions/2026-10-15-p011-carry-forward-config-deliberation.md (Q1-Q4 ACCEPTED by the operator 2026-10-15, recorded there)"
stash_entries: [D2F399C9, 80CD43B8]
requires_plan_hardening: "yes"
plan_hardening_status: "hardened"
plan_review_verdict: "PASS"
plan_review_cycles: 2
plan_review_dispatch_mode: single-agent-declared-degradation
tags: [plan, p-011, carry-forward, gates, schema, parity]
---

## Hardening signals

Requires plan hardening: **yes** (new schema, gate security behaviour, multiple template families). Hardening and review
were completed on 2026-10-15; see the Plan Hardening and Plan Review sections below.

## Task graph (shipment 217-S, feature 210-F)

| Task | Size / complexity | Depends on | Surface |
|---|---|---|---|
| 210.001-T contract: schema 1.0.0 (versioned dir + root mirror), `schema_contracts.py` registration, contract tests | M / low | - | `schemas/`, `src/autoharness/schema_contracts.py`, tests |
| 210.002-T loader + unit tests | M / medium | 210.001-T | `src/autoharness/gates/` |
| 210.003-T gate wiring + gate tests | M / medium | 210.002-T | `topology.py`, `tests/test_gates_topology.py` |
| 210.004-T template, dogfood file, manifest record | M / medium | 210.001-T | templates, `.autoharness/`, manifest |
| 210.005-T policy/agent wording + `.github` mirrors | S / low | 210.003-T | policies, agents |
| 210.006-T docs + CHANGELOG | S / trivial | 210.003-T | `docs/gates-reference.md` |
| 210.007-T install/tune skill lifecycle + verify assertion | M / medium | 210.004-T | skills, `verify_workspace.py` |

Schema version identifier is `1.0.0` (matching the repo's other contracts); the deliberation's shorthand `schema_version: 1`
means this.

## Key implementation notes

- Exact-file entries need a separate `path == entry` branch; the existing normalisation appends `/` to every prefix.
- Effective set is read from `git show HEAD:.autoharness/carry-forward.yaml` (D3.2); built-ins are the backlog dir
  prefix and `.autoharness/carry-forward.yaml` itself, always present.
- Any validation failure yields built-ins only plus a warning in check details; never widens.
- Keep `stash_referenced_paths` as an independent class.
- Do not modify the operator's uncommitted `.autoharness/config.yaml` at any point.

## Test plan

Canonical gate: `PYTHONPATH=src python -m unittest discover -s tests` (PowerShell: set `$env:PYTHONPATH='src'`).
Cases: see 210.002-T and 210.003-T; plus manifest/parity tests for 210.004-T and 210.005-T. Include a regression
test that a dirty `src/` file plus a working-tree-only widening of the carry-forward file still yields `WORKTREE_DIRTY`.

## Ordering

No blocks edge to 212-S. `217-S` is a declared dag-root shipment (label `dag-root`); the default-branch read-only probe
(`autoharness gate pipeline-topology --mode agent --shipment 217-S --phase pre_claim --json`) on 2026-10-15 passed with
`predecessor_source: declared_root` and no `UNSEQUENCED_SHIPMENT`. `.autoharness/config.yaml` is now clean, so the claim is
no longer blocked by dirt.

## Plan Hardening

**Hardening required: yes.** Triggers: a security-sensitive gate decision (P-011 carry-forward admission), a new
contract (`carry-forward` schema), operator-facing install/tune lifecycle, and multi-family template/policy/agent mirrors.

### Protected invariants

- I1. Dirt is admitted only by (a) built-ins, (b) entries from the COMMITTED `HEAD` copy, (c) the independent
  stash-referenced class. Working-tree content of the carry-forward file never changes the current decision.
- I2. The backlog dir prefix and the file's own path are carried forward under every failure mode of the file.
- I3. Failure of any kind narrows the set to built-ins; nothing widens it.
- I4. Divergent staged content still blocks (`WORKTREE_DIRTY`), for configured paths exactly as for backlog state.
- I5. Readers lacking the new capability keep today's behaviour (`skipped` / backlog-only); the protocol stays duck-typed.
- I6. No shell, no globbing, no execution, no extraction from file text beyond schema-validated path strings.

### Learnings consulted (`docs/compound/`, single-agent inline search; no subagent dispatch)

- `2026-10-10-operator-staged-config-carry-forward-and-route-pin-cascade.md`: carry-forward only clears P-011; a
  `model_routing` edit still cascades to route pins, Stage/Ship mirrors, manifest checksums and `config_hash` (bundle
  rule); full suite is 11-15 minutes and the pre-push hook reruns it per push (batch pushes). It also records the
  original request as stash `80CD43B8`.
- `2026-05-05-path-traversal-validation-parts.md`: validate `Path.parts`, not string prefixes.
- `2026-10-05-windows-realpath-containment-short-names-and-case-sensitive-dirs.md`: component-wise containment, not
  string prefixes; run Windows tests under default `%TEMP%`; symlink/junction fixtures.
- `2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md` and `2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md`:
  never mutate a published schema version in place; register versions properly.
- `2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`: do not refresh baseline
  checksums merely to quiet a check; an operator-owned file's drift is expected, not tuned away.
- `2026-08-12-hosted-review-catches-fail-closed-gaps-local-review-and-ci-miss.md`: fail-closed gaps are what hosted
  review finds; add explicit negative tests for every failure branch.
- `2026-05-06-p011-branch-before-mutation-design.md`: P-011 ordering and branch conditions; this change must not touch them.

Instruction files re-read: `.github/policies/workflow-policies.md` (P-011, P-021), `.github/instructions/constitution.instructions.md` (III/IV).

### Risky actions (`ProposedAction` / `ActionRisk`)

| ProposedAction | ActionRisk | Approval | Expected result / rollback state |
|---|---|---|---|
| Change gate admission logic in `topology.py` | high (security control) | operator PR merge | Revert PR: gate returns to backlog-only prefix; the YAML file becomes inert |
| Add `carry-forward` schema contract in `schema_contracts.py` | medium (contract) | operator PR merge | Revert PR; no consumers outside the loader |
| Install/tune writes a new operator-owned file | medium | operator PR merge | tune never overwrites; revert removes template, dogfood file stays harmless |
| Dogfood `.autoharness/carry-forward.yaml` lists `config.yaml` | medium (admits routing edits) | operator accepted (Q3) | Delete the entry in a committed change; takes effect on commit |
| Policy/agent wording and `.github` mirrors | low | operator PR merge | Revert PR |

### Added verification

- Environment precheck: `git` on PATH, Python with PyYAML, `PYTHONPATH=src`.
- Negative tests per failure branch: file missing, untracked-only (not in HEAD), blob mode symlink/submodule, oversize
  blob, invalid YAML, non-mapping root, wrong `schema_version`, unknown key, non-string entry, entry outside the
  allowlist, entry on the denylist, traversal (`..`, `.`, empty segment), absolute, drive, colon, backslash, `.git`, glob
  characters, duplicate entries, more than 32 entries, directory entry without trailing `/`, bare `.autoharness/`.
  Every case asserts: set equals built-ins, warning present, backlog dir still carried.
- Bypass regression: working-tree-only widening (dirty `carry-forward.yaml` adds `src/`; `src/` file dirty) still
  `WORKTREE_DIRTY`; the dirty file itself is `CARRY_FORWARD_ELIGIBLE`.
- Divergence: staged vs working-tree `config.yaml` blocks with `divergent_paths`.
- Branch interaction: an UNRELATED non-default branch (one that does not match the target shipment) still blocks via the
  existing `branch_ownership` check, while a branch matching the target shipment keeps passing with `BRANCH_OK` (existing
  supported flow, `tests/test_gates_topology.py` `BranchOwnershipTests.test_matching_target_branch_passes`); neither
  behaviour changes. The loader reads the current `HEAD` and reports the commit SHA in details.
- Cross-validator parity test: the hand-written validator and `schemas/carry-forward.schema.json` accept and reject the
  same fixtures (no new runtime dependency on a JSON-schema library).
- Windows: containment tests under default `%TEMP%` plus a junction fixture; LF/CRLF blob vs working-tree content.
- Order: run the targeted modules first (`tests/test_gates_topology.py`, the new loader tests, schema-contract tests,
  manifest/parity tests), then the canonical full suite once (`PYTHONPATH=src python -m unittest discover -s tests`,
  11-15 minutes); batch commits to one push (P-019 pre-push hook stays enabled).

### Monitoring, rollback and operator checkpoints

- Monitoring signals: check `details` now carry `carry_forward_source` (`head` | `builtin-fallback`),
  `carry_forward_config_warning`, `carry_forward_head_sha`, plus the existing carried path list. Any
  `builtin-fallback` on the dogfood repo is a defect to triage. Ship reports the carried path set in its first-commit
  message (210.005-T).
- Rollback triggers: any false admission of a non-configured path, any new `WORKTREE_STATUS_UNAVAILABLE` regression,
  or the full suite failing on main after merge. Procedure: revert the merge commit by PR (owner: operator); the YAML
  and schema become inert. Validation window: next two claimed shipments pass `worktree_cleanliness` as expected.
- Operator checkpoints: (1) approve each PR merge; (2) before the FIRST carry-forward of `config.yaml`, the operator
  confirms the routing edit's bundle (pins, mirrors, manifest checksums, `config_hash`) per the 2026-10-10 learning;
  (3) the file's own edits take effect only after commit (documented in 210.006-T).
- Partial rollout: tasks 210.001-T..210.003-T deliver the gate and are safe alone (no file in HEAD => built-ins only);
  210.004-T ships the default file last in effect because it lists `config.yaml`.

### Review-gate capability risks

Reviewer subagent dispatch is not exposed to this Stage session. Plan review MUST emit literal `dispatch_mode:` and
`decision:` markers and declare `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`
(`dispatch_mode: single-agent-declared-degradation`), covering all always-on personas plus Architecture Strategist and
Security Lens (this plan is security-sensitive). Anchor-review routing is not dispatched: declare same-model degradation.

### Unresolved operator decisions

None blocking: Q1-Q4 accepted.

## Plan Review

dispatch_mode: single-agent-declared-degradation
TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass
TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass (anchor_review route not dispatched)
Personas applied inline, each by its rubric: Constitution Reviewer, Python Reviewer, Scope Boundary Auditor, Learnings
Researcher, Architecture Strategist, Security Lens Reviewer (triggered: gate security control, trust boundary).

### Cycle 1 (against the hardened plan and the as-created tasks)

decision: FAIL

| ID | Sev | Persona | Finding | Disposition |
|---|---|---|---|---|
| F1 | P1 | Architecture / Python | 210.001-T scoped "schemas only", but a new contract must be registered in `src/autoharness/schema_contracts.py`, needs a versioned dir plus root mirror, and contract tests; the task would have shipped an unregistered schema or smuggled a src edit. | FIXED: 210.001-T rescoped (versioned dir + root mirror, registration, contract tests), re-sized M/low, retitled. |
| F2 | P1 | Scope Boundary Auditor | 210.004-T combined template, dogfood file, manifest record, install skill, tune skill and install/tune tests: several concerns, over the 2h rule. | FIXED: split; 210.004-T keeps template + dogfood file + manifest record; new 210.007-T (M/medium, depends on 210.004-T) holds install/tune skill lifecycle and a verify assertion; added to 217-S. |
| F3 | P1 | Security Lens | Match-time handling of a configured path was unspecified: a configured file replaced by a symlink/junction (type change) or deleted would be carried forward or mis-evaluated; the plan relied on lexical checks only. | FIXED: 210.003-T specifies lstat rules (no symlink/reparse in path or parents; final component regular or absent; type change blocks; deletion eligible) with tests. |
| F4 | P1 | Security Lens | The `.autoharness/` allowlist still admits trust-bearing files: `backlog-registry.yaml` (its `cli_command` values are executed) and `stage-worktree-marker.yaml` (a gate input), plus the bare `.autoharness/` directory entry that would admit everything under the root. | FIXED: denylist (those two files, `.autoharness/gates/`, and the bare root) added to 210.001-T/210.002-T and recorded in the deliberation. |
| F5 | P1 | Learnings Researcher | Plan ignored `docs/compound/2026-10-10-...route-pin-cascade.md` (bundle rule) and the overlapping stash `80CD43B8`. | FIXED: Plan Hardening cites the learning; 210.006-T carries the bundle warning; deliberation records the `80CD43B8` overlap and disposition. |
| F6 | P2 | Architecture | Ship's first-commit message did not have to name carried paths, weakening auditability of the Q3 acceptance. | FIXED in 210.005-T (names every carried path and `carry_forward_source`). |
| F7 | P2 | Python | Validator/schema drift risk with no JSON-schema runtime dependency. | FIXED: hand validator plus a shared-fixture parity test (210.002-T). |
| F8 | P3 | Constitution | Deliberation shorthand `schema_version: 1` vs repo convention `1.0.0`. | FIXED: plan clarifies `1.0.0`. |
| F9 | P3 | Scope | Suite runtime 11-15 minutes per push. | Advisory: batched-push guidance already in Plan Hardening. |

### Cycle 2 (after fixes)

Re-checked every P1/P2 against the revised plan, deliberation and the stored task bodies of 210.001-T..210.007-T:
F1-F8 are present and consistent; each task is under the 2-hour rule with one concern per task (schema/contract; loader;
gate wiring; template+manifest; install/tune lifecycle; wording; docs); dependency graph is acyclic (001 -> 002 -> 003 -> 005/006;
001 -> 004 -> 007); constitution III/IV honored (containment, fail-closed, no shell); invariants I1-I6 each have a named test.
No P0/P1 remain; P3 F9 advisory only.

dispatch_mode: single-agent-declared-degradation
decision: PASS

Cycles used: 2 of 3. Residual risks accepted by the operator: Q3 (routing edits carried via agent-driven commit) and
reviewer-dispatch degradation (single-agent, same-model review of a security-sensitive plan; a hosted/Copilot PR review
and the operator's merge approval remain the independent checks).


