# 088-F — Copilot CLI Output-Compression Experiment (THROWAWAY)

**Status: throwaway, flag-gated, DISABLED BY DEFAULT.** This directory is a
bounded experiment/benchmark, not a production capability pack. Nothing in
`src/autoharness/` imports this package, and no generated harness artifact
depends on it.

See:

* Plan: `docs/plans/2026-07-15-copilot-cli-output-compression-experiment-plan.md`
* Spike: `docs/spikes/2026-07-15-copilot-cli-output-compression-experiment.md`
* Reused CCR analysis: `docs/spikes/2026-07-13-brainspace-compression-feasibility.md`
* Findings + decision memo: `docs/decisions/2026-07-25-copilot-cli-output-compression-experiment-findings.md`

## What this is

A `postToolUse` compression hook prototype for GitHub Copilot CLI plus a
byte-equivalent retrieval tool, a containment-safe local store, an AUC
token-savings measurement harness, a benchmark corpus runner, and decline-case
safety tests — built to prove or disprove honest token savings without hiding
required evidence.

## MCP retrieval tool (not registered in the root `.mcp.json` by default)

`mcp_server.py` implements a minimal, dependency-free stdio JSON-RPC server
exposing one tool, `output_retrieve` (full or paginated byte-equivalent
retrieval). `mcp.json.example` shows how to register it. It is intentionally
**not** merged into the repo-root `.mcp.json` — that file is the canonical,
always-loaded shared MCP surface for every contributor and agent session in
this repo, and merging it there would make the retrieval server part of the
default environment, contradicting the plan's "disabled by default, not a
production capability-pack install" condition even though the tool itself is
inert (returns "handle not found" errors) whenever the store is empty. To
exercise retrieval locally, merge `mcp.json.example` into a local/untracked
MCP config, or invoke `brainspace/retrieval.py` functions directly (see
`tests/test_retrieval_byte_equivalent.py` for the direct-store recovery
path used by the benchmark).

## Flag gate

The experiment is disabled unless `BRAINSPACE_EXPERIMENT_ENABLED=1` is set in
the environment (see `brainspace/config.py`). With the flag unset (the
default), the hook entry point always returns `{}` (pass-through, no-op) and
no store is created.

**Not wired into `.github/hooks/` by default.** `hooks.json.example` in this
directory is a template, not a live hook registration — copying it into
`.github/hooks/` would make Copilot CLI invoke `hook_cli.py` on every
matching tool call for every contributor (the script itself still no-ops
unless the flag is set, but the plan requires this prototype to stay
throwaway and out of the default install path). To exercise the hook
end-to-end locally:

```powershell
Copy-Item experiments/088-compression-experiment/hooks.json.example .github/hooks/088-compression-experiment.json
$env:BRAINSPACE_EXPERIMENT_ENABLED = '1'
copilot   # interact normally; remove the copied file + unset the flag when done
```

## How to remove this experiment entirely

1. Delete this directory: `experiments/088-compression-experiment/`.
2. Remove the `brainspace-ccr` entry from `.mcp.json` (if present).
3. Remove any copied `.github/hooks/088-compression-experiment.json` (only
   present if a developer opted in locally — never committed by default).
4. Remove the `.autoharness/cache/brainspace/` gitignore entries from
   `.gitignore`.
5. Delete any runtime store data at `.autoharness/cache/brainspace/`.

Nothing else in the repository references this package.

## Running the experiment's tests

```powershell
python -m pytest experiments/088-compression-experiment/tests -q
```

## Running the benchmark corpus

```powershell
python experiments/088-compression-experiment/brainspace/benchmark_cli.py
```

`benchmark_cli.py` self-manages the disabled-by-default flag for the
duration of its own process only (never persisted, never leaked into the
ambient environment) -- no manual `BRAINSPACE_EXPERIMENT_ENABLED` step is
needed.

Emits a JSON + Markdown report under
`experiments/088-compression-experiment/reports/`.

## Purging the store

```powershell
python experiments/088-compression-experiment/brainspace/purge_cli.py --mode expired
```

Deletes TTL-expired rows (the default, safe mode). Pass `--mode all` to
clear the entire store, including live rows.
