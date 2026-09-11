---
description: "Acquire and release file-level locks to prevent concurrent modifications during multi-agent or human+agent workflows"
---

# File Lock

Manage per-file advisory locks so that multiple agents (or an agent and a
human operator) do not clobber the same file during complex refactors or
parallel work sessions.

## When to Use

Invoke before modifying any source file when concurrent access is possible.
This includes multi-agent orchestration, long-running refactors, and any
session where a human may be editing files in the same workspace.

Agents MUST follow the concurrency protocol defined in
`.github/instructions/concurrency.instructions.md`.

## Inputs

* `filepath`: (Required) Path to the target file, relative to the workspace root.
* `action`: (Required) One of `acquire` or `release`.
* `--workspace-root <path>` (acquire only, optional): explicit workspace
  root for the H2/H4 containment check. When omitted, the root is derived
  from `git rev-parse --show-toplevel`, but only trusted when the script's
  own installed directory is exactly that root's `scripts/` child (guards
  against a nested checkout without its own `.git` silently widening to an
  ancestor repository's root); otherwise acquire fails closed and requires
  this flag explicitly.
* `--token <token>` (release only, optional): the capability token printed
  by `acquire_lock` at acquire time (`LOCK_TOKEN=<token>`). Falls back to
  the `LOCK_TOKEN` environment variable when not supplied. Required to
  release a lock unless `--force` is given.
* `--force` (release only, operator use): break the lock even without a
  matching token. See "Ownership and the `--force` override" below.

## Output

* On `acquire` success: lock file created, exit code 0. A one-time
  capability token is printed to stdout as `LOCK_TOKEN=<token>` — capture
  it; it is never re-printed or recoverable from the lock file afterward
  (only its digest is stored).
* On `acquire` failure (lock already held, path escapes the workspace root,
  or no CSPRNG/digest source is available): exit code 1.
* On `release` success (token verified, or `--force` given): lock file
  removed, exit code 0.
* On `release` failure — ownership could not be verified and `--force` was
  not given: lock file left in place, **exit code non-zero**. This is a
  refusal, not a warning: an unverified release must never look identical
  to a successful one on exit code.
* On `release` when no lock file exists (already released, or the target
  was never locked): exit code 0 with a warning — this case does not
  require ownership proof, since there is nothing to protect.

## Ownership and the `--force` override

Every successful `acquire` mints a random capability token and stores only
its SHA-256 digest in the lock file (`owner_digest`) — the token itself is
never persisted anywhere. `release` requires the caller to present that
same token (`--token` or `LOCK_TOKEN`) before it will remove the lock; a
missing or non-matching token is refused (non-zero exit, lock left in
place). `agent`/`pid`/timestamp recorded in the lock file remain identity
metadata only — informative for a human or operator deciding whether to
break a stale lock, and never treated as proof of ownership.

**`--force` is an operator escape hatch, not routine agent usage.** It
breaks the lock unconditionally, without a token, for cases such as a
crashed process that never released its lock. Agents SHOULD NOT reach for
`--force` on their own initiative when a normal release is refused; that
refusal usually means the lock belongs to someone else. Surface the
refusal (including the `agent`/`pid`/timestamp it reports) to the operator
and let them decide.

**Honest bound (non-adversarial)**: this is an advisory locking convenience
for well-behaved cooperating agents, not a security boundary. The token
defends against accidental or confused releases — for example, one agent's
session mistakenly releasing a lock it never acquired — not against a
hostile local process, which can always delete the `.{filename}.lock` file
directly regardless of any token. Do not rely on this mechanism, or on any
text in this skill, to imply an adversarial security guarantee.

## Token exposure and safe handling

The capability token is a short-lived secret returned on **stdout** so the
caller can capture it — the scripts do not, and cannot, control what the
caller does with that stdout afterward. This is documented rather than
assumed:

* **Capture, don't print.** Because the token is printed on stdout, it can
  land in CI logs, terminal transcripts, shell history, and agent
  conversation logs if the caller echoes or re-prints it. Callers MUST
  capture the `LOCK_TOKEN=<token>` line into a variable or file rather than
  printing it again. The scripts themselves never re-echo the token (or the
  `owner_digest`) in any status, verbose, warning, or error message —
  refusal and staleness messages print the lock path, `agent`, `pid`, and
  age, but never the token or the digest.
* **Never persisted.** The token is never written to the lock file, to any
  log the scripts create, or to telemetry — only its SHA-256 digest
  (`owner_digest`) is persisted, and the digest cannot be reversed back into
  the token.
* **`--token` vs. `LOCK_TOKEN` exposure differs.** `LOCK_TOKEN` set as an
  environment variable is inherited by child processes and, on some
  systems, may be readable by other processes owned by the same user (for
  example, via `/proc/<pid>/environ` on Linux). Passing `--token <token>` as
  a command-line argument avoids environment inheritance but may be visible
  to other users via process-listing tools (for example, `ps`) on systems
  where process arguments are not restricted to their owner. Both forms are
  supported; choose based on which exposure surface is more acceptable in
  the calling environment.
* **Why this is tolerable.** These exposure paths are acceptable only
  because this token is an anti-accident capability for an *advisory* lock
  (see "Honest bound" above), not an adversarial security boundary. Token
  leakage degrades the anti-accident property (a hostile or careless holder
  of the leaked token could release the lock as if they legitimately
  acquired it) without creating an adversarial exposure that did not
  already exist — a local process with write access to the workspace could
  already delete the lock file directly, with or without the token.

## Scripts

Both PowerShell and Bash equivalents are provided for cross-platform
compatibility. Use whichever matches the runtime environment.

### acquire_lock (.ps1 / .sh)

Acquires a file lock by creating a `.{filename}.lock` file in the same
directory as the target file, after verifying the target is contained
within the workspace root (H2/H4). Fails if the lock already exists or the
target escapes the root.

```text
PowerShell: scripts/acquire_lock.ps1 <filepath> [-WorkspaceRoot <path>]
Bash:       scripts/acquire_lock.sh <filepath> [--workspace-root <path>]
```

On success, prints `LOCK_TOKEN=<token>` to stdout — capture this value; it
is required to release the lock later (unless the operator uses `--force`).

The lock file contains:

* Agent or process identifier (`$env:AGENT_NAME` / `$AGENT_NAME` or `"unknown"`) — identity metadata only, not an ownership proof
* Timestamp (ISO 8601)
* PID of the calling process — identity metadata only, not an ownership proof
* `owner_digest`: SHA-256 digest of the capability token (the token itself is never stored)

### release_lock (.ps1 / .sh)

Releases a file lock by deleting the `.{filename}.lock` file, after
verifying the caller can prove ownership of it.

```text
PowerShell: scripts/release_lock.ps1 <filepath> [-Token <token>] [-Force]
Bash:       scripts/release_lock.sh <filepath> [--token <token>] [--force]
```

Refuses (non-zero exit, lock left in place) unless the supplied token's
digest matches the lock file's `owner_digest`, or `-Force`/`--force` is
given.

## Workflow

```text
1. Agent identifies file to modify
2. Agent runs: scripts/acquire_lock.{ps1|sh} <filepath>
   ├─ Exit 0 → lock acquired, capture LOCK_TOKEN=<token>, proceed to edit
   └─ Exit 1 → lock held (or path rejected), wait or prompt operator
3. Agent modifies the file
4. Agent verifies the modification (compile, test, etc.)
5. Agent runs: scripts/release_lock.{ps1|sh} <filepath> --token <token>
   ├─ Exit 0 → lock released
   └─ Non-zero → ownership could not be verified; surface to the operator
       rather than reaching for --force
```

## Lock Hygiene

* Locks are advisory, not enforced at the filesystem level (see "Honest
  bound" above).
* Lock files MUST NOT be committed to version control.
* Lock files older than 1 hour are likely stale — warn the operator.
* Only the operator may force-break a lock they did not create, via `--force`.
