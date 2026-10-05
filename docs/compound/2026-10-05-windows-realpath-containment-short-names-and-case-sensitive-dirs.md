---
title: "Windows realpath containment: dangling links keep short names, and normcase conflates case-sensitive siblings"
problem_type: security-validation-bypass
category: path-containment
root_cause: "On Windows, os.path.realpath returns a dangling link's stored target verbatim, which can spell an in-root directory as an 8.3 short name, so an in-root dangling link compared as outside. Separately, os.path.normcase lowercases every path, so on a directory with per-directory case sensitivity enabled it conflated distinct siblings ws and WS, and an in-root link to WS/... passed a commonpath-over-normcase containment check."
tags: [harness_read, path-containment, windows, realpath, junction, case-sensitivity, 8.3-short-names]
shipment: 193-S
date: 2026-10-05
source: docs/compound/2026-10-05-windows-realpath-containment-short-names-and-case-sensitive-dirs.md
doc_type: learning
---

## Problem

Unit C's reader (`src/autoharness/harness_read.py`) resolves each target with
`os.path.realpath`. It judges containment with `os.path.commonpath` over
`os.path.normcase` forms, before checking that the target exists. Two
Windows-only behaviors broke that check.

1. **Dangling links keep the stored spelling.** `tempfile.mkdtemp()` under the
   default `%TEMP%` returns an 8.3 short path such as
   `C:\Users\DEWILL~1\...`. A symlink created from that path stores the short
   form. `realpath` canonicalizes existing paths through
   `GetFinalPathNameByHandle`. For a dangling link, though, it returns the
   stored target verbatim. The root (long form) and the target (short form)
   then had no common path, so a dangling in-root link (Proof G G20a) was
   reported `OUTSIDE_TRUST_ROOT` instead of `PATH_NOT_FOUND`.
2. **`normcase` conflates case-sensitive siblings.** After
   `fsutil file setCaseSensitiveInfo <dir> enable`, a directory can hold both
   `ws` and `WS`. Because both normcase to `ws`, a static link from the root
   `...\ws` into `...\WS\sentinel.txt` passed containment. The Copilot review
   of PR #496 found this escape.

## Resolution

* **Missing targets.** When `realpath` returns a path that does not exist,
  canonicalize its deepest existing ancestor with `realpath` and re-append the
  missing tail (`_resolve`). The tail does not exist, so it cannot be a link
  that escapes.
* **Containment.** Keep the plan's `commonpath`-over-`normcase` comparison.
  Also require the root's path components to match the target's leading
  components exactly, comparing only the drive case-insensitively
  (`_exact_parts`). Both inputs are `realpath` forms, which carry the on-disk
  case, so legitimate in-root targets still match exactly. The comparison is
  component-wise, never a string prefix.
* **The `.autoharness` root.** The AUTOHARNESS root counts only when
  `realpath(<ws>/.autoharness)` exactly equals the joined path. A
  `.autoharness` that is itself a link, whether it points outside the
  workspace or onto another workspace directory, is not a trust root.

## Prevention

* Run Windows containment tests under the default `%TEMP%` as well as an
  in-workspace `TMP`. The short-name case only shows up under `%TEMP%`.
* `fsutil file setCaseSensitiveInfo` works without admin on a host with WSL
  enabled. Use it, with a `mklink /J` junction, for native regression
  fixtures.
* Treat `normcase` as a comparison aid, not proof of identity. Pair it with an
  exact comparison of canonical forms.
