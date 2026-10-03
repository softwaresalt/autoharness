---
title: "Review record: cascade-close --timeout cap remediation plan (F50BD40F)"
description: "Plan review of docs/plans/2026-10-03-cascade-close-timeout-cap-plan.md. Two dispatched reviewer subagents (Correctness / Python Reviewer and Scope Boundary Auditor) in cycle 1, plus inline Constitution, Learnings, and Architecture focuses. A dispatched fix-verification pass ran in cycle 2. Result: PASS with 0 P0 and 0 P1. All six P2 findings were fixed. Of the eleven P3 findings, ten were applied in the plan and one (AS-01) was accepted."
doc_type: review
status: complete
created: 2026-10-03
subject:
  plan_path: docs/plans/2026-10-03-cascade-close-timeout-cap-plan.md
  base_commit: e60dd84e
decision: PASS
dispatch_mode: subagent-dispatch-via-copilot-cli
severity_rule: "P0/P1 block harvest; P2 fixed or recorded; P3 advisory"
source_stash: F50BD40F
source_deliberation: docs/decisions/2026-10-03-cascade-close-timeout-cap-deliberation.md
recorded_by: Stage
---

# Review Record: cascade-close `--timeout` Cap Remediation Plan

## Verdict

```text
dispatch_mode: subagent-dispatch-via-copilot-cli
decision: PASS
```

* Decision: **PASS**.
* Open blocking findings: **0 P0, 0 P1**. Open P2 findings: **0**. All six P2
  findings were fixed before harvest. Of the eleven P3 findings, ten were
  applied and one (AS-01) was accepted.
