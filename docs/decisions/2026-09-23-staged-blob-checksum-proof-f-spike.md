---
title: "Proof F - raw staged and HEAD checksum replay: findings (PASS)"
source: "docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md"
doc_type: decision
description: "Stage-authored Proof F findings under charter PE-1.1 section 6.8. Stage researched the established compound procedure read-only and recorded the verdict from Ship's verification-only replay evidence. The raw staged-blob digest captured by Python subprocess with binary stdout equals the post-commit HEAD-blob digest, and the combined Stage plus Ship time is inside the 30-minute bound, so Proof F is PASS. The PowerShell text-capture negative control reproduced the CRLF hazard; it is recorded, and it cannot fail the proof. Proof A remains BLOCKED."
docline:
  type: spike
  date: 2026-09-23
  time_box: "30m"
  conclusion: "proceed"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "checksum"
    - "staged-blob"
    - "crlf"
    - "proof-entry"
    - "ship-lifecycle"
proof: F
proof_verdict: PASS
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.1"
matrix_id: PE-1.1
matrix_rows: [PE-DATA-04]
branch: chore/stage-176-s-workflow-defects
head_at_authoring: 231a2e5a
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
actor_invoked: false
review_scheduled: false
backlog_item_created: false
---

# Proof F findings - raw staged and HEAD checksum replay

## Verdict

| Field | Value |
|---|---|
| Verdict | **`PASS`** |
| Pass criterion (charter section 6.8) | The staged digest equals the post-commit HEAD digest: **met** (identical SHA-256, below) |
| Time bound (charter section 6.1, 6.2) | 30m, Stage analysis and Ship execution together: **met** (see Time and File Bounds) |
| Negative control | Run and recorded. It reproduced the CRLF hazard. The negative control alone cannot fail the proof (charter section 6.8) |
| Matrix row | `PE-DATA-04` evidenced for proof entry (Proof F only; not a proof-exit audit) |
| Proof A | Remains **`BLOCKED`**, unchanged by this artifact (`docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md`) |

## Goal

Confirm that the established raw staged-blob checksum procedure replays
exactly, so the terminal activation task cannot improvise it. Charter section
6.8 states the proof carries no open question: it is a replay of
`docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`
section 1.

## Success Criteria

* **Pass**: the raw staged digest (`git cat-file -p :<path>`, Python
  subprocess, binary capture, SHA-256) equals the post-commit HEAD digest
  (`git cat-file -p HEAD:<path>`, same capture), and the combined Stage plus
  Ship elapsed time is at most 30 minutes.
* **Fail**: the raw staged digest differs from the HEAD digest after commit,
  or the time or file bound is exceeded (charter section 6.1).
* **Blocked**: a per-invocation gate rejected Ship's verification-only
  execution, or a required environment was unavailable.

## Scope Constraints

* Stage performed read-only static analysis only: no build, test suite,
  linter, fixture or fixture command (P-010; charter section 6.1).
* The only tracked change is this findings artifact. No source, config,
  agent, backlog, shipment, plan, review, charter or P-004 artifact changed.
* No claim, pull request, push, amend, plan revision 13 or review attempt 12.
* No additional worktree. The P-016 Stage spike worktree exception was not
  used.
* Scope stops at Proof F. No other proof is advanced.

## Session and Tool State

| Item | State |
|---|---|
| Backlog tool | backlogit MCP `TOOL_OK` (read-only version probe) |
| Stage checkpoints | 67 enumerated unfiltered, 0 quarantined, 0 needing quarantine, 0 active `stage`-owned: zero-candidate normal startup |
| Engram | Circuit open; not retried (operator instruction). `ENGRAM_DEGRADED` |
| Intercom | Unavailable. `INTERCOM_DEGRADED` |
| Graphtor-docs | Unavailable. `GRAPHTOR_UNAVAILABLE`; file-based reading of `docs/` used |
| Worktree at Stage start | `git status --porcelain` empty; one worktree; HEAD `231a2e5a` |

## Investigation Approach

1. Read the compound procedure verbatim
   (`docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`
   section 1).
2. Read charter section 6.8 (Proof F), section 6.1 (execution rules, time
   bound, verdict rules) and matrix row `PE-DATA-04` (section 7.7).
3. Compare Ship's reported commands and results with the normative
   procedure and with the pass and fail criteria. Stage did not re-run any
   command.

## Findings

### Normative Procedure (Compound Section 1)

The compound rule, quoted:

> any manifest-checksummed file edited on a Windows dev box MUST have its
> checksum computed via (a) or (b) above — both of which route through a
> subprocess capture of raw `.stdout` bytes, never a shell redirect (`>`,
> `Out-File`, or piping through a PowerShell console) at any stage of the
> pipeline.

Variant (b), the staged read, quoted:

> Always capture the staged blob as raw bytes through a subprocess call,
> exactly like variant (a), just with a colon-prefixed (`:<path>`, index/
> stage-0) ref instead of `HEAD:<path>`

The stated root cause is that PowerShell's pipe and redirect machinery
re-mangles LF git-blob output to CRLF on Windows.

### Evidence Provenance

All execution evidence below is Ship's verification-only invocation under
charter section 6.1. None of it is Stage execution. Stage records it as
reported and did not re-run it.

