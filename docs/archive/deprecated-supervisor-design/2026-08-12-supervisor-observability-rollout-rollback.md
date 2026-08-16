---
title: "Local Copilot CLI supervisor — event/journal contracts, redaction guarantees, and start.ps1/start.sh migration rollout+rollback runbook"
status: active
related_feature: 106-F
related_shipment: 129-S
---

# Local Copilot CLI Supervisor — Observability, Redaction, and Migration Runbook

## Summary

This doc is the operator-facing reference for the local Copilot CLI
supervisor feature (`src/autoharness/supervise/`) and its final,
behavior-changing shipment, 129-S (S3). It covers:

1. The stable event catalog (`contracts.py`) and how `events.py`'s
   `EventBus` delivers it.
2. The session journal schema (`journal.py`) — what it is, and, just as
   importantly, what it explicitly is **not**.
3. Redaction guarantees and their limits (`redact.py`).
4. The `start.ps1`/`start.sh` migration/rollback runbook, including every
   approved behavior delta introduced across the three shipments (S1/S2/S3).
5. The machine-readable exit-code contract (`errors.py`) and the stable
   `autoharness run` CLI option contract.
6. The event bus's scope: a hook surface only in this feature — no consumer
   ships, and Engram gains no new authority.

Nothing in this document is itself normative outside this repository; it
describes the contracts this repository's own code implements and tests
pin.

## 1. Event Catalog

All events are frozen, plain-data dataclasses defined once in
`src/autoharness/supervise/contracts.py`. There is exactly one canonical
definition of each event shape — no parallel/duplicate types exist
elsewhere in the codebase (`app.py`, `recovery.py`, `sidecar.py`, and
`bootstrap.py` all import and reuse these same classes rather than
inventing their own).

| Event | Fields | Emitted by |
|---|---|---|
| `SessionPhaseChanged` | `phase: str`, `previous_phase: str \| None` | `session.SessionStateMachine.transition()` (returned to the caller, who is responsible for handing it to a bus/journal); `app.py` for every phase transition it drives directly |
| `SidecarProbed` | `name: str`, `available: bool`, `detail: str` | `app.py` after `sidecar.run_sidecars()` returns, one per sidecar outcome |
| `CopilotResolved` | `exe_path: str`, `source: str` (`"env_path"` \| `"env_exe"` \| `"path_lookup"`) | `app.py` after `resolve.resolve_copilot()` returns |
| `ChildSpawned` | `argv: tuple[str, ...]`, `pid: int \| None` | `app.py` immediately after `child.spawn()` |
| `ChildOutput` | `stream: str` (`"stdout"` \| `"stderr"`), `line: str` | only emitted by backends with `supports_output_capture=True`; never emitted for `InheritStdioChildProcess` |
| `ChildOutputUnavailable` | `reason: str` | emitted (and journaled via `journal.append_child_output_unavailable()`) when the active backend cannot capture output — this is the normal, expected case for the default `InheritStdioChildProcess` backend |
| `ChildExited` | `exit_code: int` | `app.py` after `child.wait()` returns, carrying the child's real exit code verbatim (H3) |
| `ApprovalRequested` | `kind: str`, `summary: str`, `options: tuple[str, ...]`, `default: str \| None`, `timeout: float \| None` | `approvals.ConsoleApprovalService.request_approval()` before rendering/blocking on operator input |
| `ApprovalResolved` | `kind: str`, `resolution: str`, `resolved_by: str` | `approvals.ConsoleApprovalService.request_approval()` — always returned, whether interactively answered, auto-resolved via `FallbackPolicy`, or (for `resolved_by`) attributable to the operator/console/fallback |
| `CancelRequested` | `reason: str` | emitted when cancellation is observed (e.g. `KeyboardInterrupt` during `child.wait()`) before `recovery.cancel_session()` runs |
| `RestartScheduled` | `attempt: int`, `max_attempts: int`, `reason: str` | `recovery.RestartController.attempt()` before spawning a replacement child |
| `RestartExhausted` | `attempts: int` | `recovery.RestartController` when the restart budget is exhausted |
| `JournalCheckpoint` | `sequence: int`, `detail: str` | optional, caller-constructed marker event for durable-write milestones |

