---
title: "PR #436 Copilot hosted-review finding inventory (all 17 rounds, all HEADs)"
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
updated_at: "2026-09-08T21:15:00-07:00"
reviewed_head: 659c8e75c236e5e2efe8da31dca2c985b9ccba41
round_15_reviewed_head: fdcf91e2e0a5d8e9c6893e060aeaecc837592271
round_16_reviewed_head: e075de2670addf74182a6b8ed7c9ef23ea0c216e
round_16_fix_head: 0b45caf82fb6b973f6b04f7851d681a8b3b64b5a
round_17_reviewed_head: 0b45caf82fb6b973f6b04f7851d681a8b3b64b5a
round_17_continuation_reviewed_head: 8711bca15f97b386641c58b302ba5b35d9aa3da1
round_17_continuation_2_reviewed_head: e0a14f5c177bf9de648560d523d5bf717850a683
round_17_continuation_3_reviewed_head: ee207be714f6a068f9f02b29aefcf51400071251
round_17_continuation_4_reviewed_head: fbb282185fc0a33a1b09dbc141d0f1c6bed8270c
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
| 16 | `e075de26` (reviewed) | 2026-09-08T19:31:49Z | 2 | 1 | 🟡 **(round-15's own fix artifacts contained 3 fresh errors — see below)** |

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

**Round 16 (this session, Ship)** is a narrow, in-scope follow-on cycle: a
fresh Copilot review at the round-15 fix HEAD (`e075de2670addf74182a6b8ed7c9ef23ea0c216e`)
found that round 15's own newly-authored artifacts contained 3 fresh
errors (F30-F32 below) — none reopen a prior finding; all 3 are same-surface
completions of the round-15 edit itself. See "Round 16 — narrow follow-on
fix" below.

**Round 17 (this session, Ship)** is a systemic-contract fix, not a fourth
literal-substitution retry: a fresh Copilot review at the round-16 fix HEAD
(`0b45caf82fb6b973f6b04f7851d681a8b3b64b5a`) found that round 16's own new
section header reproduced the identical RC-9 conflation F30 had just fixed
one section earlier — because round 16 never recorded a `round_16_fix_head`
frontmatter field, its header prose fell back to reusing the
reviewed-subject SHA for both "reviewed" and "fixed" roles. Two
literal-substitution attempts (round 15's header, round 16's header) each
tripped the same class of defect one section later, tripping a universal
circuit breaker at the third occurrence (F33 below). The operator
dispositioned this as a genuinely new systemic-contract operation: no
committed artifact may claim to identify the commit SHA that contains it;
see "Round 17 — systemic contract fix" below.

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
| F30 | R16 (e075de26, reviewed) | thread `PRRT_kwDORzpWpM6gYcYh` | `docs/reviews/2026-09-07-pr-436-adversarial-review.md:305` | Round-15's own new "post-fix disposition" section header labelled `fdcf91e2` (the pre-fix, reviewed HEAD) as "the HEAD after the round-15 commit" — conflating reviewed-HEAD with fix-HEAD, so the `READY_WITH_FOLLOWUPS` verdict was not attributable to a specific, correct current-HEAD SHA | RC-9 | P1 | C1 | **fixed** — header rewritten to name both HEADs explicitly (`fdcf91e2` reviewed-before-fix, `e075de2670addf74182a6b8ed7c9ef23ea0c216e` fix-committed-at); added a distinct `round_15_fix_head` frontmatter field alongside the pre-existing `round_15_reviewed_head` so the two are never conflated again | this session (R16) | 1 (class rec #10 of RC-9) |
| F31 | R16 (e075de26, reviewed) | thread `PRRT_kwDORzpWpM6gYcY5` | `.backlogit/reconcile/159-S-cascade-close-20260906-073211.md:184` | A 4th file carrying `856B6770`'s disposition still said `2026-09-07`, missed by round 15's per-file sweep, which believed (and stated) it had corrected "all 3 files" | RC-12 | P1 | C1 | **fixed** — same `2026-09-07`→`2026-09-08` correction with the same chronological-impossibility note used in the other 3 files | this session (R16) | 2 (class rec #2 of RC-12 — the "swept all N files" claim was itself wrong by one, a mild RC-10 flavor) |
| F32 | R16 (e075de26, reviewed) | suppressed | `docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md:30` (citations) | Round-15's own newly-authored compound-taxonomy citation claimed "17 Copilot reviews (through round 15)"; the true count through round 15 was 16 — the 17th review is the round-16 review that caught this off-by-one | RC-1 | P2 | C1 | **fixed** — citation corrected to state the count accurately across both rounds (16 through round 15, 17th is the round-16 review itself) | this session (R16) | 1 (class rec #5 of RC-1 — a compound-learning document about evidence-consistency errors contained one of its own) |
| F33 | R17 (0b45caf8, reviewed) | thread `PRRT_kwDORzpWpM6gYzGj` | `docs/reviews/2026-09-07-pr-436-adversarial-review.md:375` | Round-16's own new section header repeated the identical RC-9 conflation F30 had just fixed one section earlier: it labelled the pre-fix reviewed HEAD `e075de26` as both "reviewed" and "fixed," when round 16's fix actually committed at `0b45caf8` — because round 16 never recorded a `round_16_fix_head` frontmatter field, its own header prose fell back to reusing the reviewed-subject SHA for both roles | RC-9 (self-referential fixed-point sub-case) | P1 | C1 | **fixed systemically, not by literal substitution** — attempts 1-2 (round 15's header, round 16's header) each substituted a corrected SHA and each re-created the same class of claim one section later, tripping a universal same-error-recurrence circuit breaker at attempt 3 (full chain: `docs/memory/2026-09-08/circuit-break-pr-436-review-head-conflation.md`); the operator dispositioned this as a genuinely new systemic-contract operation rather than a fourth retry — the round-16 header now names "reviewed subject `e075de26`" / "fix committed at `0b45caf8`" explicitly, `round_16_fix_head` is added to frontmatter to close the gap, and a `reviewed_subject_sha`/`resolution_commit_sha`/`verified_subject_sha` naming contract is established so a committed artifact never again claims to name its own containing commit — see the adversarial review's new "Round 17" section for the full contract | this session (R17) | 2 (class rec #11 of RC-9 — the first RC-9 manifestation that is itself a recurrence of a same-file, same-round-window RC-9 fix, confirming the class needed a structural resolution, not another instance-level substitution) |
| F34 | R17 (8711bca1, reviewed) | thread `PRRT_kwDORzpWpM6gZuPp` | `docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md:5` (`root_cause` frontmatter) | The round-17 commit (`8711bca1`) updated this file's `citations` block to 18 reviews/round-17 data but left the searchable `root_cause` frontmatter field asserting the stale "13 Copilot rounds ... 24 distinct findings ... 12 root-cause classes" figure, so indexed/machine retrieval would summarize an outdated dataset even though the narrative citations were current | RC-2 | P2 | C1 (same-contract-surface completion of this round's own citation update, in this same file) | **fixed** — `root_cause` reworded to state both the round-13 baseline (13 rounds/56 utterances/24 findings) and the round-17 running total (18 reviews/33 distinct findings), still 12 root-cause classes, matching the citations block | this session (R17-continuation) | 1 (class rec #7 of RC-2) |
| F35 | R17-continuation (e0a14f5c, reviewed) | thread `PRRT_kwDORzpWpM6gaOaF` | `docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md:5` (`root_cause` frontmatter) | The very commit that fixed F34 (`e0a14f5c`) left `root_cause` saying "18 Copilot reviews" while the same commit's own `citations` block already said "19th is the round-17-continuation review" — F34's own fix introduced a fresh RC-2 mismatch one field away from the one it had just closed | RC-2 | P2 | C1 (same-contract-surface completion of the F34 fix, in the same field, same file) | **fixed** — `root_cause` reworded to "19 Copilot reviews ... 34 distinct findings," matching `citations` | this session (R17-continuation, second pass) | 1 (class rec #8 of RC-2 — a fix for an RC-2 defect recreated an RC-2 defect one field away, mirroring F30/F33's recursive pattern in a different root-cause class) |
| F36 | R17-continuation (e0a14f5c, reviewed) | threads `PRRT_kwDORzpWpM6gaOav`, `PRRT_kwDORzpWpM6gaObR`, `PRRT_kwDORzpWpM6gaOb4` | all 3 review/compound files' "Round 17 continuation" narrative sections | Each file's continuation narrative cited P-021 deferred-scope stash entries `A8CA35BB`/`EE1AB6DB` as "captured," but those entries existed only in the local, uncommitted `.backlogit/stash.jsonl` working-tree copy — not in the version tracked at `e0a14f5c` — so no reviewer or tool reading the branch could actually see them | RC-1 | P1 | C1 (the citing prose is same-contract-surface with this round's own capture action; the fix is publishing the entries the prose already claims exist, not new scope) | **fixed** — `.backlogit/stash.jsonl` surgically reconstructed (committed-baseline content plus exactly these 2 new JSON lines, none of the concurrent unrelated Stage working-tree entries in the same file staged or altered) so `A8CA35BB`/`EE1AB6DB` are now durably present at the fixing commit; `.backlogit/archive/stash.jsonl` (entirely Stage-owned dirty content) left untouched | this session (R17-continuation, second pass) | 3 (one distinct defect, 3 manifestations — one per citing file; class rec #6 of RC-1) |
| F37 | R17-continuation (ee207be7, auto-triggered review) | thread `PRRT_kwDORzpWpM6gaoJt` | `docs/closure/2026-09-06-159-s-151-f-closure.md` | Missing post-mode report path referenced by the closure lock-release contract — a genuine gap in an unrelated closure artifact | RC-3 | P2 | **deferred** (P-021 C1: not a completion of this round's authorized systemic-HEAD-fix surface) | deferred | `C395CFE3` | 1 |
| F38 | R17-continuation (ee207be7, auto-triggered review) | threads `PRRT_kwDORzpWpM6gaoKN`, `PRRT_kwDORzpWpM6gaoKh` | `docs/closure/2026-09-06-159-s-151-f-closure.md` (2 manifestations) | Closure condition narrower than tracker `2B68F9D6`'s actual requirement — distinct from `EE1AB6DB`'s role-attribution issue despite sharing a file/area | RC-2 | P2 | **deferred** (same authorization boundary as F37; role-attribution vs scope-completeness confirmed distinct via P-021 discovery, not merged with `EE1AB6DB`) | deferred | `24E3E464` | 2 |
| F39 | R17-continuation (fbb28218, reviewed) | suppressed | `docs/memory/2026-09-08/circuit-break-pr-436-review-head-conflation.md:103-106` (own "Option 4") | This session's own circuit-breaker continuity record framed operator authorization as "extend/waive the breaker for this exact operation," but `.github/instructions/circuit-breaker.instructions.md` defines no waiver of a tripped same-operation limit at any threshold — only explicit approval of a genuinely new, differently-mechanized operation | RC-2 | P1 | **C1 (same-contract-surface completion of this round's own circuit-break-record authorship)** | **fixed** — "Option 4" reworded to state the actual policy (approval authorizes a genuinely new operation only, never a waiver/extension); new "## Resolution" section added documenting how the operator's disposition satisfied the genuinely-new-operation test, written without naming its own containing commit SHA | this session (R17-continuation, fourth pass) | 1 (class rec #9 of RC-2 — a self-authored continuity record about a self-referential-identity defect itself briefly asserted an unsupported policy carve-out) |
| F40 | R17-continuation (fbb28218, reviewed) | suppressed | `docs/closure/2026-09-06-159-s-151-f-closure.md:103` vs `:107-112` | Table row says the deviation "closes only after `169-S` is published and ships"; the same file's narrative 4 lines later says the disposition is already unconditional and does not depend on `169-S` — internal contradiction over whether `169-S` gates the deviation's own closure or only the remediation-publication tracker | RC-2 | P2 | **deferred** (P-021 C1: unrelated closure artifact, outside this round's authorized surface) | deferred | `35CE8C55` | 1 |
| F41 | R17-continuation (fbb28218, reviewed) | suppressed | `docs/memory/compacted/2026-09-06-159s-151f-compacted.md:17` | Calls the test-suite result a "full local build," while PR #435 records the editable-install build as not applicable (dependencies unresolvable without network access) — conflates test execution with build evidence in durable memory | RC-5 | P3 | **deferred** (P-021 C1: unrelated compacted-memory artifact, outside this round's authorized surface) | deferred | `DC6F5B20` | 1 |

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
post-push step (fixed after push, this session). Round 16 (this session,
narrow follow-on) fixed F30-F32 — 3 fresh errors introduced by round 15's
own newly-authored artifacts (adversarial-review header, one missed
cascade-close reconcile file, taxonomy citation off-by-one) — none reopen a
prior finding. Round 17 (this session) fixed F33 systemically and, in a
same-file continuation pass after a second, later Copilot review at the
round-17 commit HEAD, also fixed F34 (a same-contract-surface frontmatter
staleness gap in the very citation update round 17 had just made). A third
Copilot review, at the continuation's own fixing commit (`e0a14f5c`), then
found F35 (the F34 fix itself left one field one number stale — "18" instead
of "19" reviews) and F36 (the continuation's own narrative cited 2
newly-captured stash entries that existed only in the local working tree,
not on the branch at that commit). Both were fixed in the same
same-contract-surface pass, without re-entering a literal SHA-substitution
loop. An auto-triggered review at the F35/F36 fixing commit (`ee207be7`)
then found F37 and F38 — both genuine but out-of-scope closure-artifact
gaps, both deferred via P-021 capture rather than fixed. A fourth,
explicitly-requested review at the next fixing commit (`fbb28218`, which
also corrected a stray 30-vs-31 thread-count arithmetic error) then found,
among 7 mostly-stale suppressed restatements, one genuine same-contract-surface
defect in this session's own circuit-breaker continuity record (F39, fixed)
and two further genuine but out-of-scope findings in unrelated closure/memory
artifacts (F40, F41, both deferred). Findings F01-F41 (41 distinct findings
total, up from 24 at round 13, 29 at round 15, 32 at round 16, 33 at round
17, 34 at round 17's first continuation pass, 36 at round 17's second
continuation pass) are canonical as of round 17's fourth continuation pass.

## Root-cause taxonomy (derived, not assumed)

| ID | Root-cause class | Distinct findings | Manifestations | Definition |
|---|---|---|---|---|
| **RC-9** | **Current-HEAD readiness drift** | 5 (F11, F23, F27, F30, F33) | **11** | A readiness/gate record names a HEAD that is no longer current, because the act of recording readiness creates a new commit — **F33 is the degenerate self-referential sub-case: a committed artifact's own section header tried to name the SHA of the commit that would contain it, a structural fixed-point impossibility (the SHA does not exist until the commit is made), not ordinary post-commit staleness; resolved round 17 by retiring self-attestation from committed artifacts entirely rather than by another SHA substitution** |
| **RC-11** | **Pre/post-mutation chronology falsification** | 2 (F16, F24/F28) | **9** | Evidence produced *after* an irreversible action is narrated as if it had been produced *before* it, silently converting a safety gate into a post-hoc observation |
| **RC-10** | **Cross-surface propagation incompleteness** | 2 (F15, F25) | **8** | A correction is applied to the location that was flagged, not to every location asserting the same fact |
| **RC-2** | **Machine-readable vs narrative mismatch** | 11 (F02, F13, F14, F20, F21, F29, F34, F35, F38, F39, F40) | **16** | A frontmatter/status field a tool consumes disagrees with the prose in the same or a linked artifact — **F35: a fix for one RC-2 field-mismatch (F34) recreated a fresh, adjacent RC-2 field-mismatch one number away, the same recursive shape RC-9 showed in F30→F33; F39: this session's own circuit-breaker continuity record briefly asserted an unsupported "waiver" carve-out contradicting governing circuit-breaker policy — fixed as a same-contract-surface completion of this session's own authorship; F38/F40 remain deferred, unrelated closure artifacts** |
| **RC-5** | **Cross-surface state currency** | 5 (F05, F17, F18, F19, F41) | **6** | Durable memory or committed backlog data still asserts a superseded state that query-first retrieval will resurface as a live blocker — **F41: durable memory conflates test-suite execution with build evidence, deferred, unrelated compacted-memory artifact** |
| **RC-3** | **Unsatisfied producer contract** | 4 (F03, F07, F10, F37) | **6** | A required artifact/section/source-scan the governing contract names was never produced, or was produced with only part of its required inputs — **F37: deferred, unrelated closure artifact** |
| **RC-1** | **Evidence–artifact content error** | 5 (F01, F12, F26, F32, F36) | **8** | A statement about a file, PR, or record does not match that file/PR/record as it actually exists — **new manifestation (F26): a REMEDIATION of one finding cites an unrelated record as its own tracker, propagating a fresh RC-1 defect through the very act of fixing a prior one; F32: a compound-learning document *about* evidence-consistency errors contained one of its own (an off-by-one review count); F36: a continuation narrative cited 2 P-021 stash captures as durably recorded when they existed only in the local uncommitted working tree, across 3 files** |
| **RC-6** | **Contract misreading / unsupported carve-out** | 1 (F06) | 4 | An exemption is invented to make a failing gate pass, rather than the gate result being disclosed |
| **RC-4** | **Disclosure incompleteness** | 1 (F04) | 1 | A risky/destructive action or residual risk is omitted from the record that is contractually required to carry it |
| **RC-7** | **Non-executable command** | 1 (F08) | 1 | A documented command fails when actually invoked |
| **RC-8** | **Condition/window semantics error** | 1 (F09) | 1 | A stated condition admits an interpretation that voids its own purpose |
| **RC-12** | **Temporal impossibility** | 2 (F22, F31) | 2 | A recorded date/order is physically impossible against another recorded timestamp — **F22 fixed R15; F31 is the same underlying defect surviving in a 4th file that R15's sweep believed (and stated) it had exhaustively covered, fixed R16** |

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

## Round 16 — narrow follow-on fix (this session)

**Trigger:** a fresh Copilot review at the round-15 fix HEAD
(`e075de2670addf74182a6b8ed7c9ef23ea0c216e`) surfaced 2 open threads plus 1
suppressed comment (F30-F32 above) against artifacts round 15 itself had just
authored or edited — i.e. round 15's fix (and its own compound-learning
write-up) contained fresh, in-scope defects on the same closure-evidence
surface, not new out-of-scope scope expansion.

**Classification:** all 3 findings pass the P-021 C1 same-contract-surface
test — each is a completion of the exact round-15 change already authorised
(correcting a HEAD label, a disposition date, and a citation count inside
files round 15 itself created or edited), not a new expansion. Per the
operator's explicit instruction, this cycle proceeded directly (within the
review skill's 3-cycle limit — this is the 2nd review-fix cycle of this
session, not a same-error third-attempt recurrence).

**Method, in order:**
1. Re-read the full round-16 Copilot review body (2 threaded + 1 suppressed)
   before any edit.
2. Fixed `docs/reviews/2026-09-07-pr-436-adversarial-review.md`'s round-15
   section header (F30) and added a distinct `round_15_fix_head` frontmatter
   field so reviewed-HEAD and fix-HEAD can never again be conflated in this
   file.
3. Fixed the 4th (previously missed) file carrying `856B6770`'s disposition
   date (F31) in `.backlogit/reconcile/159-S-cascade-close-20260906-073211.md`,
   using the same correction pattern already applied to the other 3 files.
4. Fixed the compound taxonomy's own review-count citation (F32), an
   off-by-one introduced by round 15's own authoring.
5. Updated this inventory and the compound taxonomy with the round-16 data
   and the reinforced lesson: **an independent adversarial re-review of a
   fix's *target* findings does not, by itself, guarantee the fix's own
   newly-authored prose is internally consistent — a fresh full sweep of the
   newly-authored text itself (dates, HEAD labels, counts) is a distinct,
   necessary step, not implied by "the flagged findings are now resolved."**

**Verdict:** F30-F32 fixed; zero new findings introduced by this narrow
cycle (verified by direct, targeted read of each edited line, not a fresh
independent-agent pass, given the narrow 3-line scope). No prior finding
reopened.

## Round 17 — systemic contract fix (this session)

**Trigger:** a fresh Copilot review at the round-16 fix HEAD
(`0b45caf82fb6b973f6b04f7851d681a8b3b64b5a`) surfaced 1 open thread
(`PRRT_kwDORzpWpM6gYzGj`, F33 above): round 16's own new section header
reproduced the identical RC-9 conflation that F30 had flagged and round 16
itself had just fixed one section earlier — a fresh instance of the same
defect class, not a reopening of F30.

**Why this round is not a fourth literal-substitution retry.** Attempt 1
(round 15's header) and attempt 2 (round 16's header) each corrected one
wrong SHA string and each immediately reproduced the same class of error one
section later. That two-for-two recurrence rate is itself the diagnostic
signal: the defect is not "an insufficiently careful SHA correction," it is
a structural fixed-point impossibility — a committed artifact cannot name
the SHA of the commit that contains it, because that SHA does not exist
until the commit is made. The circuit breaker tripped at the third
same-class occurrence (Copilot's round-17 detection); full attempt chain
and operator disposition:
`docs/memory/2026-09-08/circuit-break-pr-436-review-head-conflation.md`. The
operator explicitly dispositioned this as a genuinely new systemic-contract
operation — removing the impossible requirement rather than retrying the
same substitution a fourth time.

**Root cause, structurally stated:** a Git-tracked review/evidence artifact
must not claim to identify the commit SHA that contains it. Every prior
attempt treated "reviewed and fixed at HEAD X" as a single claim resolvable
by picking the right X; the round-17 fix instead splits that single
overloaded claim into three distinct, individually satisfiable roles:
`reviewed_subject_sha` (the commit/diff actually reviewed before a round's
fix — always a past, already-existing commit, never self-referential),
`resolution_commit_sha` (the commit that applied a prior fix, nameable only
by a *later* artifact/entry once that commit already exists — this file's
existing `round_15_fix_head` field and the newly-added `round_16_fix_head`
field are both instances of this role), and `verified_subject_sha` (a SHA
verified before the commit that reports the verification, never the
verifying commit itself). Current PR HEAD and merge readiness remain
external, dynamic facts recorded in the PR body / check-run / review
response after push — never inside a committed file.

**Method:**
1. Re-read the open thread and the circuit-breaker memory record in full
   before any edit, confirming operator disposition was recorded.
2. Added the missing `round_16_fix_head` frontmatter field to
   `docs/reviews/2026-09-07-pr-436-adversarial-review.md` (the gap whose
   absence caused round 16's header to fall back to the reviewed-subject
   SHA for both roles) and corrected the round-16 header in place to name
   both HEADs explicitly.
3. Appended a new "Round 17" section to that same file documenting the
   contract and explicitly declining to name this round's own fix commit
   SHA inside the committed file (per the contract itself) — that SHA is
   published, after push, only in the PR body's `Local Review Readiness`
   block and in the reply that resolves thread `PRRT_kwDORzpWpM6gYzGj`.
4. Updated this inventory (F33 row, RC-9 taxonomy row, canonical-count
   summary) and the compound taxonomy (new anti-pattern, new proactive
   check, updated review-count citation) with the round-17 data.
5. Did **not** modify the reviewed `162-F`/`170-S` implementation-methodology
   plan (`docs/plans/2026-09-07-review-pattern-learning-methodology-plan.md`)
   — that is a Stage-owned planning artifact and Ship editing it would
   violate P-010. The needed refinement (propagate this naming contract
   into the `review`/`pr-lifecycle` skill guidance the plan designs) is
   recorded here as a follow-up for Stage's existing `170-S` methodology
   tracker, not implemented in this session.

**Verdict:** F33 fixed structurally (contract adopted, not a fourth SHA
substitution); zero new findings introduced. Threaded count (live-verified
via `gh api graphql reviewThreads`, all rounds to date): **26 total review
threads on PR #436, 26 resolved, 0 open** once this round's reply/resolve
step (below) completes against thread `PRRT_kwDORzpWpM6gYzGj` (25 resolved,
1 open immediately before this round). Suppressed count unchanged from round
16 (F32 remains the only suppressed finding in this round window; F33 was
threaded). No prior finding reopened.

### Round 17 continuation — post-push Copilot re-review at HEAD `8711bca1`

After the round-17 commit (`8711bca1`) was pushed and thread
`PRRT_kwDORzpWpM6gYzGj` was replied-to and resolved, a fresh Copilot review
was requested and completed at the new HEAD (19th Copilot review overall on
PR #436). It surfaced **1 new threaded finding** (`PRRT_kwDORzpWpM6gZuPp`,
F34 above — fixed) and **9 suppressed comments**. Every suppressed comment
was individually checked against the current committed file content (not
assumed from the comment text alone) before disposition:

- **3 were resolved by this same round's own action** of committing
  `docs/memory/2026-09-08/circuit-break-pr-436-review-head-conflation.md`
  as durable evidence (`docs/compound/...taxonomy.md:34`,
  `docs/reviews/...adversarial-review.md:434`,
  `docs/reviews/...copilot-finding-inventory.md:349` — each cited that file
  as missing/uncommitted; it is now committed, so the citations resolve).
- **2 were stale re-surfacing of already-correct state**, verified by direct
  inspection: `docs/reviews/...adversarial-review.md:480` (claimed the PR
  body still showed the old HEAD; live `gh pr view 436` confirms the body
  already records `Reviewed HEAD: 8711bca1`) and
  `docs/closure/159-S-151-F-post-merge-closure.md:18` (claimed
  `closure_status` was still unconditional `READY`; the committed frontmatter
  already reads `READY_WITH_CONDITIONS`, matching F13's round-1 fix).
- **1 was assessed as a misreading, not a defect**:
  `docs/closure/159-S-151-F-post-merge-closure.md:233` — read in full, the
  sentence is not self-contradictory; it correctly states `27F9EC8A` *used
  to* (mis)cover this gap in an earlier round's text and has *since* been
  resolved/archived as its own distinct, unrelated finding, so it must not
  be cited here. No change made.
- **1 concerns this same file's intentional round-13-baseline convention**
  (`docs/compound/...taxonomy.md:52`, "The headline number" section) and was
  addressed as part of F34's fix: the frontmatter `root_cause` field (the
  searchable/machine-readable surface Copilot's threaded F34 comment named)
  now states current totals, while the body's "## The headline number"
  section is deliberately left as the labeled round-13 historical snapshot
  per this file's own established convention (later rounds append "Updated
  totals" addenda rather than rewriting the baseline — see the round-14/15/16
  addenda at lines ~305, ~368). This is not a new defect, and Copilot's
  suppressed comment is satisfied by the frontmatter correction it flagged.
- **2 are genuine, still-valid, but out-of-scope for this round's authorized
  operation**: `docs/closure/2026-09-06-159-s-151-f-cascade-close-completion.md:75`
  (ambiguous "matched or pre-archived" phrasing for six of seven tasks, when
  all seven were in fact already archive-resident) and
  `docs/closure/159-S-151-F-post-merge-closure.md:26` (the unsatisfied
  condition's evidence says "pending Stage publication of 163-F/171-S," but
  active stash tracker `2B68F9D6` explicitly assigns publication —
  "selective staging, committing, pushing" — to Ship, not Stage). Both
  require editing a closure artifact outside this round's authorized
  systemic-HEAD-fix contract surface (the three review/compound files plus
  the circuit-breaker record), so per the P-021 defer-capture procedure both
  were captured as active P-021 stash entries rather than fixed here:
  `A8CA35BB` (cascade-close-completion phrasing) and `EE1AB6DB` (closure-doc
  publication-ownership phrasing). Neither reopens, reverses, or requalifies
  any prior disposition; both are provisional-priority `low`, kind `task`,
  pending Stage triage.

**Continuation verdict:** F34 fixed; 0 findings deferred as a scope
expansion of the current fix (2 pre-existing, unrelated closure-doc findings
captured for future, separately authorized work instead); 0 findings
required re-entering a literal SHA-substitution loop. Thread count after
this continuation: **27 total, 27 resolved, 0 open** (the round-17
continuation's single new thread, `PRRT_kwDORzpWpM6gZuPp`, is replied-to and
resolved as part of this same pass — it is a NEW thread, not one of the
prior 26, since the review that opened it ran after those 26 were already
resolved — see the adversarial review's Round 17 section for the reply text
and commit citation).

### Round 17 continuation, second pass — Copilot re-review at HEAD `e0a14f5c`

After the first continuation's commit (`e0a14f5c`) was pushed, the PR body
was updated for the new HEAD, and thread `PRRT_kwDORzpWpM6gZuPp` was
replied-to and resolved, a further Copilot review was requested and
completed at `e0a14f5c` (20th Copilot review overall). Live GraphQL
confirmed thread `PRRT_kwDORzpWpM6gZuPp` **is** actually resolved — the
review body's own suppressed restatement to the contrary was itself stale,
consistent with the established staleness pattern (see the "always verify
against live state" note above). This review surfaced **4 new threaded
findings**:

- `PRRT_kwDORzpWpM6gaOaF` — **F35 above, fixed.** The F34 fix committed one
  round earlier had itself gone stale by the time it landed: it set
  `root_cause` to "18 Copilot reviews" while the same commit's `citations`
  block already said the 19th review was the round-17-continuation review
  itself. Fixed by restating `root_cause` as "19 Copilot reviews ... 34
  distinct findings," matching `citations`.
- `PRRT_kwDORzpWpM6gaOav`, `PRRT_kwDORzpWpM6gaObR`, `PRRT_kwDORzpWpM6gaOb4`
  — **F36 above, fixed.** All three flag the same underlying gap from three
  different citing files: the first continuation's narrative (in this file,
  the adversarial review, and the taxonomy) described P-021 stash entries
  `A8CA35BB`/`EE1AB6DB` as "captured," but the entries existed only in the
  local, uncommitted `.backlogit/stash.jsonl` working-tree copy — invisible
  to any reviewer or tool reading the committed branch. Fixed by surgically
  reconstructing `.backlogit/stash.jsonl` (committed baseline plus exactly
  the 2 new JSON lines, none of the concurrent, unrelated Stage
  working-tree entries in that same file staged or altered) so the entries
  are now durably present at the fixing commit.

One further suppressed comment surfaced:
`docs/closure/2026-09-06-159-s-151-f-closure.md:20` (missing "Invariants to
preserve" section) — genuine but out-of-scope for the same reason F35/F36's
sibling out-of-scope findings were: it requires editing a closure artifact
outside this round's authorized systemic-HEAD-fix contract surface.
Discovery-checked against both the active and archived stash (no existing
entry describes this gap) before capture as a new P-021 deferred-scope stash
entry, provisional priority `low`, kind `task`, pending Stage triage.

**Second-pass verdict:** F35 and F36 fixed, both same-contract-surface
completions of the prior pass's own work (a stale count one field away, and
publishing captures the prior pass's own prose already claimed existed); 1
new out-of-scope closure-doc finding deferred via P-021 capture, not fixed;
0 findings required re-entering a literal SHA-substitution loop. This is the
third consecutive round in which fixing the trio of review/compound files
introduced one small same-file inconsistency the very next review caught —
expected, and handled identically each time: verify live state, classify
strictly via P-021 C1, never expand into the deferred closure-doc findings.

### Round 17 continuation, third pass — auto-triggered Copilot review at HEAD `ee207be7`

After the second pass's commit (`ee207be7`) was pushed, a Copilot review
auto-triggered (no explicit re-request needed — reviews can complete purely
from push/thread activity; always poll `gh api .../pulls/436/reviews
--paginate` and match `commit_id` against actual current HEAD rather than
assuming the review found is the one explicitly requested) and completed at
`ee207be7`. This review surfaced **3 new threaded findings**, both genuinely
new and both correctly out of scope:

- `PRRT_kwDORzpWpM6gaoJt` — **F37 above, deferred.** A missing post-mode
  report path in `docs/closure/2026-09-06-159-s-151-f-closure.md`, unrelated
  to this round's authorized systemic-HEAD-fix contract surface.
- `PRRT_kwDORzpWpM6gaoKN`, `PRRT_kwDORzpWpM6gaoKh` — **F38 above, deferred.**
  Two manifestations (same file, two locations) of the same defect: the
  closure condition is narrower than tracker `2B68F9D6`'s actual
  requirement. P-021 discovery confirmed this is distinct from `EE1AB6DB`
  (role-attribution) despite sharing a file/area — both captured
  separately, not merged, per the "positive confirmation required for
  reuse" rule.

One suppressed comment also surfaced, a stale restatement of `EE1AB6DB`'s
already-captured topic — no new entry created. Discovery-checked against
both the active and archived stash before capturing `C395CFE3` (F37) and
`24E3E464` (F38); no duplicates found. All 3 threads replied-to and
resolved, citing the respective deferred entry IDs. Live GraphQL confirmed
34 total threads, 34 resolved, 0 open, as of this pass.

**Third-pass verdict:** 0 findings required fixing (both were genuinely new,
genuinely out-of-scope closure-artifact gaps); both deferred via P-021
capture with clean discovery; 0 findings required re-entering a literal
SHA-substitution loop.

### Round 17 continuation, fourth pass — explicitly-requested Copilot review at HEAD `fbb28218`

A second review, explicitly requested via the standard re-request flow, was
also in flight concurrently and completed at `fbb28218` (the commit that
corrected a 30-vs-31 stray thread-count arithmetic error found while
verifying the third pass's resolution). This review (ID `5147309535`)
produced 0 new threaded comments but 7 suppressed comments, requiring full
inspection of the suppressed body — not just threads — per the established
"0 threads ≠ clean" lesson. Classification:

- 4 stale restatements of already-captured/out-of-scope topics (repeats of
  the F37/F38 area, and one repeat of the `closure_status READY` vs
  canonical-mismatch topic already tracked elsewhere) — no new entries.
- `docs/closure/2026-09-06-159-s-151-f-closure.md:103` — **F40 above,
  deferred.** Internal contradiction: the table row says the deviation
  "closes only after `169-S` is published and ships," while the same
  file's narrative 4 lines later says the disposition is already
  unconditional. Genuinely new, out of scope. Captured as `35CE8C55`.
- `docs/memory/compacted/2026-09-06-159s-151f-compacted.md:17` — **F41
  above, deferred.** Conflates test-suite execution with build evidence
  ("full local build") when PR #435 records the editable-install build as
  not applicable. Genuinely new, out of scope. Captured as `DC6F5B20`.
- `docs/memory/2026-09-08/circuit-break-pr-436-review-head-conflation.md:103-106`
  — **F39 above, fixed.** This session's own circuit-breaker continuity
  record — the file this round's own systemic fix is grounded in — briefly
  described operator authorization as an "extend/waive the breaker for this
  exact operation" option. `.github/instructions/circuit-breaker.instructions.md`
  defines no such waiver at any threshold: explicit operator approval can
  authorize proceeding only for a genuinely new operation (a different
  author/mechanism, not a cosmetic retry), never a waiver or extension of
  the same tripped operation's own limit. This is a same-contract-surface
  completion — the defect is in this session's own authorship of the very
  record establishing the authorization this round relies on — so it was
  fixed directly: "Option 4" reworded to state the actual policy, and a new
  "## Resolution" section added documenting how the operator's actual
  disposition satisfied the genuinely-new-operation test. The Resolution
  section is itself written under the naming contract it describes: it
  names the disposition date and the mechanism-difference test satisfied,
  without naming the SHA of the commit that contains it.

Discovery-checked `35CE8C55` and `DC6F5B20` against both active and archived
stash before capture; no duplicates found. Both are suppressed findings with
no review thread, so no reply/resolve step applies — their references are
discharged via the residual-risk citations in this inventory, the
adversarial review, and the taxonomy file, per the threadless defer-capture
path.

**Fourth-pass verdict:** 1 same-contract-surface finding fixed (F39, in this
session's own circuit-break continuity record); 2 genuinely new but
out-of-scope findings deferred (F40, F41); 4 stale restatements required no
action; 0 findings required re-entering a literal SHA-substitution loop.
This pass also required republishing `.backlogit/stash.jsonl` a further time
(baseline plus 4 new lines: `C395CFE3`, `24E3E464`, `35CE8C55`, `DC6F5B20`),
using the same surgical technique, with Stage's concurrent unrelated
working-tree entries in the same file left untouched at every step.

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
