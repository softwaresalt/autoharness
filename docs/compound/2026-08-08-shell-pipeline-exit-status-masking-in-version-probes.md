# Compound Learning: Shell Pipeline Exit-Status Masking in Version-Probe Detection Logic

**Origin**: Shipment `122-S` / Feature `114-F` (capability-pack runtime
detection + pre-merge-install checklist), PR #318, Copilot review round 1,
findings 1–2 of 3.

## The Pattern

A `bash`/`sh` detection routine probed a runtime executable's version with:

```sh
version="$("$exe" --version 2>/dev/null | head -n1)" || true
```

or equivalently:

```sh
"$exe" --version 2>/dev/null | head -n1 || true
```

Under `set -euo pipefail`, `pipefail` makes the *pipeline's* exit status the
last non-zero status among its stages — but `head -n1` almost always exits
`0` (it happily reads zero or more lines and closes), so a failing `$exe`
(nonzero exit, but *some* stdout/stderr emitted before failing) is masked:
the pipeline still reports success, `head` still captures whatever partial
output was produced, and the trailing `|| true` masks any residual signal
even if `pipefail` had caught it. The result: a broken or misbehaving
runtime that prints something before failing is misreported as `present`
with a plausible-looking (but bogus) version string.

## Why This Escaped Local Review

The ps1 sibling implementation (`Get-PackDetectionStatus`) was already
correct — it captures `$LASTEXITCODE` directly after a non-piped invocation
(`$output = & $exePath --version 2>$null; if ($LASTEXITCODE -eq 0 -and
$output) {...}`), so there was no analogous bug to notice by "check the
other script for the same issue" during a same-file review pass. The sh
script's own existing test suite exercised only the `present`/`absent`
happy-path branches with real or fully-missing executables, never a
fixture that both (a) prints output and (b) exits nonzero — the exact shape
that exposes pipeline masking.

## The Fix

Replace the piped pattern with a plain command-substitution assignment so
`if`/`if raw_output=...` tests the *command's own* exit status directly,
never a pipeline's:

```sh
if raw_output="$("$exe" --version 2>/dev/null)"; then
  version="$(printf '%s\n' "$raw_output" | head -n1 | xargs 2>/dev/null || true)"
fi
```

Here `head`/`xargs` only ever operate on already-captured, already-successful
output — they can no longer participate in exit-status determination.

## Generalizable Rule

**Any shell detection/probe logic that pipes a version/health-check
invocation through a text-processing filter (`head`, `grep`, `awk`, `sed`,
`tail`) must capture the *probed command's own* exit status before piping,
never rely on the pipeline's aggregate status** — even under `pipefail` —
because a downstream filter stage that itself succeeds (which text filters
almost always do, having *some* input or none) silently absorbs the
upstream failure signal. The only way to safely combine "check exit code"
and "extract first line of output" is to capture raw output first via plain
command substitution, gate on that command's own `if`/`$?` result, and only
then post-process the already-captured string.

## Cross-Reference

- **Regression coverage added**: `tests/test_deploy_harness_scripts.py`
  `DeployHarnessShChecklistPackDetectionTests` — a fixture executable that
  exits `1` but prints a stdout banner first, deterministically
  reproducing the exact shape that exposed this bug, run via WSL bash on
  the Windows dev host.
- **Sibling correctness confirmed, not just assumed**: the ps1 script
  needed no fix; `DeployHarnessPs1ChecklistPackDetectionTests` proves this
  with the same fixture shape rather than leaving it unverified by
  omission.
- Related shipment: `docs/decisions/2026-08-07-capability-pack-runtime-installer-deliberation.md`
  (Option C — bounded detection scope; this shipment's scope boundary).
