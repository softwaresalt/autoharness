---
problem_type: runtime-defect-and-review-hardening
category: supervise
root_cause: mcp-json-editor-variable-not-substituted-by-standalone-cli
tags: [supervise, engram, graphtor-docs, mcp, redaction, concurrency, pid-reuse, p-018, copilot-review]
shipment: 129-S
feature: 120-F
pr: 331
---

# 129-S: Supervisor Engram/graphtor-docs Startup Defect + 8-Round Review Hardening

Shipment `129-S` (S3, final of the Plan-1 serial chain) shipped the Copilot CLI
supervisor's application services, adapters, and the `start.ps1`/`start.sh`
compatibility-shim migration. During Ship execution the operator reported a
concrete release-blocking runtime defect discovered on a real launch: Engram
and graphtor-docs never became live, while Copilot and backlogit did. This
document records the root cause, the fix, and the eight rounds of substantive
hosted Copilot (P-018) review findings that followed, since several encode
durable, non-obvious lessons about MCP config portability, redaction ordering,
and process-lifecycle safety.

## Root Cause: `.mcp.json`'s `${workspaceFolder}` Is a VS-Code-Only Editor Variable

The committed root `.mcp.json` used `${workspaceFolder}` in the
engram/graphtor-docs/backlogit MCP server `env` blocks. VS Code's MCP client
substitutes this editor variable before launching a server; the standalone
`copilot` CLI (the actual runtime for `autoharness run` / `start.ps1` /
`start.sh`) does **not** — it passes the literal unresolved string through to
the child process's environment. Verified via
`copilot mcp get engram --json --show-secrets`, which echoed the raw
`${workspaceFolder}` text.

Both `engram shim` and `graphtor-docs serve` crashed immediately when handed
this literal, unresolved path. Copilot itself started fine (it does not depend
on that variable), and backlogit's `BACKLOGIT_WORKSPACE` value happened to go
unread by its actual startup path — so the operator observed exactly the
reported symptom: Copilot + backlogit alive, Engram and graphtor-docs both
absent, with no fatal error surfaced anywhere in the visible session.

**Durable rule**: never rely on editor-only substitution variables
(`${workspaceFolder}`, `${workspace_folder}`, etc.) in any MCP config file that
is also read by a standalone/headless CLI client. If a default relative to the
process CWD is correct, omit the override entirely and let the tool fall back
to its own default — every tool here already had a working CWD-relative
default once the broken override was removed.

## Fix (three complementary parts, all within existing 129-S/120-F scope)

1. **`.mcp.json`**: removed the broken `${workspaceFolder}` env overrides for
   backlogit/engram/graphtor-docs entirely. Each tool falls back correctly to
   its own CWD-relative default.
2. **`supervise/process.py`, `supervise/process_pty.py`, `supervise/app.py`**:
   threaded an explicit `cwd` through every real child-process backend
   (`InheritStdioChildProcess`, `PipeChildProcess`, `PtyChildProcess` via
   `os.chdir` before `execvp`, `WinPtyChildProcess`) and anchored the default
   Copilot child factory's cwd to `workspace_root`. This closes a compounding
   gap where correctness previously depended on the operator's shell already
   being `cd`'d into the workspace.
3. **`supervise/sidecar.py`**: added graphtor-docs as a third one-shot
   preflight sidecar (mirroring backlogit sync / Engram pre-warm), with PATH +
   workspace-local `.graphtor/bin/graphtor-docs(.exe)` fallback resolution
   (mirroring `scripts/deploy-harness.ps1`), and threaded `cwd=str(workspace_root)`
   through every sidecar subprocess call (previously accepted only "for
   interface symmetry/future use" per `120.002-T`'s own docstring, never
   actually applied). Absence/failure of any sidecar still yields a structured
   "unavailable"/"degraded" outcome plus a warning — never silent
   success-shaped readiness.

