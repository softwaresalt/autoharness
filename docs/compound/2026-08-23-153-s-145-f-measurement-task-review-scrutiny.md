---
type: compound-learning
shipment: 153-S
feature: 145-F
date: 2026-08-23
tags:
    - copilot-review
    - evidence-quality
    - measurement-task
    - p-021-c1
---

# Evidence-recording tasks are still subject to full review scrutiny — verbatim transcripts and causal accuracy are load-bearing

## Context

Shipment 153-S / task `145.001-T` was a pure measurement/diagnosis task:
no source code change, only a backlog-record disposition (`SUBSUMED`)
documenting evidence for why a previously-observed test-order dependence
(`BranchOwnershipTests` intra-file pollution) had disappeared as a
downstream consequence of an unrelated, already-shipped fix (mechanism A,
152-S).

A fresh current-HEAD Copilot review on the resulting PR (#401) — which
touched **zero** source or test files, only `.backlogit/` records — still
raised 2 legitimate findings against that evidence record:

1. **Missing verbatim output.** The archived task record summarized every
   measurement (`Ran 2 tests ... OK`, `FAILED (failures=1)`) instead of
   including the actual captured command transcripts. A reviewer (human
   or Copilot) cannot verify that a reported pass/fail actually came from
   the named test rather than some other failure without the real
   output, including full tracebacks for negative-control failures.
2. **Causal misattribution.** The causal narrative tying the disappearance
   to the mechanism-A fix named the wrong leaked state (`GITHUB_HEAD_REF`/
   `GITHUB_REF_NAME`/`GITHUB_REF_TYPE` — deliberate per-test override
   values) instead of the actual established mechanism (destructive
   Windows `putenv`-of-empty-value deletion of the ambient
   `GIT_CONFIG_VALUE_2`, laundered through `_run_git`'s designed
   `check=False` swallow into `BRANCH_MISMATCH`). The correct causal chain
   was already fully documented in two OTHER existing, cross-referenced
   records (`144-F.md`, `145-F.md`) that this task's own evidence section
   should have matched but didn't.

## Lesson

**"No source change" does not mean "no review scope."** A measurement or
diagnosis task's entire deliverable IS its evidence record, so:

- **Verbatim > synthesized.** Any time a task's job is to *prove* something
  via test output, the record must carry the actual captured transcript
  (or a verified-representative bounded tail for long-but-uniform runs),
  not a hand-summarized one-liner. A summary invites exactly the kind of
  "did this really fail the way you say it did" scrutiny that a reviewer
  (bot or human) is right to raise.
- **Cross-check causal narratives against already-established records.**
  When a task's causal claim overlaps ground already documented elsewhere
  in the backlog (a parent feature's root-cause section, a sibling task's
  established mechanism), re-read those records before writing the new
  causal statement, rather than re-deriving the mechanism from first
  principles under time pressure. A plausible-sounding but wrong
  attribution (here: blaming the test's own deliberate override values
  instead of the actual leaked ambient state) is the kind of error that
  looks locally coherent but contradicts the cross-referenced source of
  truth.
- **Both findings passed P-021 C1** (same-contract-surface completions of
  the task's own already-authorized evidence-recording deliverable) and
  were fixed directly in a single review-fix cycle, well within budget.
  Neither was a scope expansion requiring C2 capture.

## Reusable technique confirmed a second time

The "surgical revert -> measure -> restore -> verify-zero-diff" technique
for a throwaway negative control (first used to produce the original
145.001-T disposition) was re-run a second time here, this time capturing
full verbatim transcripts on both the current-code and reverted-code
passes. It reproduced byte-identical results both times, confirming the
technique itself is deterministic and safe to re-run for evidence
enrichment without touching the original disposition.

## Where this is reflected

- `.backlogit/archive/145.001-T.md` — corrected evidence record (commit
  `d33dc898`).
- `docs/closure/153-S-145-F-post-merge-closure.md` — closure record citing
  this correction.
