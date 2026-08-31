---
title: "SHIP-5 — Fail-closed harness verification gates"
date: 2026-08-31
slug: fail-closed-harness-gates
doc_type: plan
source_stash: "D1A46B8C, 5CBA0A85, 11BCE865"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-5"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
---

# SHIP-5 — Fail-closed harness verification gates

## Problem

Three gates that report success when they have not actually checked anything.
Governing law, inherited from `029-DL`: **a convention survives iff a machine
produces it or penalizes its absence.** All three of these penalize nothing.

### D1A46B8C — markdownlint is installed but not enforced

`.markdownlint.json` exists and P-008 is therefore *enforceable*, but:

* `.githooks/pre-push.sh` L29 guards the lint behind
  `if command -v markdownlint >/dev/null 2>&1;` and L36-L37 emit
  `WARNING: markdownlint not found — skipping Markdown lint gate.` and exit
  successfully. **The gate is absent on every machine that has not installed
  `markdownlint-cli`.**
* There is no markdownlint job in CI at all, so the hook is the only carrier and
  it fails open.

Source ref: PR #409 review; deferred under P-021 C1 because changing hook control
flow alters hook *semantics* for every contributor and adding a CI job changes CI
*composition* — both different contract surfaces from "install the missing config
file".

### 5CBA0A85 — no fail-closed agent→skill dangling-reference check

