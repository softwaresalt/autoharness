# Ship session checkpoint — 198-S / 192-F post-merge closure HALTED before cascade (2026-10-02)

## State at halt

* Branch `chore/198-s-closure`, cut from `main` at `eb8b7811` (merge of PR #482,
  `feat(shipment-close): cascade-close evidence capture command`). Merge
  confirmed: `MERGED` at `2026-10-03T05:10:52Z`, and the SHA is an ancestor of
  `origin/main`.
* Lifecycle topology gate: exit 0 (`BRANCH_OK`, sole active shipment `198-S`,
  predecessor `201-S` explicit).
* Pre-mode: `PROCEED`. 23 manifest items: `192-F` is `active` in the queue,
  and the 22 tasks are `done` in the archive. No orphans, and the record is
  consistent. Report: `.backlogit/reconcile/198-S-pre-20261003-051636.md`.
* Step 0(c): `autoharness shipment cascade-close --classify-only` exited 0 with
  classifier `CASCADE`, engine `VERIFIED` (1.11.0 / 131577c, cli), and selected
  path `cascade`. The `pre_close` record is
  `docs/closure/evidence/198-S-192-F-close-evidence.json`.
* **The mutating cascade-close was NOT run.** The predicted `shipment ship`
  runtime for 24 artifacts is about 973 to 1020 s, over the hard
  `MAX_TIMEOUT_SECONDS` = 900 cap. A timeout kills the engine partway through
  archiving (exit 6, torn backlog). Analysis is in
  `.backlogit/reconcile/198-S-cascade-close-20261003-051645.md`. Backlog
  unmodified.
* Not done, because they depend on the close: the INV-12 disposition step,
  post-mode, the closure artifact
  `docs/closure/198-S-192-F-post-merge-closure.md`, source-artifact
  retirement, P-020 compaction, the closure index resync, and
  the closure PR.

## Follow-ups captured (active stash)

* `F50BD40F` (bug/high): the cascade-close timeout cap is below the observed
  engine runtime. This blocks the 198-S closure.
* `E01BA307` (task/low): the evidence record stores absolute paths, the
  redaction margin, and the `cli.binary` allowlist. Related to `4DA3BCE6`.
* `320499CC` (task/low): no directory fsync on Windows, the spawn-failure
  `mutation_state`, the exit-code 2/4 and 6/8 nuances, the A4b duplicate-ID
  check, and probe scratch-dir accumulation.
* `8C88A1DB` (feature/low): the evidence path is fixed to
  `docs/closure/evidence`. Related to `40134A08`.

None of these entries contains a deliberation ID, so the `pre_close`
disposition `referrer_ids` stay valid. A re-plan after the stash captures was
`IDENTICAL`.

## Source artifacts (for Step 7 after the close)

* `192-F` `source_stash_id` `008F3BCF`: already archived
  (`2026-09-28T03:36:57Z`). Re-plan stash `1263B218` was also already archived
  (`2026-10-02T22:50:31Z`).
* `192-F` `source_deliberation_id` `035-DL`: the planned outcome is
  `retained_shared_reference` (referrers `2A85BA55`, `4DA3BCE6`, `AE33E3E3`).
  Copy it from the disposition report after the close. Never archive it from
  Ship.

## Resume

After the operator decides on `F50BD40F` (a timeout fix, or explicit
acceptance of the risk at `--timeout 900`), run the mutating command:

```text
autoharness shipment cascade-close --shipment 198-S --feature 192-F --sha eb8b78115c4650e898049920d7f454cb435083dd --message "Merge pull request #482 from softwaresalt/feat/198-s-cascade-close-evidence" --author "Derek Williams <42183845+softwaresalt@users.noreply.github.com>" --timeout <n> --json
```

Before running it, re-acquire the `.backlogit/queue/198-S.md` lock and re-run
pre-mode. Then run the disposition step from the evidence record, then
post-mode, and then write the closure artifact with `close_path: cascade` and
`close_evidence`. If the backlog drifted, the run exits 4. A
`--replace-pre-close` then needs operator approval.
