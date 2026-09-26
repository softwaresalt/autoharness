---
title: "IM-14 non-claim audit redesign: closed-vocabulary tripwire over a closed list of audited commits, cleared by a digest ledger, with a narrow permanent floor"
source: "docs/decisions/2026-09-26-im14-non-claim-audit-redesign-spike.md"
doc_type: decision
description: "Time-boxed Stage spike, requested by the operator after the LIFECYCLE-E2-R1-2d562820 epoch stop (manifest d4bfb3aa), on the IM-14 / PE-SAFETY-06 non-claim audit of plan revision 3 (blob ffa663de). The open claim-form regex net (O1) cannot converge: against 26 in-vocabulary claim forms it catches 11 and misses 15, including all 8 IM-14-F11 forms, and each review round has found new forms. The recommended design (O2 hybrid) detects the threat vocabulary rather than claim forms, scans only added lines of a closed list of audited commits (first-parent, no rename detection), clears hits through the required sentence or a closed SHA-256 ledger asserted by the test, supplies base commits as constants rather than an environment variable, and keeps only a git-free floor over three new modules after S(D) closes. It catches 26 of 26 claim forms and both split-token forms, surfaces 0 pre-existing lines, handles renames and copies, and fits inside rev 3's growth headroom (+96 bytes, +42 words). No re-charter trigger."
docline:
  type: spike
  date: 2026-09-26
  time_box: "2h"
  conclusion: "proceed"
  confidence: "medium"
  linked_parent_work_item: "docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md (unit C5, Non-Claim Audit Inventory)"
  promoted_to: ["none"]
  tags:
    - "non-claim-audit"
    - "IM-14"
    - "PE-SAFETY-06"
    - "ship-lifecycle"
    - "review-convergence"
artifact_class: spike-findings
epoch: LIFECYCLE-E2-R1-2d562820
epoch_verdict: EPOCH_STOPPED
operator_decision_commit: d4bfb3aa33e57da84070735c6f6917d9bee97be2
plan_baseline_blob: ffa663de030a0a07baa5b62ea1078b750a0a4009
growth_baseline_blob: 2d562820
head_at_authoring: d4bfb3aa33e57da84070735c6f6917d9bee97be2
branch: chore/stage-176-s-workflow-defects
worktrees: 1
plan_edited: false
prototypes: ".proof-scratch/im14/ (Git-ignored, deleted after recording evidence)"
recharter_trigger: false
---

## Goal

What bounded, deterministic IM-14 non-claim audit mechanism satisfies the
IM-14 and `PE-SAFETY-06` matrix rows as ratified, closes IM-14-F07.1,
IM-14-F08 and IM-14-F11 by construction (and IM-14-F09, F10, F12, F13, F14
and F15 where possible), and imposes negligible ongoing nuisance on normal
development workflows?

## Success Criteria

* The design meets the ratified row text, not reviewer extrapolations.
* Each open blocker closes by construction, not by adding more patterns.
* Evidence covers (a) every rev 3 control and every missed form in
  IM-14-F05, F10 and F11, (b) the pre-existing listed files and (c) a
  synthetic rename.
* A drop-in specification for the plan section exists, with its size
  delta against revision 3 and the headroom against revision 1.
* Lifetime and nuisance are weighed explicitly, as the operator asked.

## Scope Constraints

* Read-only on product, source and plan. The plan stays at revision 3.
* Prototypes only in `.proof-scratch/`, verified Git-ignored first
  (`.gitignore:10:.proof-scratch/`), never committed, deleted afterwards.
* One worktree (P-016). The synthetic rename used a throwaway, independent
  `git init` repository inside `.proof-scratch/`, not a worktree.
* No new subsystem, threat class, public name or reason code. A design
  needing one would be a re-charter trigger (charter section 5; reset
  deliberation Phase 4).

## Investigation Approach

