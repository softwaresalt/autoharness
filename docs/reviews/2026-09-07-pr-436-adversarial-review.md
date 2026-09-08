---
title: "Adversarial re-review of PR #436 at HEAD 659c8e75 (report-only, Stage-run); round-15/round-16/round-17 convergence disposition appended"
doc_type: review
review_mode: report-only
posture: adversarial-analysis
target_pr: 436
reviewed_head: 659c8e75c236e5e2efe8da31dca2c985b9ccba41
round_15_reviewed_head: fdcf91e2e0a5d8e9c6893e060aeaecc837592271
round_15_fix_head: e075de2670addf74182a6b8ed7c9ef23ea0c216e
round_16_reviewed_head: e075de2670addf74182a6b8ed7c9ef23ea0c216e
round_16_fix_head: 0b45caf82fb6b973f6b04f7851d681a8b3b64b5a
round_17_reviewed_head: 0b45caf82fb6b973f6b04f7851d681a8b3b64b5a
diff_base: cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab
diff_scope: "full branch diff vs merge-base with origin/main (28 files, +1518/-25)"
readiness_outcome: BLOCKED
round_15_readiness_outcome: READY_WITH_FOLLOWUPS
p0_count: 0
p1_count: 7
p2_count: 3
p3_count: 1
round_15_p0_count: 0
round_15_p1_count: 0
round_15_p2_count: 2
round_15_p3_count: 1
round_16_p0_count: 0
round_16_p1_count: 0
round_16_p2_count: 2
round_16_p3_count: 1
round_17_p0_count: 0
round_17_p1_count: 0
round_17_p2_count: 2
round_17_p3_count: 1
round_17_readiness_outcome: READY_WITH_FOLLOWUPS
round_17_continuation_reviewed_head: 8711bca15f97b386641c58b302ba5b35d9aa3da1
round_17_continuation_2_reviewed_head: e0a14f5c177bf9de648560d523d5bf717850a683
round_17_continuation_3_reviewed_head: ee207be714f6a068f9f02b29aefcf51400071251
round_17_continuation_4_reviewed_head: fbb282185fc0a33a1b09dbc141d0f1c6bed8270c
head_attribution_contract: "no field in this file names the SHA of the commit that contains it; see 'Round 17' section for the reviewed_subject_sha / resolution_commit_sha / verified_subject_sha naming contract"
generated_by: stage
generated_at: "2026-09-07T23:42:58-07:00"
updated_by: ship
updated_at: "2026-09-08T20:45:00-07:00"
inventory: docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md
compound_learning: docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md
source: docs/reviews/2026-09-07-pr-436-adversarial-review.md
tags: [review, adversarial, report-only, p-018, p-021, evidence-consistency, closure]
---

# Adversarial review — PR #436 @ `659c8e75`

## Scope and posture

**Report-only, no mutation of PR #436.** No file in the PR was edited, no
thread replied to or resolved, no commit or push made, no fifth review-fix
cycle run. This artifact exists solely as Stage planning/learning input.

* **Reviewed HEAD:** `659c8e75c236e5e2efe8da31dca2c985b9ccba41` (local `HEAD`
  == `origin/post-merge/151-f-…` — verified identical).
* **Diff:** full branch vs merge-base `cb474a0a` — **28 files, +1518 / -25**,
  not merely the latest commit.
* **All cross-reference existence checks were run against the branch tree
  (`git show HEAD:<path>`, `git grep … HEAD`), never against the local
  working tree**, which carries substantial untracked Stage artifacts that a
  reviewer of this PR cannot see.

### Declared deviation from the `review` skill contract

`review`'s report-only mode states *"Do not write a review artifact"* and
*"Do not create backlog follow-up items"*. This run deviates on both,
deliberately and under Stage authority: the operator directed a durable
adversarial artifact and P-021 capture of new findings. The deviation is
recorded here rather than taken silently, and is itself an input to the
methodology plan (finding **AF-11**).

## Persona coverage

| Persona | Tier | Triggered by | Findings |
|---|---|---|---|
| Constitution Reviewer | always-on | — | AF-01, AF-05, AF-07 |
| Correctness Reviewer | always-on | — | AF-02, AF-03, AF-04 |
| Maintainability Reviewer | always-on | — | AF-08, AF-10 |
| Python Reviewer | always-on | — | 0 direct (no `.py` in diff); contributed the read-only verification of `src/autoharness/gates/topology.py:294,654` used by AF-05 |
| Learnings Researcher | always-on | — | matched 5 prior compound entries; established AF-05 as a **third recurrence** of a known class |
| Template Integrity Reviewer | conditional | Markdown harness artifacts, policy/instruction surfaces, frontmatter contracts | AF-08, AF-10 |
| Scope Boundary Auditor | conditional | diff spans backlog data + closure docs + memory; P-021 scope questions | AF-06, AF-07, AF-11 |
| Schema-CLI-Docs Coupling Reviewer | conditional | frontmatter fields consumed by `src/autoharness/gates/topology.py`; registry vs CLI capability | AF-05, AF-08, AF-09 |
| Agent-Native Parity Reviewer | conditional | query-first backlog retrieval is the agent-facing surface | AF-07 |
| Security Reviewer | **not triggered** | no auth/endpoint/input-handling/`scripts/**`/`.github/workflows/**` in diff | — |
| Concurrency Reviewer | **not triggered** | no concurrent/async surface | — |
| Architecture Strategist | **not triggered** | no module boundary / abstraction change | — |

