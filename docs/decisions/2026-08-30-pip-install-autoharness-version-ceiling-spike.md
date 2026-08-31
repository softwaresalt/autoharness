---
title: "Why does `pip install autoharness` appear not to update past an old version, and what command or release fix yields the latest intended version?"
source: "docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md"
doc_type: decision
description: "Read-only diagnosis of an autoharness upgrade stall on this workstation, establishing that the installed version is 1.4.11 (not 1.5.0), that 1.5.0 is the latest intended and is correctly published to PyPI and GitHub Releases, and that three independent client-side causes — a lagging non-PyPI mirror index, a non-upgrading plain install command, and TLS interception of files.pythonhosted.org — jointly prevent the upgrade. No repository or release fix is required."
docline:
  type: spike
  date: 2026-08-30
  time_box: "1h"
  conclusion: "proceed"
  confidence: "high"
  linked_parent_work_item: null
  promoted_to: ["none"]
  tags:
    - "packaging"
    - "pypi"
    - "pip"
    - "release-distribution"
    - "environment-diagnosis"
---

## Goal

**Why does `pip install autoharness` appear not to advance the installed version,
and what exact command or repository/release change is needed to obtain the latest
intended version?**

The investigation was scoped read-only: no source, template, schema, packaging,
workflow, backlog, git, or GitHub state was modified. The sole write is this
findings artifact.

## Premise Correction (material to the answer)

The question was posed as an inability to update *beyond 1.5.0*. The measured state
does not support that framing, and the correction changes the remediation:

- The installed version on this workstation is **1.4.11**, not 1.5.0.
- **1.5.0 is the latest intended version.** There is nothing beyond it to obtain —
  repository `main`, the `v1.5.0` tag, `plugin.json`, and PyPI all agree on 1.5.0.

So the real symptom is a version **ceiling at 1.4.11**, and the goal is to reach
1.5.0 — not to find a phantom post-1.5.0 release.

## Observed State

### Installed (client)

| Interpreter | Path | autoharness version |
|---|---|---|
| Python 3.14.3 (PATH default) | `C:\Python\Python314\Lib\site-packages` | **1.4.11** |
| Python 3.12.10 | `C:\Python\Python312\Lib\site-packages` | **1.4.11** |

