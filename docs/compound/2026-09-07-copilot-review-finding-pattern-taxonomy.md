---
title: "Hosted-review finding patterns are predictable: a 12-class taxonomy and a proactive pre-PR evidence-consistency gate"
problem_type: review-coverage-gap
category: hosted-review-pattern-learning
root_cause: "Local review reviews the diff, not the evidence graph; and it runs once, before the remediation commits that create the most recurrent defect classes exist. Across PR #436's 13 Copilot rounds, 56 raw finding utterances compressed to 24 distinct findings in 12 root-cause classes, and 100% escaped local review and CI. The three highest-volume classes (current-HEAD readiness drift, pre/post-mutation chronology falsification, cross-surface propagation incompleteness) are all structural properties of multi-artifact evidence sets that no single-file diff review can observe, and two of them are actually *created by* the act of remediating a prior round."
resolution_type: process
severity: high
component: "review skill / pr-lifecycle skill / Ship agent / compound library"
related_pr: 436
related_shipment: 159-S
related_feature: 151-F
inventory: docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md
source: docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md
doc_type: learning
tags:
  - copilot-review
  - review-pattern
  - evidence-consistency
  - p-018
  - p-021
  - compound-learning
  - closure-evidence
  - current-head-drift
  - chronology
  - machine-readable-narrative-parity
  - proactive-detection
  - self-inflicted-regression
  - suppressed-findings-first-class
citations:
  - "PR #436 (chore: post-merge closure for 151-F), 17 Copilot reviews (through round 15), 20+ threads, 36+ suppressed findings"
  - "docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md (full per-finding evidence trail, updated through round 15/F29)"
  - "docs/reviews/2026-09-07-pr-436-adversarial-review.md (independent re-review at HEAD 659c8e75; round-15 post-fix disposition appended)"
  - "src/autoharness/gates/topology.py:294 _closure_artifact_complete / :654 closure_complete"
  - "docs/compound/114-S-109-F-copilot-review-fix-patterns.md (suppressed comments; unenforced closure conditions)"
  - "docs/compound/093-S-review-loop-convergence.md (bounded review loops)"
---

# Hosted-review findings are predictable — stop re-discovering them one round at a time

**Companion inventory:** `docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md`
(one row per distinct finding, round/HEAD, fixing commit, recurrence count).
This file carries the *reusable* half: the taxonomy, the proactive checks, the
promotion rule, and the metrics. Keep the two in sync.

## The headline number

PR #436 took **13 Copilot review rounds**. It produced **56 raw finding
utterances** that deduplicate to **24 distinct findings** in **12 root-cause
classes**. **Zero** were caught by the local `review` skill or by CI.
**64% of utterances (36/56) were suppressed, non-threaded findings** visible
only in the review body's free-text field.

Five separate times the PR looked converged (`ad4cb74a` generated literally
zero comments; rounds 7-9 opened zero threads) and four more substantive
rounds followed each time.

The recurrence structure is the point: this was not 24 unrelated defects
found 13 times. It was **a small number of structural evidence-integrity
defect classes, re-manifesting on new surfaces and new HEADs**.

## Why local review missed all 24

Four causes, in order of contribution:

1. **Local review reviews the *diff*. These defects are properties of the
   *evidence graph*.** A frontmatter field contradicting prose two files away
   is invisible in any single-file hunk.
2. **Local review runs once — *before* the remediation commits exist.** The
   two highest-volume classes (`RC-9` current-HEAD drift, `RC-11` chronology
   falsification) are *manufactured by the act of remediating*. A pre-fix
   review is structurally incapable of seeing them.
3. **No persona owned "is this evidence internally consistent and temporally
   possible?"** Constitution / Correctness / Maintainability / Python /
   Template Integrity all review content quality, not evidence coherence.
4. **A docs/backlog-only PR was treated as low-risk.** It was not. This PR's
   `closure_status: READY` field is read by
   `_closure_artifact_complete()` (`src/autoharness/gates/topology.py:294`)
   and mechanically unblocks successor shipments. **A documentation PR that
   writes a field a gate consumes is a gate change wearing a docs costume.**

## The taxonomy — 12 root-cause classes, with PR #436 examples