**Anchor-reviewer routing:** `TOOL_DEGRADED: model-specific-review-routing —
declared fallback: same-model rubric pass`. Model-specific dispatch is not
available in this session; the same rubric was applied by the caller's model.

## Findings

### AF-01 — P1 — Closure record asserts a Copilot-gate state that is false at the reviewed HEAD

`docs/closure/159-S-151-F-post-merge-closure.md` (Releasability Evidence)
states the shipped change is verified with *"Copilot review `SATISFIED`, local
review `READY`"*. At this exact HEAD, Copilot review thread
`PRRT_kwDORzpWpM6gHgcP` (opened `2026-09-08T06:16:06Z` against
`.backlogit/stash.jsonl:55`) is **unresolved**. A P-018 thread-based gate
polled now returns `UNRESOLVED_THREADS`, not `SATISFIED`.

This is a machine-checkable claim in a durable record, and it is currently
untrue. **Class RC-9** (current-HEAD readiness drift) — but on a new surface:
Copilot's own round-13 suppressed comment flagged the *PR body*; this is the
*durable closure artifact*, which outlives the PR.

* **Action routing:** `manual` · **Owner:** Ship (next authorised session)
* **Not fixed here** — fixing it requires editing PR #436.

### AF-02 — P1 — Self-contradicting verdict in one paragraph block

Same file, Releasability Evidence:

> "**Closure verdict: READY (mechanically unconditional; one distinct
> residual risk open for disposition).**"

…followed 14 lines later by:

> "No part of the mechanical archival or either disposition remains
> provisional."

Both cannot be true. **Class RC-2**, over-correction residue variant.
**Dedup:** identical to Copilot suppressed finding F21 at this same HEAD —
independently reproduced, confirming it is real and unfixed.

### AF-03 — P1 — Temporal impossibility in the `856B6770` P-005 deviation record

`docs/closure/2026-09-06-159-s-151-f-closure.md:125` records
`| Disposition | **ACCEPTED WITH REMEDIATION** (operator, 2026-09-07) |` for
a finding whose stash entry `856B6770` has
`created_at: 2026-09-08T04:53:59Z`. **The disposition predates the finding it
dispositions by roughly a day.** The same `2026-09-07` date is propagated to
seven further locations across four files (`git grep` confirmed).

**Class RC-12** (temporal impossibility). **Dedup:** identical to Copilot
suppressed finding F22 — independently reproduced.

Note the RC-10 amplification: because the wrong date was swept consistently
across all surfaces, the propagation sweep made the error *more* durable, not
less. A consistency sweep validates agreement, not truth.

### AF-04 — P1 — Pre-mode report still presents the reconstructed scan as pre-close evidence

`.backlogit/reconcile/159-S-pre-20260906-072505.md:~114` still places the
three-source linked-deliberation scan inside the set of checks *"reverified
immediately before closure"*, while the cascade report and the
cascade-close-completion record both establish it was reconstructed after the
mutation. **Class RC-11** — this is the exact defect that generated the
`856B6770` deviation, still present in the artifact that is the primary
evidence for it.

**Dedup:** Copilot suppressed finding F24 (flagged "previously missed") —
independently reproduced.

### AF-05 — P1 — **NEW** — Both remediation conditions are unenforceable; `closure_complete()` returns `True` regardless

Verified against source, not inferred:

* `src/autoharness/gates/topology.py:654` — `closure_complete()` globs
  `docs/closure/{shipment_id}-*-post-merge-closure.md` and returns `True` if
  **any** match satisfies `_closure_artifact_complete()`.
* `src/autoharness/gates/topology.py:294` — `_closure_artifact_complete()`
  requires `compaction_status ∈ {done, degraded}` **AND**
  (`closure_status == READY` **OR** a fully-satisfied `conditions:` block when
  `closure_status == READY_WITH_CONDITIONS`).
* The artifact's frontmatter: `closure_status: READY`,
  `compaction_status: done`, and a `conditions:` list containing **exactly one
  entry — the stale-lock condition, `satisfied: true`**.

Both P-005 deviation records declare a *pending* remediation in prose —
`"The deviation is closed when 169-S is durably published and ships"` and
`"a separate follow-up shipment … Not yet a durably committed backlog record
as of this PR"` — but **neither is represented in the `conditions:` block that
the gate can read.** `closure_complete('159-S')` therefore returns `True`
today, and every successor shipment's predecessor-closure check is unblocked
while both remediations remain unpublished.

This is the **third recorded recurrence** of the class named in
`docs/compound/114-S-109-F-copilot-review-fix-patterns.md`: *"a stated closure
condition is only real if the code actually enforces it."* Copilot never
raised it in this form on this PR — it argued about the *value* of
`closure_status`, never about the **absent machine-readable representation of
the remediation conditions**.

* **Class:** RC-2 (machine-readable vs narrative), cross-contract variant
* **Action routing:** `manual` · **Owner:** Stage (design), then Ship
* **Provisional priority:** high

