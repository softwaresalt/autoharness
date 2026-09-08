---
title: "PR #436 Copilot hosted-review finding inventory (all 15 rounds, all HEADs)"
doc_type: review-inventory
problem_type: review-pattern-analysis
category: hosted-review-finding-taxonomy
related_pr: 436
related_shipment: 159-S
related_feature: 151-F
compound_learning: docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md
source: docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md
generated_by: stage
generated_at: "2026-09-07T23:42:58-07:00"
updated_by: ship
updated_at: "2026-09-08T09:00:00-07:00"
reviewed_head: 659c8e75c236e5e2efe8da31dca2c985b9ccba41
round_15_reviewed_head: fdcf91e2e0a5d8e9c6893e060aeaecc837592271
tags: [copilot-review, review-pattern, p-018, p-021, evidence-consistency, compound-learning]
---

# PR #436 — Complete Copilot Finding Inventory

Companion inventory for
`docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md`. That
compound learning carries the reusable taxonomy, the proactive checks, and the
promotion rules; this file carries the full per-finding evidence trail that
would make the compound entry unwieldy. **The two are bidirectionally linked —
update both or neither.**

## Retrieval method (reproducible)

| Surface | Command | Raw count |
|---|---|---|
| Reviews (all authors) | `gh api repos/softwaresalt/autoharness/pulls/436/reviews --paginate` | 34 |
| — of which Copilot-authored | filter `user.login like 'copilot*'` | 15 |
| Inline review comments (all authors) | `gh api repos/softwaresalt/autoharness/pulls/436/comments --paginate` | 39 |
| — of which Copilot-authored | filter `user.login == 'Copilot'` | 20 |
| Review threads (GraphQL, `reviewThreads(first:100)`) | `gh api graphql` | 20 (19 resolved, 1 open) |
| Suppressed / non-threaded findings | parsed from `### Suppressed comments` blocks inside the 15 Copilot review bodies | 36 slots |
| Issue comments | `gh api repos/softwaresalt/autoharness/issues/436/comments --paginate` | 5 (all operator) |
| PR body Review History | `gh pr view 436 --json body` | 13 documented rounds |

**Raw Copilot finding utterances: 56** (20 threaded inline + 36 suppressed)
**as of round 13**. **Distinct findings after dedup: 24 (round 13).** The
2.3× compression ratio is itself the headline signal: most of this PR's
review volume was *the same finding re-surfacing on a new HEAD or a new
file*, not new defects.

**Round 15 update:** round 14's single fix commit (`fdcf91e2`) plus round
15's fresh hosted review (3 threaded + 2 suppressed, all at HEAD `fdcf91e2`)
add 6 more raw utterances and 5 more distinct findings (F25-F29; F26 is a
*new* defect introduced by round 14's own fix, not a re-surfacing of a prior
one). **Distinct findings after dedup, round 15: 29.** Round 15 fixed all of
F22, F24, F25, F26, F28, F29 in one coherent commit and queued F27 (PR-body
readiness) for the immediate post-push step — see "Round 15 — convergence
pass" below.

> **Suppressed findings are invisible to `reviewThreads`.** 36 of 56
> utterances (64%) lived only in the review body's free-text `body` field. Any
> gate that reads only thread state under-counts this PR's findings by nearly
> two thirds. This is a re-confirmation of the lesson already recorded in
> `docs/compound/114-S-109-F-copilot-review-fix-patterns.md`.

## Round / HEAD chronology

