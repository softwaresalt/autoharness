---
title: "docs/compound source value semantics - correct the provenance-string outlier and ratchet the conformance check to value shape"
date: 2026-08-23
source: "docs/plans/2026-08-23-docs-compound-source-value-semantics-plan.md"
doc_type: "plan"
stash_id: FAE1E7B7
deliberation: ".backlogit/archive/026-DL.md"
requires_plan_hardening: no
hardening_present: no
review: docs/reviews/2026-08-23-docs-compound-source-value-semantics-review.md
review_verdict: PASS
amendments: "A1, A2, A3, A4, A5 (binding, applied in place)"
blast_radius: "contained (one corpus file frontmatter-only, one test module, one prose bullet in one template file with no installed dogfood counterpart and no manifest checksum entry; one directly-affected repo-side regression test, tests/test_compound_template_docline_frontmatter.py)"
---

# Implementation Plan - docs/compound `source` value semantics

Date: 2026-08-23
Agent: Stage (planning only - Ship executes)
Stash source: `FAE1E7B7`
Deliberation: `026-DL`
Predecessor: `025-DL` -> feature `140-F` / shipment `148-S` (PR #387, merged
`2026-08-22T01:47:17Z`, closure `docs/closure/148-S-140-F-post-merge-closure.md`)
Classification: **bug / corpus conformance violation against an already-merged
autoharness-owned authoring contract**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Goal

Make `source` mean exactly one thing across `docs/compound/`, and make that
meaning CHECKABLE rather than merely documented:

1. correct the single file whose `source` is a provenance string, preserving
   that provenance string verbatim in the key the authoring contract already
   designates for it (`citations`);
2. ratchet the structural guard from a non-emptiness check to a value-shape
   assertion, so the same class of drift cannot recur silently;
3. ratchet the template's Quality Criteria bullet so the checkable criterion
   matches the normative prose that already sits eight lines above it.

## Non-goals

* No re-opening, re-running, re-evaluating, or retroactive reinterpretation of
  `140.001-T`, its AC3 verbatim-preservation rule, or feature `140-F`. AC3
  constrained what that task was authorized to do, it is already satisfied and
  merged, and this plan proceeds under a NEW authorization. See 026-DL.
* No new authoring contract. `templates/skills/compound/SKILL.md.tmpl` Phase 3
  ALREADY states the self-referential rule normatively; Task 3 is a one-line
  ratchet of an existing bullet to match it, not a redefinition, and not a
  re-litigation of `140.002-T`.
* No change to `doc_type` handling, and no value-shape assertion on `doc_type`
  (026-DL R3 - it would hard-code rung 3 of the template's capability-neutral
  authority order and contradict amendment C3).
* No migration, lint, or assertion change for any other `docs/` subdirectory.
  `decisions/`, `plans/`, `reviews/`, `closure/`, `spikes/`, `research/`,
  `design-docs/` and `product-specs/` are in docline scope and may carry the
  same class of gap; that is a SEPARATE surface and widening into it is a
  P-021 scope breach (026-DL R6, inherited from 025-DL R3).
* No change to any compound document's BODY bytes.
* No change to backlogit, to the docline base schema, or to the docline scope,
  path map or profile set.
* Does NOT resolve, supersede, or depend on active stash entry `B57F9E24`
  (backlogit checkpoint truncation), which remains external and unscheduled.

## Baseline (measured by Stage, read-only, 2026-08-23, HEAD `259ddeb1`)

Full-frontmatter parse of every `*.md` under `docs/compound/`:

| Measure | Value |
| --- | --- |
| Total markdown files | **75** (was 73 at 025-DL time, 2026-08-21) |
| `source` present and non-empty | 75 / 75 |
| `doc_type` present and non-empty | 75 / 75 |
| `source` self-referential (`docs/compound/<...>.md`) | **74 / 75** |
| `source` NOT self-referential | **1 / 75** |

The single outlier:

* File: `docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md`
* Current value: `source: "123-S / 115-F (PR #323 Copilot review)"`
* Current frontmatter keys, in order: `title`, `date`, `source`, `tags`,
  `doc_type`. There is **no `citations` key**.