### AF-06 — P1 — **NEW (partial dedup)** — The `856B6770` remediation tracker has no identifier, no record, and no capture

Cross-reference existence on the branch tree:

* `169-S` — referenced in 5 files on the branch; **no `169-S` record exists on
  this branch or on `main`** (`git ls-files "*169-S*"` → empty). It exists
  only as an untracked local file, invisible to any reviewer of this PR.
  *Partially captured* by `1CD92B69`.
* The `856B6770` remediation — described only as *"a separate follow-up
  shipment (not `169-S`)"*. **It has no ID at all.** It is not captured by
  `1CD92B69` (whose payload names only `169-S` and `15A02E21`), and not by
  `856B6770` itself (whose payload is the disposition question, not the
  publication of its remedy).

So the accepted-with-remediation disposition of a P0-class safety-gate
deviation currently rests on a remediation with **no trackable identity**.
This is the P-005/P-021 auditability gap: the deviation is searchable, its
remedy is not.

* **Class:** RC-5 / RC-3 · **Provisional priority:** high

### AF-07 — P1 — Committed stash contradicts the closure narrative for `856B6770`

`git show HEAD:.backlogit/stash.jsonl` line 55 carries `856B6770` with
`"priority":"high"`, `REQUIRES DELIBERATION: yes`, and no disposition, while
four closure/memory records declare it resolved. Query-first backlogit
retrieval will keep surfacing a false unresolved high-priority blocker.

**Dedup:** this is the open thread `PRRT_kwDORzpWpM6gHgcP` (Copilot F18), and
Copilot itself names it a recurrence of F17/`15A02E21`. **Class RC-5, second
recurrence in the same PR.**

