---
title: "v1.5.0 release dry-run evidence (150.006-T / 150.007-T)"
date: 2026-08-29
doc_type: plan
agent: "Ship"
---

# v1.5.0 Release Dry-Run Evidence

Tracks the evidence SHA each release dry run was executed against, per
`150.006-T` / `150.007-T` acceptance criteria. `150.009-T` must confirm this
evidence SHA equals the actual merge commit SHA before tagging, or re-run
both dry runs against the merge commit on any mismatch.

**Environment note**: this local Windows sandbox's native networking cannot
complete a TLS handshake with `files.pythonhosted.org` (Fastly CDN) --
confirmed via `curl.exe -4`/`-6` (`schannel: ... SEC_E_ILLEGAL_MESSAGE`) and
`Invoke-WebRequest` (`HandshakeFailure`) against that host specifically,
while `pypi.org`'s JSON API (a different host) is reachable natively. WSL
(Ubuntu 26.04)'s network path on the same machine reaches
`files.pythonhosted.org` without issue. All `uv build` / `uvx twine check` /
isolated-install steps below were therefore executed for real via a WSL
bash invocation against the same working tree (`/mnt/c/Source/GitHub/autoharness`),
not simulated or weakened. This is a local-sandbox network-path quirk only;
the GitHub Actions `release.yml` runner has its own unrestricted network
access and is unaffected.

## Dry Run A (150.006-T): build and package integrity

**Evidence SHA**: `484e5b06eb830ce49dd00fd248fffd13a24109ac`

1. Cleaned `dist/` of stale `1.4.11` artifacts before building.
2. `uv build` (via WSL) -> exactly two artifacts, both carrying `1.5.0`:
   - `dist/autoharness-1.5.0.tar.gz`
   - `dist/autoharness-1.5.0-py3-none-any.whl`
3. `uvx twine check dist/*` (via WSL) -> both `PASSED`.
4. Installed the explicitly named wheel
   (`dist/autoharness-1.5.0-py3-none-any.whl`, never a glob) into an
   isolated `uv venv` (Python 3.12, `/tmp/autoharness-isolated-venv`, not the
   source tree).
5. `autoharness version` -> exactly `1.5.0`, exit 0.
6. Installed distribution metadata via `importlib.metadata.version("autoharness")`
   -> `1.5.0` (confirms the real metadata path, not the source literal
   fallback).
7. `autoharness home` -> resolved to
   `.../site-packages/autoharness/data`, exit 0.
8. All ten `force-include` destinations from `pyproject.toml`
   (`tool.hatch.build.targets.wheel.force-include`), derived at run time
   (not hard-coded), verified present, non-empty, and readable from the
   isolated install:
   `templates`, `schemas`, `.github/agents`, `.github/skills`,
   `.github/instructions`, `.github/prompts`,
   `.github/copilot-instructions.md`, `.github/copilot-review-instructions.md`,
   `docs`, `AGENTS.md` -> all `OK`.

**Result: PASS.**

## Dry Run B (150.007-T): quality gates

See update appended by `150.007-T`.
