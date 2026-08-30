---
description: "Circuit breaker protocol — prevents agents from entering infinite retry loops on persistent failures"
applyTo: '**'
---

# Circuit Breaker Instructions

These rules prevent agents from spinning indefinitely when a task, command,
tool invocation, file generation, or repair cycle repeatedly fails. Every agent
in this workspace MUST observe these limits.

## Universal Retry Threshold

**MAXIMUM_RETRY_THRESHOLD = 3.**

The threshold is exactly three counted failures for the same operation.

* Count every non-zero native process exit, tool failure, validation failure,
  and timeout immediately when it is observed. Do not wait for a later
  diagnostic step before incrementing the counter.
* If any single operation (command execution, code fix attempt, file
  generation, tool invocation, or equivalent workflow action) fails three
  counted times with substantially the same error, the agent MUST STOP
  executing that operation immediately.
* Agents MUST NOT make a fourth attempt for the same operation after the third
  counted same-operation failure. A re-run with cosmetic argument changes,
  higher verbosity, a different transport, a new shell, or a different model is
  still a retry when it targets the same operation.
* A pause, cooldown, context compaction, model switch, shell restart, worktree
  switch, or parallel work item MUST NOT reset the same-operation counter. No
  reset, pause, parallel counter, or fourth run exists for a tripped
  same-operation circuit.

### Same-Operation Identity and Hidden Details

Agents MUST classify failures conservatively when deciding whether attempts are
substantially the same operation.

* Use the normalized command or tool name, target, working directory, workflow
  phase, allowlisted non-secret environment key names, and redacted or
  one-way-digested non-secret values as the baseline operation identity. Never
  fingerprint or persist the environment wholesale, secret-bearing values, or
  raw command payloads.
* When output truncation hides the concrete failure details, same-operation
  identity MAY be provisional. Compute a provisional same-operation fingerprint
  from only the safe baseline signals above. While details remain hidden,
  another failed invocation with that fingerprint counts against the same
  operation.
* Once concrete details are observable, record identity from native process exit
  or timeout, stable target/code, normalized message, affected path, workflow
  phase, and links to any already captured diagnostic evidence.
* Escalation records MUST link each counted attempt to concrete operation evidence without recounting prior attempts. Linking provisional attempts to a
  later concrete identity is bookkeeping only; it never restarts the threshold.
* Hidden output cannot create the different-error exception. Only a genuinely
  different observable error, with distinct stable evidence, may break the
  same-error chain and continue a skill-managed exploration loop.
* Attempt-three evidence may be inspected without re-execution. Inspecting logs,
  summaries, or already captured diagnostics is not another attempt and MUST NOT
  authorize a fourth attempt.

### Counted Diagnostic Transport

Changing diagnostic transport is allowed only below the threshold and only as
the next counted attempt.

* If the current same-operation count is 1 or 2 and truncation or transport
  limits hide details, the agent MAY change diagnostic transport on the next
  counted diagnostic invocation, such as using a narrower target, structured
  output, or a bounded log capture.
* The next counted diagnostic consumes the next attempt. Assign its attempt
  number before execution. If it returns non-zero or times out, increment the
  same-operation counter immediately. A zero exit MUST NOT erase prior counted
  failures. It closes the chain only when it directly verifies that the same
  operation succeeded.
* Diagnostic escalation is never a side channel, preflight replay, parallel
  counter, reset, or free probe. If the next counted diagnostic is attempt
  three and observes the same operation failing, the circuit trips.
* Preserve the native exit status separately from captured output. Masking or
  replacing the native exit status does not create a successful attempt.
* After diagnosis or success, diagnostic verbosity MUST return to normal
  logging with immediate de-escalation.

### Skill-Managed Loop Exception

Skills that define their own loop limits (build-feature: 5, fix-ci: 5) take
precedence over the universal threshold **only for genuinely different
observable errors within their loop scope**. The universal threshold applies to
all operations outside skill-managed loops.

When operating inside a skill-managed loop:

* Follow the skill's documented attempt limit (e.g., 5 for build-feature) while
  each failure is a genuinely different observable error with distinct evidence.
* If the same error recurs on the third counted same-operation attempt within
  the loop, the universal circuit breaker applies: STOP and escalate. The
  skill's larger loop limit does not permit attempt four for the same operation.
* Hidden or truncated output does not prove a different error. Use provisional
  same-operation identity until concrete observable evidence distinguishes the
  failure.
* When the skill loop completes (success or breaker trip), the universal
  threshold governs all subsequent operations.

## Escalation Protocol

Upon hitting the retry threshold (universal or skill-managed):

1. **Stop** — do not attempt the operation again, do not schedule a post-trip
   probe, and do not route the same operation through a parallel counter.