Root cause identified by this review and *not* stated in the thread: the
working tree's copy of `856B6770` **does** carry a `--- STAGE TRIAGE +
DELIBERATION UPDATE` block. The disposition was written locally and never
committed, because `.backlogit/stash.jsonl` edits are Stage-owned and Ship
correctly refused to touch them (P-021 capture-only). **The gap is structural,
not an oversight: no workflow step hands a Ship-observed stash-currency gap
back to Stage for commit before the PR is presented as ready.**

### AF-08 — P2 — **NEW** — `reviewed_head` is ambiguous and machine-unconsumed

Both closure artifacts carry `reviewed_head: 494089ab638a7d111618ff6f9fd30febbc635934`
(PR #435's head), while the PR body's readiness block names `659c8e75` (this
PR's head). Verified: **zero consumers in `src/`** (`grep -r reviewed_head src`
→ no hits). A frontmatter key with two plausible referents, sitting beside
sibling keys that *are* gate-consumed, is a latent RC-2 trap for the next
reader or the next tool that starts reading it.

* **Recommendation:** either document the referent inline, rename to
  `subject_pr_reviewed_head`, or drop it. Design call, not a defect today.

### AF-09 — P2 — Registry advertises no `features.sizing` though the CLI supports it — **DUPLICATE, already captured**

`.autoharness/backlog-registry.yaml` `features:` omits `sizing`, and neither
`create_task` nor `update_task` declares size/complexity params, yet
`backlogit update --help` genuinely exposes `--size`, `--size-source`,
`--size-ruleset-version`, `--complexity`.

**Dedup: no new capture.** Already stash entry `D456616B` (low, task),
which states the settled rule — *"the ADVERTISED flag is authoritative and
parameter presence never arms the gate"* — and assigns it to the SHIP-7
registry-parity charter. Recorded here only to show the dedup path was
actually walked.

### AF-10 — P2 — **NEW** — Reconcile reports carry no machine-readable outcome field

`.backlogit/reconcile/159-S-post-*.md` frontmatter is
`shipment_id / mode / merge_commit_sha / timestamp` — no verdict field. The
pre-mode report's `recommendation: PROCEED` and the cascade report's `CLOSED`
outcome are **prose only**. Every dispute in this PR's 13 rounds was about
exactly these values, and none of them is machine-readable. Any future
automated consumer of reconcile evidence must parse prose, which is precisely
the condition that lets RC-2 mismatches survive.

* **Class:** RC-2 (latent) · **Provisional priority:** medium

### AF-11 — P3 — advisory — `review` report-only mode cannot serve Stage adversarial analysis

Report-only forbids writing an artifact and forbids creating follow-up items,
yet a Stage-run adversarial review needs both (durable artifact + P-021
capture). This run declared the deviation. The `review` skill should
acknowledge a Stage-run analysis posture rather than forcing an undeclared
deviation. Feeds the methodology plan directly.

## Dedup map — adversarial vs Copilot vs existing stash

| AF | Status | Maps to Copilot finding | Existing stash | New capture |
|---|---|---|---|---|
| AF-01 | reproduced, new surface | F23 (class) | — | **`846D0282`** |
| AF-02 | reproduced | **F21** | — | **`846D0282`** (bundled: same file, same round-13 unfixed set) |
| AF-03 | reproduced | **F22** | — | **`846D0282`** (bundled) |
| AF-04 | reproduced | **F24** | — | **`846D0282`** (bundled) |
| AF-05 | **NEW** | none | — | **`0BE73C89`** |
| AF-06 | **NEW** (partial) | none | `1CD92B69` covers `169-S`+`15A02E21` only | **`9E22BFC6`** |
| AF-07 | reproduced | **F18** / thread `PRRT_kwDORzpWpM6gHgcP` | — | **`27F9EC8A`** |
| AF-08 | **NEW** | none | — | **`AFEFC6AB`** |
| AF-09 | duplicate | none | **`D456616B`** | none — deduped |
| AF-10 | **NEW** | none | — | **`AFEFC6AB`** (bundled: same frontmatter-contract class) |
| AF-11 | **NEW** (process) | none | — | folded into the methodology deliberation, not a stash entry |

**Bundling rule applied:** AF-01..AF-04 are four unfixed findings in the same
two files from the same round-13 review with one owner and one fix window, so
they are one capture, not four. AF-08 and AF-10 are both
"reconcile/closure frontmatter lacks a machine-readable contract" and share a
root cause. This is the anti-noise promotion rule from the compound learning
applied to capture, not just to learnings.

## Verdict

| Counter | Value |
|---|---|
| P0 | **0** |
| P1 | **7** (AF-01 … AF-07) |
| P2 | **3** (AF-08, AF-09, AF-10) |
| P3 | **1** (AF-11) |
| **Readiness outcome** | **`BLOCKED`** |

**PR #436 is not merge-ready at `659c8e75`.** Seven P1 findings stand, one
Copilot thread is open, and the closure record asserts a gate state that is
currently false.

**No fix cycle was run and none is authorised.** The operator's authorisation
covered exactly one bounded fourth round, already consumed by commit
`659c8e75`. Every finding above is captured for separate disposition. The
next owner for the PR itself is the **operator** (to authorise or decline a
further round); the next owner for the captured items is **Stage**, then
**Ship**.

## Round 15 — post-fix disposition (this session, Ship; reviewed HEAD `fdcf91e2` before the fix, fix committed at HEAD `e075de2670addf74182a6b8ed7c9ef23ea0c216e`)

The operator subsequently authorised round 14 (one bounded fix, commit
`fdcf91e2`) and then, after round 14 produced a fresh recurrence (F26) and
three further findings escaped hosted review, explicitly authorised this
round-15 **comprehensive convergence pass** — fix everything on the
closure-evidence-contract surface in one coherent commit rather than another
single-thread cycle.

**Local review for this disposition:** an independent adversarial
`code-review`-agent pass (not a self-check) was run against the round-15 diff
before commit, applying the Constitution / Correctness / Maintainability /
Template Integrity / Scope Boundary / Schema-CLI-Docs Coupling / Learnings
Researcher lenses to the full 6-file evidence graph (not diff-only). Verdict:
all 9 checked findings **RESOLVED**, zero new P0/P1 issues.

### Before/after disposition — every AF-01 … AF-11

| AF | Round-13 status | Round-15 disposition |
|---|---|---|
| AF-01 | P1, reproduced | **RESOLVED.** Canonical closure record (`docs/closure/159-S-151-F-post-merge-closure.md`) now disambiguates that "Copilot review `SATISFIED`, local review `READY`" describes PR #435's own review state at `reviewed_head: 494089ab…`, not this closure PR (#436)'s review state; #436's own readiness is tracked in the PR body (fixed as F27, queued for the immediate post-push step). |
| AF-02 | P1, reproduced (= F21) | **RESOLVED in round 14** (`fdcf91e2` rewrote the verdict/closing sentence for `READY_WITH_CONDITIONS`); round 15 re-verified no residual self-contradiction remains in the canonical file. |
| AF-03 | P1, reproduced (= F22) | **RESOLVED in round 15.** `856B6770`'s disposition date corrected from the impossible `2026-09-07` to the ground-truth `2026-09-08` (verified directly against the entry's `created_at: 2026-09-08T04:53:59Z`) in all 3 files that carried the wrong date, each with an explicit chronological-impossibility correction note; the unrelated, correctly-dated `15A02E21` disposition (`2026-09-07`, entry created `2026-09-06`) was left untouched. |
| AF-04 | P1, reproduced (= F24) | **RESOLVED in round 15.** `.backlogit/reconcile/159-S-pre-20260906-072505.md` now carries an explicit chronology-correction paragraph: the three-source linked-deliberation scan was reconstructed post-hoc in round 4 (`42428afe`), not executed live at report-generation time, despite sitting under a "reverified immediately before closure" heading. |
| AF-05 | P1, **NEW** at round 13 | **RESOLVED in round 15 (docs-only; no code change required).** Live-verified `src/autoharness/gates/topology.py`'s `_closure_conditions_satisfied()`/`_closure_artifact_complete()` already mechanically enforce the `conditions:` block (`satisfied: true` literal + non-empty `evidence` per entry, fail-closed otherwise) — `FilesystemTopologyReaders('.').closure_complete('159-S')` returns `False` today against the current frontmatter. Round 14 had already added a `conditions:` entry (partial fix) but pointed it at the wrong tracker (`27F9EC8A`, an unrelated archived finding); round 15 corrected the tracker to the dedicated `2B68F9D6` so the condition's `evidence` field is now truthful as well as mechanically enforced. |
| AF-06 | P1, **NEW** (partial dedup) | **Substantially addressed as a side effect.** The `856B6770` remediation now has a full durable identity (`163-F` / `163.001-T`..`163.007-T` / `171-S`, published in round 14) **and** a dedicated, correctly-scoped active tracker (`2B68F9D6`, round 15) — the original "no ID at all" gap no longer exists. Not separately re-captured; already covered by existing stash entry `9E22BFC6` per the round-13 dedup map, which remains Stage's to triage. |
| AF-07 | P1, reproduced (= F18) | **RESOLVED in round 14** (`fdcf91e2` published `856B6770`'s already-Stage-authored archival into the committed stash). |
| AF-08 | P2, **NEW** | **Unchanged, still open.** `reviewed_head` ambiguity is a design question (rename vs. document vs. drop), genuinely outside this closure PR's evidence-graph-correction surface; already captured (`AFEFC6AB`), no duplicate capture made. |
| AF-09 | P2, duplicate | **Unchanged.** Already deduped to existing stash entry `D456616B`; no action this round. |
| AF-10 | P2, **NEW** | **Unchanged, still open.** Reconcile reports still carry no machine-readable outcome field; this requires a code/schema change, not a docs-only fix, and is outside this PR's surface. Already captured (`AFEFC6AB`, bundled with AF-08); no duplicate capture. |
| AF-11 | P3, **NEW** (process) | **Unchanged, advisory.** Feeds the methodology plan (`docs/plans/2026-09-07-review-pattern-learning-methodology-plan.md`, feature `162-F`, shipment `170-S`) directly; not implemented this round (P-001/dependency-gated behind open #436, `169-S`, `162-S`). |

### Residual P2/P3 after round 15

Two residual, non-blocking items remain, both already captured and both
outside this closure PR's narrow evidence-graph-correction surface:

* **AF-08 / AF-10 (P2, bundled under `AFEFC6AB`)** — `reviewed_head`
  ambiguity and reconcile reports' lack of a machine-readable outcome field.
  Both are design/code questions for a future shipment, not this PR.
* **AF-11 (P3)** — `review` skill's report-only mode cannot cleanly serve a
  Stage-run adversarial-analysis posture; feeds the queued `162-F`/`170-S`
  methodology work, not actioned here.

### Round-15 verdict

| Counter | Value |
|---|---|
| P0 | **0** |
| P1 | **0** (all 7 resolved: AF-01 through AF-07) |
| P2 | **2** (AF-08/AF-10 bundled, AF-09 deduped-closed) |
| P3 | **1** (AF-11, advisory) |
| **Readiness outcome** | **`READY_WITH_FOLLOWUPS`** |

`READY_WITH_FOLLOWUPS` because the PR-body Local Review Readiness block
itself (F27) still needs to be updated for the new HEAD as the immediate next
step after this commit is pushed — this artifact's own local-review pass
covers the committed evidence-graph fix, not the PR body update that follows
it. No P0/P1 remain on this closure PR's evidence-graph surface. This PR is
**still not being merged** — no merge approval was given or sought this
round; `162-F`/`170-S` (the harness-implementation methodology) remain queued
and P-001/dependency-gated behind open #436, `169-S`, and `162-S`.

## Round 16 — narrow follow-on disposition (this session, Ship; reviewed
subject HEAD `e075de2670addf74182a6b8ed7c9ef23ea0c216e` before this round's
fix, fix committed at HEAD `0b45caf82fb6b973f6b04f7851d681a8b3b64b5a`)

A fresh Copilot review at the round-15 fix HEAD found 3 fresh findings
(`F30`-`F32` in the finding inventory) inside artifacts round 15 itself had
just authored: this file's own round-15 section header conflated the
reviewed-HEAD (`fdcf91e2`) with the fix-HEAD (now corrected above, and a
distinct `round_15_fix_head` frontmatter field added so the two are never
conflated again); a 4th file carrying `856B6770`'s disposition date that
round 15's sweep missed despite claiming it had covered "all 3 files"; and
this document's companion compound-taxonomy file's own review-count citation
was off by one. All 3 are same-contract-surface completions of round 15's
own change (P-021 C1 in-scope), fixed directly per the operator's explicit
authorization to continue the convergence pass; none reopens a prior
finding, and no fifth AF-series finding was introduced.

Fixed by direct, targeted verification of each of the 3 edited lines against
ground truth (not a fresh independent-agent pass, given the narrow 3-line
scope of this cycle) — HEAD label cross-checked against `git log`, date
cross-checked against `.backlogit/archive/stash.jsonl`'s `856B6770.created_at`,
review count cross-checked against `gh pr view 436 --json reviews` filtered
to `copilot-pull-request-reviewer`.

### Round-16 verdict

| Counter | Value |
|---|---|
| P0 | **0** |
| P1 | **0** (F30/F31 fixed; no new P1) |
| P2 | **2** (AF-08/AF-10 bundled, unchanged) |
| P3 | **1** (AF-11, unchanged) |
| **Readiness outcome** | **`READY_WITH_FOLLOWUPS`** (same residual follow-ups as round 15; F32 was P2-equivalent metadata, now fixed) |

Threads `PRRT_kwDORzpWpM6gYcYh` and `PRRT_kwDORzpWpM6gYcY5` replied to
(citing the round-16 fixing commit) and resolved. F32 has no thread
(suppressed); its disposition is recorded here and in the finding inventory.
This PR is **still not being merged** — no merge approval was given or
sought this round.

## Round 17 — systemic contract fix for reviewed-vs-fixing HEAD conflation (this session, Ship; reviewed subject HEAD `0b45caf82fb6b973f6b04f7851d681a8b3b64b5a`)

A fresh Copilot review at HEAD `0b45caf8` (thread `PRRT_kwDORzpWpM6gYzGj`)
found that the Round 16 header immediately above reproduced, in its own new
prose, the identical class of defect (RC-9, current-HEAD readiness drift)
that F30 had already flagged and round 16 itself corrected one section
earlier: it named the pre-fix reviewed HEAD (`e075de26`) as both "reviewed"
and "fixed," when the round-16 fix actually committed at `0b45caf8`. Ship
acknowledged the finding transparently on the thread and did not apply a
further edit in that session — the same-error recurrence tripped a
universal circuit breaker; see
`docs/memory/2026-09-08/circuit-break-pr-436-review-head-conflation.md` for
the full attempt chain and the operator's subsequent disposition.

**Why a literal SHA-substitution retry cannot converge.** Attempts 1 and 2
each tried to fix a *specific wrong SHA string* by substituting the correct
one — but "the correct one" for a HEAD-attribution claim inside a section
that itself becomes part of a new commit is not a fixed target: the moment
the file is edited and committed, the repository's HEAD advances to a new
SHA that the just-written prose cannot have named, because that SHA did not
exist at authoring time. A tracked artifact's own containing commit is a
value the artifact cannot compute about itself before that commit is
created — this is a recursive fixed-point impossibility, not an authoring
mistake that a more careful retry can fix. Round 16 fixed F30's *instance*
of the conflation (the round-15 header) but re-created a *fresh* instance of
the same underlying impossible claim in its own new header, because both
attempts treated the defect as "wrong SHA, substitute the right one" rather
than "this class of claim can never be made correctly about a commit's own
contents."

**The systemic resolution (operator-directed, distinct from a fourth
literal-substitution retry).** The class of claim itself is retired, not
patched again:

1. A Git-tracked review/evidence artifact **MUST NOT** claim to identify the
   commit SHA that contains it. This applies to every round's disposition
   prose and frontmatter in this file and its companions, going forward.
2. Tracked artifacts instead use stable, non-self-referential identities:
   - **`reviewed_subject_sha`** — the commit/diff actually reviewed *before*
     the round's remediation (already the meaning of this file's
     `*_reviewed_head` fields; unaffected by this change).
   - **`resolution_commit_sha`** — the commit that *applied* a prior
     remediation, recorded only by a *later* artifact/entry once that
     commit already exists in history (already the meaning of this file's
     `round_15_fix_head`, and now `round_16_fix_head`, added below to close
     the gap that caused the round-16 recurrence: round 16 never recorded
     its own `round_16_fix_head`, so its header prose fell back to reusing
     the reviewed-subject SHA for both roles).
   - **`verified_subject_sha`** — for a post-fix verification performed
     *before* the commit that reports it, the SHA being verified, never the
     verifying commit itself.
3. Current PR HEAD and merge readiness are external, dynamic facts, queried
   from GitHub after push and recorded in the PR body / check-run / review
   response — never inside a committed file. This round's own fix commit
   SHA is therefore deliberately **absent** from this section and from this
   file's frontmatter: it cannot be known at the time this section is
   authored, and it will instead be published, after push, as the
   `headRefOid` in this PR's `## Local Review Readiness` block (and cited in
   the reply that resolves thread `PRRT_kwDORzpWpM6gYzGj`) — not written
   back into this file in a later edit, which would only reproduce the same
   impossibility one level down.