1. Read the ratified rows: implementation matrix IM-14
   (`docs/decisions/2026-09-25-lifecycle-proof-exit-refresh-spike.md`
   line 314) and charter section 7.6 `PE-SAFETY-06`, plus the precedent
   audit (`docs/decisions/2026-09-24-lifecycle-proof-exit-spike.md`
   line 222).
2. Read the Delta Review 1 and 2 findings in
   `docs/reviews/2026-09-25-ship-lifecycle-release-units-plan-review.md`
   and the rev 3 section (plan lines 719-753).
3. Build a control corpus and run O1 (rev 3 patterns, verbatim) and a
   closed-vocabulary term detector against it.
4. Measure the pre-existing baseline, the history nuisance rate and the
   per-shipment load over the last 12 first-parent merges.
5. Run a synthetic rename and copy, and prototype the ledger check.

## Findings

### What the Ratified Rows Require

| Row | Requirement | Pass criterion | Evidence |
|---|---|---|---|
| IM-14 | No artifact claims race, TOCTOU or hardlink-alias resistance | Holding: the text audit is clean | Text audit |
| `PE-SAFETY-06` | Same | Text audit of proof artifacts and the matrix draft finds no such claim | Audit record in the proof-exit report |

The precedent audit that met `PE-SAFETY-06` was a human text audit with a
recorded judgment ("finds only non-claims"). Deciding claim versus
non-claim is semantic. The ratified rows ask for an audit and a record.
They do not ask for an automated classifier. The rev 3 regex test was a
plan-level extrapolation of that requirement, and the review epoch then
tried to make an open pattern set complete. That is why it did not
converge: blockers went 7, then 2, then 3, and every IM-14 round found new
claim forms (IM-14-F05: 7, IM-14-F11: 8).

The charter's threat model lists TOCTOU, race and hardlink-alias
resistance as **explicitly not claimed**. Auditing that nothing claims
them adds no requirement and no threat class.

### Options Evaluated

| Criterion | O1 open regex net (rev 3) | O2 added lines, closed vocabulary, closed exemptions, attestation | O3 term tripwire with markers | O4 attestation only, minimal floor |
|---|---|---|---|---|
| False negatives | Open: 15 of 26 claim forms missed | Closed for any form naming the threat; out-of-vocabulary residue goes to the text audit | Same as O2 | Everything except the floor goes to people |
| False positives | 3 of 9 natural non-claims fail, with no clearing path | Hits need a ledger entry; negations are cleared once, by digest | Every hit needs an in-text marker, which pollutes product text | None |
| Pre-existing text | Whole-file scan; 0 hits today only because of vocabulary luck | 0 by construction | Whole-file: 4 unrelated hits | n/a |
| Base commit under `unittest discover` | Unnamed (IM-14-F09) | Constants in the test; skip names its reason; C5 step, closure and D3 fail on skip | Needs a base or whole-file | None |
| Renames and copies | `AM` filter drops them (IM-14-F13) | `--no-renames`: counted as additions | Depends on scope | n/a |
| Harvest before C5 | "Same scan" cannot run (IM-14-F07.1) | Harvest records the text audit; the harvest commit enters the audited list at C5 | Same gap as O1 | Text audit only |
| Exemptions | Property-based whole files (IM-14-F08) | None by path; closed digest ledger (`fixture`, `non-claim`) | Markers per line | n/a |
| Lifetime and nuisance | Permanent and growing | Bounded list, final after S(D); then a git-free floor over 3 new modules | Permanent, repo-wide if unscoped: 722 hits in 168 of 1469 commits | Minimal |
| Fit in C5 | Current | Same file; no new public name or reason code | Markers need product edits | Weakest deterministic evidence |

O2 as recommended below borrows O3's detector (term presence) and O4's
recorded text audit for the residue.

### Evidence

Controls, rev 3 patterns versus the closed vocabulary. Command:
`python .proof-scratch/im14/controls.py`.

