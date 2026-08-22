---
title: "An updater-renamed *.exe.old image is a useful, corroborating signal for a stale process holding a replaced Windows binary — not a platform guarantee"
tags: [windows, mcp, backlogit, engine-attestation, operations]
provenance: "127-S / 118-F post-merge closure, dynamic engine attestation"
source: docs/compound/2026-08-12-windows-stale-process-exe-old-detection.md
doc_type: learning
---

## Summary

When a Windows executable file is replaced on disk (e.g. by an in-place CLI
upgrade) while a process still holds an open handle to the original file,
some updaters/installers rename the still-open original file to
`<original-name>.old` (e.g. `backlogit.exe.old`) as part of their
replace-in-place strategy, so that a fresh binary can occupy the original
path immediately. **This is updater/installer-specific behavior, not a
Windows platform guarantee** — the exact renaming convention (if any) is
chosen by whatever tool performs the replacement, and whether an in-use
image can be renamed at all depends on the file-sharing mode the original
process opened it with. Where it does apply, it is a useful, low-cost
corroborating signal — combined with process start time and executable
identity/version — for detecting a stale long-lived process (e.g. an MCP
daemon) that is still serving a pre-upgrade binary after a CLI tool has
been upgraded in place. It must not be treated as a guaranteed or
universal Windows behavior.

## Concrete case

`backlogit` was upgraded in place from `v1.8.0-dirty`/`fd8d2c9d` to the
clean release `v1.9.0`/`39528a4` (build `2026-08-12T03:49:03Z`). A
long-lived `backlogit mcp` process (PID 45252, started 2026-08-11
14:54:01 — i.e. *before* the upgrade) was still running. `Get-Process`
showed its image as `backlogit.exe.old`, confirming it held a handle to the
now-replaced pre-upgrade binary even though the on-disk path
`backlogit.exe` now resolved to v1.9.0. Terminated via
`Stop-Process -Id 45252 -Force` (PID-specific, never by process name, to
avoid collateral termination of an unrelated process that happens to share
a name) so that any future MCP connection would spawn a fresh process
against the current on-disk binary.

## Generalizable lesson

Before relying on a long-lived daemon/MCP process for identity-sensitive
operations (e.g. a "confirm CLI/MCP engine identity" attestation gate),
check `Get-Process <name>*` for an `.old`-suffixed image name as a possible,
tool-specific tell that the process predates the currently-installed
binary — but corroborate it with independent evidence (process start time
relative to the known upgrade time, and executable/version identity where
obtainable) rather than treating the naming convention alone as proof, since
it depends on the specific updater/installer's behavior and on file-sharing
semantics, not a Windows platform guarantee. Restart only the specific stale
PID (never a name-based kill, which could terminate an unrelated
same-named process) and re-verify no stale process remains before trusting
engine-identity coherence across CLI and MCP surfaces. This corroborating
signal generalizes to any Windows host tool whose updater/installer uses a
similar replace-in-place convention while a long-lived process may still be
holding the old binary open (build servers, watchers, language servers,
etc.) — always verify against start time and identity, never the naming
convention in isolation.
