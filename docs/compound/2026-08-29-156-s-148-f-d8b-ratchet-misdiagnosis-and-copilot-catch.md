---
type: compound-learning
shipment: 156-S
feature: 148-F
task: 148.008-T
date: 2026-08-29
problem_type: incorrect_regression_toleration_masking_real_defect
category: testing
root_cause: A newly-surfaced set of unresolved template placeholders was classified as an already-accepted plan residual (RK-J) and "fixed" by widening a zero-tolerance ratchet baseline to accept them, without first re-reading the plan's actual DoD language closely enough to notice it required zero unresolved placeholders workspace-wide, and without checking whether the general variable-derivation function actually bound those variables at all.
resolution_type: fix
severity: high
source: docs/compound/2026-08-29-156-s-148-f-d8b-ratchet-misdiagnosis-and-copilot-catch.md
doc_type: learning
title: "A ratchet baseline is a place to prove a regression didn't happen, never a place to accept one"
citations:
  - src/autoharness/verify_workspace.py
  - tests/test_template_variable_derivation_contract.py
  - docs/plans/2026-08-27-policy-registry-and-review-persona-layer-plan.md
tags:
    - copilot-review
    - ratchet-contract
    - misdiagnosis
    - p-021-c1
    - production-regression
---

# A ratchet baseline is a place to prove a regression didn't happen, never a place to accept one

## Context

Shipment 156-S (feature 148-F, task 148.008-T, U8) installed 13 review-persona
templates, including `technology-reviewer.agent.md.tmpl` rendered twice
(`python-reviewer.agent.md`, `concurrency-reviewer.agent.md`). The plan's D8-B
section pins exact verbatim text for four placeholders —
`{{LANGUAGE_SAFETY_CHECKS}}`, `{{LANGUAGE_IDIOM_CHECKS}}`,
`{{LANGUAGE_ERROR_HANDLING_CHECKS}}`, `{{LANGUAGE_PERFORMANCE_CHECKS}}` — that
must be bound (resolved) at render time.

When U8's own end-to-end verification suite ran `autoharness verify-workspace`
against the freshly-staged workspace, these 4 placeholders showed up as
unresolved for the first time (the two technology-reviewer-derived templates
had never previously been staged for verification). The pre-existing (150-S)
`test_template_variable_derivation_contract.py` ratchet test —
`EXPECTED_UNRESOLVED_VARIABLES: frozenset[str] = frozenset()` — failed as a
result.

**The first fix attempt was wrong.** It reopened the ratchet baseline to
`frozenset({"LANGUAGE_SAFETY_CHECKS", ...})` (the 4 D8-B variables),
reasoning that RK-J (a plan risk-note) already accepted these as a residual.
This reasoning had two errors:

1. **RK-J's actual scope was misread.** RK-J only accepts, as future work,
   that the D8-B constants are *pinned literals* rather than *derived from
   `_language_defaults()`* (a generalization needed for non-Python primary
   languages). It says nothing about tolerating these 4 variables being
   **unresolved** in a Python-primary workspace — the plan's own DoD requires
   **zero unresolved placeholders** across all 14 installed artifacts.
2. **The actual binding gap was never checked.** `_derive_template_variables`
   in `verify_workspace.py` only ever wired `CONCURRENCY_PATTERNS` (D8-A) —
   the 4 D8-B variables were never bound at all. The already-installed
   `python-reviewer.agent.md` happened to already contain the correct
   resolved text from a one-off mechanism used during the original U5/U6
   install, which masked the gap until U8's fresh staging re-render exposed
   it for the first time.

The net effect: `autoharness verify-workspace` — a real CLI command a real
user would run against a real installed workspace — would report unresolved
placeholders and exit 1 (`src/autoharness/cli.py:118`,
`if report.get("unresolved"): return True`). **This was a genuine production
regression being actively hidden by a test change, not accepted by one.**

**Copilot's PR review caught it.** Its comment named the exact mechanism:
"Once the newly registered technology-reviewer template is staged, these four
placeholders enter `report["unresolved"]`; `cli.py:112-121` treats any such
entry as failure, so `autoharness verify-workspace` now exits 1 even though
this test passes... Record the D8-B values in `variables_used` (or derive them
during staging) and keep this ratchet empty rather than masking the failed
gate." Re-reading the plan's D8/D8-A-D8-D/RK-J sections in full (not just the
risk-note summary) confirmed Copilot was right and the original fix was wrong.

## The real fix

Added 4 module-level pinned constants (byte-for-byte identical to the plan's
D8-B text, verified by direct grep comparison) to `verify_workspace.py`, and a
binding block in `_derive_template_variables` gated on
`primary_language.lower() == "python"`, placed immediately after the existing
`CONCURRENCY_PATTERNS`/`ERROR_PATTERN`/`DOC_COMMENT_STYLE` bindings. Reverted
the ratchet back to `frozenset()`. Verified: `autoharness verify-workspace`
now reports "Unresolved placeholders: 0"; full suite unaffected (1905 passed,
20 skipped, unchanged pass count).

## Lesson

- **A ratchet/contract test failing is a signal to investigate the
  production code path, not primarily the test.** Widening an
  `EXPECTED_UNRESOLVED`-style baseline should be treated as a last resort
  requiring its own explicit justification traced to an accepted plan
  decision's *exact* wording — not a remembered paraphrase of it. Reread the
  cited risk-note/decision section in full before trusting a "this is already
  accepted" instinct.
- **"The plan accepts a residual" and "the DoD tolerates being unresolved"
  are different claims.** RK-J accepted a *design* residual (pinned constants
  vs. a future general derivation mechanism) — it never touched the DoD's
  zero-unresolved-placeholders requirement. Conflating a scoping note about
  *how* something is implemented with a tolerance for *whether* it works is
  an easy trap under time pressure.
- **When a placeholder is reported unresolved, check whether the derivation
  function actually binds it — don't assume prior installs prove it does.**
  The already-installed persona file's correct text (from a one-off historical
  render path) created false confidence that the general resolver handled it;
  it didn't, and only a fresh re-render exposed the gap.
- **Automated review (Copilot or otherwise) is a genuine safety net, not
  just a nag.** This finding was correct, specific, and cited the exact
  execution path (`cli.py:112-121`) that would fail in production. Treat a
  bot-authored review comment that contradicts a prior human conclusion as
  worth a full re-investigation before dismissing it as already-litigated.
- **Byte-for-byte verification matters for pinned text.** Before landing the
  corrected fix, the 4 constants were diffed directly against the plan's
  literal text via `grep`, and the already-installed artifact's existing text
  was compared against the new constants, to confirm the fix reproduces
  exactly what the plan specifies with no paraphrasing drift.

## Where this is reflected

- `src/autoharness/verify_workspace.py` — the 4 pinned D8-B constants and
  their binding block (commit `3450837f`).
- `tests/test_template_variable_derivation_contract.py` — ratchet reverted to
  `frozenset()`, comments/tests corrected to state the real fix rather than
  the withdrawn residual-toleration framing (commit `3450837f`).
- PR #417 (shipment 156-S) — Copilot review thread `PRRT_kwDORzpWpM6dbaCv`,
  replied and resolved citing the fix commit.