Ordered by manifestation volume, not by discovery order.

### RC-9 — Current-HEAD readiness drift (8 manifestations, the most recurrent)

The readiness/gate record names a HEAD that is no longer current, **because
recording readiness creates a new commit**. Copilot raised this at
`060384e5`, `7d483840`, `be0882c9`, `373e8965`, `46176517`, `dd796a53`,
`659c8e75` — seven rounds — and it was never structurally fixed, only
re-chased.

> "The PR readiness record is stale: GitHub reports current HEAD
> `060384e5…`, while the PR description records reviewed HEAD `90b65178…`."

**This class is self-generating and cannot be fixed by being more careful.**
It needs a *contract*, not diligence: state readiness as a claim about a
named SHA, and require re-verification only when the diff's *semantic content*
changes, not when the readiness block itself is rewritten.

### RC-11 — Pre/post-mutation chronology falsification (8)

Evidence produced *after* an irreversible action is narrated as if produced
*before* it — silently converting a safety gate into a post-hoc observation.

> "Byte-identical post-close evidence establishes the eventual empty set, but
> it cannot establish that the pre-mutation guard ran."

This is the highest-severity class in the taxonomy. A reconstructed scan can
prove *what the data was*; it can never recreate *the halt opportunity that
was never offered*. Note the specific trap: the reconstruction here was
genuinely byte-identical and genuinely correct, which is exactly why it read
as compliant evidence for five rounds.

### RC-10 — Cross-surface propagation incompleteness (7)

A correction is applied to the location that was flagged, not to every
location asserting the same fact. Rounds 6, 7, 8 and 9 of PR #436 were
*entirely* this: each round fixed one more stale assertion about the same
`15A02E21` risk (Stash Disposition §, then Risky Action Record opening, then
Follow-Ups §, then Outcome §, then Releasability §, then a section heading,
then an opening sentence).

**Four review rounds were spent on one fact that had seven homes.**

### RC-2 — Machine-readable vs narrative mismatch (9 across 5 findings)

A frontmatter/status field a tool consumes disagrees with prose in the same
or a linked artifact. Includes the inverse failure (`F21`): over-correcting
the prose and leaving a stale qualifier behind.

> "`closure_status: READY` makes `topology.py` treat this shipment as
> complete and unblock successors, but this record itself says pre-mode
> found a `status-mismatch` whose required result was `HALT`."

### RC-5 — Cross-surface state currency (5)

Durable memory or **committed backlog data** still asserts a superseded state
that query-first retrieval resurfaces as a live blocker. PR #436 hit this
three times: compacted memory (R1), stash entry `15A02E21` (R10), stash entry
`856B6770` (R13 — **still open**). Copilot named the third one as a
recurrence of the second in its own words: *"This recreates the same
data-currency gap already identified for `15A02E21`."*

**When a reviewer tells you a finding is a recurrence, that is a promotion
signal, not a comment.**

### RC-3 — Unsatisfied producer contract (5)

A required artifact/section/source-scan the governing contract names was
never produced, or produced from only some of its required inputs. PR #436:
a missing post-mode report; a closure artifact that pointed at a runtime
report instead of inlining the required structured evidence; a
linked-deliberation scan that read 1 of 3 engine-defined sources.

### RC-1 — Evidence–artifact content error (3)

A statement about a file/PR/record doesn't match that file/PR/record.
PR #436 described PR #435's scope as "templates/skills/tests only" when it
also changed `src/autoharness/verify_workspace.py` and the installed Ship
agent. **The fix here was verified by running `gh pr view 435 --json files`
first — never trust review text or your own prior summary about a fact you
can query.**

### RC-6 — Contract misreading / unsupported carve-out (4)

An exemption is invented to make a failing gate pass, instead of the gate
result being disclosed. PR #436's "task-artifact-filter parity" carve-out was
withdrawn in round 2 and then **re-surfaced three more times** in downstream
summaries that had copied it.

**A withdrawn claim propagates exactly like a stale fact (RC-10). Withdrawing
it in one place does not withdraw it.**

### RC-4 / RC-7 / RC-8 / RC-12 — the low-volume, high-signal classes

