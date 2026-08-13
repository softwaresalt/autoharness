---
title: "Windows renames a running process's image to *.exe.old when the on-disk binary is replaced under an open handle"
tags: [windows, mcp, backlogit, engine-attestation, operations]
provenance: "127-S / 118-F post-merge closure, dynamic engine attestation"
---

## Summary

When a Windows executable file is replaced on disk (e.g. by an in-place CLI
upgrade) while a process still holds an open handle to the original file,
`Get-Process`/`ProcessName` on that still-running process will show its image
name suffixed with `.exe.old` (or more generally `<original-name>.old`).
This is Windows silently renaming the on-disk reference the running process
still points to, distinct from the fresh binary now occupying the original
path. It is a reliable, zero-guesswork signal for detecting a stale
long-lived process (e.g. an MCP daemon) that is still serving a pre-upgrade
binary after a CLI tool has been upgraded in place.

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
check `Get-Process <name>*` for an `.old`-suffixed image name as a Windows-
specific tell that the process predates the currently-installed binary.
Restart only the specific stale PID (never a name-based kill, which could
terminate an unrelated same-named process) and re-verify no stale process
remains before trusting engine-identity coherence across CLI and MCP
surfaces. This technique generalizes to any Windows host tool that supports
in-place upgrade while a long-lived process may still be holding the old
binary open (build servers, watchers, language servers, etc.).
