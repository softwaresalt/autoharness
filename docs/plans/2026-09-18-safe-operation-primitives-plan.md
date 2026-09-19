---
title: "Foundation: safe operation primitives — atomic write, path containment, fixed-argv exec, bounded reader"
description: "Builds the four security and integrity primitives every safe operation composes from: an atomic write using temp-in-destination plus fsync plus os.replace, a path containment resolver rejecting every escape from a declared workspace root, a fixed-argv subprocess runner with a per-operation executable allowlist and no shell anywhere, and a bounded JSON reader returning a typed quarantine record rather than raising. Each ships RED-first. Pinned against the full 134-record live checkpoint corpus including the two observed torn records."
doc_type: plan
source: docs/plans/2026-09-18-safe-operation-primitives-plan.md
date: 2026-09-18
plan_id: safe-operation-primitives
plan_path: docs/plans/2026-09-18-safe-operation-primitives-plan.md
plan_role: active
revision: 1
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document authored under the strategic redesign, not a remediation of a prior revision. It carries REMEDIATED-PENDING-REVIEW because it awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-safe-operation-primitives-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 86498B64
  - 14F4D6F3
  - 71200CBB
  - C9CD24F3
merged_stash_ids:
  - 14F4D6F3
feature_id: 179-F
shipment_id: 185-S
unit_role: precursor-foundation
depends_on_shipments:
  - 184-S
gates:
  - 186-S
  - 176-S
  - 178-S
  - 180-S
requires_plan_hardening: true
hardening_rationale: "Every primitive here is a security control: command execution, path traversal, partial-write integrity, and untrusted-input bounds. Three downstream units and one foundation depend on them being correct, and a defect in any one is inherited by all four."
tags:
  - foundation
  - security
  - atomicity
  - primitives
  - precursor
---

# Foundation: safe operation primitives

## Problem frame

The architecture decision requires every safe operation to write atomically,
contain its paths, execute without a shell, and bound its untrusted input.
**None of these primitives exists.** Four downstream units each assumed one or
more of them.

Two of the four are motivated by *observed* defects rather than by principle.

### Observed evidence: the atomic writer

The live checkpoint corpus holds 134 records. Two fail to parse:

```text
checkpoint-20260821-203531.json   4975 B   truncated mid-'context',  position 4975
checkpoint-20260901-002917.json   5445 B   truncated mid-'progress', position 5445
```

Both truncate at **exactly their file length**, mid-object. These are not
corrupt bytes — they are **partial writes from a non-atomic writer**, preserved
in the record. Attempt-08 recorded the same shape as a design gap on `179-S`
(`B3`, `B5`: a multi-step writer with no atomic commit can leave two active
documents, or a manifest pointing at an artifact that does not exist). The
corpus shows it is not hypothetical.

### Observed evidence: the bounded reader

Attempt-08 `B4` on `180-S` recorded that "the live checkpoint directory already
contains records that fail a naive parse, so this is an observed condition, not
a hypothetical one." The two records above are that condition. A scanner that
raises on them cannot complete a corpus scan, and a scanner that skips them
silently under-reports.

## The four primitives

### PR-1 — Atomic write

Write a temp file **in the destination directory**, `fsync`, then `os.replace`.
Temp-in-destination matters: `os.replace` is only atomic within one filesystem,
so a temp file in the system temp directory defeats the guarantee on any
workspace mounted separately.

No operation in this portfolio writes a file by any other path.

### PR-2 — Path containment

Resolve against a declared workspace root and reject every escape: parent
traversal, absolute paths outside the root, and **symlinked escapes after
resolution** — checking before resolution inspects a string rather than a
destination. Rejection is the default.

### PR-3 — Fixed-argv exec

`subprocess.run(argv_list, shell=False)` with a per-operation executable
allowlist. The argument vector is a list and never a string; `shell=False` is
structurally guaranteed rather than promised in prose.

This is the boundary attempt-08 `A1` on `178-S` found missing. A Markdown agent
cannot provide it, because a Markdown agent does not execute argv — the model
composes a shell string. Python does execute argv, which is why the boundary
has to live here.

An argument beginning with a hyphen is carried as a plain argv element and is
not reinterpreted by a shell, because there is no shell.

### PR-4 — Bounded reader

Explicit size and nesting-depth bounds over untrusted JSON, returning a typed
`QUARANTINE` record carrying its reason rather than raising. Malformed or
partially written input is **classified, not fatal**, and no field is silently
dropped.

## Composed-state check

| Primitive | Pass state | Fail state | Producer | Consumer | Activation |
|---|---|---|---|---|---|
| PR-1 | `WRITE_COMMITTED` — reader never observes a partial file | `WRITE_ABORTED` — previous content intact | `179.002-T` | `186-S` recorder, `180-S` checkpoint op | none (inert library) |
| PR-2 | `PATH_CONTAINED` | `PATH_REJECTED` | `179.004-T` | every safe operation | none |
| PR-3 | `EXEC_COMPLETED` | `EXEC_REFUSED` — not on allowlist, or argv invalid | `179.006-T` | `178-S` ensure-branch, `176-S` gate | none |
| PR-4 | `PARSED` | `QUARANTINED` — typed, never an exception | `179.008-T` | `180-S` scanner, `186-S` normalizer | none |

