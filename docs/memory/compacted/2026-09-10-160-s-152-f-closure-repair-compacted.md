---
title: Compacted memory — 160-S / 152-F closure-evidence repair (PR #442)
doc_type: memory
memory_class: compacted
created: 2026-09-10
shipment: 160-S
feature: 152-F
tasks: []
merge_commit: 038b393f7eeb207acd86fb39383981fa181efd5d
pr: 442
consolidates:
  - docs/archive/memory/2026-09-10-ship-pr442-160-s-closure-repair-merge.md   # verbose original
related_compacted: docs/memory/compacted/2026-09-09-160-s-152-f-compacted.md   # original merge/closure compaction (PR #439)
---

# Compacted: 160-S / 152-F — closure-evidence filename repair (PR #442)

Dense consolidation of Ship's repair of 160-S/152-F's post-merge closure
evidence discoverability, which had blocked successor shipment 161-S's
`pipeline-topology --phase pre_claim` gate.

## Outcome

Merged PR #442 (merge commit `038b393f`, two parents `753d1b90`+`179ae8cd`,
merged 2026-09-11T02:54:02Z) via `gh pr merge --merge` only, after operator
approval scoped to this PR. `docs/closure/2026-09-08-160-s-152-f-closure.md`
renamed to `docs/closure/160-S-152-F-post-merge-closure.md` (no content
rewrite) so it matches the `pipeline-topology` gate's discovery glob
(`docs/closure/{shipment_id}-*-post-merge-closure.md`). Re-verified on
merged `main`: `pipeline-topology --shipment 161-S --phase pre_claim` now
exits 0 (`shipment_readiness: passed`); previously blocked with
`PREDECESSOR_CLOSURE_INCOMPLETE`.

## Key learnings

* Same defect class as documented in
  `docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md`
  — now recurred a **fourth and fifth** time (156-S, 159-S already fixed
  before this session; 160-S fixed here). The systemic producer/consumer
  contract fix remains open and unowned by this repair (correctly out of
  scope, P-021 C1).
* Branch-creation gate correctly halted (`DARK_MODE_HALTED`) when `main`
  was dirty with unrelated operator changes, rather than bypassing it.
  Explicit operator authorization to carry unrelated changes forward
  unmutated is a distinct, narrower authority than a general "proceed"
  instruction, and was required before branch creation could proceed.
  Byte-identical preservation (SHA-256 hash comparison before/after every
  branch switch) is a cheap, high-confidence verification for this
  guarantee.
* HEAD advancement re-arms the P-018 Copilot-review gate: a prior
  `SATISFIED`/completed review at an old commit does not carry forward
  after a new push, even a metadata-only `gh pr edit` change to the PR
  description does not require Copilot re-review, but a new **commit**
  does.
* A Copilot review finding that a PR description has gone stale relative
  to current HEAD (file count, reviewed-HEAD value) is a same-contract-
  surface, in-scope fix (P-014 requires the readiness block to match
  current HEAD) — resolved via `gh pr edit`, no new commit required.
* **P-020 compaction-candidate rule correction (this session's own
  mistake, caught by Copilot round-1 review of PR #443)**: the "part of a
  completed feature or chore" Phase 2 candidacy rule has **no age gate** —
  it is independent of the `threshold_days` age-based rule. A freshly
  written session-memory file documenting a just-merged, completed release
  unit qualifies as a compaction candidate immediately, not only once it
  ages past 14 days. Initially misreported this as a correct scan-only
  no-op; corrected by actually compacting the fresh memory (this file) once
  the error was identified.

## Follow-ups (Stage-owned, P-021, unchanged by this repair)

`24A85BF8` (pre-existing flaky `test_graphtor_mcp_shim.py` test, reused,
Stage deliberation pending); systemic closure-evidence producer/consumer
contract fix (`docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md`);
stale `.backlogit/stash.jsonl:61` reference subsumed by existing deferred
entry `5ADCA9FE` (no new entry created).