| Gate / fact | Ship-reported result |
|---|---|
| P-001 | Registered CLI, read-only: active shipment, task, feature and chore lists each `[]` |
| P-002 | Not applicable; no claim |
| P-011 | Initial `git status` empty; branch `chore/stage-176-s-workflow-defects` |
| P-016 | One worktree |
| Config route | Schema-valid; `gpt-6-luna` / `openai` / `xhigh` |
| Host | Windows 11 10.0.26200; Python 3.14.3; Git 2.55 (Windows); PowerShell 7.6.6 |
| Scratch | `.proof-scratch/proof-f-20260923-224540`, canonical path confirmed contained in the current working directory |
| Fixture | Independent `git init` repository inside scratch (not a worktree, not registered); local-only author; `core.autocrlf false`; one file `checksum-fixture.txt` |
| Exit status | Every exact command exited 0; no output redaction needed |
| Cleanup | Only the exact authorized scratch path removed |
| After | `git status` empty; HEAD unchanged at `231a2e5a`; one worktree; no production file touched |

One non-material note: an initial ephemeral config-validation command lacked
`import json` and was corrected before any proof evidence was taken. It is
not part of the replay and does not affect the verdict.

### Replay Result

| Step | Capture | Bytes | CRLF count | SHA-256 |
|---|---|---|---|---|
| Staged blob `:checksum-fixture.txt` after `git add` of an LF change | Python `subprocess.run([...], capture_output=True, text=False, check=True).stdout` | 15 | 0 | `b2cf96e60a865b57de4f3c867278d10f4dd16c69955c3c8c355beedf45f3aed8` |
| HEAD blob `HEAD:checksum-fixture.txt` after commit | Same binary subprocess capture | 15 | 0 | `b2cf96e60a865b57de4f3c867278d10f4dd16c69955c3c8c355beedf45f3aed8` |
| Negative control: PowerShell text capture (`git ... cat-file ... \| Out-String`) | PowerShell text pipeline, UTF-8 bytes | 17 | 2 | Not an admissible digest (hazard reproduced) |

The staged digest equals the HEAD digest byte-for-byte. The pass criterion
is met.

### Static Conformance to the Compound Procedure

| Compound requirement | Replay | Conforms |
|---|---|---|
| Raw `.stdout` bytes from a subprocess, never a shell redirect or PowerShell pipe | `text=False`, `capture_output=True`, hashed `.stdout` directly | Yes |
| Staged read uses the colon-prefixed stage-0 ref | `:checksum-fixture.txt` | Yes |
| HEAD read uses `HEAD:<path>` with the same capture | Yes, post-commit | Yes |
| `git add --renormalize` before the staged read | Plain `git add`. The compound ties renormalize to a `.gitattributes eol=lf` pin added in the same change; the fixture has no `.gitattributes` and sets `core.autocrlf false`, so renormalize would not change the index entry. Charter section 6.8 setup does not require it | Not material to this replay |
| Redirect or PowerShell capture is unsafe | Negative control reproduced the CRLF re-mangling (15 LF bytes became 17 bytes with 2 CRLF) | Hazard confirmed |

### Negative Control

The negative control reproduced the documented hazard. Charter section 6.8
requires only that it is run and recorded. **The negative control alone
cannot fail the proof.** Its result supports the compound rule that no
redirect-based or PowerShell text-capture variant is safe.

### Time and File Bounds

| Component | Elapsed |
|---|---|
| Ship invocation (reported; includes the 13m34s scratch execution) | 16m07s |
| Stage analysis and authoring (measured by host clock from 23:00:15 to the pre-commit check at 23:02:06, local time) | 1m51s |
| **Combined** | **17m58s**, within the 30m bound (Stage limit was under 13m53s) |

The Ship invocation figure is used rather than the shorter scratch-execution
figure, so the combined total is the conservative one. File bound (1 script,
disposable repository): Ship reported one fixture file in one disposable
repository, removed at cleanup, and no production file touched. No bound was
exceeded.

### Matrix Row Status (Proof F Only; Not a Proof-Exit Audit)

| Row | Criterion | Evidence | Status |
|---|---|---|---|
| `PE-DATA-04` | Proof F staged digest equals HEAD digest | Both digests in Replay Result, from Ship's transcript | Satisfied for proof entry |

### Remaining Unknowns

* Linux behavior is not part of Proof F (host: Windows). The digests are of
  raw blob bytes and are platform-independent by construction; no Linux claim
  is made here.
* The `--renormalize` step was not exercised because the fixture had no
  `eol=lf` pin. That path is established in the compound note and is not a
  Proof F question.

## Recommendation

Proceed. The terminal activation task must compute manifest checksums from
raw staged-blob bytes exactly as compound section 1 prescribes: Python
subprocess, binary capture, stage-0 `:<path>` ref, SHA-256 of `.stdout`,
with `git add --renormalize` first when an `eol=lf` pin is added in the same
change. No redirect or PowerShell text capture is permitted at any stage.

## Next Steps

* Record this verdict in the proof-exit report under charter section 8 when
  the portfolio closes.
* Proof A remains `BLOCKED` and routed as recorded in its own artifact.
* This session stops after Proof F. No other proof is advanced.

## References

* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (sections
  6.1, 6.2, 6.8, 7.7 row `PE-DATA-04`, 8)
* `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`
  (section 1)
* `docs/decisions/2026-09-23-p004-red-runner-proof-a-spike.md`
* `.github/skills/spike/SKILL.md`
* `.github/agents/_stage.agent.md`
* `.github/agents/_ship.agent.md`
* `.github/instructions/role-enforcement.instructions.md`
