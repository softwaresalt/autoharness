---
shipment: 128-S
feature: 119-F
category: review-process
tags: [copilot-review, mis-triage, frozen-spec, task-acceptance-criteria, ship-agent, p-018, review-loop, quote-dont-paraphrase]
---

# Quote the exact hosted-review comment text before triaging it as a false positive

## Problem

Hosted Copilot review on PR #328 (shipment `128-S`, supervision core
library — session state machine, PTY/process adapters, recovery/restart,
redacted journal) surfaced two findings that were triaged, during PR #328's
own review-fix cycle, as false positives:

1. `session.py:75` (Copilot comment `3772476016`) — the original triage
   record characterized this as "Copilot suggested adding a direct
   transition edge ... straight to `FAILED`", and dismissed it by citing
   `119.003-T`'s "no direct failure edge ... to `FAILED`" requirement.
2. `recovery.py:136` (Copilot comment `3772515911`) — the original triage
   record characterized this as "flagged the unconditional lock release
   ... as a potential double-release", and dismissed it by citing
   `119.006-T`'s "lock released exactly once (F22)" requirement.

Both dismissals were recorded in this repository's own compound-learning
corpus (an earlier version of this very document) as a success story:
"verify the hosted finding against the frozen spec before fixing or
dismissing it." **That verification step was performed — and still
produced the wrong answer** — because it verified a paraphrase of each
finding, not the finding itself.

## What actually went wrong

`128-S`'s own post-merge closure PR (#329) received its own hosted Copilot
review, which flagged that the closure documentation's classification of
both findings was itself incorrect. Re-investigation using the *exact*
original comment text (via `gh api .../pulls/328/comments`, not a summary
written from memory of reading it) showed:

- Comment `3772476016` actually asked to **"add `DRAINING` as a legal
  destination"** for the pre-`RUNNING` phases — not a direct edge to
  `FAILED`. The frozen spec's "no direct failure edge ... to `FAILED`"
  language does not forbid this: `FAILED` remains reachable only through
  `DRAINING` either way. The original triage attacked a suggestion
  ("edge to `FAILED`") that was never actually made, and in doing so
  missed that the *real* suggestion (an edge to `DRAINING`) was legal,
  spec-compatible, and fixed a genuine gap: `BOOTSTRAPPING`/`PREFLIGHT`/
  `RESOLVING`/`LAUNCHING` had no direct failure path to `DRAINING` at all
  (unlike `RUNNING`/`RESTARTING`, which already had one), forcing a
  genuine failure during those phases to be misrepresented as an
  operator-initiated `CANCELLING` transition.
- Comment `3772515911` was actually about **premature lock release before
  child cleanup on an exception raised before the happy path ran** — not
  "double release." F22 ("lock released exactly once, no path can strand
  it") is about avoiding a *stranded* or *duplicated* release, and says
  nothing about *when* within the cleanup sequence the single release may
  happen. The original triage rebutted a claim ("double-release") that
  was never made, and in doing so missed that a still-live child could
  genuinely be left running after the (single, correctly-F22-compliant)
  lock release if an exception pre-empted the happy-path child cleanup.

Both findings were **genuine** and were fixed in a follow-up PR (#330).

## Generalizable lesson

Checking a hosted-review finding against the frozen spec is necessary but
not sufficient — it is only as reliable as the fidelity of what gets
checked. **Before triaging any hosted-review comment as a false positive
(or fixing it), re-read the literal, exact comment text from the review
API (`gh api repos/OWNER/REPO/pulls/N/comments`) and quote or closely
paraphrase it in the triage record.** Do not triage from a remembered or
summarized characterization of the finding, even one written minutes
earlier in the same session — a paraphrase that silently substitutes a
more-obviously-wrong straw-man suggestion (here: "edge to `FAILED`"
instead of the actual "edge to `DRAINING`"; "double-release" instead of
the actual "premature release before cleanup") lets a spec-citation that
is entirely accurate as far as it goes still produce the wrong verdict,
because it was never checked against what was actually said.

A second-order lesson: a closure/compound-learning document is itself a
hosted-review-checkable artifact. This mis-triage was caught only because
the *closure PR* was itself put through hosted review — closure
documentation that asserts "N findings were false positives" is a factual
claim worth the same scrutiny as the code changes it describes, not a
narrative afterthought exempt from review.
