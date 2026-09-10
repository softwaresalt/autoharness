---
title: "Hosted-review pattern learning: proactive detection + bounded compound promotion"
description: "Implementation plan for baking Copilot/hosted-review finding-pattern learning into the harness: a pre-PR pattern-retrieval step and Evidence Consistency Reviewer persona in the review skill, a bounded mechanical post-fix delta check, a hosted-review finding inventory and compound-promotion checkpoint in pr-lifecycle, suppressed-finding enumeration in the GitHub PR automation instruction, Ship wiring at both ends, and template/dogfood parity plus manifest checksum coverage."
source: "docs/decisions/2026-09-07-review-pattern-learning-methodology-deliberation.md"
date: 2026-09-07
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
evidence:
  - docs/reviews/2026-09-07-pr-436-copilot-finding-inventory.md
  - docs/reviews/2026-09-07-pr-436-adversarial-review.md
  - docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md
related_but_distinct:
  - "stash 846D0282 / 0BE73C89 / 9E22BFC6 / 27F9EC8A / AFEFC6AB — PR #436 evidence defects. MUST NOT be folded into this shipment; they are the *motivating data*, not the scope."
  - "shipment 169-S (Pre-Mode member-class contract) — separate charter; this plan must not touch shipment-reconcile's Pre-Mode."
tags: [plan, review, compound-learning, p-018, p-021, dogfood-parity, reliability]
---

## Problem Frame

Hosted review is the harness's most productive defect detector and its least
systematically exploited one. PR #436: **13 rounds, 56 utterances, 24 distinct
findings, 12 root-cause classes, 100% escape past local review and CI**, with
**three classes already recorded in `docs/compound/` and never retrieved**.

The harness has the knowledge and lacks the loop. This plan installs the loop.

**Requires plan hardening: yes.** The change spans four agent/skill/template
families, modifies a review gate surface, and touches installed dogfood files
under manifest checksum control.

### Grounded surfaces (verified 2026-09-07)

| Surface | Dogfood | Template | Lines (dogfood/template) |
|---|---|---|---|
| review skill | `.github/skills/review/SKILL.md` | `templates/skills/review/SKILL.md.tmpl` | 235 / 235 |
| pr-lifecycle skill | `.github/skills/pr-lifecycle/SKILL.md` | `templates/skills/pr-lifecycle/SKILL.md.tmpl` | 336 / 336 |
| PR automation instruction | `.github/instructions/github-pr-automation.instructions.md` | `templates/instructions/github-pr-automation.instructions.md.tmpl` | 795 / 801 |
| Ship agent | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | 835 / 1111 |
| Copilot review instruction | `.github/instructions/copilot-code-review.instructions.md` | — | 72 |
| Persona subagents | `.github/agents/subagents/` (13 installed) | `templates/agents/review/*.agent.md.tmpl` | **names do not mirror — verified** |

Manifest entries carry `path` / `primitive` / `template` / `checksum`
(SHA-256 over raw LF bytes) / `note` in `.autoharness/harness-manifest.yaml`.
**Every installed file changed by this plan requires a recomputed checksum.**

Anchor points:

* `review/SKILL.md` — persona tables at "Always-On"/"Conditional"; workflow at
  "### Step 1: Determine Review Scope" → "### Step 2: Route Personas".
* `pr-lifecycle/SKILL.md` — "### Step 3: Handle review feedback" (line 102),
  "### Step 4b: Re-request review after fixes" (184), "### Step 5: Merge
  approval gate" (196), "### Step 6: Post-merge cleanup" (292).
* `github-pr-automation.instructions.md` — Part 1 §1.3 categorize, §1.5 reply,
  §1.6 resolve.

## Scope

**In scope:** the retrieval → detection → synthesis → promotion loop, its
persona, its mechanical checks, its metrics, and proof that templates and
dogfood mirrors carry it.