| Class | PR #436 example | Why it matters |
|---|---|---|
| **RC-4** Disclosure incompleteness | Risky Action Record said "no destructive action occurred" after a lock deletion + cascade archival | A contract-required disclosure slot that is filled with a falsehood is worse than an empty one |
| **RC-7** Non-executable command | `git revert <merge-sha>` documented as the rollback; fails without `-m 1` | Rollback instructions are *only* exercised in an emergency — a broken one is discovered at the worst moment |
| **RC-8** Condition/window semantics | "next CI run or next release, whichever comes first" ends observation before the artifact ships | A condition that admits an interpretation voiding its own purpose |
| **RC-12** Temporal impossibility | Disposition dated `2026-09-07`; the stash entry it dispositions was created `2026-09-08T04:53:59Z` | Cheap to detect mechanically, and a reliable tell that a narrative was written from intent rather than from evidence |

## Proactive pre-PR checks — one per class

Run these **before** requesting hosted review, and **again after every
review-fix commit**. Each maps to a class above.

| Class | Proactive check | Mechanisable? |
|---|---|---|
| RC-9 | Compare the readiness block's stated SHA to `git rev-parse HEAD` **as the last action before push**; if a fix commit changed only the readiness block itself, say so explicitly rather than re-running the whole gate | Yes — trivial SHA compare |
| RC-11 | For every claim of the form "X was verified/collected before Y", locate the artifact carrying X and confirm its commit/timestamp precedes Y's. If X was reconstructed, the word "reconstructed" must appear in the same paragraph | Partly — grep for pre-mutation verbs, then manual |
| RC-10 | `git grep` the **identifier** of every corrected fact (stash ID, shipment ID, verdict token) across all touched files; every hit must agree. Do this *after* the fix, not before | Yes — grep-and-compare |
| RC-2 | Extract every frontmatter field that a tool consumes; assert prose agreement in the same file and in every file that cites it. Then check for *stale qualifiers* left by over-correction | Partly |
| RC-5 | For every `.backlogit/` entity named in the narrative, read the **committed** record (`git show HEAD:<path>`) — not the working tree — and confirm it agrees | Yes |
| RC-3 | Re-read the governing SKILL/instruction section, enumerate its required outputs and required *inputs*, and tick each one against the artifact | No — requires contract reading |
| RC-1 | Any statement about another PR/file/record must be re-derived from the source (`gh pr view N --json files`, `git show`), never copied from a prior summary | Yes |
| RC-6 | Any sentence that explains why a gate did **not** apply is a carve-out. Either the contract text supports it verbatim, or it is a disclosed deviation. There is no third option | No — judgment |
| RC-4 | Every contract-required disclosure slot (risky actions, residual risk, deviations) must be filled from the session's actual action log, not from memory | Partly |
| RC-7 | Every command in the artifact is copy-paste executed (or dry-run) before the artifact is committed | Yes |
| RC-8 | Every condition/window gets read adversarially: "what is the earliest moment this is satisfiable, and is that the moment I meant?" | No — judgment |
| RC-12 | Assert `disposition_date >= finding_created_at` for every disposition; assert every stated ordering against real timestamps | Yes |

## The reusable evidence-consistency checklist

Use verbatim for any PR whose payload is evidence (closure records,
reconcile reports, memory compactions, backlog publications, review
histories). **Run it against the branch tree (`git show HEAD:<path>`), never
against the working tree** — untracked local artifacts are invisible to
reviewers and to `main`.

1. **Machine-readable fields.** List every frontmatter key any tool reads
   (`closure_status`, `compaction_status`, `conditions[].satisfied`,
   `archived_status`, `status`, `priority`). For each: which code reads it,
   what does that code do with each value, and does the prose in this file
   agree?
2. **Prose vs. its own frontmatter.** Read the document's verdict sentence
   and its frontmatter as if they were written by two different people.
3. **Source artifacts.** Every claim about another artifact is re-derived
   from that artifact, not from a summary of it.
4. **Producer/consumer naming.** Every file the narrative promises to exist
   must exist *at the exact path the consumer globs for*. Verify the glob, not
   the intent (`docs/closure/{shipment_id}-*-post-merge-closure.md`).