* Plan hardening was required (three signals present) and was done inline (the
  plan's `## Plan Hardening` section).
* Harvest is **permitted**.

## Capability Declaration (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch (native)`. This Stage session
  has no native subagent tool.
  * Declared fallback: reviewer subagents were dispatched as separate,
    read-only, non-interactive `copilot -p` processes.
  * Their tool permissions:
    * allowed: `view`, `shell(git:*)`, `shell(Select-String:*)`, and
      `shell(Get-Content:*)`;
    * denied: `write`, `git commit`, and `git push`;
    * built-in MCP servers were disabled.
  * Each was told it is a leaf executor with no spawning, so the depth is 1
    hop.
  * Model: the CLI default, the same family as the caller. Cross-model
    routing was not used, so the Architecture Strategist focus was applied
    same-model and inline.
* `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, and `GRAPHTOR_UNAVAILABLE`:
  file-based search was used.

## Persona Coverage

| Persona | Mode | Cycle 1 | Cycle 2 |
|---|---|---|---|
| Correctness / Python Reviewer | dispatched subagent | PASS_WITH_FINDINGS (CR-01..CR-06: 1 P2, 5 P3) | combined fix-verification: all resolved |
| Scope Boundary Auditor | dispatched subagent | PASS_WITH_FINDINGS (SB-01..SB-06: 4 P2, 2 P3) | combined fix-verification: all resolved |
| Constitution Reviewer | inline (Stage) | PASS: no findings | n/a |
| Learnings Researcher | inline (Stage) | PASS: no findings | n/a |
| Architecture Strategist | inline, same-model (declared) | PASS: one P3 accepted (AS-01) | n/a |
| Fix verification (both dispatched focuses) | dispatched subagent | n/a | PASS_WITH_FINDINGS (NF-01..NF-04: 4 P3), all applied |

Agent-Native Parity and Security Lens were not triggered. The plan has no MCP
or agent-tool surface change, no auth change, and no new trust boundary.

## Findings and Dispositions

### Cycle 1: Correctness / Python Reviewer

The reviewer independently verified:

* the thresholds: B(28) = 1670, B(30) = 1775, B(31) = 1827, B(64) = 3560,
  B(65) = 3612;
* that every unit leaves the suite green on its own. The only existing pins
  are `tests/test_shipment_close_runner.py` ~L156-159 and
  `tests/test_cli_shipment_cascade_close.py` L222.
  `test_shipment_cascade_close_invoke.py` passes `timeout=60` explicitly;
* INV-T1 and INV-T2.

| ID | Sev | Finding (short) | Disposition |
|---|---|---|---|
| CR-01 | P2 | The close SHA is ambiguous. `merge_commit_sha` is a record key, so a replace at one SHA and a mutating run at another exits 4, and `eb8b7811` would stamp the remediation tasks wrongly. | Fixed. A single `--sha S_final` (the remediation PR merge) for both runs (plan, Runtime Verification and Closure; deliberation D7). |
| CR-02 | P2 | Workspace calibration and a `docs/gates-reference.md` link in a shipped template break cross-reference integrity. | Fixed. The note is generic, with no link, and F and P are labeled as reference values (A8c). |
| CR-03 | P3 | The insertion point splits a paragraph whose wrapped text is pinned. | Fixed. The note is a new paragraph before the END marker, with no reflow. |
| CR-04 | P3 | The formula literal is not pinned exactly, and its non-ASCII symbols invite drift. | Fixed. A single ASCII literal `B = ceil(1.5 * (F + P * N))` in the test constant `_SIZING_FORMULA`. |
| CR-05 | P3 | The `validate_timeout` docstring hard-codes the range. | Fixed. The docstring names the constants. |
| CR-06 | P3 | Exit 4 comes from the step-3 handed-off check, not step-5 revalidation, and the headroom figure was understated. | Fixed in the plan and the deliberation. |

### Cycle 1: Scope Boundary Auditor

The reviewer confirmed:

* the three-file residuals in A8a and A8c are justified;
* stash `9869AA32` is kept out of scope;
* Option A is the simplest fix that keeps a finite ceiling.

| ID | Sev | Finding (short) | Disposition |
|---|---|---|---|
| SB-01 | P2 | The template points at `docs/gates-reference.md`, which is not installed in target workspaces, and it embeds workspace coefficients. | Fixed (same as CR-02). |
| SB-02 | P2 | The "stay attached" sentence conflicts, without saying so, with the circuit-breaker instruction's "terminate the process" after 5 minutes. | Fixed. An explicit interim, command-specific precedence (D4). The circuit-breaker instruction is not edited, and `9869AA32` is the named tracking point (Constraints). |
| SB-03 | P2 | The close SHA and the branch order were not stated. | Fixed. Staging merges first, then one implementation branch from `main` (the closure branch is already merged, PR #483), then S_final, then the closure branch. |
| SB-04 | P2 | The manifest-append authorization was only paraphrased, and the 198-S body update was not planned. | Fixed. The relay text is quoted verbatim, and harvest adds comments on 198-S and 192-F plus description amendments. |
| SB-05 | P3 | "Feature first" was ambiguous for an existing manifest. | Fixed. Append after `192.010-T`; 192-F stays at index 0. |
| SB-06 | P3 | A new closure-artifact wall-time obligation is scope creep. | Fixed. It is now a prose note in the reconcile report only. |

### Inline personas

* **Constitution Reviewer.** No findings.
  * Role boundaries hold: Stage plans only.
  * Both destructive closure steps name operator destructive-command approval.
  * Scratch and workspace rules are unaffected.
  * No secrets are involved.
* **Learnings Researcher.** No findings.
  `docs/compound/2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md`
  is reflected: a timeout stays `indeterminate`, never "no mutation" (INV-T3).
  No prior solution covers timeout sizing.
* **Architecture Strategist** (same-model, declared). One finding:
  * **AS-01 (P3, accepted).** `SHIPMENT_USAGE` repeats the numbers as
    literals instead of deriving them from the runner constants. The lazy
    import of `runner` in `cli.py` would have to become eager, or the usage
    would have to be formatted at print time. The A8b test pin derived from
    the constants prevents drift at lower cost.

### Cycle 2: fix verification

All twelve cycle-1 findings were verified as resolved. The granularity check
holds:

| Unit | Files | Functions | Scenarios |
|---|---|---|---|
| A8a | 3 | 1 | 2 |
| A8b | 2 | 1 | 1 |
| A8c | 3 | 0 | 0 new |
| A8d | 2 | 2 | 2 |

The two three-file units follow the accepted residual precedent. Each unit
leaves the suite green.

| ID | Sev | Finding (short) | Disposition |
|---|---|---|---|
| NF-01 | P3 | Pins could break on line wraps, and the exact sentence tokens were unspecified. | Fixed. The plan lists the exact tokens, and A8d checks them on whitespace-collapsed text. |
| NF-02 | P3 | The S_final rationale did not cover the 23 original members. | Fixed. The trade-off is stated, and traceability is kept through per-task `commit` fields, PR #482, and the closure artifact. |
| NF-03 | P3 | The precedence sentence lacked an anchor in the circuit-breaker instruction. | Fixed. It cites the circuit-breaker's own "the most specific applicable limit governs" principle, which is also a pinned token. |
| NF-04 | P3 | The review record was missing. | Fixed. This document. |

## Harvest Carries

* The release unit `release-unit-a8` (A8a-A8d) lands in one PR.
* Ship-owned at implementation:
  * refresh the `.autoharness/harness-manifest.yaml` checksum for
    `.github/skills/shipment-reconcile/SKILL.md` (A8c), from the LF staged blob;
  * use the canonical runner
    `$env:PYTHONPATH='src'; python -m unittest discover -s tests`.
* Closure (Ship, after the remediation merge):
  1. `--classify-only --replace-pre-close` at S_final, with operator approval.
  2. The mutating `cascade-close` at S_final, with the default timeout (N = 28,
     B = 1670 s), with operator approval, staying attached until exit.