**Out of scope (explicit):** fixing PR #436; changing P-018 gate semantics;
changing circuit-breaker limits; `shipment-reconcile` Pre-Mode (169-S);
`AGENTS.md` / `.github/copilot-instructions.md` / constitution edits beyond a
single pointer line; any runtime telemetry engine.

## Design

### D1 — `review` Step 1.5: Review-Pattern Retrieval

Insert between Step 1 (scope) and Step 2 (routing), so its output can
**influence routing**.

1. Derive a class query from the changed-file categories (evidence artifacts,
   templates, gates, CLI).
2. Search `docs/compound/` for entries whose `problem_type` /`category` /
   `root_cause` / `tags` match, **prioritising**
   `2026-09-07-copilot-review-finding-pattern-taxonomy.md`.
3. Emit `PATTERN_RETRIEVAL_OK: {n} classes` or
   `PATTERN_RETRIEVAL_EMPTY` (non-blocking).
4. If any retrieved class's trigger matches the diff, **mark the Evidence
   Consistency Reviewer as required** for Step 2.

Degraded mode: on retrieval failure, log
`TOOL_DEGRADED: pattern-retrieval — fallback: taxonomy file read` and read the
taxonomy file directly. Never silently skip.

### D2 — Evidence Consistency Reviewer (new conditional persona)

New installed file `.github/agents/subagents/evidence-consistency-reviewer.agent.md`, paired template `templates/agents/review/evidence-consistency-reviewer.agent.md.tmpl` (**verified 2026-09-07**: personas install to `.github/agents/subagents/` but their templates live under `templates/agents/review/` — the directory names do NOT mirror; `templates/agents/subagents/` does not exist).

* **Trigger:** diff touches `docs/closure/**`, `docs/memory/**`,
  `.backlogit/**`, `docs/reviews/**`, **or** any file whose frontmatter carries
  a key read by `src/autoharness/gates/**`.
* **Rubric:** the 10-point evidence-consistency checklist from the compound
  learning, verbatim.
* **Hard constraint:** reads the **branch tree** (`git show HEAD:<path>`,
  `git grep … HEAD`), never the working tree. This is what makes it able to
  see what a reviewer sees.
* Added to `review/SKILL.md`'s Conditional persona table and to Step 2's
  routing rules alongside Security / Template Integrity / Schema-CLI-Docs.

### D3 — Post-fix delta check (bounded, mechanical, not a review round)

New subsection in `review/SKILL.md` and referenced from `pr-lifecycle` Step
4b. Runs after each review-fix commit, **on touched files only**, immediately
before push. Exactly four checks — the mechanisable classes:

| Check | Class | Assertion |
|---|---|---|
| `head_sha_parity` | RC-9 | readiness block SHA == `git rev-parse HEAD` |
| `identifier_propagation` | RC-10 | `git grep` each corrected identifier; all hits agree |
| `chronology_verbs` | RC-11 | every "before/prior to/immediately before <mutation>" claim resolves to evidence whose commit precedes the mutation, or contains the word "reconstructed" |
| `date_ordering` | RC-12 | every disposition date ≥ the `created_at` of the entity it dispositions |

Emits a 4-line pass/fail block appended to the PR's Review History.
**Never triggers a review round; never consumes circuit-breaker budget.**

### D4 — `pr-lifecycle` hosted-review finding inventory + compound checkpoint