5. **Temporal ordering.** Every "before/after" claim is checked against real
   commit SHAs and timestamps. Every disposition postdates its finding.
6. **Cross-references.** Every referenced ID/path exists **on the remote
   branch**. Local untracked files do not count.
7. **Current HEAD.** The readiness block's SHA equals `git rev-parse HEAD` at
   push time.
8. **Operator dispositions.** Every disposition is quoted or cited with a
   date, and the entity it dispositions reflects it **in committed data**.
9. **Propagation sweep.** `git grep` each corrected identifier; reconcile
   every hit.
10. **Withdrawn claims.** Anything retracted in an earlier round is grepped
    for and removed everywhere, including downstream summaries.

## Generalizable pattern vs. one-off correction

Promote to a compound learning **only** when at least one holds:

* **Recurrence** — the same root-cause class appears ≥2 times in one PR, or
  ≥2 times across PRs. (PR #436: RC-9 ×8, RC-11 ×8, RC-10 ×7.)
* **Cross-contract invariant** — the finding reveals a rule spanning two
  surfaces that neither surface states (e.g. "a docs field consumed by a gate
  is a gate change").
* **Escape** — the finding escaped local review *and* CI and was caught only
  by hosted review.
* **High severity** — P0/P1, or it touches a fail-closed safety gate.
* **Reviewer-declared recurrence** — the reviewer itself says "this is the
  same issue as X" (PR #436, F18).

Treat as a **one-off correction, no compound entry**, when: it is a typo,
a single wrong number with no class behind it, a formatting nit, or a fix
whose reasoning does not generalise past this file. One-offs are recorded in
the PR's Review History and nowhere else.

## How to update the library without generating noise

**Never write one compound file per comment.** The bounded rule:

1. **Search first.** `grep` `docs/compound/` for the `root_cause` /
   `problem_type` / `category` of the finding. This entry consolidated five
   prior learnings rather than adding a sixth sibling.
2. **If the root-cause class already exists → append, don't create.** Add a
   dated example row/section to the existing file and bump its `tags`. A new
   file is justified only by a *new class*, never by a new instance.
3. **One entry per PR at most, written once at closure** — not per round.
   Batch the whole PR's findings into a single taxonomy pass.
4. **Split content when it gets unwieldy**: reusable taxonomy → `docs/compound/`;
   per-finding evidence trail → `docs/reviews/`; link them bidirectionally in
   frontmatter (`inventory:` ↔ `compound_learning:`).
5. **Consolidation over accretion.** If two learnings share a `root_cause`,
   merge them and leave the superseded file a stub pointer.

## Feedback-loop metrics (workflow evidence, not a telemetry engine)

All five are derivable from artifacts the workflow already produces — the
finding inventory, the PR's Review History, and `git log`. No runtime
instrumentation is required or implied.

| Metric | Definition | Source | Target direction |
|---|---|---|---|
| **Recurrence rate** | manifestations ÷ distinct findings, per PR | inventory table | ↓ (PR #436: 56/24 = **2.33**) |
| **First-detected phase** | for each finding: `plan` / `local-review` / `ci` / `hosted-review` / `post-merge` | inventory "Source" column | shift left (PR #436: **100% hosted-review**) |
| **Escaped-to-hosted-review count** | findings first detected by hosted review that a listed proactive check would have caught | inventory + checklist mapping | ↓ |
| **Time-to-disposition** | capture timestamp → operator/Stage disposition timestamp, per P-021 deferred entry | stash `created_at` + disposition record | ↓, and **must be ≥ 0** (RC-12 guard) |
| **Class coverage** | fraction of the 12 classes with an active proactive check wired into a skill | this file's checklist table | → 100% |

Record them **once per PR at closure**, in the closure record's review
section. That is the whole feedback loop: measure at closure, promote at
closure, retrieve at the next pre-PR gate.

## Round 15 addendum — convergence lesson: fixing a finding can itself create a new one

**Data update (round 15, this session):** round 14 fixed 3 of round 13's 4
unfixed findings in one bounded commit (`fdcf91e2`) — but its own fix
introduced a *new* defect (a new RC-1 manifestation: citing an unrelated,
already-archived stash entry, `27F9EC8A`, as the tracker for a distinct
publication gap), and it left 2 more findings untouched simply because it
never edited the files they lived in. Round 15's fresh hosted review then
surfaced **5 more findings** (3 threaded + 2 suppressed, `F25`-`F29`) at the
same HEAD `fdcf91e2`. Updated totals: **62 raw utterances, 29 distinct
findings, still 12 root-cause classes** (no new class was needed — F26 is a
new *manifestation* of RC-1, not a new class).

**The central lesson, stated generally:** *after any authoritative state
change (a stash entry moves active→archived, a `closure_status` flips, a
disposition is recorded), enumerate every producer and consumer of that fact
— frontmatter, narrative prose, compacted memory, reports, the PR body, and
gate outputs — and update all of them in the same pass.* Fixing the flagged
location and stopping there is exactly how round 14 both resolved F18/F21/F23
*and* created F26: it updated the two files it was editing anyway, but chose
a convenient existing ID (`27F9EC8A`) rather than verifying that ID's own
semantics matched the new fact being recorded. A propagation sweep (RC-10's
proactive check) validates *agreement*, not *truth* — sweeping a wrong fact
consistently everywhere does not make it right, and can look more convincing
than an isolated error.

**Suppressed findings are first-class, not a lesser tier.** Two of round 15's
five findings (`F28`, `F29`) had no review thread at all — they lived only in
the Copilot review body's free-text section. Both were exactly as severe
(P1/P1) as the threaded findings, and one (`F29`, compacted memory asserting
unconditional `READY`) is arguably the more durable risk, since compacted
memory is what a *future* session retrieves, long after this PR's threads are
resolved and forgotten. **Convergence requires reading the whole review body
every round, not just `reviewThreads` — this is the third time this exact
lesson has been re-confirmed on this same PR** (see the headline "64% of
utterances were suppressed" statistic above, and `docs/compound/114-S-109-F-copilot-review-fix-patterns.md`).

**Convergence requires a semantic-delta check against the entire evidence
graph, not a thread-by-thread patch loop.** The round-13→14→15 sequence is a
worked example of *why* a bounded, single-thread-at-a-time cycle does not
converge on a multi-artifact evidence set: each cycle's fix is locally
correct and globally incomplete, so the *set* of true statements about the
shipment never stabilizes across all its producers/consumers in fewer
iterations than there are producers/consumers. The fix that finally converged
(round 15) did three things differently from rounds 1-14: (a) it inventoried
*all* findings — threaded and suppressed — before editing anything; (b) it
searched all touched files for every stale identifier/date/claim rather than
fixing only the specific flagged lines; and (c) it commissioned an
*independent* adversarial re-review of its own diff before committing, rather
than trusting the fixer's own read of "done." **(c) is the mechanizable part
of this lesson: a self-check by the same agent that made the edits cannot
reliably catch a round-14-style self-inflicted regression, because the same
blind spot that produced the error is present at self-review time too.**

### New proactive check (RC-1, refined)

| Class | Proactive check | Mechanisable? |
|---|---|---|
| RC-1 (refined) | Before citing *any* existing ID (stash entry, task, shipment) as the tracker/evidence for a fact, read that ID's own record and confirm its subject matches the fact being cited — never reuse an ID for convenience because it happens to be `active` or nearby | Partly — the read is mechanical; the subject-match judgment is not |
| Convergence-loop (new) | Before starting any review-fix cycle on a multi-artifact evidence set, inventory the *entire* current review body (threaded + suppressed) and cross-reference against the full producer/consumer set for every fact being corrected, not just the flagged lines. Run an independent (not self-authored) adversarial pass on the resulting diff before commit | Partly — inventory step is mechanical; independence is a process requirement |

## The loop this closes

**Before PR:** retrieve this taxonomy → run the 10-point checklist →
fix what it finds locally.
**After hosted review:** classify every finding (threaded *and* suppressed)
into a class → count recurrences → apply the promotion rule → append here or
record as one-off.
**At closure:** emit the five metrics.

Each pass should shrink the next PR's hosted-review round count. That is the
compounding mechanism, and it is measurable with the metrics above.