2. **Log** — record the failure chain as a session memory checkpoint at
   `docs/memory/{YYYY-MM-DD}/circuit-break-{operation-slug}.md`.
   All workspace logs MUST be bounded and follow these controls:
   * Canonicalize the workspace root and candidate diagnostics path before any
     raw capture.
   * Write workspace diagnostics only below an ignored `logs/diagnostics/` path
     after verifying the ignore rule and confirming the canonicalized
     diagnostics path stays inside the canonicalized workspace root.
   * If canonicalization fails, or the resolved diagnostics path escapes the
     workspace root (including through a symlink/junction/reparse point),
     omit the raw capture and retain only the bounded, redacted checkpoint
     evidence below. Never write captures outside the workspace.
   * Capture combined stdout and stderr only up to 1 MiB or 10,000 lines,
     whichever is reached first, and never beyond the command timeout. Preserve
     the native exit status separately.
   * Inspect at most the final 64 KiB or 500 lines, or a smaller identified
     failure block.
   * Persist only a redacted summary and evidence link; exclude secrets,
     credentials, tokens, sensitive output, raw payload content, and raw
     environment values.
   * Apply bounded extraction retention: retain the ignored raw capture only for
     the active diagnostic session, then use the repository-approved log
     disposition path. A memory checkpoint retains only the redacted excerpt,
     hash, and limits used.
   Each entry MUST include:
   * Timestamp (ISO 8601)
   * Operation that failed
   * Attempt count
   * For each attempt: native process exit code or timeout marker, normalized
     command/tool target, cwd, workflow phase, stable target/code, normalized
     message, affected path, and diagnostic-evidence link
   * Whether an identity was provisional and how it was linked to concrete
     evidence without recounting prior attempts
   * Files involved
   * Agent and skill context
   * Whether this was a universal or skill-managed breaker trip
3. **Prompt** — surface the following message to the operator:
   `Circuit breaker triggered after {N} consecutive failures. Details: docs/memory/{filename}. Please advise.`
4. **Checkpoint** — write a memory checkpoint so session state is preserved if
   the operator decides to restart or reassign.
5. **De-escalate diagnostics** — After diagnosis or success, diagnostic
   verbosity MUST return to normal logging with immediate de-escalation. Do not
   keep high-volume capture, expanded tracing, or diagnostic transports enabled
   beyond the bounded diagnosis window.

## Domain-Specific Limits

These limits supplement the universal threshold. The most specific applicable
limit governs, but same-operation attempt three still trips the universal
breaker.

| Counter                                     | Limit | Action on breach                                    |
|---------------------------------------------|-------|-----------------------------------------------------|
| Build/test fix attempts per task            | 5     | Mark task `blocked`, exit loop (skill-managed) |
| Same-error recurrence within skill loop     | 3     | Universal breaker applies on attempt 3: stop, log, prompt |
| Consecutive same-check failures in fix-ci   | 3     | Halt fix-ci, report check stability issue           |
| Total fix-ci cycles per PR                  | 5     | Halt, leave PR open for manual intervention (skill-managed) |
| Consecutive task failures                   | 3     | Halt session, prompt operator for guidance          |
| Review-fix cycles per task                  | 3     | Accept remaining findings as backlog items, move on |
| Tasks attempted in session                  | 20    | Halt, write memory checkpoint, exit session         |
| Session stalls                              | 3     | Halt, write checkpoint, prompt operator             |

## Cooldown Delay (No Auto-Reset)

For transient below-threshold failures where the underlying cause is likely to
resolve automatically (network hiccups, temporary tool unavailability,
short-lived rate limit windows), agents MAY delay the next invocation by up to
5 minutes before consuming the next attempt.

Cooldown is only a delay before a below-threshold next counted attempt:

1. Cooldown MAY be used only while the same-operation count is 1 or 2.
2. The delayed invocation is still the next counted diagnostic or normal retry,
   and it consumes the next attempt when executed.
3. Cooldown MUST NOT reset the same-operation counter, reclassify prior
   failures, create a parallel counter, or authorize a free probe.
4. After the third counted same-operation failure, cooldown MUST NOT reset/retry
   a tripped same-operation circuit. There is no post-trip probe and no fourth
   attempt.
5. A pause for cooldown does not change operation identity; if the same
   operation fails again, count it immediately.

Cooldown is appropriate only when:

* the operation is non-critical,
* the current count is still below the threshold,
* the failures match transient conditions such as timeouts or temporary tool
  unavailability, and
* unattended delay is preferable to immediate operator escalation.

Cooldown is **not** appropriate when:

* the threshold has already tripped,
* the failure indicates a logic or contract problem (wrong arguments, auth
  failure, schema mismatch),