`autoharness version` (PATH-resolved, `C:\Python\Python314\Scripts\autoharness.exe`)
reports `1.4.11`, consistent with package metadata. Two shim copies exist
(Python314 and Python312 `Scripts\`), but both back onto 1.4.11, so shim shadowing
is **not** a contributing cause here.

### Intended / published (repository and index)

| Source | Version | Evidence |
|---|---|---|
| `pyproject.toml` `[project].version` | 1.5.0 | working tree at `2661c1c8`, clean |
| `plugin.json` `.version` | 1.5.0 | working tree |
| Newest git tag (`--sort=-v:refname`) | `v1.5.0` | ahead of `v1.4.11` |
| GitHub Release | `v1.5.0`, marked `Latest`, not draft/prerelease | published `2026-08-30T20:31:29Z` |
| PyPI JSON API `info.version` | 1.5.0 | published `2026-08-30T20:30:22Z` (wheel), `20:30:24Z` (sdist) |
| PyPI Simple API `versions` | `..., 1.4.11, 1.5.0` | 1.5.0 present, `yanked=false`, `requires-python=">=3.10"` |

Both 1.5.0 distributions (`autoharness-1.5.0-py3-none-any.whl`,
`autoharness-1.5.0.tar.gz`) are present and unyanked on PyPI, and the GitHub Release
carries the same two files plus `.publish.attestation` sidecars.

`requires-python = ">=3.10"` is satisfied by both local interpreters, so
Python-version exclusion is **not** a cause.

### Release pipeline health

`gh run list --workflow release.yml` shows the v1.5.0 publish was attempted twice:

| Created | Title | Conclusion |
|---|---|---|
| 2026-08-30T19:07:10Z | `fix: clear ambient GITHUB_HEAD_REF before patched_environ() in topolo…` | **failure** |
| 2026-08-30T20:29:58Z | `fix: pin core-metadata-version to 2.4 to fix v1.5.0 PyPI publish fail…` | **success** |

The earlier failure is the one referenced by the recent closure commits on `main`
and analysed in `docs/compound/2026-08-30-unpinned-hatchling-metadata-version-vs-pinned-publish-action.md`
(hatchling 1.32.0 defaulting to Metadata-Version 2.5 versus a pinned
`gh-action-pypi-publish` bundling twine < 7.0.0). That failure was **already
remediated** by the `core-metadata-version = "2.4"` pin now present in
`pyproject.toml`, and the retry succeeded.

**Conclusion on the release side: the publish is healthy and complete. No
repository, packaging, or release fix is required.**

## Root Cause

The stall is entirely **client-side**, and is the product of three independent
causes that must all be addressed. Any one of them alone is sufficient to produce
the reported symptom.

### Cause 1 (primary) — pip resolves against a non-PyPI mirror that lacks 1.5.0

`pip config list` shows exactly one relevant key set: **`global.index-url`**. Its
value was deliberately not printed. Safe structural classification only:

| Indicator | Value |
|---|---|
| Host is `pypi.org` | **False** |
| Scheme is https | True |
| Embeds userinfo/credentials | False |
| Path ends in `/simple` | True |

Resolution differs by index, with the local HTTP cache bypassed in both runs:

```text
# configured index, --no-cache-dir
autoharness (1.4.11)
Available versions: 1.4.11, 1.4.10, ... 1.4.2
  LATEST: 1.4.11

# explicit PyPI, --no-cache-dir
autoharness (1.5.0)
Available versions: 1.5.0, 1.4.11, ... 1.4.2
  LATEST: 1.5.0
```

Because both runs used `--no-cache-dir` and still diverged, this is **not** a stale
local pip HTTP cache (1304 MB / 1839 files present, but not implicated). The
configured upstream mirror genuinely does not yet carry 1.5.0 — a mirror-sync lag,
expected given 1.5.0 was published only hours before this investigation.

### Cause 2 (contributing) — plain `pip install` is a no-op when already satisfied

```text
python -m pip install --dry-run --no-deps autoharness
  Requirement already satisfied: autoharness in C:\Python\Python314\Lib\site-packages (1.4.11)
```

`pip install <pkg>` without `--upgrade` only enforces *presence*, not *recency*. Even
once the mirror carries 1.5.0, the command as issued will continue to report
"Requirement already satisfied" and change nothing. This is standard pip semantics,
not a defect.

### Cause 3 (blocks the obvious workaround) — TLS interception of `files.pythonhosted.org`

Redirecting to PyPI resolves metadata but cannot download:

```text
python -m pip install --dry-run --no-deps --upgrade --index-url https://pypi.org/simple autoharness
  Collecting autoharness
  ... SSLError(1, '[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure')
  error: ssl-verification-failed
  Failed to establish a secure connection to files.pythonhosted.org
```

Endpoint reachability probe:

| Endpoint | Result |
|---|---|
| `https://pypi.org/simple/autoharness/` | REACHABLE (200) |
| `https://files.pythonhosted.org/` | **TLS-BLOCKED** |
| GitHub release wheel URL (`v1.5.0`) | REACHABLE (200) |
| `codeload.github.com` tag tarball | REACHABLE (200) |

A TLS-inspecting proxy terminates `files.pythonhosted.org` while permitting
`pypi.org` and `github.com`. This is almost certainly *why* the internal mirror was
configured in the first place, and it means `--index-url https://pypi.org/simple`
alone is **not** a working remediation on this host. Note `--trusted-host` will not
help: the failure is a handshake failure, not certificate verification of a
successfully negotiated session.

### Ruled out

- Package-name collision — the PyPI project `autoharness` carries the same summary,
  the `softwaresalt/autoharness` Repository URL, and the `autoharness` console
  script. Distribution name is correct; no alternate name is needed.
- Yanked/prerelease 1.5.0 — `yanked=false`, `isPrerelease=false`.
- `requires-python` exclusion — `>=3.10` vs. local 3.14.3 / 3.12.10.
- Stale local pip cache — disproved via `--no-cache-dir`.
- Unpublished source — PyPI and GitHub Release artifacts are byte-identical to each
  other (see below).

### Artifact-identity verification

The GitHub Release assets and the PyPI distributions are the **same bytes**, so the
GitHub Release is a safe substitute source:

| Artifact | sha256 | PyPI == GitHub |
|---|---|---|
| `autoharness-1.5.0-py3-none-any.whl` | `720049ceb1731b01168cd455c2d36babe7743de890b0ce05a840353a52424282` | **True** |
| `autoharness-1.5.0.tar.gz` | `f0c89267cf6d48bf0340758bd664b685f16f48f9c7de1b14d0f5e5db029e274a` | **True** |

## Remediation

**Recommended (works today, digest-verified, respects the TLS constraint):** install
the 1.5.0 wheel straight from the GitHub Release, which is reachable and byte-identical
to the PyPI artifact.

```powershell
python -m pip install --upgrade `
  https://github.com/softwaresalt/autoharness/releases/download/v1.5.0/autoharness-1.5.0-py3-none-any.whl
```

If the two `jsonschema` / `PyYAML` dependencies also need resolving and the mirror can
serve them (it can — only `autoharness` itself is stale), the command above will pull
them from the configured mirror normally.

**Preferred steady state (once the mirror catches up):** the durable fix is the
`--upgrade` flag, which was missing from the original command.

```powershell
python -m pip install --upgrade autoharness
python -m pip index versions autoharness   # confirm LATEST advances to 1.5.0
```

**Verification after either path:**

```powershell
python -m pip show autoharness   # expect Version: 1.5.0
autoharness version              # expect 1.5.0
```

Apply to **both** interpreters if both are used, since each holds its own 1.4.11:

```powershell
C:\Python\Python314\python.exe -m pip install --upgrade <wheel-url-or-autoharness>
C:\Python\Python312\python.exe -m pip install --upgrade <wheel-url-or-autoharness>
```

**Alternatives**, in descending preference:

1. **Copilot CLI plugin** (no Python involved; the CLI's own help calls this the
   recommended path): `copilot plugin update autoharness`.
2. **Install from git** — documented in `autoharness help`, and `codeload.github.com`
   is reachable: `python -m pip install --upgrade git+https://github.com/softwaresalt/autoharness.git@v1.5.0`.
3. **Ask the platform team to force a mirror sync** of `autoharness` 1.5.0 on the
   configured internal index. This is the correct long-term organisational fix, since
   the lag will recur on every future release.
4. **Corporate CA bundle for pip** (`--cert <ca-bundle.pem>` or `global.cert`) if
   direct PyPI downloads are wanted. This is an org-policy decision, not a repository
   change.

## Answer to the Question

`pip install autoharness` is not failing, and neither is the release. It is doing
exactly what it was asked: the command lacks `--upgrade`, so it stops at
"Requirement already satisfied (1.4.11)"; and even with `--upgrade`, the
pip-configured non-PyPI mirror does not yet carry 1.5.0. The latest intended version
is **1.5.0**, correctly published to both PyPI and GitHub Releases on
2026-08-30. No repository or release fix is needed — the earlier
Metadata-Version 2.5 publish failure was already fixed by the
`core-metadata-version = "2.4"` pin and the retry succeeded.

## Confidence

**High.** Every claim is backed by a direct read-only measurement: index resolution
compared across two indexes with caching disabled, dry-run installs demonstrating
both failure modes without mutating the environment, endpoint reachability probes,
and sha256 equality between PyPI and GitHub artifacts. The one residual unknown is
the internal mirror's sync schedule, which is outside this repository.

## Investigation Constraints and Degradations

- **PACK-ROUTING degraded (agent-engram):** conceptual/semantic surfaces
  (`engram search`, `engram query-memory`) failed with
  `Database operation failed: stored relation 'content_record' does not have field 'chunk_id'`.
  Structural surfaces were healthy (`workspace-status`: 201 code files, 1025
  functions, 14571 edges, `stale_files: false`, scan complete
  `2026-08-31T01:31:12Z`; `symbols`: 1384 symbols). The correct health subcommand is
  `workspace-status`, not `status`. Prior-decision discovery therefore fell back to
  literal known-path reads over `docs/decisions/` and `docs/compound/`, which is
  recorded here as the required degraded-routing note. The Cozo schema error is a
  separate defect worth its own triage; it was not investigated further under this
  time box.
- **agent-intercom degraded:** tools not exposed in this runtime; remote operator
  visibility reduced. Investigation continued because it is non-destructive.
- **backlogit:** `sync_index` OK (1039 items). `backlogit_search_items` returned
  `null` for the publish/release query, so no prior backlog item was linked.
- **Secrets:** the configured `global.index-url` value was never printed; only
  non-secret structural indicators were emitted. Index URLs were redacted from all
  captured pip output.
- **Scope:** read-only throughout. No install or upgrade was performed — the two
  `pip install` invocations used `--dry-run`, which does not mutate the environment.

## Follow-ups (not promoted)

Per the spike's `promoted_to: ["none"]`, no queue item, plan, branch, PR, stash
record, or compound learning was created. Two observations are recorded here only,
for the operator to route if desired:

1. The Engram Cozo `content_record` / `chunk_id` schema mismatch breaks all semantic
   search in this workspace.
2. Internal-mirror lag will silently cap every future autoharness release on hosts
   using that index; a documented upgrade path in `README.md` covering the mirror and
   TLS-interception case would prevent recurrence.
