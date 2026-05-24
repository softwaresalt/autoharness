---
description: "Circuit breaker protocol — prevents agents from entering infinite retry loops on persistent failures"
applyTo: '**'
---

# Circuit Breaker Instructions

These rules prevent agents from spinning indefinitely when a task, command,
or repair cycle repeatedly fails. Every agent in this workspace MUST observe
these limits.

## Universal Retry Threshold

**MAXIMUM_RETRY_THRESHOLD = 3.**

If any single operation (command execution, code fix attempt, file generation,
tool invocation) fails **3 consecutive times** with substantially the same
error, the agent MUST STOP executing that operation immediately.

### Skill-Managed Loop Exception

Skills that define their own loop limits (build-feature: 5, fix-ci: 5) take
precedence over the universal threshold **within their loop scope**. The
universal threshold applies to all operations outside skill-managed loops.

When operating inside a skill-managed loop:

* Follow the skill's documented attempt limit (e.g., 5 for build-feature).
* If the **same error** recurs on attempts 3+ within the loop, the universal
  circuit breaker applies: STOP and escalate. Different errors on each attempt
  indicate genuine exploration and may continue to the skill's limit.
* When the skill loop completes (success or breaker trip), the universal
  threshold governs all subsequent operations.

## Escalation Protocol

Upon hitting the retry threshold (universal or skill-managed):

1. **Stop** — do not attempt the operation again.
2. **Log** — record the failure chain as a session memory checkpoint at
   `docs/memory/{YYYY-MM-DD}/circuit-break-{operation-slug}.md`.
   Each entry MUST include:
   * Timestamp (ISO 8601)
   * Operation that failed
   * Attempt count
   * Error output or summary for each attempt
   * Files involved
   * Agent and skill context
   * Whether this was a universal or skill-managed breaker trip
3. **Prompt** — surface the following message to the operator:
   `Circuit breaker triggered after {N} consecutive failures. Details: docs/memory/{filename}. Please advise.`
4. **Checkpoint** — write a memory checkpoint so session state is preserved
   if the operator decides to restart or reassign.

## Domain-Specific Limits

These limits supplement the universal threshold. The most specific applicable
limit governs.

| Counter                                     | Limit | Action on breach                                    |
|---------------------------------------------|-------|-----------------------------------------------------|
| Build/test fix attempts per task            | 5     | Mark task `blocked`, exit loop (skill-managed) |
| Same-error recurrence within skill loop     | 3     | Universal breaker applies: stop, log, prompt        |
| Consecutive same-check failures in fix-ci   | 3     | Halt fix-ci, report check stability issue           |
| Total fix-ci cycles per PR                  | 5     | Halt, leave PR open for manual intervention (skill-managed) |
| Consecutive task failures                   | 3     | Halt session, prompt operator for guidance           |
| Review-fix cycles per task                  | 3     | Accept remaining findings as backlog items, move on  |
| Tasks attempted in session                  | 20    | Halt, write memory checkpoint, exit session          |
| Session stalls                              | 3     | Halt, write checkpoint, prompt operator              |

## Cooldown and Auto-Reset (Optional)

For transient failures where the underlying cause is likely to resolve
automatically (network hiccups, temporary tool unavailability, short-lived rate
limit windows), agents MAY use a time-bounded cooldown before escalating to the
operator immediately.

1. On circuit trip, record `circuit_open_until = now + 5 minutes`.
2. While `now < circuit_open_until`, return early in degraded mode rather than
   repeatedly retrying the failing operation.
3. When the cooldown expires, auto-reset the circuit state and allow **one**
   retry.
4. If that retry fails and re-trips the breaker, start a fresh cooldown window.
5. After **3 circuit trips** for the same operation in one session, stop
   auto-resetting and escalate to the operator.

Cooldown is appropriate when:

* the operation is non-critical
* the failures match transient conditions such as timeouts or temporary tool
  unavailability
* unattended recovery is preferable to indefinite waiting

Cooldown is **not** appropriate when:

* the failure indicates a logic or contract problem (wrong arguments, auth
  failure, schema mismatch)
* the operation is a mandatory gate (for example: index sync, shipment claim,
  PR merge readiness)
* repeated trips show the condition is not transient

**Out of scope:** SDK-style minimum-interval throttles and hourly query budgets
are separate rate-limiting patterns, not part of this universal circuit breaker
template.

### Review-Fix Cycle Definition

A review-fix cycle is one complete iteration of: (1) invoke review skill →
(2) parse findings → (3) apply fixes. Cycle counting starts at 0 (first review).
After 3 fix cycles, accept remaining P2/P3 findings as new backlog items,
commit the task, and move it to `done`.

## Stall Detection

Commands that exceed their timeout are counted as failures:

| Command type       | Timeout   |
|--------------------|-----------|
| Build/test         | 45 minutes|
| Other commands     | 5 minutes |

If a command exceeds its timeout, terminate the process and count it as
one failed attempt toward the retry threshold.

### Session Stall Counting

A **session stall** occurs when the agent encounters a blocking condition that
prevents forward progress. The session stall counter increments when:

1. A command exceeds its timeout (build/test: 45 min, other: 5 min)
2. A file lock acquisition blocks and the retry also fails (per concurrency protocol)
3. A required tool or MCP surface becomes unavailable mid-session
4. An agent-intercom heartbeat ping fails (when the pack is enabled)

After 3 session stalls in a single session, the agent MUST halt execution,
write a session checkpoint to `docs/memory/`, and prompt the operator:

`Session stall limit (3) reached. Environment may be unstable. Please investigate.`

Each stall MUST be logged in the circuit breaker checkpoint with the stall type,
timestamp, and the action that was blocked.

## Anti-Pattern Recognition

Agents MUST NOT attempt to work around the circuit breaker by:

* Restarting the same operation with trivial or cosmetic changes
* Splitting the same failing operation into sub-operations that reproduce
  the same error
* Ignoring or suppressing error output to avoid incrementing the counter
* Resetting attempt counters without operator approval

## Log Format

Each circuit breaker checkpoint in `docs/memory/` follows this structure:

```markdown
---
type: circuit-breaker
timestamp: {ISO 8601}
agent: {agent name}
skill: {skill name or "direct"}
breaker_type: {universal | skill-managed | session-stall}
operation: {brief description}
attempts: {count}
---

## Failure Chain

### Attempt 1
{error output}

### Attempt 2
{error output}

### Attempt 3
{error output}

## Context
- Files involved: {list}
- Resolution: Circuit breaker triggered. Awaiting operator guidance.
- Suggested next steps: {if any}
```
