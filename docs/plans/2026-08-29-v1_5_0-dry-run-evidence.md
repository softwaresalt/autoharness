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

**Evidence SHA**: `299b8228ec09808924ba897649a737fec4d8e61f`

1. **Full existing test suite**: `PYTHONPATH=src uv run --no-sync python -m
   unittest discover -s tests` -> `Ran 2022 tests ... OK (skipped=20)`.
   (2022 vs the 2018 reference in the last recorded closure is a modest
   increase, expected: this shipment added one new test file,
   `tests/test_circuit_breaker_checkpoint_yaml_safety.py`, with 4 tests,
   for `150.001-T`'s regression cases; no tests were skipped or lost.)
   `--no-sync` was required because native Windows `uv` cannot resolve/
   rebuild the editable install without reaching `files.pythonhosted.org`
   (see the environment note above); `--no-sync` runs against the
   already-installed venv, which is unaffected since only version strings
   and documentation/template content changed, not import-time behavior.
2. **Markdown quality gate** (per the `D1A46B8C` resolved policy, Option B):
   confirmed the `markdownlint` binary is present (`0.49.1`) -- absence
   would have been a HALT, not a skip. Ran `markdownlint "**/*.md"` over
   the full repository (respecting `.markdownlintignore`) -> zero output,
   exit 0, **zero violations**.
3. **verify-workspace / template / schema checks**:
   - Ran `autoharness verify-workspace --workspace .` -> `blockers: []`,
     `strict_schema_blockers: []`.
   - **INV-5 checksum drift audit**: `checksum_scan` reports 12 `user-modified`
     entries (of 72 tracked artifacts). All 12 are **pre-existing baseline
     drift, confirmed unrelated to this release**: `git diff` against every
     one of these 12 paths, across the entire `158-S` session (from the
     `chore/158-s-...` branch point through this dry run), is **empty** --
     none of them were touched by `150.001-T` through `150.006-T`. The only
     two checksum changes made during this release are the ones this
     shipment deliberately re-recorded (`150.001-T`'s
     `.github/instructions/circuit-breaker.instructions.md` and
     `150.002-T`'s `.github/skills/workspace-discovery/SKILL.md`), and both
     now report `unchanged`. The 12 pre-existing entries are:
     `.autoharness/workspace-profile.yaml`, `.autoharness/config.yaml`,
     `.autoharness/backlog-registry.yaml`, `start.sh`, `start.ps1`,
     `.github/agents/auto-mergeinstall.agent.md`,
     `.github/agents/auto-tune.agent.md`,
     `.github/instructions/github-pr-automation.instructions.md`,
     `.github/instructions/copilot-code-review.instructions.md`,
     `.github/instructions/capability-pack-enforcement.instructions.md`,
     `.github/prompts/feature-flow-dark.prompt.md`, and
     `.github/instructions/role-enforcement.instructions.md`. These are
     genuine pre-existing findings in the baseline workspace (most plausibly
     legitimate workspace-specific customization drift from the generic
     installed default, consistent with the several `.autoharness/*.yaml`
     and `start.*` entries already known to differ from a fresh-install
     baseline), not a STOP condition under INV-5, which scopes to drift
     *introduced by this release*.
   - Template validity: no unresolved `{{...}}` placeholders were reported;
     YAML frontmatter parses; cross-references resolve (`blockers: []`).
   - **INV-4**: confirmed via `git diff --stat schemas/` (this session) that
     no `schemas/**/<version>.schema.json` mirror was modified.

**Result: PASS.**