Every pass state is reachable, and **no fail state is `NO_OBSERVATION`** —
each failure is an explicit, observable token. This unit activates nothing: it
is a library, and its consumers activate it in their own commits.

## Rollout

**PREPARE (inert).** All eight implementation and test tasks. The primitives
are importable but no shipped code path calls them, so live behaviour is
byte-identical throughout.

**VERIFY.** `179.009-T` — the evidence record: every assertion observed failing,
the same assertions observed passing, and all 134 pinned checkpoint records
processed without error or unhandled exception.

**ACTIVATE.** None in this unit. Consumers activate.

## Tasks

| ID | Phase | Task | Size | Cx |
|---|---|---|---|---|
| `179.001-T` | RED | atomic write tests incl. interrupted-write simulation and the two torn records | S | medium |
| `179.002-T` | IMPL | atomic write primitive | S | medium |
| `179.003-T` | RED | path containment tests incl. traversal and symlink escape | S | medium |
| `179.004-T` | IMPL | path containment primitive | S | medium |
| `179.005-T` | RED | fixed-argv exec tests incl. allowlist and no-shell assertions | S | medium |
| `179.006-T` | IMPL | fixed-argv exec primitive | S | medium |
| `179.007-T` | RED | bounded reader tests pinned to the full 134-record corpus | M | high |
| `179.008-T` | IMPL | bounded reader + typed `QUARANTINE` record | M | medium |
| `179.009-T` | VERIFY | primitives evidence record | S | low |

Edges: four **independent** RED→IMPL pairs, all four converging on
`179.009-T`. The pairs are not serialized against each other — they touch
disjoint modules and share no state.

## Fixtures

The checkpoint corpus is pinned as **frozen committed copies**, never
regenerated from live data: all 134 records, including both torn records and
every legacy record lacking `schema_version`. A fixture regenerated from live
data stops testing the historical shapes the primitives exist to survive.

## Out of scope

* Domain operations. `ensure-branch`, `p004-gate` and `checkpoint create` are
  consumers in `178-S`, `176-S` and `180-S`.
* Manifest normalization — `186-S` owns it, built on PR-1 and PR-4.
* Any repair of the two torn records. They are quarantined and reported.
  **Immutable history is never rewritten.**

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | `os.replace` atomicity assumptions differ across platforms | PR-1's contract test asserts temp-in-destination explicitly, which is the property that makes the guarantee portable; the test fails if a temp file is created elsewhere. |
| R2 | The allowlist becomes a bypass if operations may extend it at runtime | The allowlist is declared per operation at registration time and is not mutable at call time; PR-3's test asserts an unlisted executable is refused. |
| R3 | Quarantine becomes a silent pass | `QUARANTINED` is a distinct terminal token consumers must handle; `186-S` and `180-S` both classify it as failure, never as absence. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Is a temp file in the system temp directory good enough for PR-1? | No, and this is the most likely silent defect. `os.replace` is atomic only within one filesystem; a workspace on a separate mount would silently lose the guarantee while every test still passed. PR-1's contract test asserts the temp file is created **in the destination directory**. |
| H2 | Does PR-2 checking before resolution suffice? | No. A pre-resolution check inspects a string; a symlink escape is only visible after resolution. PR-2 resolves first and rejects after, and the test includes a symlinked escape. |
| H3 | Can PR-3's allowlist be extended at call time? | No. The allowlist is fixed per operation at registration. A call-time extension would make the allowlist advisory, which is not a control. |
| H4 | Is `QUARANTINE` a disguised pass? | No. It is a distinct terminal token, and both consumers (`186-S`, `180-S`) classify it as failure. The hazard is a future consumer treating it as absence; the token's typed shape makes that a visible choice rather than a default. |
| H5 | What if a torn record is repaired to make a test pass? | Forbidden. The two torn records are pinned fixtures precisely because they are real. Repairing them would delete the evidence that motivated PR-1 and PR-4. |
| H6 | Do the four RED/IMPL pairs interact? | They touch disjoint modules and share no state, which is why they are not serialized. If an implementation introduces a shared helper, the pairs acquire a real dependency and the DAG must be updated rather than the sharing hidden. |

### Blast radius

Library-only. Nothing in the shipped workspace calls these primitives until a
consumer activates them, so this unit cannot change live behaviour. Its risk is
entirely **inherited**: four downstream units build on these four functions, so
a defect here is a defect in all of them.

### Rollback

Every task is inert. Reverting any commit in this unit leaves no workspace state
to repair and breaks no live path, because no live path exists.

### Verification floor

`179.009-T` is not satisfied by a green suite. It requires all 134 pinned
checkpoint records processed with zero unhandled exceptions, and both torn
records observed as typed quarantine results. A suite that passes without
touching the corpus has not verified PR-4.
