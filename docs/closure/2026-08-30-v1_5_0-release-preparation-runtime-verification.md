---
title: "v1.5.0 release preparation — runtime verification (150.006-T/158-S)"
date: 2026-08-30
doc_type: closure
agent: "Ship"
source: "150-F / 158-S"
---

# Runtime Verification — v1.5.0 Release Preparation

Shipment `158-S` / feature `150-F`. Runtime surface: `cli` (per
`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`).

## Validator Contract

- `validator_manifest.surfaces[0].surface`: `cli`
- `adapter_hint`: `command`
- Probe `cli-help`: `uv run autoharness --help` (required, evidence types
  `stdout` + `exit-code`)
- `validation_expectations.minimum_verdict`: `PASS`
- `validation_expectations.preserve_invariants`: "The autoharness CLI starts
  without import, packaging, or option-parsing failures"
- `validation_expectations.release_blockers`: "The CLI help smoke check fails"

## Adapter Selection

Command adapter (`cli`), matching the manifest's `adapter_hint`. No downgrade
was needed — the CLI is directly invokable in this environment.

## Environment Prechecks

- Native Windows `uv run` cannot resolve/rebuild the editable install because
  it cannot reach `files.pythonhosted.org` for build-dependency metadata (see
  `docs/plans/2026-08-29-v1_5_0-dry-run-evidence.md` for the full TLS-handshake
  diagnosis). `uv run --no-sync` runs against the already-synced venv and is
  unaffected, since this probe does not require the venv to be rebuilt.
- The packaged wheel itself (built and installed via WSL, where network access
  works) was independently probed in an isolated environment during
  `150.006-T`'s dry run (see Additional Evidence below) — this is a second,
  stronger form of the same CLI-surface check, exercising the actual
  force-included `autoharness/data/` bundle rather than the source tree.

## Execution

**Probe 1 — source-tree CLI smoke (this task, `cli-help`)**:

```text
$ uv run --no-sync autoharness --help
autoharness — agent harness framework

Usage:
  autoharness home              Print the autoharness installation path
  autoharness version           Print the installed version
  ...
exit code: 0
```

- Expected: "Command exits successfully and prints CLI help text."
- Observed: exit 0, full help text printed (command list, install
  instructions). Matches expected signal exactly.

**Probe 2 — isolated packaged-wheel CLI smoke (from `150.006-T`, reused as
stronger evidence for the same surface)**:

```text
$ uv tool run / uv pip install (isolated venv) dist/autoharness-1.5.0-py3-none-any.whl
$ autoharness version
1.5.0
exit code: 0
$ autoharness home
/.../site-packages/autoharness/data
exit code: 0
```

- Confirms the CLI entrypoint, version resolution (`importlib.metadata`), and
  bundled-data path resolution all work correctly from an installed wheel, not
  just the source tree — closer to how an end operator will actually invoke
  the tool after `pip install autoharness==1.5.0`.

## Verification Verdict

**PASS.**

Both the source-tree CLI-help probe (required by the validator manifest) and
the stronger isolated packaged-wheel probe (version + home + bundled-data,
from `150.006-T`) succeeded with exact expected output and zero exit codes.
The declared invariant — "the autoharness CLI starts without import,
packaging, or option-parsing failures" — holds.

## Follow-up Recommendations

None required for merge. The unattended `release.yml` publish workflow will
perform an additional, independent packaged-from-PyPI smoke test
(`uv tool run --isolated --no-config --from "autoharness==1.5.0" autoharness version`)
as part of `150.010-T`'s publish-monitoring scope — this is a distinct,
later verification of the actual published artifact and is tracked
separately, not a gap in this pre-merge verification.

## Releasability Handoff

Per `runtime_validation.releasability` in the workspace profile
(`required: false`, `status_when_satisfied: "READY"`, `required_evidence: []`):
no additional monitoring/rollback/owner/validation-window evidence is required
beyond what `operational-closure` records below. This is a CLI packaging
release, not a hosted service deployment — release.yml's own publish
monitoring (`150.010-T`) is the operative "deployment" verification.
