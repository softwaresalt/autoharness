---
type: circuit-breaker
timestamp: 2026-09-18T02:57:00Z
agent: "Orchestrator"
skill: "direct"
breaker_type: universal
operation: "engram checkpoint provenance search"
attempts: 3
identity: "engram-content-record-missing-chunk-id"
---

# Circuit Breaker - Engram Checkpoint Provenance Search

## Failure Chain

### Attempt 1
- Exit/timeout: exit 1
- Operation evidence: `engram search`, workspace `C:\Source\GitHub\autoharness`, investigation phase, checkpoint filename target, `.engram/cozo/main/engram.db`
- Normalized message: Engram error 5001; stored relation `content_record` does not have field `chunk_id`.
- Diagnostic artifact: none

### Attempt 2
- Exit/timeout: exit 1
- Operation evidence: `engram search`, workspace `C:\Source\GitHub\autoharness`, investigation phase, Stage session ID target, `.engram/cozo/main/engram.db`
- Normalized message: Engram error 5001; stored relation `content_record` does not have field `chunk_id`.
- Diagnostic artifact: none

### Attempt 3
- Exit/timeout: exit 1
- Operation evidence: `engram query-memory`, workspace `C:\Source\GitHub\autoharness`, investigation phase, checkpoint-creation provenance target, `.engram/cozo/main/engram.db`
- Normalized message: Engram error 5001; stored relation `content_record` does not have field `chunk_id`.
- Diagnostic artifact: none

## Context
- Files involved: `.backlogit/checkpoints/checkpoint-20260916-064310.json`, `.engram/cozo/main/engram.db`
- Provisional-to-concrete identity link: All three calls returned the same concrete Engram error code and missing-field message; no provisional identity was needed.
- Logging controls: No raw output capture was written; this checkpoint contains only bounded, redacted command targets and normalized errors.
- Resolution: Circuit breaker triggered. Awaiting operator guidance.
- Suggested next steps: Diagnose the Engram content-record schema mismatch without rerunning unified search or query-memory in this session.
