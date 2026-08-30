---
title: "GitHub Actions push-triggered CI sets GITHUB_HEAD_REF to empty string, not absent — a test-suite env-patch guard that only clears ambient values can silently miss push-context coverage"
description: "10 tests in tests/test_gates_topology.py::BranchOwnershipTests were only ever exercised in pull_request-triggered CI or locally, never in push-triggered CI, because prior post-merge runs to main had the test job path-filtered to skipped. The first push-context run to actually execute the test job (158-S's PR #423 merge) failed all 10 with patched_environ()'s A5 entry-guard rejecting GITHUB_HEAD_REF because its ambient value was already the empty string."
problem_type: "test-coverage-gap"
category: "ci-environment-fidelity"
component: "test_gates_topology / _env_patch"
root_cause: "GitHub Actions sets GITHUB_HEAD_REF to the empty string (present, not absent/unset) on push-triggered workflow runs, as opposed to pull_request-triggered runs (a real branch name) or a local shell (typically unset entirely). tests/_env_patch.py's patched_environ() A5 entry-guard (144.002-T, BINDING) deliberately fails closed with a RuntimeError when a key it is asked to manage already holds an empty-string ambient value, to avoid the Windows SetEnvironmentVariableW empty-value-delete restore bug. Ten tests called patched_environ(GITHUB_HEAD_REF=...) without first clearing the ambient value, so they worked in every context this repo's CI had actually exercised (pull_request events, and local shells where the variable is simply unset) but broke the first time a push-triggered run actually executed the full test job."
resolution_type: "fix"
severity: "medium"
tags:
  - "ci"
  - "github-actions"
  - "test-environment"
  - "push-vs-pull-request-event"
  - "env-patch"
citations:
  - "Shipment 158-S / feature 150-F (v1.5.0 release preparation)"
  - "PR #423 (merge exposing the gap), PR #425 (fix)"
  - "commit 8c4c35ad (identical prior fix for a single test, same root cause)"
  - "tests/_env_patch.py (A5 entry-guard, 144.002-T BINDING)"
  - "tests/test_gates_topology.py::BranchOwnershipTests"
source: docs/compound/2026-08-30-github-actions-push-event-github-head-ref-empty-string-not-absent.md
doc_type: learning
---

# GitHub Actions push events set `GITHUB_HEAD_REF` to empty string, not absent

## The pitfall

A test that manages a CI-platform environment variable via a restore-safe
helper (here, `patched_environ()`) must account for **every** ambient value
the variable can legitimately hold across **every** trigger context the
workflow actually runs under — not just the contexts the test author
happened to exercise locally or that CI happened to run so far.

`GITHUB_HEAD_REF` has three distinct ambient states depending on context:

| Context | Ambient `GITHUB_HEAD_REF` |
|---|---|
| `pull_request`-triggered CI | a real branch name (non-empty) |
| `push`-triggered CI | **the empty string** (present, not absent) |
| Local shell | typically unset entirely (`os.environ.get(...) is None`) |

Ten tests in `tests/test_gates_topology.py::BranchOwnershipTests` called
`patched_environ(GITHUB_HEAD_REF=...)` (setting a value, or `None` to
ensure absence) without first clearing whatever ambient value already
existed. This worked everywhere the suite had actually been exercised —
locally (unset) and in `pull_request`-triggered CI (non-empty, and the
override simply replaced it) — but the moment a `push`-triggered CI run
finally executed the full test job (this repository's prior post-merge
runs had the `test` job path-filtered to `skipped`, so this had never
actually happened), all ten failed with:

```text
RuntimeError: patched_environ() cannot safely touch 'GITHUB_HEAD_REF':
its current value is the empty string, and restoring an empty-string
value via os.environ[key] = '' would itself trigger Windows'
SetEnvironmentVariableW empty-value-delete behavior, reintroducing the
defect through this helper's own restore path.
```

This is `tests/_env_patch.py`'s `patched_environ()` A5 entry-guard
(144.002-T, BINDING) working exactly as designed — it is correctly
refusing to unsafely restore an empty-string value. The bug was in the
**tests**, not the guard: they never cleared the ambient value before
asking the guard to manage it.

## Why it stayed hidden

CI coverage is not automatically representative of every trigger context a
workflow supports. A workflow's `test` job can be conditionally skipped
(e.g. via a path-filter `detect code changes` gate) on some trigger types
and not others, so "CI has been green for months" does not mean "every
code path this test exercises has actually run under every event type the
workflow listens for." A latent gap can sit undetected until the first
run that happens to hit the untested combination — here, a push-triggered
run whose diff was large enough to trip the path filter.

## The fix

Clear the ambient value **before** handing the key to `patched_environ()`,
not instead of using it — the restore-safe helper is still the correct
mechanism for the test's own managed override; the fix is ensuring its
entry-time precondition (no pre-existing empty-string ambient value) holds
regardless of which CI event triggered the run:

```python
import os as _os

def _clear_ambient_github_head_ref() -> None:
    _os.environ.pop('GITHUB_HEAD_REF', None)

# ... before each patched_environ(GITHUB_HEAD_REF=...) call:
_clear_ambient_github_head_ref()
with patched_environ(GITHUB_HEAD_REF=...):
    ...
```

This mirrors an identical prior fix (commit `8c4c35ad`) applied to a
single sibling test for the same root cause — the convention already
existed in this file; it simply hadn't been applied to these ten tests.

## Generalizable takeaway

When a test patches a CI-platform environment variable, enumerate **every**
ambient state that variable can hold across every event type the workflow
actually listens for (not just the ones locally reproducible or previously
observed in CI), and clear/normalize the ambient value before handing it to
a restore-safe patching helper. A "the tests pass, CI is green" signal is
only as strong as the trigger-context diversity CI has actually exercised —
verify with `git log` / workflow run history whether a given job has ever
actually executed under the trigger type you're relying on it to validate.
