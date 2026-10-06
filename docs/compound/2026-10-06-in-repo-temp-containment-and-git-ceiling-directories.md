---
title: "In-repo TEMP containment for test runs and git hooks: pin GIT_CEILING_DIRECTORIES to the temp dir itself"
problem_type: workspace-containment
category: test-environment
root_cause: "The pre-push hook and the canonical unittest command inherit the caller's TEMP/TMP/TMPDIR, so a plain git push wrote transient temp dirs outside the worktree (Principle IV). Rerouting TEMP into the repo fixes containment but places every temp dir inside the repository's git tree, so tests that assert behavior 'outside a git repo' find the enclosing repository unless GIT_CEILING_DIRECTORIES stops discovery at the temp dir itself."
tags: [principle-iv, workspace-containment, temp, git-hooks, pre-push, git-ceiling-directories, unittest, windows]
shipment: 194-S
date: 2026-10-06
source: docs/compound/2026-10-06-in-repo-temp-containment-and-git-ceiling-directories.md
doc_type: learning
---

## Problem

During 194-S, the repository pre-push hook ran the full unittest suite with the
default Windows `%TEMP%`. The suite cleaned up after itself, but the transient
directories were still created outside the worktree. That is a Principle IV
(workspace containment) stop condition, and it halted the dark-mode run before
PR creation.

Environment variables do not persist across agent shell invocations, so the
reroute has to be set in the same invocation as every command that can run
tests, git hooks or `git push`.

## Solution

Set all four variables in the same PowerShell invocation as the command, and
create the directory first. Python's `tempfile` silently skips a `TEMP`/`TMP`/
`TMPDIR` that does not exist and falls back to the system temp directory, which
would repeat the outside-worktree writes this workaround exists to prevent (for
example in a fresh checkout, or after closure deletes the scratch directory):

```powershell
# Run from the repository root of the active checkout; never hard-code a checkout path.
$root = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0 -or -not $root) { throw 'not inside a git checkout' }
$r = Join-Path $root '.proof-scratch\<shipment>\tmp'  # git-ignored
New-Item -ItemType Directory -Force -Path $r -ErrorAction Stop | Out-Null
if (-not (Test-Path -LiteralPath $r -PathType Container)) { throw "temp dir missing: $r" }
$env:TEMP = $r; $env:TMP = $r; $env:TMPDIR = $r
$env:GIT_CEILING_DIRECTORIES = $r
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests   # or: git push origin HEAD
```

`GIT_CEILING_DIRECTORIES` must be the temp directory itself. Setting it to the
repository's parent (for example `C:\Source\GitHub`) is not enough: git still
discovers the repository root, which sits below that ceiling. Three tests then
fail because they expect a temp directory that is not inside any git
repository:

* `test_benchmark_controls.RunBenchmarkTests.test_manifest_resolves_none_commit_sha_outside_git_repo`
* `test_eval_cli.EvalReviewCliTests.test_review_degrades_cleanly_outside_git`
* `test_eval_cli.EvalRunCliTests.test_run_with_review_folds_quality`

With the ceiling at the temp directory, the full suite passed (3352 tests,
`OK (skipped=57)`), both locally and through the pre-push hook.

## Related notes

* `uv run` needs network access to resolve the build backend. When it is
  unavailable, run the repository CLI from source with
  `python -c "import sys; from autoharness.cli import main; sys.argv=['autoharness', ...]; sys.exit(main())"`
  and `PYTHONPATH=src`. `python -m autoharness` does not work because the
  package has no `__main__`.
* `git checkout` and `git pull` run no hook in this repository (`core.hooksPath`
  is `.githooks`, which installs only `pre-push`). Only pushes need the reroute
  for hook containment.
* The durable fix (have the hook reroute temp and pin the ceiling itself, or make
  the three tests set their own ceiling) is stash `B99B661D`.
