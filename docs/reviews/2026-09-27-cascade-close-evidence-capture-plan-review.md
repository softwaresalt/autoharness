---
title: "Review record: automatic, fail-closed CASCADE close-evidence capture plan"
description: "Review record for docs/plans/2026-09-27-cascade-close-evidence-capture-plan.md (stash 008F3BCF). After plan hardening pass 2, three review-fix cycles, and a bounded fix-verification loop, all seven personas return PASS with 0 open P0 and 0 open P1 under severity rule C4. The remaining P2 and P3 items are accepted residuals, out-of-scope follow-ups, or harvest carries."
doc_type: review
status: complete
created: 2026-09-27
subject:
  plan_path: docs/plans/2026-09-27-cascade-close-evidence-capture-plan.md
  base_commit: deb0564b
  reviewed_blob: f54f40bb6645a987cb7a30712bcbfc3e365973c5
  note: "The plan is uncommitted. reviewed_blob is the plan content as reviewed, before the Plan Review pointer section and the status change were appended."
decision: PASS
dispatch_mode: single-agent-declared-degradation
severity_rule: C4
source_stash: 008F3BCF
source_deliberation: docs/decisions/2026-09-27-close-evidence-frontmatter-context-tier-staging-deliberation.md
recorded_by: Stage
---

# Review Record: CASCADE Close-Evidence Capture Plan

## Verdict

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* Decision: **PASS**. Seven of seven personas return PASS.
* Open blocking findings: **0 P0, 0 P1**. Severity rule C4 blocks harvest only on
  P0 and P1 findings, and on matrix-critical P2 findings. No matrix-critical P2 is
  open.
* Plan hardening was **required** (all five signals are present) and is
  **satisfied**. The plan carries the original hardening record plus Hardening
  Pass 2 (H-B1 to H-B10), including the invariants INV-P1 to INV-P7 and the
  `ProposedAction` / `ActionRisk` tables.
* Harvest is **permitted** once the operator confirms the Stage-recommended
  decisions listed below. None of them blocks safe execution. Harvest, shipment
  assembly, and commit are out of scope for this invocation. *(D-A1 to D-A6 and the
  D-A3 amendment are operator-confirmed as of 2026-09-27T22:50-07:00.)*

## Capability Declaration (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
  This Stage runtime exposes no reviewer subagent tool. Stage applied the four
  always-on personas inline, each with its own finding list.
* The cross-model personas (Architecture Strategist, Security Lens, and
  Agent-Native Parity) ran as independent, read-only external reviewer passes
  through the Copilot CLI on the anchor route, `gpt-6-sol`. They used write-denied
  tool permissions. The reviewer model differs from Stage's `claude-opus-5.5`.
* Intercom, Engram, and graphtor were not probed in this bounded invocation.
  Knowledge retrieval used a direct file search of `docs/compound/`, the plan's
  cited sources, and the code.

## Persona Coverage

| Persona | Mode | Model | Raised | Final |
|---|---|---|---|---|
| Constitution Reviewer | inline pass | claude-opus-5.5 | 1 P1, 1 P2, 1 P3 | PASS |
| Python Reviewer | inline pass | claude-opus-5.5 | 3 P2, 2 P3 | PASS |
| Scope Boundary Auditor | inline pass | claude-opus-5.5 | 3 P2, 1 P3 | PASS |
| Learnings Researcher | inline pass | claude-opus-5.5 | 1 P2, 2 P3 | PASS |
| Architecture Strategist | anchor external pass | gpt-6-sol | 2 P0, 7 P1, 3 P2 | PASS (cycle 3) |
| Security Lens Reviewer | anchor external pass | gpt-6-sol | 2 P0, 3 P1, 2 P2 | PASS (cycle 3) |
| Agent-Native Parity Reviewer | anchor external pass | gpt-6-sol | 3 P0, 4 P1, 3 P2 | PASS (fix verification) |

Security Lens was triggered by the subprocess execution, the persistence of
subprocess output into the repository, and path containment. Agent-Native Parity
was triggered by the agent-facing CLI command, the skill and agent routing, and
the MCP bypass path.

## Cycle Log