Test-first: failing tests were added across `test_supervise_process.py`,
`test_supervise_process_pty.py`, `test_supervise_sidecar.py`, and
`test_supervise_app.py` before the production fix, including a POSIX
real-subprocess integration/smoke test proving all three sidecars complete, in
order, strictly before the (faked) Copilot child spawn. A regression guard was
added to `test_verify_workspace.py` asserting the committed `.mcp.json` never
reintroduces `${workspaceFolder}`/`${workspace_folder}`.

## Eight Rounds of Hosted Copilot (P-018) Review — Durable Lessons

PR #331 went through 8 rounds of substantive findings (16 total), all fixed
with real code + regression tests rather than dismissed as advisory. Three
carry lessons worth generalizing:

1. **Redaction coverage must be driven by key-name pattern, not an enumerated
   allowlist.** `bootstrap.py`'s `.env.local` loader originally registered only
   two hardcoded GitHub-token variable names with the redactor. Any other
   secret-shaped `.env.local` value (e.g. `TAVILY_API_KEY`) was silently never
   protected. Fixed by matching every loaded key against the same
   `TOKEN|SECRET|KEY|PASSWORD` pattern already used elsewhere in the redactor,
   so new secret-shaped env vars are covered automatically without a
   allowlist edit.

2. **A raw child-output write path can bypass redaction even when a
   redaction choke point exists elsewhere.** `_pump_child_output`'s direct
   `sys.stdout.write(data)` ran before either registered redaction point, so a
   secret echoed by the child process reached the real console unredacted
   even though the same value was correctly redacted in the `ChildOutput`
   event payload. **Lesson**: every distinct sink of a data stream (console,
   event bus, journal) needs its own redaction application point verified
   independently — redacting one sink is not evidence the others are covered.

3. **A lock acquired only around the mutation step doesn't protect an
   unsynchronized read that logically precedes it.** `_ENVIRON_MUTATION_LOCK`
   was acquired only around `os.environ.update()`, but `bootstrap_workspace()`
   (called with `env=None`) does its own internal `dict(os.environ)` baseline
   read with no synchronization — a concurrent session could observe another
   session's still-applied mutation and misinterpret it as a NO-CLOBBER
   preset. **Lesson**: when auditing a lock's scope, trace every read of the
   protected state backward to its logical origin, not just forward from the
   write.

4. **A PTY backend's `close()` guard against signaling an exited process must
   be mirrored in every other method that can signal, not just `close()`.**
   `process_pty.py`'s POSIX `close()` correctly guarded
   `if self._pid is not None and self._exit_code is None:` before calling
   `os.kill`, but its `signal()` method had no equivalent guard. A caller that
   already reaped a child (`child.wait()`) and then passed that same object
   into a restart path risked signaling a reused PID. Fixed at the call site
   (`child=None` instead of the already-exited child) plus an explicit
   `child.close()` retained separately to avoid introducing an fd leak, since
   the shared cleanup block inside `RestartController.attempt()` is skipped
   entirely when `child=None`.

## Verification Evidence

- Full test suite at final HEAD `3867917f`: 1853 passed (+713 subtests), 0
  failed, 19 skipped.
- P-018 gate: `SATISFIED` — 0 unresolved threads, 16/16 findings across 8
  rounds fixed, replied-to, and resolved via GraphQL `resolveReviewThread`.
- Merged via merge commit `fa0eb14bad50d0b4ec028685a15f7472a6984e39` (2
  parents, confirmed ancestor of `origin/main`).
- P-015 closure classification: `classify_shipment_close_path` returned
  `CASCADE` (qualifying features: `120-F`, `117-F`), reproduced by
  `sim-shipment-closure.ps1` against the installed engine (`v1.9.0` /
  `39528a4`): 66/66 assertions passed. Cascade close via
  `backlogit shipment ship 129-S` archived all 11 manifest artifacts
  (`120.001-T`..`120.008-T`, `120-F`, `117-F`, `129-S`) with
  `returned_ids: []` — zero residue, matching the manifest's own documented
  expectation exactly.

## Follow-ups

None identified. All P0/P1 findings across the shipment's review history are
resolved; no deferred scope was carved out.