* the operation is a mandatory gate (for example: index sync, shipment claim,
  PR merge readiness), or
* repeated trips show the condition is not transient.

**Out of scope:** SDK-style minimum-interval throttles and hourly query budgets
are separate rate-limiting patterns, not part of this universal circuit breaker
template.

### Review-Fix Cycle Definition

A review-fix cycle is one complete iteration of: (1) invoke review skill →
(2) parse findings → (3) apply fixes. Cycle counting starts at 0 (first review).
After 3 fix cycles: every remaining finding that FAILS the P-021 C1
same-contract-surface test (below) is captured as a new backlog item — a
P-021 C2 `DEFERRED SCOPE EXPANSION` entry, not an informal note — before the
task is committed and moved to `done`. A finding that PASSES C1 and
remains unresolved SOLELY because this 3-cycle budget is exhausted is
different: per the Symmetric guard below, it is never captured as a deferred
scope expansion (it was never out of scope) and it MUST NOT be silently closed
as a backlog item either — halt the task instead and escalate that in-scope
finding to the operator for explicit disposition (extend the cycle-count
limit, or explicitly accept documented residual risk).

**Scope bound (P-021 C1)**: the 3-cycle count above bounds HOW MANY cycles are
permitted; it does not by itself bound WHAT may be fixed within a cycle. Every
finding raised during a review-fix cycle MUST also pass the P-021 C1
same-contract-surface test before it is fixed: a finding is in scope ONLY if
fixing it requires ONLY completing the exact change already authorized — the
same contract surface. `same file`, `same function`, `same PR`, `same
subsystem`, and `related` are NOT sufficient to put a finding in scope on
their own. Genuine ambiguity resolves OUT of scope — this is the fail-safe
default, not an exception to it.

Three worked discrimination cases (provenance:
`docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`):

* A finding that the shared-instruction verifier is missing the new field →
  **same surface** (the field itself) → fix it.
* A finding that a regex does not handle an object-separated form → **different
  surface** (matcher robustness, not the new field) → defer, even though it is
  in the exact same function, file, and PR, and was itself in scope for an
  earlier authorized cycle.
* A finding that a policy interaction is unresolved → **different surface and a
  different kind of work** (design/decision work, not a mechanical fix) →
  defer.

**Capture requirement (P-021 C2)**: an out-of-scope finding MUST be captured as
a `DEFERRED SCOPE EXPANSION` stash entry before the finding is closed in any
form — capture is never conditional on a PR or thread existing.

**Symmetric guard (P-021 C3)**: (i) a same-contract-surface completion of the
authorized change IS in scope and MUST be fixed, not deferred; AND (ii)
deferring such a completion WITHOUT a captured entry AND a residual-risk
record is itself a P-021 violation, actioned per P-021 C7.

**Cycle-limit disposition (P-021 C3, hardening H14)**: this is exactly the
cycle-limit disposition described in the Review-Fix Cycle Definition above —
the capture-as-backlog-item action attaches only to C1-failing findings, never
to an unresolved in-scope one, which halts and escalates to the operator
instead.

These scope rules narrow WHAT is fixed inside a cycle; they do not relax, widen,
or otherwise alter the 3-cycle count semantics above.

## Stall Detection

Commands that exceed their timeout are counted as failures:

| Command type       | Timeout    |
|--------------------|------------|
| Build/test         | 45 minutes |
| Other commands     | 5 minutes  |

If a command exceeds its timeout, terminate the process and count it as one
failed attempt toward the retry threshold immediately. The timeout marker is
part of the same-operation evidence, just like a native process exit code.

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
timestamp, and the action that was blocked. Stall diagnostics follow the same
workspace-log bounds, redaction, raw-payload exclusion, bounded extraction
retention, and immediate de-escalation rules as other breaker diagnostics.

## Anti-Pattern Recognition

Agents MUST NOT attempt to work around the circuit breaker by:

* Restarting the same operation with trivial or cosmetic changes
* Splitting the same failing operation into sub-operations that reproduce the
  same error
* Ignoring, suppressing, or discarding error output to avoid incrementing the
  counter
* Piping, wrapping, or otherwise masking a failing command so its native exit
  status is replaced by a successful helper or shell exit
* Treating hidden or truncated output as proof of a different error
* Resetting attempt counters without explicit operator approval for a genuinely
  new operation
* Moving the same operation to another shell, model, worktree, diagnostic
  transport, pause, or parallel workflow to bypass the threshold
* Running a post-trip probe, auto-reset retry, or fourth attempt for the same
  operation

## Log Format