Event delivery is entirely the responsibility of
`autoharness.supervise.events.EventBus`:

* `EventBus(redactor=None).subscribe(type_or_predicate, handler) -> token`
  registers a handler either by exact event type or an arbitrary predicate.
* `.emit(event_instance)` redacts the event (via `redact.redact_record`,
  using the bus's own `Redactor` if one was supplied) and only then
  delivers it to matching subscribers. If redaction fails closed, the event
  is **dropped** and a warning is produced — it is never delivered
  unredacted.
* `install_no_listen_guard()` is an H7 enforcement context manager: it
  installs a `sys.addaudithook` on `socket.bind` for the duration of the
  `with` block, raising `ListeningSocketDetected` if anything inside that
  block attempts to open a listening socket. `check_import_denylist(names)`
  is a secondary, lexical safety net checking that a set of module names
  (e.g. HTTP/socket-server-ish modules) were never imported.

Adding a new field to an existing event is additive and non-breaking.
Renaming or removing a field, or renaming an event class, is a breaking
change to this contract and must be treated as such (version bump +
changelog entry in a future shipment, if/when this contract needs to
evolve).

## 2. Session Journal Schema

`autoharness.supervise.journal.SessionJournal` persists one JSON object per
line (JSONL) at:

```text
<workspace_root>/.autoharness/sessions/<session_id>/journal.jsonl
```

Schema:

* **Line 0** is a schema-versioned header record, written once, before any
  event line:

  ```json
  {"schema_version": 1, "session_id": "<id>", "kind": "header", "seq": 0, "timestamp": "<UTC ISO-8601>"}
  ```

* **Every subsequent line** carries:
  * `seq` — a monotonically increasing integer, continuing on from the
    header's `seq=0` (so the first real event is `seq=1`).
  * `timestamp` — UTC, ISO-8601 (`datetime.now(timezone.utc).isoformat()`).
  * `kind` — the event's class name (for `append_event()`) or a marker
    kind (`"redaction_failed"`, `"auto_resolved"`, etc. — see below).
  * The event's own fields, flattened via `dataclasses.asdict()`.

* **Resume cursor**: `read_cursor(path) -> int` (module-level function, also
  exposed as `SessionJournal.read_own_cursor()`) returns the last
  successfully written `seq`, or `-1` if the file does not exist or
  contains no valid `seq`-bearing line. A caller resuming a session computes
  the next `seq` as `read_cursor(path) + 1` uniformly, whether resuming an
  existing journal or starting a brand-new one. A crash-truncated trailing
  line (a corrupt/incomplete JSON fragment from a mid-write crash) is
  tolerated: it is skipped by `read_cursor`, and — on the NEXT session that
  reopens this journal — isolated onto its own line (if it wasn't already
  newline-terminated) before any new line is appended, so the crash
  fragment can never merge with a subsequent well-formed record and corrupt
  it too.

* **Redaction choke point**: every write, including the header line, routes
  through `redact.redact_record()`. A record that cannot be safely
  redacted is never written verbatim — instead a `{"kind":
  "redaction_failed", "seq": ..., "timestamp": ..., "warning": ...}`
  marker record is written in its place, preserving the append-only,
  monotonically increasing `seq` sequence.

* **Path containment**: journal paths are resolved via
  `locking._resolve_contained_path()` (the SAME containment helper
  `locking.py` uses for its own guard/record files) — an escaping
  `session_id` (e.g. containing `..`) raises `LockError` rather than being
  silently clamped into an unintended location.

* **Gitignore maintenance (H6)**: on first use, `journal.py` calls
  `locking.ensure_ignored(workspace_root, "sessions")` — the SAME
  `.autoharness/.gitignore` maintenance helper `locking.py` already
  introduced for its own lock files, so there is exactly one ignore-file
  code path.

### What the journal is **not**

* It is **not** a checkpoint. It is local, gitignored, operational
  observability/resume state for a single supervised session — nothing
  more.
* **backlogit remains the sole backlog/checkpoint authority.** The journal
  has no relationship to backlog items, shipments, or task tracking. Ship
  and Stage's own checkpoint/continuity protocols (backlogit-based) are
  entirely separate from this journal and are not superseded, extended, or
  replaced by it in any way.
* It carries no authority to gate merges, approvals, or backlog state
  transitions. It is a diagnostic artifact a human or a future tool may
  read; nothing in this feature currently reads it back to drive decisions
  beyond a session's own resume-cursor computation.

## 3. Redaction Guarantees and Limits

`autoharness.supervise.redact` is the single choke point every
emission/persistence path (journal writes, `EventBus.emit()`, approval
summaries) routes through. Guarantees:

* **Two complementary mechanisms**:
  1. **Pattern-based** — regexes for well-known secret shapes (`ghp_`,
     `gho_`, `ghu_`, `ghs_`, `ghr_`, `github_pat_` prefixes) plus key-name
     matching (`TOKEN`/`SECRET`/`KEY`/`PASSWORD`, case-insensitive) for
     structured mapping input — a sensitive-named key's value is replaced
     regardless of its shape (string, number, nested list/dict), not just
     when it happens to be a string.
  2. **Registered-value based** — `register_secret(value)` (module-level,
     against a process-global `Redactor`) or `Redactor.register_secret()`
     (against an explicit, injected instance) records a concrete,
     already-resolved secret value for exact whole-match substring
     redaction wherever it appears in text — even when it matches no regex
     pattern at all (H5). This is how `bootstrap.py` ensures a `gh auth
     token`-resolved value is caught even though a future token format
     might not match today's regexes.
* **Whole-match only.** A matched secret is replaced entirely with a fixed
  placeholder (`***REDACTED***`); there is no partial masking (no "first/last
  N characters shown"), because partial masking of a token-shaped secret can
  still leak enough entropy to be useful.
* **Fail-closed drop-on-failure.** `redact_record()` is the fail-closed
  entry point: if a record cannot be safely processed (an unsupported
  value shape, a non-string mapping key, two distinct keys redacting to the
  same output key, or any other exception during redaction), the record is
  **dropped** (`(None, warning)` is returned) rather than ever emitted
  unredacted. There is no "degraded pass-through" path anywhere in this
  choke point. The warning text itself is a fully constant string
  (`"redaction failed, record dropped"`) — never the original exception
  message or even the exception's type name — because a maliciously/
  accidentally constructed exception class could embed secret material in
  its own `__name__`.
* **Known limits** (documented, not defects):
  * Only the value shapes `str`, `Mapping`, `list`/`tuple`, and
    `int`/`float`/`bool`/`None` are supported; anything else (e.g. raw
    `bytes`, arbitrary objects, sets) fails closed rather than being
    redacted or passed through.
  * Pattern-based redaction cannot catch a secret shape it has never seen;
    this is precisely why the registered-value mechanism exists as a
    complementary, format-agnostic backstop for values this codebase itself
    resolved (e.g. via `gh auth token`).
  * Redaction never inspects the CHILD process's own stdout/stderr when
    the active backend is `InheritStdioChildProcess` (the default): that
    stream bypasses this process entirely (see `process.py`), so no secret
    the child itself prints is redacted by this feature. This is an
    accepted, documented scope boundary of the "inherited stdio by
    default" design (H3-aligned: the child's own I/O is never intercepted
    or altered), not a redaction gap in this module.

## 4. Migration / Rollback Runbook

### Staged rollout across three shipments

* **S1 (127-S)** — zero behavior change. Built the shared core
  (`contracts.py`, `errors.py`, `redact.py`, `locking.py`, `process.py`,
  `process_pty.py`, `session.py`) with full unit test coverage, and pinned
  `start.ps1`/`start.sh`'s CURRENT (pre-migration) behavior via the
  characterization suites this shipment (S3) has since evolved.
* **S2 (128-S)** — an unwired library. Added `events.py`, `journal.py`,
  `recovery.py`, `result.py` — all fully implemented and tested, but not
  yet invoked by any entry point. Still zero observable behavior change to
  `start.ps1`/`start.sh`.
* **S3 (129-S, this shipment)** — the ONLY behavior-changing shipment.
  Added `bootstrap.py`, `sidecar.py`, `resolve.py`, `approvals.py`,
  `app.py`, the `autoharness run` CLI adapter, and converted
  `start.ps1`/`start.sh` (+ `templates/scripts/*.tmpl` copies) into thin
  compatibility shims that delegate the entire session lifecycle to
  `autoharness run`.

### Pre-migration script content preservation

The full pre-migration `start.ps1`/`start.sh` inline logic is preserved via
git history — no separate backup file was created in the working tree.
The last commit that modified `start.ps1`/`start.sh` before this migration
is:

```text
4d6aa0b0 fix(start): COPILOT_USE_REMOTE appends --remote not --yolo (PR 227 t1)
```

To inspect or recover the exact pre-migration script content:

```bash
git show 4d6aa0b0:start.ps1
git show 4d6aa0b0:start.sh
git show 4d6aa0b0:templates/scripts/start.ps1.tmpl
git show 4d6aa0b0:templates/scripts/start.sh.tmpl
```

(If this shipment's own commit SHA is needed instead — e.g. to diff
"one commit before the migration landed" — the orchestrator will record
that SHA once this shipment is committed; `4d6aa0b0` is the last commit
that touched these files strictly BEFORE this migration's changes.)

### Rollback procedure

* **Single-file revert per shim.** Each of the four migrated files
  (`start.ps1`, `start.sh`, `templates/scripts/start.ps1.tmpl`,
  `templates/scripts/start.sh.tmpl`) can be reverted independently via
  `git checkout 4d6aa0b0 -- <path>` (or an equivalent revert commit). There
  is no cross-file coupling that requires all four to roll back together,
  although rolling back only some of them re-introduces the pre-migration
  Windows/POSIX behavior asymmetry documented below (deltas 2/3/4/6/7) for
  whichever files are reverted.
* **Requires redeploy.** A shim rollback only takes effect for workspaces
  that re-pull/re-fetch the reverted script content — there is no runtime
  toggle. Any workspace with the migrated shim already installed keeps
  running the migrated behavior until it is explicitly redeployed with the
  reverted file.
* **No `AUTOHARNESS_SUPERVISOR=0` escape hatch.** An environment-variable
  escape hatch to skip the new supervisor path and fall back to legacy
  inline behavior was considered and explicitly **withdrawn** (per F16).
  It is NOT present anywhere in this migration, and none of the four shim
  files, `bootstrap.py`, `resolve.py`, `sidecar.py`, or `app.py` reference
  such a variable. Do not add one in a future change without first
  revisiting F16's rationale for withdrawing it.
* Rolling back does **not** require reverting any of the new
  `src/autoharness/supervise/*.py` modules or the `autoharness run` CLI
  adapter — they remain valid, tested, unused-by-the-shim code if the shim
  itself is reverted, ready to be re-adopted by re-applying the shim change
  later.

### Approved behavior deltas

Every delta below is a deliberate, tested, and (where applicable)
characterization-suite-pinned behavior change introduced by unifying
Windows/POSIX bootstrap logic into a single, platform-branch-free Python
implementation. None of these are regressions; each is documented at its
point of origin (`bootstrap.py`/`resolve.py`/`sidecar.py` module docstrings)
and pinned by `tests/test_start_ps1_characterization.py` and/or
`tests/test_start_sh_characterization.py`.

| Delta | Description | Pinned by |
|---|---|---|
| **DELTA 1** (`WINDOWS_PAT_NO_GH`) | `gh` absent or failing when resolving `GITHUB_TOKEN`/`GITHUB_PERSONAL_ACCESS_TOKEN` is non-fatal: a warning is emitted, the affected variable(s) are left UNSET (never set to an empty string), and the session proceeds. This was already the (accidental, by-omission) POSIX behavior; it is now an explicit, tested, cross-platform contract. | PS1 suite (`test_delta1_...` / gh-absent/failing tests); SH suite (`test_delta1_shared_gh_absent_is_non_fatal_and_leaves_vars_unset`) |
| **DELTA 2** (`POSIX_ENGRAM_DATA_DIR`) | `ENGRAM_DATA_DIR` now defaults to `<workspace_root>/.engram` on POSIX. The pre-migration `start.sh` had this line present but commented out — it was never active. | SH suite (`test_copilot_home_and_engram_data_dir_default_to_workspace_subdirs`) |
| **DELTA 3** (`POSIX_PAT_BOOTSTRAP`) | `GITHUB_TOKEN`/`GITHUB_PERSONAL_ACCESS_TOKEN` resolution via `gh auth token` now runs on POSIX at all — the pre-migration `start.sh` had NO PAT handling whatsoever. Same non-fatal-on-`gh`-absent/failing contract as Windows (DELTA 1). | SH suite (`test_delta3_github_tokens_resolved_from_gh_when_both_unset`) |
| **DELTA 4** — WITHDRAWN during Ship-side local review (129-S). An earlier draft of this shipment unified `GITHUB_TOKEN`/`GITHUB_PERSONAL_ACCESS_TOKEN` onto a single guarded/no-clobber contract with at most one `gh auth token` call. That was an unnamed, unapproved fourth delta outside ruling A's three-entry matrix (deltas 1–3 only) and has been REVERTED: `bootstrap.py` now preserves the pre-migration `start.ps1` per-variable asymmetry byte-identically on BOTH platforms — `GITHUB_TOKEN` guarded/no-clobber, `GITHUB_PERSONAL_ACCESS_TOKEN` UNGUARDED and always re-resolved when `gh` is available (see `bootstrap.py`'s `_TOKEN_VAR_NO_CLOBBER`). | PS1 suite (`test_github_tokens_resolved_from_gh_when_both_unset`, `test_github_token_preset_pat_is_still_unguarded_reresolved`); SH suite (same two, POSIX-side) |
| **DELTA 5** (H3 exit code fix) | The pre-migration `start.ps1` ended with a bare `& $copilotExe @copilotArguments` and NO `exit $LASTEXITCODE`, so the `pwsh` host process's own exit code was ALWAYS `0` regardless of the supervised child's real exit code (a genuine latent bug, previously pinned by the old suite as `test_pwsh_host_exit_code_does_not_mirror_child_exit_code`). The new shim's `exit $LASTEXITCODE` is a deliberate, task-mandated (H3) fix — H3 is a hard requirement of the shim conversion itself, independent of and not subject to the three-delta carve-out (which governs preservation of legacy behavior, not the shim's own non-negotiable exit-code-verbatim obligation). The migrated suite now pins VERBATIM exit-code propagation as the correct, intended behavior, replacing the old bug-pinning test entirely. `start.sh` was already correct here (`exec` preserves exit status natively) and remains so. | PS1 suite (`test_child_exit_code_propagates_verbatim`); SH suite (same test name, re-pinning already-correct behavior) |
| **DELTA 6** (`POSIX_SIDECAR_PREFLIGHT`, implied by consolidation) | `backlogit sync` and the Engram pre-warm sequence (direct sync, falling back to bind+daemon sync on failure) now run on POSIX too. The pre-migration `start.sh` had NO sidecar logic at all (explicitly pinned as an ABSENCE by the old suite). This is an unavoidable consequence of `sidecar.py` being one shared, platform-branch-free module, and 120.002-T's own task text describes this preflight as logic "duplicated in start.ps1 and start.sh" — treating parity as the intended baseline. FLAGGED FOR EXPLICIT OPERATOR ACKNOWLEDGEMENT alongside DELTA 7: unlike deltas 1–3, this was not separately pre-named in a ruling; Ship accepted it as a forced, non-fatal (see 120.002-T: "FAILURE IS NON-FATAL") consequence of the sole-shared-module architecture rather than reverting it into a platform branch, which would itself contradict the "no platform branching for behavior" design principle applied throughout this shipment. | SH suite (`test_delta6_backlogit_sync_runs_when_resolved`, `test_delta6_engram_direct_prewarm_happy_path`, plus failure/absence variants) |
| **DELTA 7** (`POSIX_REMOTE_FLAG`, implied by consolidation) | `--remote` composition (`COPILOT_USE_REMOTE` truthy check + double-add guard) now applies on POSIX too. The pre-migration `start.sh` had NO `--remote`/`COPILOT_USE_REMOTE` logic at all (explicitly pinned as an ABSENCE by the old suite). Same rationale as DELTA 6, but EXPLICITLY PRE-APPROVED: 120.003-T's own task text states verbatim "ON POSIX THIS IS A DELIBERATE BEHAVIOR CHANGE ... legitimate in Shipment 3 ... must be called out in the 120.008-T migration notes" — this entry is that call-out. | SH suite (`test_delta7_remote_flag_appended_when_use_remote_truthy`, plus not-truthy/no-duplicate variants) |
| **WORKSPACE ROOT ANCHORING** (not numbered — an internal-consistency fix, not a cross-platform unification) | The pre-migration `start.sh` anchored `.env.local` lookup to its own script directory (absolute, cwd-independent) but defaulted `COPILOT_HOME` to a cwd-relative `"./.copilot"` literal — an internal inconsistency within that single script. The new shim passes `--workspace "$script_dir"` explicitly (see the `--workspace`/`-w` CLI addition below) so ALL bootstrap defaults (`.env.local` lookup, `COPILOT_HOME`, `ENGRAM_DATA_DIR`) are consistently anchored to the script's own directory on BOTH platforms, matching (and fixing) the more correct of the two pre-existing conventions, and restoring `start.ps1`'s pre-existing cwd-independence (`$PSScriptRoot`-anchored) which a naive migration would otherwise have silently broken. | PS1 suite (workspace-anchoring is implicit in every end-to-end test, since the sandbox always invokes from the workspace dir and the shim now passes `--workspace $PSScriptRoot` explicitly); SH suite (same, via `--workspace "$script_dir"`) |

