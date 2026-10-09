---
title: "Copilot review-body findings without threads: make the P-018 gate and the shadow-review loop see them"
description: "Deliberation for stash 38D29192. Copilot can report a valid finding only in its review body (a 'Previously missed' or 'Suppressed comments' section) with no review thread. The thread-based shadow-review loop and the P-018 copilot-review gate both miss it. Decision: add a deterministic, fail-closed BLOCK verdict that clears only when each Copilot review carrying threadless body findings has an agent-postable disposition comment, and teach the PR-automation loop to read, handle, and disposition review-body findings."
topic: "P-018 copilot-review gate and shadow-review loop blind to threadless review-body findings"
depth: "standard"
decision_status: "decided"
promoted_to: "plan"
source_stash: 38D29192
linked_artifacts:
  - "docs/plans/2026-10-08-copilot-review-body-findings-gate-plan.md"
  - "docs/compound/2026-10-08-copilot-review-body-findings-without-threads.md"
tags:
  - "p-018"
  - "copilot-review"
  - "shadow-review"
  - "review-body-findings"
---

# Copilot review-body findings without threads

## Problem Frame

**Source:** stash `38D29192` (bug, provisional medium). It is a 169-S post-merge
closure follow-up from Ship Step 5. It carries no `DEFERRED SCOPE EXPANSION`
marker, so the P-021 C6 precedence route does not apply. The entry itself declares
`requires deliberation: yes`.

On PR #506, Copilot review rounds 2 to 5 ran at HEADs `fb68e399`, `b879a045`,
`24d5fc13`, and `a5e571a5`. Each round reported one valid, in-scope finding only
in a collapsed `Previously missed (1)` section of the `ccr-overview-v2` review
body. The headline read `0 open findings`, and the round had no inline comment
and no review thread. `autoharness gate copilot-review` returned `SATISFIED` for
each HEAD. The gate checks only two things: a completed Copilot review for the
current HEAD, and unresolved Copilot-authored threads. Ship caught the four
findings only by reading the bodies by hand.

There are two blind spots:

1. **The shadow-review loop.** In `github-pr-automation.instructions.md`, §1.2
   polls, §1.3 categorizes, §1.5 replies, §1.6 resolves, and §1.8 counts cycles.
   All of these steps walk comments and threads, so a body-only finding has
   nothing to categorize, reply to, or resolve.
2. **The P-018 gate.** In `src/autoharness/gates/copilot_review.py`, the
   GraphQL query does not fetch the review `body`, and `classify()` has no
   verdict for a body finding. The Local Review Readiness record (§1.9.2) has no
   field for body findings either, so the gate can report a body-only finding
   as "0 comments".

**Success criteria.**

* A Copilot review whose body carries a threadless finding can no longer
  produce a PASS verdict until that finding is visibly dispositioned.
* The agent loop reads, categorizes, fixes or defers, and records body findings
  with an audit trail equivalent to a thread reply.
* A finding that is deferred or declined does not wedge the gate or require an
  operator `--force`.

**Scope boundaries (P-021 C1).**

* In scope:
  * the copilot-review gate module and its CLI rendering;
  * the gate reference doc;
  * the PR-automation instruction, the P-018 policy text, and the Ship 7c gate
    step (template plus installed mirror);
  * a cross-surface contract pin.
