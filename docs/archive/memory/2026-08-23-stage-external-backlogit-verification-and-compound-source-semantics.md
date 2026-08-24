---
title: "Stage session 2026-08-23 - external backlogit fix verification + docs/compound source value semantics"
date: 2026-08-23
source: "docs/memory/2026-08-23-stage-external-backlogit-verification-and-compound-source-semantics.md"
doc_type: "reference"
agent: stage
route: "claude-opus-5 / anthropic / high"
mode: dark-factory
---

# Stage Session Memory - 2026-08-23

Scope (operator-bounded, exact and exclusive): stash IDs `3C7AAC71`,
`90F2A9F8`, `B57F9E24`, `FAE1E7B7`, plus queued deliberations `024-DL` and
`025-DL`. `merge_approval_pre_authorized=false`,
`admin_fallback_pre_authorized=false`, agent-intercom unavailable (local CLI
visibility only).

## Outcome

Stage completed cleanly. No stop condition fired. No P-001 / P-009 / P-014 /
P-016 / P-017 / P-020 / P-021 boundary was crossed. No source, template, test
or config file was modified; no branch, commit or PR was created; no build,
test suite or linter was run; no shipment was claimed.

## Disposition of the six scoped IDs

| ID | Disposition |
| --- | --- |
| `3C7AAC71` | FIXED UPSTREAM (backlogit 146-F, PR #374, `b0772938`). Evidence recorded in the entry; ARCHIVED |
| `90F2A9F8` | FIXED UPSTREAM (same feature; the exact report-and-continue behaviour the entry argued for). Evidence recorded; ARCHIVED |
| `B57F9E24` | **NOT FIXED.** Root cause newly identified; precise unblocker recorded; priority raised medium -> high; REMAINS ACTIVE |
| `FAE1E7B7` | Deliberated (`026-DL`), planned, reviewed PASS, harvested to `146-F` / `154-S`; CONSUMED and ARCHIVED |
| `024-DL` | RESOLVED-AND-DELIVERED (141-F/149-S, 143-F/151-S, 144-F/152-S, 145-F/153-S). Terminal outcome record appended; ARCHIVED |
| `025-DL` | RESOLVED-AND-DELIVERED (140-F/148-S). Terminal outcome record appended; residual handed to `026-DL`; ARCHIVED |

## External verification method

`C:\Source\GitHub\backlogit` was used READ-ONLY. Engram was bound and healthy
for that workspace (`ENGRAM_OK`: 640 code files, 4489 edges, scan complete,
`stale_files: false`) after one failed daemon start followed by a successful
`engram --workspace ... bind`. All unified-search / symbol / code-graph
operations went through the engram CLI per operator preference; direct reads
were confined to exact known paths surfaced by those searches. No writes, no
build, no test run, no mutating workflow in that repository.

Key discriminator: the installed `backlogit 1.10.1-0.20260823032255-b07729386a31`
is built from repo HEAD `b0772938` (`v1.10.0-49`), so upstream code state and
runtime behaviour are the same thing here.

## The one still-open defect, with its newly identified mechanism

`B57F9E24` is a **V1-probe misclassification** in
`internal/events/memory.go:CreateCheckpoint`, NOT a file-writer defect
(`internal/events/fsutil.go:70 syncWriteFileAtomic` has been a correct
temp+fsync+rename since 2026-04-22 and predates the observation).

A truncated `schema_version: 1` payload fails `json.Unmarshal`, so the V1 guard
is false, so the function reclassifies it as LEGACY and writes the raw bytes
verbatim with no parse check, no validation and no size bound - returning
success. The installed CLI's own help states the rule: *"A dump without
schema_version=1 (legacy) is written verbatim with no schema validation."*

Confirmed against the preserved artifact
`.backlogit/archive/checkpoints/checkpoint-20260821-203531.json`: it is COMPACT
JSON, which is the tell, because the V1 branch re-marshals through
`jsonutil.MarshalReadable` (pretty). A compact torn file proves the legacy
fall-through.

Preferred upstream fix: make the probe FAIL CLOSED by distinguishing "no
`schema_version` field" from "unparseable bytes", returning an error on a JSON
syntax error instead of silently reclassifying.

## Decisions recorded

* `FAE1E7B7` joins `025-DL`'s docline contract surface as the **SAME CONTRACT
  SURFACE but a SEPARATE SUCCESSOR FEATURE** - `140-F` is archived and `148-S`
  shipped, so a closed acceptance record cannot absorb new work.
* `140.001-T` AC3 (verbatim frontmatter preservation) is **preserved and not
  amended**. It constrained what that task could do; it is satisfied and merged;
  the correction proceeds under a new authorization. The displaced provenance
  string is preserved verbatim in `citations`, so the change relocates value
  rather than destroying it.
* 025-DL's R3/R4/R5/R6 carried forward as binding constraints.
* ONE shipment, not a serial chain: all three tasks share one contract surface,
  one review, and a combined estimate under one session. No conditional branch
  of the kind that forced 024-DL's 149-S -> 151-S split exists here.

## Artifacts created

* Deliberation `026-DL`
* `docs/plans/2026-08-23-docs-compound-source-value-semantics-plan.md`
* `docs/reviews/2026-08-23-docs-compound-source-value-semantics-review.md`
  (PASS; 3 P1 + 2 P2, all resolved by binding amendments A1-A5; 0 unresolved
  P0/P1; 1 of 3 cycles used)
* Feature `146-F`; tasks `146.001-T` (XS/low), `146.002-T` (S/medium),
  `146.003-T` (XS/low); shipment `154-S` (queued)

## Next steps

1. Ship claims `154-S` and executes `146.001-T` -> `146.002-T` -> `146.003-T`
   in dependency order.
2. `B57F9E24` stays active; re-check on the next backlogit upgrade past
   `b0772938`.
3. Operator decisions outstanding (NOT actioned - out of scope): whether to
   capture a checkpoint size-bound rule in the autoharness Checkpoint Payload
   Contract, and whether active entry `E0B80A6C` should be prioritised given it
   sits on the same causal pathway as `B57F9E24`.

## Dirty-worktree note

The worktree was already dirty at activation with pre-existing operator/tool
changes (archive/checkpoint moves and deletions, `.mcp.json`, `023-DL` archive
and log artifacts). All were preserved; none were reverted, overwritten,
committed or conflated with this session's work. They blocked no gate. This
session's own writes are additive: three new documents plus backlogit-managed
backlog and stash state.
