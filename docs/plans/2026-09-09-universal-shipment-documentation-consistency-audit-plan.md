---
title: "Universal shipment documentation consistency audit"
description: "Implementation plan for promoting the ten-category documentation consistency audit from an ephemeral PR-body checklist into a durable, technology-agnostic harness capability applied on every shipment in every installed workspace: one normative instruction template as single source of truth, referenced from Ship/operational-closure/pr-lifecycle and the Evidence Consistency Reviewer persona; consolidation of the existing compound taxonomy learning; a PR-body concision contract; an anti-self-referential-readiness rule; dogfood mirror parity plus manifest checksum refresh; and deterministic verification across three target technology profiles."
source: "docs/decisions/2026-09-09-universal-shipment-documentation-consistency-audit-deliberation.md"
source_stash: 8F2FD1F6
date: 2026-09-09
status: reviewed
requires_plan_hardening: "yes"
plan_hardening_status: "hardened"
plan_review_verdict: "PASS"
plan_review_cycles: 1
evidence:
  - docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md
  - docs/compound/2026-08-18-stage-agent-checkpoint-index-sync-ordering-self-contradiction.md
  - .backlogit/queue/162.004-T.md
depends_on_shipment: 170-S
related_but_distinct:
  - "feature 162-F / shipment 170-S — builds the CONDITIONAL Evidence Consistency Reviewer persona and review-skill retrieval. This plan is the universalization layer ON TOP of it, sequenced behind it. It MUST NOT re-author the persona from scratch, re-open 170-S's PASS verdict, or restate its rubric."
  - "stash 1CD92B69 / 6B627A50 / 2B68F9D6 — Stage publication-currency gaps for 161-F/163-F/169-S/171-S. Unrelated planned work; their untracked artifacts must NOT be swept into this feature's publication."
tags: [plan, documentation-consistency, universality, compound-learning, template-authoring, p-021, dogfood-parity]
---

## Problem Frame

PR #440 carried a ten-point documentation consistency checklist in its **PR
body** and then deleted it before merge. The audit worked; the delivery vector
did not survive. The operator's requirement is that the audit become *"a
compound learning that gets applied by the harness on every shipment regardless
of workspace in which the harness is installed."*

**Requires plan hardening: yes.** The change spans three template families
(instructions, agents, skills), modifies a readiness gate surface, and touches
installed dogfood files under manifest checksum control.

### The constraint that shapes everything

Verified 2026-09-09: **no mechanism propagates `docs/compound/` content into an
installed workspace.** `templates/skills/compound/SKILL.md.tmpl` authors into
the *target's own* initially-empty `docs/compound/`; nothing under
`templates/foundation/`, `templates/packs/`, or any install layer bundles
learning content.

Consequently the requirement splits across two vectors, and conflating them
would produce a plan that cannot deliver:

| Vector | Carrier | Scope |
|---|---|---|
| **Memory** — *why* the audit exists | `docs/compound/` (consolidated) | This repository only |
| **Behaviour** — the audit itself | Normative **template** surfaces | Every installed workspace |

### Grounded surfaces (verified 2026-09-09, line counts from working tree)

| Surface | Dogfood | Template | Lines (dogfood/template) |
|---|---|---|---|
| Ship agent | `.github/agents/_ship.agent.md` | `templates/agents/_ship.agent.md.tmpl` | 835 / 1111 (pre-existing drift) |
| operational-closure | `.github/skills/operational-closure/SKILL.md` | `templates/skills/operational-closure/SKILL.md.tmpl` | 125 / 125 |
| pr-lifecycle | `.github/skills/pr-lifecycle/SKILL.md` | `templates/skills/pr-lifecycle/SKILL.md.tmpl` | 336 / 336 |
| review skill | `.github/skills/review/SKILL.md` | `templates/skills/review/SKILL.md.tmpl` | 235 / 235 |
| pull-request instruction | `.github/instructions/pull-request.instructions.md` | `templates/instructions/pull-request.instructions.md.tmpl` | 42 / 42 |
| **New** audit instruction | `.github/instructions/shipment-documentation-audit.instructions.md` | `templates/instructions/shipment-documentation-audit.instructions.md.tmpl` | — (new) |
| Evidence Consistency persona | `.github/agents/subagents/evidence-consistency-reviewer.agent.md` | `templates/agents/review/evidence-consistency-reviewer.agent.md.tmpl` | **created by 162.004-T (170-S)** |