| Cycle | Scope | Result |
|---|---|---|
| Hardening | plan-harden pass 2 (H-B1 to H-B10) | Plan hardened; A3a split out |
| 1 | Full review by all 7 personas | FAIL: 6 P0, 8 P1 |
| 2 | Cross-model re-review | FAIL: 5 P1 new, AN-F01 reopened |
| 3 | Cross-model re-review | AS and SL PASS; AN FAIL on AN-F09 (P0) |
| Fix verification (AN only, cycle-3 dispositions) | Two bounded verification passes confined to the cycle-3 fixes | Pass 1 reopened AN-F01 and AN-F07 and raised AN-F10 (all P1). Pass 2: all RESOLVED, NEW: none, PASS |

The review-fix cycle limit (3) was honoured. The verification passes reviewed
only the cycle-3 fixes and their mechanical consequences. They opened no new
review scope. They were needed because P-021 C3 forbids deferring an in-scope P0
or P1 for budget reasons alone.

## Findings

Severity is the final merged severity. "Resolved" means the plan text now carries
the fix, and each fix is cited inline in the plan by its finding ID.

| ID | Sev | Scope | Summary | Disposition |
|---|---|---|---|---|
| AS-F01 / AN-F03 | P0 | in | The no-clobber rule forbade the `invoking → post_close` transition, so no run could ever finalize | Resolved: owner-bound transition (A1b) |
| AS-F02 | P0 | in | Revalidation compared only the verdict, not statuses, fingerprints, or `parent_id` | Resolved: full-snapshot revalidation (A3 step 5) |
| SL-F01 | P0 | in | Concurrent runs could both spawn the cascade | Resolved: per-pair `O_EXCL` lock (A1b) |
| SL-F02 | P0 | in | A Windows `.cmd` or `.bat` shim could reinterpret arguments | Resolved: `.exe` required (A3a) |
| AN-F01 | P0 | in | A direct MCP or CLI cascade could pass the gate under a self-declared `safe_close` | Resolved: SAFE_CLOSE verdict record required, plus observation-set invariance (A2, A4), with a narrowed guarantee and a benign residual (decision pending) |
| AN-F02 | P0 | in | Classification ran before the `invoking` check, so an interrupted cascade could reroute to SAFE_CLOSE | Resolved: lock and record check come first (A2, A3 step 1) |
| AN-F09 | P0 | in | A task-only, partial-feature SAFE_CLOSE had no observation set | Resolved: observation set (A2), checked by A4 |
| AS-F03 | P1 | in | The parse needed full stdout, but only an excerpt was kept | Resolved: bounded 1 MiB parse buffer; overflow gives `parse_error` (A1b) |
| AS-F04 | P1 | in | The INV-10 shipment-record `archived` / `shipped` check was missing | Resolved (A3b) |
| AS-F05 | P1 | in | `mutation_state: none` could not be proven without member hashes | Resolved: every member is fingerprinted (A1, A2) |
| AS-F06 | P1 | in | Units exceeded the 2-hour rule | Resolved: split into A1/A1b and A3a/A3b/A3 (10 units, each S or M) |
| AS-F09 | P1 | in | R3 needs the stdout excerpt on success too | Resolved (A1) |
| AS-F10 | P1 | in | `parent_id` was not checked for archived manifest tasks | Resolved (A3b) |
| AS-F11 | P1 | in | The validator accepted `pass` despite a non-zero exit or timeout | Resolved, including the cycle-3 residual on `returned_ids` (A1) |
| SL-F03 | P1 → P2 | in / out | The first PATH match was trusted | In-scope part resolved: absolute-path spawn, binary hash, and re-hash (A3a, A3). Registry pin is out of scope (C1), carried |
| SL-F04 | P1 → P2 | in | A finite redactor cannot guarantee safety | Resolved: every free-text field is redacted and bounded. The residual is accepted (Risks) |
| SL-F06 | P1 | in | Symlinked or junctioned lock and evidence directory components | Resolved: per-component checks (A1b) |
| AN-F04 | P1 | in | Exit 0 meant different things per mode | Resolved: mode-specific routing table (A5) |
| AN-F07 | P1 | in | Linked deliberations were unobserved under SAFE_CLOSE | Resolved: observation-set union (A2) |
| AN-F10 | P1 | in | The gate rejected siblings already archived at baseline | Resolved: exact-location and hash invariance (A4) |
| CR-F01 | P1 | in | Principle VII: the wrapper hid the destructive call from approval | Resolved: destructive labelling and approval sentence (A3, A5, A6) |
| AS-F07 | P2 | in | Writes and the subprocess runner sat in `gates/` | Resolved: `shipment_close/` package (layering note) |
| AS-F08 | P2 | in | `feature_id` was not bound to the qualifying set | Resolved (A2) |
| AS-F12 | P2 | in | `build_evidence_path` lacked the workspace root | Resolved (A1) |
| SL-F05 / SL-F07 | P2 | in | TOCTOU on the gate read | Resolved with a pre-read identity and containment re-check (A4). The residual parent-swap race is accepted as outside the threat model |
| AN-F05 | P2 | in | Edited routing sections had no parity pin | Resolved (A5, A6) |
| AN-F06 | P2 | in | Exit 2 was ambiguous and `--json` was undefined | Resolved: exit 8 and `--json` fields (A3) |
| AN-F08 | P2 | in | A re-hash drift left a misleading `invoking` record | Resolved: re-hash first (A3 step 6) |
| CR-F02 | P2 | in | Principle IX: deterministic serialization | Resolved (A1) |
| PR-F01 | P2 | in | Typed signatures, one error type, exit constants | Resolved (A1, A3a, A3b) |
| PR-F02 | P2 | in | Windows test fakes need an `.exe` or `argv_prefix` seam | Resolved (A3a) |
| PR-F03 | P2 | in | Process-group kill and an absolute `taskkill` path | Resolved (A3a) |
| SBA-F02 | P2 | in | SAFE_CLOSE fail-closed amends D-A3 | In scope under C1: it completes R5 on the same gate contract surface. Operator decision pending (below) |
| SBA-F03 | P2 | in | The gate could land before the routing | Resolved: A4, A5, and A6 ship in one release unit (Dependency Graph) |
| SBA-F04 | P2 | out | A trusted absolute binary pin in the registry | Out of scope (C1: new configuration contract). Stash at the harvest session |
| LR-F01 | P2 | in | Cite the 2026-08-20 linked-deliberation lesson | Resolved (A2) |
| CR-F03 | P3 | in | Emit P-005 telemetry on HALT exits | Carry to the A3 task as an optional note |
| PR-F04 | P3 | in | Join reader threads with a bound | Resolved (A3a) |
| PR-F05 | P3 | in | Test modules follow the repository's canonical unittest runner | Carry to every code task |
| SBA-F01 | P3 | in | The unit count grew from 7 to 10 | Accepted. Every split is justified by AS-F06 |
| LR-F02 / LR-F03 | P3 | in | Cite the timeout lesson and the `bootstrap_grant` `O_EXCL` precedent | Resolved |