New **Step 3c** (after Step 3's disposition sequence) and **Step 6b**
(post-merge cleanup):

* **3c — Inventory.** Enumerate findings from **both** `reviewThreads` **and**
  the `body` field of every hosted review (per §1.3 update in D5). Classify
  each into the 12 taxonomy classes. Record round/HEAD, thread-or-suppressed,
  class, severity, disposition.
* **6b — Compound checkpoint.** Apply the 5-signal promotion threshold. For
  each promotable class: **append** to the existing `docs/compound/` entry with
  matching `root_cause`, or create one **only if the class is new**. Emit the
  five metrics into the closure record's review section.

### D5 — `github-pr-automation.instructions.md` §1.3

Add a **suppressed-findings enumeration** requirement with the exact recipe:

```text
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){
  pullRequest(number:$n){reviews(last:50){nodes{ id body submittedAt commit{oid}
  author{login} }}}}}' -F o=<owner> -F r=<repo> -F n=<pr>
```

Parse each `body` for `### Suppressed comments (N)` and extract every
`**path:line**` + bullet. **A round is not "clean" until both thread count and
suppressed count are zero** — PR #436 read "clean" five times while carrying
36 suppressed findings.

### D6 — Ship agent wiring

Two insertions in `_ship.agent.md` + template:

1. **Before local readiness** — invoke `review` (which now performs D1/D2);
   record `PATTERN_RETRIEVAL_*` in the readiness block.
2. **After hosted review / at closure** — invoke the D4 inventory + checkpoint.
3. **Stage handback (fixes AF-07's structural cause)** — when Ship observes a
   Stage-owned data-currency gap (stash entry, backlog record) that it may not
   itself edit under P-021 capture-only, it MUST record it as a **readiness
   blocker routed to Stage**, not merely capture it and proceed to claim
   readiness. P-001/P-021 preserved: Ship still does not edit; it declines to
   claim readiness.

### D7 — `copilot-code-review.instructions.md` pointer

One paragraph pointing at the taxonomy and the 10-point checklist. **No policy
text.** Foundation files untouched.

## Task Decomposition (test-first)

Every implementation task is preceded by its RED test task. `T1` and `T2` are
pure-test tasks that must be observed failing before `T3`+ land.

| # | Task | Type | Depends on |
|---|---|---|---|
| **T1** | RED: parity + presence tests for review-skill changes — assert `review/SKILL.md` and its `.tmpl` both contain Step 1.5, the Evidence Consistency Reviewer row, and the delta-check subsection; assert byte-parity of the shared region | test | — |
| **T2** | RED: parity + presence tests for pr-lifecycle / PR-automation changes — Step 3c, Step 6b, §1.3 suppressed enumeration, in both dogfood and template | test | — |
| **T2b** | RED: **behavioural** assertions for Ship's readiness-semantics change — assert the Stage-handback rule is present in both Ship surfaces AND that it is specified as `READY_WITH_FOLLOWUPS` + named blocker (not a hard halt) except when the gap contradicts a machine-readable gate field | test | — |
| **T3** | Author `evidence-consistency-reviewer.agent.md` + template mirror (10-point rubric, branch-tree constraint) | impl | T1 |
| **T4** | `review` skill + template: Step 1.5 retrieval, persona table row, Step 2 routing rule | impl | T1, T3 |
| **T5** | `review` skill + template: post-fix delta check subsection (4 checks), including the explicit circuit-breaker non-consumption assertion | impl | T4 |
| **T5b** | `review` skill + template: Stage-run analysis posture for report-only mode (AF-11) | impl | T4 |
| **T6** | `pr-lifecycle` skill + template: Step 3c inventory, Step 6b compound checkpoint + metrics | impl | T2 |
| **T7** | `github-pr-automation.instructions.md` + template: §1.3 suppressed-findings enumeration + GraphQL recipe | impl | T2 |
| **T8** | `_ship.agent.md` + template: retrieval-before-readiness, synthesis-at-closure, Stage-handback rule | impl | T2b, T4, T6 |
| **T9** | `copilot-code-review.instructions.md` pointer | impl | T4, T6 |
| **T10** | Recompute `.autoharness/harness-manifest.yaml` checksums for every changed installed file; GREEN the T1/T2/T2b suites | impl | T3–T9 |

### Test anchor strategy (binding)

Presence/parity tests MUST anchor on **structural markers** — heading text,
table-row cell content, named tokens — never on line numbers or brittle
whole-line regex. Prior art:
`docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md`.
Markdown has no AST guarantee here, so the equivalent discipline is:
locate the heading, then assert within its section slice.

### Role ownership (binding)

* The **post-fix delta check (D3)** is executed by **Ship** during its
  review-fix loop, and may be executed by **Stage** in report-only analysis
  posture. It is never executed by a persona subagent.
* The **compound checkpoint (D4/Step 6b)** authors files under
  `docs/compound/` and `docs/reviews/`; when it runs inside a Ship session it
  is a documentation write on Ship's own closure surface, not a Stage action.
  Promotion decisions that would create a **new backlog item** remain Stage's.

### Circuit-breaker relationship (binding)

The delta check MUST NOT count as a review-fix cycle and MUST NOT consume
circuit-breaker budget. Prior art constraining this boundary:
`docs/compound/093-S-review-loop-convergence.md` (unbounded auto-triggered
review loops) and
`docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`
(what does and does not constitute a cycle). T5 must assert this in text.

**Canonical source gate** (PowerShell form, run at T1, T2, and T10):

```powershell
$env:PYTHONPATH='src'; python -m unittest discover -s tests
```

## Verification

* T1/T2 observed **RED** before T3 lands (P-004 red-phase evidence).
* T10 observed **GREEN** with the full suite.
* Template ↔ dogfood parity asserted mechanically, not by eye — this is the
  repository's recurring failure mode (`096-S-template-vs-global-skill-placeholders`).
* No unresolved template-variable placeholders (double-brace form) in any authored template.
* Every cross-reference in new text resolves to a file that exists.
* `markdownlint` clean on all touched Markdown.

## Rollback

All changes are additive Markdown in versioned files. Rollback is
`git revert -m 1 <merge-sha>` (mainline-parent form — the RC-7 lesson from
this very PR), followed by restoring the prior manifest checksums from the
same revert. No data migration, no schema change, no CLI surface change.

## Residual risks

* **Persona cost** — one extra conditional persona on evidence-bearing diffs
  only. Accepted.
* **Delta check false positives** on legitimately-reconstructed evidence —
  mitigated: the RC-11 check passes when the word "reconstructed" is present,
  i.e. it enforces *disclosure*, not *prohibition*.
* **Ship's Stage-handback rule could deadlock a PR** if Stage is unavailable.
  Mitigated: it produces `READY_WITH_FOLLOWUPS` + a named blocker, not a hard
  halt, unless the gap contradicts a machine-readable gate field.

## Plan Hardening

**Hardening required: yes.** Triggers present: (a) the change spans four
agent/skill/template families; (b) it modifies a **review gate surface**,
which is the harness's own defect-detection control; (c) it edits installed
dogfood files under manifest checksum control; (d) it changes **Ship's
readiness semantics** (D6.3), which is a behavioural contract, not
documentation.

### Reinforcing context consulted

| Source | What it constrains here |
|---|---|
| `docs/compound/093-S-review-loop-convergence.md` | The delta check must not become an unbounded auto-triggered loop |
| `docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md` | What legitimately counts as a review-fix cycle |
| `docs/compound/114-S-109-F-copilot-review-fix-patterns.md` | Suppressed comments; "a stated condition is only real if code enforces it" |
| `docs/compound/096-S-template-vs-global-skill-placeholders.md` | Template↔dogfood parity is a recurring failure mode; assert it mechanically |
| `docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md` | Structural anchors, not line-number regex |
| `docs/compound/2026-05-06-harness-manifest-artifacts-vs-entries-added.md` | Manifest entry/checksum discipline |
| `.github/instructions/circuit-breaker.instructions.md` | Review-Fix Cycle Definition; P-021 C1 test |
| `.github/instructions/role-enforcement.instructions.md` | P-001/P-010 role separation for D6.3 |

### Risky actions

| # | `ProposedAction` | `ActionRisk` | Approval needed |
|---|---|---|---|
| RA-1 | Modify `.github/skills/review/SKILL.md` — the harness's own review gate | **medium** — a defect here degrades every subsequent review | No; covered by T1 RED tests + full suite |
| RA-2 | Modify `_ship.agent.md` readiness semantics (Stage-handback) | **high** — can change whether a PR is presentable | **Yes** — operator confirmation that `READY_WITH_FOLLOWUPS`-with-named-blocker is the correct strength |
| RA-3 | Recompute `.autoharness/harness-manifest.yaml` checksums | **medium** — a wrong checksum makes `verify-harness` report drift on an unmodified file | No; verified by re-running `verify-harness` |
| RA-4 | Add a conditional persona (spawn cost on evidence diffs) | **low** | No |

No destructive action, no migration, no data mutation, no schema change, no
CLI surface change. Nothing in this plan deletes or rewrites existing content;
all edits are additive sections and table rows.

### Deepened runtime verification

* **Environment precheck:** `python --version`, `backlogit --version`, and
  `git rev-parse --show-toplevel` resolve before T1 runs.
* **Target scenarios:** (1) a code-only diff — Evidence Consistency Reviewer
  must **not** trigger; (2) a `docs/closure/**` diff — it **must** trigger;
  (3) a diff touching a file whose frontmatter carries a
  `src/autoharness/gates/**`-consumed key — it **must** trigger via the
  frontmatter clause, not the path clause.
* **Blocked-path handling:** if `docs/compound/` is empty or unreadable,
  Step 1.5 emits `PATTERN_RETRIEVAL_EMPTY` and the pipeline continues. The
  loop degrades to today's behaviour; it never fails closed on a knowledge
  lookup.

### Deepened operational closure

* **Monitoring signals:** hosted-review round count per PR; recurrence rate;
  escaped-to-hosted-review count. All three come from the D4 inventory — the
  same artifact the plan installs.
* **Rollback triggers:** (a) Evidence Consistency Reviewer produces ≥3 false
  P0/P1 on a single PR; (b) the delta check blocks a push on a legitimately
  reconstructed-and-disclosed artifact; (c) `verify-harness` reports checksum
  drift on a file this plan did not change.
* **Rollback procedure:** `git revert -m 1 <merge-sha>` — **mainline-parent
  form**; a bare `git revert` on a merge commit fails (this is RC-7, the exact
  defect Copilot found on PR #436 and the reason it is written out here).
* **Owner:** Ship for execution; Stage for the promotion-threshold semantics.
* **Validation window:** **both** the next full CI run on `main` **and** the
  next PR that triggers the Evidence Consistency Reviewer — *not* "whichever
  comes first" (RC-8, also from PR #436).

### Human checkpoints

1. **Before T8**: operator confirms RA-2's strength (`READY_WITH_FOLLOWUPS`
   vs hard halt).
2. **Before T10**: operator confirms the manifest-checksum recompute set
   matches exactly the files this shipment changed.

### Review-gate capability risk carried forward

Model-specific dispatch is **not currently available** in this workspace.
Plan review below therefore emits an explicit
`dispatch_mode: same-model-declared-degradation` marker and a literal
`decision:` marker, and applies every persona rubric inline rather than
skipping any persona.

### Unresolved operator decisions

* **RA-2 strength** (above) — does not block planning or harvest; blocks T8.
* Nothing else. The promotion threshold, metrics, and surface list are decided
  in the deliberation.

## Plan Review

`dispatch_mode: same-model-declared-degradation`

`decision: PASS` *(cycle 2; cycle 1 was `decision: FAIL`)*

### Gate decision and rationale

Cycle 1 returned **FAIL** on one P1. Cycle 2, after bounded remediation,
returns **PASS**: zero P0, zero P1, zero P2 outstanding, three P3 advisories
acknowledged. Hardening was required and is present, with `ProposedAction` /
`ActionRisk` classification for all four risky actions.

**Declared degradation:** `TOOL_DEGRADED: model-specific-review-routing —
declared fallback: same-model inline rubric pass`. Every persona rubric below
was applied in full; none was skipped. Anchor-reviewer route unavailable, so
Architecture Strategist ran as an inline same-model pass.

### Persona coverage

| Persona | Tier | How it ran | Triggered by |
|---|---|---|---|
| Constitution Reviewer | always-on | inline, same-model | — |
| Python Reviewer | always-on | inline, same-model | — |
| Scope Boundary Auditor | always-on | inline, same-model | — |
| Learnings Researcher | always-on | inline, same-model | — |
| Architecture Strategist | cross-model (degraded) | inline same-model fallback (anchor route unavailable) | skill/agent/instruction boundary changes |
| Agent-Native Parity Reviewer | cross-model (degraded) | inline same-model fallback | changes Ship's agent-facing readiness contract |
| Security Lens Reviewer | cross-model | **not triggered** | no auth/authz, API surface, sensitive data store, external integration, or secrets management in scope |

### Cycle 1 findings

| ID | Sev | Persona | Finding | Remediation |
|---|---|---|---|---|
| **PR1-1** | **P1** | Agent-Native Parity Reviewer | D6.3 changes **Ship's readiness semantics** — a behavioural contract — but T2 asserted only *textual presence*. A plan that alters when a PR may be presented as ready, verified only by a `grep`, repeats the exact class this plan exists to prevent: a stated condition with no enforcement | **Applied** — added **T2b**, a dedicated RED task asserting both presence *and* the specified strength (`READY_WITH_FOLLOWUPS` + named blocker, not hard halt, except on machine-readable-gate contradiction). T8 now depends on T2b, not T2 |
| **PR1-2** | P2 | Scope Boundary Auditor | T5 bundled two unrelated `review`-skill edits (delta check; Stage-run analysis posture / AF-11) into one task, harming both sizing accuracy and reviewability | **Applied** — split into **T5** and **T5b** |
| **PR1-3** | P2 | Learnings Researcher | The delta check's "not a review round" claim sits on exactly the contested boundary that `093-S` and `2026-08-16-bounded-review-fix-cycle…` already adjudicate, but neither was cited or asserted | **Applied** — added the binding *Circuit-breaker relationship* subsection with both citations and a T5 assertion requirement |
| **PR1-4** | P2 | Constitution Reviewer | No statement of **who** executes the delta check and the compound checkpoint. Ambiguity here is a latent P-001/P-010 hazard | **Applied** — added the binding *Role ownership* subsection |
| **PR1-5** | P2 | Python Reviewer | Presence/parity tests would default to line-regex, which this repository has already recorded as brittle | **Applied** — added the binding *Test anchor strategy* subsection citing `2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md` |

### Cycle 2 findings

Zero P0. Zero P1. Zero P2.

| ID | Sev | Persona | Finding |
|---|---|---|---|
| PR2-1 | P3 | Architecture Strategist | The Evidence Consistency Reviewer's frontmatter-key trigger requires knowing which keys `src/autoharness/gates/**` reads. Today that is `closure_status`, `compaction_status`, `conditions[].satisfied`. If a gate starts reading a new key, the trigger silently under-fires. **Advisory:** consider deriving the key list at review time rather than hard-coding it. Not blocking — the path-based clause already covers every artifact family in practice |
| PR2-2 | P3 | Scope Boundary Auditor | T10 (manifest checksums) is mechanically trivial but touches an 89 KB generated file. Advisory: keep it a standalone task so its diff stays reviewable — **already the case** |
| PR2-3 | P3 | Learnings Researcher | `docs/compound/` now holds seven Copilot-review-related entries. Advisory: a future consolidation pass could merge `107-S`, `114-S` and `115-S` into the new taxonomy entry. Explicitly **out of scope** for this shipment; captured as a candidate, not a task |

### Hardening requirement

Required: **yes**. Satisfied: **yes** — `## Plan Hardening` present with
triggers, reinforcing context, four `ProposedAction`/`ActionRisk` entries,
deepened runtime verification (3 target scenarios + blocked-path handling),
deepened operational closure (monitoring, three rollback triggers,
mainline-parent rollback command, owner, two-condition validation window), two
human checkpoints, and one carried-forward review-gate capability risk.

### Runtime verification and operational closure

Both present and specific. No gaps to call out.

### Recommendation

**Proceed to `harvest`.** RA-2's operator confirmation is a **T8 execution
precondition**, not a harvest blocker.