**Path contract (verified, do not assume a mirror):** personas install to
`.github/agents/subagents/` but their templates live under
`templates/agents/review/*.agent.md.tmpl`. The directory names do not mirror and
`templates/agents/subagents/` does not exist.

Manifest entries carry `path` / `primitive` / `template` / `checksum` (SHA-256
over raw LF bytes, computed from the staged git blob via
`git cat-file -p :<path>`, never a raw Windows working-tree read) / `note` in
`.autoharness/harness-manifest.yaml`. **Every installed file changed by this
plan requires a recomputed checksum.**

## The ten audit categories (single source of truth)

Authored once in the new instruction template. Categories 1, 2, 3, 4, 7, 10 are
inherited from the existing taxonomy; **5, 6, 8, 9 are new** and are the
completion half of this feature.

| # | Category | Origin |
|---|---|---|
| 1 | Lifecycle/temporal consistency | taxonomy RC-11 |
| 2 | Status consistency across frontmatter/headings/conditions/summaries/follow-ups/verdicts | taxonomy RC-2, RC-5 |
| 3 | Immutable evidence semantics (`last_code_affecting_head` vs current PR HEAD; no self-referential SHA claims) | taxonomy RC-9 + round-17 addendum; **PR #439** |
| 4 | PR/commit/branch/task/shipment identity consistency | taxonomy RC-1, RC-2 |
| 5 | Quantitative consistency (tests/findings/items/counts) | **new** |
| 6 | Ownership/role attribution consistency | **new** |
| 7 | Path/cross-reference integrity incl. moved/archived/compacted files and relocation stubs | taxonomy RC-10 |
| 8 | Scope/distribution wording consistency | **new** |
| 9 | Frontmatter schema consistency with canonical *neighbouring* artifacts | **new** (taxonomy checks own-frontmatter only) |
| 10 | Stale TODO/pending/conditional language after conditions are satisfied | taxonomy RC-5; `2026-08-18` learning |

## Design decisions carried from deliberation

* **D1** — categories authored **once**; all other surfaces reference, never
  restate. Restating would manufacture the cross-surface drift the audit exists
  to catch.
* **D2** — audit obligation is **unconditional per shipment**; an explicit
  "no documentation surface touched" outcome must still be recorded, so an
  unrecorded audit is distinguishable from one that never ran.
* **D3** — **technology-agnostic predicates only**. No `.backlogit/**`,
  `src/autoharness/**`, Python, Copilot, or IDE/provider names in normative text.
* **D4** — **consolidate** the existing compound taxonomy learning in place; no
  competing entry.
* **D5** — PR bodies carry **verdict + evidence pointer + deferred follow-up
  IDs only**.
* **D6** — **anti-self-referential readiness**: mutable surfaces own current-HEAD
  readiness; committed evidence records only immutable/named observed state.
* **D7** — **P-021 integration**: in-scope fixed before readiness, out-of-scope
  captured before disposition. No new deferral mechanism.
* **D8** — **no new template variables**; verified negatively.

## Work Breakdown

Nine tasks, each scoped under the 2-hour rule, width-isolated so no task mixes
template authoring with CLI/schema work.

