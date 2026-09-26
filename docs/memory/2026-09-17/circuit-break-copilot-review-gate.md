---
type: circuit-breaker
timestamp: 2026-09-17T22:46:01Z
agent: "Orchestrator"
skill: "pr-lifecycle"
breaker_type: universal
operation: "autoharness gate copilot-review 456"
attempts: 3
identity: "copilot-review-456-current-head-waiting"
---

# Circuit Breaker - Copilot Review Gate

## Failure Chain

### Attempt 1

- Exit/timeout: exit 1
- Operation evidence: `autoharness gate copilot-review 456 --repo softwaresalt/autoharness --enforcement auto`; workspace root; PR readiness phase; PR #456; reviewed HEAD `4b1efd852e0bf4f4bf85e6cb3ae2da951a1b7d0e`
- Normalized message: `WAITING_FOR_REVIEW`; Copilot is requested but has not completed a review for the current HEAD.
- Diagnostic artifact: shell session 404

### Attempt 2

- Exit/timeout: exit 1
- Operation evidence: same gate and target after the first two-minute review interval
- Normalized message: `WAITING_FOR_REVIEW`; no completed current-HEAD Copilot review.
- Diagnostic artifact: shell session 405

### Attempt 3

- Exit/timeout: exit 1
- Operation evidence: same gate and target after the second two-minute review interval
- Normalized message: `WAITING_FOR_REVIEW`; no completed current-HEAD Copilot review.
- Diagnostic artifact: shell session 406

## Context

- Files involved: none; remote PR gate for `https://github.com/softwaresalt/autoharness/pull/456`
- Provisional-to-concrete identity link: all attempts targeted the same PR, reviewed HEAD, enforcement mode, and gate verdict.
- Logging controls: bounded summaries only; no raw payloads, environment values, credentials, or API responses persisted.
- Resolution: Circuit breaker triggered. PR remains open; no merge attempt was made.
- Suggested next steps: wait for Copilot to complete its current-HEAD review, then run the gate once after explicit operator continuation.