### `--workspace`/`-w` CLI addition

`autoharness run`'s original T17 contract as literally stated in 120.006-T
did not list a workspace-root option, and F25 declares that contract
"COMPLETE, STABLE," with "adding ... an option" being "a documented
contract change." This addition is exactly that: a documented contract
change, flagged here for explicit operator acknowledgement, made for a
concrete reason rather than silently absorbed. Without it, the shims would
have had to rely on the invocation's current working directory for
bootstrap anchoring — which matches `start.sh`'s pre-existing (partially
inconsistent, see above) cwd-relative behavior but would have silently
broken `start.ps1`'s pre-existing cwd-independent behavior (anchored to
`$PSScriptRoot`, not cwd). `--workspace`/`-w PATH` (default: `.`) closes
this gap and is now part of the stable `autoharness run` option contract
(see below); both shim scripts pass it explicitly, anchored to their own
script directory (`$PSScriptRoot` / `$script_dir` respectively). This
option name/shape is not novel: `autoharness gate check`/`size`/
`copilot-review`/`dag-readiness` already establish `--workspace`/`-w PATH`
as this CLI's standing convention for a workspace-root override, so `run`
adopts the same established shape rather than inventing a new one.


## 5. Exit-Code Contract and `autoharness run` Option Contract

### Machine-readable exit codes (`errors.py`)

