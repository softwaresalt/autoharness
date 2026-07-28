---
title: "088 Compression — Failure-Content-in-Success Decline: Spec Reconciliation + Detector Coverage Hardening (Follow-up Plan)"
date: "2026-07-28"
description: "Follow-up implementation plan for stash 3D8724BA: reconcile the 088-F compression plan spec to the shipped failure-bearing-success decline invariant and close a colon-anchored coverage gap in the decline detector, with positive and negative controls. Throwaway, flag-gated experiment only; no default install."
doc_type: plan
source: docs/plans/2026-07-28-088-failure-content-in-success-decline-followup-plan.md
deliberation_source: "008-DL"
stash_source: "3D8724BA"
feature: "093-F"
relates_to:
  - "088-F"
  - "086-F"
references:
  - "docs/plans/2026-07-15-copilot-cli-output-compression-experiment-plan.md"
  - "docs/decisions/2026-07-25-copilot-cli-output-compression-experiment-findings.md"
  - "experiments/088-compression-experiment/brainspace/policy.py"
  - "experiments/088-compression-experiment/brainspace/hook.py"
  - "experiments/088-compression-experiment/brainspace/evidence_oracle.py"
requires_plan_hardening: "yes"
plan_review_verdict: "approved-with-conditions"
tags:
  - "copilot-cli"
  - "compression"
  - "experiment"
  - "evidence-integrity"
  - "primitive-5"
  - "primitive-7"
  - "follow-up"
---

<!-- markdownlint-disable MD013 -->

<!-- markdownlint-disable-next-line MD025 -->
# 088 Compression — Failure-Content-in-Success Decline: Spec Reconciliation + Detector Coverage Hardening

## Problem and source

