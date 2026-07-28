---
problem_type: test-gate-selection
category: validation
root_cause: repository-root-pytest-discovers-vendored-reference-tests-and-fails-unrelated-collection
tags: [tests, unittest, pytest, references, validation, ci, telemetry]
shipment: 097-S
feature: 092-F
pr: 241
---

# 097-S: The Canonical Repository Test Gate Is `unittest`, Not Root `pytest`

The source-validation gate for autoharness is the standard-library unittest
suite:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests
```

CI's real source gate is the same test surface. A repository-root
`python -m pytest -q` invocation is not canonical for this workspace.

## Problem

`pyproject.toml` configures `pythonpath = ["src"]` for pytest but does not set
`testpaths` or exclude vendored `references/*` content. Running pytest from the
repository root can therefore wander into vendored reference repositories and
fail during collection with unrelated import-file-mismatch errors.

That failure mode is not evidence that autoharness source changes are broken.

## Durable Rule

- For full-suite local evidence, run
  `PYTHONPATH=src python -m unittest discover -s tests`.
- Treat root `pytest -q` collection failures in `references/*` as outside the
  canonical gate unless the repository intentionally configures pytest testpaths
  later.
- PR readiness blocks for source changes should record the unittest command and
  result, for example: `Ran 721 tests ... OK`.

## Why It Matters

Using the wrong gate can falsely block a shipment after its real CI-equivalent
suite is green. Ship agents should validate against the repository's declared
gate rather than escalating unrelated vendored-reference collection failures.