| # | Task | Concern | Size | Cx |
|---|---|---|---|---|
| T1 | RED: audit presence/parity/variable-hygiene tests | verification | S | low |
| T2 | Author universal audit instruction template + dogfood mirror | template authoring | M | medium |
| T3 | Consolidate compound taxonomy learning | compound authoring | S | low |
| T4 | Universalize persona trigger (conditional → every-shipment, agnostic) | agent template | M | high |
| T5 | Ship agent weave: pre-readiness audit + P-021 disposition | agent template | M | medium |
| T6 | pr-lifecycle + pull-request: PR-body concision contract | skill/instruction | S | medium |
| T7 | operational-closure weave: audit before closure | skill | S | low |
| T8 | Dogfood mirror parity + manifest checksum refresh | dogfood parity | S | medium |
| T9 | GREEN: three-technology-profile acceptance verification | verification | M | medium |

### T1 — RED: audit presence/parity/variable-hygiene tests

Author failing tests first, per P-004 red-phase discipline. Assert: the audit
instruction template exists and enumerates exactly ten categories; each
referencing surface points at it; **no surface restates the category list**
(anti-duplication assertion); the template introduces **no new `{{...}}`
variables** and leaves none unresolved. Tests must fail against pre-change HEAD.

### T2 — Author universal audit instruction template + dogfood mirror

Create `templates/instructions/shipment-documentation-audit.instructions.md.tmpl`
and its installed mirror. Contains: the ten categories with a checkable
predicate each, the D6 anti-self-reference rule, the D7 P-021 routing rule, the
D5 PR-body concision contract, and the recorded-outcome requirement from D2.
Technology-agnostic language only (D3).

### T3 — Consolidate compound taxonomy learning

Extend `docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md` in
place: fold in categories 5/6/8/9, state the ten-category universal form, add
PR #439 (self-referential `reviewed_head` fixed-point loop) and PR #440
(recurring documentation inconsistencies) evidence, and record the
delivery-paradox finding. Preserve and extend existing canonical frontmatter
(`problem_type`, `category`, `root_cause`, `tags`). **Create no competing entry.**

### T4 — Universalize persona trigger

Amend the Evidence Consistency Reviewer persona (template + installed mirror,
**as delivered by 170-S**) so its rubric references the T2 instruction rather
than carrying its own copy, and its trigger becomes every-shipment with
technology-agnostic predicates. **Highest collision risk** — must re-read the
persona as 170-S actually left it rather than as this plan predicts.

### T5 — Ship agent weave

Add a mandatory pre-readiness audit step to Ship (template + mirror) that
invokes the audit, records its outcome, fixes in-scope findings before claiming
readiness, and routes out-of-scope findings through P-021 capture before
disposition. Respect the pre-existing 835/1111-line dogfood drift: mirror only
the changed region, per width-isolation precedent.

### T6 — pr-lifecycle + pull-request concision contract

