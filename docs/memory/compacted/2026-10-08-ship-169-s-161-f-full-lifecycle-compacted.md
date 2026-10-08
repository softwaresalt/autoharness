---
title: "Ship 169-S / 161-F full lifecycle (compacted)"
date: 2026-10-08
shipment: 169-S
feature: 161-F
doc_type: memory
compacted_from: docs/archive/memory/2026-10-08-ship-169-s-161-f-session.md
---

# Ship 169-S / 161-F: full lifecycle (compacted)

**Outcome.** SHIP-11, the Option A fix for stash bug `15A02E21`: the
`shipment-reconcile` Member-Class Status Contract (a `qualifying-feature` row
and a `strict-scalar` row, declared status over location, explicit HALT for
every unlisted value), Pre-Mode step 2b, the classifier contract halt and the
Step 0(c) agreement check, with the Ship pointer and parity tests. Shipped in
PR #506, merged as `489e7c3b` with `--merge`. It closed by cascade (classifier
`CASCADE`, engine `VERIFIED`), the first pre-close Pre-Mode under the new
contract. The closure artifact is
`docs/closure/169-S-161-F-post-merge-closure.md`.

## Decisions

* **161.007-T** (diagram 05) disposed not-applicable in-repo: its target is
  untracked operator WIP in `git stash@{1}`; delta deferred as `675EA40E`.
* **Copilot cycle limit.** The round-4 finding was valid and in scope after
  three review-fix cycles; Ship held the merge instead of fixing past the limit
  or deferring an in-scope finding, and the operator authorized an extension.
* **Lock token.** The locked closure sequence (lock, Pre-Mode, classify-only,
  agreement check, mutating cascade-close, disposition, post-mode, release) ran
  in one supervised process so the token never left memory.
* **Decision record.** Left unmodified (P-010: Ship does not modify
  deliberation artifacts); the bug record was marked fixed.
* **Tooling.** The global `autoharness` is a stale 1.5.0, so the checkout's CLI
  ran through a git-ignored `src` wrapper; tests, hooks and pushes rerouted
  temp directories to `.proof-scratch/169-S/tmp`.

## Evidence

* Local review: 10 personas, `READY_WITH_FOLLOWUPS`, P0=0/P1=0 at `c2e6b48e`;
  full suite 3476 OK (skipped=57).
* Copilot: six rounds; round 1 one thread (fixed `fb68e399`); rounds 2 to 5
  one review-body "Previously missed" finding each (fixed `b879a045`,
  `24d5fc13`, `0b2c0bc5`, `c2e6b48e`); round 6 clean; P-018 PASS.
* Close: Pre-Mode `PROCEED` (`161-F` `active` matched as qualifying feature),
  agreement `agreed`, cascade run `357f5eded7184c8a9cf436a6b960da07` exit 0,
  `returned_ids` `[]`, all postconditions true, `DISPOSITION_COMPLETE`,
  post-mode `PROCEED`; close commit `8c751c02`.

## Learnings

* Copilot can report a finding only in a collapsed "Previously missed" section
  under a "0 open findings" headline, with no thread; read every review body
  (`docs/compound/2026-10-08-copilot-review-body-findings-without-threads.md`,
  gate gap `38D29192`).
* The cascade child took 1153 s for N = 9 (B = 672 s), an outlier against
  earlier closures (198-S: N = 28 in 985 s); run-to-run variance can approach
  the 1800 s default (`4CB6A1E0`, wording corrected in the closure artifact).
* After a cascade moves a record, re-derive pathspecs from `git status`: a
  stale `queue/` path made `git add` fail and the first close commit had to be
  amended before push.

## Follow-ups

Shipment deferrals `675EA40E`, `D16452D7`, `814BB949`, `F0F8916F`,
`A9BABC8B`, `B5AB7D95`, `D6502107`, `E1E31E6A`; closure captures
`4CB6A1E0`, `16128302`, `38D29192`.
