---
title: "Shell Pipeline Failure Discarded by Trailing `|| true` in Version-Probe Detection Logic"
description: "A version-probe pipeline's correctly-propagated pipefail failure is discarded by a trailing || true while partial stdout is still captured, causing a broken runtime to be misreported as present"
problem_type: "logic_error"
category: "shell-scripting"
component: "scripts/deploy-harness.sh, templates/scripts/deploy-harness.sh.tmpl"
root_cause: "A trailing `|| true` on a piped version-probe command substitution discards the pipeline's own correctly pipefail-propagated nonzero exit status, while the piped filter stage (head) still forwards whatever partial stdout the failing command printed, so downstream logic that infers success from non-empty output is misled"
resolution_type: "code_fix"
severity: "medium"
message: "pack detected present despite exiting nonzero / partial version string from a failing runtime"
citations:
  - "scripts/deploy-harness.sh"
  - "templates/scripts/deploy-harness.sh.tmpl"
  - "tests/test_deploy_harness_scripts.py"
tags:
  - "shell-scripting"
  - "pipefail"
  - "exit-status"
  - "detection-logic"
  - "code-review-finding"
source: docs/compound/2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md
doc_type: learning
---

# Compound Learning: Shell Pipeline Failure Discarded by Trailing `|| true` in Version-Probe Detection Logic

**Origin**: Shipment `122-S` / Feature `114-F` (capability-pack runtime
detection + pre-merge-install checklist), PR #318, Copilot review round 1,
findings 1–2 of 3. **Corrected** in PR #319 (post-merge closure) round 1
after a Copilot finding identified that the original write-up of this
document mischaracterized the `pipefail` mechanism itself (see "Correction"
below) — the code fix was always correct; only this document's explanation
was wrong.

## The Pattern

A `bash`/`sh` detection routine probed a runtime executable's version with:

```sh
version="$("$exe" --version 2>/dev/null | head -n1)" || true
```

or equivalently:

```sh
"$exe" --version 2>/dev/null | head -n1 || true
```

**Corrected mechanism** (per PR #319 Copilot review): under
`set -euo pipefail`, the pipeline's exit status is *correctly*
pipefail-propagated — if `$exe --version` exits nonzero and `head -n1`
exits `0`, the pipeline's own exit status is still the nonzero status from
`$exe`, exactly as `pipefail` is designed to do. The actual bug is that the
trailing `|| true` explicitly **discards** that correctly-propagated
nonzero status, forcing the assignment to "succeed" regardless. Meanwhile,
`head -n1` still receives and forwards whatever partial stdout `$exe`
printed before failing, so the `version` variable is still populated with
that partial/bogus output via the command substitution — independent of
the (discarded) pipeline exit status. The result is the same symptom
(broken runtime misreported as `present`), but the mechanism is "`|| true`
throws away a correct pipefail failure signal while a text filter forwards
partial output regardless of the pipeline's exit status" — not "pipefail
itself fails to detect the failure."

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
`tail`) and then discards the pipeline's exit status (e.g. a trailing
`|| true`) loses the *probed command's own* failure signal, even though
`pipefail` correctly propagated it in the first place** — because the
downstream filter stage still forwards whatever partial input it received
regardless of the pipeline's ultimate exit status. The only way to safely
combine "check exit code" and "extract first line of output" is to capture
raw output first via plain command substitution (no trailing `|| true` on
the substitution itself), gate on that command's own `if`/`$?` result, and
only then post-process the already-captured, already-successful string.

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
