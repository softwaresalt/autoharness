---
title: "Spike skill template docline frontmatter conformance"
source: docs/plans/2026-08-16-spike-template-docline-conformance-plan.md
doc_type: plan
description: "Implementation plan for stash 61358124 — bring templates/skills/spike/SKILL.md.tmpl Phase 5 findings-artifact frontmatter into conformance with the docline contract validated by `backlogit docs lint --profile authoring`."
---

# Implementation plan — spike skill template docline frontmatter conformance

* **Source stash**: `61358124` (low priority, task, no prior deliberation, never consumed)
* **Cross-workspace counterpart**: backlogit stash `7F0A6E89` / source task `102.001-T`;
  the backlogit-side implementation already shipped in `ec2b859`.
* **Agent / route**: Stage — `claude-opus-5` / `anthropic` / `high`
* **Mode**: P-017 dark factory, operator AFK, autonomous judgment authorized
* **Requires plan hardening**: **no** — see the hardening gate assessment below.

## Problem

`templates/skills/spike/SKILL.md.tmpl` Phase 5 (lines ~282–294) instructs the agent to
write the spike findings artifact with this frontmatter:

```yaml
title: "{Goal question — short form}"
type: spike
date: {YYYY-MM-DD}
time_box: "{time_box value}"
conclusion: "{proceed|pivot|defer|abandon}"
confidence: "{high|medium|low}"
linked_parent_work_item: "{feature or chore path/ID, or null}"
promoted_to: ["{plan|queue|learnings|none}"]
tags:
  - "{domain tag}"
  - "{technology tag}"
```

Every spike-specific field sits at the top level, and the docline-required top-level
fields `source`, `doc_type`, and `description` are absent. Consequently **every findings
artifact this template generates fails documentation lint**.

## Evidence (measured this session, not asserted)

Both shapes were rendered into a throwaway backlogit workspace outside this repository
and linted with the installed toolchain (`backlogit v1.9.0-39-g17530fe3`). The probe
workspace was deleted afterwards; this repository was not mutated.

| Shape | `backlogit docs lint --profile authoring` |
|---|---|
| Current template shape | `valid: false`, **2 violations** — `source` required/missing, `doc_type` required/missing |
| Target `docline`-nested shape | `valid: true`, **0 violations** |

This is a confirmed live defect with a verified fix shape, not a speculative cleanup.

## Target shape

```yaml
title: "{Goal question — short form}"
source: {{DOCS_DECISIONS}}/{YYYY-MM-DD}-{slug}-spike.md
doc_type: decision
description: "{One-sentence summary of the investigation and its outcome}"
docline:
  type: spike
  date: {YYYY-MM-DD}
  time_box: "{time_box value}"
  conclusion: "{proceed|pivot|defer|abandon}"
  confidence: "{high|medium|low}"
  linked_parent_work_item: "{feature or chore path/ID, or null}"
  promoted_to: ["{plan|queue|learnings|none}"]
  tags:
    - "{domain tag}"
    - "{technology tag}"
```

## Scope

**In scope**

1. The Phase 5 YAML example block in `templates/skills/spike/SKILL.md.tmpl`.
2. The Step 4.2 promotion instruction at line ~226, which currently reads "Update the
   spike findings artifact's `promoted_to` frontmatter field to include `plan` and add a
   `plan_artifact` field". Both field references must be re-pointed under `docline` so the
   template stays internally consistent with its own Phase 5 example. **This is the
   coherence trap in this change**: fixing the example alone leaves the template
   instructing the agent to write a top-level `promoted_to` that no longer exists.
3. Test/fixture verification that a generated findings artifact conforms.

**Explicitly out of scope**

* The 10 pre-existing `docs/decisions/*.md` files that already fail authoring lint for
  missing `source`/`doc_type`. They are historical artifacts, not template output, and
  are **not** in this stash's scope. Fixing them here would be silent scope expansion.
* `docs/audits/` `doc_type: audit` not being in the ingestion-profile closed vocabulary.
  Separate concern, separate surface, not in scope.
* Any other skill template. `templates/skills/brainstorm/SKILL.md.tmpl` already references
  the docline path map and needs no change.
* There is **no** installed `.github/skills/spike/SKILL.md` in this workspace, so no
  installed-copy synchronization is required.

## Decomposition

Two width-isolated tasks. Task 1 is template authoring; task 2 is test/verification.
They are deliberately not combined — different surfaces, different failure modes.

### Task 1 — Correct the spike template's findings-artifact frontmatter contract

Edit `templates/skills/spike/SKILL.md.tmpl` only:

* Replace the Phase 5 YAML block with the target shape above.
* Re-point the Step 4.2 `promoted_to` / `plan_artifact` references under `docline`.
* Use the existing `{{DOCS_DECISIONS}}` template variable for `source` — do not hardcode
  `docs/decisions`, and do not introduce a new unregistered docs path. `{{DOCS_DECISIONS}}`
  is already registered (`install-harness` SKILL.md line 281 → `docs/decisions`) and is
  already used elsewhere in this same template, so this introduces **no new variable**.
