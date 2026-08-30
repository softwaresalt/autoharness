---
title: "An unpinned hatchling build-system dependency can silently emit a newer Metadata-Version than the pinned pypa/gh-action-pypi-publish action's bundled twine accepts"
description: "The v1.5.0 release's first tag/publish attempt failed at the PyPI publish step because hatchling 1.32.0 (resolved fresh at build time from an unversioned [build-system] requires = [\"hatchling\"]) defaults to Metadata-Version 2.5 (PEP 794), which the release.yml-pinned pypa/gh-action-pypi-publish action's bundled twine < 7.0.0 (packaging < 26.0) does not recognize. Local uvx twine check (which always resolves the latest twine) could not reproduce the failure; only the actual pinned CI action's older toolchain rejected it."
problem_type: "environment-drift"
category: "packaging-toolchain-version-skew"
component: "pyproject.toml [build-system] / release.yml"
root_cause: "pyproject.toml declared requires = [\"hatchling\"] with no upper bound, so every build resolves the latest hatchling release available at build time. hatchling 1.32.0 (2026-08-11) made Metadata-Version 2.5 (PEP 794, ratified September 2025) the unconditional default for every build, with no pyproject.toml field required to trigger it. The pinned pypa/gh-action-pypi-publish action SHA in release.yml bundles twine < 7.0.0, whose packaging dependency (< 26.0) predates 2.5 support (packaging first added \"2.5\" to its valid-metadata-versions list in 26.0, 2026-01-21; twine did not require packaging>=26.1 until 7.0.0, 2026-07-28; the action first bundled twine 7 in v1.14.2, 2026-07-29) -- the pinned action SHA predates that release."
resolution_type: "fix"
severity: "high"
tags:
  - "release"
  - "pypi"
  - "hatchling"
  - "packaging-metadata"
  - "ci-pinning"
  - "build-system-dependency"
citations:
  - "Shipment 158-S / feature 150-F (v1.5.0 release preparation)"
  - "release.yml run 33329970485 (failed attempt), 33333803838 (succeeded)"
  - "PR #426 (fix: pin core-metadata-version = 2.4)"
  - "PEP 794 (Core Metadata 2.5, accepted 2025-09-05)"
  - "pypa/hatch commits cd91ac45, 4f5cdf09, 7fb09e87 (backend/src/hatchling/metadata/spec.py)"
  - "pypa/gh-action-pypi-publish v1.14.2 release notes (twine 7 bump)"
source: docs/compound/2026-08-30-unpinned-hatchling-metadata-version-vs-pinned-publish-action.md
doc_type: learning
---

# An unpinned build-backend dependency can drift ahead of a security-pinned CI action's bundled toolchain

## The pitfall

`pyproject.toml`'s `[build-system] requires` commonly has no upper bound
(`requires = ["hatchling"]`), so every real build — local or CI — resolves
whatever the **latest** release of that build backend is *at build time*,
not whatever was current when the project was last touched. Meanwhile,
`release.yml`'s publish step uses a **security-pinned, immutable SHA**
reference to `pypa/gh-action-pypi-publish` (per this repo's own
`ci-security.instructions.md` dependency-pinning rule) — which is exactly
correct security practice, but it also means that action's bundled `twine`
(and `twine`'s own `packaging` dependency) is frozen at whatever was
current **when that SHA was pinned**, potentially months behind the
unpinned build backend.

These two facts compose into a silent compatibility gap: the build backend
can start emitting output (here, a newer `Metadata-Version`) that the
pinned validator genuinely cannot parse, and nothing in the local
development loop necessarily catches it — because local ad hoc validation
tools (`uvx twine check`, `pip install twine`) **also** resolve the latest
`twine` by default, which already supports whatever the build backend just
started emitting. The version skew is invisible until the actual pinned CI
action runs.

## What happened

`hatchling` 1.32.0 (2026-08-11) made `Metadata-Version: 2.5` (PEP 794,
ratified September 2025) the **unconditional default** for every wheel/
sdist build — no `pyproject.toml` field is required to trigger it. The
`v1.5.0` tag push triggered `release.yml`, which built the distributions
with whatever `hatchling` was current that day, then failed at
"Validate built distributions" (`uvx twine check` **inside the pinned
action's own container**):

```text
ERROR    InvalidDistribution: Invalid distribution metadata: '2.5' is not a
         valid metadata version
```

The pinned `pypa/gh-action-pypi-publish` action SHA bundled `twine < 7.0.0`
(`packaging < 26.0`), and `packaging` did not add `"2.5"` to its
recognized metadata versions until `26.0` (2026-01-21) — `twine` did not
require `packaging>=26.1` until `7.0.0` (2026-07-28), and the action first
bundled `twine` 7 in `v1.14.2` (2026-07-29). The pinned SHA predated that.

Critically, **local validation could not reproduce this failure**:
`uvx twine check dist/*` resolved `twine==7.0.0` fresh from PyPI and
passed cleanly, because the *latest* twine already understands 2.5. Only
directly testing with `packaging==25.0` (matching the pinned action's
toolchain era) reproduced the actual incompatibility.

## Why it was caught safely

The release plan's own rollback protocol required probing PyPI for
`autoharness==1.5.0`'s existence *before* taking any remediation action on
any failure at or after the publish step — this confirmed a `404` (nothing
uploaded) before the tag was deleted, guaranteeing no version was burned by
the rollback itself.

## The fix

Pin `core-metadata-version` explicitly in `pyproject.toml`'s
`[tool.hatch.build.targets.wheel]` **and** `[tool.hatch.build.targets.sdist]`
(both targets independently read this setting — there is no single
inherited value):

```toml
[tool.hatch.build.targets.wheel]
core-metadata-version = "2.4"

[tool.hatch.build.targets.sdist]
core-metadata-version = "2.4"
```

`2.4` is universally supported by every current PyPI toolchain and already
covers this project's needs (`License-Expression`/`License-File` per
PEP 639).

## How to actually verify a fix like this locally

Since the latest `twine`/`packaging` cannot reproduce a stale-validator
failure, test against a `packaging`/`twine` version matching the *pinned
CI action's era* instead:

```bash
uv run --with "packaging==25.0" --with "twine==6.2.0" --isolated python -c "
import zipfile
from packaging.metadata import parse_email
z = zipfile.ZipFile('dist/your-1.0.0-py3-none-any.whl')
raw, unparsed = parse_email(z.read('your-1.0.0.dist-info/METADATA'))
print('Metadata-Version:', raw.get('metadata_version'), 'unparsed:', unparsed)
"
```

## Generalizable takeaway

An unpinned build-backend dependency (`[build-system] requires`) and a
deliberately security-pinned CI action can silently drift apart in
toolchain-version assumptions. When a release workflow validates build
output with a pinned action, either (a) pin the build backend's own
output format (`core-metadata-version` or equivalent) to a version the
pinned validator is known to accept, or (b) periodically bump the pinned
action SHA to track current toolchain capability — and prefer testing
against the *pinned validator's actual era*, not whatever the latest
locally-resolved validator happens to accept, when diagnosing a mismatch
like this.
