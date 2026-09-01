---
title: "SHIP-2 — Release and CI pipeline fail-closed gates"
date: 2026-08-31
slug: release-ci-fail-closed-gates
doc_type: plan
source_stash: "8E10B13B, E738A7D1"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-2"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
---

# SHIP-2 — Release and CI pipeline fail-closed gates

## Problem

Two independent fail-open conditions on the paths that decide whether software is
published and whether `main` is green.

### 8E10B13B — the pre-publish PyPI probe exits 0 when the version already exists

Verified at `.github/workflows/release.yml`:

* L94-L107: the probe opens `https://pypi.org/pypi/autoharness/{version}/json`,
  catches `HTTPError`, prints "not yet on PyPI" on 404, re-raises other HTTP
  errors — and on **success** (the version exists) falls into the `else:` branch
  and merely prints "`already on PyPI; publish will skip existing files on
  reruns`". No `raise`, no `sys.exit`. **The step exits 0.**
* L109-L112: the very next step is `pypa/gh-action-pypi-publish` (SHA-pinned)
  with `skip-existing: true`, so the upload is silently skipped.
* L114+: "Smoke test published package from PyPI" then **passes**, because the
  version genuinely exists — but the artifacts it smoke-tests are the
  pre-existing ones, not the ones this run produced. The workflow then creates or
  updates the GitHub Release around them and reports success.

The workflow is triggered by tag push and is **unattended**, so no human sits
between the probe and the publish. A monitoring instruction cannot enforce this;
the interim mitigation applied in PR #422 moved an assertion into task
`150.009-T` as a pre-push human-gated check, which is agent discipline, not a
machine gate — precisely the "penalizes its absence" gap `029-DL` says does not
survive. This is a permanent property of the workflow, not a v1.5.0 condition.

Source refs: PR #422; Copilot review threads `PRRT_kwDORzpWpM6dfKPY` and
`PRRT_kwDORzpWpM6dfKPh`; reviewed HEAD `6ccd3254`.

### E738A7D1 — push-context coverage gap in the topology tests

`tests/_env_patch.py`'s A5 entry-guard fails closed when a key it is about to
touch already holds the empty string. GitHub Actions **ambiently sets
`GITHUB_HEAD_REF=""` in push-triggered runs**, so five pre-existing
`test_gates_topology.py` tests tripped the guard the first time a push-context
run executed the full test job.

**The immediate fix is already in.** Verified at `2661c1c8`:
`tests/test_gates_topology.py:929` defines `_clear_ambient_github_head_ref()`
and the affected tests call it before `patched_environ(...)`. Ship applied it as
a separate hotfix PR outside the `158-S` manifest because it was blocking
`150.009-T`'s "main is green" pre-tag assertion.

The residual is what this shipment addresses: **nothing prevents recurrence.**
The five tests were patched individually; there is no end-to-end assertion that a
push-context environment (ambient empty-string `GITHUB_HEAD_REF`) is handled, and
the next test written against `patched_environ(GITHUB_HEAD_REF=...)` without the
clear helper will reintroduce the identical failure. The retrospective question
posed by the entry — was a separate hotfix the right treatment? — is answered
here: **yes.** Ship could not leave `main` red before an irreversible PyPI
publish decision, the fix matched an existing precedent (`8c4c35ad`, identical
root cause), and it was correctly kept out of the `158-S` manifest under P-021
C1 as a different contract surface.

## Direction

`8E10B13B` asks a real question its own text flags as needing deliberation:
should the probe hard-fail unconditionally, or allow an explicit operator
override for deliberate re-runs, and should `skip-existing` be retained at all?

**Decision (recorded here, adversarially reviewed below): hard-fail
unconditionally; retain `skip-existing: true` as defence in depth; add no
override.**

* An override on an **unattended, tag-triggered** workflow has no one to operate
  it. It would be either a workflow-dispatch input (which changes the trigger
  surface) or a repository variable (which is a persistent, invisible
  disable-switch). Both are worse than re-tagging with a new version, which is
  the correct remedy for the situation the override would serve.
* Retaining `skip-existing` costs nothing once the probe fails closed and
  preserves the belt-and-braces property if the probe is ever bypassed.
* This keeps the change **inside one contract surface** — the probe's exit code —
  rather than expanding into trigger configuration.

## Hardening (P-006)

Triggered: CI workflow control flow on the irreversible publish path.

* **H1 (binding).** The probe must fail on *presence*, not on any inferred
  identity of the artifacts. Do not attempt to compare local build hashes against
  PyPI artifacts — that is a much larger design and is not authorized here.
* **H2 (binding).** Distinguish the three outcomes explicitly: 404 → proceed;
  version present → exit non-zero with a message naming the version and the
  remedy (bump and re-tag); any other error → re-raise. A network failure must
  **not** be silently treated as "not present". The current code already
  re-raises non-404 `HTTPError`; the new code must not regress that, and must
  also not swallow `URLError`.
* **H3.** No change to the pinned publish action SHA, the trigger, permissions,
  or any secret handling.
* **H4 (binding, from R4 below).** The regression test must not perform network
  I/O. It exercises the probe logic against injected responses.
* **H5 (binding) — TDD sequencing: the red test lands FIRST.** Task 2's detail
  already demands "**Red before green**: the 200 case must be demonstrated failing
  against the pre-fix workflow content", but cycle 0 ordered task 1 (the fix)
  ahead of task 2 (the test), which makes that impossible to honour. Corrected
  execution order, matching the queued task order:
  1. **Task 2 first** (`152.002-T`): extract the probe body into an importable
     helper and write the three cases. The 200-response case **MUST be observed
     failing** against the current fail-open `else:` branch. **Record the observed
     red result.**
  2. **Task 1 second** (`152.001-T`): replace the `else:` branch with the
     fail-closed exit. Task 2's 200 case turns green.
  3. **Task 3 last** (`152.003-T`): independent of both.

  The extraction in step 1 is behaviour-preserving, so the red result is a genuine
  observation of the defect and not an artefact of the refactor.
* **H6 (binding) — safety mode.** Every task enters `careful`. Task 1
  additionally enters `freeze-scope` bounded to the pre-publish probe step of
  `.github/workflows/release.yml` — it edits the irreversible publish path, where
  an over-broad edit is the risk, and **H3** already forbids touching the pinned
  action SHA, trigger, permissions, or secrets.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Make the release pre-publish PyPI probe fail closed on an already-published version | S | medium | `.github/workflows/release.yml` |
| 2 | Add a regression test asserting the probe fails closed, proceeds on 404, and re-raises transport errors | M | medium | `tests/` |
| 3 | Add an end-to-end push-context guard for ambient empty-string `GITHUB_HEAD_REF` | M | medium | `tests/test_gates_topology.py`, `tests/_env_patch.py` |

### Task 1 detail

Replace the `else:` branch at L102-L106 with an explicit non-zero exit naming the
version and the remedy. Keep the 404 path and the non-404 re-raise. Keep
`skip-existing: true` at L112 unchanged and add a one-line comment recording that
it is now defence in depth behind a fail-closed probe, so a future reader does
not remove it as redundant.

### Task 2 detail

Extract the probe body into an importable helper (or a test that executes the
embedded script with injected `urlopen`), then assert three cases: 404 →
proceeds; 200 → non-zero exit with the version in the message; `URLError` →
propagates. **Red before green**: the 200 case must be demonstrated failing
against the pre-fix workflow content.

### Task 3 detail

Two parts, both small:

1. A test that sets an ambient `GITHUB_HEAD_REF=""` in `os.environ` and drives
   the topology evaluation end to end, asserting the push-context outcome — the
   scenario that actually occurred in CI, rather than five individually patched
   call sites.
2. A guard that makes recurrence detectable: assert that every
   `patched_environ(...)` call in `test_gates_topology.py` naming
   `GITHUB_HEAD_REF` is preceded by `_clear_ambient_github_head_ref()`, or
   equivalently fold the clearing into a helper that the tests must use. The
   `029-DL` law applies — a convention survives only if a machine produces it or
   penalizes its absence.

## Non-goals

* No artifact-identity verification between the local build and PyPI (H1).
* No workflow-dispatch input, repository variable, or any override mechanism.
* No change to `tests/_env_patch.py`'s A4/A5 semantics. Those guards are correct;
  the ambient empty string is an environmental fact the *tests* must handle, and
  weakening A5 would reintroduce the Win32 empty-value-delete defect it exists to
  prevent.

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `actionlint` or equivalent
YAML/workflow parse on `release.yml`; markdownlint on changed docs.

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Security | **P0** | If the probe hard-fails, a **legitimate re-run of a failed post-publish step** (e.g. the release-record step failed after a successful upload) can no longer complete, and an operator under pressure will disable the gate wholesale. | **Resolved.** The failure message must name the supported remedy explicitly: re-run only the *post-publish* jobs, or bump and re-tag. The gate is on the *pre-publish* step only; steps after publish are unaffected by it, so a post-publish re-run is served by re-running those steps, not by re-entering the publish path. Recorded as an acceptance criterion on task 1. |
| 2 | Correctness | **P1** | The current code's `else:` branch is reached on **any** 2xx. A redirect or a cached mirror response could produce a false "already published" and hard-fail a legitimate release. | **Resolved.** H2 extended: the probe must assert the response is from `pypi.org` and that the decoded body identifies the requested version, not merely that the request succeeded. If the body cannot be parsed, treat it as a transport error and re-raise rather than as "present". |
| 3 | Correctness | **P1** | `skip-existing: true` retained behind a fail-closed probe is now unreachable in the intended path, so it will look like dead configuration and be deleted by a future cleanup. | **Resolved.** Task 1 requires an inline comment stating it is deliberate defence in depth. Task 2 does not assert on it, so removing it will not break a test — hence the comment is the only surviving signal and is mandatory. |
| 4 | Maintainability | P2 | A test that reaches PyPI over the network would be flaky and would make the suite non-hermetic. | **Resolved** as binding **H4**: injected responses only, no network. |
| 5 | Scope | P2 | Task 3 could grow into a general environment-hygiene framework for the whole suite. | Bounded: one end-to-end push-context test plus one guard scoped to `test_gates_topology.py`. Generalising to the whole suite is a P-021 capture, not this shipment. |
| 6 | Architecture | P2 | Extracting the embedded probe script into an importable module changes where release logic lives. | Accepted and preferred — an inline heredoc in YAML is untestable by construction, and the extraction is the minimum that makes task 2 possible. The workflow keeps calling it as a step; no behaviour moves. |
| 7 | Constitution | P3 | Editing a release workflow is high-consequence and might warrant operator approval. | The dark-mode record pre-authorizes merge approval for PRs produced from this scoped work; the change is non-destructive, adds a gate rather than removing one, and does not touch secrets, permissions, or the pinned action SHA (H3). |

**Verdict: PASS.** 1 P0 and 2 P1 raised; all three resolved before harvest. Zero
unresolved P0/P1. Two review-fix cycles of three.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass.`
Every selected persona was covered inline against the Persona Rubric Adapter and normalized to
the P0–P3 scale; no persona was skipped. Declared, not silent.