This is the residual open question carried out of `8AC574F1` ("13 skills
referenced by installed pipeline agents are not installed"), which Stage archived
on 2026-08-29 as SATISFIED. The installation half is genuinely done —
`.github/skills/` now installs 18 skills and all 13 previously-missing pipeline
skills are verified present. But the closing question was not satisfied by that
installation: **nothing prevents the regression from recurring.** The gap was
found by inspection, not by a gate.

### 11BCE865 — silent frontmatter truncation is undetectable

Ten `docs/` files carry silently truncated frontmatter values. The failure mode
is distinct from, and nastier than, a decode failure: an unquoted YAML scalar
containing **space-hash** triggers YAML's comment rule, so the value is silently
cut at the `#` and the document still parses. `tests/test_docs_frontmatter_decodes.py`
asserts the frontmatter *decodes* — which it does — so the guard cannot see this
class at all. None of the ten were introduced by the P-020 compaction that found
them.

## Direction

Make each gate penalize absence:

1. Add a markdownlint CI job that runs on every PR, and change the pre-push hook
   from skip-on-missing to **fail**-on-missing.
2. Add a fail-closed cross-reference check to `verify-harness` that resolves
   every skill named by an installed agent and fails when one is not installed.
3. Repair the ten truncated values and extend the frontmatter guard to detect
   truncation, not merely decode failure.

## Hardening (P-006)

Triggered: changes CI composition and hook semantics for every contributor.

* **H1 (binding).** The pre-push hook's fail-on-missing message must name the
  exact install command (`npm install -g markdownlint-cli`) and an explicit,
  documented escape hatch (`git push --no-verify`), so the change is a *gate*,
  not a wall. A contributor who cannot install the linter must still be able to
  push deliberately and visibly.
* **H2 (binding).** The CI job must land **before or with** the hook change. If
  the hook starts failing while CI still has no markdownlint job, the only
  enforcement lives on developer machines — strictly worse than today for anyone
  who cannot install it.
* **H3 (binding).** The CI job must lint the **same glob with the same config**
  as the hook (`**/*.md` with `.markdownlint.json`). Two gates with different
  scopes produce green-locally/red-in-CI, which trains contributors to ignore the
  local gate.
* **H4 (binding).** The new `verify-harness` check must be *additive and
  fail-closed for the check itself*: if the agent set or skill set cannot be
  enumerated, the check must fail rather than pass vacuously. A cross-reference
  check that silently finds zero references is the same bug it exists to catch.
* **H5.** Repairing the ten truncated values is a **content-preserving** edit:
  quote the scalar so the full value survives. Do not rewrite or shorten the
  values, and do not touch files outside the enumerated ten.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Add a fail-closed markdownlint CI job and make the pre-push hook fail when the linter is missing | M | medium | `.github/workflows/`, `.githooks/pre-push.sh` |
| 2 | Add a fail-closed agent→skill dangling cross-reference check to `verify-harness` | M | high | `src/autoharness/`, `tests/` |
| 3 | Repair the ten truncated docs frontmatter values and extend the guard to detect silent truncation | M | medium | `docs/**`, `tests/test_docs_frontmatter_decodes.py` |

Task 1 keeps the CI job and the hook change together to honour **H2** and **H3** —
splitting them would guarantee a window where the two gates disagree.

## Non-goals

* No new markdownlint rules and no change to `.markdownlint.json`. If the
  repository does not currently lint clean under the existing config, driving the
  count to zero is in scope only for files this shipment already touches;
  anything broader is a P-021 capture.
* No general cross-reference framework. Task 2 checks exactly one edge type:
  installed agent → named skill. Path, anchor and `file:line` citation resolution
  belongs to portfolio unit **S4** (D-PROV, `PROV-04`), which already owns it.
* No change to which skills are installed.

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `verify-harness`;
`markdownlint "**/*.md"` locally and in CI; a deliberate negative test for each
gate (uninstall/mask the linter → hook must fail; remove a skill → verify-harness
must fail; introduce a space-hash scalar → frontmatter guard must fail).

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Correctness | **P0** | Turning markdownlint fail-closed in CI **before** the repository lints clean would make `main` permanently red and block every PR in this run's own portfolio. | **Resolved.** Task 1's acceptance is ordered: (a) run the linter over the current tree and record the violation count; (b) if non-zero, the job lands scoped to **changed files** on PRs, with a repository-wide run added only once the count reaches zero. The count must be measured, not assumed. This is recorded as a hard precondition, not a suggestion. |
| 2 | Correctness | **P1** | Hook fail-on-missing plus no escape hatch would hard-block any contributor without Node.js. | **Resolved** as binding **H1**: named install command plus documented `--no-verify` escape. |
| 3 | Architecture | **P1** | A `verify-harness` check that enumerates skills by scanning `.github/skills/` will pass vacuously in a workspace where the directory is absent. | **Resolved** as binding **H4**: inability to enumerate either side is a **failure**, not a skip. Task 2's acceptance includes a negative test for the empty/absent-directory case. |
| 4 | Maintainability | **P1** | Task 2 must parse agent markdown to find skill references; a naive regex will produce false positives on prose that merely mentions a skill name. | **Resolved.** Task 2's acceptance restricts detection to **structured invocation references** (the documented `invoke the X skill` / explicit `.github/skills/<name>` path forms) and requires the check to report the exact file and line of each unresolved reference, so a false positive is immediately diagnosable rather than mysterious. |
| 5 | Template integrity | P2 | Repairing docs frontmatter could alter values that downstream tooling reads. | **H5**: quote-only, content-preserving. Task 3's acceptance asserts the decoded value after repair equals the *intended* full value, and that the file still decodes. |
| 6 | Scope | P2 | Task 3 could expand into a repository-wide frontmatter audit. | Bounded to the ten enumerated files plus the guard extension. Any eleventh file the extended guard reveals is a P-021 capture. |
| 7 | Security | P3 | A CI job that runs `npm install -g` pulls a third-party toolchain into the pipeline. | Pin the `markdownlint-cli` version and use the existing Node setup action already present in the workflow ecosystem; no unpinned global installs. Recorded as an acceptance criterion on task 1. |
| 8 | Constitution | P3 | Changing hook semantics affects every contributor without their consent. | Principle-conformant: the change adds a gate with a documented escape and is announced by the failure message itself. **H1**. |

**Verdict: PASS.** 1 P0 and 3 P1 raised; all four resolved before harvest. Zero
unresolved P0/P1. Two review-fix cycles of three.
