---
title: "Ship 149-S execution and closure session (full-suite test-isolation diagnosis and ambient-cwd decoupling)"
date: 2026-08-21
agent: ship
route: "claude-sonnet-5 / anthropic / high"
shipment: 149-S
feature: 141-F
tasks:
  - 141.001-T
  - 141.002-T
  - 141.003-T
  - 141.004-T
  - 141.005-T
pr: 390
merge_commit: ca9059bf9c651b61c9d0a458568ffc798ff4cf91
---

# Ship 149-S: Execution and Closure Session

## Sequence

1. **Claim**: verified pre-claim eligibility (topology gate PASS, no active
   shipment, predecessor 148-S shipped/closed), claimed 149-S, created a
   fresh active checkpoint immediately.
2. **141.001-T (diagnosis, no source/test change)**: ran the canonical
   full-suite gate, reproduced the exact known 5 failures. Captured
   previously-unrecorded verbatim `git` stderr for the two git-related
   failures via an ad-hoc (never committed) `subprocess.run` monkeypatch:
   `error: missing config value GIT_CONFIG_VALUE_2 / fatal: unable to parse
   command-line config` -- git's environment-variable config-injection
   mechanism, with zero references anywhere in this repo's own code or
   dependencies. Ran the plan's mandatory step-2 "exclusion" re-check
   (positive enumeration of the 84-module complement set excluding the
   three `test_scope_containment_*` modules a prior deliberation entry
   blamed): the same 5 failures reproduced WITHOUT those modules present,
   **falsifying** the entry's own established fact. Per the fixed protocol,
   stopped and recorded `VERDICT: INCONCLUSIVE` with the falsification
   evidence -- zero bisection rounds run, exactly as the protocol requires
   when the premise itself is disproven.
3. **141.002-T**: added an AST-based structural guard
   (`tests/test_test_suite_isolation_contract.py`) asserting no module
   under `tests/` anchors a temp workspace inside the live working tree via
   `dir=Path.cwd()`. Fixed 8 of 58 sites. **Learned the hard way**: a
   first-pass static "containment not required" call for
   `test_backlog_only_workspace_succeeds` was WRONG -- empirically running
   the fixed module revealed a real regression
   (`NO_IMPLEMENTATION_WORKTREE`), because the pipeline-topology gate's own
   `worktree_topology` check shells out to real `git worktree list` scoped
   to the workspace, a dependency the test's own mocking didn't cover.
   Reverted that one site to an in-repo anchor and re-verified. This
   became the standing methodology for the rest of the shipment: NEVER
   trust a static containment read; always verify empirically
   (before/after isolation run) before finalizing a site's classification.
4. **141.003-T**: fixed the remaining 16 sites in `test_backlog_root.py`
   (containment not required for any, confirmed empirically).
5. **141.004-T**: fixed the remaining 34 sites in `test_gates_topology.py`
   (33 not required; 1, victim #2, required and anchored, per the same
   worktree_topology dependency). Emptied the guard's allowlist.
   **Notable side discovery**: while verifying isolation parity, found that
   victim #2 ALSO fails when `test_gates_topology.py` runs standalone (94
   tests, no other file involved) if any of 5 specific `BranchOwnershipTests`
   tests run first -- and this reproduces IDENTICALLY against the completely
   unmodified original file. This is a genuine, pre-existing, intra-file
   test-order pollution bug, unrelated to the ambient-cwd `dir=Path.cwd()`
   work this shipment targets (none of the 5 candidate tests use tempfile
   at all). Bisected within the file (fast, ~1s/run) to the 5 candidates but
   did not root-cause the mechanism (no env leakage found; out of this
   shipment's authorized scope to fix). Recorded on the task and in the
   closure record for 151-S's benefit -- proof that "full-suite pollution"
   is not monolithic: it can be reproduced at file-level granularity
   independent of cross-file interaction, which may be a useful lead for
   151-S's own remediation bisection.
6. **Feature AC-F1**: re-measured the canonical full-suite gate after
   141.004-T. `Ran 1722 tests, FAILED (failures=3, errors=2, skipped=20)` --
   exact same 5 pre-existing failures, no new ones. Closed feature 141-F.
7. **Local review** (code-review agent): READY, zero P0/P1/P2.
8. **PR #390**: one Copilot review thread (guard's scan was non-recursive
   `test_*.py`-only, contradicting its own "no module under tests/"
   invariant) -- fixed by switching to `Path.rglob("*.py")`. Resolved,
   re-reviewed, `SATISFIED`. Merged with `--merge`, verified 2-parent commit.
9. **Post-merge closure**: P-015 classifier returned `CASCADE`. The cascade
   swept in an out-of-manifest deliberation (`024-DL`, plain `references`
   link) -- the THIRD occurrence of the exact recurring engine-behavior
   surprise first seen on 143-S/134-F/019-DL and again on 148-S/140-F/025-DL
   earlier in this same session. Reverted `024-DL` per the now well-worn
   remediation, re-verified all other post-conditions, recorded the third
   occurrence on the existing compound learning doc.

## Hard-won lessons (compound-worthy)

* A per-site "containment required?" determination for ambient-cwd
  decoupling work CANNOT be made reliably from a static read alone when the
  code under test invokes a CLI/gate surface with its own hidden
  dependencies (here: a `worktree_topology` check shelling out to real
  `git worktree list`, invisible from the test's own mocking surface).
  Always verify empirically, per-module, before finalizing.
* "Full-suite test pollution" is not necessarily a whole-suite,
  cross-file phenomenon -- it can and did reproduce at single-file
  granularity here (`test_gates_topology.py` alone, 94 tests, one test
  polluted by 5 specific sibling tests in the same file), a materially
  smaller and more tractable diagnostic surface than the full 1722-test
  canonical gate.
* The out-of-manifest linked-deliberation cascade recurrence is now a
  three-time pattern (143-S/134-F/019-DL, 148-S/140-F/025-DL,
  149-S/141-F/024-DL) -- always a plain `references`-list entry (not
  `custom_fields.source_deliberation_id` after the first occurrence),
  always caught by the Cascade Close Sub-Procedure's own step-3 exact-match
  check, always remediated identically (revert only the swept artifact,
  re-verify everything else). This is now firmly a Stage-owned engine-
  behavior follow-up, reinforced by independent repeated observation.

## Deferred / follow-up

* `141.001-T`'s `VERDICT: INCONCLUSIVE` -- gates 151-S's remediation scope
  (feature 143-F).
* Supplementary `BranchOwnershipTests`-order intra-file pollution finding on
  `test_gates_topology.py` -- unactioned, recorded for 151-S.
* Cascade close out-of-manifest reference-link sweep (third occurrence) --
  Stage-owned template/classifier hardening follow-up remains open.

## Session state at close

Shipment 149-S archived (`archived_status: shipped`). Feature 141-F archived
(`archived_status: done`). All 4 executable tasks archived with preserved
`parent_id`; `141.005-T` remains untouched (pre-archived/superseded before
this shipment began). No successor shipment (151-S) claimed. Two
`.mcp.json` stashes left untouched for Orchestrator restoration. Post-merge
closure branch/PR in progress at the time this memory file was written (see
`docs/closure/149-S-141-F-post-merge-closure.md` for the authoritative
structured closure record).
