---
title: "Multi-persona plan review — spike template docline frontmatter conformance"
source: docs/reviews/2026-08-16-spike-template-docline-conformance-review.md
doc_type: review
description: "Mandatory multi-persona adversarial review of the 61358124 implementation plan. Verdict PASS after one fix cycle; four findings raised, all resolved in the plan before harvest."
---

# Multi-persona plan review — spike template docline frontmatter conformance

* **Plan under review**: `docs/plans/2026-08-16-spike-template-docline-conformance-plan.md`
* **Source stash**: `61358124`
* **Reviewer**: Stage — `claude-opus-5` / `anthropic` / `high`
* **Cycles**: 1 fix cycle, 1 re-review
* **Verdict**: **PASS** — 0 P0, 0 unresolved P1

## Personas applied

Security, Reliability, Simplicity/Minimalism, Composability/Interoperability,
Maintainer, and an explicit Adversary/Skeptic tasked with falsifying the plan.

## Findings

### P1-1 — `source` placeholder could ship unsubstituted (Maintainer, Adversary)

**Raised.** The plan specified `source: {{DOCS_DECISIONS}}/{YYYY-MM-DD}-{slug}-spike.md`
but never stated that the agent must substitute the real date and slug. The lint rule is
presence-only, so an artifact carrying a literal `{slug}` in `source` would still pass
while being self-inconsistent — a silent contract failure that the acceptance criteria
would not catch.

**Resolved.** Plan Task 1 now carries an explicit substitution requirement with the
rationale recorded.

### P1-2 — Acceptance criterion 1 was vacuously satisfiable (Adversary)

**Raised.** "A findings artifact ... passes `backlogit docs lint --profile authoring` with
zero findings" did not say *where* the fixture lives. This was falsified empirically
during review: `backlogit docs lint --profile authoring --path docs/plans` returns **empty
output and exit 1**, because `docs/plans` is not an in-scope documentation surface. A
fixture linted from a non-scoped directory would produce zero findings for the wrong
reason and the criterion would pass without verifying anything.

**Resolved.** Acceptance criterion 1 now pins the fixture to the in-scope `docs/decisions/`
surface and records why the qualifier is load-bearing.

### P1-3 — `doc_type: decision` was assumed, not verified (Security-adjacent, Adversary)

**Raised.** The plan mandated `doc_type: decision` on the strength of the handoff text.
The linter enforces a **closed vocabulary** for `doc_type`, and the `authoring` profile
does not evaluate that rule — so the original evidence table could not have detected a
rejected value. This is a real trap: `doc_type: audit` *is* rejected by
`unknown_doc_type`, as observed on `docs/audits/2026-08-15-backlog-storage-root-reference-inventory.md`.

**Resolved.** Verified by running the `ingestion` profile against a `doc_type: decision`
artifact: **no `unknown_doc_type` finding** was produced (only the expected
pipeline-supplied `ingested_at`). `decision` is confirmed in-vocabulary. Promoted to
acceptance criterion 2 so the check is repeated rather than trusted.

### P2-4 — Task 2 test module was unnamed; `description` enforcement status unstated (Maintainer)

**Raised.** "Prefer a new test module" is nondeterministic for the executing agent, and
the plan implied `description` was contract-required without noting that neither lint
profile enforces it — inviting a future maintainer to delete it as dead weight.

**Resolved.** Task 2 now names `tests/test_spike_template_docline_frontmatter.py`
explicitly, and Task 1 records that `description` is handoff-required but not
lint-enforced. Task 2's dependency on Task 1 is now stated.

## Persona verdicts

| Persona | Verdict | Note |
|---|---|---|
| Security | **PASS** | Documentation-template prose only. No new execution path, network surface, credential handling, or privilege. Nothing downloaded or executed. |
| Reliability | **PASS** | Strictly removes a guaranteed-failure path: today *every* generated findings artifact fails authoring lint. Measured 2 → 0 violations. No new runtime failure mode. |
| Simplicity | **PASS** | One template file plus one new test module. The Adversary's challenge to collapse to a single task was rejected: template authoring and test authoring are different surfaces, and width isolation is a standing rule here. |
| Composability / Interoperability | **PASS (favoured)** | This is precisely a cross-tool conformance repair — autoharness-generated artifacts becoming valid input to backlogit's docline pipeline. Under the session's ordering policy, composability/interoperability supersedes feature work, which is what justifies staging this ahead of the deferred feature-shaped entries. |
| Maintainer | **PASS after fix** | P1-1 and P2-4 addressed determinism and future-reader hazards. |
| Adversary / Skeptic | **PASS after fix** | Two of its three falsification attempts succeeded (P1-2, P1-3) and forced real plan changes. Its remaining objection — that this is low-priority cosmetic work — is rejected: the defect is a 100% failure rate on generated artifacts, verified by measurement, not a style preference. |

## Scope-discipline check

The plan explicitly excludes the 10 pre-existing `docs/decisions/*.md` files that already
fail authoring lint, and the `docs/audits/` `doc_type: audit` vocabulary mismatch. Both
are real, both were discovered during this review, and both are **out of the `61358124`
stash scope**. Harvesting them would be silent scope expansion and is a stop condition for
this session. Confirmed excluded and enforced by acceptance criterion 6.

## P-006 hardening gate

Plan declares `Requires plan hardening: no`. Independently re-assessed by this review
against the three elevated-blast-radius signals — schemas (not touched), CLI distribution
(not touched), multiple template families (one family, one file). **Concur: hardening not
required.** The cross-tool coupling to backlogit's externally-owned docline contract was
considered as a candidate signal and rejected, because it bounds the durability of the
verification rather than widening the change's blast radius, and acceptance criteria 1–2
re-establish it against the live linter on every run.

## Verdict

**PASS.** 0 P0, 0 P1 unresolved, 0 P2 unresolved. Cleared for harvest.
