# Ship session record: 210-S / 203-F, post-merge closure (2026-10-13 UTC)

Session record for the Ship execution of shipment 210-S (feature 203-F, stash FB6F9FE0):
stash-referenced companion-document carry-forward through P-011 and the `pre_claim`
`worktree_cleanliness` gate. Dark mode (P-017) scoped to 210-S only; merge approval
pre-authorized; admin fallback not authorized.

## Outcome

* PR #516 merged as merge commit `1f8958c9` (two parents `acff0052` and `1fcdbee7`), merged
  2026-10-13T14:15:14Z. CI on the PR head and on the merge commit: success.
* Shipment 210-S closed through the P-015 CASCADE path (`autoharness shipment cascade-close`,
  exit 0, postconditions pass, 9 of 9 archived, `returned_ids` empty); shipment record
  archived with `archived_status: shipped`.

## Decisions and what changed

* Gate (`src/autoharness/gates/topology.py`): `StashReferences`, optional reader capability
  `stash_referenced_paths`, exact whole-token matching against active entries of the working-copy
  `stash.jsonl` of the resolved backlog root, new docs/ files only (untracked or staged-added),
  full containment predicate, fail-closed stash reads (missing, symlink, non-regular, non-UTF-8,
  malformed, pathologically nested), `details.stash_referenced_paths` and
  `details.stash_reference_warning`, explicit `_UNREAD` sentinel for the worktree snapshots.
* Policy and agents: P-011 carry-forward set (registry 1.34.0), P-010 carve-out (Ship commits
  already-captured entries and documents verbatim), Ship carry-forward and mid-cycle intake
  (task boundary only; Ship-confirmed documents), Stage companion-document commit guidance.
* Contract test `tests/test_stash_referenced_carry_forward_contract.py`; manifest checksums for the
  three touched mirrors refreshed.
* Mid-cycle intake was restricted to task boundaries because `pre_claim` classification is
  unavailable once the shipment is active; a later-blocked `pre_claim` loses cleanliness details,
  so the backlog-only fallback halts on a stash-referenced document (fail closed, plan unit B6).
  Making the cleanliness result visible on later-blocked results is deferred (stash A851D81B).

## Review

* Local multi-persona review (9 personas, report-only): no P0/P1; in-scope P2/P3 fixed; out-of-scope
  findings captured as DEFERRED SCOPE EXPANSION stash entries E148C09C, 325FF702, 44321776,
  E04BEC17, 86AE78EA.
* Copilot review on PR #516 (requested via GraphQL `requestReviews`, operator-directed): five rounds.
  R1 (4 threads): FIFO stash, details-key claim in CHANGELOG, later-blocked fallback (partial,
  deferred A851D81B). R2 (1 thread): validate reader answer fields. R3 (1 threadless body finding):
  a reader warning discards returned paths; disposition marker comment posted. R4 (6 threads):
  state the full containment predicate in policy, Ship, and Stage text. R5: approval recommended,
  0 open findings. All 11 threads resolved; P-018 gate SATISFIED on the final HEAD.

## Learnings

* Copilot rounds repeatedly found cross-surface propagation gaps (RC-10): a rule changed in code
  needs the same predicate in policy template and mirror, Ship, Stage, docs, and CHANGELOG.
* `backlogit move --status done` relocates a task to `.backlogit/archive/` while it still declares
  `status: done`; Pre-Mode must classify by declared status, never by location.
* The pre-push hook runs the full suite plus markdownlint (about 11 minutes); batch pushes.
* A blocked `pre_claim` result reports only its blocking check, so cleanliness details are absent
  whenever a later check blocks.

## Residual risks and follow-ups

* Prose mention of an exact docs/ path in any active stash entry admits that new file (the
  operator-specified FB6F9FE0 contract); narrowing deferred to E148C09C.
* Deferred stash entries: E148C09C, 325FF702, 44321776, E04BEC17, 86AE78EA, A851D81B.
* Carryover cut: Feature C (211-S, UTC mandatory for recorded dates and times) remains open.