Each circuit breaker checkpoint in `docs/memory/` follows this structure.
Keep captured output within the explicit limits above and redacted; include
summaries or links to ignored bounded artifacts rather than full raw output.

**YAML-safe scalar encoding (REQUIRED).** The four free-form frontmatter
values below — `agent`, `skill`, `operation`, and `identity` — MUST be
emitted as **JSON string literals** (the exact output of a JSON string
encoder, e.g. Python's `json.dumps(value)`), never as a bare value wrapped
in naive double quotes. YAML 1.2 double-quoted scalars share JSON's escape
rules, so a JSON-encoded string is always valid YAML — but naive
double-quoting is NOT equivalent and fails on an embedded double quote, an
embedded backslash, or a trailing backslash. For example, if `skill` is the
plain text `direct`, its JSON string literal is `"direct"`; if `skill` is
`read "config" file`, the JSON string literal is `"read \"config\" file"` —
never `""read "config" file""`. Always compute the JSON string literal; do
not copy an example's bare-quote appearance literally.

```markdown
---
type: circuit-breaker
timestamp: {ISO 8601}
agent: {JSON string literal, e.g. "Ship"}
skill: {JSON string literal, e.g. "direct" or "read \"config\" file"}
breaker_type: {universal | skill-managed | session-stall}
operation: {JSON string literal, e.g. "uv build"}
attempts: {count}
identity: {JSON string literal, e.g. "provisional-fingerprint-1"}
---

# Circuit Breaker - {operation}

## Failure Chain

### Attempt 1
- Exit/timeout: {native process exit code or timeout marker}
- Operation evidence: {command/tool target, cwd, phase, stable target/code, path}
- Normalized message: {bounded redacted summary}
- Diagnostic artifact: {bounded redacted link or "none"}

### Attempt 2
- Exit/timeout: {native process exit code or timeout marker}
- Operation evidence: {command/tool target, cwd, phase, stable target/code, path}
- Normalized message: {bounded redacted summary}
- Diagnostic artifact: {bounded redacted link or "none"}

### Attempt 3
- Exit/timeout: {native process exit code or timeout marker}
- Operation evidence: {command/tool target, cwd, phase, stable target/code, path}
- Normalized message: {bounded redacted summary}
- Diagnostic artifact: {bounded redacted link or "none"}

## Context
- Files involved: {list}
- Provisional-to-concrete identity link: {how attempts were linked without recounting}
- Logging controls: {byte limit, line limit, time limit, redaction, retention}
- Resolution: Circuit breaker triggered. Awaiting operator guidance.
- Suggested next steps: {if any}
```

### Frontmatter YAML-Safety Regression Cases

Each case below MUST be verified against a YAML parser (e.g. Python's
`yaml.safe_load`, which implements YAML 1.1 scalar-scanning rules; the
double-quoted-scalar escape semantics and the plain-scalar `#`/`: ` hazards
exercised here behave identically under YAML 1.1 and YAML 1.2, so this is
not a 1.2-specific claim): the encoded frontmatter value MUST (i) **parse**
without error and (ii) **round-trip** — the parsed field value MUST equal
the original raw value byte-for-byte. A value that parses but decodes to a
different string (silent truncation) is a REGRESSION FAILURE, not a pass;
this is the failure mode already observed in the wild for the space-hash
case, and a parse-only assertion does not catch it.

| Hazard class | Raw value | JSON string literal | Bare/unquoted (currently shipping) | Naive bare-double-quote | JSON-escaped |
|---|---|---|---|---|---|
| Embedded double quote | `say "hi"` | `"say \"hi\""` | parses, round-trips | PARSE-FAIL | parses, round-trips |
| Embedded backslash | `C:\path\file` | `"C:\\path\\file"` | parses, round-trips | PARSE-FAIL | parses, round-trips |
| Trailing backslash | `ends\` | `"ends\\"` | parses, round-trips | PARSE-FAIL | parses, round-trips |
| Colon-space | `key: value` | `"key: value"` | PARSE-FAIL | parses, round-trips | parses, round-trips |
| Space-hash | `note #1` | `"note #1"` | parses, silently truncates to `note` | parses, round-trips | parses, round-trips |

All four hazard classes (embedded double quote, embedded/trailing backslash,
colon-space, space-hash) MUST be covered by regression evidence before this
checkpoint format is considered hardened -- the table above has five rows
because embedded backslash and trailing backslash are two concrete test
values of the same backslash-escaping hazard class. Only the JSON-escaped
form both parses and round-trips across every row; the currently-shipping
bare/unquoted form fails two of five (parse-fail on colon-space, silent
truncation on space-hash -- the exact failure already observed in the wild),
and naive bare-double-quoting alone still fails three of five (embedded
quote, embedded backslash, trailing backslash).