Totals raised, after deduplication (AN-F03 was merged into AS-F01): **7 P0, 14 P1, 16 P2, 6 P3**. Open at the gate: **0 P0, 0 P1**. The
open P2 items are the accepted SL-F04 and SL-F07 residuals and the SBA-F04
out-of-scope follow-up. The open P3 items are the CR-F03 and PR-F05 carries.

## Stage-Recommended Decisions (pending operator confirmation)

> *Partly superseded (operator rulings 2026-09-27T22:50-07:00): items 1 and 4 are
> operator-confirmed. Items 2 and 3 were not named in the ruling. They stand as this
> review's accepted residuals unless the operator overrides them before Ship claims
> 198-S. See "Post-review amendments (operator rulings 2026-09-27T22:50-07:00)" at
> the end of this record.*

1. **D-A3 amendment (AN-F01, SBA-F02):** SAFE_CLOSE closures require a verdict
   record, and the gate fails closed instead of only warning. Fallback if the
   operator declines: revert the A4 SAFE_CLOSE branch to a warning, and record
   AN-F01 as an accepted residual.
2. **Benign-residual acceptance (AN-F01, AN-F07):** a direct cascade whose effect
   equals the safe-close outcome is not detected. It stays a P-005 deviation by
   skill contract, and enforcement is requested upstream in A7.