| Round | HEAD | Copilot review at | Threaded | Suppressed | Verdict |
|---|---|---|---|---|---|
| 1 | `90b65178` | 2026-09-06T07:53:25Z | 5 | 0 | 🟡 Changes recommended |
| 2 | `060384e5` | 2026-09-06T08:06:05Z | 4 | 2 | 🟡 |
| 3 | `7d483840` | 2026-09-06T08:17:14Z | 4 | 3 | 🟡 |
| 3-fix | `be0882c9` | 2026-09-06T08:26:57Z | 0 | 5 | 🔵 Needs a closer look |
| 4 | `42428afe` | 2026-09-06T18:20:36Z | 2 | 3 | 🟡 |
| 5 | `5f4466ff` | 2026-09-06T18:32:35Z | 2 | 3 | 🟡 |
| 6 | `373e8965` | 2026-09-06T18:52:44Z | 2 | 3 | 🟡 |
| 7 | `0aa510ce` | 2026-09-06T19:02:10Z | 0 | 1 | 🔵 |
| 8 | `ea9f18b8` | 2026-09-06T19:14:10Z | 0 | 2 | 🔵 |
| 9 | `da72c93f` | 2026-09-06T19:28:31Z | 0 | 1 | 🔵 |
| 9-fix | `ad4cb74a` | 2026-09-06T19:35:56Z | 0 | 0 | 🔵 (0 comments generated) |
| 10 | `46176517` | 2026-09-08T04:34:56Z | 6 | 1 | 🟡 |
| 11 | `dd796a53` | 2026-09-08T04:50:29Z | 0 | 5 | 🔵 |
| 12 | `094bd157` | 2026-09-08T05:06:34Z | 8 | 3 | 🟡 |
| 13 | `659c8e75` | 2026-09-08T06:16:06Z | 1 | 4 | 🟡 |
| 14 | `fdcf91e2` | (Ship, single-round fix; no fresh hosted review requested before round 15) | — | — | 🟡 partial fix |
| 15 | `fdcf91e2` (reviewed) | 2026-09-08 (round-15 review) | 3 | 2 | 🟡 **(convergence pass — see below)** |

Note the shape: **`ad4cb74a` produced literally zero comments, and rounds 7-9
produced zero threads — yet the PR was not clean.** Four more substantive
rounds followed. "Zero new threads" was a false convergence signal five
separate times on this PR.