`autoharness.supervise.errors.EXIT_CODE_BY_KIND` is the single source of
truth mapping every `ErrorKind` to a stable exit code:

| `ErrorKind` | Exit code | Raised by |
|---|---|---|
| `UNKNOWN` | 1 | fallback for an `AutoharnessError` raised without a specific kind |
| `CONFIG` | 2 | `ConfigError` — invalid or missing supervisor configuration |
| `LOCK` | 3 | `LockError` — session guard lock acquisition, contention, or containment failure (includes a refused/blocked force-unlock outcome) |
| `RESOLUTION` | 4 | `ResolutionError` — the Copilot CLI executable could not be resolved |
| `APPROVAL` | 5 | `ApprovalError` |
| `RESTART` | 6 | `RestartError` |
| `ILLEGAL_TRANSITION` | 7 | `IllegalTransitionError` — an illegal `SessionStateMachine` transition was attempted |

A module-load-time assertion in `errors.py` itself guarantees every
`ErrorKind` member has exactly one entry in this table (totality). `cli.py`
NEVER hardcodes an exit code: `_run_command()` exits with
`result.exit_code`, which itself derives from this table via however
`app.py` constructed the `SupervisorResult` — a non-error/`"ok"` result's
`exit_code` is the supervised child's own real exit code, propagated
verbatim (H3), not a value from this table at all.