Stash `3D8724BA` (high, PR #226 Copilot review, `compression-plan:84`) asked that
the 088-F compression prototype **decline** (never compress) a **successful**
`postToolUse.textResultForLlm` that embeds failure evidence — a non-zero exit
code, `stderr`, a stack trace, or a gate verdict — and that a **failure-content
detector** plus **negative controls** be added to the plan task breakdown and the
`088.004-T` acceptance criteria.

**Investigation finding (reality check).** The detector itself already shipped.
Commit `118bf21` (`feat(088.004-T)`, 2026-07-25) introduced
`brainspace/policy.py::classify_decline_reason` with the
`FAILURE_BEARING_SUCCESS` decline reason and `_FAILURE_BEARING_PATTERNS`, wired
it into `hook.py::process_post_tool_use` (declines **before** compression on
`resultType == "success"`), and added negative controls
(`test_policy_decline_cases.py::test_failure_bearing_success_declines`,
`test_hook_decide_then_stash.py::test_failure_bearing_output_declines_before_store`,
a `corpus.py` decline control, and a `benchmark-report` control row). `088-F`,
`088.004-T`, and shipment `088-S` are now **archived**, so the stash entry's
original intent (fold the spec-expansion into the still-open 088-F shipment) is
no longer reachable.

Two residuals from the stash entry remain **genuinely open**:

1. **Spec drift.** The compression plan
   (`docs/plans/2026-07-15-copilot-cli-output-compression-experiment-plan.md`,
   last touched 2026-07-23, before the detector landed) still describes
   `088.004-T` only in terms of secret / gate / stack-trace / operator decline
   cases plus "confirm failure outputs are untouched" — which refers to the
   `postToolUseFailure` passthrough, **not** the failure-bearing-**success**
   decline invariant that was actually implemented. The spec is the
   system-of-record for the deferred narrow pilot; if it does not mandate this
   invariant, a future implementer could regress it.
2. **Coverage gap (evidence-integrity).** `_FAILURE_BEARING_PATTERNS` is
   colon-anchored (`exit code:\s*[1-9]\d*`, `exit status\s*[1-9]\d*`,
   `returncode=[1-9]\d*`, `^stderr:`). Very common non-colon phrasings —
   `exit code 1`, `exited with code 1`, make `Error 1` / `*** [target] Error 1`,
   `npm ERR!`, JetBrains `Process finished with exit code 1` — are **not**
   detected. For such a successful result `classify_decline_reason` returns
   `None`, the result becomes a compression candidate, and if the failure line
   sits in the omitted middle, `_compress_view` collapses it → evidence loss.
   The hook's `_EVIDENCE_LINE_PATTERNS` and `evidence_oracle.py` share the same
   colon assumption, so neither protects nor flags the uncovered forms.

Per the 093-S closure learning, evidence-integrity gaps in this experiment are
**hard blockers for narrow-pilot promotion** — "that promotion gate never
relaxes." Closing this gap is therefore on the promotion path, not cosmetic.

## Scope and non-goals

**In scope (single skill domain: the 088 compression decline / evidence-integrity policy):**

* Broaden the decline detector's failure-signal recognition to the common
  non-colon / alternate non-zero-exit and stderr forms, with positive **and**
  negative controls.
* Align the hook's evidence-line protection and the evidence oracle to the same
  broadened failure-signal set (defense-in-depth + measurement correctness).
* Reconcile the 088-F compression plan spec and capture explicit acceptance
  criteria + traceability for the failure-bearing-success invariant.

**Explicit non-goals:**

* No change to the throwaway / flag-gated / disabled-by-default posture of the
  experiment. No default or production install.
* No re-implementation of the already-shipped detector, negative controls, hook
  wiring, store, retrieval, or measurement harness.
* No schema changes, no CLI-distribution changes, no base-harness behavior
  changes, no new capability pack.
* No generic "any error/failed/non-zero" heuristic — the design deliberately
  uses precise, enumerated forms to protect AUC-savings measurement fidelity.

## Work breakdown (2-hour rule, width-isolated)

| Task | Concern | ~Effort | Depends on |
| --- | --- | --- | --- |
| 093.001-T Broaden decline detector failure-signal coverage (`policy.py`) + positive/negative controls | decline policy | ~2h | — |
| 093.002-T Align hook evidence-line protection + evidence oracle to the broadened set | evidence-integrity defense-in-depth | ~2h | 093.001-T |
| 093.003-T Reconcile compression plan spec + capture acceptance criteria and traceability | spec / docs | ~1.5h | 093.001-T, 093.002-T |

Each task targets a single concern in one file family; no task mixes detector
code, hook/oracle code, and doc reconciliation.

### Task detail

* **093.001-T** — In `brainspace/policy.py`, extend `_FAILURE_BEARING_PATTERNS`
  to recognize the common non-colon / alternate non-zero-exit and stderr forms
  while explicitly **excluding zero-exit** forms (`exit code: 0`, `exit code 0`,
  `exited with code 0`). Candidate additions (final set to be confirmed against
  false-positive risk): `exit code 1` (space, no colon),
  `exited with (exit )?code N`, `returncode N` (space form),
  make `Error N` / `*** [target] Error N`, `npm ERR!`,
  `Process finished with exit code N`. Add **positive controls** (each new form
  classifies as `FAILURE_BEARING_SUCCESS` and, through the hook, passes through
  byte-identically) and **negative controls** (benign successful outputs that
  merely mention `error`, `failed`, `warning`, or a `exit code: 0` success line
  still classify as `None` and remain compressible — no false-positive
  regression). Single concern: the decline detector only.

* **093.002-T** — Align the hook's `_EVIDENCE_LINE_PATTERNS`
  (`brainspace/hook.py`) and the evidence oracle's required-fact patterns
  (`brainspace/evidence_oracle.py`) to recognize the same broadened
  failure-signal set as 093.001-T, so that (a) any compressed (non-declined)
  view never collapses a failure-evidence line, and (b) the oracle flags a lost
  non-zero-exit / stderr fact regardless of colon form. Add tests asserting the
  broadened evidence lines are preserved by `_compress_view` and detected by the
  oracle. Depends on 093.001-T so the pattern sets stay identical.

* **093.003-T** — Update
  `docs/plans/2026-07-15-copilot-cli-output-compression-experiment-plan.md`: the
  `088.004-T` Work-breakdown row, the `088.004-T` Task-detail bullet, and the
  Plan Hardening "Evidence oracle gates every safe win" / decline bullets to
  **explicitly enumerate** the failure-bearing-**success** decline invariant
  (embedded non-zero exit / stderr / stack trace / gate verdict in a successful
  `postToolUse.textResultForLlm`). Record that the detector + negative controls
  shipped in `088.004-T` (commit `118bf21`) and that the invariant must not
  regress in the deferred narrow pilot. Capture explicit acceptance criteria and
  a `3D8724BA` → `093-F` → `policy.py`/tests traceability chain (the archived
  `088.004-T` cannot be reopened; the invariant is captured here as the
  system-of-record). Docs/backlog-only.

## Plan Hardening (P-006)

**Triggered (fail-safe): yes.** The change touches the compressor's decline
decision — an evidence-integrity surface. Hardening measures:

* **Fail-safe direction is preserved and is the whole point.** Broadening a
  **decline** detector can only make the compressor **more** conservative: it
  passes *more* originals through byte-identically. It can never newly hide
  evidence. The only downside is a reduction in compression coverage
  (false positives), which is an experiment-quality concern, not a safety
  regression.
* **Negative controls are mandatory, not optional.** Every added pattern must
  ship with a negative control proving a benign successful output that merely
  mentions "error"/"failed"/"warning"/a zero-exit success line still compresses.
  This bounds the false-positive blast radius on the experiment's AUC-savings
  fidelity.
* **Pattern-set parity is a hard invariant.** The decline detector
  (`policy.py`), the hook's evidence-line protection (`hook.py`), and the
  evidence oracle (`evidence_oracle.py`) must recognize the **same** broadened
  failure-signal set. 093.002-T depends on 093.001-T precisely so the three sets
  cannot drift.
* **Containment unchanged.** No new store, no new I/O, no new external surface;
  the experiment remains disabled-by-default and throwaway. Rollback = disable
  the flag / delete `experiments/088-compression-experiment/` (already true).
* **Spec-before-regression.** 093.003-T records the invariant in the plan
  system-of-record so the narrow pilot cannot silently drop it.

Blast radius does **not** hit the elevated triggers (no schema, no CLI
distribution, no multiple template families, no base-harness dependency).
Hardening is applied for fail-safe completeness, not because the change is wide.

## Plan Review (multi-lens)

* **Safety / evidence-integrity** — PASS. Change is fail-safe-directional;
  negative controls bound false positives; pattern-set parity prevents
  defense-in-depth drift. Directly closes a promotion-blocking gap (093-S).
* **Scope / width isolation** — PASS. One skill domain (decline / evidence
  policy) confined to `experiments/088-compression-experiment/` + one plan doc.
  No mixing with unrelated stash entries (8FD768E9 engram-doc,
  7D1E2F1A telemetry rotation, rename/`/compact`/intercom features all stay in
  the stash).
* **Task granularity (2-hour rule)** — PASS. Three single-concern tasks,
  single file family each, with a clean dependency chain (T1 → T2 → T3).
* **Duplication risk** — PASS with condition. The detector, hook wiring, and
  base negative controls already shipped (118bf21). Ship MUST extend, not
  re-create them; each task description states this explicitly.
* **Testability** — PASS. Positive + negative controls per added pattern;
  evidence-line preservation + oracle detection tests; targeted pytest over
  `experiments/088-compression-experiment/tests` (097-S: the repo *source* gate
  remains `PYTHONPATH=src python -m unittest discover -s tests`, but the
  experiment ships its own pytest suite).

**Verdict: approved-with-conditions.** Conditions: (1) Ship extends the existing
detector/tests rather than re-implementing them; (2) every new failure-signal
pattern ships with a paired negative control; (3) `policy.py`, `hook.py`, and
`evidence_oracle.py` failure-signal sets stay identical.

## Handoff to Ship

* Shipment covers feature `093-F` + tasks `093.001-T` → `093.003-T` in
  dependency order.
* Implementation is Ship's: 093.001-T / 093.002-T are code+tests under
  `experiments/088-compression-experiment/`; 093.003-T is a docs/backlog edit to
  the 088-F compression plan.
* Test surface: `pytest` over `experiments/088-compression-experiment/tests`
  (has its own `conftest.py` fixtures). Keep the experiment disabled-by-default.
* Traceability: stash `3D8724BA` → deliberation `008-DL` → this plan → `093-F`.
