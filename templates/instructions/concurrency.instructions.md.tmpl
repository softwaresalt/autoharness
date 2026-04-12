---
description: "File operation locking protocol — prevents concurrent modifications to the same file by multiple agents or human+agent workflows"
applyTo: '**'
---

# Concurrency Instructions

These rules prevent multiple agents (or an agent and a human operator) from
clobbering the same file during complex refactors or parallel work sessions.

## When Locking Is Required

Acquire file locks ONLY when concurrent file access is likely:

* Multiple agents are active on the same branch
* The operator has explicitly enabled concurrent-access mode
* The workspace uses the `agent-intercom` pack with multi-agent sessions
* A human operator is known to be editing files in the workspace concurrently

In single-agent, single-branch workflows (the common case), branch-level
isolation via Git provides sufficient concurrency safety. **Do not acquire
per-file locks in single-agent mode** unless one of the conditions above is met.

## Lock Protocol

### Before Modifying a Source File

When locking is required, the agent MUST acquire a lock before modification:

1. Execute the lock script for the current platform:
   * PowerShell: `scripts/acquire_lock.ps1 <filepath>`
   * Bash: `scripts/acquire_lock.sh <filepath>`
   where `<filepath>` is the path to the file, relative to the workspace root.
2. If the script exits with code **0**, the lock is acquired. Proceed.
3. If the script exits with a **non-zero** code, the file is already locked.
   The agent MUST NOT modify the file. Instead:
   * Wait briefly (one cycle) and retry once.
   * If the retry also fails, count it as a session stall (per
     `circuit-breaker.instructions.md`) and prompt the operator:
     `File lock conflict on <filepath>. Another process holds the lock. Please resolve.`

### After Completing the Modification

After modifying the file and verifying the result (compilation, tests, etc.),
release the lock:

1. PowerShell: `scripts/release_lock.ps1 <filepath>`
   Bash: `scripts/release_lock.sh <filepath>`
2. If the release fails, log a warning but do not halt — stale locks are
   recoverable.

### Lock Scope

* Locks are per-file, not per-directory.
* Lock files are created as `.<filename>.lock` in the same directory as
  the target file.
* Lock files contain the agent name, timestamp, and process context for
  diagnostic purposes.

## Rules

1. **Lock only when concurrent access is likely.** Do not lock in
   single-agent, single-branch workflows.
2. **Release promptly.** Do not hold locks across unrelated operations.
   Acquire immediately before the edit, release immediately after
   verification.
3. **Do not force-break locks.** If a lock exists, only the operator may
   decide to break it. Agents MUST NOT delete lock files they did not create.
4. **Lock files are ephemeral.** They MUST NOT be committed to version
   control. The workspace `.gitignore` should include `.*.lock` entries
   (or `**/.*.lock` for an explicit recursive pattern) for agent lock files.

## Recovery

If an agent session terminates abnormally and leaves stale locks:

* The operator can remove `.*.lock` files manually.
* The next agent session should check lock file timestamps and warn if
  any lock is older than 1 hour — it is likely stale.