### `autoharness run` option contract

```text
autoharness run [--json] [--force-unlock] [--max-restarts N]
                [--pty | --no-pty] [--session-id ID] [--workspace PATH]
                [-- <verbatim child argv>]
```

| Option | Effect |
|---|---|
| `--json` | Emit the `SupervisorResult` as JSON (`result.to_dict()`) instead of a human-readable summary. |
| `--force-unlock` | Opt in to attempting a gated force-unlock recovery when the session lock is refused due to contention (still routed through the operator/`approval_service` gate — this flag only opts IN to the possibility, it does not itself bypass approval). |
| `--max-restarts N` | Restart budget for the supervised child. Default: `0`. |
| `--pty` | Spawn the child under a pseudo-terminal (falls back to inherited stdio on any PTY failure/unavailability, never `PipeChildProcess`). |
| `--no-pty` | Never attempt a PTY; always use inherited stdio. |
| `--session-id ID` | Explicit session id. Default: generated. |
| `--workspace`, `-w PATH` | Workspace root for bootstrap/lock/journal state. Default: the current working directory. See the migration runbook above for why this exists. |
| `--` | Everything after this marker is forwarded VERBATIM as the supervised child's argv — never re-parsed, re-quoted, reordered, or filtered. |

Every option maps 1:1 onto a `run_session()` parameter; `cli.py` contains
no policy of its own beyond argument-syntax validation (H8-aligned: pure
adapter, no duplicated decision logic).

## 6. Event Bus Scope

The `EventBus` introduced in S2 and wired up in this shipment is, in this
feature, **a hook surface only**:

* No consumer ships as part of this feature. Nothing in this repository
  subscribes to the bus for any purpose beyond the tests that exercise
  `EventBus` itself.
* Engram gains **no new authority** from this feature. The session journal
  and event bus are local, gitignored, operational artifacts; they do not
  feed Engram's indexing, do not grant Engram any write/mutation
  capability, and are not a checkpoint/backlog substitute (see the "What
  the journal is not" section above).
* Future consumers (a TUI, a remote dashboard, a log shipper) MAY subscribe
  to this bus later, but doing so is out of scope for 129-S and would be a
  separate, explicitly-scoped shipment.
