# Ship 208-S post-merge closure session (2026-10-10)

Fresh-context Ship session that ran the post-merge closure for shipment
208-S (covering feature 201-F) after PR #511 merged. It supersedes the
halt checkpoint `2026-10-10-ship-208-s-halt.md`, which is now compacted.

## Outcome at time of writing

* PR #511 merged: merge commit `bc461105` (`--merge`), parents `26446a68`
  and `3ef04bac`, merged 2026-10-10T23:36:59Z. CI on `bc461105` succeeded.
* Shipment 208-S closed via the P-015 CASCADE path. The classifier returned
  CASCADE and the engine VERIFIED (backlogit 1.11.0, CLI). The mutating
  `autoharness shipment cascade-close` returned exit 0 with
  `postcondition_verdict: pass`. The shipment record is `shipped`, archived
  with `archived_status: shipped`. Feature 201-F and tasks 201.001-T to
  201.009-T are archived.
* Closure branch `post-merge/201-f-p018-copilot-review-body-findings`. Backlog
  commit `0bb02879`. The closure artifact and evidence record are committed
  in the next commit (see the closure PR).
* Stash captures (P-021 C2 or post-merge Step 6): `5A51B5F9` (cp1252 `--force`
  print, the required capture), `31A1FEAC` (file-lock staged vs installed
  script drift), `674BA1FE` (`stash get` does not resolve archived entries).

## Decisions and rationale

* CASCADE chosen only because the classifier and engine both verified. The
  operator's closure directive named this exact path, so it was taken as the
  destructive-command clearance (intercom was unavailable).
* Timeout left at the default 1800 s. Reference budget B = 777 s. Supervision
  budget 2400 s. The run was attached and async, and was not killed.
* Source stash `38D29192` was NOT re-archived. It was already archived on
  2026-10-08T20:57:17Z (`reason: archived`). The halt checkpoint's "source-stash
  retirement NOT done" line is superseded by that archive record.
* The `custom_fields.source_stash_id` field is absent on 201-F and 208-S. The
  provenance link is the label `source-stash-38D29192`. Outcome recorded as
  `none`. The gap is already tracked (`C9E87CE9`, `FD85BC61`).
* The INV-12 disposition snapshot is empty. The deliberation file is cited by
  path only and is not a backlogit deliberation record. No hand archive.
* Stash `3FC709F9` (operator-accepted hardening follow-up) was not edited,
  archived, or harvested. `F373C349` was left for Stage.

## Deviations (disclosed)

* The Pre-Mode lock used `.autoharness/staging/scripts/acquire_lock.ps1`
  because the skill-relative `.github/skills/file-lock/scripts/` path does
  not exist. The workspace-root `scripts/acquire_lock.ps1` has a different
  SHA-256. The lock was released with its token (`31A1FEAC` tracks it).
* `uv run autoharness --help` (the declared `cli-help` probe) failed twice on
  a PyPI TLS handshake (network). The installed entrypoint (`autoharness home`
  = this workspace) was used. Verdict recorded as `PASS_WITH_FOLLOW_UP`.
* MCP backlog and GitHub tools were unavailable (TOOL_DEGRADED). The backlogit
  CLI and `gh` were used.
* Process deviation (disclosed): an earlier Ship session claimed 208-S and
  implemented its tasks before the operator's acceptance of hold 3FC709F9
  (verbatim decision record: PR #511 comment 6095553824). See the closure
  artifact, decision (a).

## Learnings

* Run `--classify-only` after Pre-Mode, then the agreement check, before any
  route. The Pre-Mode report and the evidence record must agree.
* A feature's `custom_fields` do not carry `source_stash_id` in this
  workspace. Retirement evidence must come from the label and the stash
  archive record.
* `backlogit stash get` reads only the active store. Archived candidates need
  a direct, read-only parse of `archive/stash.jsonl` until `674BA1FE` is
  resolved.

## Remaining closure steps at time of writing

* Closure PR: local review (P-014), Copilot review loop, §1.9 gate,
  DARK_MODE_MERGE_AUTHORIZED, `--merge`, two-parent proof, MERGE_CONFIRMED.
* Post-merge: return to `main`, confirm a clean tree, run the post-merge
  smoke on `main`, confirm CI on the closure merge commit, emit
  DARK_MODE_COMPLETE.