Encode D5: PR bodies carry audit verdict, evidence pointer, and deferred
follow-up IDs — never the category list. Add an explicit prohibition so a future
agent does not re-paste the checklist (the exact PR #440 regression).

### T7 — operational-closure weave

Require the audit outcome to be present and satisfied before closure evidence is
written, consistent with D6 (closure records immutable observed state).

### T8 — Dogfood mirror parity + manifest checksum refresh

Recompute SHA-256 checksums over LF-normalized staged git blobs for every
changed tracked `.github` artifact; add manifest entries for the new instruction.

### T9 — GREEN acceptance across three technology profiles

Render and verify against **three profiles from the schema's own enumeration** —
`python`/`cli-tool`, `typescript`/`web-app`, `go`/`mcp-server` — asserting the
audit surface renders, is referenced consistently, contains no stack-specific
tokens, and passes existing template quality gates (frontmatter validity,
Markdown structure, variable completeness, cross-reference integrity).

## Acceptance Criteria

1. Ten categories exist in exactly one normative location; all other surfaces
   reference it. Anti-duplication test passes.
2. Audit is unconditional per shipment; a "no documentation surface" outcome is
   still recorded.
3. No stack/IDE/provider-specific tokens in any normative audit text.
4. Compound taxonomy learning consolidated in place; no competing entry; canonical
   frontmatter intact.
5. PR-body concision contract enforced; checklist prohibited in PR bodies.
6. Anti-self-referential rule stated and testable.
7. P-021 routing wired both directions.
8. **No new template variables**; variable-resolution docs untouched.
9. Dogfood mirrors match templates for changed regions; manifest checksums refreshed.
10. Verification green on all three technology profiles plus existing quality gates.

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **File collision with 170-S** on Ship agent, review persona, pr-lifecycle | High | Hard dependency edge; T4/T5/T6 must re-read post-170-S content before editing, never assume this plan's predicted text |
| Restating categories in a referencing surface (self-inflicted RC-10) | Medium | T1 anti-duplication test is the guard |
| Ship agent dogfood drift (835 vs 1111) tempts a full re-render | Medium | Width-isolation: mirror only changed regions, per existing manifest precedent |
| Audit becomes unbounded/expensive on every shipment | Medium | Bounded predicate list; "no documentation surface touched" is a valid fast outcome |
| Sweeping unrelated untracked Stage artifacts into publication | High | Selective staging only; 61 unrelated dirty artifacts explicitly out of scope |

## Out of Scope

* Re-authoring anything 170-S delivers.
* Any propagation of `docs/compound/` content into target workspaces (impossible
  by design; behaviour travels via templates).
* The 161-F/163-F/169-S/171-S publication-currency gaps (stash 1CD92B69,
  6B627A50, 2B68F9D6).
* Source/CLI/schema changes — none required.

---

## Plan Hardening Record (P-006)

Hardening applied 2026-09-09 because blast radius spans three template families
plus checksum-controlled installed artifacts.

| # | Hardening finding | Resolution |
|---|---|---|
| H1 | Original draft authored a *new* compound entry, duplicating the taxonomy learning | Changed to in-place consolidation (D4/T3); operator instruction and RC-10 both require it |
| H2 | Original draft restated the ten categories in Ship, pr-lifecycle, and the persona | Collapsed to single-source + reference (D1); T1 anti-duplication test added as the enforcing guard |
| H3 | "Every shipment" risked unbounded cost on code-only shipments | D2 refined: obligation unconditional, *invocation* may fast-path, but outcome always recorded |
| H4 | Trigger predicates inherited dogfood paths from `162.004-T` | D3 added; T9 asserts absence of stack-specific tokens |
| H5 | No explicit guard against re-pasting the checklist into PR bodies | T6 adds an explicit prohibition, not merely an omission |
| H6 | Collision with 170-S under-specified | Promoted to a hard dependency edge + explicit "re-read as left by 170-S" instruction in T4/T5/T6 |
| H7 | D8 (no new variables) was aspirational | Made testable: T1 asserts negatively |
| H8 | Self-referential rule risked recreating the PR #439 loop in the audit's own evidence | D6 restructures rather than re-substitutes; committed evidence never names its own commit |

## Plan Review Record

**Verdict: PASS** (cycle 1 of max 3). Zero P0, zero P1.

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| P2-1 | P2 | T4 depends on content that does not yet exist on disk (170-S unshipped) | Accepted — dependency edge makes this safe; T4 carries an explicit re-read instruction rather than a predicted diff |
| P2-2 | P2 | Ship agent dogfood/template drift (835/1111) may widen during execution | Accepted — width-isolation mirroring is established precedent in the manifest notes |
| P3-1 | P3 | Nine tasks is at the upper end for one shipment | Accepted — each is independently ≤2h and width-isolated; splitting would fragment the single coherent contract |

**Gate results:** 2-hour rule satisfied for all nine tasks; width isolation holds
(no task mixes template work with CLI/schema work); every task has a parent
feature; no P-003 violations; acceptance criteria are machine-checkable.