**Plan hardening (P-006): required — `yes`. Satisfied.** **H1**–**H6** are binding
and each is propagated into a task acceptance criterion.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Security | inline persona pass | 1 P0 (cycle 0) |
| Correctness | inline persona pass | 2 P1 (cycle 0), 1 P1 (cycle 1) |
| Maintainability | inline persona pass | 1 P2 (cycle 0) |
| Scope boundary | inline persona pass | 1 P2 (cycle 0) |
| Architecture | inline persona pass | 1 P2 (cycle 0) |
| Constitution | inline persona pass | 1 P3 (cycle 0), 1 P1 (cycle 1) |
| Template integrity | inline persona pass | — (no template surface) |
| Schema/CLI/docs coupling | inline persona pass | — (no finding) |

### Review-fix cycle 1 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 8 | Correctness | **P1** | Task 2's detail mandates red-before-green on the 200-response case, but the task order put the fix (task 1) ahead of the test (task 2), making the required red observation impossible. | **Resolved by H5.** Execution order is now 2 → 1 → 3, matching the queued order, with the red result on the 200 case explicitly recorded before task 1 begins. |
| 9 | Constitution | **P1** | No safety mode declared on a shipment that edits the irreversible release/publish path. | **Resolved by H6**: `careful` on all tasks, plus `freeze-scope` bounded to the pre-publish probe step for task 1. |

**Verdict: PASS.** Cycle 1: 2 P1 raised, both resolved. Cumulative: **zero
unresolved P0/P1**.

### Review-fix cycle 2 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 10 | Constitution | P2 | **H6** declared `careful` for every task and `freeze-scope` for task 1, but **none of the three executable tasks carried a safety-mode line in its own body**. A safety mode that exists only in a plan is not a safety mode the executing agent reads — and task 1 edits the irreversible publish path, which review flagged as high/production-impact. | **Resolved.** All three tasks now declare their safety mode inline: `152.001-T` carries `careful` + `freeze-scope` bounded to the pre-publish probe step of `.github/workflows/release.yml`, restating **H3**'s prohibitions (pinned action SHA, trigger, permissions, secrets, `skip-existing`) as an enforced bound; `152.002-T` and `152.003-T` carry `careful` with their behaviour-preserving and `tests/`-only bounds stated. **H6** is read as requiring propagation into each executable task, not merely declaration here. |

No other cycle-2 finding was raised against this shipment; its plan content is
unchanged apart from this record.

**Verdict: PASS.** Cycle 2: 1 P2 raised, resolved. Cumulative: **zero unresolved
P0/P1**. Three review-fix cycles of three consumed; the next review is the final
independent disposition cycle.