Supporting baseline facts, each independently re-verified this session:

* `templates/skills/compound/SKILL.md.tmpl` Phase 3 states normatively:
  "`source` is this document's own repo-relative path ... It is never a
  description of where the *problem* came from; it is the location of the
  learnings file itself."
* The same template models a `citations` key in its Phase 3 frontmatter block
  and describes its purpose in Quality Criteria: "Citations make it possible to
  trace the learning back to the work that produced it."
* The same template's Quality Criteria also says "`source` and `doc_type` are
  present and non-empty" - strictly weaker than its own Phase 3 prose.
* `tests/test_docs_compound_frontmatter_contract.py::test_all_compound_docs_have_source_and_doc_type`
  asserts non-emptiness only (`if not source_value: missing_source.append(rel)`),
  so it reports 75/75 GREEN on a corpus containing a known violation.
* `.github/skills/` contains only `install-harness`, `tune-harness`,
  `verify-harness`, `workspace-discovery`. There is **no installed dogfood
  counterpart** to `templates/skills/compound/SKILL.md.tmpl`.
* `.autoharness/harness-manifest.yaml` has **no checksum entry** for
  `templates/skills/compound/SKILL.md.tmpl`. (`DOCS_COMPOUND: "docs/compound"`
  is present as a template variable and is unaffected by this work.)
* **(A3)** `tests/test_compound_template_docline_frontmatter.py` (landed by
  `140.002-T`) DOES pin `templates/skills/compound/SKILL.md.tmpl` as ordinary
  repo-side regression coverage. Two of its assertions bear directly on Task 3:
  `QualityCriteriaTests::test_quality_criteria_mentions_source_and_doc_type`
  (requires the literal backticked `` `source` `` and `` `doc_type` `` inside
  the `## Quality Criteria` section) and
  `CapabilityNeutralGuidanceTests::test_no_forbidden_tool_tokens_anywhere_in_template`
  (whole-file scan for `backlogit`, `docs classify`, `docs migrate`,
  `docs lint`, `docs scope`). This is regression coverage, NOT a paired-edit or
  checksum obligation, so it does not change the P-006 determination.

## Requires plan hardening

**no** - considered, not defaulted (P-006).

Rationale: the total blast radius is one corpus file changed frontmatter-only
and body-invariantly, one test module, and one prose bullet in one template
file. The plan touches no schema, no CLI distribution surface, and exactly one
template family. That template file has no installed dogfood counterpart and no
manifest checksum entry - both re-verified above - so there is no paired-edit
obligation and no checksum churn. Every change is small, local, mechanically
verifiable and fully git-revertible. This mirrors 025-DL's hardening
determination on the same surface, which held through execution of `140-F`
without surfacing a hardening-class hazard.

## Task breakdown

Three tasks, width-isolated per P-003 / 026-DL R6: corpus DATA, TEST surface,
TEMPLATE family. Each is well inside the 2-hour rule.

Execution order is **corpus -> test -> template**, a deliberate deviation from
this repository's usual RED-harness-first precedent. Rationale (026-DL R4):
there is exactly ONE known violation against an exactly measured baseline, so a
RED intermediate commit would break the canonical local gate mid-shipment for
zero diagnostic gain. The discriminating-power obligation in Task 2 replaces
what a RED harness would otherwise have proven.

### Task 1 - Correct the outlier `source` and relocate its provenance verbatim

Surface: corpus data (`docs/compound/`, one file).

Steps:

1. **RE-MEASURE FIRST** (026-DL R5). Re-run the full-frontmatter parse over
   `docs/compound/*.md` at execution HEAD and record the counts. The corpus is
   growing at roughly one document per day, so the 74/75 baseline above MUST NOT
   be trusted blind.
   * If exactly one non-conforming file is found and it is the expected one,
     proceed. **(A2)** Record explicitly that Task 2's exemption allowlist must
     therefore be EMPTY.
   * If **more than one** non-conforming file is found, fix ONLY the known
     outlier named in this plan, and capture the additional files as a NEW
     P-021 deferred entry for Stage. Do NOT silently widen scope. **(A2)**
     Record the exact list of surviving non-conforming files and the P-021
     capture ID in the task evidence, and hand that list to Task 2 as its
     exemption allowlist. This is what keeps the scope guard intact WITHOUT
     deadlocking Task 2's corpus-wide assertion.
   * If **zero** are found, the finding no longer reproduces: record that
     outcome with evidence and close the task `done`. Task 2 and Task 3 still
     proceed - the guard ratchet is valuable independent of the data fix.
     **(A2)** In this branch the shipment MUST record the data-fix half as a
     verified no-op rather than implying a correction was made.