**Round 14 (`fdcf91e2`, Ship)** resolved thread `PRRT_kwDORzpWpM6gHgcP`
(AF-07/F18: committed stash still showed `856B6770` active) by publishing
Stage's already-authored archival of `856B6770` into `.backlogit/stash.jsonl`
/ `.backlogit/archive/stash.jsonl`, and updated `closure_status` from `READY`
to `READY_WITH_CONDITIONS` in the two files it touched
(`docs/closure/159-S-151-F-post-merge-closure.md`,
`docs/closure/2026-09-06-159-s-151-f-closure.md`), adding a new unsatisfied
`conditions:` entry. **That new condition cited the already-archived,
unrelated finding `27F9EC8A` as its tracker** (round 14's own commit message
acknowledges this was a deliberate stopgap: *"only the currency-gap entry
`27F9EC8A` is republished in active form ... as the truthful, concrete
publication-gap citation, since the durable remediation identity ... cannot
be coherently published in this round"*) — this is the direct root cause of
round 15's thread `PRRT_kwDORzpWpM6gJ3AI` (F26 below): republishing an
archived, semantically-unrelated finding as a live tracker is itself a new
manifestation of RC-1 (evidence–artifact content error), because it makes a
machine-readable `conditions:` entry point at a stash record that is not,
and was never intended to be, about the cited gap. Round 14 also did **not**
touch `docs/closure/2026-09-06-159-s-151-f-cascade-close-completion.md`, the
reconcile pre-mode report, the compacted memory file, or the PR body —
leaving four of round 13's/round-12-and-earlier's classes of defect present
on those untouched surfaces, which is exactly what round 15's hosted review
(3 threads + 2 suppressed) found.

**Round 15 (this session, Ship)** is the comprehensive convergence pass:
see "Round 15 — convergence pass" below for the full finding-by-finding
disposition.

## Distinct finding inventory

Legend — **RC** = root-cause class (see taxonomy below). **P-021** = scope
classification at the time of capture. **Rec** = manifestation count across
rounds/HEADs.

| # | Round/HEAD | Source | File / surface | Issue (concise) | RC | Sev | P-021 scope | Resolution | Fixing commit / stash | Rec |
|---|---|---|---|---|---|---|---|---|---|---|
| F01 | R1 `90b65178` | thread `…6fqK7Q` | `.backlogit/reconcile/159-S-pre-*.md` | 6 tasks recorded as queue-resident `matched`; they were archive-resident `pre-archived`, contradicting the cascade report's own snapshot | RC-1 | P1 | C1 in-scope | fix | `060384e5` | 1 |
| F02 | R1 `90b65178` | thread `…6fqK7T` | `docs/closure/159-S-151-F-post-merge-closure.md` | Evidence summary says lock condition open + `READY_WITH_CONDITIONS`; own frontmatter says satisfied + `READY` | RC-2 | P1 | C1 | fix | `060384e5` | 1 |
| F03 | R1 `90b65178` | thread `…6fqK7V` | same | Claims pre/cascade/post reports exist; post-mode report absent though SKILL.md:327-348 requires it before lock release | RC-3 | P1 | C1 | fix (report authored) | `060384e5` | 1 |
| F04 | R1 `90b65178` | thread `…6fqK7Z` | `docs/closure/2026-09-06-159-s-151-f-closure.md` | Risky Action Record says "no destructive action"; session deleted a lock and ran a cascade archival | RC-4 | P1 | C1 | fix | `060384e5` | 1 |
| F05 | R1 `90b65178` | thread `…6fqK7e` | `docs/memory/compacted/2026-09-06-159s-151f-compacted.md` | Durable memory still says P-015 closure pending operator authorization after it completed | RC-5 | P2 | C1 | fix | `060384e5` | 1 |
| F06 | R2 `060384e5` | thread `…6fqO5p` | `.backlogit/reconcile/159-S-pre-*.md` | Task-only filter applied to the per-item `expected_status` check; `151-F` was `status-mismatch` ⇒ required `HALT`, not `PROCEED` | RC-6 | **P0** | C1 (carve-out withdrawn) | fix → disclosed deviation | `7d483840` | 4 |
| F07 | R2 `060384e5` | thread `…6fqO5u` | `docs/closure/2026-09-06-159-s-151-f-closure.md` | Points at runtime report only; contract requires inline structured validator evidence (probe/outcome/checkpoint/verdict/blockers) | RC-3 | P2 | C1 | fix | `7d483840` | 1 |
| F08 | R3 `7d483840` | thread `…6fqSr-` | same | `git revert` on a merge commit fails without `-m <mainline>`; rollback procedure non-executable as written | RC-7 | P1 | C1 | fix | `be0882c9` | 1 |
| F09 | R3 `7d483840` | thread `…6fqSsD` | same | "whichever comes first" can end the validation window at the next CI run, before the release is published | RC-8 | P2 | C1 | fix | `be0882c9` | 1 |
| F10 | R2-R3-R3fix | suppressed ×3 | `.backlogit/reconcile/159-S-cascade-close-*.md` | Records only absent `custom_fields.source_deliberation_id`; the other two engine-defined sources (description text, `references`) never scanned ⇒ `allowed_ids` unverifiable | RC-3 | P1 | C1 | fix (operator-authorised R4) | `42428afe` | 3 |
| F11 | R2,R3,R3fix,R4,R6,R10,R11 | suppressed ×5 + threads `…6fuMPT`, `…6gGGaG` | PR body / Local Review Readiness | Readiness block records a stale reviewed HEAD; current-HEAD Copilot check incomplete | RC-9 | P2 | C1 | partially self-resolving; never structurally fixed | (none) | **7** |
| F12 | R4 `42428afe` | suppressed ×2 | `docs/closure/2026-09-06-159-s-151-f-closure.md` (Affected Runtime Surfaces §, Monitoring Plan §) | PR #435 described as templates/skills/tests-only; it also changed `src/autoharness/verify_workspace.py` and the installed Ship agent | RC-1 | P2 | C1 | fix (verified via `gh pr view 435 --json files` first) | `5f4466ff` | 2 |
| F13 | R4,R5,R11,R12 | threads `…6ft_fB`, `…6fuELJ`, `…6gGfcV` + suppressed ×2 | `docs/closure/159-S-151-F-post-merge-closure.md:18` (`closure_status`) | Machine-readable `READY` makes `closure_complete()` unblock successors while an unresolved pre-mode `HALT` / undispositioned deviation stands | RC-2 | **P0** | C1 → **deferred** | disclosed → operator disposition (R10/R13) | `15A02E21`, `856B6770` | 5 |
| F14 | R5 `5f4466ff` | thread `…6fuELJ` | `.backlogit/reconcile/159-S-pre-*.md:130` | Report's own `recommendation: PROCEED` contradicts its own `status-mismatch` classification | RC-2 | P1 | deferred | disclosed | `15A02E21` | 1 |
| F15 | R6-R9 | suppressed ×7 | 4 closure/memory records (Stash Disposition, Risky Action Record, Follow-Ups, Outcome, Releasability, headings, opening sentences) | `15A02E21`'s unresolved-authorization risk fixed in one location at a time; every round found another unswept location | RC-10 | P2 | C1 | fix (4 sequential sweeps) | `0aa510ce`→`ea9f18b8`→`da72c93f`→`ad4cb74a` | **7** |
| F16 | R5,R11,R12 | thread `…6gGfcv` + suppressed ×5 | cascade-close + pre-mode reports, cascade-close-completion | Step 0(c) three-source linked-deliberation scan was **reconstructed after** the destructive cascade but presented as pre-close evidence; a post-hoc scan cannot recreate the pre-mutation halt opportunity | RC-11 | **P0** | **deferred** | disclosed → operator disposition (R13) | `856B6770` | **7** |
| F17 | R10 `46176517` | threads `…6gGGZr`, `…6gGGZ7` | `.backlogit/stash.jsonl:53`, `docs/closure/2026-09-06-159-s-151-f-closure.md` | Committed stash still shows `15A02E21` active/`REQUIRES DELIBERATION: yes`; `169-S` absent from branch and `main` — query-first retrieval surfaces a false unresolved blocker | RC-5 | P1 | **deferred** (Stage-owned) | deferred | `1CD92B69` | 2 |
| F18 | R13 `659c8e75` | thread `PRRT_kwDORzpWpM6gHgcP` | `.backlogit/stash.jsonl:55` | Same currency gap, now for `856B6770` — Copilot names it explicitly as a recurrence of F17 | RC-5 | P1 | **deferred** | **fixed** (published `856B6770` archival) | `fdcf91e2` (R14) | 1 (class rec #2) |
| F19 | R12 `094bd157` | thread `…6gGfdU` | `docs/memory/compacted/2026-09-06-159s-151f-compacted.md:108` | Round-12 finding absent from durable compacted memory; still unconditional `READY` ⇒ recovery from memory loses the live safety issue | RC-5 | P1 | C1 | fix | `659c8e75` | 1 |
| F20 | R12 `094bd157` | thread `…6gGfc_` | `docs/closure/2026-09-06-159-s-151-f-closure.md:288` | Operational closure declares `READY` / "nothing pending" while the same file's completion record admits an open deviation | RC-2 | P1 | C1 | fix | `659c8e75` | 1 |
| F21 | R13 `659c8e75` | suppressed | `docs/closure/159-S-151-F-post-merge-closure.md:231` | Verdict line still says "one residual risk open for disposition" while lines 241-247 say it was dispositioned — over-correction residue | RC-2 | P2 | C1 | fixed (verdict/closing sentence rewritten for `READY_WITH_CONDITIONS`) | `fdcf91e2` (R14) | 1 |
| F22 | R13 `659c8e75` | suppressed | `docs/closure/2026-09-06-159-s-151-f-closure.md:125` | Disposition dated `2026-09-07` but `856B6770` was created `2026-09-08T04:53:59Z` — the disposition predates the finding it dispositions | RC-12 | P1 | C1 | **fixed** (`2026-09-07`→`2026-09-08` corrected in all 3 closure/memory files carrying this specific entry's disposition date, with an explicit chronological-impossibility note; unrelated correctly-dated `15A02E21` disposition left untouched) | this session (R15) | 1 |
| F23 | R13 `659c8e75` | suppressed | `docs/closure/159-S-151-F-post-merge-closure.md:194` | PR body still records `856B6770` undispositioned / `READY_WITH_FOLLOWUPS` at `094bd157` / P-018 blocked, contradicting the file's current-HEAD claim | RC-9 | P2 | C1 | fixed (canonical file now states current disposition; PR body itself updated at R15, see F27) | `fdcf91e2` (R14) + this session (R15, PR body) | 1 |
| F24 | R13 `659c8e75` | suppressed ("previously missed") | `.backlogit/reconcile/159-S-pre-*.md:114` | Scan still placed inside the check "reverified immediately before closure" — remains false pre-mutation evidence | RC-11 | P1 | C1 | **fixed** — explicit chronology-correction paragraph added, clarifying the scan was reconstructed post-hoc in round 4 (`42428afe`), not live at report-generation time | this session (R15) | 1 (class rec #9, now closed) |
| F25 | R15 (fdcf91e2, reviewed) | thread `PRRT_kwDORzpWpM6gJ2_g` | `docs/closure/2026-09-06-159-s-151-f-cascade-close-completion.md:172` | Still claimed `closure_complete('159-S')==True`/topology gate unblocked though canonical closure is `READY_WITH_CONDITIONS` (round 14 did not touch this file) | RC-10 | P1 | C1 | **fixed** — frontmatter `closure_status`→`READY_WITH_CONDITIONS`, Outcome section rewritten to state `closure_complete('159-S')` currently returns `False`, live-verified against `topology.py` | this session (R15) | 1 (class rec #10) |
| F26 | R15 (fdcf91e2, reviewed) | thread `PRRT_kwDORzpWpM6gJ3AI` | `.backlogit/stash.jsonl:55` | Committed active `27F9EC8A` says archived and is misused as the tracker for the distinct `163-F`/`171-S`/`169-S` publication gap (round 14's own stopgap, self-acknowledged in its commit message) | RC-1 | P1 | C1 | **fixed** — index-only selective patch: `27F9EC8A` restored to archived (its real, unrelated, already-resolved finding), new dedicated active tracker `2B68F9D6` created by Stage for the publication gap; all doc references to `27F9EC8A`-as-tracker replaced with `2B68F9D6` | this session (R15) | 1 (class rec #3 of the stash-currency/tracker-misuse family) |
| F27 | R15 (fdcf91e2, reviewed) | thread `PRRT_kwDORzpWpM6gJ3Au` | `docs/closure/159-S-151-F-post-merge-closure.md:18` (PR body Local Review Readiness) | PR body readiness block covers old HEAD `659c8e75`/`READY` rather than current HEAD and conditional closure | RC-9 | P2 | C1 | **queued for fix at the post-fix HEAD** (PR body updated after this commit is pushed, per the required workflow's ordering — readiness must be recorded for the HEAD it actually describes) | this session (R15, post-push step) | 1 (class rec #9 of RC-9) |
| F28 | R15 (fdcf91e2, reviewed) | suppressed | `.backlogit/reconcile/159-S-pre-20260906-072505.md` | Post-hoc linked-deliberation reconstruction (round 4) still narrated as immediately-pre-close evidence | RC-11 | P1 | C1 | **fixed** — same fix as F24 (single edit resolves both the round-13 suppressed finding and this round-15 recurrence) | this session (R15) | see F24 |
| F29 | R15 (fdcf91e2, reviewed) | suppressed | `docs/memory/compacted/2026-09-06-159s-151f-compacted.md` | Compacted memory still asserted unconditional `READY`, contradicting canonical `READY_WITH_CONDITIONS` | RC-2 / RC-10 | P1 | C1 | **fixed** — new third addendum (`2026-09-08, third`) explicitly retracts the prior "unconditional READY" conclusion and states the current, correct `closure_status`/tracker/`closure_complete()` facts | this session (R15) | 1 (class rec #6 of RC-2) |

### Chronology preserved, duplicates collapsed

The recurrence counts above are *manifestation* counts. Every manifestation is
attributable to a specific round/HEAD in the "Round/HEAD" column; the table
collapses them into one row per distinct defect so the taxonomy is not skewed
by re-statement volume. Four findings (F21-F24) surfaced in round 13's own
review at the current HEAD and were **unfixed** as of round 13, because the
operator authorised exactly one bounded fourth PR-fix round and no fifth
cycle at that time. Round 14 (`fdcf91e2`) subsequently fixed F18/F21/F23 (in
the two files it touched) but, in doing so, introduced F26 (a new RC-1
manifestation: citing the wrong, already-archived stash entry as a live
tracker) and left F22/F24 untouched because they lived in files round 14
did not edit. Round 15 (this session) is a **comprehensive convergence
pass** that fixed every one of F22, F24, F25, F26, F28, F29 in one coherent
evidence-graph edit, and queued F27 (PR-body readiness) for the immediate
post-push step. Findings F01-F29 (29 distinct findings total, up from 24 at
round 13) are canonical as of round 15.

## Root-cause taxonomy (derived, not assumed)

| ID | Root-cause class | Distinct findings | Manifestations | Definition |
|---|---|---|---|---|
| **RC-9** | **Current-HEAD readiness drift** | 3 (F11, F23, F27) | **9** | A readiness/gate record names a HEAD that is no longer current, because the act of recording readiness creates a new commit |
| **RC-11** | **Pre/post-mutation chronology falsification** | 2 (F16, F24/F28) | **9** | Evidence produced *after* an irreversible action is narrated as if it had been produced *before* it, silently converting a safety gate into a post-hoc observation |
| **RC-10** | **Cross-surface propagation incompleteness** | 2 (F15, F25) | **8** | A correction is applied to the location that was flagged, not to every location asserting the same fact |
| **RC-2** | **Machine-readable vs narrative mismatch** | 6 (F02, F13, F14, F20, F21, F29) | **10** | A frontmatter/status field a tool consumes disagrees with the prose in the same or a linked artifact |
| **RC-5** | **Cross-surface state currency** | 4 (F05, F17, F18, F19) | **5** | Durable memory or committed backlog data still asserts a superseded state that query-first retrieval will resurface as a live blocker |
| **RC-3** | **Unsatisfied producer contract** | 3 (F03, F07, F10) | **5** | A required artifact/section/source-scan the governing contract names was never produced, or was produced with only part of its required inputs |
| **RC-1** | **Evidence–artifact content error** | 3 (F01, F12, F26) | **4** | A statement about a file, PR, or record does not match that file/PR/record as it actually exists — **new manifestation (F26): a REMEDIATION of one finding cites an unrelated record as its own tracker, propagating a fresh RC-1 defect through the very act of fixing a prior one** |
| **RC-6** | **Contract misreading / unsupported carve-out** | 1 (F06) | 4 | An exemption is invented to make a failing gate pass, rather than the gate result being disclosed |
| **RC-4** | **Disclosure incompleteness** | 1 (F04) | 1 | A risky/destructive action or residual risk is omitted from the record that is contractually required to carry it |
| **RC-7** | **Non-executable command** | 1 (F08) | 1 | A documented command fails when actually invoked |
| **RC-8** | **Condition/window semantics error** | 1 (F09) | 1 | A stated condition admits an interpretation that voids its own purpose |
| **RC-12** | **Temporal impossibility** | 1 (F22) | 1 | A recorded date/order is physically impossible against another recorded timestamp — **now fixed (R15)** |

## Escape analysis

All 24 round-1-through-13 findings escaped the local `review` skill and
reached hosted review. Round 14's F26 (a *new* defect created by round 14's
own fix) also escaped, because round 14 ran no fresh local-review pass over
its own edit before pushing. Zero of F01-F26 were caught by the pre-PR local
review or by CI. Contributing factors, in order of contribution:

1. **The local review reviews the *diff*; these defects are properties of the
   *evidence graph*.** RC-2/RC-5/RC-10 defects are invisible in a single-file
   diff hunk — they only appear when two artifacts are read against each other.
2. **The local review runs once, before the fix commits exist.** RC-9 and
   RC-11 are *created by* the act of remediating, so a pre-fix review cannot
   observe them.
3. **No persona owned "is this evidence internally consistent and temporally
   possible?"** Constitution/Correctness/Maintainability/Python/Learnings-Researcher
   plus Template Integrity all review *content*, not *evidence coherence*.
4. **Docs/backlog-only PRs were implicitly treated as low-risk.** They are
   not: this PR's `closure_status` field mechanically unblocks successor
   shipments via `closure_complete()`.
5. **A fix that publishes one piece of Stage-authored evidence can itself
   introduce a new RC-1 defect (round 14 → F26) if the fixer does not verify
   that a cited tracker ID actually names the gap being cited, not merely
   that *some* active tracker exists.** Round 15 broke this cycle by running
   an independent adversarial re-review (a fresh `code-review`-agent pass,
   not a self-check) of its own diff before committing — see the compound
   taxonomy's round-15 addendum for the generalised proactive check this
   produces.

## Round 15 — convergence pass (this session)

**Trigger:** the operator explicitly stated the review loop was not
converging (round 14 fixed 3 of round 13's 4 unfixed findings but introduced
one new one, F26) and authorised a comprehensive convergence pass rather than
another single-thread-at-a-time cycle.

**Method, in order:**
1. Re-read the full round-15 Copilot review body and all 3 open threads plus
   the 2 suppressed comments (F25-F29 above) before any edit — never
   thread-only.
2. Cross-checked every finding against ground truth: ran
   `FilesystemTopologyReaders('.').closure_complete('159-S')` live (returns
   `False`, confirming AF-05's mechanical-enforcement question is *already*
   correctly implemented in `src/autoharness/gates/topology.py` — no code
   change was needed, only a truthful docs description); read
   `.backlogit/archive/stash.jsonl`'s `856B6770` record directly to establish
   its ground-truth `created_at` (`2026-09-08T04:53:59Z`) rather than trusting
   any doc's restated date.
3. Applied one coherent fix across all 6 affected files (see the finding rows
   above for the per-file disposition), using an index-only staged patch for
   the two stash JSONL files so Stage's other, unrelated uncommitted work
   (6 further active entries + 1 archive addition + a `15A02E21` text edit)
   remained untouched and unpublished (P-010: Ship publishes, never edits or
   triages, stash semantics).
4. Commissioned an independent adversarial `code-review`-agent pass over the
   resulting diff (not a self-check) before committing, specifically to catch
   any round-14-style "fix introduces a new RC-1" regression. It reported all
   9 findings RESOLVED and zero new P0/P1 issues.
5. Refreshed `docs/reviews/2026-09-07-pr-436-adversarial-review.md` for the
   post-fix HEAD (before/after disposition of every AF-01–AF-11) and this
   inventory file, consolidating rather than duplicating.

## Cross-references

- Compound learning (taxonomy, proactive checks, promotion rules):
  `docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md`
- Adversarial re-review of this same PR, refreshed for the round-15 fixed
  HEAD: `docs/reviews/2026-09-07-pr-436-adversarial-review.md`
- Prior related learnings consolidated rather than duplicated:
  `docs/compound/114-S-109-F-copilot-review-fix-patterns.md` (suppressed
  comments, "0 threads ≠ clean", unenforced closure conditions),
  `docs/compound/093-S-review-loop-convergence.md` (unbounded review loops),
  `docs/compound/2026-08-12-hosted-review-catches-fail-closed-gaps-local-review-and-ci-miss.md`
  (hosted review catches what local review + CI miss),
  `docs/compound/2026-09-03-copilot-review-surfaces-latent-parent-id-closure-blocker.md`
  (verify hosted findings against real code before acting).