* **`source` must resolve to the artifact's own repo-relative path.** The Phase 5
  instructions must state explicitly that the agent substitutes the real `{YYYY-MM-DD}`
  and `{slug}` it used for the filename, so `source` matches the file it appears in. A
  findings artifact that ships with an unsubstituted placeholder in `source` is
  self-inconsistent even though it may still pass a presence-only lint rule.
* **`description` is handoff-required, not lint-enforced.** Measured this session: neither
  the `authoring` nor the `ingestion` profile flags a missing `description`. It is required
  by the `61358124` / `7F0A6E89` handoff contract and by ingestion usefulness. Record this
  so a later reader does not delete it as redundant.
* Change nothing else: no spike workflow behaviour, no inputs, no phase structure. The
  `time_box` and `linked_parent_work_item` entries in the **Inputs** section (lines ~38
  and ~42) describe skill *inputs*, not frontmatter, and must be left alone.

Size **XS** / complexity **low**. Single file, mechanical, with a verified target shape.

### Task 2 — Verification that generated spike findings conform

* Add focused test coverage asserting the template's Phase 5 frontmatter example carries
  top-level `title`, `source`, `doc_type: decision`, `description`, and nests `type`,
  `date`, `time_box`, `conclusion`, `confidence`, `linked_parent_work_item`,
  `promoted_to`, and `tags` under `docline`.
* Assert no top-level `type:`/`conclusion:` remains in the Phase 5 block (regression guard
  against a partial fix).
* Assert the template contains no residual top-level `promoted_to` instruction in Step 4.2.
* Use a **new** test module named `tests/test_spike_template_docline_frontmatter.py`.
  `tests/test_verify_workspace.py` has pre-existing uncommitted operator changes in the
  working tree and must not be disturbed.
* Existing template/plugin verification must continue to pass.

Size **S** / complexity **low**.

**Dependency**: Task 2 verifies Task 1's output and must be sequenced after it.

## Acceptance criteria

1. A findings artifact generated from the corrected template, **written to the in-scope
   `docs/decisions/` surface**, passes `backlogit docs lint --profile authoring` with
   **zero** findings attributable to that artifact. The path qualifier is load-bearing:
   measured this session, `backlogit docs lint --path docs/plans` returns empty output and
   exit 1 because `docs/plans` is not an in-scope documentation surface, so a fixture
   linted from the wrong directory would produce a vacuous pass.
2. `doc_type: decision` is confirmed inside the linter's closed vocabulary — verified this
   session by running the `ingestion` profile against a `doc_type: decision` artifact and
   observing **no** `unknown_doc_type` finding (only the expected pipeline-supplied
   `ingested_at`). Contrast: `doc_type: audit` *is* rejected by that rule, so this check is
   discriminating rather than a formality.
3. The template is internally consistent: no instruction anywhere in the file references a
   frontmatter field at a level the Phase 5 example does not produce.
4. Existing template/plugin verification passes.
5. No unrelated spike workflow behaviour changes.
6. No file outside `templates/skills/spike/SKILL.md.tmpl` and
   `tests/test_spike_template_docline_frontmatter.py` is modified.

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Partial fix — example corrected, Step 4.2 left stale | Medium | Task 2 asserts on it explicitly; called out as the coherence trap above |
| External contract drift — backlogit's lint contract changes | Low | Evidence is pinned to `v1.9.0-39-g17530fe3`; acceptance re-runs the real linter rather than trusting a hardcoded expectation |
| Scope creep into the 10 pre-existing failing decision docs | Medium | Explicitly excluded above and enforced by acceptance criterion 5 |
| Touching the dirty `tests/test_verify_workspace.py` | Medium | Task 2 mandates a new test module |

## P-006 hardening gate assessment

**Requires plan hardening: no.** Assessed against the three elevated-blast-radius signals:

* **Schemas** — not touched. No JSON schema changes.
* **CLI distribution** — not touched. No `src/autoharness/` changes, no packaging changes.
* **Multiple template families** — no. Exactly one family (`templates/skills/spike/`), one file.

The one non-trivial property is the cross-tool coupling to backlogit's externally-owned
docline contract. That is recorded as an explicit risk with a version-pinned evidence
trail and a live-linter acceptance criterion rather than escalated to hardening, because
it does not widen the change's blast radius — it only bounds the durability of the
verification, which acceptance criterion 1 re-establishes on every run.

## Traceability

* Stash `61358124` → this plan → review
  `docs/reviews/2026-08-16-spike-template-docline-conformance-review.md`
* Cross-workspace counterpart: backlogit stash `7F0A6E89`, task `102.001-T`, commit `ec2b859`
