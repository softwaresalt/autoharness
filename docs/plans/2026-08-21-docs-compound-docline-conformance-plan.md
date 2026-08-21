---
title: "docs/compound docline conformance - backfill source/doc_type and align the authoring contract"
date: 2026-08-21
stash_id: F73BA065
deliberation: ".backlogit/queue/025-DL.md"
requires_plan_hardening: no
hardening_present: no
blast_radius: "contained (single doc directory, frontmatter-only body-invariant migration via a first-party idempotent tool, plus one template file with no installed dogfood counterpart)"
---

# Implementation Plan - docs/compound docline conformance

Date: 2026-08-21
Agent: Stage (planning only - Ship executes)
Stash source: `F73BA065`
Deliberation: `025-DL`
Classification: **bug / corpus conformance gap against an opted-into contract**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Goal

Make every document under `docs/compound/` satisfy the docline base frontmatter
contract (`source` and `doc_type` present), and amend the compound authoring
template so newly authored learnings are born conformant.

## Non-goals

* No change to backlogit or to the docline base schema.
* No migration of any other `docs/` subdirectory. `decisions/`, `plans/`,
  `reviews/`, `closure/`, `spikes/`, `research/`, `design-docs/` and
  `product-specs/` are all in docline scope and may share the gap; that is a
  SEPARATE surface and is explicitly out of scope (P-021 C1).
* No change to any compound document's BODY bytes.
* No change to the docline scope, path map, or profile set (tool-owned; no
  repo-local lever exists).
* Does NOT resolve or supersede active stash entry `90F2A9F8` (docline
  hard-abort-on-first-decode-error), which remains external and unscheduled.

## Baseline (measured by Stage, read-only, 2026-08-21)

* `docs/compound/` holds **73** markdown files.
* **72** lack `source`; **73** lack `doc_type`; **0** have both.
* **4** have no YAML frontmatter block at all.
* `backlogit docs scope` maps `docs/compound/` -> doc_type `learning`; the scope
  already excludes `docs/archive/` and `docs/memory/`, so `docs/compound/` is in
  scope by deliberate configuration.
* `backlogit docs migrate --path docs/compound --format json` (dry-run, no
  writes) plans `action: update` for every file with `body_bytes_changed: false`.

## Requires plan hardening

**no** - considered, not defaulted. Rationale: the corpus half is a first-party,
idempotent, dry-run-first, body-preserving, single-path-scoped and fully
git-revertible migration with a mechanical verification predicate. The contract
half is a single template file (`templates/skills/compound/SKILL.md.tmpl`) with
**no installed dogfood counterpart** under `.github/skills/` - therefore no
paired-edit obligation and no `.autoharness/harness-manifest.yaml` checksum
churn. Neither half touches schemas, CLI distribution, or multiple template
families. See 025-DL "REQUIRES PLAN HARDENING" for the full statement.

## Task breakdown

### Task 1 - Verify and apply the docs/compound frontmatter migration

**Test-first requirement.** Before any write, add
`tests/test_docs_compound_frontmatter_contract.py` asserting that every `*.md`
under `docs/compound/` has a YAML frontmatter block containing non-empty
`source` and `doc_type` keys. This test MUST be RED at the start of the task
(73 failures) and GREEN at the end. Include the 4 no-frontmatter files by name
in the failure message so a skipped file cannot hide.

**Steps.**
1. Re-run the dry-run: `backlogit docs migrate --path docs/compound --format json`.
2. **GATE (blocking).** Inspect the planned `source` value. If the migration
   would fabricate provenance it cannot know, STOP and return to Stage. Do not
   `--apply` an unexamined value. Record the observed value verbatim in the task.
3. Enumerate the 4 files with no frontmatter block by name and record whether
   the dry-run plans a synthesised block for each.
4. Apply, scoped: `backlogit docs migrate --apply --yes --path docs/compound`.
   The `--path` MUST be exactly `docs/compound`.
5. Any of the 4 files the migration skipped: hand-author a frontmatter block
   consistent with the amended contract from Task 2 conventions (`doc_type:
   learning`, `source` matching the value observed in step 2).
6. Re-run the migration dry-run to prove **idempotence**: second run must plan
   zero changes.

**Acceptance criteria.**
* AC1. `tests/test_docs_compound_frontmatter_contract.py` passes; 73/73 files
  carry non-empty `source` and `doc_type`.
* AC2. `git diff --stat docs/compound` shows changes confined to frontmatter;
  for every changed file the diff contains **no** hunk below the closing `---`
  of the frontmatter block. Evidence: the diff itself, not an assertion about it.
