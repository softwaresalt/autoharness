---
title: "Select a shipment close path from the classifier's verdict, never from a partial or summarized reading of the exception prose"
tags: [shipment-closure, p-015, review-protocol, safe-close, cascade]
provenance: "127-S / 118-F post-merge closure"
source: docs/compound/2026-08-12-close-path-decisions-must-use-the-classifier-not-summarized-prose.md
doc_type: learning
---

## Summary

Before executing shipment `127-S`'s post-merge close, an intermediate
planning pass (carried across a context-compaction boundary) concluded
"proceed with safe-close, not cascade" based on a reading of the Ship agent
instructions that captured the *unconditional* prohibition sentence
("NEVER the cascade... P-015") but missed the immediately-following
conditional exception clause (item "e": the P-015 verified
fully-covered-root exception, which instructs running
`classify_shipment_close_path` and using its verdict to select the close
path). Re-reading the full, current section on-disk (not a prior summary of
it) before acting surfaced the exception, and running the actual classifier
against the real manifest returned `CASCADE` — which matched both the
shipment's own Stage-authored manifest description (which explicitly
predicted `backlogit shipment ship 127-S` as the close command) and the
operator's brief (which referenced that exact command).

## Generalizable lesson

1. **A close-path decision (or any policy-conditional operational decision)
   must always be made by re-reading the full, current, on-disk source of
   truth immediately before acting — never from a summary/paraphrase of it
   carried across a compaction boundary or an earlier turn.** Summaries are
   lossy by construction; a conditional exception clause is exactly the kind
   of detail that can silently drop out of a summary while the unconditional
   default sentence survives, because the default sentence is shorter and
   reads as more "important" in isolation.
2. **When agent instructions say "select the close path from the verified
   check, never from prose alone," that is a literal instruction to run the
   actual classifier function/tool and act on its return value — not to
   reason qualitatively about whether the manifest "looks like" it should
   qualify.** The classifier existed in this very shipment's own diff
   (`src/autoharness/gates/shipment_closure.py`); it should have been
   invoked as the very first step of the close decision, not after a
   provisional prose-based decision had already been drafted.
3. Cross-check any close-path (or similarly consequential) decision against
   independent evidence before executing: here, the shipment manifest's own
   description text and the operator's brief both independently pointed at
   the cascade path, which would have caught the wrong-default decision even
   if the classifier itself had not been re-run.
