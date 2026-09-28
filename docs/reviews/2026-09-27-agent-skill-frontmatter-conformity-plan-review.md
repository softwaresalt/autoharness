---
title: "Review record: agent and skill frontmatter conformity contract plan"
description: "Review record for docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md (stash EF96B695). After Hardening Pass 2 (H-B1 to H-B12), three review-fix cycles, and a bounded fix-verification pass confined to the cycle-3 fixes, all six selected personas return PASS, with 0 open P0 and 0 open P1 under severity rule C4. The remaining items are accepted P2/P3 residuals, out-of-scope follow-ups, or harvest carries."
doc_type: review
status: complete
created: 2026-09-27
subject:
  plan_path: docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md
  base_commit: deb0564b
  reviewed_blob: 8f082f2992bad866b534ed0ea3cc82b5bd8788fa
  note: "The plan is uncommitted. reviewed_blob is the plan content as reviewed, before the Plan Review pointer section and the status change were appended."
decision: PASS
dispatch_mode: single-agent-declared-degradation
severity_rule: C4
source_stash: EF96B695
source_deliberation: docs/decisions/2026-09-27-close-evidence-frontmatter-context-tier-staging-deliberation.md
recorded_by: Stage
---

# Review Record: Agent and Skill Frontmatter Conformity Contract Plan

## Verdict

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* Decision: **PASS**. All six selected personas return PASS.
* Open blocking findings: **0 P0, 0 P1**. Under severity rule C4, only P0 findings,
  P1 findings, and matrix-critical P2 findings block harvest. No matrix-critical P2
  is open.
* Plan hardening was **required** (the plan declares four signals) and is
  **satisfied**:
  * the plan keeps its original hardening record;
  * it adds Hardening Pass 2 (H-B1 to H-B12), invariants INV-B5 and INV-B6, the
    extended INV-B1, and the `ProposedAction` / `ActionRisk` table.
* Harvest is **permitted** once the operator confirms the Stage-recommended
  decisions listed below. None of them blocks safe execution. *(D-B1 to D-B6 and the
  B3 tier value are operator-confirmed as of 2026-09-27T22:50-07:00.)*
* Harvest, shipment assembly, and commit are out of scope for this invocation.

## Capability Declaration (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
  This Stage runtime has no reviewer subagent tool. Stage applied the four always-on
  personas inline, each with its own finding list.
* The cross-model personas (Architecture Strategist and Agent-Native Parity) ran as
  independent, read-only external reviewer passes. They used the Copilot CLI on the
  anchor route `gpt-6-sol` (`reasoning_effort: high`), with the `write` tool denied
  and a read-only shell allowlist. The reviewer model differs from Stage's
  `claude-opus-5.5`. This follows the precedent in
  `docs/reviews/2026-09-27-cascade-close-evidence-capture-plan-review.md`.
* Security Lens Reviewer was **not triggered**:
  * the plan touches no auth or authz, no secrets, no sensitive data store, no API
    surface, and no external integration;
  * path containment (symlink escape) is a filesystem-robustness concern, and the
    Architecture and Python personas reviewed it.
* Intercom, Engram, and graphtor were not probed in this bounded invocation.
  Knowledge came from a direct search of `docs/compound/`, the plan's cited
  sources, and read-only code inspection.

## Persona Coverage

| Persona | Mode | Model | Raised | Final |
|---|---|---|---|---|
| Constitution Reviewer | inline pass | claude-opus-5.5 | 1 P2 | PASS |
| Python Reviewer | inline pass | claude-opus-5.5 | 3 P2, 2 P3 | PASS |
| Scope Boundary Auditor | inline pass | claude-opus-5.5 | 1 P2, 2 P3 | PASS |
| Learnings Researcher | inline pass | claude-opus-5.5 | 2 P3 | PASS |
| Architecture Strategist | anchor external pass | gpt-6-sol | 2 P0, 7 P1 (+1 duplicate of AN-F10) | PASS (fix verification) |
| Agent-Native Parity Reviewer | anchor external pass | gpt-6-sol | 10 P1 | PASS (fix verification) |

Agent-Native Parity was triggered because tune-harness consumes the verify-workspace
JSON report and the migration-proposal contract, and because the plan changes agent
and skill instruction surfaces.

## Cycle Log

| Cycle | Scope | Result |
|---|---|---|
| Hardening | plan-harden pass 2 (H-B1 to H-B12) | Plan hardened. B2 split into B2a and B2b. Audit claims reproduced |
| 1 | Full review by all 6 personas | FAIL: AS 1 P0 / 5 P1; AN 6 P1; inline 5 P2 / 6 P3 |
| 2 | Cross-model re-review | FAIL: AS-F4 and AS-F6 reopened; AS-F5 escalated to P0; AN-F2 and AN-F4 reopened; new AS-F7, AS-F8, AN-F7, AN-F8 |
| 3 | Cross-model re-review | AS FAIL (AS-F7 reopened; new AS-F9, AS-F10). AN FAIL (new AN-F9, AN-F10). Everything else RESOLVED |
| Fix verification (cycle-3 fixes only) | One bounded pass per external persona | AN: PASS, NEW: none. AS first pass: discarded as a category error (it judged the unimplemented code, not the plan). AS second pass, with a plan-level framing: PASS, NEW: none |