```text
O1 regex net (rev 3): claims=26 caught=11 missed=15
   out-of-vocab caught=0/4
   rev3 negatives hit=0/3
   natural non-claims hit=3/9
   F05: caught 7/7   F10: caught 0/2   F11: caught 0/8   EXTRA: caught 0/7   POS_REV3: caught 5/5
O3 term tripwire: claims=26 caught=26 missed=0
   out-of-vocab caught=1/4
   rev3 negatives hit=1/3 (the required sentence)
   natural non-claims hit=6/9
   F05: caught 7/7   F10: caught 2/2   F11: caught 8/8   EXTRA: caught 7/7   POS_REV3: caught 5/5
```

The 26 claim forms are the rev 3 positives, IM-14-F05, F10 and F11, and 7
further forms found by this spike (for example `closes the TOCTOU window`
and `race conditions cannot occur`). O1's 3 natural-negation false
positives were `This module is not race-free.`, `It does not protect
against TOCTOU.` and `Never claim protection against race conditions.`
O1 has no way to clear them.

Recommended detector with adjacent-line join, required-sentence clearing
and ledger. Command: `python .proof-scratch/im14/rec.py`.

```text
controls caught 26 / 26 | split-token 2 / 2 | OOV 1 / 4 | natural non-claims surfaced 6 / 9 | substring traps (trace/embrace/racetrack/grace) 0
pre-existing baseline, added-lines scope (HEAD..HEAD): 0
12 merges: surfaced total 62 | merges with >=1 surfaced 8 | median surfaced 3 max 24 | outside docs/.backlogit total 3
rename repo: --no-renames surfaced 2 ['copied.py', 'reader2.py']
   rename-detecting name-status: ['C100', 'reader.py', 'copied.py', 'R100', 'reader.py', 'reader2.py']
   digest-keyed ledger covers renamed+copied lines: True
   unledgered claim fails: True | unused-entry check: []
```

Required-sentence clearing: the sentence alone and inside a docstring
clear. The sentence followed or preceded by `It is race-free.`, and `This
reader makes no race claim.`, do not clear.

Pre-existing listed files (IM-14-F14). Command:
`python .proof-scratch/im14/baseline.py`, over the 12 pre-existing files
rev 3 lists.

```text
TOTAL whole-file O1 0 O3 4
  .autoharness/harness-manifest.yaml lines 216, 221, 281 (file-lock script notes)
  src/autoharness/cli.py line 1411 ("symlink swap" in a bootstrap-grant comment)
repo-wide, last 300 commits: commits=1469 added_lines=379206 O1_added_hits=64 O3_added_hits=722 commits_with_O3_hit=168
listed pre-existing files, last 300 commits: commits=189 added_lines=6226 O1_added_hits=0 O3_added_hits=10 commits_with_O3_hit=7
```

A whole-file scan would make 4 unrelated lines fail. Added-lines scope
surfaces 0. A permanent repo-wide term gate would surface trigger lines in
about 11% of commits (168 of 1469), mostly `docs/` (343) and
`.backlogit/` (279). That is the long-term nuisance the operator named.

Synthetic rename and copy (IM-14-F13). A throwaway repository commits
`reader.py` containing `This reader is race-free.`, then a pure rename to
`reader2.py`, then a copy to `copied.py`.

```text
name-status -M -C --find-copies-harder: C100 reader.py copied.py; R100 reader.py reader2.py
--diff-filter=AM --name-only (default renames): reader2.py
--diff-filter=AM with -C --find-copies-harder: (empty)
added lines containing race, default -M: 1
--no-renames added lines containing race: 2
```

With rename detection on, an `AM` filter drops half or all of the carried
claim. `--no-renames` surfaces both copies, and a digest-keyed ledger
clears a reviewed line under its new path with no new entry.

Environment facts: `.github/workflows/ci.yml` has no `fetch-depth`
(checkout depth 1), so any git-range scan in CI needs history fetched
first. `harness_read.py`, `harness_surfaces.py` and `harness_verdict.py`
do not exist yet, so the floor starts at 0.

### What Was Tried and Failed