3. **Accepted residuals:** SL-F04 (finite redactor) and SL-F07 (parent-swap race
   outside the threat model).
4. The original D-A1 to D-A6 remain Stage-recommended and pending, as recorded in
   the deliberation.

## Runtime Verification and Closure Readiness

The plan's Runtime Verification section now carries an environment precheck, an
OS-temp scratch workspace, a real-binary proof, a delete-and-FAIL proof, a re-run
no-clobber proof, and an explicit `BLOCKED` path (P-012). Operational closure
names a rollback per unit, rollback triggers, a monitoring window (the next three
CASCADE closures), and the owner (Ship). No gap remains.

## Harvest Carries

* Every code-bearing unit (A1, A1b, A2, A3a, A3b, A3, A4) carries
  `harness-surface:harness-architect`, and A5 to A7 carry `harness-surface:none`.
* Sizes and complexities follow the plan: A1 S/low, A1b M/medium, A2 M/medium,
  A3a S/medium, A3b M/medium, A3 M/medium, A4 M/medium, A5 M/low, A6 S/low,
  A7 S/low.
* A4, A5, and A6 must be in the same release unit as A1 to A3.
* Stash at harvest: SBA-F04 (the registry binary pin).

## Post-review amendments (PR #460 hosted review)

These edits were made after `reviewed_blob` and after this review's PASS, in
response to Copilot review comments on PR #460. They tighten the plan without
widening scope and do not reopen any finding above:

* A1b / A2 / A3 / A5 (Principle VII): plain `--classify-only` is now
  no-clobber. An existing `pre_close` record gives exit 2 and nothing is written.
  Replacing a `pre_close` record needs the mutating mode or the explicit
  `--classify-only --replace-pre-close`, which is an overwrite and therefore
  needs destructive-command approval. Tasks 192.002-T, 192.006-T, and 192.008-T
  carry the same wording, and A1b gains the matching no-clobber test.

## Post-review amendments (operator rulings 2026-09-27T22:50-07:00)

These plan edits came after `reviewed_blob` and after this review's PASS. They apply
the operator's rulings on the staging deliberation. They are not new design and they
reopen no finding above:

* D-A1 to D-A6 are confirmed, including the D-A3 amendment (SAFE_CLOSE fails
  closed). The D-A3 decline fallback is moot.
* Shipment 198-S is an operator-declared `dag-root`, and its ordering-only 189-S
  edge is removed.
* The benign direct-cascade residual and the SL-F04 and SL-F07 residuals were not
  named in the ruling. They stand as accepted residuals unless the operator
  overrides them before Ship claims 198-S.
* The plan carries a matching "Operator Rulings (2026-09-27T22:50-07:00)" section,
  and 192-F carries the same wording.

## Re-review (2026-10-02, P-021 C6, stash 1263B218) — cycle 1

The 2026-09-27 PASS above predates the 2026-10-02 re-plan onto the 201-S /
195-F flat cascade contract, so the re-plan was re-reviewed before 198-S can
be claimed (P-021 C6).

* **Reviewed revision:** `afed104c` (re-plan amendment plus Hardening Pass 3).
* **Personas:** Correctness, Architecture Strategist, Scope Boundary Auditor,
  and Security Lens.
* **Result:** 5 P1 findings (Correctness F1 and F2, Architecture F1, Scope
  SR-1, and Security F1), dispositioned as R1 to R4 (Correctness F2 and Scope
  SR-1 share R1), and the remaining findings below P1. All 32 findings were
  consolidated into dispositions R1 to R18.

### Dispositions and fix commits