* AC3. Every pre-existing frontmatter key survives verbatim (no key removed,
  no value rewritten). Spot-verify at minimum
  `2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md`, which
  carries `problem_type`/`category`/`root_cause`/`tags`/`shipment`/`task`/`date`.
* AC4. Second migration dry-run plans zero changes (idempotence proven).
* AC5. The 4 no-frontmatter files are individually named in the task record with
  their disposition (migrated vs hand-authored).
* AC6. No file outside `docs/compound/` is modified, with ONE explicit
  exemption: `tests/test_docs_compound_frontmatter_contract.py`, which the
  test-first requirement above REQUIRES this task to create. That test is an
  in-scope deliverable of this plan, not a scope breach. No other path outside
  `docs/compound/` may be touched. (Corrected in review-fix cycle 1 - as
  originally written AC6 contradicted the task's own test-first requirement and
  was unsatisfiable.)

**Rollback.** `git checkout -- docs/compound` restores the corpus exactly;
the migration writes nothing outside that path. The contract test
`tests/test_docs_compound_frontmatter_contract.py` is a newly added file and is
removed separately if the task is abandoned.

### Task 2 - Amend the compound authoring template to require source and doc_type

**Test-first requirement.** Extend
`tests/test_docs_compound_frontmatter_contract.py` (or add a sibling structural
test) asserting that `templates/skills/compound/SKILL.md.tmpl` Phase 3 frontmatter
example contains both `source:` and `doc_type:` keys. RED before, GREEN after.

**Steps.**
1. Amend the Phase 3 YAML frontmatter example in
   `templates/skills/compound/SKILL.md.tmpl` to include `source` and
   `doc_type`, using the value semantics confirmed in Task 1 step 2.
2. `doc_type` guidance MUST state that the value is path-derived and that
   `backlogit docs classify <path>` is the authority - not a free-text choice.
3. Add the two fields to the skill's "Quality Criteria" list.
4. Confirm no `.github/skills/compound/` counterpart exists; if one has appeared
   since planning, STOP - a paired edit plus manifest checksum refresh is then
   required and this task's scope no longer holds.

**Acceptance criteria.**
* AC7. The template's Phase 3 example carries `source` and `doc_type`.
* AC8. The template still renders (no unresolved or malformed `{{...}}`
  introduced; the two new keys must not add a new template variable).
* AC9. `.github/skills/` contains no `compound/` directory - verified and
  recorded, not assumed.
* AC10. No `.autoharness/harness-manifest.yaml` entry changes (proves no
  dogfood counterpart was silently touched).

**Dependency.** Task 2 depends on Task 1 (Task 1 step 2 establishes the `source`
value semantics that Task 2 documents).

## Width isolation (P-003)

Task 1 is a data migration over one doc directory. Task 2 is a template-family
edit. They are deliberately separate tasks and must not be merged.

## Verification gate for the shipment

* `tests/test_docs_compound_frontmatter_contract.py` green.
* Canonical suite green per `docs/compound/097-S-canonical-unittest-gate.md`
  (`$env:PYTHONPATH='src'; python -m unittest discover -s tests`), allowing for
  the known pre-existing failures tracked under `E8158860` if that shipment has
  not yet merged.
* `backlogit docs lint --path docs/compound` reports zero required-field errors
  for `source`/`doc_type`. (Note: per active entry `90F2A9F8` the linter
  hard-aborts on the first decode error anywhere in scope; use `--path` scoping.)

## Amendments applied from plan review

Source: `docs/reviews/2026-08-21-docs-compound-docline-conformance-review.md` (PASS).

* **C1 (P1-1)** - The shipment verification gate is rewritten to:
  `backlogit docs lint --path docs/compound` reports **ZERO required-field errors
  of ANY kind** (not merely zero `source`/`doc_type` errors). Any residual error
  class must be enumerated by field name and either fixed within Task 1 when the
  value is mechanically derivable, or captured as a NEW deferred stash entry
  under P-021 C1. Silent acceptance of a residual class is forbidden.
* **C2 (P2-1, P2-2)** - The four `docs/compound/` files with no YAML frontmatter
  block are named here so execution does not have to rediscover them:
  * `2026-08-07-copilot-review-fix-introduces-new-filter-bug.md`
  * `2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`
  * `2026-08-15-never-serialize-raw-operator-content-into-json-reports.md`
  * `2026-08-15-torn-archive-log-entry-without-file-mutation-must-not-be-committed.md`

  If the corpus has changed since planning, the executing agent re-derives the
  list and records the delta. The contract test scope is `*.md` only;
  `docs/compound/.gitkeep` and any future non-markdown asset are out of scope.