* **Growing the claim-form regex (O1).** Every added pattern family
  invites the next reviewer to find a form with an intervening word,
  reversed order or a synonym. The 7 forms this spike found without trying
  hard, and the 0 of 7 caught, show the set is open.
* **A marker in the text (pure O3).** It clears negations, but it edits
  product text and still needs a scope and a base.
* **Joining adjacent lines naively.** A first prototype joined every line
  with its successor. That flagged innocent lines next to a hit (62 hits
  reported as 122). The join now fires only when the successor alone has
  no hit, and it also tries the hyphen-stripped join (`TOC-` then `TOU`).
* **"Current diff against a base" as the scope.** On a shared default
  branch it sweeps in unrelated merged work and stays live forever. A
  closed list of audited commits bounds both.

### Remaining Unknowns

* The real ledger load for these five shipments. The sample median is 3
  surfaced lines per merge (maximum 24, almost all in `docs/` and
  `.backlogit/`). This lifecycle discusses the non-claims more than usual.
* Whether reviewers accept the plan and review manifest leaving automated
  scope. Here they are covered by the E3 text audit, which is the ratified
  `PE-SAFETY-06` form. IM-14-F08 asked for their remaining prose to be
  scanned.
* The final closure pull request after S(D) is not audited by the test.
  Its text audit is recorded in the closure record.

## Recommendation

**Proceed** with O2 hybrid in E3. Summary:

1. Detect the threat vocabulary, not claim forms. Coverage is closed for
   every phrasing that names race, TOCTOU, time-of-check, hardlink or
   symlink swap.
