---
title: "Ship session memory - 144-S execution and closure"
date: 2026-08-21
agent: ship
route: "claude-sonnet-5 / anthropic / high (P-013.5)"
shipment: 144-S
feature: 136-F
tasks: ["136.002-T", "136.003-T"]
pr: 382
merge_commit: c4e4851cb2e4e1ebee72f675b4bd96264f3a87ad
---

# Ship session memory - shipment 144-S

## What shipped

Restored workspace-wide `backlogit docs lint` traversal (the single known
malformed-frontmatter file was already fixed by `138.001-T`/`146-S`) and
added `tests/test_docs_frontmatter_decodes.py`, a regression guard that
dynamically discovers every `docs/**/*.md` file and asserts any frontmatter
block present decodes as YAML, distinguishing "no frontmatter" (skipped)
from "opened but never closed" (failed) from "closed but malformed YAML"
(failed, with file:line).

## Pipeline trace

* Tool availability: `TOOL_OK` for backlogit CLI (1.10.0) and the
  `autoharness` gate CLI. Intercom/Engram/Graphtor MCP surfaces were
  unavailable per operator note at session start; proceeded in degraded
  visibility using local/CLI fallbacks (grep/glob for codebase discovery,
  direct `backlogit`/`git`/`gh` CLI calls).
* Pre-claim topology gate for `144-S` passed twice (initial + immediately
  before claim); claimed via `backlogit shipment claim 144-S`.
* **Confirmed (again) the backlogit 1.10.0 claim-cascade behavior** first
  noted in the 147-S session: claiming the shipment atomically flipped the
  covering feature `136-F` and both queued tasks `136.002-T`/`136.003-T` to
  `active` in the same operation, before any task-level claim ran. The
  pre-archived member `136.001-T` was correctly left untouched (no queue
  file for the cascade to touch). Promoted to a standalone compound
  learning this session: `docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`.
* Post-claim topology gate: `CLAIM_VERIFY_OK`, sole active shipment.
* Intake reconciliation (manual, since `shipment-reconcile` is template-only
  in this dogfood repo): all manifest items matched `expected_status:
  active` except `136.001-T`, classified `pre-archived` (valid); no
  orphans; shipment record `active` = `record-consistent`. `PROCEED`.
* Executable task set derivation (147-S contract): filtered to task
  artifacts, then applied the status rule -- `136.001-T` (archived) ->
  `pre_archived_skipped`; `136.002-T`, `136.003-T` (active) -> kept. No
  `already_done`, no fail-closed anomalies.
* `136.002-T` sweep: 476 `docs/**/*.md` files (403 with frontmatter, 73
  without) scanned via direct PyYAML parsing (mirroring the task's own
  method), cross-checked against `backlogit docs lint` repo-wide output
  (536 findings, all `required`/`unknown_doc_type`, zero decode-type). Zero
  additional confirmed hazards; zero out-of-scope captures. Legitimate
  zero/zero outcome.
* `136.003-T` TDD: wrote the guard, confirmed green against current `main`,
  then temporarily reverted the `138.001-T` quoting fix (not committed) to
  confirm the guard fails and correctly names the file:line, then restored
  and reconfirmed green.
* Self-review (own pass, before PR): found and fixed a BOM-handling gap
  (`utf-8` -> `utf-8-sig`) in the guard's own file-reading step. Applied in
  commit `1d228395`.
* PR #382 created. CI green (`ci gate`, `detect code changes`,
  `pipeline-topology (ambient)`, `test`) on every push.
* Copilot hosted review (round 1, at HEAD `fa6c7b85`): 2 findings --
  (1) stale docstring paths (`.backlogit/queue/...` should read
  `.backlogit/archive/...` once both tasks are marked done); (2) the
  regex-based frontmatter extractor could not distinguish "no frontmatter"
  from an unterminated (`---`-opened, never-closed) block. Both fixed in
  commit `0c443d30` (replaced the regex with a three-way `_frontmatter_status`
  classifier built on `str.splitlines()`, verified via temporary local
  fixtures for both the unterminated case and the EOF-without-trailing-
  newline closed case). Both threads replied-to (citing the fixing commit)
  and resolved via GraphQL before merge.
* `autoharness gate copilot-review 382` -> `SATISFIED` at HEAD `0c443d30`
  before merge.
* P-009 verified: repo allows merge-commit only (`allow_merge_commit: true`,
  squash/rebase both `false`).
* Merged via `gh pr merge --merge` at `c4e4851c` (two parents confirmed:
  `7850ffc1` main tip + `0c443d30` branch tip).
* P-015 closure: `classify_shipment_close_path(['136-F','136.002-T',
  '136.003-T','136.001-T'], '.backlogit')` -> **CASCADE** (`136-F` is a
  root, fully covered by all three manifest-member children including the
  pre-archived `136.001-T`, manifest contains nothing beyond the qualifying
  root + children). `backlogit shipment ship 144-S --sha c4e4851c...` used
  in place of manual safe-close, per the P-015 verified fully-covered-root
  exception. `archived_ids`: `136.002-T`, `136.003-T`, `136-F`, `144-S`
  (exact match); `returned_ids: []`; `136.001-T.parent_id` re-read as
  `136-F`, unchanged.
* Source stash `395EBE60`: already absent from the active stash and from
  `backlogit stash get` (confirmed "not found") -- Stage had already
  retired it during harvest before this session began, per the operator's
  own briefing. No `backlogit_stash_remove` action was needed or possible
  this session.

## Out-of-scope findings encountered (not absorbed)

Running the full local suite (`PYTHONPATH=src python -m unittest discover
-s tests`) surfaced 3 failures + 2 errors that reproduce only when the full
suite runs together (CI's own `test` job passes cleanly at the same HEAD).
These are the exact tests already named in stash entry `E8158860`
(`DEFERRED SCOPE EXPANSION -- five tests fail ONLY when the full tests/
suite runs together`) -- confirmed via discovery lookup before doing
anything else, cited in the PR body, no new capture created. The 536
`backlogit docs lint` required-field/unknown-doc-type findings are likewise
pre-existing and already captured under `F73BA065` and `90F2A9F8`.

## Follow-ups

None new. Existing stash entries `90F2A9F8`, `8FA8FC22`, `E8158860`,
`F73BA065` are unaffected by this shipment and remain Stage's to
deliberate (P-021 C6), not Ship's to action.