* Out of scope:
  * acting on the content of any historical body finding (for example
    58A85283's file-lock test-coverage requests);
  * reconciling the pre-existing template/mirror drift in
    `github-pr-automation`;
  * human-reviewer body findings;
  * any change to enforcement modes, `--max-wait`, `--force` auditing, or exit
    codes.

## Research Findings

### Prior learnings (Step 1.8; confidence high)

* `docs/compound/2026-10-08-copilot-review-body-findings-without-threads.md`
  (the source learning for this entry):
  * read every review body;
  * handle threadless findings through a PR comment that quotes the finding
    and cites the fixing SHA or deferral stash ID;
  * count a body finding as a review-fix cycle;
  * a round is clean only when it has no open threads and no body finding;
  * list body findings in the Local Review Readiness block.
* `docs/compound/114-S-109-F-copilot-review-fix-patterns.md`, PR #297
  round 12: the thread-based gate returned `SATISFIED` while the body carried
  two suppressed comments. Its lesson was "always read the full review body".
* `docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md`, PR #436:
  64 % of utterances (36 of 56) were suppressed, non-threaded findings that were
  visible only in the review body. The note tags this class as
  `suppressed-findings-first-class`.
* Stash `58A85283` (PR #444 round 2) records two findings embedded as
  "suppressed comments" in the review body.

**Conclusion from the learnings.** This is at least the **fourth recorded
recurrence** (114-S / PR #297, PR #436, PR #444, PR #506). Three prose-only
"read the body" lessons did not prevent it. P-018 exists to replace prose with
deterministic enforcement ("enforced deterministically ... not by prose alone").
A prose-only fix would repeat the failure mode that the lessons document.

### Observed body formats (read-only `gh api graphql`, 2026-10-08)

**Format 1: `ccr-overview-v2` (PR #506).**

* The body starts with `<!-- ccr-overview-v2 -->` and a risk line
  (`### 🔵 Needs a closer look`).
* Open findings appear in one of two forms:
  * a bold headline, `**0 open findings**`;
  * a `<details open><summary><strong>1 open finding</strong></summary>` list.
    In the observed list, each item links a `(#discussion_r<id>)` anchor, so the
    item is threaded.
* Other sections:
  * `<summary><strong>1 resolved since last review</strong></summary>` lists
    findings that are already resolved, so it holds no findings to handle;
  * `<summary><strong>Previously missed (1)</strong></summary>` with the text
    "In code that hasn't changed since last review" holds the threadless
    finding;
  * `What changed in this PR` is a summary, not a finding.
* The round-6 clean body (`c2e6b48e`) has only the headline and the risk line.
* The review node's inline-comment count was 1 for round 1 and 0 for rounds 2
  to 6.

**Format 2: legacy "Review details" (PR #444).**

* The body has a `<details><summary>Review details</summary>` block.
* The block contains `### Suppressed comments (5)` and a nested
  `**Previously missed (2)** — in code that hasn't changed since the last review.`
  heading.
* Each finding is listed as `**path:line**` followed by a bullet.

**What both formats share.** Both have a `Previously missed (N)` marker, and the
legacy format adds `Suppressed comments (N)`. Neither format is versioned or
documented by GitHub as a contract, so format drift is a real risk.

### Code surface (`src/autoharness/gates/copilot_review.py`, 654 lines)

* `_GRAPHQL_QUERY` fetches the following and nothing else:
  * `headRefOid`;
  * `reviewRequests(first:100)`;
  * `reviews(last:100){ author state commit{oid} }`;
  * `reviewThreads(first:100){ id isResolved comments(first:1){ author } }`.
* The parser is strict and fail-closed. A truncated connection, a malformed
  node, or an unknown state yields `parse_ok=False`, which `classify()` maps to
  `DETECTION_AMBIGUOUS`.
* `PASS_VERDICTS = {SATISFIED, NOT_APPLICABLE}`. Every other verdict exits 1.
* The module boundary allows the standard library only, with no reach into
  other gate modules.
* `cli.py` (`_gate_copilot_review_command`, around line 876) renders the
  result. It prints an unresolved-thread count line, and its `--json` output
  uses `CopilotReviewResult.to_dict()`.
* Every surface that names the verdict set:
  * `templates/instructions/github-pr-automation.instructions.md.tmpl` and its
    mirror (§1.8, §1.9.4 Check 5, §1.9.5);
  * `templates/policies/workflow-policies.md.tmpl` and its mirror (P-018);
  * `templates/agents/_ship.agent.md.tmpl` and its mirror (7c);
  * `docs/copilot-review-gate.md`.

## Options Evaluated

### Option A: Instruction-only (prose)

Teach §1.2, §1.3, §1.5 to §1.8, and §1.9.2 to read review bodies, handle
threadless findings through a PR comment, and record them in the readiness
block. The gate is unchanged.

* **Pros:** smallest change; no parser for a proprietary format; no
  contract change.
* **Cons:**
  * The gate keeps returning `SATISFIED` over open body findings. That is the
    exact failure in the report.
  * The fix relies on prose, which has failed four times.
  * It contradicts P-018's "not by prose alone" premise.
* **Effort:** low. **Fit:** poor.

### Option B: Gate hard-BLOCK on any body finding of the current-HEAD review

Add a BLOCK verdict whenever the current-HEAD Copilot review body has a
threadless-finding marker.

* **Pros:** deterministic; a simple rule.
* **Cons:**
  * A body finding cannot be "resolved". If the finding is deferred
    (P-021 C2) or declined (invalid) without a new push, the current HEAD stays
    blocked forever. Clearing it would need an operator `--force` every time,
    which is an agent-unreachable path and a dark-mode wedge.
  * Checking only the current HEAD ignores body findings from earlier rounds
    that later rounds do not repeat. Unresolved threads, by contrast, persist
    across HEADs.
* **Effort:** medium. **Fit:** partial.

### Option C: Advisory signal only

The gate detects body findings and reports them in its JSON and message output.
The verdict stays `SATISFIED` (exit 0). The instructions require a disposition
before merge.

* **Pros:** deterministic detection; no exit-code or verdict-set change; no
  wedge.
* **Cons:** enforcement is still prose. An agent that reads only the exit code
  merges anyway.
* **Effort:** medium. **Fit:** partial.

### Option D: Gate BLOCK cleared by an agent-postable disposition marker (thread parity), plus instructions

The gate fetches the review `body` and `databaseId` and runs a conservative,
pure detector of threadless findings. Any completed Copilot review on the PR,
in any round, that carries threadless findings must be dispositioned by a PR
conversation comment with an exact marker line naming that review's
`databaseId`. Until then, the gate returns a new BLOCK verdict. The instructions
teach the loop to read bodies, fix or defer each finding, and post the
disposition comment. The comment is the audit trail that a thread reply
normally provides, and it is what clears the gate.

* **Pros:**
  * Deterministic and fail-closed, consistent with P-018.
  * Parity with thread semantics: findings from every round count, and the
    agent clears them by its own action, exactly as it resolves threads. No
    `--force` is needed.
  * A deferral or decline clears the gate without a push.
  * The PR comment is visible to the operator.
  * It covers both observed formats.
* **Cons:**
  * It is a contract change: a new verdict, new query fields, and a marker
    contract.
  * The detector parses an unversioned proprietary format. A drift could make
    it miss findings, which would fall back to Option A's prose layer.
  * Open PRs that already hold handled-but-unmarked body findings need marker
    comments posted after the upgrade.
* **Effort:** medium to high, across 9 bounded units. **Fit:** best.

## Trade-off Comparison

| Criterion | A: prose | B: hard block | C: advisory | D: block + disposition |
|---|---|---|---|---|
| Closes the reported defect deterministically | No | Yes | No | Yes |
| Deferred or declined finding without `--force` | n/a | No (wedge) | Yes | Yes |
| Earlier-round body findings | Prose only | No | Prose only | Yes |
| Exit-code / PASS-set contract change | None | New BLOCK verdict | None | New BLOCK verdict (exit 1, PASS set unchanged) |
| Format-drift exposure | None | Miss or false block | Miss | Miss (prose layer backstops) |
| Dark-mode autonomy | Yes | Wedges | Yes | Yes |
| Blast radius | Low | Medium | Medium | Medium-high (contract surfaces) |

## Decision

**Adopt Option D, with Option A's instruction layer as the defense-in-depth
backstop.** This decision was made by Stage under Orchestrator delegation on
2026-10-08. The operator directed this entry to be staged first, ahead of the
queued DAG. The operator may override it at plan review or at PR time.

### D1. New BLOCK verdict

* Add `Verdict.UNDISPOSITIONED_BODY_FINDINGS`, evaluated after
  `UNRESOLVED_THREADS` and before `SATISFIED`.
* It exits 1 and is not in `PASS_VERDICTS`.
* The exit codes, `--force` auditing, enforcement modes, and `--max-wait` stay
  unchanged.

### D2. Detector

Add a pure, standard-library function over one review body that returns the
number of threadless findings and the markers matched. The count is:

`max(S, PM) + U`

* `S` is the N in `Suppressed comments (N)`.
* `PM` is the N in `Previously missed (N)`. The legacy format nests PM inside S,
  which is why the formula takes the maximum.
* `U` counts **unanchored open findings**. It equals `max(0, N_open − A)`:
  * `N_open` is the N in the `N open finding(s)` headline or summary;
  * `A` is the number of `#discussion_r<digits>` anchors inside that open
    findings `<details>` block.
  * When the headline is a bold `**N open findings**` with N ≥ 1 and no list
    follows, `A = 0`.

The detector does not count:

* `resolved since last review` items;
* `What changed in this PR`;
* the overview risk line ("Needs a closer look").

Matching is case-insensitive and tolerates `**` and `<strong>` wrappers.

### D3. Scope of reviews

Every completed Copilot review on the PR counts, in any round. A completed
review has state `APPROVED`, `CHANGES_REQUESTED`, or `COMMENTED`. `DISMISSED` and
`PENDING` reviews are excluded.

### D4. Disposition marker

* The marker is a PR conversation (issue) comment, not authored by the Copilot
  bot.
* **Amended by plan review PR-1 (2026-10-08):** the comment's
  `authorAssociation` must be `OWNER`, `MEMBER`, or `COLLABORATOR`. On a public
  repository anyone can comment, but resolving a thread needs write access, so
  this filter restores real parity with thread resolution.
* The comment body contains a line that matches
  `^Copilot-Review-Body-Disposition: <databaseId>$` (multiline; trailing
  whitespace tolerated). The literal token is `Copilot-Review-Body-Disposition:`.
* One comment may carry several marker lines, one per review.
* The gate checks only that the marker is present. This is the same trust level
  as agent-performed thread resolution. The content contract lives in the
  instructions:
  * the comment quotes each finding;
  * each finding is marked fixed at a SHA, deferred to a stash ID, or declined
    with a rationale.

### D5. Fail-closed parsing additions

The following yield `DETECTION_AMBIGUOUS`:

* a non-string `body` on a Copilot review;
* a Copilot review with threadless findings but no integer `databaseId`;
* a malformed PR `comments` connection;
* a `comments(last:100)` connection that is truncated
  (`hasPreviousPage` is not `False`) while at least one body-finding review
  has no marker among the fetched comments.

A body with no recognized markers counts as zero findings. This is a documented
limitation, and the D6 prose layer covers it.

### D6. Instruction layer (template plus mirror)

The PR-automation instruction changes are:

* §1.2 reads every Copilot review's `body`;
* §1.3 classifies body findings;
* a new threadless-finding handling step covers fixing or capturing the finding
  first, then posting the disposition comment with shell-safe construction;
* §1.7 defines a clean round on threads **and** bodies;
* §1.8 counts a body finding as a cycle. The P-021 C3/C4 halt applies to an
  in-scope body finding at the limit;
* §1.9.1 adds `databaseId` and `body` to `reviews`;
* §1.9.2 adds a `Review-body findings:` readiness field;
* §1.9.4 Check 5 and §1.9.5 add the new verdict and its remediation.

The P-018 policy text and Ship 7c gain the third condition and the new verdict
name.

### D7. Priority

Stage re-prioritizes the work from **medium to high**. The reasons are the
fourth recurrence, a fail-closed merge gate that silently passes over valid
findings, and the operator's directive to stage it first.

## Rejected Alternatives

* **A (prose only).** It has failed four times, and it leaves the reported gate
  defect in place. It is retained only as the D6 backstop.
* **B (current-HEAD hard block).** It wedges on any deferral or decline, needs
  operator `--force` in normal operation, and ignores earlier rounds.
* **C (advisory).** It leaves the merge decision to prose. P-018's whole premise
  is to remove that dependency.
* **Marker in the PR body readiness block instead of PR comments.** This was
  rejected because the PR body is rewritten every round, so a marker there is
  easy to lose. A PR comment is append-only and timestamped, and it is the audit
  trail the source learning prescribes.
* **Parsing each finding's identity (path:line or title) and requiring one
  marker per finding.** This was rejected because it is over-coupled to the
  proprietary format. A per-review marker plus the instruction-level per-finding
  content is sufficient and more robust.

## Unresolved Questions

* **OQ-1.** Copilot may change the body format (a `ccr-overview-v3`). The
  detector tolerates wrapper changes but not renamed sections. The plan adds an
  advisory `detail` note when a body carries a `ccr-overview-v<N>` marker with
  N ≠ 2, so drift is visible. A miss still falls back to the prose layer. This
  is not blocking.
* **OQ-2.** In-flight PRs at upgrade time need disposition comments posted for
  body findings they already handled. The rollout note in the plan states this.
  At staging time no PR is open from this harness.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| False BLOCK from a format variant (for example, an anchored open finding miscounted) | Fail-closed is the intended direction. The agent clears it by posting the disposition marker, which needs no `--force`. Fixture tests use real bodies from PR #506 (rounds 1, 2, 6) and PR #444. |
| False negative after format drift | The D6 prose layer reads every body. The OQ-1 advisory detail surfaces an unknown overview version. |
| Existing tests' GraphQL fixtures lack the new fields, so the strict parser rejects them | The plan updates the shared fixture builder in the same unit (U2) as the parser change. |
| Contract drift across 4 rendered surfaces and the doc | U8 adds a cross-surface pin on the verdict name and the marker literal, derived from the code constants. |
| Template/mirror pre-existing drift in `github-pr-automation` | The new text is inserted semantically identically in both files. The drift is not reconciled here (out of scope). |