2. In `docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md`
   only, set:
   `source: "docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md"`
3. Add a `citations` key carrying the displaced value VERBATIM:

   ```yaml
   citations:
     - "123-S / 115-F (PR #323 Copilot review)"
   ```

   Place it consistently with the template's Phase 3 key order.
4. Change nothing else. `title`, `date`, `tags`, `doc_type` survive byte-identical.

**(A4) Why adding `citations` is safe, with evidence.** docline's normalizer
folds non-contract keys under a `docline` namespace ("move, never drop"), so
adding a key could in principle invite future churn. It does not here: 74 of the
75 corpus files already carry non-contract keys (`title`, `date`, `tags`, and in
many cases `problem_type`, `category`, `root_cause`, `component`, `severity`,
and `citations` itself), and all of them survived `140.001-T`'s migration with
proven body invariance and verbatim key preservation. `citations` is no more
exposed than `tags` already is, and it is the key the authoring contract
designates for provenance ("Citations make it possible to trace the learning
back to the work that produced it").

Acceptance criteria:

* AC1.1 `git diff` for the changed file is confined entirely to the YAML
  frontmatter block; **zero body bytes change** (026-DL constraint 4, inherited
  from 025-DL R4). Show the diff as evidence.
* AC1.2 The displaced provenance string `123-S / 115-F (PR #323 Copilot review)`
  is still present in the file, character-for-character, under `citations`.
  Evidence: a grep showing it before and after.
* AC1.3 `title`, `date`, `tags`, `doc_type` are unchanged (026-DL constraint 3,
  inherited from 025-DL R5). **(A4)** No key other than `citations` is added.
* AC1.4 Exactly ONE file is modified. Evidence: `git diff --name-only`.
* AC1.5 `backlogit docs lint --path docs/compound` passes.
* AC1.6 The re-measurement from step 1 is recorded in the task evidence with its
  counts, including the case where the finding no longer reproduces.

### Task 2 - Ratchet the structural guard from non-emptiness to value shape

Surface: test module (`tests/test_docs_compound_frontmatter_contract.py`).

Steps:

1. Add a value-shape assertion for `source`: with surrounding quotes stripped
   and whitespace trimmed, `source` MUST equal the file's own repo-relative
   POSIX path.
2. **Derive the expected path from the file's actual location** -
   `path.relative_to(repo_root).as_posix()` - never a hard-coded flat
   `docs/compound/` prefix (026-DL R1). The authoring template models
   `source: "{{DOCS_COMPOUND}}/{category}/{slug}-{YYYY-MM-DD}.md"`, so a
   category SUBDIRECTORY is a legal future shape; a flat-prefix predicate would
   become a false failure the day the first one is created.
3. Make the assertion ADDITIVE (026-DL R2). Every existing behaviour must still
   fail after the ratchet: non-emptiness, the YAML-null (`source: null` /
   `source: ~`) case, the comment-only (`source: # missing`) case, the
   empty-string case, and the `*.md`-only scope guard
   (`test_no_non_markdown_assets_are_in_scope`, amendment C2). Do not delete or
   relax any of them to simplify the new assertion.
4. **(A2) Exemption allowlist.** Carry a single named allowlist constant for
   files exempted from the VALUE-SHAPE assertion only (never from non-emptiness).
   It MUST be empty in the expected one-outlier case. It may be non-empty ONLY
   when Task 1 recorded additional non-conforming files, in which case it
   enumerates exactly those files, each annotated with the deferring P-021
   capture ID. It is a SHRINKING allowlist in the sense of `141.002-T`: entries
   may only ever be removed, never added, without a new Stage authorization.
5. Leave `doc_type` at its existing non-emptiness check (026-DL R3).
6. On failure, report the offending file, its actual `source`, and the expected
   path, so the message is self-diagnosing.

Acceptance criteria:

* AC2.1 The full canonical gate is GREEN after Task 1:
  `$env:PYTHONPATH='src'; python -m unittest discover -s tests`
  (per `docs/compound/097-S-canonical-unittest-gate.md` - the canonical gate is
  `unittest discover`, NOT root pytest).
* AC2.2 **(A1, REWRITTEN) DISCRIMINATING POWER PROVEN IN ISOLATION.** Demonstrate
  that the new assertion fails on a wrong `source` value using an ISOLATED
  FIXTURE - a temporary directory or an in-test synthetic document - and record
  the failure output. **Mutating any tracked file under `docs/` for this purpose
  is FORBIDDEN**, including with an intended revert: that is a
  mutate-then-remember-to-undo pattern on the exact data this task exists to
  protect (see
  `docs/compound/2026-08-15-torn-archive-log-entry-without-file-mutation-must-not-be-committed.md`).
  A green-by-construction assertion does not satisfy this AC.
* AC2.3 All pre-existing behaviours of the module still fail as before. Evidence:
  a per-case demonstration or a negative-case table covering non-emptiness, YAML
  null, comment-only, empty string, and the `*.md` scope guard.
* AC2.4 The predicate is location-derived, not prefix-hard-coded. Evidence: the
  diff showing `relative_to(...).as_posix()` (or equivalent) at the call site.
* AC2.5 `doc_type` handling is unchanged. Evidence: the diff.
* AC2.6 The test glob is still scoped to `docs/compound/` only (026-DL R6).
* AC2.7 **(A2)** The exemption allowlist is EMPTY when Task 1 recorded exactly
  one non-conforming file, and otherwise contains exactly and only the extra
  files Task 1 recorded, each annotated with its deferring P-021 capture ID.
  Assert emptiness/contents explicitly so the allowlist cannot silently grow.
  Task 2 terminates `done` in every branch.

### Task 3 - Ratchet the template's Quality Criteria bullet to value shape

Surface: template family (`templates/skills/compound/SKILL.md.tmpl`, one bullet).

Steps:

1. Replace the Quality Criteria bullet
   "`source` and `doc_type` are present and non-empty (see Phase 3 above)"
   with a formulation that keeps `doc_type` at presence/non-emptiness while
   stating the `source` VALUE rule, cross-referencing the Phase 3 prose that
   already states it normatively.
2. Change nothing else in the file. Phase 3, the frontmatter block, the
   `doc_type` three-rung authority order, and amendment C3's capability-neutral
   wording all survive verbatim.
3. Keep the wording CAPABILITY-NEUTRAL: name no specific tool and no specific
   command. This template is a base Primitive 1 artifact that installs into
   workspaces with no backlog tooling at all (025-DL amendment C3).

**(A5) Scope of capability neutrality.** It constrains TEXT WRITTEN INTO THE
TEMPLATE only. It does NOT constrain this repository's own task acceptance
commands, which may and should name concrete local tooling (see AC1.5 and
AC2.1). Do not omit a useful local gate out of misplaced neutrality, and do not
copy a local command into the template.

Acceptance criteria:

* AC3.1 Exactly one file changed, and the diff is confined to the Quality
  Criteria bullet. Evidence: `git diff`.
* AC3.2 The amended bullet names NO tool and NO command (capability-neutral,
  C3). Evidence: the diff text.
* AC3.3 `doc_type` is still described as presence/non-emptiness in that bullet
  (026-DL R3).
* AC3.4 **(A3, REWRITTEN)** Verification is the canonical gate PLUS the named
  directly-affected regression module
  `tests/test_compound_template_docline_frontmatter.py`, both GREEN.
* AC3.5 The full canonical gate stays GREEN.
* AC3.6 **(A3, NARROWED)** No `.autoharness/harness-manifest.yaml` change is
  required. Evidence: confirm `templates/skills/compound/SKILL.md.tmpl` has no
  checksum entry and that no dogfood counterpart exists under `.github/skills/`.
  If EITHER of those two assumptions is FALSE at execution time, STOP and return
  to Stage - it would invalidate the P-006 hardening determination. The
  existence of the regression module named in AC3.7 does NOT fire this trigger;
  a repo-side test pinning a template is ordinary regression coverage, not a
  paired-edit or checksum obligation.
* AC3.7 **(A3, NEW) The two live assertions in
  `tests/test_compound_template_docline_frontmatter.py` that bear on this exact
  edit both stay GREEN:**
  * `QualityCriteriaTests::test_quality_criteria_mentions_source_and_doc_type` -
    it slices the template from the `## Quality Criteria` marker to end-of-file
    and requires the literal backticked tokens `` `source` `` and `` `doc_type` ``
    to appear in that slice. The amended bullet MUST keep both tokens, backticked,
    inside that section.
  * `CapabilityNeutralGuidanceTests::test_no_forbidden_tool_tokens_anywhere_in_template` -
    it scans the WHOLE file for `backlogit`, `docs classify`, `docs migrate`,
    `docs lint`, `docs scope`. The amended bullet MUST introduce none of them.
    This is the mechanical enforcement of AC3.2.

## Shipment shape

**ONE shipment.** A serial multi-shipment chain was evaluated and REJECTED: all
three tasks share a single contract surface (`docs/compound` `source` value
semantics), a single review, and a combined estimate well under one working
session. There is no conditional branch of the kind that forced 024-DL's work
into the 149-S -> 151-S split, and no cross-shipment `blocks` chain is required.

Intra-shipment order is dependency-encoded: Task 1 -> Task 2 -> Task 3.

## Verification

Canonical gate: `$env:PYTHONPATH='src'; python -m unittest discover -s tests`
(`docs/compound/097-S-canonical-unittest-gate.md`). Root pytest is
cross-reference only.

Corpus gate: `backlogit docs lint --path docs/compound`.

Final acceptance: the value-shape assertion must be GREEN across the corpus
measured at execution HEAD, not against the 75-file baseline recorded here.

## Risks

| ID | Risk | Mitigation |
| --- | --- | --- |
| K1 | Corpus drift between plan and execution (73 -> 75 in two days) | Task 1 step 1 re-measures first and branches explicitly on 0 / 1 / >1 non-conforming files |
| K2 | A flat-prefix predicate breaks on the first category subdirectory | AC2.4 requires a location-derived predicate |
| K3 | The ratchet silently weakens an existing guard | AC2.3 requires per-case proof that every pre-existing behaviour still fails |
| K4 | Green-by-construction assertion that never actually discriminates | AC2.2 requires recorded proof of failure on a wrong value |
| K5 | Template edit turns out to have a dogfood counterpart or a manifest entry | AC3.6 makes this a STOP-and-return-to-Stage condition, because it would invalidate the P-006 `no` |
| K6 | Scope creep into other `docs/` subdirectories | Non-goals + AC2.6 pin the glob to `docs/compound/` |
| K7 (A2) | The ">1 non-conforming file" branch leaves Task 2 permanently RED and deadlocks the shipment | Shrinking exemption allowlist + AC2.7; Task 2 terminates `done` in every branch |
| K8 (A3) | Task 3's bullet rewrite silently breaks a live template regression assertion | AC3.7 names both affected assertions and their exact literal requirements |
| K9 (A1) | Proving discriminating power corrupts tracked corpus data via a missed revert | AC2.2 forbids tracked-file mutation outright; isolated fixture only |

## Traceability

* Stash: `FAE1E7B7` (P-021 deferred scope expansion; duplicate scan CLEAN over
  190 entries; late-identifier reconciliation performed with NO RESULT, `PR: N/A`
  and `review-thread: N/A` stand as truthful terminal records).
* Deliberation: `026-DL`.
* Predecessor: `025-DL` -> `140-F` / `148-S` (PR #387, closure PR #388).
* Originating task whose AC3 correctly deferred this: `140.001-T`.