* The review-fix cycle limit (3) was honoured.
* The verification passes looked only at the cycle-3 fixes and opened no new review
  scope. They were needed because P-021 C3 forbids deferring an in-scope P0 or P1
  for budget reasons alone.
* The first AS verification output was not used as evidence. The pass was repeated
  with the same scope and a corrected framing.

## Findings

Severity is the final merged severity. "Resolved" means the plan text now carries
the fix, and the plan cites each fix inline by its finding ID.

### Architecture Strategist (gpt-6-sol)

| ID | Sev | Unit | Finding | Disposition |
|---|---|---|---|---|
| AS-F1 | P0 | B2a, runtime | The legacy unconditional `orchestrator_tier_fields` check makes "a workspace with no agents passes" false at overall-verify level | Resolved. Proofs and tests assert at check level, and INV-B3 keeps the legacy checks unreclassified |
| AS-F2 | P1 | B2b | A bare `model` migration to `model_family` produced forbidden keys for skills and plugin agents | Resolved. Profile-aware `remove-key` |
| AS-F3 | P1 | B2b | Missing required keys on managed-source files had no action | Resolved. `add-key`, with a deterministic skill `name` |
| AS-F4 | P1 | B3, B7 | Plugin invocation mechanism unspecified; `max_subagent_tier` is a ceiling; auto-tune tier conflict; P-013.1 reconciliation | Resolved. Body tier statement, ceiling decoupled, both agents at 2, B7 clarifies P-013.1 and P-013.4 |
| AS-F5 | P0 | B2a | A managed symlink escape was skipped rather than failed closed | Resolved. `FM_PATH_ESCAPE` fails closed without a read. The pre-existing checksum-scan read is an out-of-scope residual (R-1) |
| AS-F6 | P1 | B1, C | Extension contract: import-time derivation versus monkeypatching; `context_tier` on plugin agents | Resolved. Call-time `agent_key_sets` / `skill_key_sets`, with a single `ROUTE_VALUE_KEYS` extension point |
| AS-F7 | P1 | B2a, B2b, B5 | Community checksum semantics and reinstall refresh were undefined | Resolved. `managed-community` class, `reinstall-community` refreshes both checksums, idempotence test |
| AS-F8 | P1 | B2b | `rerender` was offered even when the source reproduces the defect | Resolved. `source-repair` |
| AS-F9 | P1 | B2b | The new community `template_path` read lacked containment | Resolved. Containment before the read, even with an empty `source_checksum` |
| AS-F10 | — | B2b | Duplicate of AN-F10 | Merged into AN-F10 |

### Agent-Native Parity Reviewer (gpt-6-sol)

| ID | Sev | Unit | Finding | Disposition |
|---|---|---|---|---|
| AN-F1 | P1 | B2b, B5 | Tune did not preserve the full proposal payload; `status` and `severity` were unspecified | Resolved |
| AN-F2 | P1 | B2a, B2b | Markdown parity for proposals and informational findings | Resolved. `summary` field, `info[]`, a two-line renderer branch, parity tests |
| AN-F3 | P1 | B2b | No deterministic action for every code and class | Resolved. Ordered rules 1 to 8 and a table-driven test |
| AN-F4 | P1 | B2a | Unknown or suffix-shaped labels were assumed to be managed | Resolved. Positive allowlist, existing-source evidence, `unknown-provenance` class |
| AN-F5 | P1 | B1 | The plugin forbidden set missed the review-route keys and `context_tier` | Resolved. `ROUTE_VALUE_KEYS` |
| AN-F6 | P1 | B3, B6 | Unsupported claim of plugin route resolution | Resolved. Claim withdrawn, and the operator-session model documented |
| AN-F7 | P1 | B2a | A managed symlink escape was skipped (same fix as AS-F5) | Resolved |
| AN-F8 | P1 | B2a | Any `plugin.json` selected `plugin-global` | Resolved. Requires `install_mode: self-install`, `name: autoharness`, and membership in `agents[]` |
| AN-F9 | P1 | B2a | The scan missed `distribution.local_agents_dir` | Resolved. Reuses `_resolve_agent_scan_dirs` |
| AN-F10 | P1 | B2b | Passing template mode does not prove the render is valid | Resolved. The rendered candidate is validated in installed mode |