| Disposition | Fix | Fix commit |
|---|---|---|
| R1 | A `--classify-only` record that selected `cascade` is compared against the fresh result; any difference exits 4 and the record is never overwritten | `e3a1c889` (batch 1) |
| R2 | Removed the disposition-set deliberation records, the planned-`archive` exemption, and the `stranded_linked_deliberation` warnings from the A4 gate. A3c detects drift at close time, and the advisories stay in stash 3B43CE5A and D79EA53A | `e3a1c889` (batch 1) |
| R3 | Binary trust: bare-name `cli.binary`, basename match, and probe `cwd` in an empty temporary directory | `e3a1c889` (batch 1) |
| R4 | Unit splits A1c, A2b, A3c, A3d, and A4b (2-hour rule) | `43318b71`, `1d6b1428` (batch 2) |
| R5 | Harvest delta, removal of the edge `192.004-T` → `192.003-T`, and the 17-item manifest | `43318b71`, `1d6b1428` (batch 2) |
| R6 | Input sanitization of the probe values; the re-assessed fields are never redacted | `cb407602` (batch 3a) |
| R7 | `probe_excerpt` dropped; the A2a probe is the only version spawn | `cb407602` (batch 3a) |
| R8 | Record serialization helpers (`*_to_record` / `*_from_record`) and the canonical `declared_status` encoding | `cb407602` (batch 3a) |
| R9 | "Truly archived" parity pinned against `_is_engine_inert` | `6969a752` (batch 3b) |
| R10 | `planning_error` drift outcomes | `6969a752` (batch 3b) |
| R11 | `closure_scope` exclusion from the observation set | `6969a752` (batch 3b) |
| R12 | Record path containment under the backlog root | `6969a752` (batch 3b) |
| R13 | A1c accepts only pre-mutation outcomes (`archive`, `already-archived`, `retained_*`), never `archived`, and enforces engine/outcome consistency both ways | batch 4 (this commit) |
| R14 | The A1 record shape lists the plan fields it omits (`shipment_id`, `engine`) and why; no blanket field-for-field claim | batch 4 (this commit) |
| R15 | The command's `EXIT_*` constants live in `shipment_close/__init__.py`, not in the read-only gate module | batch 4 (this commit) |
| R16 | The `dag-root` ruling is marked superseded by the 2026-10-02 re-plan in the frontmatter and in Ruling 1 | batch 4 (this commit) |
| R17 | `redact` covers quoted JSON keys with a `:` separator; case folded into A1b scenario 1 | batch 4 (this commit) |
| R18 | A2a tests cover a non-string or over-long `commit`, empty stdout, and an unexpected exception → UNVERIFIED (folded into scenarios 1 and 3) | batch 4 (this commit) |

### Persona findings

| Persona | Finding | Severity | Disposition |
|---|---|---|---|
| Correctness | F1 | P1 | R2 |
| Correctness | F2 | P1 | R1 |
| Correctness | F3 | below P1 | R5 |
| Correctness | F4 | below P1 | R6 |
| Correctness | F5 | below P1 | R7 |
| Correctness | F6 | below P1 | R10 |
| Correctness | F7 | below P1 | R2 |
| Correctness | F8 | below P1 | R11 |
| Correctness | F9 | below P1 | R8 |
| Correctness | F10 | below P1 | R13 |
| Correctness | F11 | below P1 | R14 |
| Correctness | F12 | below P1 | R16 |
| Architecture Strategist | F1 | P1 | R4 |
| Architecture Strategist | F2 | below P1 | R6 |
| Architecture Strategist | F3 | below P1 | R8 |
| Architecture Strategist | F4 | below P1 | R9 |
| Architecture Strategist | F5 | below P1 | R13 |
| Architecture Strategist | F6 | below P1 | R2 |
| Architecture Strategist | F7 | below P1 | R15 |
| Architecture Strategist | F8 | below P1 | R5 |
| Scope Boundary Auditor | SR-1 | P1 | R1 |
| Scope Boundary Auditor | SR-2 | below P1 | R2 |
| Scope Boundary Auditor | SR-3 | below P1 | R2 |
| Scope Boundary Auditor | SR-4 | below P1 | R7 |
| Scope Boundary Auditor | SR-5 | below P1 | R18 |
| Scope Boundary Auditor | SR-6 | below P1 | R6 |
| Scope Boundary Auditor | SR-7 | below P1 | R16 |
| Security Lens | F1 | P1 | R3 |
| Security Lens | F2 | below P1 | R6 |
| Security Lens | F3 | below P1 | R12 |
| Security Lens | F4 | below P1 | R17 |
| Security Lens | F5 | below P1 | R7 |

Cycle 1 verdict: REVISE -> all findings dispositioned and applied; cycle-2 verification pending.