2. Scan only added lines of a closed list of audited commits (harvest,
   each unit's merge and closure merges), first-parent, `--no-renames`.
3. A hit clears only through the required sentence or a closed SHA-256
   ledger (`non-claim`, `fixture`) in the test. Unused entries fail.
4. Base commits are constants in the test. The C5 step, closure and D3
   preflight fail on a skip.
5. After S(D) the list is final. Only a git-free floor over the three new
   modules remains, so later work pays nothing.
6. The recorded text audit covers the residue, as the ratified row asks.

Confidence **medium**. The mechanism evidence is strong. The ledger load
is estimated from history, and the scope choice for the plan and manifest
still needs reviewer acceptance.

### Finding Closure Map

| Finding | Status in rev 3 | How the design closes it |
|---|---|---|
| IM-14-F07.1 (blocking) | Open | No inventory: S(A)'s merge commit is audited whole, so A's test module is in scope. Harvest records its text audit, and the harvest commit is audited at C5 |
| IM-14-F08 (blocking) | Open | No path exemption. Pattern and fixture lines clear only through closed digest entries the test asserts, and unused entries fail |
| IM-14-F11 (blocking) | Open | Term presence: all 8 forms hit (8 of 8) |
| IM-14-F09 | Non-blocking | Bases are `AUDITED` constants. A skip names its reason and fails the C5 step, closure and D3 preflight |
| IM-14-F10 | Non-blocking | Both reversed forms hit (2 of 2) |
| IM-14-F12 | Non-blocking | No "added by" column. D3's files are audited with S(D)'s merge commit |
| IM-14-F13 | Informational | `--no-renames`; evidence above |
| IM-14-F14 | Non-blocking | Added lines only: 0 pre-existing hits instead of 4. Negations clear once, by digest |
| IM-14-F15 | Non-blocking | Same as IM-14-F08 |

### Proposed Drop-In Specification

This text replaces plan revision 3 lines 719-753, the whole "Non-Claim
Audit Inventory" section. The heading and anchor are unchanged, so the
cross-references at lines 190, 203 and 322 still resolve.

````markdown
### Non-Claim Audit Inventory

IM-14 and `PE-SAFETY-06` are `P2-critical`. The matrix, C5, D3 and closure
all cite this scope. It is a text audit (charter section 7.6): the test
guarantees coverage, and a recorded reviewer disposition supplies judgment.

* **Audited commits.** `tests/test_harness_noclaim_audit.py` holds a
  closed list, `AUDITED`. C5 creates it with the harvest commit and S(A)'s
  merge and closure merge commits. Each later closure appends its
  shipment's merge commit and the previous closure's merge commit. After
  S(D) closes, the list is final.
* **Scope.** Every added line of each listed commit's first-parent diff
  (`git diff --no-renames -U0 <sha>^1 <sha>`), on every path, with no
  path exemption. Renames and copies count as additions, and unchanged
  text is never rescanned. A git-free floor also scans every line of
  `harness_read.py`, `harness_surfaces.py` and `harness_verdict.py`.
* **Detector.** Case-insensitive, after whitespace runs collapse to one
  space, on each line and each adjacent pair of added lines:
  `\b(?:rac(?:e|es|ed|ing|y)|toctou|time[-\s]*of[-\s]*check|hard[-\s]*links?|hardlink\w*|symlink[-\s]*swap\w*)\b`.
  The vocabulary names the threat, not the claim form, and is closed.
* **Clearing.** A hit clears only if its line has no hit once the
  required sentence is removed, or the SHA-256 of its normalized line is
  in the test's closed `LEDGER` as `non-claim` or `fixture`. Any other
  hit fails, and so does a `LEDGER` entry that no scanned line uses. The
  task adding the line adds the entry; local review confirms it.
* **Base commits.** Only the `AUDITED` constants, never an environment
  variable. Without git or a listed commit the scan skips, naming the
  reason. The C5 step runs this module after `git fetch --unshallow` and
  fails on any skip, as closure and D3 preflight do.
* **Required sentence.** C1 writes it in the reader module docstring:
  "This reader makes no race, TOCTOU or hardlink-alias resistance claim."
  The audit asserts it is present.
* **Residue.** Claims outside the vocabulary, this plan, its review
  manifest and the final closure pull request fall to the text audit.
  Harvest, each closure and E3 record its result with the `LEDGER` count.
* **Controls.** Must hit: every claim form in IM-14-F05, F10 and F11;
  `race-` then a newline then `free`; `hard-` then a newline then `link`.
  Must not hit: `trace-free`, `embrace-safe` and `grace period`. The
  required sentence hits and clears.
````

### Size Delta and Headroom

Measured on the section text (LF-joined, UTF-8).

| Measure | Rev 3 section | Proposed | Delta | Rev 3 total | Limit (rev 1 +20%) | Projected total | Headroom left |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bytes (section) | 2400 | 2496 | +96 | — | — | — | — |
| Body bytes | — | — | +96 (+1 for the MD047 newline, CONST-G2-F01) | 76103 | 76533 | 76200 (+19.5%) | 333 |
| File bytes | — | — | +97 | 81929 | 82995 | 82026 (+18.6%) | 969 |
| Words | 326 | 368 | +42 | 12001 | 12237 | 12043 (+18.1%) | 194 |

The specification fits under cumulative measurement against rev 1 blob
`2d562820`, with no public name, reason code or task added.

### Re-Charter and E3 Scope

* **No re-charter trigger.** The design adds no subsystem, threat class,
  public name, reason code or platform mechanism. It stays one structural
  test in C5's existing file, and it audits properties the charter already
  lists as not claimed.
* **E3 scope note (not a trigger).** C5's Change cell (line 323) still
  says the audit test "creates the non-claim audit inventory with A's and
  C's files", and its CI module list omits the audit module. The
  specification states the CI duty normatively, so C5 can stay frozen.
  If E3 reviewers want the C5 cell aligned, that is a one-clause edit
  outside the section and needs the operator to widen E3 scope.
* **Open non-IM-14 carries.** CONST-G2-F01 (restore the plan's final
  newline, +1 byte) is counted above. The other non-blocking carries from
  Delta Review 2 are unchanged.

### Next Steps

1. The operator ratifies or amends this recommendation.
2. On ratification, E3 opens scoped to the IM-14 section, with rev 3 as
   baseline and the specification above as the proposed revision.
3. Harvest stays blocked until E3 publishes `PASS`.