### Inline personas (claude-opus-5.5)

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| CR-F1 | P2 | Principle IX: 65 of the 100 in-scope files are CRLF in the working tree, so byte-identity must be judged on the staged blob | Resolved (B4) |
| PY-F1 | P2 | The duplicate-key loader implementation and the recursive placeholder walk were unspecified | Resolved (B1) |
| PY-F2 | P2 | The exception scope was too broad or unspecified | Resolved (B1, B2a) |
| PY-F3 | P2 | The symlink test needs a platform `skipif` | Resolved (B2a) |
| PY-F4 | P3 | `Finding` immutability and ordering | Resolved (B1) |
| PY-F5 | P3 | Invalid `plugin.json` handling | Resolved (B2a). Fail-safe to `tier-routed` |
| SB-F1 | P2 | `.github/skills/` is plugin-distributed with this repository's rendered variables | Accepted. Out of scope (pre-existing); harvest carry HC-2 |
| SB-F2 | P3 | B7 adds policy text | Accepted. In scope: it is required to keep P-013.1 and P-013.4 unambiguous for the contract (R6) |
| SB-F3 | P3 | Unit growth (8 units) | Accepted. B2a is decomposed into subtasks at harvest (2-hour rule) |
| LR-F1 | P3 | `docs/compound/2026-05-05-agent-tool-list-completeness.md`: `tools` content is not validated by the contract | Accepted residual. Out of scope, and existing coverage is unchanged |
| LR-F2 | P3 | `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md` (git-blob checksums) applies to B3, B4, B5, and B7 | Resolved. IM-12 staged-blob rule reinforced |

### Counts

| Severity | Found | Open |
|---|---|---|
| P0 | 2 | 0 |
| P1 | 17 | 0 |
| P2 | 5 | 1 (SB-F1, accepted out-of-scope carry) |
| P3 | 6 | 1 (LR-F1, accepted residual) |

## Residuals (P-021 C1 out of scope)

* **R-1 (from AS-F5):** the pre-existing manifest and community checksum scans read
  the bytes of manifest-tracked artifacts without a symlink-containment check.
  * This plan does not introduce that read, and fixing it would change the checksum
    scan, which is outside stash EF96B695.
  * The AS cycle-3 pass confirmed that this out-of-scope classification is
    legitimate.

## Stage-Recommended Decisions (pending operator confirmation)

> *Superseded (operator rulings 2026-09-27T22:50-07:00): D-B1 to D-B6, including
> D-B5, and the B3 tier value are operator-confirmed. B7 was not named separately in
> the ruling. It stands as reviewed plan scope unless the operator overrides it
> before Ship claims 199-S. See "Post-review amendments (operator rulings
> 2026-09-27T22:50-07:00)" at the end of this record.*

* D-B1 to D-B4 (from the deliberation).
* D-B5: agents distributed through `plugin.json` take the `plugin-global` profile.
  They carry `max_subagent_tier` and no route-value keys, and run on the operator's
  session model.
* D-B6: managed findings fail closed whatever the checksum status, and only the
  remediation differs.
* The B3 tier value: `max_subagent_tier: 2` for both auto-tune and
  auto-mergeinstall. This supersedes the earlier "auto-tune Tier 3", and matches
  the "Tier 2" declared in both agent bodies.
* B7: add clarifying sentences to P-013.1 and P-013.4. Their MUST text is unchanged.

## Runtime Verification and Closure Readiness

* Five runtime scenarios are defined, and each one asserts at check level. There is
  also an environment precheck and a blocked path (`RUNTIME_VERIFICATION_BLOCKED`).
* Scenario 1 needs a pre-change baseline verify run, which Ship captures before B2a.
* Closure records the command, the exit code, and a JSON excerpt for each scenario.

## Harvest Carries

* **HC-1:** decompose B2a into two ordered subtasks, as the plan's harvest note
  specifies.
* **HC-2:** capture a stash follow-up for SB-F1: the plugin-distributed
  `.github/skills/` carry this repository's rendered variables.
* **HC-3:** capture a stash follow-up for R-1: symlink containment in the
  pre-existing checksum scan.
* **HC-4:** linear order B1, B3, B4, B2a, B2b, B5, B6, B7. Each task gets its
  `size` and `complexity` as the plan declares them.
* **HC-5:** notify the downstream context-tier plan of its required adjustments.
  They are listed in the Stage report for this invocation, and in the plan's
  `## Plan Review` section.

## Post-review amendments (PR #460 hosted review)

These edits were made after `reviewed_blob` and after this review's PASS, in
response to Copilot review comments on PR #460. They tighten the plan without
widening scope and do not reopen any finding above:

* B2a (AS-F5 containment): the workspace-root `plugin.json` now gets the same
  pre-read containment as scanned files. It is read only if it resolves inside
  the workspace as a regular, non-symlink, non-reparse-point file. Otherwise it
  is never read, one warning is added, and the plugin-agent set is empty
  (fail-safe to `tier-routed`). A symlink-escape regression case is added. Tasks
  193.004-T and 193.004.001-ST carry the same wording.

## Post-review amendments (operator rulings 2026-09-27T22:50-07:00)

These plan edits came after `reviewed_blob` and after this review's PASS. They apply
the operator's rulings on the staging deliberation. They are not new design and they
reopen no finding above:

* D-B1 to D-B6 (including D-B5) and the B3 tier value `max_subagent_tier: 2` for both
  plugin agents are confirmed.
* B7 was not named separately. It stands as reviewed scope unless the operator
  overrides it before Ship claims 199-S.
* The dogfood Ship `max_subagent_tier` divergence is decided by ruling 5b in the
  context-tier plan (C4a), not in this plan.
* The plan carries a matching "Operator Rulings (2026-09-27T22:50-07:00)" section,
  and 193-F carries the same wording.