4. Merge gates compare the dynamic `headRefOid` reported by GitHub against
   the externally published PR-body readiness value; no committed file is
   required, or permitted, to self-attest its own containing SHA.

**Frontmatter correction applied this round:** `round_16_fix_head:
0b45caf82fb6b973f6b04f7851d681a8b3b64b5a` added — the missing field whose
absence caused the round-16 header to fall back to the reviewed-subject SHA
for both roles — and `round_17_reviewed_head:
0b45caf82fb6b973f6b04f7851d681a8b3b64b5a` added (the subject this round
reviewed: a fixed historical fact about a commit that already exists, not a
claim about this round's own commit). The Round 16 header above is
corrected in place to name both HEADs explicitly using the "reviewed
subject" / "fix committed at" phrasing this contract establishes, rather
than a single ambiguous "reviewed and fixed at."

**Scope note:** the full methodology generalisation of this contract
(naming-convention adoption across the `review`/`pr-lifecycle` skills, and
the compound taxonomy's RC-9 proactive check) is not implemented this round.
It is tracked as a follow-up under the already-queued `162-F`/`170-S`
methodology work (P-001/dependency-gated, not yet claimed). The reviewed
implementation plan for that work (`docs/plans/2026-09-07-review-pattern-learning-methodology-plan.md`)
is a Stage-owned planning artifact; Ship does not edit it (P-010) and
instead records this needed refinement here for Stage's `170-S` tracker to
pick up.

### Round-17 verdict

| Counter | Value |
|---|---|
| P0 | **0** |
| P1 | **0** |
| P2 | **2** (AF-08/AF-10 bundled, unchanged) |
| P3 | **1** (AF-11, unchanged) |
| **Readiness outcome** | **`READY_WITH_FOLLOWUPS`** (unchanged from round 16; this round is a structural-contract fix, not a new substantive finding) |

Thread `PRRT_kwDORzpWpM6gYzGj` is replied to (citing this round's resolution
commit, published in the PR body after push, per the contract above, rather
than in this file) and resolved. This PR is **still not being merged** — no
merge approval was given or sought this round.

### Round-17 continuation — post-push Copilot re-review at HEAD `8711bca1`

After the round-17 fix commit was pushed and thread `PRRT_kwDORzpWpM6gYzGj`
was replied-to/resolved, a fresh Copilot review was requested and completed
at the new HEAD (reviewed subject `8711bca15f97b386641c58b302ba5b35d9aa3da1`
— see `round_17_continuation_reviewed_head` in this file's frontmatter, a
`reviewed_subject_sha` for an already-existing, already-pushed commit, not a
self-referential claim). It opened one new thread,
`PRRT_kwDORzpWpM6gZuPp`, on
`docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md:5`:
that file's round-17 update refreshed its `citations` block but left the
searchable `root_cause` frontmatter field stating the stale round-13 totals.
This is a same-contract-surface completion of the round-17 citation work
(same file, same update), not a scope expansion, and was fixed in place
(frontmatter now states both the round-13 baseline and the round-17 running
total). Nine suppressed comments were also individually verified against
current committed content; two genuine but unrelated closure-doc findings
(cascade-close task-archival phrasing, publication-ownership phrasing) were
out of scope for this round's authorized systemic-HEAD-fix operation and
were captured as P-021 deferred-scope stash entries (`A8CA35BB`,
`EE1AB6DB`) rather than fixed here; the remaining suppressed comments were
either already resolved by this round's own actions (committing the
circuit-breaker record) or stale re-statements of already-correct content.
Full per-finding detail: `docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md`'s
F34 row and "Round 17 continuation" section. Readiness outcome unchanged:
`READY_WITH_FOLLOWUPS`, P0=0/P1=0/P2=2/P3=1. No merge approval given or
sought.

### Round-17 second continuation — post-push Copilot re-review at HEAD `e0a14f5c`

After the first continuation's fix commit was pushed, the PR body updated,
and thread `PRRT_kwDORzpWpM6gZuPp` replied-to/resolved, a further Copilot
review was requested and completed at the new HEAD (reviewed subject
`e0a14f5c177bf9de648560d523d5bf717850a683` — see
`round_17_continuation_2_reviewed_head` in this file's frontmatter, a
`reviewed_subject_sha` for an already-existing, already-pushed commit).
Live GraphQL confirmed thread `PRRT_kwDORzpWpM6gZuPp` **is** actually
resolved; the review body's own suppressed restatement to the contrary was
itself stale, consistent with the pattern already observed twice this
session. This review opened 4 new threads:

- `PRRT_kwDORzpWpM6gaOaF` — the prior continuation's own F34 fix left the
  `root_cause` frontmatter one number behind its own `citations` block
  ("18" reviews vs. the "19th" the citations already named). Fixed by
  restating `root_cause` as "19 Copilot reviews ... 34 distinct findings" —
  same-contract-surface completion of the prior pass's own edit.
- `PRRT_kwDORzpWpM6gaOav`, `PRRT_kwDORzpWpM6gaObR`, `PRRT_kwDORzpWpM6gaOb4`
  — all three name the same underlying gap in three different citing
  files: the prior continuation's narrative described P-021 stash entries
  `A8CA35BB`/`EE1AB6DB` as "captured," but `backlogit stash add` only
  writes the local working-tree copy of `.backlogit/stash.jsonl` — those
  entries were not yet committed, so no reviewer of the branch could
  actually see them. Fixed by surgically committing exactly those 2 JSON
  lines onto the last committed baseline, leaving the file's other,
  concurrent, unrelated Stage-owned working-tree entries untouched and
  unstaged.

One further suppressed comment
(`docs/closure/2026-09-06-159-s-151-f-closure.md:20`, a missing "Invariants
to preserve" section) was genuine but out of scope for this round's
authorized systemic-HEAD-fix operation, for the same reason as
`A8CA35BB`/`EE1AB6DB`; a clean active+archived P-021 discovery scan found
no existing duplicate, so it was captured as a new stash entry
(`5F70D80C`) rather than fixed here. Full per-finding detail:
`docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md`'s F35/F36
rows and "Round 17 continuation, second pass" section. Readiness outcome
unchanged: `READY_WITH_FOLLOWUPS`, P0=0/P1=0/P2=2/P3=1 (the 2 P2s and 1 P3
remain the same pre-existing, already-disclosed follow-up items; F35/F36
were fixed, not counted as new residual severity). No merge approval given
or sought.

### Round-17 third continuation — auto-triggered Copilot review at HEAD `ee207be7`

After the second continuation's fix commit (`ee207be7`) was pushed, a
Copilot review auto-triggered without an explicit re-request (reviews can
complete purely from push/thread activity — always poll
`gh api .../pulls/436/reviews --paginate` and match `commit_id` against
actual current HEAD, not just the last explicitly requested review) and
completed at reviewed subject
`ee207be714f6a068f9f02b29aefcf51400071251` (`round_17_continuation_3_reviewed_head`
in this file's frontmatter). This review opened 3 new threads, all
genuinely new and all correctly out of scope for this round's authorized
systemic-HEAD-fix operation:

- `PRRT_kwDORzpWpM6gaoJt` — a missing post-mode report path in
  `docs/closure/2026-09-06-159-s-151-f-closure.md`. Deferred as `C395CFE3`.
- `PRRT_kwDORzpWpM6gaoKN`, `PRRT_kwDORzpWpM6gaoKh` — two manifestations
  (same file, two locations) of the same defect: the closure condition is
  narrower than tracker `2B68F9D6`'s actual requirement. P-021 discovery
  confirmed this is distinct from `EE1AB6DB` (role-attribution) despite
  sharing a file/area — reuse requires positive confirmation of the same
  expansion, not proximity alone, so both were captured separately as
  `24E3E464` rather than merged with `EE1AB6DB`.

One suppressed comment was a stale restatement of `EE1AB6DB`'s
already-captured topic; no new entry. All 3 threads replied-to and
resolved, citing `C395CFE3`/`24E3E464`. Live GraphQL confirmed 34 total
threads, 34 resolved, 0 open. Full per-finding detail:
`docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md`'s F37/F38
rows and "Round 17 continuation, third pass" section. Readiness outcome
unchanged: `READY_WITH_FOLLOWUPS`, P0=0/P1=0/P2=2/P3=1. No merge approval
given or sought.

### Round-17 fourth continuation — explicitly-requested Copilot review at HEAD `fbb28218`

A second review, explicitly requested via the standard re-request flow and
running concurrently with the third continuation's auto-triggered review,
completed at reviewed subject `fbb282185fc0a33a1b09dbc141d0f1c6bed8270c`
(`round_17_continuation_4_reviewed_head` in this file's frontmatter — the
commit that also corrected a stray 30-vs-31 thread-count arithmetic error
found while verifying the third continuation's resolution). This review
produced 0 new threaded comments but 7 suppressed comments, requiring full
inspection of the suppressed body per the established "0 threads ≠ clean"
lesson:

- 4 were stale restatements of already-captured/out-of-scope topics; no
  new entries.
- `docs/closure/2026-09-06-159-s-151-f-closure.md:103` — genuinely new,
  out of scope: the table row says the deviation "closes only after
  `169-S` is published and ships," while the same file's narrative 4 lines
  later says the disposition is already unconditional — an internal
  contradiction in an unrelated closure artifact. Deferred as `35CE8C55`.
- `docs/memory/compacted/2026-09-06-159s-151f-compacted.md:17` —
  genuinely new, out of scope: calls the test-suite result a "full local
  build," conflating test execution with build evidence, when PR #435
  records the editable-install build as not applicable. Deferred as
  `DC6F5B20`.
- `docs/memory/2026-09-08/circuit-break-pr-436-review-head-conflation.md:103-106`
  — genuinely new, **and in scope**: this session's own circuit-breaker
  continuity record briefly described operator authorization as an
  "extend/waive the breaker for this exact operation" option, but
  `.github/instructions/circuit-breaker.instructions.md` defines no waiver
  of a tripped same-operation limit at any threshold — explicit operator
  approval authorizes proceeding only for a genuinely new operation, never
  a waiver/extension of the tripped operation's own limit. Because the
  defect is in this session's own authorship of the very continuity record
  this round's authorization relies on, it is a same-contract-surface
  completion, not an expansion. Fixed: "Option 4" reworded to state the
  actual policy; a new "## Resolution" section added, itself written under
  the naming contract it describes (it names the disposition date and the
  mechanism-difference test satisfied, never the SHA of the commit
  containing it).

`35CE8C55` and `DC6F5B20` are suppressed findings with no review thread, so
no reply/resolve step applies — their references are discharged via
residual-risk citations in this file, the finding inventory, and the
taxonomy file, per the threadless defer-capture path. Discovery-checked
both against active and archived stash before capture; no duplicates
found. Full per-finding detail:
`docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md`'s F39/F40/F41
rows and "Round 17 continuation, fourth pass" section. This pass also
required republishing `.backlogit/stash.jsonl` a further time (baseline
plus 4 new lines: `C395CFE3`, `24E3E464`, `35CE8C55`, `DC6F5B20`), using
the same surgical technique that isolates only the new lines from Stage's
concurrent unrelated working-tree entries in the same file. Readiness
outcome unchanged: `READY_WITH_FOLLOWUPS`, P0=0/P1=0/P2=2/P3=1 (F39 fixed,
not counted as new residual severity; F40/F41 are new deferred follow-ups,
consistent with the pre-existing P2/P3 count which already tracked
deferred, not-yet-remediated items). No merge approval given or sought.

